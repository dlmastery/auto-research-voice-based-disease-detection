"""The competitive benchmark harness.

Everything in this module exists to make one number defensible: **the margin of an
audio model above the strongest confound baseline, measured on identical
speaker-disjoint folds.** A win that does not clear the confound bar is reported
as `NOT CLEARED` (CLAUDE.md §4.3, and F1: on SVD, age alone reaches AUC 0.871).

Guarantees enforced in code, not in prose:

* **Speaker-disjoint folds** with a hard pre-fit assertion. `assert_speaker_disjoint`
  raises before any `.fit()` touches the data; there is no flag to disable it.
* **Every fitted object is fit per fold on TRAIN ONLY** -- scaler, head,
  calibrator, and the ensemble's member selection. Scaling fitted before
  splitting moves SVD by -0.14/+0.14 pp but VOICED by -8.3/+7.8 pp over 1,000
  repetitions (Applied Soft Computing S1568494626007970), so "it's only a small
  effect" is not defensible.
* **The confound battery runs on the identical folds** as the audio model, so the
  margin is paired and its bootstrap CI is a paired CI.
* **The power check is COMPUTED, not assumed** (R6): `min_attainable_p(n) = 2/2^n`
  against Holm's tightest threshold `0.05/m` for the actual family size.
* **Speaker-level metrics are reported alongside recording-level ones.** When a
  corpus gives ~14 recordings per speaker, recording-level n is not the
  statistical n; the speaker-level number is the honest one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Sequence

import numpy as np
from scipy import stats
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from .embed import EmbeddingBundle

POSITIVE_LABEL_DEFAULT = "pathological"
HEAD_NAMES = ("logreg", "linsvm", "mlp", "gbt")
ENSEMBLE_NAME = "ens_rank3"


# --------------------------------------------------------------------------- #
# Splits
# --------------------------------------------------------------------------- #


def assert_speaker_disjoint(
    speaker_ids: np.ndarray, train_idx: np.ndarray, test_idx: np.ndarray
) -> None:
    """Hard pre-fit gate. Raises if a single speaker appears on both sides."""
    tr = set(map(str, np.asarray(speaker_ids)[train_idx]))
    te = set(map(str, np.asarray(speaker_ids)[test_idx]))
    overlap = tr & te
    if overlap:
        raise AssertionError(
            f"SPEAKER LEAKAGE: {len(overlap)} speaker(s) in both train and test, "
            f"e.g. {sorted(overlap)[:5]}"
        )
    if not te:
        raise AssertionError("empty test fold")


def stratified_group_folds(
    speaker_ids: Sequence[str], y: np.ndarray, n_folds: int, seed: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Speaker-disjoint folds, label-balanced at the SPEAKER level.

    `GroupKFold` is deterministic (no shuffle), so repeats need their own group
    permutation. Speakers are shuffled per seed, then greedily assigned to the
    fold that currently has the fewest speakers of that speaker's majority class.
    """
    speaker_ids = np.asarray([str(s) for s in speaker_ids])
    rng = np.random.default_rng(seed)
    uniq = np.unique(speaker_ids)
    rng.shuffle(uniq)

    spk_label: dict[str, int] = {}
    for s in uniq:
        m = speaker_ids == s
        spk_label[s] = int(round(float(y[m].mean())))

    counts = np.zeros((n_folds, 2), dtype=int)
    assign: dict[str, int] = {}
    for s in uniq:
        lab = spk_label[s]
        f = int(np.lexsort((np.arange(n_folds), counts[:, lab]))[0])
        assign[s] = f
        counts[f, lab] += 1

    folds = []
    fold_of = np.array([assign[s] for s in speaker_ids])
    for f in range(n_folds):
        test_idx = np.flatnonzero(fold_of == f)
        train_idx = np.flatnonzero(fold_of != f)
        if test_idx.size == 0 or len(np.unique(y[train_idx])) < 2:
            continue
        assert_speaker_disjoint(speaker_ids, train_idx, test_idx)
        folds.append((train_idx, test_idx))
    if len(folds) < 2:
        raise ValueError("could not build >=2 usable speaker-disjoint folds")
    return folds


def _inner_group_splits(groups: np.ndarray, y: np.ndarray, n_inner: int = 3):
    """Group-aware inner splits for calibration / ensemble selection (train only)."""
    n_inner = max(2, min(n_inner, len(np.unique(groups))))
    try:
        return list(GroupKFold(n_splits=n_inner).split(np.zeros(len(y)), y, groups))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Heads
