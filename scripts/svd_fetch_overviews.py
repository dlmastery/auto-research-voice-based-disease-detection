"""Fetch the per-archive `overview.csv` from every SVD Zenodo archive via range reads.

Builds the definitive speaker inventory (id, age, sex, pathology) for the whole
Saarbruecken Voice Database without downloading 38 GB of audio. Each archive costs
~4 HTTP range requests.

Output:
    data/raw/svd_meta/overview_<archive>.csv      one per archive
    data/raw/svd_meta/svd_inventory.csv           concatenated, with a pathology column
    autoresearch_results/acquisition/svd_inventory_stats.json
"""

from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from svd_remote_zip import _url, central_directory, extract_member, total_size  # noqa: E402

OUTDIR = REPO / "data" / "raw" / "svd_meta"
STATS = REPO / "autoresearch_results" / "acquisition" / "svd_inventory_stats.json"


def archives() -> list[dict]:
    proc = subprocess.run(
        ["curl", "-sS", "--ssl-no-revoke", "-L", "--max-time", "120",
         "https://zenodo.org/api/records/16874898"],
        capture_output=True, timeout=180,
    )
    rec = json.loads(proc.stdout.decode("utf-8", errors="replace"))
    return [{"key": f["key"], "size": f["size"]} for f in rec["files"]]


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    STATS.parent.mkdir(parents=True, exist_ok=True)

    rows_all: list[dict] = []
    per_archive: dict[str, dict] = {}
    failures: dict[str, str] = {}

    for a in sorted(archives(), key=lambda x: x["size"]):
        key = a["key"]
        # data.zip is the full 17.9 GB mirror of everything else; skip it.
        if key == "data.zip":
            continue
        label = Path(key).stem
        try:
            url = _url(key)
            size = total_size(url)
            entries = central_directory(url, size)
            ov = next((e for e in entries if e["name"].lower().endswith("overview.csv")), None)
            speaker_dirs = sorted({e["name"].split("/")[0] for e in entries
                                   if "/" in e["name"] and e["name"].split("/")[0].isdigit()})
            n_audio = sum(1 for e in entries if e["name"].lower().endswith(".nsp"))

            per_archive[label] = {
                "archive_bytes": size,
                "n_speaker_dirs": len(speaker_dirs),
                "n_nsp_files": n_audio,
                "has_overview_csv": ov is not None,
            }

            if ov is not None:
                data = extract_member(url, ov).decode("utf-8-sig", errors="replace")
                (OUTDIR / f"overview_{label}.csv").write_text(data, encoding="utf-8")
                for r in csv.DictReader(io.StringIO(data), delimiter=";"
                                        if data.count(";") > data.count(",") else ","):
                    r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
                    r["_archive"] = label
                    rows_all.append(r)
            print(f"OK   {label:45s} speakers={len(speaker_dirs):4d} nsp={n_audio:5d}", flush=True)
        except Exception as exc:  # noqa: BLE001
            failures[label] = f"{type(exc).__name__}: {exc}"
            print(f"FAIL {label:45s} {type(exc).__name__}", flush=True)

    if rows_all:
        cols: list[str] = []
        for r in rows_all:
            for k in r:
                if k not in cols:
                    cols.append(k)
        with (OUTDIR / "svd_inventory.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows_all)

    stats = {
        "artifact": "svd_inventory_stats",
        "zenodo_doi": "10.5281/zenodo.16874898",
        "license": "CC-BY-4.0",
        "n_archives_processed": len(per_archive),
        "n_archives_failed": len(failures),
        "failures": failures,
        "total_speaker_dirs": sum(v["n_speaker_dirs"] for v in per_archive.values()),
        "total_nsp_files": sum(v["n_nsp_files"] for v in per_archive.values()),
        "inventory_rows": len(rows_all),
        "per_archive": per_archive,
    }
    STATS.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "per_archive"}, indent=2))


if __name__ == "__main__":
    main()
