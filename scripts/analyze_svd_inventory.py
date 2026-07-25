"""Analyse the SVD inventory for class balance and speaker-disjoint-split feasibility.

The headline question: SVD ships a session id (`AufnahmeID`, which is also the folder
name inside every zip) AND a separate speaker id (`SprecherID`). Splitting on the
folder name is the obvious thing to do and is WRONG whenever one speaker contributed
more than one session. This script measures how wrong.

Usage:
    python scripts/analyze_svd_inventory.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "raw" / "svd_meta" / "svd_inventory.csv"
OUT = REPO / "autoresearch_results" / "acquisition" / "svd_inventory_analysis.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True, timeout=30).stdout.strip() or "UNCOMMITTED"
    except Exception:
        return "UNKNOWN"


def main() -> None:
    rows = list(csv.DictReader(SRC.open(encoding="utf-8", newline="")))

    sessions = [r["AufnahmeID"] for r in rows if r.get("AufnahmeID")]
    speakers = [r["SprecherID"] for r in rows if r.get("SprecherID")]
    sess_c, spk_c = Counter(sessions), Counter(speakers)

    # AufnahmeTyp: 'n' = normal/healthy, 'p' = pathological.
    typ = Counter((r.get("AufnahmeTyp") or "?").strip() for r in rows)

    healthy_rows = [r for r in rows if (r.get("_archive") or "") == "healthy"]
    path_rows = [r for r in rows if (r.get("_archive") or "") != "healthy"]

    # --- the leakage measurement -------------------------------------------------
    # How many speakers contributed more than one session?
    multi = {k: v for k, v in spk_c.items() if v > 1}
    n_multi_sessions = sum(multi.values())

    # Do any speakers appear on BOTH sides of the healthy/pathological label?
    spk_healthy = {r["SprecherID"] for r in healthy_rows if r.get("SprecherID")}
    spk_path = {r["SprecherID"] for r in path_rows if r.get("SprecherID")}
    cross_label = sorted(spk_healthy & spk_path)

    # Do any speakers appear in more than one pathology archive?
    arch_per_spk: dict[str, set[str]] = {}
    for r in rows:
        if r.get("SprecherID"):
            arch_per_spk.setdefault(r["SprecherID"], set()).add(r.get("_archive", ""))
    multi_archive = {k: sorted(v) for k, v in arch_per_spk.items() if len(v) > 1}

    sex = Counter((r.get("Geschlecht") or "?").strip() for r in rows)

    def sex_by(rs) -> dict:
        return dict(Counter((r.get("Geschlecht") or "?").strip() for r in rs).most_common())

    stats = {
        "artifact": "svd_inventory_analysis",
        "source_file": str(SRC.relative_to(REPO)).replace("\\", "/"),
        "source_sha256": sha256(SRC),
        "repo_commit": git_sha(),
        "zenodo_doi": "10.5281/zenodo.16874898",
        "license": "CC-BY-4.0",

        "n_rows": len(rows),
        "n_unique_sessions_AufnahmeID": len(sess_c),
        "n_unique_speakers_SprecherID": len(spk_c),
        "AufnahmeTyp_counts": dict(typ.most_common()),

        "class_balance": {
            "healthy_sessions": len(healthy_rows),
            "pathological_sessions": len(path_rows),
            "healthy_speakers": len(spk_healthy),
            "pathological_speakers": len(spk_path),
            "meets_500_per_class_speakers": len(spk_healthy) >= 500 and len(spk_path) >= 500,
        },

        "LEAKAGE": {
            "session_id_is_the_zip_folder_name": True,
            "n_speakers_with_multiple_sessions": len(multi),
            "n_sessions_belonging_to_multi_session_speakers": n_multi_sessions,
            "max_sessions_per_speaker": max(spk_c.values()) if spk_c else 0,
            "pct_rows_at_risk_if_split_on_session": round(
                100.0 * n_multi_sessions / len(rows), 2) if rows else 0.0,
            "n_speakers_in_multiple_archives": len(multi_archive),
            "n_speakers_on_both_healthy_and_pathological_sides": len(cross_label),
            "example_cross_label_speakers": cross_label[:10],
            "example_multi_archive_speakers": dict(list(multi_archive.items())[:5]),
        },

        "confounds": {
            "sex_all": dict(sex.most_common()),
            "sex_healthy": sex_by(healthy_rows),
            "sex_pathological": sex_by(path_rows),
        },

        "split_key_verdict": (
            "Split on SprecherID, never on AufnahmeID. AufnahmeID is the zip folder "
            "name, so it is the default grouping any naive loader picks up, and it is "
            "NOT speaker-unique."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
