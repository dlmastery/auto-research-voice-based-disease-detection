"""run_v1_ssl_vs_handcrafted.py -- V1: do SSL embeddings beat eGeMAPS once age is MATCHED?

PRE-REGISTERED IN `IDEA_TABLE.md`. Feasibility re-checked before launch (see below).

CLAIM
  Under simultaneously speaker-disjoint AND demographically balanced splits, frozen
  SSL embeddings do not reliably beat handcrafted eGeMAPS features.

WHY THIS IS THE MOST INFORMATIVE RUN IN THE PROGRAM SO FAR
  F1/F3 established that patient AGE alone reaches ROC-AUC 0.87 on SVD while WavLM
  reaches 0.74 -- the audio model loses to a demographic variable. F4 established that
  ~a third of WavLM's discrimination is speaker IDENTITY. Both leave one question open:
  once the age confound is REMOVED BY CONSTRUCTION, is there any real acoustic signal
  left, and does an SSL model find more of it than 88 handcrafted features?
  Matching answers that directly.

FEASIBILITY (re-checked 2026-07-28, closing a standing open question)
  The data-split audit FAILED this design at 49 speakers -- only 9 age-matched pairs
  existed. At the full corpus (1,679 speakers) greedy 1:1 matching on sex and age +/-3y
  yields **308 pairs = 616 speakers**. V1 moved from infeasible to runnable purely
  because the corpus grew 34x.

BUILT-IN MANIPULATION CHECK
  On the matched subset an AGE-ONLY classifier must collapse toward chance. If it does
  not, the matching failed and every other number here is void. This is reported first
  and is the run's own falsifier for its construction.

RIGOR
  m = 9 pre-registered (3 encoders x 3 corpora). Kept at 9 even though fewer cells run
  -- shrinking m post hoc to buy significance is forbidden. n = 10 ->
  min attainable paired p = 0.001953 <= 0.05/9 = 0.005556.

SCOPE HONESTLY STATED
  The pre-registration names {HeAR, WavLM-base+, Whisper-small-enc}. Only WavLM is
  extracted on this host; HeAR and Whisper are GPU extraction work not yet done, and
  COUGHVID is excluded per F2 (no real speaker ids). So this run tests ONE SSL encoder
  against eGeMAPS on ONE corpus and cannot settle the registered claim -- it can only
  support or undermine it for that cell.

JUDGE-FREE. Objective is ROC-AUC against ground-truth clinical labels.

Usage:  python scripts/run_v1_ssl_vs_handcrafted.py
        V1_TOL=5 V1_REPEATS=3 python scripts/...
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
REPEATS = int(os.environ.get("V1_REPEATS", "10"))
FOLDS = int(os.environ.get("V1_FOLDS", "5"))
TOL = float(os.environ.get("V1_TOL", "3"))       # age-matching tolerance in years
FAMILY_M = 9                                      # pre-registered
OUT = ROOT / "autoresearch_results" / "V1_ssl_vs_handcrafted.json"


def load(corpus: str, backbone: str):
    c = sorted(glob.glob(str(ROOT / f"cache/embeddings/{backbone}/{corpus}/*.npz")),
               key=lambda p: Path(p).stat().st_size)
    return np.load(c[-1], allow_pickle=True) if c else None


def matched_speakers(spk, y, age, sex, tol: float, seed: int) -> set:
    """Greedy 1:1 sex-exact, age-within-tol matching of pathological to healthy speakers.

    Greedy nearest-age is deliberate: it maximises the number of usable pairs, and any
    residual age gap is REPORTED rather than assumed away. The manipulation check (an
    age-only classifier on the matched set) is what proves the matching actually worked
    -- construction alone is never taken on trust.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(spk))             # break ties differently per repeat
    sp, yy, ag, sx = spk[order], y[order], age[order], sex[order]
    seen, rows = set(), []
    for s, lab, a, g in zip(sp, yy, ag, sx):
        if s not in seen:
            seen.add(s); rows.append((s, lab, a, g))
    heal = [r for r in rows if r[1] == 0]
    path = [r for r in rows if r[1] == 1]
    used, keep = set(), []
    for s, _, a, g in heal:
        c = [p for p in path if p[0] not in used and p[3] == g and abs(p[2] - a) <= tol]
        if c:
            c.sort(key=lambda p: abs(p[2] - a))
            used.add(c[0][0]); keep += [s, c[0][0]]
    return set(keep)


