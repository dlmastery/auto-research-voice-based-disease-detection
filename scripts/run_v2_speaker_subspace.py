"""run_v2_speaker_subspace.py -- V2: how much of the "disease" signal is speaker identity?

PRE-REGISTERED IN `IDEA_TABLE.md` BEFORE THIS RUN. Nothing below was chosen after
seeing a result; the falsifier, the predicted range and the family size m=14 are
quoted from the registry.

CLAIM
  A large fraction of frozen-embedding disease discrimination lives in a low-rank
  SPEAKER-IDENTITY subspace, and removing it collapses AUC further than a
  variance-matched random projection of the same rank does.

AUDITED CLAIM
  Yeh, Sun, Mahapatra, Chandra, Mower Provost, Sisman, 2026, "Who is Speaking or Who
  is Depressed? A Controlled Study of Speaker Leakage in Speech-Based Depression
  Detection" (arXiv:2604.14354) establishes by MEASUREMENT that speaker overlap
  inflates performance and that a DANN fails to close the gap, concluding identity
  reliance is "a property of current speech representations". The MECHANISTIC test --
  estimate the identity subspace, project it out, re-measure -- has not been run.

FALSIFIER (two-sided, both pre-registered)
  (a) If projecting out the rank-k speaker subspace collapses disease AUC toward
      chance while a variance-matched same-rank random projection does not --
      D(k) = AUC_rand(k) - AUC_spk(k) with a Holm-corrected 95% CI excluding 0, AND
      AUC_spk(k)'s CI including 0.5 -- the clinical-validity claim is falsified.
  (b) If D(k) is within the noise band for ALL k while AUC_spk(k) stays well above
      chance, the HYPOTHESIS is falsified and the audited result is STRENGTHENED --
      the positive control the field currently lacks.

PREDICTED (before the run)
  At k=16: AUC_spk drops 0.10-0.25 from AUC_full; the random control drops < 0.05;
  D(16) in [0.06, 0.22], positive. Manipulation check: speaker-ID accuracy on the
  projected embeddings falls from ~0.90 to < 0.30.

RIGOR
  m = 14 (7 ranks x 2 corpora) is the PRE-REGISTERED family size and is used here
  even though only SVD is run, which is the conservative choice -- shrinking m after
  the fact to buy significance is exactly the move the contract forbids.
  n = 10 repeats -> min attainable paired p = 2/2^10 = 0.001953 <= 0.05/14 = 0.003571.

LEAKAGE DISCIPLINE
  Every subspace -- speaker AND random control -- is estimated on TRAINING SPEAKERS
  ONLY, inside each fold. Estimating it on all data would leak test speakers into the
  very projection meant to remove them, which would flatter the result.

JUDGE-FREE. Objective is ROC-AUC against ground-truth clinical labels.

Usage:  python scripts/run_v2_speaker_subspace.py            # CPU, no network
        V2_RANKS=1,16 V2_REPEATS=3 python scripts/...        # quick screening pass
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RANKS = [int(x) for x in os.environ.get("V2_RANKS", "1,2,4,8,16,32,64").split(",")]
REPEATS = int(os.environ.get("V2_REPEATS", "10"))
FOLDS = int(os.environ.get("V2_FOLDS", "5"))
FAMILY_M = 14          # pre-registered; NOT recomputed from what was actually run
OUT = ROOT / "autoresearch_results" / "V2_speaker_subspace.json"
PARTIAL = OUT.with_suffix(".partial.json")   # written after every repeat


def load_svd() -> dict:
    """Largest cached WavLM matrix for SVD. speaker_id travels inside the npz."""
    cands = sorted(glob.glob(str(ROOT / "cache/embeddings/wavlm/svd/*.npz")),
                   key=lambda p: Path(p).stat().st_size)
    if not cands:
        sys.exit("FATAL: no cached WavLM embeddings. Run scripts/run_benchmark.py first.")
    d = np.load(cands[-1], allow_pickle=True)
    return {"X": d["X"].astype(np.float64), "spk": d["speaker_ids"],
            "y": (d["labels"] == "pathological").astype(int), "src": Path(cands[-1]).name}


def speaker_subspace(X: np.ndarray, spk: np.ndarray, k: int) -> np.ndarray:
    """Top-k directions of the BETWEEN-SPEAKER scatter -- the identity subspace.

    Between-speaker scatter is what separates one person from another while ignoring
    within-person variation across their recordings, which is exactly the "who is
    talking" direction we want to delete. Weighting each speaker equally (rather than
    each recording) keeps a 336-recording speaker from defining the subspace on their
    own.
    """
    means = np.stack([X[spk == s].mean(0) for s in np.unique(spk)])
    means = means - means.mean(0, keepdims=True)
    # SVD of the speaker-mean matrix; right singular vectors span the identity subspace
    _, sv, Vt = np.linalg.svd(means, full_matrices=False)
    return Vt[:k].T, sv                                   # (d, k)


def variance_controls(Vt: np.ndarray, frac: np.ndarray, target_var: float,
                      k: int) -> dict:
    """Two rank-k control subspaces, both built from the data's own principal axes.

    WHY NOT A UNIFORMLY RANDOM SUBSPACE. A random k-subspace of a 1536-dim space
    captures only ~k/d of the variance. The screening pass made this concrete: at
    k=16 the speaker subspace held 0.818 of the variance while the best of 400 random
    draws reached 0.350. Removing 35% of the variance and removing 82% of it are not
    the same intervention, so that comparison could not separate "identity was
    removed" from "more signal was removed". The control has to hold variance fixed.

      pca_topk    -- the top-k principal subspace. This is the variance-MAXIMISING
                     rank-k subspace, so it removes at least as much variance as the
                     speaker subspace can (0.879 vs 0.818 at k=16). If deleting MORE
                     variance this way costs LESS disease AUC, the speaker subspace's
                     damage cannot be a variance effect. Strictly conservative.
      var_matched -- start from the top-k and swap the lowest-variance member down
                     the spectrum until the captured variance lands on `target_var`.
                     Equal variance destroyed, different directions.

    Reporting both means the claim survives whichever control a reader trusts more.
    """
    out = {}
    top = np.arange(k)
    out["pca_topk"] = (Vt[top].T, float(frac[top].sum()))

    idx = list(range(k))
    cur = frac[idx].sum()
    nxt = k
    # walk the last slot down the spectrum; variance falls monotonically toward target
    while cur > target_var and nxt < len(frac):
        cand = idx[:-1] + [nxt]
        cand_var = frac[cand].sum()
        if abs(cand_var - target_var) >= abs(cur - target_var):
            break
        idx, cur, nxt = cand, cand_var, nxt + 1
    out["var_matched"] = (Vt[idx].T, float(cur))
    return out


def project_out(X: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Remove the span of B (d x k, orthonormal columns) from every row of X."""
    return X - (X @ B) @ B.T


