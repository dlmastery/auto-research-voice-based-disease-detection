"""Fetch the Coswara COVID-19 respiratory-sound corpus.

WHY NOT ``git clone`` (2026-07-25): the survey says "a few GB"; the repo is
actually **13.00 GB of blobs / 16.75 GB with history**. Two ``git clone``
attempts on this host (a plain one and ``--filter=blob:none --depth 1``) were
both killed mid-transfer - one reaped at ~6 GiB, one died with ``fatal: early
EOF`` - each time leaving an empty working tree and discarding the bytes. git
cannot resume a broken clone, so it is the wrong tool here.

This script fetches the same content over plain HTTP from ``raw.githubusercontent``
one file at a time, which **is** resumable and restart-safe.

Repository layout (github.com/iiscleap/Coswara-Data, branch ``master``)
----------------------------------------------------------------------
* ``combined_data.csv``      (359 KB) - the master participant metadata table.
* ``csv_labels_legend.json`` (1.6 KB) - decodes the categorical columns.
* ``extract_data.py``                 - upstream's shard-reassembly script.
* ``annotations/``           (1.1 MB) - human annotation files.
* ``technical_validation/``  (20 MB)  - validation artefacts.
* 43 x ``YYYYMMDD/`` date directories, each holding
    - ``YYYYMMDD.csv``            - that day's participant metadata, and
    - ``YYYYMMDD.tar.gz.aa``, ``.ab``, ``.ac`` ... - the audio, split into
      ~500 MB shards that must be concatenated before extraction.
  Date dirs run 48 MB (20200911) to 884 MB (20200502); 12.98 GB total.

Reassembling audio: ``cat YYYYMMDD.tar.gz.* > YYYYMMDD.tar.gz && tar -xzf ...``
(or just run upstream's ``extract_data.py``). ``--extract`` does this for you.

Usage
-----
    python scripts/fetch_coswara.py --metadata-only   # ~4 MB, all the labels
    python scripts/fetch_coswara.py --pilot           # metadata + smallest date dir
    python scripts/fetch_coswara.py --dates 20200911 20200505
    python scripts/fetch_coswara.py --audio           # everything, 13 GB
    python scripts/fetch_coswara.py --pilot --extract # + reassemble the shards
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from _download import download, human, raw_dir, session

REPO = "iiscleap/Coswara-Data"
BRANCH = "master"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
TREE_API = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"

TOP_META = ["combined_data.csv", "csv_labels_legend.json", "extract_data.py",
            "README.md", "LICENSE.md"]


def gh_headers() -> dict:
    """Unauthenticated GitHub API is rate-limited per-IP; use a token if one exists."""
    h = {"User-Agent": "auto-research-voice/1.0", "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not tok:
        try:
            tok = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                 text=True, timeout=20).stdout.strip() or None
        except Exception:
            tok = None
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def get_tree(sess):
    r = sess.get(TREE_API, timeout=120, headers=gh_headers())
    if r.status_code == 403:
        print("[error] GitHub API rate-limited. Set GITHUB_TOKEN or run `gh auth login`.",
              file=sys.stderr)
        r.raise_for_status()
    r.raise_for_status()
    j = r.json()
    if j.get("truncated"):
        print("[warn] GitHub truncated the tree listing; some files may be missed",
              file=sys.stderr)
    return [e for e in j["tree"] if e["type"] == "blob"]


def date_dirs(blobs):
    """{'YYYYMMDD': [(path, size), ...]} for the 43 audio date directories."""
    out = defaultdict(list)
    for e in blobs:
        head = e["path"].split("/")[0]
        if len(head) == 8 and head.isdigit():
            out[head].append((e["path"], e.get("size", 0)))
    return out


def extract_date(d: Path, tag: str) -> None:
    """cat the .tar.gz.* shards back together and untar."""
    shards = sorted(d.glob(f"{tag}.tar.gz.*"))
    shards = [s for s in shards if not s.name.endswith(".part")]
    if not shards:
        print(f"  [skip-extract] no shards for {tag}")
        return
    tgz = d / f"{tag}.tar.gz"
    print(f"  [extract] {tag}: joining {len(shards)} shard(s) -> {tgz.name}")
    with open(tgz, "wb") as out:
        for s in shards:
            with open(s, "rb") as fh:
                while chunk := fh.read(1 << 22):
                    out.write(chunk)
    import tarfile
    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(d, filter="data")
    tgz.unlink()  # the shards remain; the joined copy is redundant
    print(f"  [extract] {tag}: done")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--list", action="store_true", help="print the date-dir table and exit")
    g.add_argument("--metadata-only", action="store_true",
                   help="master CSV + legend + all 43 per-date CSVs (~4 MB)")
    g.add_argument("--pilot", action="store_true",
                   help="metadata + the smallest date directory (48 MB)")
    g.add_argument("--dates", nargs="+", metavar="YYYYMMDD", help="specific date dirs")
    g.add_argument("--audio", action="store_true", help="every date directory (13 GB)")
    ap.add_argument("--extract", action="store_true",
                    help="reassemble + untar the shards of each fetched date dir")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    dest = raw_dir("coswara")
    sess = session()

    print(f"Coswara  {REPO}@{BRANCH}")
    blobs = get_tree(sess)
    dd = date_dirs(blobs)
    total = sum(e.get("size", 0) for e in blobs)
    print(f"  blobs: {len(blobs)}   total: {human(total)}   date dirs: {len(dd)}")

    (dest / "github_tree.json").write_text(
        json.dumps([{"path": e["path"], "size": e.get("size", 0)} for e in blobs], indent=2),
        encoding="utf-8")

    if args.list:
        for tag in sorted(dd, key=lambda t: sum(s for _, s in dd[t])):
            sz = sum(s for _, s in dd[tag])
            print(f"  {human(sz):>10}  n={len(dd[tag])}  {tag}")
        return 0

    # ---- metadata: always ----
    print("\n[1/2] metadata")
    by_path = {e["path"]: e.get("size", 0) for e in blobs}
    for name in TOP_META:
        if name in by_path:
            download(RAW + name, dest / name, sess=sess,
                     expect_size=by_path[name], sleep=args.sleep)
    for tag in sorted(dd):
        csv_path = f"{tag}/{tag}.csv"
        if csv_path in by_path:
            download(RAW + csv_path, dest / tag / f"{tag}.csv", sess=sess,
                     expect_size=by_path[csv_path], sleep=0.2)

    if args.metadata_only:
        print("\nmetadata-only: done.")
        return 0

    # ---- audio ----
    if args.pilot:
        chosen = [min(dd, key=lambda t: sum(s for _, s in dd[t]))]
    elif args.dates:
        chosen = list(args.dates)
        bad = [t for t in chosen if t not in dd]
        if bad:
            print(f"[error] no such date dir(s): {bad}", file=sys.stderr)
            return 1
    elif args.audio:
        chosen = sorted(dd)
    else:
        ap.print_help()
        print("\n[error] pick one of --list/--metadata-only/--pilot/--dates/--audio",
              file=sys.stderr)
        return 2

    want = sum(sum(s for _, s in dd[t]) for t in chosen)
    print(f"\n[2/2] audio: {len(chosen)} date dir(s), {human(want)}")
    for tag in chosen:
        for path, size in sorted(dd[tag]):
            if path.endswith(".csv"):
                continue  # already fetched above
            download(RAW + path, dest / path, sess=sess, expect_size=size, sleep=args.sleep)
        if args.extract:
            extract_date(dest / tag, tag)

    print(f"\nDone. Files in {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
