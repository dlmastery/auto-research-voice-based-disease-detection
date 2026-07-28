"""extract_egemaps_resumable.py -- eGeMAPS extraction that survives being killed.

WHY THIS EXISTS
  The standard extractor computes every recording and writes ONE npz at the end. On
  this host long background jobs get reaped, and it has now happened three times:
  COUGHVID WavLM died at 1,152/13,535, and full-corpus SVD eGeMAPS died at
  21,200/28,509 -- 74% of the work, discarded, with RAM healthy at the time. Each
  retry starts from zero, so the job can never finish no matter how many times it runs.

  This is the same all-or-nothing defect already fixed in the V2 runner, and it is the
  reason `fetch_svd_resumable.py` exists for downloads. Compute deserves the same
  treatment as bandwidth: work that has been done should not be thrown away because
  the process that did it was interrupted.

HOW
  Features are appended to a shard file every CHUNK recordings. On restart, already-
  extracted paths are skipped. Re-running repeatedly makes progress until complete;
  a final pass merges the shards into the cache layout the loaders expect.

Usage:
  python scripts/extract_egemaps_resumable.py --corpus svd
  python scripts/extract_egemaps_resumable.py --corpus svd --merge   # when complete
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHARDS = ROOT / "cache" / "egemaps_shards"
CHUNK = int(__import__("os").environ.get("EGE_CHUNK", "500"))


def feats(path: str) -> np.ndarray:
    """88 eGeMAPSv02 functionals for one file, or NaNs if unreadable."""
    import opensmile

    global _SMILE
    try:
        _SMILE
    except NameError:
        _SMILE = opensmile.Smile(feature_set=opensmile.FeatureSet.eGeMAPSv02,
                                 feature_level=opensmile.FeatureLevel.Functionals)
    try:
        return _SMILE.process_file(path).to_numpy()[0].astype(np.float32)
    except Exception:                                  # noqa: BLE001
        return np.full(88, np.nan, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="svd")
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()

    man = ROOT / "data" / "interim" / a.corpus / "manifest.csv"
    if not man.exists():
        sys.exit(f"FATAL: {man} missing")
    df = pd.read_csv(man).drop_duplicates("path").reset_index(drop=True)
    SHARDS.mkdir(parents=True, exist_ok=True)
    done_file = SHARDS / f"{a.corpus}_done.json"

    done: dict[str, list] = json.loads(done_file.read_text()) if done_file.exists() else {}
    todo = [p for p in df["path"] if p not in done]
    print(f"[{a.corpus}] {len(done):,} already extracted, {len(todo):,} remaining "
          f"of {len(df):,}", flush=True)

    if not a.merge and todo:
        t0 = time.time()
        for i in range(0, len(todo), CHUNK):
            batch = todo[i: i + CHUNK]
            for p in batch:
                done[p] = feats(str(ROOT / p)).tolist()
            done_file.write_text(json.dumps(done))     # CHECKPOINT every chunk
            n = len(done)
            rate = (n - (len(df) - len(todo))) / max(1e-9, time.time() - t0)
            print(f"  [{n:,}/{len(df):,}] checkpointed  ({rate:.1f} files/s)", flush=True)

    if len(done) < len(df) and not a.merge:
        print(f"[{a.corpus}] INCOMPLETE -- {len(df) - len(done):,} left. "
              f"Re-run this script to continue; nothing is lost.")
        return

    # merge into the cache layout the V1/V6 loaders already understand
    keep = df[df["path"].isin(done)].reset_index(drop=True)
    X = np.array([done[p] for p in keep["path"]], dtype=np.float32)
    ok = ~np.isnan(X).any(1)
    out = ROOT / "cache" / "embeddings" / "egemaps" / a.corpus
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "resumable_fullcorpus.npz"
    np.savez_compressed(
        dest, X=X[ok],
        recording_ids=keep.loc[ok, "path"].str.split("/").str[-1].str.replace(".wav", "",
                                                                              regex=False).values,
        speaker_ids=keep.loc[ok, "speaker_id"].values,
        labels=keep.loc[ok, "label"].values, sex=keep.loc[ok, "sex"].values,
        age=keep.loc[ok, "age"].astype(np.float32).values,
        duration_s=keep.loc[ok, "duration_s"].astype(np.float32).values,
        rms=np.zeros(int(ok.sum()), dtype=np.float32),
        backbone="egemaps", pooling="functionals")
    print(f"[merge] {dest}  X={X[ok].shape}  ({(~ok).sum()} unreadable dropped)")


if __name__ == "__main__":
    main()