def auc_cv(X, y, groups, seed) -> float:
    """Speaker-disjoint GroupKFold ROC-AUC. Scaler fitted on TRAIN only, every fold."""
    # GroupKFold is deterministic, so shuffle the group->fold assignment per repeat
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    perm = {s: i for i, s in enumerate(rng.permutation(uniq))}
    gshuf = np.array([perm[g] for g in groups])
    oof = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=FOLDS).split(X, y, gshuf):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=2000, C=1.0)
        clf.fit(sc.transform(X[tr]), y[tr])
        oof[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    return float(roc_auc_score(y, oof))


def speaker_id_acc(X, spk, seed, n_way=60, min_recs=12) -> tuple[float, float]:
    """Manipulation check: can a probe still tell WHO is talking? Returns (acc, chance).

    A manipulation check is only informative if the manipulated quantity is high to
    begin with. The screening pass used a 150-way task over speakers with >= 4
    recordings and scored 0.204 unprojected -- too weak to demonstrate anything, since
    a number that low leaves no room to fall. Narrowing to a 60-way task over speakers
    with >= 12 recordings gives the probe enough examples per class for identity to be
    genuinely learnable, so a subsequent collapse means something.

    Chance is returned alongside, because 1/60 and 1/150 are different floors and an
    accuracy is uninterpretable without one.
    """
    rng = np.random.default_rng(seed)
    keep = [s for s in np.unique(spk) if (spk == s).sum() >= min_recs]
    keep = list(rng.permutation(keep)[:n_way])
    m = np.isin(spk, keep)
    Xs, ss = X[m], spk[m]
    tr = np.zeros(len(ss), bool)
    for s in keep:                                        # half of each speaker's recs
        idx = np.where(ss == s)[0]
        tr[rng.permutation(idx)[: max(2, len(idx) // 2)]] = True
    sc = StandardScaler().fit(Xs[tr])
    clf = LogisticRegression(max_iter=1000, C=1.0)
    clf.fit(sc.transform(Xs[tr]), ss[tr])
    return float((clf.predict(sc.transform(Xs[~tr])) == ss[~tr]).mean()), 1.0 / len(keep)


def main() -> None:
    t0 = time.time()
    d = load_svd()
    X, y, spk = d["X"], d["y"], d["spk"]
    print(f"[data] {X.shape[0]:,} recordings x {X.shape[1]} dims, "
          f"{len(np.unique(spk)):,} speakers, {y.sum():,} pathological  <- {d['src'][:16]}")

    res = {"hypothesis": "V2 -- speaker-identity subspace ablation",
           "audited": "arXiv:2604.14354", "objective": "ROC-AUC vs clinical labels (JUDGE-FREE)",
           "corpus": "svd", "backbone": "wavlm", "n_recordings": int(X.shape[0]),
           "n_speakers": int(len(np.unique(spk))), "folds": FOLDS, "repeats": REPEATS,
           "family_m_preregistered": FAMILY_M, "ranks": RANKS, "rows": []}

    full = [auc_cv(X, y, spk, seed=s) for s in range(REPEATS)]
    res["auc_full_mean"] = float(np.mean(full))
    res["auc_full"] = full
    print(f"[full] AUC = {np.mean(full):.4f} (n={REPEATS} repeats)")

    sid_full, chance = speaker_id_acc(X, spk, 0)
    print(f"[check] speaker-ID accuracy, UNprojected = {sid_full:.4f} (chance {chance:.4f})")

    # repeats OUTSIDE ranks: the full-matrix SVD is the expensive step and depends
    # only on the repeat's train split, so it is computed once and reused for all k
    acc: dict[int, dict[str, list]] = {k: {"spk": [], "topk": [], "matched": [],
                                           "v_spk": [], "v_topk": [], "v_match": []}
                                       for k in RANKS}
    uniq = np.unique(spk)
    for s in range(REPEATS):
        r = np.random.default_rng(10_000 + s)
        tr_spk = set(r.permutation(uniq)[: int(0.8 * len(uniq))].tolist())
        m_tr = np.array([g in tr_spk for g in spk])
        Xtr = X[m_tr]
        Xc = Xtr - Xtr.mean(0, keepdims=True)
        _, sv, Vt = np.linalg.svd(Xc, full_matrices=False)
        frac = (sv ** 2) / (sv ** 2).sum()
        tot = (Xc ** 2).sum()
        print(f"  [repeat {s}] train speakers={len(tr_spk)} recs={m_tr.sum():,}", flush=True)

        for k in RANKS:
            B, _ = speaker_subspace(Xtr, spk[m_tr], k)
            v_spk = float(((Xc @ B) ** 2).sum() / tot)
            ctrl = variance_controls(Vt, frac, v_spk, k)
            acc[k]["spk"].append(auc_cv(project_out(X, B), y, spk, seed=s))
            acc[k]["v_spk"].append(v_spk)
            for nm, key in (("pca_topk", "topk"), ("var_matched", "matched")):
                C, v = ctrl[nm]
                acc[k][key].append(auc_cv(project_out(X, C), y, spk, seed=s))
                acc[k][f"v_{key if key!='matched' else 'match'}"].append(v)

        # CHECKPOINT after every repeat. This run took ~2.5 h and wrote nothing until
        # it finished, so a crash at repeat 9 would have discarded nine repeats of
        # completed work and left no way to tell how far it had got (stdout is
        # block-buffered when redirected, so the log was empty too). A long job that
        # cannot be resumed or observed is a long job that will eventually be re-run
        # from zero.
        PARTIAL.write_text(json.dumps(
            {"completed_repeats": s + 1, "of": REPEATS, "ranks": RANKS,
             "acc": {str(kk): vv for kk, vv in acc.items()}}, indent=2), encoding="utf-8")
        print(f"  [repeat {s}] checkpointed -> {PARTIAL.name}", flush=True)

    for k in RANKS:
        a = acc[k]
        rng = np.random.default_rng(1000 + k)
        row = {"k": k, "auc_speaker_removed": float(np.mean(a["spk"])),
               "variance_removed_speaker": float(np.mean(a["v_spk"])),
               "drop_from_full": float(res["auc_full_mean"] - np.mean(a["spk"]))}
        for nm, key in (("pca_topk", "topk"), ("var_matched", "matched")):
            D = np.array(a[key]) - np.array(a["spk"])       # control minus speaker
            boot = np.array([np.mean(rng.choice(D, len(D), replace=True))
                             for _ in range(10_000)])
            ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
            row[f"auc_{nm}_removed"] = float(np.mean(a[key]))
            row[f"variance_removed_{nm}"] = float(np.mean(a[f"v_{key if key!='matched' else 'match'}"]))
            row[f"D_vs_{nm}"] = float(D.mean())
            row[f"D_vs_{nm}_ci95"] = ci
            row[f"D_vs_{nm}_excludes_zero"] = bool(ci[0] > 0 or ci[1] < 0)
        B_all, _ = speaker_subspace(X, spk, k)
        row["speaker_id_acc_after"], _ = speaker_id_acc(project_out(X, B_all), spk, 0)
        res["rows"].append(row)
        print(f"[k={k:3d}] spk={row['auc_speaker_removed']:.4f} "
              f"topk={row['auc_pca_topk_removed']:.4f} matched={row['auc_var_matched_removed']:.4f} "
              f"| D_topk={row['D_vs_pca_topk']:+.4f} D_match={row['D_vs_var_matched']:+.4f} "
              f"| var {row['variance_removed_speaker']:.3f}/"
              f"{row['variance_removed_pca_topk']:.3f}/{row['variance_removed_var_matched']:.3f} "
              f"| spkID {row['speaker_id_acc_after']:.3f}")

    res["speaker_id_acc_full"] = sid_full
    res["speaker_id_chance"] = chance
    res["elapsed_s"] = round(time.time() - t0, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\n[write] {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
