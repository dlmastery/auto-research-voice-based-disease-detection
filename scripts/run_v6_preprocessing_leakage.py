"""run_v6_preprocessing_leakage.py -- V6: does fitting the scaler before splitting inflate AUC?

PRE-REGISTERED IN `IDEA_TABLE.md` BEFORE THIS RUN.

CLAIM
  The inflation from fitting the scaler/normaliser before splitting varies by an order
  of magnitude across corpora, so "we scaled before splitting but it's a small effect"
  is not defensible on an unmeasured corpus.

AUDITED CLAIM
  "Feature scaling induced data leakage quantification in machine learning-based voice
  pathology detection", Applied Soft Computing (S1568494626007970): 1,000 repetitions
  per configuration; the effect is -0.14 to +0.14 pp on SVD but -8.3 to +7.8 pp on
  VOICED. Leakage can DEGRADE as well as inflate. That is a measurement on handcrafted
  features; the open question is whether it generalises to EMBEDDING features.

FALSIFIER
  If the fit_on_all - fit_per_fold AUC difference has a 95% CI contained within
  +/-0.01 AUC on all corpora for both representations, the "corpus-specific magnitude"
  claim is falsified for this pipeline family and preprocessing scope can be
  de-prioritised as an audit axis.

PREDICTED (before the run)
  Effect < 0.01 AUC on SVD (reproducing the published near-null) and > 0.03 AUC on at
  least one of Coswara/COUGHVID. Sign NOT predicted -- the published result shows both.

RIGOR
  m = 6 (3 corpora x 2 representations) pre-registered; n = 10 ->
  min attainable paired p = 0.001953 <= 0.05/6 = 0.008333. Family size is kept at the
  pre-registered 6 even where fewer cells run.

WHY THIS IS THE HONEST VERSION OF A "FREE" EXPERIMENT
  The two arms differ in EXACTLY one line -- where StandardScaler is fitted. Everything
  else (splits, folds, seeds, model, data) is shared, so the paired difference isolates
  preprocessing scope and nothing else.

JUDGE-FREE. Objective is ROC-AUC against ground-truth clinical labels.

Usage:  python scripts/run_v6_preprocessing_leakage.py
        V6_REPEATS=3 python scripts/...        # quick screening pass
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
REPEATS = int(os.environ.get("V6_REPEATS", "10"))
FOLDS = int(os.environ.get("V6_FOLDS", "5"))
FAMILY_M = 6           # pre-registered; never recomputed from what actually ran
OUT = ROOT / "autoresearch_results" / "V6_preprocessing_leakage.json"


def load_cached(corpus: str, backbone: str) -> dict | None:
    """Largest cached embedding matrix for a (corpus, backbone), or None if absent."""
    cands = sorted(glob.glob(str(ROOT / f"cache/embeddings/{backbone}/{corpus}/*.npz")),
                   key=lambda p: Path(p).stat().st_size)
    if not cands:
        return None
    d = np.load(cands[-1], allow_pickle=True)
    y = (d["labels"] != "healthy").astype(int)     # non-healthy = positive, all corpora
    if len(np.unique(y)) < 2:
        return None
    return {"X": d["X"].astype(np.float64), "spk": d["speaker_ids"], "y": y,
            "src": Path(cands[-1]).name}


def auc_cv(X, y, groups, seed, fit_on_all: bool) -> float:
    """Speaker-disjoint GroupKFold AUC. The ONLY difference between arms is one line.

    fit_on_all=True  -- scaler fitted on the WHOLE matrix before splitting (the leak)
    fit_on_all=False -- scaler fitted on each fold's TRAIN rows only (correct)
    """
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    perm = {s: i for i, s in enumerate(rng.permutation(uniq))}
    gshuf = np.array([perm[g] for g in groups])

    Xg = StandardScaler().fit_transform(X) if fit_on_all else X
    oof = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=FOLDS).split(Xg, y, gshuf):
        if fit_on_all:
            Xtr, Xte = Xg[tr], Xg[te]
        else:
            sc = StandardScaler().fit(Xg[tr])
            Xtr, Xte = sc.transform(Xg[tr]), sc.transform(Xg[te])
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr, y[tr])
        oof[te] = clf.predict_proba(Xte)[:, 1]
    return float(roc_auc_score(y, oof))


def main() -> None:
    t0 = time.time()
    res = {"hypothesis": "V6 -- preprocessing-fit leakage",
           "audited": "Applied Soft Computing S1568494626007970",
           "objective": "ROC-AUC vs clinical labels (JUDGE-FREE)",
           "repeats": REPEATS, "folds": FOLDS,
           "family_m_preregistered": FAMILY_M, "cells": []}

    for corpus in ("svd", "coswara", "coughvid"):
        for backbone in ("wavlm", "egemaps"):
            d = load_cached(corpus, backbone)
            if d is None:
                print(f"[skip] {corpus}/{backbone}: no usable cached matrix", flush=True)
                res["cells"].append({"corpus": corpus, "backbone": backbone,
                                     "status": "NOT RUN -- no cached embeddings"})
                continue
            X, y, spk = d["X"], d["y"], d["spk"]
            if len(np.unique(spk)) < FOLDS * 2:
                print(f"[skip] {corpus}/{backbone}: only {len(np.unique(spk))} speakers",
                      flush=True)
                res["cells"].append({"corpus": corpus, "backbone": backbone,
                                     "status": f"NOT RUN -- {len(np.unique(spk))} speakers"})
                continue

            leak, clean = [], []
            for s in range(REPEATS):
                leak.append(auc_cv(X, y, spk, s, fit_on_all=True))
                clean.append(auc_cv(X, y, spk, s, fit_on_all=False))
            D = np.array(leak) - np.array(clean)
            rng = np.random.default_rng(0)
            boot = np.array([np.mean(rng.choice(D, len(D), replace=True))
                             for _ in range(10_000)])
            ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
            cell = {"corpus": corpus, "backbone": backbone, "status": "RUN",
                    "n_recordings": int(len(y)), "n_speakers": int(len(np.unique(spk))),
                    "auc_fit_on_all": float(np.mean(leak)),
                    "auc_fit_per_fold": float(np.mean(clean)),
                    "delta_mean": float(D.mean()), "delta_ci95": ci,
                    # the falsifier's own test, evaluated mechanically
                    "ci_within_pm_0.01": bool(ci[0] > -0.01 and ci[1] < 0.01)}
            res["cells"].append(cell)
            print(f"[{corpus}/{backbone}] leak={np.mean(leak):.4f} clean={np.mean(clean):.4f} "
                  f"D={D.mean():+.5f} CI=[{ci[0]:+.5f},{ci[1]:+.5f}] "
                  f"within+-0.01={cell['ci_within_pm_0.01']}", flush=True)

    run = [c for c in res["cells"] if c.get("status") == "RUN"]
    res["cells_run"] = len(run)
    res["all_within_pm_0.01"] = bool(run) and all(c["ci_within_pm_0.01"] for c in run)
    res["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\n[V6] {len(run)} cells run; all within +/-0.01: {res['all_within_pm_0.01']}")
    print(f"[write] {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
