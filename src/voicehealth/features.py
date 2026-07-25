"""Classical acoustic features -- the baseline SOTA papers claim to beat.

Gap 1 in `corpus/SURVEY_sota_methods.md` (e) exists because "SSL beats handcrafted
features" is almost always reported under protocols with speaker overlap and/or
demographic imbalance. This module produces the honest comparator, on the same
manifest, through the same cache and the same `EmbeddingBundle` interface as
`voicehealth.embed`, so `voicehealth.benchmark` cannot tell them apart.

Two backends, and the artifact always records WHICH ONE RAN:

  ``opensmile-eGeMAPSv02``  the real thing -- openSMILE's 88-dim eGeMAPS v02
                            Functionals (Eyben et al., IEEE T-AFFC 2016,
                            doi:10.1109/TAFFC.2015.2457417). Used whenever the
                            `opensmile` package imports.
  ``librosa-core-v1``       a documented reimplementation of the CORE set only:
                            F0 statistics, jitter (local), shimmer (local), HNR,
                            MFCC 1-13 mean/std/delta-std, and spectral shape
                            (centroid / bandwidth / rolloff / flux / flatness /
                            zero-crossing rate). **It is NOT eGeMAPS** and is
                            never labelled as such; the LLD set, the smoothing
                            and the functional set all differ.

The backend id is part of the content hash, so an opensmile run and a fallback
run can never collide in the cache or be compared as if they were the same
feature set.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .embed import (
    DEFAULT_CACHE_DIR,
    PREPROCESS_POLICY,
    EmbeddingBundle,
    _lib_versions,
    _source_file_hashes,
    content_hash,
    load_audio,
)

FEATURE_SR = 16000


def opensmile_available() -> bool:
    try:
        import opensmile  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def backend_id() -> str:
    return "opensmile-eGeMAPSv02" if opensmile_available() else "librosa-core-v1"


# --------------------------------------------------------------------------- #
# Backend A -- real openSMILE eGeMAPS v02
# --------------------------------------------------------------------------- #


def _egemaps_opensmile(waves: Sequence[np.ndarray]) -> tuple[np.ndarray, list[str]]:
    import opensmile

    smile = opensmile.Smile(
        feature_set=opensmile.FeatureSet.eGeMAPSv02,
        feature_level=opensmile.FeatureLevel.Functionals,
        num_workers=1,
    )
    rows, names = [], None
    for w in waves:
        df = smile.process_signal(np.asarray(w, dtype=np.float32), FEATURE_SR)
        if names is None:
            names = [str(c) for c in df.columns]
        rows.append(df.to_numpy(dtype=np.float32)[0])
    return np.vstack(rows).astype(np.float32), (names or [])


# --------------------------------------------------------------------------- #
# Backend B -- documented librosa/numpy reimplementation of the core set
# --------------------------------------------------------------------------- #


def _jitter_shimmer_hnr(x: np.ndarray, f0: np.ndarray, voiced: np.ndarray, sr: int) -> dict:
    """Period-based perturbation measures from a frame-level F0 track.

    Jitter (local)  = mean |T_i - T_{i-1}| / mean T          (cycle-to-cycle period variation)
    Shimmer (local) = mean |A_i - A_{i-1}| / mean A          (cycle-to-cycle amplitude variation)
    HNR             = 10*log10(r_max / (1 - r_max)) from the normalised autocorrelation
                      peak at the F0 lag, averaged over voiced frames (Boersma 1993 form).

    These are computed on the F0 track, not on glottal cycles located in the
    waveform, so they are approximations of the Praat definitions -- which is
    exactly why this backend is not called eGeMAPS.
    """
    out = {"jitter_local": 0.0, "shimmer_local": 0.0, "hnr_db": 0.0}
    f0v = f0[voiced]
    if f0v.size < 3:
        return out
    periods = 1.0 / np.clip(f0v, 1e-6, None)
    out["jitter_local"] = float(np.mean(np.abs(np.diff(periods))) / np.mean(periods))

    hop = 160
    frame_idx = np.flatnonzero(voiced)
    amps = []
    for fi in frame_idx:
        s, e = fi * hop, fi * hop + 400
        seg = x[s:e]
        if seg.size:
            amps.append(float(np.abs(seg).max()))
    amps_arr = np.asarray(amps)
    if amps_arr.size >= 3 and amps_arr.mean() > 0:
        out["shimmer_local"] = float(np.mean(np.abs(np.diff(amps_arr))) / amps_arr.mean())

    hnrs = []
    for fi, f in zip(frame_idx, f0v):
        s, e = fi * hop, fi * hop + 1024
        seg = x[s:e]
        if seg.size < 512:
            continue
        seg = seg - seg.mean()
        denom = float(np.dot(seg, seg))
        if denom <= 0:
            continue
        lag = int(round(sr / max(f, 1e-6)))
        if lag <= 0 or lag >= seg.size:
            continue
        r = float(np.dot(seg[:-lag], seg[lag:])) / denom
        r = min(max(r, 1e-6), 1 - 1e-6)
        hnrs.append(10.0 * np.log10(r / (1.0 - r)))
    if hnrs:
        out["hnr_db"] = float(np.mean(hnrs))
    return out


def _core_features_librosa(waves: Sequence[np.ndarray]) -> tuple[np.ndarray, list[str]]:
    import librosa

    rows, names = [], None
    for x in waves:
        feat: dict[str, float] = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f0, voiced, _ = librosa.pyin(
                x, fmin=60.0, fmax=500.0, sr=FEATURE_SR, frame_length=1024, hop_length=160
            )
        f0 = np.nan_to_num(f0, nan=0.0)
        voiced = np.nan_to_num(voiced, nan=False).astype(bool)
        f0v = f0[voiced]
        feat["f0_mean"] = float(f0v.mean()) if f0v.size else 0.0
        feat["f0_std"] = float(f0v.std()) if f0v.size else 0.0
        feat["f0_p20"] = float(np.percentile(f0v, 20)) if f0v.size else 0.0
        feat["f0_p50"] = float(np.percentile(f0v, 50)) if f0v.size else 0.0
        feat["f0_p80"] = float(np.percentile(f0v, 80)) if f0v.size else 0.0
        feat["voiced_fraction"] = float(voiced.mean()) if voiced.size else 0.0
        feat.update(_jitter_shimmer_hnr(x, f0, voiced, FEATURE_SR))

        S = np.abs(librosa.stft(x, n_fft=1024, hop_length=160))
        for nm, val in [
            ("centroid", librosa.feature.spectral_centroid(S=S, sr=FEATURE_SR)),
            ("bandwidth", librosa.feature.spectral_bandwidth(S=S, sr=FEATURE_SR)),
            ("rolloff", librosa.feature.spectral_rolloff(S=S, sr=FEATURE_SR)),
            ("flatness", librosa.feature.spectral_flatness(S=S)),
            ("zcr", librosa.feature.zero_crossing_rate(x, frame_length=1024, hop_length=160)),
        ]:
            feat[f"spec_{nm}_mean"] = float(val.mean())
            feat[f"spec_{nm}_std"] = float(val.std())
        flux = np.diff(S, axis=1)
        feat["spec_flux_mean"] = float(np.abs(flux).mean()) if flux.size else 0.0
        feat["loudness_rms_mean"] = float(np.sqrt(np.mean(x**2)))

        mfcc = librosa.feature.mfcc(y=x, sr=FEATURE_SR, n_mfcc=13, hop_length=160)
        dmfcc = librosa.feature.delta(mfcc) if mfcc.shape[1] > 9 else np.zeros_like(mfcc)
        for i in range(13):
            feat[f"mfcc{i + 1}_mean"] = float(mfcc[i].mean())
            feat[f"mfcc{i + 1}_std"] = float(mfcc[i].std())
            feat[f"dmfcc{i + 1}_std"] = float(dmfcc[i].std())

        if names is None:
            names = list(feat.keys())
        rows.append([feat[k] for k in names])
    return np.asarray(rows, dtype=np.float32), (names or [])


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #


def extract_features(
    rows: Sequence[dict[str, Any]],
    *,
    corpus_id: str | None = None,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    force: bool = False,
    verbose: bool = True,
) -> EmbeddingBundle:
    """Extract (or load from cache) the classical feature matrix for `rows`.

    Returns the same `EmbeddingBundle` type as `voicehealth.embed` so the
    benchmark harness treats handcrafted features and SSL embeddings identically.
    `bundle.backend` is recorded in the manifest and in the artifact JSON.
    """
    backend = backend_id()
    corpus_id = corpus_id or str(rows[0].get("corpus", "unknown"))

    manifest: dict[str, Any] = {
        "encoder_id": backend,
        "encoder_key": "egemaps" if backend.startswith("opensmile") else "classical",
        "encoder_revision": _feature_backend_revision(backend),
        "corpus_id": corpus_id,
        "n_files": len(rows),
        "source_file_hashes": _source_file_hashes(rows),
        "sample_rate": FEATURE_SR,
        "pooling": "functionals",
        **PREPROCESS_POLICY,
        "lib_versions": _lib_versions(),
    }
    chash = content_hash(manifest)
    manifest["content_hash"] = chash
    cache_path = Path(cache_dir) / manifest["encoder_key"] / corpus_id / f"{chash}.npz"

    if cache_path.exists() and not force:
        if verbose:
            print(f"[features] cache hit {cache_path}")
        return EmbeddingBundle.from_npz(cache_path)

    if verbose:
        print(f"[features] backend={backend} n={len(rows)}")

    waves, raw_dur, raw_rms = [], [], []
    for i, r in enumerate(rows):
        w, d, rms = load_audio(r["abs_path"], FEATURE_SR)
        waves.append(w)
        raw_dur.append(d)
        raw_rms.append(rms)
        if verbose and (i + 1) % 200 == 0:
            print(f"[features]   decoded {i + 1}/{len(rows)}", flush=True)

    if backend.startswith("opensmile"):
        X, names = _egemaps_opensmile(waves)
    else:
        X, names = _core_features_librosa(waves)

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    manifest["feature_names"] = names
    manifest["n_features"] = int(X.shape[1])

    bundle = EmbeddingBundle(
        X=X,
        recording_ids=np.array([r["recording_id"] for r in rows]),
        speaker_ids=np.array([str(r["speaker_id"]) for r in rows]),
        labels=np.array([str(r.get("label", "")) for r in rows]),
        sex=np.array([str(r.get("sex", "")) for r in rows]),
        age=np.array([float(r["age"]) if r.get("age") else np.nan for r in rows], dtype=np.float32),
        duration_s=np.asarray(raw_dur, dtype=np.float32),
        rms=np.asarray(raw_rms, dtype=np.float32),
        src_sha256=np.array([str(r.get("sha256", "")) for r in rows]),
        backbone=manifest["encoder_key"],
        pooling="functionals",
        hash=chash,
        cache_path=cache_path,
        manifest=manifest,
    )
    bundle.to_npz(cache_path)
    if verbose:
        print(f"[features] wrote {cache_path}  X={X.shape}")
    return bundle


def _feature_backend_revision(backend: str) -> str:
    if backend.startswith("opensmile"):
        try:
            import opensmile

            return f"opensmile-python {opensmile.__version__}"
        except Exception:  # noqa: BLE001
            return "unknown"
    try:
        import librosa

        return f"librosa {librosa.__version__}"
    except Exception:  # noqa: BLE001
        return "unknown"


def describe_backend() -> dict[str, Any]:
    b = backend_id()
    return {
        "backend": b,
        "is_real_egemaps": b.startswith("opensmile"),
        "citation": (
            "Eyben, Scherer, Schuller et al., 2016 IEEE T-AFFC "
            "'The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and "
            "Affective Computing' (doi:10.1109/TAFFC.2015.2457417)"
            if b.startswith("opensmile")
            else "reimplementation -- NOT eGeMAPS; core set only, see module docstring"
        ),
        "revision": _feature_backend_revision(b),
    }


if __name__ == "__main__":
    print(json.dumps(describe_backend(), indent=2))
    _ = hashlib  # keep the import meaningful for callers importing helpers