# --------------------------------------------------------------------------- #


def make_head(name: str, seed: int):
    if name == "logreg":
        return LogisticRegression(max_iter=5000, C=1.0, random_state=seed)
    if name == "linsvm":
        return LinearSVC(C=0.1, max_iter=20000, dual="auto", random_state=seed)
    if name == "mlp":
        # MLP-small beat linear probing in 23/30 model-task combinations
        # (arXiv:2606.15436), so it is in the head set by evidence, not by taste.
        return MLPClassifier(
            hidden_layer_sizes=(256,),
            alpha=1e-3,
            max_iter=600,
            early_stopping=False,
            random_state=seed,
        )
    if name == "gbt":
        return HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.1, early_stopping=False, random_state=seed
        )
    raise ValueError(f"unknown head {name!r}")


def _fit_predict_head(
    name: str, Xtr, ytr, gtr, Xte, seed: int
) -> np.ndarray:
    """Fit one head on TRAIN ONLY and return P(positive) on test."""
    clf = make_head(name, seed)
    if name == "linsvm":
        # Platt-calibrate with GROUP-AWARE inner folds so ECE is not inflated by
        # speaker leakage inside the calibration loop.
        inner = _inner_group_splits(gtr, ytr)
        clf = CalibratedClassifierCV(clf, cv=inner if inner else 3, method="sigmoid")
    clf.fit(Xtr, ytr)
    return clf.predict_proba(Xte)[:, 1]


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #


def expected_calibration_error(y: np.ndarray, p: np.ndarray, n_bins: int = 15) -> float:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = idx == b
        if not m.any():
            continue
        ece += (m.mean()) * abs(float(y[m].mean()) - float(p[m].mean()))
    return float(ece)


