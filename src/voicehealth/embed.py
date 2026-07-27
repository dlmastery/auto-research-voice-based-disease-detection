"""Frozen-embedding extraction for the voice-health claim audit.

One interface, several backbones. Embeddings are extracted **once** and cached to
`.npz` keyed by a content hash of everything that could change them (source file
SHA-256 set, backbone id + HF revision, preprocessing policy, pooling, dtype,
library versions). Nothing is ever re-extracted inside a fold / seed / sweep loop
-- that is the hard rule in `skills/voice-embedding-extraction/SKILL.md` §5.

Preprocessing policy (pinned, and part of the cache key):
  * decode -> mono by channel mean (SVD `.egg` is a separate modality and is never
    mixed in; the interim manifest already carries acoustic-only files)
  * resample to the backbone's native rate with `librosa.resample` (soxr_hq)
  * **no peak normalisation** -- RMS intensity is a confound-battery member
    (SKILL.md §2.3); `rms` is recorded per file so `intensity_rms_only` stays
    measurable
  * raw `duration_s` recorded BEFORE any cropping (the `duration_only` baseline)
  * silence is kept (SKILL.md §3): `silence_only` must remain runnable

`speaker_id` always travels inside the `.npz`. A downstream loader that cannot
find it must fail loudly rather than fall back to a recording-level split.

Usage
-----
    from voicehealth.embed import load_manifest, extract_embeddings
    rows = load_manifest("data/interim/svd/manifest.csv")
    bundle = extract_embeddings(rows, backbone="wavlm", pooling="mean_std")
    bundle.X.shape  # (n_recordings, d)
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

# Windows without Developer Mode cannot create the HF cache symlinks (WinError 1314).
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

try:  # pragma: no cover - host-specific TLS shim (corporate MITM cert store)
    import truststore

    truststore.inject_into_ssl()
except Exception:  # noqa: BLE001
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = REPO_ROOT / "cache" / "embeddings"

# --------------------------------------------------------------------------- #
# Backbone registry
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BackboneSpec:
    """A frozen audio encoder. `kind` selects the extraction path."""

    key: str
    hf_id: str
    kind: str  # "hf_ssl" | "whisper_encoder" | "hear"
    sample_rate: int
    nominal_dim: int
    evidence: str


BACKBONES: dict[str, BackboneSpec] = {
    "wavlm": BackboneSpec(
        key="wavlm",
        hf_id="microsoft/wavlm-base-plus",
        kind="hf_ssl",
        sample_rate=16000,
        nominal_dim=768,
        evidence="SpeechDx MRR 0.38 (arXiv:2606.17339); pre-registered headline representation",
    ),
    "wav2vec2": BackboneSpec(
        key="wav2vec2",
        hf_id="facebook/wav2vec2-base",
        kind="hf_ssl",
        sample_rate=16000,
        nominal_dim=768,
        evidence="the field's default baseline; makes our numbers comparable to published ones",
    ),
    "whisper": BackboneSpec(
        key="whisper",
        hf_id="openai/whisper-small",
        kind="whisper_encoder",
        sample_rate=16000,
        nominal_dim=768,
        evidence="SpeechDx overall winner, mean MRR 0.44 over 27 speaker-disjoint tasks (arXiv:2606.17339)",
    ),
    "hear": BackboneSpec(
        key="hear",
        hf_id="google/hear-pytorch",
        kind="hear",
        sample_rate=16000,
        nominal_dim=512,
        evidence=(
            "health-acoustic prior, ViT-L MAE over 313M 2-s clips (arXiv:2403.02522). "
            "GATED on HF (license acceptance + token). Its training corpus is NOT released, "
            "so any HeAR number imports an undisclosed prior -- state this every time."
        ),
    ),
}

POOLINGS = ("mean", "mean_std", "attention")

# Pinned preprocessing policy. Changing any value changes the content hash.
PREPROCESS_POLICY: dict[str, Any] = {
    "mono": "channel_mean",
    "resampler": "librosa.resample/soxr_hq",
    "peak_normalise": False,
    "keep_silence": True,
    "vad": None,
    "max_seconds": 30.0,
    "min_seconds": 0.5,
    "windowing": {"mode": "full_utterance_capped", "max_seconds": 30.0},
    "layer": "last_hidden_state",
    "dtype": "float32",
}


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #


def load_manifest(
    manifest_csv: str | Path,
    *,
    repo_root: Path | None = None,
    require_columns: Sequence[str] = ("path", "speaker_id", "label"),
) -> list[dict[str, Any]]:
    """Read an interim manifest and resolve audio paths to absolute paths.

    Raises if `speaker_id` is absent -- without it a downstream loop would
    silently split on recordings (the #1 leakage failure in this field).
    """
    manifest_csv = Path(manifest_csv)
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    with manifest_csv.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"empty manifest: {manifest_csv}")
    missing = [c for c in require_columns if c not in rows[0]]
    if missing:
        raise ValueError(f"{manifest_csv} is missing required column(s): {missing}")

    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        p = Path(rec["path"])
        rec["abs_path"] = str(p if p.is_absolute() else (root / p))
        rec["recording_id"] = Path(rec["path"]).stem
        out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# Content hashing
# --------------------------------------------------------------------------- #


def _lib_versions() -> dict[str, str]:
    import soundfile
    import torch
    import transformers
    import librosa

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "soundfile": soundfile.__version__,
        "librosa": librosa.__version__,
    }


def _source_file_hashes(rows: Sequence[dict[str, Any]]) -> str:
    """SHA-256 over the sorted per-file SHA-256 list (anchored to source bytes)."""
    digests = []
    for r in rows:
        h = r.get("sha256") or r.get("src_sha256")
        if not h:
            # fall back to hashing the file itself (slower, still deterministic)
            h = hashlib.sha256(Path(r["abs_path"]).read_bytes()).hexdigest()
        digests.append(h)
    joined = "\n".join(sorted(digests))
    return hashlib.sha256(joined.encode()).hexdigest()


def _hf_revision(hf_id: str) -> str:
    try:
        from huggingface_hub import model_info

        return str(model_info(hf_id).sha)
    except Exception:  # noqa: BLE001 - offline is fine, recorded as unknown
        return "unknown"


def _label_hashes(rows: Sequence[dict[str, Any]]) -> str:
    """SHA-256 over the LABEL-BEARING fields, in manifest order.

    IMPL_CRITIC finding #1 (INVALIDATES-RESULTS): the cache key previously covered
    only the audio bytes via ``_source_file_hashes``. Because ``from_npz`` returns
    labels/speaker ids from the cache, a manifest that was **relabelled** — a fixed
    label bug, a new task definition, a corrected speaker id, an age correction —
    hashed identically and got a CACHE HIT that silently returned the OLD labels.
    Every downstream metric would then be computed against superseded ground truth
    with no error and no warning.

    Order is preserved (not sorted) because row order is the alignment between
    embeddings and labels; a permutation is a different cache entry.
    """
    parts = []
    for r in rows:
        parts.append("|".join(str(r.get(k, "")) for k in
                              ("speaker_id", "session_id", "label", "sex", "age", "task")))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def build_manifest_dict(
    rows: Sequence[dict[str, Any]],
    spec: BackboneSpec,
    pooling: str,
    corpus_id: str,
) -> dict[str, Any]:
    return {
        "encoder_id": spec.hf_id,
        "encoder_key": spec.key,
        "encoder_revision": _hf_revision(spec.hf_id),
        "corpus_id": corpus_id,
        "n_files": len(rows),
        "source_file_hashes": _source_file_hashes(rows),
        # labels are part of the cache identity — see _label_hashes docstring
        "label_hashes": _label_hashes(rows),
        "sample_rate": spec.sample_rate,
        "pooling": pooling,
        **PREPROCESS_POLICY,
        "lib_versions": _lib_versions(),
    }


def content_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Bundle
# --------------------------------------------------------------------------- #


@dataclass
class EmbeddingBundle:
    X: np.ndarray  # (n, d) float32
    recording_ids: np.ndarray
    speaker_ids: np.ndarray
    labels: np.ndarray
    sex: np.ndarray
    age: np.ndarray
    duration_s: np.ndarray
    rms: np.ndarray
    src_sha256: np.ndarray
    backbone: str
    pooling: str
    hash: str
    cache_path: Path
    manifest: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.speaker_ids) != len(self.X):
            raise ValueError("speaker_ids must align with X")
        if len(set(map(str, self.speaker_ids))) < 2:
            raise ValueError("fewer than 2 speakers -- no speaker-disjoint split is possible")

    @property
    def n_speakers(self) -> int:
        return len(set(map(str, self.speaker_ids)))

    def to_npz(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            X=self.X,
            recording_ids=self.recording_ids,
            speaker_ids=self.speaker_ids,
            labels=self.labels,
            sex=self.sex,
            age=self.age,
            duration_s=self.duration_s,
            rms=self.rms,
            src_sha256=self.src_sha256,
            backbone=np.array(self.backbone),
            pooling=np.array(self.pooling),
            content_hash=np.array(self.hash),
        )
        path.with_suffix(".manifest.json").write_text(
            json.dumps(self.manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    @classmethod
    def from_npz(cls, path: Path) -> "EmbeddingBundle":
        z = np.load(path, allow_pickle=False)
        mpath = path.with_suffix(".manifest.json")
        manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
        if "speaker_ids" not in z:
            raise ValueError(f"{path} has no speaker_ids -- refusing to load (leakage risk)")
        return cls(
            X=z["X"].astype(np.float32),
            recording_ids=z["recording_ids"],
            speaker_ids=z["speaker_ids"],
            labels=z["labels"],
            sex=z["sex"],
            age=z["age"],
            duration_s=z["duration_s"],
            rms=z["rms"],
            src_sha256=z["src_sha256"],
            backbone=str(z["backbone"]),
            pooling=str(z["pooling"]),
            hash=str(z["content_hash"]),
            cache_path=path,
            manifest=manifest,
        )


# --------------------------------------------------------------------------- #
# Audio loading
# --------------------------------------------------------------------------- #


def load_audio(path: str | Path, target_sr: int) -> tuple[np.ndarray, float, float]:
    """Return (waveform, raw_duration_s, rms). Mono, resampled, NOT normalised."""
    import soundfile as sf

    x, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if x.ndim > 1:
        x = x.mean(axis=1)
    raw_duration = float(len(x)) / float(sr)
    rms = float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) if len(x) else 0.0
    if sr != target_sr:
        import librosa

        x = librosa.resample(x, orig_sr=sr, target_sr=target_sr, res_type="soxr_hq")
    max_len = int(PREPROCESS_POLICY["max_seconds"] * target_sr)
    if len(x) > max_len:
        x = x[:max_len]
    min_len = int(PREPROCESS_POLICY["min_seconds"] * target_sr)
    if len(x) < min_len:
        x = np.pad(x, (0, min_len - len(x)))
    return x.astype(np.float32), raw_duration, rms


# --------------------------------------------------------------------------- #
# Pooling
# --------------------------------------------------------------------------- #


def pool_frames(H, mask, pooling: str):
    """Pool (B, T, D) frame states under a (B, T) validity mask.

    `attention` is a **parameter-free** saliency pooling: softmax over the
    z-scored per-frame L2 norm. There is no trained query vector -- training one
    would make the extractor non-frozen, which is off-thesis. Documented as such
    so nobody mistakes it for a learned attention head.
    """
    import torch

    mask = mask.to(H.dtype)
    denom = mask.sum(dim=1, keepdim=True).clamp(min=1.0)
    if pooling == "mean":
        return (H * mask.unsqueeze(-1)).sum(dim=1) / denom
    if pooling == "mean_std":
        mu = (H * mask.unsqueeze(-1)).sum(dim=1) / denom
        var = ((H - mu.unsqueeze(1)) ** 2 * mask.unsqueeze(-1)).sum(dim=1) / denom
        return torch.cat([mu, var.clamp(min=1e-10).sqrt()], dim=-1)
    if pooling == "attention":
        norms = H.norm(dim=-1)
        m = (norms * mask).sum(dim=1, keepdim=True) / denom
        sd = (((norms - m) ** 2 * mask).sum(dim=1, keepdim=True) / denom).clamp(min=1e-10).sqrt()
        logits = ((norms - m) / sd).masked_fill(mask < 0.5, float("-inf"))
        w = torch.softmax(logits, dim=1).unsqueeze(-1)
        return (H * w).sum(dim=1)
    raise ValueError(f"unknown pooling: {pooling!r} (choose from {POOLINGS})")


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


def _batches_by_seconds(
    rows: Sequence[dict[str, Any]], durations: Sequence[float], batch_seconds: float, max_items: int
) -> Iterable[list[int]]:
    """Batch by TOTAL AUDIO SECONDS, not file count (clinical corpora have a long tail)."""
    order = sorted(range(len(rows)), key=lambda i: durations[i])
    cur: list[int] = []
    cur_max = 0.0
    for i in order:
        d = max(durations[i], PREPROCESS_POLICY["min_seconds"])
        new_max = max(cur_max, d)
        if cur and (new_max * (len(cur) + 1) > batch_seconds or len(cur) >= max_items):
            yield cur
            cur, cur_max = [i], d
        else:
            cur.append(i)
            cur_max = new_max
    if cur:
        yield cur


def _load_model(spec: BackboneSpec, device: str, fp16: bool):
    import torch

    dtype = torch.float16 if (fp16 and device.startswith("cuda")) else torch.float32
    if spec.kind == "hf_ssl":
        from transformers import AutoModel

        model = AutoModel.from_pretrained(spec.hf_id, torch_dtype=dtype)
    elif spec.kind == "whisper_encoder":
        from transformers import WhisperModel

        model = WhisperModel.from_pretrained(spec.hf_id, torch_dtype=dtype).encoder
    elif spec.kind == "hear":
        from transformers import AutoModel

        try:
            model = AutoModel.from_pretrained(spec.hf_id, torch_dtype=dtype, trust_remote_code=True)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "HeAR (google/hear-pytorch) could not be loaded. It is GATED on HuggingFace: "
                "accept the license at https://huggingface.co/google/hear and run "
                "`huggingface-cli login`. Do NOT substitute another encoder and call it HeAR. "
                f"Underlying error: {type(exc).__name__}: {exc}"
            ) from exc
    else:  # pragma: no cover
        raise ValueError(f"unknown backbone kind {spec.kind!r}")
    return model.to(device).eval()


def extract_embeddings(
    rows: Sequence[dict[str, Any]],
    backbone: str,
    *,
    pooling: str = "mean_std",
    corpus_id: str | None = None,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    batch_seconds: float = 240.0,
    max_batch_items: int = 32,
    device: str | None = None,
    fp16: bool = True,
    force: bool = False,
    verbose: bool = True,
) -> EmbeddingBundle:
    """Extract (or load from cache) one embedding matrix for `rows`.

    `batch_seconds` is the padded-audio budget per batch; 240 s at fp16 fits well
    inside 16 GB for every backbone in the registry.
    """
    if backbone not in BACKBONES:
        raise ValueError(f"unknown backbone {backbone!r}; known: {sorted(BACKBONES)}")
    if pooling not in POOLINGS:
        raise ValueError(f"unknown pooling {pooling!r}; known: {POOLINGS}")
    spec = BACKBONES[backbone]
    corpus_id = corpus_id or str(rows[0].get("corpus", "unknown"))

    manifest = build_manifest_dict(rows, spec, pooling, corpus_id)
    chash = content_hash(manifest)
    manifest["content_hash"] = chash
    cache_path = Path(cache_dir) / spec.key / corpus_id / f"{chash}.npz"

    if cache_path.exists() and not force:
        if verbose:
            print(f"[embed] cache hit {cache_path}")
        return EmbeddingBundle.from_npz(cache_path)

    import torch

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = _load_model(spec, device, fp16)
    if verbose:
        print(f"[embed] {spec.hf_id} pooling={pooling} device={device} n={len(rows)}")

    durations = [float(r.get("duration_s") or 0.0) or 1.0 for r in rows]
    n = len(rows)
    X: np.ndarray | None = None
    raw_dur = np.zeros(n, dtype=np.float32)
    raw_rms = np.zeros(n, dtype=np.float32)

    feature_extractor = None
    if spec.kind == "whisper_encoder":
        from transformers import WhisperFeatureExtractor

        feature_extractor = WhisperFeatureExtractor.from_pretrained(spec.hf_id)

    done = 0
    with torch.inference_mode():
        for idx in _batches_by_seconds(rows, durations, batch_seconds, max_batch_items):
            waves, lens = [], []
            for i in idx:
                w, d, r = load_audio(rows[i]["abs_path"], spec.sample_rate)
                waves.append(w)
                lens.append(len(w))
                raw_dur[i] = d
                raw_rms[i] = r

            if spec.kind == "whisper_encoder":
                feats = feature_extractor(
                    waves, sampling_rate=spec.sample_rate, return_tensors="pt"
                ).input_features.to(device=device, dtype=model.dtype)
                H = model(feats).last_hidden_state  # (B, 1500, D)
                T = H.shape[1]
                # Whisper pads to 30 s with no attention mask; valid encoder frames
                # are n_samples // 320 (hop 160 * conv stride 2).
                mask = torch.zeros(H.shape[0], T, device=device)
                for b, L in enumerate(lens):
                    mask[b, : max(1, min(T, L // 320))] = 1.0
            else:
                maxlen = max(lens)
                batch = torch.zeros(len(idx), maxlen, dtype=torch.float32)
                amask = torch.zeros(len(idx), maxlen, dtype=torch.long)
                for b, w in enumerate(waves):
                    batch[b, : len(w)] = torch.from_numpy(w)
                    amask[b, : len(w)] = 1
                batch = batch.to(device=device, dtype=model.dtype)
                amask = amask.to(device)
                out = model(batch, attention_mask=amask)
                H = out.last_hidden_state  # (B, T, D)
                fl = model._get_feat_extract_output_lengths(amask.sum(-1)).cpu().numpy()
                mask = torch.zeros(H.shape[0], H.shape[1], device=device)
                for b, L in enumerate(fl):
                    mask[b, : max(1, min(H.shape[1], int(L)))] = 1.0

            emb = pool_frames(H.float(), mask, pooling).cpu().numpy().astype(np.float32)
            if X is None:
                X = np.zeros((n, emb.shape[1]), dtype=np.float32)
            X[idx] = emb
            done += len(idx)
            if verbose and done % 128 < len(idx):
                print(f"[embed]   {done}/{n}", flush=True)

    del model
    if device.startswith("cuda"):
        torch.cuda.empty_cache()

    assert X is not None
    if not np.isfinite(X).all():
        raise RuntimeError("non-finite values in embeddings -- refusing to cache")

    bundle = EmbeddingBundle(
        X=X,
        recording_ids=np.array([r["recording_id"] for r in rows]),
        speaker_ids=np.array([str(r["speaker_id"]) for r in rows]),
        labels=np.array([str(r.get("label", "")) for r in rows]),
        sex=np.array([str(r.get("sex", "")) for r in rows]),
        age=np.array([float(r["age"]) if r.get("age") else np.nan for r in rows], dtype=np.float32),
        duration_s=raw_dur,
        rms=raw_rms,
        src_sha256=np.array([str(r.get("sha256", "")) for r in rows]),
        backbone=spec.key,
        pooling=pooling,
        hash=chash,
        cache_path=cache_path,
        manifest=manifest,
    )
    bundle.to_npz(cache_path)  # write the artifact BEFORE any summary print (cp1252)
    if verbose:
        print(f"[embed] wrote {cache_path}  X={X.shape}")
    return bundle


def available_backbones(check_remote: bool = False) -> dict[str, str]:
    """Report which backbones can actually be loaded on this host."""
    out: dict[str, str] = {}
    for key, spec in BACKBONES.items():
        if not check_remote:
            out[key] = "registered"
            continue
        try:
            from huggingface_hub import model_info

            info = model_info(spec.hf_id)
            out[key] = f"reachable (gated={getattr(info, 'gated', None)})"
        except Exception as exc:  # noqa: BLE001
            out[key] = f"UNAVAILABLE: {type(exc).__name__}"
    return out


if __name__ == "__main__":  # tiny smoke path
    print(json.dumps(available_backbones(check_remote=bool(os.environ.get("VH_REMOTE"))), indent=2))
