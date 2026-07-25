"""CLI for the competitive benchmark harness.

    C:/Users/evija/anaconda3/python.exe scripts/run_benchmark.py \
        --corpus svd --backbone wavlm --head all --folds 5 --repeats 10

Writes `autoresearch_results/bench_<corpus>_<backbone>[_<pooling>].json` containing
every measured number, the config hash, the dataset census, the power check, and a
pointer to the cached embedding `.npz` that produced it (CLAUDE.md R1: no orphan
numbers). The agent never states a metric it did not read out of this file (R2).

`--backbone egemaps` runs the classical baseline through the identical harness.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from voicehealth.benchmark import (  # noqa: E402
    CONFOUND_SETS,
    HEAD_NAMES,
    BenchmarkConfig,
    run_benchmark,
)
from voicehealth.embed import BACKBONES, POOLINGS, extract_embeddings, load_manifest  # noqa: E402
from voicehealth import features as feat_mod  # noqa: E402

CLASSICAL = ("egemaps", "classical")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Speaker-disjoint voice-health benchmark")
    p.add_argument("--corpus", default="svd", help="corpus id under data/interim/<corpus>/")
    p.add_argument(
        "--manifest", default=None, help="override manifest path (default data/interim/<corpus>/manifest.csv)"
    )
    p.add_argument(
        "--backbone",
        default="wavlm",
        help=f"one of {sorted(BACKBONES)} or 'egemaps' (classical features)",
    )
    p.add_argument("--pooling", default="mean_std", choices=list(POOLINGS))
    p.add_argument("--head", default="all", help="'all' or comma-separated: " + ",".join(HEAD_NAMES))
    p.add_argument("--folds", type=int, default=5)
    p.add_argument("--repeats", type=int, default=10, help="repeated speaker-disjoint partitions")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--bootstrap", type=int, default=2000)
    p.add_argument("--positive-label", default="pathological")
    p.add_argument("--batch-seconds", type=float, default=240.0)
    p.add_argument("--device", default=None)
    p.add_argument("--no-fp16", action="store_true")
    p.add_argument("--force-extract", action="store_true")
    p.add_argument("--tag", default="", help="suffix for the output filename")
    p.add_argument("--out-dir", default=str(REPO_ROOT / "autoresearch_results"))
    p.add_argument("--notes", default="")
    return p.parse_args(argv)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    t0 = time.time()

    manifest_path = Path(args.manifest) if args.manifest else (
        REPO_ROOT / "data" / "interim" / args.corpus / "manifest.csv"
    )
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        return 2
    rows = load_manifest(manifest_path)

    heads = tuple(HEAD_NAMES) if args.head == "all" else tuple(
        h.strip() for h in args.head.split(",") if h.strip()
    )
    bad = [h for h in heads if h not in HEAD_NAMES]
    if bad:
        print(f"ERROR: unknown head(s) {bad}; known: {list(HEAD_NAMES)}")
        return 2

    is_classical = args.backbone in CLASSICAL
    if is_classical:
        bundle = feat_mod.extract_features(
            rows, corpus_id=args.corpus, force=args.force_extract
        )
        backend_desc = feat_mod.describe_backend()
        pooling = "functionals"
    else:
        if args.backbone not in BACKBONES:
            print(f"ERROR: unknown backbone {args.backbone!r}; known: {sorted(BACKBONES)} + 'egemaps'")
            return 2
        bundle = extract_embeddings(
            rows,
            args.backbone,
            pooling=args.pooling,
            corpus_id=args.corpus,
            batch_seconds=args.batch_seconds,
            device=args.device,
            fp16=not args.no_fp16,
            force=args.force_extract,
        )
        backend_desc = {
            "backend": BACKBONES[args.backbone].hf_id,
            "evidence": BACKBONES[args.backbone].evidence,
        }
        pooling = args.pooling

    cfg = BenchmarkConfig(
        corpus=args.corpus,
        backbone=args.backbone,
        pooling=pooling,
        heads=heads,
        n_folds=args.folds,
        n_repeats=args.repeats,
        seed=args.seed,
        n_boot=args.bootstrap,
        positive_label=args.positive_label,
        confound_sets=CONFOUND_SETS,
        embedding_hash=bundle.hash,
        embedding_path=str(bundle.cache_path),
        notes=args.notes,
    )
    result = run_benchmark(bundle, cfg)

    payload = {
        "schema": "voicehealth.bench/1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 1),
        "command": " ".join([Path(sys.argv[0]).name] + (argv or sys.argv[1:])),
        "git_sha": _git_sha(),
        "host": {"platform": platform.platform(), "python": sys.version.split()[0]},
        "manifest": str(manifest_path),
        "backend": backend_desc,
        "embedding_artifact": str(bundle.cache_path),
        "embedding_manifest": str(Path(bundle.cache_path).with_suffix(".manifest.json")),
        "embedding_content_hash": bundle.hash,
        "config": result.config,
        "config_hash": result.config_hash,
        "dataset": result.dataset,
        "power_check_R6": result.power,
        "recording_level": result.recording_level,
        "speaker_level": result.speaker_level,
        "per_repeat_auc": result.per_repeat_auc,
        "margins_vs_confound": result.margins,
        "verdicts": result.verdicts,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.tag}" if args.tag else ""
    pool_tag = "" if is_classical else f"_{pooling}"
    out_path = out_dir / f"bench_{args.corpus}_{args.backbone}{pool_tag}{suffix}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Artifact written BEFORE any summary print (cp1252 console kills unicode).
    print(f"\n[bench] artifact: {out_path}")
    print(f"[bench] config_hash={result.config_hash}  embeddings={bundle.cache_path}")
    d = result.dataset
    print(
        f"[bench] {d['corpus']}: {d['n_recordings']} recordings / {d['n_speakers']} speakers "
        f"({d['n_positive_speakers']} pos / {d['n_negative_speakers']} neg speakers)"
    )
    pw = result.power
    print(
        f"[bench] power R6: n_paired={pw['n_paired']} m={pw['family_size']} "
        f"min_p={pw['min_attainable_p']:.5f} vs holm={pw['holm_tightest_threshold']:.5f} "
        f"feasible={pw['feasible']}"
    )
    bar = result.margins["confound_bar_name"]
    print(f"[bench] confound bar: {bar} rec-AUC={result.margins['confound_bar_auc_recording']:.4f} "
          f"spk-AUC={result.margins['confound_bar_auc_speaker']:.4f}")
    print(f"{'head':14s} {'recAUC':>8s} {'recUAR':>8s} {'spkAUC':>8s} {'spkUAR':>8s} {'ECE':>6s}  verdict")
    for name, r in result.recording_level.items():
        s = result.speaker_level[name]
        v = result.verdicts.get(name, "")
        print(
            f"{name:14s} {r['roc_auc']:8.4f} {r['uar']:8.4f} {s['roc_auc']:8.4f} "
            f"{s['uar']:8.4f} {r['ece']:6.3f}  {v}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
