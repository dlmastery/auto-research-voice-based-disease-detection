"""Analyse COUGHVID metadata for class balance and speaker-disjoint-split feasibility.

Reads metadata straight out of the zip (no audio extraction). Emits a JSON artifact
so every number in the data card has provenance (CLAUDE.md R1/R2).

Usage:
    python scripts/analyze_coughvid_meta.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZIP = REPO / "data" / "raw" / "coughvid" / "public_dataset_v3.zip"
MEMBER = "coughvid_20211012/metadata_compiled.csv"
OUT = REPO / "autoresearch_results" / "acquisition" / "coughvid_meta_stats.json"
CSV_COPY = REPO / "data" / "raw" / "coughvid" / "metadata_compiled.csv"

# The published-benchmark convention: keep only clips the cough detector is
# confident about. Retained as a named constant so the data card can cite it.
COUGH_THRESHOLD = 0.8


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        ).stdout.strip() or "UNCOMMITTED"
    except Exception:
        return "UNKNOWN"


def main() -> None:
    zf = zipfile.ZipFile(ZIP)
    raw = zf.read(MEMBER).decode("utf-8", errors="replace")
    CSV_COPY.write_text(raw, encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(raw)))

    uuids = [r["uuid"] for r in rows]
    uuid_counts = Counter(uuids)

    def nonempty(field: str) -> int:
        return sum(1 for r in rows if (r.get(field) or "").strip())

    status = Counter((r.get("status") or "MISSING").strip() or "MISSING" for r in rows)

    # Expert-labelled subset: rows where at least one clinician filled diagnosis_k.
    expert_rows = [r for r in rows
                   if any((r.get(f"diagnosis_{k}") or "").strip() for k in (1, 2, 3, 4))]
    expert_diag = Counter()
    for r in expert_rows:
        for k in (1, 2, 3, 4):
            v = (r.get(f"diagnosis_{k}") or "").strip()
            if v:
                expert_diag[v] += 1

    def fnum(r, field):
        try:
            return float(r[field])
        except (ValueError, TypeError, KeyError):
            return None

    conf = [v for v in (fnum(r, "cough_detected") for r in rows) if v is not None]
    high_conf = [r for r in rows
                 if (fnum(r, "cough_detected") or 0.0) >= COUGH_THRESHOLD]
    status_hc = Counter((r.get("status") or "MISSING").strip() or "MISSING"
                        for r in high_conf)

    # Speaker-disjoint feasibility. There is no participant id, so the only
    # proxies for "same person submitted twice" are geolocation and timestamp.
    geo = Counter((r.get("latitude", ""), r.get("longitude", "")) for r in rows
                  if (r.get("latitude") or "").strip())
    repeat_geo = {f"{a},{b}": c for (a, b), c in geo.most_common(10)}

    def crosstab(field: str) -> dict:
        tab: dict[str, Counter] = {}
        for r in rows:
            st = (r.get("status") or "MISSING").strip() or "MISSING"
            tab.setdefault(st, Counter())[(r.get(field) or "MISSING").strip() or "MISSING"] += 1
        return {k: dict(v.most_common(8)) for k, v in tab.items()}

    stats = {
        "artifact": "coughvid_meta_stats",
        "source_zip": str(ZIP.relative_to(REPO)).replace("\\", "/"),
        "source_zip_bytes": ZIP.stat().st_size,
        "source_zip_sha256": sha256(ZIP),
        "metadata_member": MEMBER,
        "repo_commit": git_sha(),
        "n_rows": len(rows),
        "n_unique_uuids": len(uuid_counts),
        "uuid_is_unique_per_row": len(uuid_counts) == len(rows),
        "speaker_id_field_present": False,
        "id_fields_available": ["uuid (per-recording, NOT per-participant)"],
        "label_coverage": {
            "status_self_reported": nonempty("status"),
            "status_SSL": nonempty("status_SSL"),
            "age": nonempty("age"),
            "gender": nonempty("gender"),
            "respiratory_condition": nonempty("respiratory_condition"),
            "latitude": nonempty("latitude"),
        },
        "status_counts_all": dict(status.most_common()),
        "cough_detected": {
            "n_with_value": len(conf),
            "mean": round(sum(conf) / len(conf), 4) if conf else None,
            "threshold": COUGH_THRESHOLD,
            "n_at_or_above_threshold": len(high_conf),
            "status_counts_at_threshold": dict(status_hc.most_common()),
        },
        "expert_labelled_subset": {
            "n_rows_with_any_expert_diagnosis": len(expert_rows),
            "diagnosis_label_counts": dict(expert_diag.most_common()),
            "n_with_4_experts": sum(
                1 for r in rows
                if all((r.get(f"diagnosis_{k}") or "").strip() for k in (1, 2, 3, 4))),
        },
        "confounds": {
            "gender_by_status": crosstab("gender"),
            "respiratory_condition_by_status": crosstab("respiratory_condition"),
            "top_repeated_geolocations": repeat_geo,
            "n_distinct_geolocations": len(geo),
        },
        "split_key_verdict": (
            "NO participant identifier exists. uuid is per-recording. Speaker-disjoint "
            "splitting is IMPOSSIBLE on COUGHVID; repeat submissions by the same person "
            "cannot be detected or grouped. Any published COUGHVID accuracy is therefore "
            "an upper bound of unknown tightness."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