def score_all(y: np.ndarray, p: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    yhat = (p >= threshold).astype(int)
    single_class = len(np.unique(y)) < 2
    return {
        "roc_auc": float("nan") if single_class else float(roc_auc_score(y, p)),
        "uar": float(balanced_accuracy_score(y, yhat)),
        "accuracy": float(accuracy_score(y, yhat)),
        "f1": float(f1_score(y, yhat, zero_division=0)),
        "ece": expected_calibration_error(y, p),
    }


def aggregate_to_speaker(
    speaker_ids: np.ndarray, y: np.ndarray, p: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mean predicted probability per speaker. The honest unit when a speaker
    contributes many recordings of the same label."""
    uniq = np.unique(speaker_ids)
    ys, ps = [], []
    for s in uniq:
        m = speaker_ids == s
        ys.append(int(round(float(y[m].mean()))))
        ps.append(float(p[m].mean()))
    return uniq, np.asarray(ys), np.asarray(ps)


# --------------------------------------------------------------------------- #
# Bootstrap over speakers
# --------------------------------------------------------------------------- #


def _bootstrap_speaker_indices(
    speaker_ids: np.ndarray, n_boot: int, seed: int
) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    uniq = np.unique(speaker_ids)
    by_spk = {s: np.flatnonzero(speaker_ids == s) for s in uniq}
    out = []
    for _ in range(n_boot):
        picked = rng.choice(uniq, size=len(uniq), replace=True)
        out.append(np.concatenate([by_spk[s] for s in picked]))
    return out


def bootstrap_ci(
    y: np.ndarray,
    p: np.ndarray,
    speaker_ids: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    n_boot: int,
    seed: int,
    boot_idx: list[np.ndarray] | None = None,
) -> dict[str, float]:
    idxs = boot_idx or _bootstrap_speaker_indices(speaker_ids, n_boot, seed)
    vals = []
    for ii in idxs:
        if len(np.unique(y[ii])) < 2:
            continue
        vals.append(metric(y[ii], p[ii]))
    if not vals:
        return {"lo": float("nan"), "hi": float("nan"), "n_boot": 0}
    arr = np.asarray(vals)
    return {
        "lo": float(np.percentile(arr, 2.5)),
        "hi": float(np.percentile(arr, 97.5)),
        "n_boot": int(arr.size),
    }


def paired_bootstrap_delta(
    y: np.ndarray,
    p_a: np.ndarray,
    p_b: np.ndarray,
    speaker_ids: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    n_boot: int,
    seed: int,
) -> dict[str, float]:
    """CI on metric(a) - metric(b) using the SAME speaker resample for both."""
    idxs = _bootstrap_speaker_indices(speaker_ids, n_boot, seed)
    vals = []
    for ii in idxs:
        if len(np.unique(y[ii])) < 2:
            continue
        vals.append(metric(y[ii], p_a[ii]) - metric(y[ii], p_b[ii]))
    arr = np.asarray(vals) if vals else np.asarray([np.nan])
    return {
        "delta": float(metric(y, p_a) - metric(y, p_b)),
        "lo": float(np.nanpercentile(arr, 2.5)),
        "hi": float(np.nanpercentile(arr, 97.5)),
        "p_gt_zero": float(np.mean(arr > 0)) if vals else float("nan"),
        "n_boot": int(len(vals)),
    }


# --------------------------------------------------------------------------- #
# Power (R6)
# --------------------------------------------------------------------------- #


def power_check(n_paired: int, family_size: int, alpha: float = 0.05) -> dict[str, Any]:
    """CLAUDE.md R6: is the plan arithmetically capable of clearing Holm at all?"""
    min_p = 2.0 / (2.0**n_paired) if n_paired > 0 else 1.0
    holm = alpha / max(family_size, 1)
    n_needed = 1
    while 2.0 / (2.0**n_needed) > holm and n_needed < 64:
        n_needed += 1
    return {
        "n_paired": int(n_paired),
        "family_size": int(family_size),
        "min_attainable_p": float(min_p),
        "holm_tightest_threshold": float(holm),
        "feasible": bool(min_p <= holm),
        "min_n_for_feasibility": int(n_needed),
        "rule": "CLAUDE.md R6 -- paired Wilcoxon min p = 2/2^n vs Holm 0.05/m",
    }


# --------------------------------------------------------------------------- #
# Confound battery
# --------------------------------------------------------------------------- #


def confound_matrix(bundle: EmbeddingBundle, which: str) -> np.ndarray:
    """Build a confound design matrix from metadata that never heard the audio."""
    age = np.nan_to_num(bundle.age.astype(np.float64), nan=float(np.nanmean(bundle.age)))
    sex = np.asarray([1.0 if str(s).upper().startswith("M") else 0.0 for s in bundle.sex])
    dur = bundle.duration_s.astype(np.float64)
    rms = bundle.rms.astype(np.float64)
    cols = {
        "age_only": [age],
        "sex_only": [sex],
        "age_sex": [age, sex],
        "duration_only": [dur],
        "intensity_rms_only": [rms],
        "age_sex_duration_rms": [age, sex, dur, rms],
    }
    if which not in cols:
        raise ValueError(f"unknown confound set {which!r}; known: {sorted(cols)}")
    return np.column_stack(cols[which])


CONFOUND_SETS = (
    "age_only",
    "sex_only",
    "age_sex",
    "duration_only",
    "intensity_rms_only",
    "age_sex_duration_rms",
)


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


@dataclass
class BenchmarkConfig:
    corpus: str
    backbone: str
    pooling: str
    heads: tuple[str, ...] = HEAD_NAMES
    n_folds: int = 5
    n_repeats: int = 10
    seed: int = 0
    n_boot: int = 2000
    positive_label: str = POSITIVE_LABEL_DEFAULT
    confound_sets: tuple[str, ...] = CONFOUND_SETS
    embedding_hash: str = ""
    embedding_path: str = ""
    notes: str = ""

    def hash(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class RunResult:
    config: dict[str, Any]
    config_hash: str
    dataset: dict[str, Any]
    power: dict[str, Any]
    recording_level: dict[str, Any] = field(default_factory=dict)
    speaker_level: dict[str, Any] = field(default_factory=dict)
    per_repeat_auc: dict[str, list[float]] = field(default_factory=dict)
    margins: dict[str, Any] = field(default_factory=dict)
    verdicts: dict[str, str] = field(default_factory=dict)


def _oof_predictions(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    heads: Sequence[str],
    folds: Sequence[tuple[np.ndarray, np.ndarray]],
    seed: int,
) -> dict[str, np.ndarray]:
    """Out-of-fold P(positive) for every head plus the rank-average ensemble.

    The ensemble picks its 3 members **per fold** from TRAIN-ONLY inner OOF AUC.
    Selecting members by test AUC would be test-peeking; this does not.
    """
    preds = {h: np.full(len(y), np.nan) for h in heads}
    preds[ENSEMBLE_NAME] = np.full(len(y), np.nan)

    for train_idx, test_idx in folds:
        assert_speaker_disjoint(groups, train_idx, test_idx)  # hard pre-fit gate
        scaler = StandardScaler().fit(X[train_idx])  # TRAIN ONLY
        Xtr, Xte = scaler.transform(X[train_idx]), scaler.transform(X[test_idx])
        ytr, gtr = y[train_idx], groups[train_idx]

        fold_test: dict[str, np.ndarray] = {}
        for h in heads:
            p = _fit_predict_head(h, Xtr, ytr, gtr, Xte, seed)
            preds[h][test_idx] = p
            fold_test[h] = p

        # --- train-only inner selection for the ensemble -------------------- #
        inner = _inner_group_splits(gtr, ytr, n_inner=3)
        inner_auc: dict[str, float] = {}
        if inner and len(heads) >= 3:
            for h in heads:
                oof = np.full(len(ytr), np.nan)
                ok = True
                for itr, ite in inner:
                    if len(np.unique(ytr[itr])) < 2:
                        ok = False
                        break
                    sc = StandardScaler().fit(Xtr[itr])
                    oof[ite] = _fit_predict_head(
                        h, sc.transform(Xtr[itr]), ytr[itr], gtr[itr], sc.transform(Xtr[ite]), seed
                    )
                m = ~np.isnan(oof)
                inner_auc[h] = (
                    float(roc_auc_score(ytr[m], oof[m]))
                    if ok and m.any() and len(np.unique(ytr[m])) > 1
                    else 0.0
                )
            members = sorted(inner_auc, key=lambda h: -inner_auc[h])[:3]
        else:
            members = list(heads)[:3]

        ranks = [stats.rankdata(fold_test[h]) / len(test_idx) for h in members]
        preds[ENSEMBLE_NAME][test_idx] = np.mean(ranks, axis=0)

    return preds


def run_benchmark(
    bundle: EmbeddingBundle,
    cfg: BenchmarkConfig,
    *,
    verbose: bool = True,
) -> RunResult:
    y = (bundle.labels == cfg.positive_label).astype(int)
    groups = np.asarray([str(s) for s in bundle.speaker_ids])
    X = bundle.X.astype(np.float64)

    if len(np.unique(y)) < 2:
        raise ValueError(f"positive_label {cfg.positive_label!r} does not split the labels")

    spk_uniq, spk_y, _ = aggregate_to_speaker(groups, y, y.astype(float))
    dataset = {
        "corpus": cfg.corpus,
        "n_recordings": int(len(y)),
        "n_speakers": int(len(spk_uniq)),
        "n_positive_recordings": int(y.sum()),
        "n_negative_recordings": int((1 - y).sum()),
        "n_positive_speakers": int(spk_y.sum()),
        "n_negative_speakers": int((1 - spk_y).sum()),
        "recordings_per_speaker_mean": float(len(y) / len(spk_uniq)),
        "embedding_dim": int(X.shape[1]),
        "embedding_cache": str(bundle.cache_path),
        "embedding_content_hash": bundle.hash,
        "speakers_with_mixed_labels": int(
            sum(1 for s in spk_uniq if len(np.unique(y[groups == s])) > 1)
        ),
    }

    audio_names = list(cfg.heads) + [ENSEMBLE_NAME]
    confound_names = [f"confound::{c}" for c in cfg.confound_sets]
    all_names = audio_names + confound_names

    pooled: dict[str, np.ndarray] = {}
    per_repeat: dict[str, list[float]] = {n: [] for n in all_names}

    for rep in range(cfg.n_repeats):
        seed = cfg.seed + rep
        folds = stratified_group_folds(groups, y, cfg.n_folds, seed)
        if verbose:
            print(f"[bench] repeat {rep + 1}/{cfg.n_repeats} ({len(folds)} folds)", flush=True)

        rep_preds = _oof_predictions(X, y, groups, cfg.heads, folds, seed)
        for cset in cfg.confound_sets:
            Xc = confound_matrix(bundle, cset)
            cp = np.full(len(y), np.nan)
            for tr, te in folds:
                assert_speaker_disjoint(groups, tr, te)
                sc = StandardScaler().fit(Xc[tr])
                clf = LogisticRegression(max_iter=5000, random_state=seed)
                clf.fit(sc.transform(Xc[tr]), y[tr])
                cp[te] = clf.predict_proba(sc.transform(Xc[te]))[:, 1]
            rep_preds[f"confound::{cset}"] = cp

        for name, p in rep_preds.items():
            m = ~np.isnan(p)
            per_repeat[name].append(
                float(roc_auc_score(y[m], p[m])) if len(np.unique(y[m])) > 1 else float("nan")
            )
            pooled.setdefault(name, np.zeros(len(y)))
            pooled[name] += np.nan_to_num(p) / cfg.n_repeats

    # --- metrics ---------------------------------------------------------- #
    boot_idx_rec = _bootstrap_speaker_indices(groups, cfg.n_boot, cfg.seed + 777)
    rec: dict[str, Any] = {}
    spk: dict[str, Any] = {}
    spk_p: dict[str, np.ndarray] = {}

    for name in all_names:
        p = pooled[name]
        r = score_all(y, p)
        r["roc_auc_ci95"] = bootstrap_ci(
            y, p, groups, lambda a, b: float(roc_auc_score(a, b)), cfg.n_boot, cfg.seed, boot_idx_rec
        )
        r["per_repeat_auc_mean"] = float(np.nanmean(per_repeat[name]))
        r["per_repeat_auc_std"] = float(np.nanstd(per_repeat[name]))
        rec[name] = r

        su, sy, sp = aggregate_to_speaker(groups, y, p)
        spk_p[name] = sp
        s = score_all(sy, sp)
        s["roc_auc_ci95"] = bootstrap_ci(
            sy, sp, su, lambda a, b: float(roc_auc_score(a, b)), cfg.n_boot, cfg.seed
        )
        spk[name] = s

    # --- confound bar + margins ------------------------------------------- #
    best_conf = max(confound_names, key=lambda n: rec[n]["roc_auc"])
    best_audio = max(audio_names, key=lambda n: rec[n]["roc_auc"])

    margins: dict[str, Any] = {
        "confound_bar_name": best_conf,
        "confound_bar_auc_recording": rec[best_conf]["roc_auc"],
        "confound_bar_auc_speaker": spk[best_conf]["roc_auc"],
        "best_audio_head": best_audio,
        "per_head": {},
    }
    su, sy, _ = aggregate_to_speaker(groups, y, y.astype(float))
    for name in audio_names:
        rec_delta = paired_bootstrap_delta(
            y,
            pooled[name],
            pooled[best_conf],
            groups,
            lambda a, b: float(roc_auc_score(a, b)),
            cfg.n_boot,
            cfg.seed,
        )
        spk_delta = paired_bootstrap_delta(
            sy,
            spk_p[name],
            spk_p[best_conf],
            su,
            lambda a, b: float(roc_auc_score(a, b)),
            cfg.n_boot,
            cfg.seed,
        )
        a = np.asarray(per_repeat[name], dtype=float)
        b = np.asarray(per_repeat[best_conf], dtype=float)
        ok = ~(np.isnan(a) | np.isnan(b))
        try:
            w = stats.wilcoxon(a[ok], b[ok])
            wil = {"statistic": float(w.statistic), "p_value": float(w.pvalue)}
        except Exception as exc:  # noqa: BLE001 - e.g. all-zero differences
            wil = {"statistic": float("nan"), "p_value": float("nan"), "error": str(exc)[:120]}
        margins["per_head"][name] = {
            "recording_level_delta_auc": rec_delta,
            "speaker_level_delta_auc": spk_delta,
            "paired_wilcoxon_over_repeats": wil,
            "cleared_confound_bar_recording": bool(rec_delta["lo"] > 0),
            "cleared_confound_bar_speaker": bool(spk_delta["lo"] > 0),
        }

    power = power_check(cfg.n_repeats, family_size=len(audio_names))

    verdicts: dict[str, str] = {}
    for name in audio_names:
        m = margins["per_head"][name]
        if m["cleared_confound_bar_speaker"] and m["cleared_confound_bar_recording"]:
            v = "CLEARED_CONFOUND_BAR"
        elif m["cleared_confound_bar_recording"]:
            v = "NOT CLEARED (recording-level only; speaker-level CI includes 0)"
        else:
            v = "NOT CLEARED"
        if not power["feasible"]:
            v += " | UNDERPOWERED (R6)"
        verdicts[name] = v

    return RunResult(
        config=asdict(cfg),
        config_hash=cfg.hash(),
        dataset=dataset,
        power=power,
        recording_level=rec,
        speaker_level=spk,
        per_repeat_auc={k: [float(v) for v in vs] for k, vs in per_repeat.items()},
        margins=margins,
        verdicts=verdicts,
    )
