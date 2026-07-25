"""Pre-fetch the frozen audio backbones into the HF cache.

Run once before `scripts/run_benchmark.py`. Downloads are ~1.7 GB total.
On this host the system OpenSSL trust store is required (corporate MITM cert);
`voicehealth.embed` installs the same `truststore` shim at import.

    C:/Users/evija/anaconda3/python.exe scripts/fetch_backbones.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Windows without Developer Mode cannot create the HF cache symlinks (WinError 1314).
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

try:  # pragma: no cover - host-specific TLS shim
    import truststore

    truststore.inject_into_ssl()
except Exception:  # noqa: BLE001
    pass

from huggingface_hub import snapshot_download  # noqa: E402

REPOS = {
    "wavlm": ("microsoft/wavlm-base-plus", ["*.json", "pytorch_model.bin"]),
    "wav2vec2": ("facebook/wav2vec2-base", ["*.json", "pytorch_model.bin"]),
    "whisper": ("openai/whisper-small", ["*.json", "*.txt", "model.safetensors"]),
    # HeAR is gated (license acceptance + HF token). Included so that
    # `--backbone hear` works the moment a token is configured.
    "hear": ("google/hear-pytorch", ["*.json", "pytorch_model.bin"]),
}


LOCAL_ROOT = Path(__file__).resolve().parents[1] / "models"


def main(argv: list[str]) -> int:
    wanted = argv[1:] or [k for k in REPOS if k != "hear"]
    rc = 0
    for key in wanted:
        repo, patterns = REPOS[key]
        try:
            path = snapshot_download(repo_id=repo, allow_patterns=patterns)
            print(f"OK   {key:10s} {repo} -> {path}")
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"WARN {key:10s} HF cache download failed ({type(exc).__name__}); "
                  f"retrying into models/ without symlinks")
        try:
            # Windows without Developer Mode cannot symlink inside the HF cache
            # (WinError 1314). `local_dir` copies real files instead.
            target = LOCAL_ROOT / repo.replace("/", "__")
            path = snapshot_download(repo_id=repo, allow_patterns=patterns, local_dir=str(target))
            print(f"OK   {key:10s} {repo} -> {path}  (local_dir)")
        except Exception as exc:  # noqa: BLE001
            rc = 1
            print(f"FAIL {key:10s} {repo}: {type(exc).__name__}: {str(exc)[:200]}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
