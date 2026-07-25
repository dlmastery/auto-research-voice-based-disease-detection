"""Fetch the Saarbruecken Voice Database (SVD).

KEY FINDING (2026-07-25): SVD does **not** need to be scraped out of the web
interface. ``stimmdb.coli.uni-saarland.de`` is now a Next.js SPA whose own
"complete dataset is available for download here" link points at an **open
Zenodo record**:

    https://zenodo.org/records/16874898   (DOI 10.5281/zenodo.16874898)
    concept DOI 10.5281/zenodo.16258834   -> always resolves to the latest version

That record is ``access_right: open``, licensed **CC-BY-4.0**, and holds 73
files / 38.06 GB. So the whole corpus is a plain authenticated-free HTTP fetch.
``github.com/rijulg/svd-downloader`` (the scraper the survey pointed at) is
obsolete for this purpose.

Layout of the Zenodo record
---------------------------
* ``data.zip``      (17.88 GB) - the complete corpus in one archive.
* ``healthy.zip``   (6.02 GB)  - the healthy/control speakers.
* 71 x ``<Pathology>.zip``     - one archive per pathology (German label),
  ranging from 5.5 MB (``Morbus Parkinson``) to 1.93 GB
  (``Hyperfunktionelle Dysphonie``).

``data.zip`` and the per-class zips are **redundant encodings of the same
corpus**: take *either* ``data.zip`` *or* {healthy.zip + the pathology zips},
not both. The per-class zips are what you want for class-balanced work, and
they make a small pilot possible.

Speaker metadata
----------------
The per-speaker table is served separately by the SPA at
``/data/voice_data.csv`` and is **not** in the Zenodo record. It is the file
that makes speaker-disjoint splitting possible (``SprecherID`` column), so this
script always fetches it. 167 KB, 2,225 session rows.

Audio format
------------
The archives contain Kay/CSL ``.nsp`` files (sound pressure + EGG channel), not
WAV. Convert with ``github.com/UMEssen/stimmdatenbank-converter`` (linked from
the Zenodo description).

Usage
-----
    python scripts/fetch_svd.py --metadata-only   # 167 KB, always do this first
    python scripts/fetch_svd.py --pilot           # metadata + ~6 smallest zips
    python scripts/fetch_svd.py --list            # show the file table, fetch nothing
    python scripts/fetch_svd.py --files healthy.zip "Morbus Parkinson.zip"
    python scripts/fetch_svd.py --all             # 38 GB - both encodings, rarely what you want
    python scripts/fetch_svd.py --per-class       # healthy.zip + all 71 pathology zips (~20 GB)
"""

from __future__ import annotations

import argparse
import json
import sys

from _download import download, human, raw_dir, session

RECORD_ID = "16874898"
CONCEPT_DOI = "10.5281/zenodo.16258834"
RECORD_DOI = "10.5281/zenodo.16874898"
ZENODO_API = f"https://zenodo.org/api/records/{RECORD_ID}"
METADATA_CSV = "https://stimmdb.coli.uni-saarland.de/data/voice_data.csv"

# The two redundant "whole corpus" archives; excluded from --per-class.
BULK = {"data.zip"}
HEALTHY = "healthy.zip"


def fetch_record(sess):
    r = sess.get(ZENODO_API, timeout=90)
    r.raise_for_status()
    return r.json()


def file_table(record):
    """[(key, size, url, md5), ...] sorted small -> large."""
    out = []
    for f in record["files"]:
        out.append((
            f["key"],
            f["size"],
            f["links"]["self"],
            (f.get("checksum") or "").replace("md5:", "") or None,
        ))
    return sorted(out, key=lambda x: x[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--list", action="store_true", help="print the file table and exit")
    g.add_argument("--metadata-only", action="store_true",
                   help="fetch only voice_data.csv (167 KB)")
    g.add_argument("--pilot", action="store_true",
                   help="metadata + the N smallest pathology zips (proves the path)")
    g.add_argument("--per-class", action="store_true",
                   help="healthy.zip + all 71 pathology zips (~20 GB); skips data.zip")
    g.add_argument("--all", action="store_true", help="every file in the record (38 GB)")
    g.add_argument("--files", nargs="+", metavar="KEY", help="explicit file keys to fetch")
    ap.add_argument("--pilot-n", type=int, default=6,
                    help="how many of the smallest zips --pilot grabs (default 6)")
    ap.add_argument("--sleep", type=float, default=2.0,
                    help="seconds to pause between files (default 2)")
    args = ap.parse_args()

    dest = raw_dir("svd")
    sess = session()

    print(f"SVD  Zenodo record {RECORD_ID}  (DOI {RECORD_DOI}, concept {CONCEPT_DOI})")
    record = fetch_record(sess)
    files = file_table(record)
    total = sum(s for _, s, _, _ in files)
    lic = (record["metadata"].get("license") or {}).get("id")
    print(f"  title:   {record['metadata']['title']}")
    print(f"  license: {lic}   access: {record['metadata'].get('access_right')}")
    print(f"  files:   {len(files)}   total: {human(total)}")

    # Always record provenance next to the data.
    (dest / "zenodo_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

    if args.list:
        for k, s, _, _ in files:
            print(f"  {human(s):>10}  {k}")
        return 0

    # ---- metadata CSV (the speaker table) ----
    print("\n[1/2] speaker metadata (voice_data.csv)")
    download(METADATA_CSV, dest / "voice_data.csv", sess=sess, sleep=args.sleep)
    if args.metadata_only:
        print("\nmetadata-only: done.")
        return 0

    # ---- pick the audio archives ----
    if args.pilot:
        chosen = [f for f in files if f[0] not in BULK and f[0] != HEALTHY][: args.pilot_n]
        label = f"pilot ({args.pilot_n} smallest pathology zips)"
    elif args.per_class:
        chosen = [f for f in files if f[0] not in BULK]
        label = "per-class (healthy + all pathologies)"
    elif args.all:
        chosen = files
        label = "ALL (both redundant encodings)"
    elif args.files:
        want = set(args.files)
        chosen = [f for f in files if f[0] in want]
        missing = want - {f[0] for f in chosen}
        if missing:
            print(f"  [error] no such file(s) in record: {sorted(missing)}", file=sys.stderr)
            return 1
        label = "explicit selection"
    else:
        ap.print_help()
        print("\n[error] pick one of --list/--metadata-only/--pilot/--per-class/--all/--files",
              file=sys.stderr)
        return 2

    want_bytes = sum(s for _, s, _, _ in chosen)
    print(f"\n[2/2] audio archives - {label}: {len(chosen)} file(s), {human(want_bytes)}")
    for i, (key, size, url, md5) in enumerate(chosen, 1):
        print(f"  ({i}/{len(chosen)}) {key}  {human(size)}")
        download(url, dest / key, sess=sess, expect_size=size, expect_md5=md5,
                 sleep=args.sleep)

    print(f"\nDone. Files in {dest}")
    print("NOTE: archives hold Kay/CSL .nsp files (audio + EGG), not WAV.")
    print("      Converter: https://github.com/UMEssen/stimmdatenbank-converter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
