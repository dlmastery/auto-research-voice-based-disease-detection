"""fetch_svd_resumable.py — RESUMABLE download of the SVD corpus from Zenodo.

Why this exists: the first downloader used `urllib.request.urlretrieve`, which has no
resume. The Saarbrueecken record's final archive is ~22 GB, so every interruption threw
away all partial progress and restarted from zero — it could never finish. This version
streams to a `.part` file and, on restart, sends an HTTP `Range:` header to continue
from the byte it reached.

Also ASCII-safe on stdout: the record contains German pathology filenames (umlauts) and
the Windows cp1252 console raises UnicodeEncodeError when printing them, which killed an
earlier run outright.

Usage:
    PYTHONIOENCODING=utf-8 python scripts/fetch_svd_resumable.py
    PYTHONIOENCODING=utf-8 python scripts/fetch_svd_resumable.py --only-missing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:  # noqa: BLE001
    pass

RECORD = "https://zenodo.org/api/records/16874898"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "svd_full"


def say(msg: str) -> None:
    """ASCII-only stdout — the console cannot encode the corpus's umlauts."""
    sys.stdout.write(msg.encode("ascii", "replace").decode("ascii") + "\n")
    sys.stdout.flush()


def fetch_one(url: str, dest: Path, size: int, *, chunk: int = 1 << 20) -> bool:
    """Stream `url` to `dest`, resuming from a `.part` file if one exists."""
    if dest.exists() and dest.stat().st_size == size:
        return True
    part = dest.with_suffix(dest.suffix + ".part")
    have = part.stat().st_size if part.exists() else 0
    if have > size:                      # corrupt partial — start over
        part.unlink()
        have = 0

    req = urllib.request.Request(url, headers={"User-Agent": "research-audit/1.0"})
    if have:
        req.add_header("Range", f"bytes={have}-")

    t0, last = time.time(), have
    with urllib.request.urlopen(req, timeout=120) as r:
        # 200 means the server ignored Range: restart the file rather than corrupt it
        mode = "ab" if (have and r.status == 206) else "wb"
        if mode == "wb":
            have = 0
        with open(part, mode) as fh:
            while True:
                buf = r.read(chunk)
                if not buf:
                    break
                fh.write(buf)
                have += len(buf)
                if have - last > (256 << 20):        # progress every 256 MB
                    el = time.time() - t0
                    rate = (have - (last if el else have)) / max(el, 1) / 1e6
                    say(f"    {have/1e9:.1f}/{size/1e9:.1f} GB  {have/size*100:.0f}%  {rate:.0f} MB/s")
                    last = have
    if part.stat().st_size == size:
        part.replace(dest)
        return True
    say(f"    incomplete: {part.stat().st_size}/{size} — rerun to resume")
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-missing", action="store_true")
    args = ap.parse_args()

    rec = json.load(urllib.request.urlopen(RECORD, timeout=60))
    files = rec.get("files", [])
    total = sum(f.get("size", 0) for f in files)
    OUT.mkdir(parents=True, exist_ok=True)

    have = sum(p.stat().st_size for p in OUT.glob("*") if p.is_file() and not p.name.endswith(".part"))
    say(f"record: {len(files)} files / {total/1e9:.1f} GB   already complete: {have/1e9:.1f} GB")

    # smallest first so the cheap ones bank quickly, big archive last
    ok = 0
    for i, f in enumerate(sorted(files, key=lambda x: x.get("size", 0)), 1):
        dest = OUT / f["key"]
        size = f.get("size", 0)
        if dest.exists() and dest.stat().st_size == size:
            ok += 1
            continue
        say(f"[{i}/{len(files)}] {size/1e9:.2f} GB  (resuming if partial)")
        try:
            if fetch_one(f["links"]["self"], dest, size):
                ok += 1
                say(f"    done ({ok}/{len(files)} complete)")
        except Exception as exc:  # noqa: BLE001
            say(f"    FAILED {type(exc).__name__} — partial kept, rerun to resume")

    done = sum(p.stat().st_size for p in OUT.glob("*") if p.is_file() and not p.name.endswith(".part"))
    say(f"COMPLETE {ok}/{len(files)} files, {done/1e9:.1f}/{total/1e9:.1f} GB")


if __name__ == "__main__":
    main()
