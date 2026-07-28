"""run_v7_silence_shortcut.py -- V7: does the Clever-Hans silence shortcut generalise?

PRE-REGISTERED IN `IDEA_TABLE.md` BEFORE THIS RUN.

CLAIM
  Non-phonatory signal alone (silence/pause structure, recording-level duration and
  intensity statistics) achieves a substantial fraction of headline performance on
  voice-health corpora OUTSIDE the one where the effect was first documented.

AUDITED CLAIM
  Liu, Feng, Yuan, Ling, Interspeech 2024, "Clever Hans Effect Found in Automatic
  Detection of Alzheimer's Disease through Speech" (arXiv:2406.07410): near-100% AD
  detection from SILENT SEGMENTS ALONE on the Pitt corpus, dropping to ~80% elsewhere.
  The audited proposition is the implicit assumption that this is Pitt-specific. This
  hypothesis therefore deliberately targets corpora that have NOT been checked -- Pitt
  itself is DUA-gated for us, and re-deriving a known Pitt result would be redundant.

FALSIFIER
  If `silence_only` AND `duration+intensity_only` both score < 0.60 AUC on ALL of SVD,
  Coswara and COUGHVID under speaker-disjoint splits, the generalisation claim is
  falsified and the shortcut is confirmed Pitt-specific for this corpus set.

PREDICTED (before the run)
  silence_only in [0.55, 0.70] on Coswara (crowd-recorded, heterogeneous protocol) and
  in [0.50, 0.60] on SVD (controlled studio protocol, sustained vowels) -- i.e. the
  shortcut is predicted to scale with ACQUISITION HETEROGENEITY, not with disease.
  That is the falsifiable content: if it instead scales with disease severity or is
  flat across protocols, the mechanism proposed here is wrong.

RIGOR
  m = 6 (3 corpora x 2 shortcut feature sets) pre-registered; n = 10 ->
  min attainable paired p = 0.001953 <= 0.05/6 = 0.008333.

NOTE ON WHAT A "SHORTCUT" MEANS HERE
  These features contain NO phonation. If a classifier reaches high AUC from how long
  someone recorded and how much of it was silence, it has learned the recording
  protocol, not the patient. That is why this doubles as the AUC_conf_max battery in
  COMPOSITE.md -- a headline model must beat the best of these, not merely chance.

JUDGE-FREE. Objective is ROC-AUC against ground-truth clinical labels.

Usage:  python scripts/run_v7_silence_shortcut.py
        V7_REPEATS=3 python scripts/...          # quick screening pass
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
REPEATS = int(os.environ.get("V7_REPEATS", "10"))
FOLDS = int(os.environ.get("V7_FOLDS", "5"))
WORKERS = int(os.environ.get("V7_WORKERS", "6"))
FAMILY_M = 6           # pre-registered
OUT = ROOT / "autoresearch_results" / "V7_silence_shortcut.json"
SIL_CACHE = ROOT / "cache" / "silence"


def silence_features(path: str) -> list[float]:
    """Energy-VAD pause statistics for one recording. NO phonatory content.

    Deliberately crude and threshold-based rather than a learned VAD: the point is to
    show what a trivially-available signal buys, so a sophisticated detector would
    overstate the shortcut's accessibility. Threshold is relative to the file's own
    peak, so absolute gain differences between corpora do not drive it.
    """
    import soundfile as sf

    try:
        x, sr = sf.read(path, dtype="float32", always_2d=False)
    except Exception:
        return [np.nan] * 7
    if x.ndim > 1:
        x = x.mean(1)
    if len(x) < sr // 10:
        return [np.nan] * 7

    win = max(1, sr // 100)                       # 10 ms frames
    n = len(x) // win
    if n < 3:
        return [np.nan] * 7
    frames = x[: n * win].reshape(n, win)
    energy = np.sqrt((frames ** 2).mean(1) + 1e-12)
    thresh = 0.10 * energy.max()                  # relative to this file's own peak
    speech = energy > thresh

    sil = ~speech
    # run-lengths of silence
    runs, cur = [], 0
    for s in sil:
        if s:
            cur += 1
        elif cur:
            runs.append(cur); cur = 0
    if cur:
        runs.append(cur)
    runs_s = np.array(runs, dtype=float) * (win / sr) if runs else np.array([0.0])

    return [
        float(sil.mean()),                        # silence ratio
        float(len(runs)),                         # number of pauses
        float(runs_s.mean()),                     # mean pause length (s)
        float(runs_s.max()),                      # longest pause (s)
        float(np.log1p(len(x) / sr)),             # log duration
        float(speech.sum() * win / sr),           # total speech time (s)
        float(np.diff(speech.astype(int)).__abs__().sum()),  # speech/silence transitions
    ]


def build_silence(corpus: str) -> dict | None:
    """Compute (or load) silence features for every decoded recording of a corpus."""
    man = ROOT / "data" / "interim" / corpus / "manifest.csv"
    if not man.exists():
        return None
    import pandas as pd

    df = pd.read_csv(man).drop_duplicates("path")
    SIL_CACHE.mkdir(parents=True, exist_ok=True)
    cache = SIL_CACHE / f"{corpus}.npz"
    if cache.exists():
        d = np.load(cache, allow_pickle=True)
        print(f"[{corpus}] silence features loaded from cache: {d['X'].shape}", flush=True)
        return {"X": d["X"], "spk": d["spk"], "y": d["y"]}

    paths = [str(ROOT / p) for p in df["path"]]
    print(f"[{corpus}] computing silence features for {len(paths):,} files "
          f"({WORKERS} workers)...", flush=True)
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        feats = list(ex.map(silence_features, paths, chunksize=64))
    X = np.array(feats, dtype=np.float64)
    ok = ~np.isnan(X).any(1)
    X, sub = X[ok], df[ok]
    y = (sub["label"].values != "healthy").astype(int)
    spk = sub["speaker_id"].values
    np.savez_compressed(cache, X=X, spk=spk, y=y)
    print(f"[{corpus}] silence features: {X.shape} ({(~ok).sum()} unreadable)", flush=True)
    return {"X": X, "spk": spk, "y": y}


def build_dur_int(corpus: str) -> dict | None:
    """duration + intensity only, straight from the cached embedding npz metadata."""
    cands = sorted(glob.glob(str(ROOT / f"cache/embeddings/wavlm/{corpus}/*.npz")),
                   key=lambda p: Path(p).stat().st_size)
    if not cands:
        return None
    d = np.load(cands[-1], allow_pickle=True)
    X = np.column_stack([d["duration_s"].astype(float), d["rms"].astype(float),
                         np.log1p(d["duration_s"].astype(float))])
    return {"X": X, "spk": d["speaker_ids"], "y": (d["labels"] != "healthy").astype(int)}


def auc_cv(X, y, groups, seed) -> float:
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    perm = {s: i for i, s in enumerate(rng.permutation(uniq))}
    g = np.array([perm[v] for v in groups])
    oof = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=FOLDS).split(X, y, g):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(X[tr]), y[tr])
        oof[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    return float(roc_auc_score(y, oof))


def main() -> None:
    t0 = time.time()
    res = {"hypothesis": "V7 -- Clever-Hans silence shortcut beyond Pitt",
           "audited": "arXiv:2406.07410", "objective": "ROC-AUC (JUDGE-FREE)",
           "repeats": REPEATS, "folds": FOLDS,
           "family_m_preregistered": FAMILY_M, "cells": []}

    for corpus in ("svd", "coswara", "coughvid"):
        for name, builder in (("silence_only", build_silence),
                              ("duration_intensity_only", build_dur_int)):
            try:
                d = builder(corpus)
            except Exception as exc:                       # noqa: BLE001
                d = None
                print(f"[skip] {corpus}/{name}: {type(exc).__name__}: {exc}", flush=True)
            if d is None or len(np.unique(d["y"])) < 2 or len(np.unique(d["spk"])) < FOLDS * 2:
                why = ("no data" if d is None else
                       f"{len(np.unique(d['spk']))} speakers / "
                       f"{len(np.unique(d['y']))} classes")
                res["cells"].append({"corpus": corpus, "features": name,
                                     "status": f"NOT RUN -- {why}"})
                print(f"[skip] {corpus}/{name}: {why}", flush=True)
                continue

            aucs = [auc_cv(d["X"], d["y"], d["spk"], s) for s in range(REPEATS)]
            rng = np.random.default_rng(0)
            boot = np.array([np.mean(rng.choice(aucs, len(aucs), replace=True))
                             for _ in range(10_000)])
            ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
            # directionless: a shortcut that predicts the WRONG way is still a shortcut
            m = float(np.mean(aucs))
            cell = {"corpus": corpus, "features": name, "status": "RUN",
                    "n_recordings": int(len(d["y"])),
                    "n_speakers": int(len(np.unique(d["spk"]))),
                    "auc": m, "auc_ci95": ci,
                    "auc_directionless": float(max(m, 1 - m)),
                    "clears_0.60": bool(max(m, 1 - m) >= 0.60)}
            res["cells"].append(cell)
            print(f"[{corpus}/{name}] AUC={m:.4f} (directionless "
                  f"{cell['auc_directionless']:.4f}) CI=[{ci[0]:.4f},{ci[1]:.4f}] "
                  f">=0.60: {cell['clears_0.60']}", flush=True)

    run = [c for c in res["cells"] if c.get("status") == "RUN"]
    res["cells_run"] = len(run)
    # the falsifier, evaluated mechanically rather than by eye
    res["all_below_0.60"] = bool(run) and all(not c["clears_0.60"] for c in run)
    res["falsifier_fully_evaluable"] = len(run) == FAMILY_M
    res["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\n[V7] {len(run)}/{FAMILY_M} cells run; all below 0.60: "
          f"{res['all_below_0.60']}; falsifier fully evaluable: "
          f"{res['falsifier_fully_evaluable']}")
    print(f"[write] {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
