"""audit_demographic_baseline.py — the confound bar an audio model must clear.

Before any voice model may claim it detects pathology, we establish what the
*demographics alone* achieve on the same corpus. The constitution requires that a
finding claims only the margin ABOVE the strongest confound baseline.

This reproduces FINDINGS.md F1 exactly. CPU only, seconds, no audio, no GPU.

Usage:
    python scripts/audit_demographic_baseline.py --dataset svd
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

ROOT = Path(__file__).resolve().parents[1]
SVD_META = ROOT / "data" / "raw" / "svd_meta" / "voice_data.csv"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def load_svd() -> pd.DataFrame:
    """SVD session metadata. `SprecherID` is the speaker id — the split unit."""
    if not SVD_META.exists():
        raise SystemExit(
            f"missing {SVD_META}\n"
            "fetch it first (167 KB):\n"
            "  https://stimmdb.coli.uni-saarland.de/data/voice_data.csv"
        )
    df = pd.read_csv(SVD_META)
    # A session is healthy iff it carries neither a diagnosis nor a pathology tag.
    df["healthy"] = df["Pathologien"].isna() & df["Diagnose"].isna()
    df["age"] = (
        pd.to_datetime(df["AufnahmeDatum"], errors="coerce")
        - pd.to_datetime(df["Geburtsdatum"], errors="coerce")
    ).dt.days / 365.25
    return df


def audit_svd() -> dict:
    df = load_svd()
    d = df.dropna(subset=["age"]).copy()
    y = (~d["healthy"]).astype(int).values          # 1 = pathological
    groups = d["SprecherID"].values
    age = d["age"].values
    sex = (d["Geschlecht"] == "w").astype(int).values

    auc_age = roc_auc_score(y, age)
    auc_sex = roc_auc_score(y, sex)

    # Speaker-disjoint CV so the baseline itself is not leakage-inflated.
    X = np.c_[age, sex]
    proba = cross_val_predict(
        LogisticRegression(max_iter=1000), X, y,
        cv=GroupKFold(5), groups=groups, method="predict_proba",
    )[:, 1]
    auc_both = roc_auc_score(y, proba)

    # Leakage exposure: speakers contributing multiple sessions.
    per_spk = d.groupby("SprecherID").size()

    res = {
        "dataset": "svd",
        "artifact": str(SVD_META),
        "artifact_md5": _md5(SVD_META),
        "n_sessions": int(len(d)),
        "n_speakers": int(d["SprecherID"].nunique()),
        "n_pathological": int(y.sum()),
        "n_healthy": int((1 - y).sum()),
        "mean_age_healthy": float(d.loc[d.healthy, "age"].mean()),
        "mean_age_pathological": float(d.loc[~d.healthy, "age"].mean()),
        "auc_age_only": float(auc_age),
        "auc_sex_only": float(auc_sex),
        "auc_age_sex_speaker_disjoint": float(auc_both),
        "speakers_with_multiple_sessions": int((per_spk > 1).sum()),
        "max_sessions_per_speaker": int(per_spk.max()),
        "published_benchmark": "UAR 85.22 (arXiv:2410.10537) — different metric, indicative only",
    }
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="svd", choices=["svd"])
    ap.add_argument("--out", default=str(ROOT / "autoresearch_results" / "F1_demographic_baseline.json"))
    args = ap.parse_args()

    res = audit_svd()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")

    print("=== DEMOGRAPHIC CONFOUND BASELINE (no audio) ===")
    print(f"  dataset      : {res['dataset']}  (md5 {res['artifact_md5'][:12]})")
    print(f"  n            : {res['n_sessions']} sessions / {res['n_speakers']} speakers")
    print(f"  balance      : {res['n_pathological']} pathological / {res['n_healthy']} healthy")
    print(f"  mean age     : healthy {res['mean_age_healthy']:.1f}  "
          f"pathological {res['mean_age_pathological']:.1f}")
    print(f"  AUC age      : {res['auc_age_only']:.4f}")
    print(f"  AUC sex      : {res['auc_sex_only']:.4f}")
    print(f"  AUC age+sex  : {res['auc_age_sex_speaker_disjoint']:.4f}  (speaker-disjoint 5-fold)")
    print(f"  leakage risk : {res['speakers_with_multiple_sessions']} speakers have >1 session "
          f"(max {res['max_sessions_per_speaker']}) -> NEVER split on recordings")
    print(f"  wrote {args.out}")
    print()
    print("  An audio model must clear the age+sex bar to claim it detects PATHOLOGY")
    print("  rather than DEMOGRAPHICS.")


if __name__ == "__main__":
    main()