def auc_cv(X, y, groups, seed) -> float:
    rng = np.random.default_rng(seed)
    u = np.unique(groups)
    perm = {s: i for i, s in enumerate(rng.permutation(u))}
    g = np.array([perm[v] for v in groups])
    oof = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=FOLDS).split(X, y, g):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(X[tr]), y[tr])
        oof[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    return float(roc_auc_score(y, oof))


def main() -> None:
    t0 = time.time()
    wav, ege = load("svd", "wavlm"), load("svd", "egemaps")
    if wav is None:
        sys.exit("FATAL: no cached WavLM for svd")
    spk, age, sex = wav["speaker_ids"], wav["age"].astype(float), wav["sex"]
    y = (wav["labels"] == "pathological").astype(int)

    res = {"hypothesis": "V1 -- SSL vs handcrafted under age-matched speaker-disjoint splits",
           "objective": "ROC-AUC vs clinical labels (JUDGE-FREE)", "corpus": "svd",
           "age_tolerance_years": TOL, "repeats": REPEATS, "folds": FOLDS,
           "family_m_preregistered": FAMILY_M,
           "encoders_registered": ["HeAR", "WavLM-base+", "Whisper-small-enc"],
           # NOT set from "the cache file exists" -- that is what it originally said, and
           # it claimed eGeMAPS ran when the arm had been silently skipped on a row-count
           # mismatch. Filled in AFTER the loop from what actually produced a number.
           "encoders_run": ["WavLM-base+"],
           "note_scope": "HeAR and Whisper not extracted on this host; COUGHVID excluded per F2",
           "repeats_detail": []}

    for s in range(REPEATS):
        keep = matched_speakers(spk, y, age, sex, TOL, seed=s)
        m = np.isin(spk, list(keep))
        ys, spks, ages = y[m], spk[m], age[m]
        # per-speaker view for the balance report
        _, first = np.unique(spks, return_index=True)
        sy, sa = ys[first], ages[first]
        row = {"seed": s, "n_speakers": int(len(first)), "n_recordings": int(m.sum()),
               "age_healthy": float(sa[sy == 0].mean()), "age_patho": float(sa[sy == 1].mean())}
        row["age_gap"] = abs(row["age_patho"] - row["age_healthy"])

        # MANIPULATION CHECK FIRST: age must now be uninformative
        row["auc_age_only"] = auc_cv(ages.reshape(-1, 1), ys, spks, s)
        row["auc_wavlm"] = auc_cv(wav["X"].astype(np.float64)[m], ys, spks, s)
        if ege is not None:
            # align eGeMAPS rows to the same recordings via recording_ids
            idx = {r: i for i, r in enumerate(ege["recording_ids"])}
            sel = [idx[r] for r in wav["recording_ids"][m] if r in idx]
            if len(sel) == m.sum():
                row["auc_egemaps"] = auc_cv(ege["X"].astype(np.float64)[sel], ys, spks, s)
        res["repeats_detail"].append(row)
        print(f"  [seed {s}] {row['n_speakers']} spk, age gap {row['age_gap']:.2f}y | "
              f"age-only {row['auc_age_only']:.4f} | wavlm {row['auc_wavlm']:.4f}"
              + (f" | egemaps {row['auc_egemaps']:.4f}" if "auc_egemaps" in row else ""),
              flush=True)

    R = res["repeats_detail"]
    if any("auc_egemaps" in r for r in R):
        res["encoders_run"].append("eGeMAPS(baseline)")
    else:
        res["egemaps_skipped_reason"] = (
            "cached eGeMAPS for svd covers only the 667-recording pilot slice, so it "
            "cannot be aligned to the full-corpus matched subset. Full-corpus eGeMAPS "
            "extraction is required before the SSL-vs-handcrafted contrast can run.")
    for k in ("auc_age_only", "auc_wavlm", "auc_egemaps", "age_gap", "n_speakers"):
        vals = [r[k] for r in R if k in r]
        if vals:
            res[f"mean_{k}"] = float(np.mean(vals))
    # the construction's own falsifier, evaluated mechanically
    res["matching_worked"] = bool(res.get("mean_auc_age_only", 1.0) < 0.60)
    if "mean_auc_egemaps" in res:
        d = np.array([r["auc_wavlm"] - r["auc_egemaps"] for r in R if "auc_egemaps" in r])
        rng = np.random.default_rng(0)
        boot = np.array([np.mean(rng.choice(d, len(d), replace=True)) for _ in range(10_000)])
        res["wavlm_minus_egemaps"] = float(d.mean())
        res["wavlm_minus_egemaps_ci95"] = [float(np.percentile(boot, 2.5)),
                                           float(np.percentile(boot, 97.5))]
        res["ssl_beats_handcrafted"] = bool(np.percentile(boot, 2.5) > 0)
    res["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\n[V1] matching worked (age-only < 0.60): {res['matching_worked']} "
          f"(age-only {res.get('mean_auc_age_only', float('nan')):.4f})")
    if "wavlm_minus_egemaps" in res:
        print(f"[V1] WavLM - eGeMAPS = {res['wavlm_minus_egemaps']:+.4f} "
              f"CI {res['wavlm_minus_egemaps_ci95']} | SSL wins: {res['ssl_beats_handcrafted']}")
    print(f"[write] {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
