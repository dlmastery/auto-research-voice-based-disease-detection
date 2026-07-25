"""Fetch the COUGHVID crowdsourced cough dataset from Zenodo.

Record
------
    https://zenodo.org/records/7024894      (version 3.0, published 2021-02-03)
    record DOI  10.5281/zenodo.7024894
    concept DOI 10.5281/zenodo.4048311   -> always resolves to the latest version
    licence     CC-BY-4.0                   access_right: open

NOTE: the survey lists COUGHVID as "~1 GB" and gives concept DOI
``10.5281/zenodo.4048312``. Both are wrong. The record holds a single file,
``public_dataset_v3.zip``, of **2,297,542,075 bytes (2.30 GB)**, and the concept
DOI is ``...4048311``. Verified against the Zenodo API on 2026-07-25.

The archive contains webm/ogg cough audio plus a metadata CSV carrying the
``cough_detected`` confidence, self-reported status, age, gender and geography.

Usage
-----
    python scripts/fetch_coughvid.py --info      # print record metadata, fetch nothing
    python scripts/fetch_coughvid.py             # download the 2.30 GB archive
    python scripts/fetch_coughvid.py --extract   # download + unzip
"""

from __future__ import annotations

import argparse
import json

from _download import download, human, raw_dir, session

RECORD_ID = "7024894"
RECORD_DOI = "10.5281/zenodo.7024894"
CONCEPT_DOI = "10.5281/zenodo.4048311"
ZENODO_API = f"https://zenodo.org/api/records/{RECORD_ID}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--info", action="store_true", help="print record metadata and exit")
    ap.add_argument("--extract", action="store_true", help="unzip after download")
    ap.add_argument("--sleep", type=float, default=2.0)
    args = ap.parse_args()

    dest = raw_dir("coughvid")
    sess = session()

    r = sess.get(ZENODO_API, timeout=90)
    r.raise_for_status()
    rec = r.json()
    meta = rec["metadata"]
    files = rec["files"]
    total = sum(f["size"] for f in files)

    print(f"COUGHVID  Zenodo record {RECORD_ID}")
    print(f"  title:   {meta['title']}")
    print(f"  doi:     {RECORD_DOI}   concept: {CONCEPT_DOI}")
    print(f"  licence: {(meta.get('license') or {}).get('id')}   "
          f"access: {meta.get('access_right')}")
    print(f"  version: {meta.get('version')}   published: {meta.get('publication_date')}")
    print(f"  files:   {len(files)}   total: {human(total)}")
    for f in files:
        print(f"    {human(f['size']):>10}  {f['key']}")

    (dest / "zenodo_record.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")

    if args.info:
        return 0

    print()
    for f in files:
        download(f["links"]["self"], dest / f["key"], sess=sess,
                 expect_size=f["size"],
                 expect_md5=(f.get("checksum") or "").replace("md5:", "") or None,
                 sleep=args.sleep)

    if args.extract:
        import zipfile
        for f in files:
            p = dest / f["key"]
            if p.suffix == ".zip":
                print(f"  [extract] {p.name}")
                with zipfile.ZipFile(p) as zf:
                    zf.extractall(dest)
                print(f"  [extract] {p.name}: done")

    print(f"\nDone. Files in {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
