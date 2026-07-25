"""Analyse Coswara metadata for class balance and speaker-disjoint-split feasibility.

Emits a JSON artifact so every number in the data card has provenance (CLAUDE.md R1/R2).

Usage:
    python scripts/analyze_coswara_meta.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "raw" / "coswara_meta" / "combined_data.csv"
OUT = REPO / "autoresearch_results" / "acquisition" / "coswara_meta_stats.json"

# Coswara covid_status values grouped into the binary task used by the published
# AUC ~0.92 claims. Kept explicit rather than inferred so the mapping is auditable.
POSITIVE = {"positive_mild", "positive_moderate", "positive_asymp"}
NEGATIVE = {"healthy"}
EXCLUDED = {"recovered_full", "resp_illness_not_identified", "no_resp_illness_exposed"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
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
    rows = list(csv.DictReader(SRC.open(encoding="utf-8", newline="")))

    ids = [r["id"] for r in rows]
    id_counts = Counter(ids)
    returning = Counter(r.get("rU", "") for r in rows)

    # Does any single id carry more than one record_date? That is the direct
    # test of whether id is a safe grouping key for GroupKFold.
    dates_per_id: dict[str, set[str]] = {}
    for r in rows:
        dates_per_id.setdefault(r["id"], set()).add(r.get("record_date", ""))
    multi_date_ids = {k: sorted(v) for k, v in dates_per_id.items() if len(v) > 1}

    status = Counter(r["covid_status"] for r in rows)
    n_pos = sum(v for k, v in status.items() if k in POSITIVE)
    n_neg = sum(v for k, v in status.items() if k in NEGATIVE)

    # Confound cross-tabs: the demographic shortcuts flagged in the survey.
    def crosstab(field: str) -> dict:
        tab: dict[str, Counter] = {}
        for r in rows:
            cls = "positive" if r["covid_status"] in POSITIVE else (
                "negative" if r["covid_status"] in NEGATIVE else "other")
            tab.setdefault(cls, Counter())[r.get(field, "") or "MISSING"] += 1
        return {k: dict(v) for k, v in tab.items()}

    def age_stats() -> dict:
        out = {}
        for cls_name, keys in (("positive", POSITIVE), ("negative", NEGATIVE)):
            ages = []
            for r in rows:
                if r["covid_status"] in keys:
                    try:
                        ages.append(float(r["a"]))
                    except (ValueError, TypeError):
                        pass
            if ages:
                ages.sort()
                n = len(ages)
                out[cls_name] = {
                    "n_with_age": n,
                    "mean": round(sum(ages) / n, 2),
                    "median": ages[n // 2],
                    "min": ages[0],
                    "max": ages[-1],
                }
        return out

    stats = {
        "artifact": "coswara_meta_stats",
        "source_file": str(SRC.relative_to(REPO)).replace("\\", "/"),
        "source_sha256": sha256(SRC),
        "repo_commit": git_sha(),
        "n_rows": len(rows),
        "n_unique_ids": len(id_counts),
        "id_is_unique_per_row": len(id_counts) == len(rows),
        "max_rows_per_id": max(id_counts.values()),
        "n_ids_with_multiple_rows": sum(1 for v in id_counts.values() if v > 1),
        "n_ids_with_multiple_record_dates": len(multi_date_ids),
        "returning_user_field_rU": dict(returning),
        "covid_status_counts": dict(status.most_common()),
        "binary_task": {
            "positive_labels": sorted(POSITIVE),
            "negative_labels": sorted(NEGATIVE),
            "excluded_labels": sorted(EXCLUDED),
            "n_positive": n_pos,
            "n_negative": n_neg,
            "meets_500_per_class": n_pos >= 500 and n_neg >= 500,
        },
        "confounds": {
            "gender_by_class": crosstab("g"),
            "country_by_class_top": {
                k: dict(Counter(v).most_common(5))
                for k, v in crosstab("l_c").items()
            },
            "age": age_stats(),
        },
        "split_key_verdict": (
            "id is unique per row; rU flags self-declared returning users who are NOT "
            "linkable to their prior id, so id-level GroupKFold is the best available "
            "grouping but does NOT fully guarantee speaker disjointness."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
