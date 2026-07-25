"""Canonicalise a voice corpus to 16 kHz mono float32 WAV + a manifest.

Usage
-----
    python scripts/preprocess_audio.py --corpus svd
    python scripts/preprocess_audio.py --corpus coughvid [--limit N]
    python scripts/preprocess_audio.py --corpus coswara [--limit-dates N]

Output
------
    data/interim/<corpus>/*.wav          16 kHz mono float32
    data/interim/<corpus>/manifest.csv   the contract every later stage reads
    data/interim/<corpus>/failures.csv   one row per file we could not use

Manifest contract (required columns, in this order, first):

    path,corpus,speaker_id,session_id,label,sex,age,duration_s,orig_format,sha256

Extra columns are appended after those ten: `pathology`, `task`,
`speaker_id_provenance`, `orig_sample_rate`, `src_sha256`. Consumers that only
know the ten required columns are unaffected.

`sha256` is the digest of the *decoded* 16 kHz waveform bytes, so it detects the
same audio arriving twice under different filenames or container formats --
i.e. it is the leakage check. `src_sha256` digests the source file for
provenance.

THE SPEAKER-ID RULE
-------------------
A row with no speaker_id is a FATAL error, not a warning: without it the file
cannot be assigned to a speaker-disjoint split, so including it would silently
permit train/test leakage. Such files are excluded from the manifest, written
to failures.csv, and counted.

`speaker_id_provenance` records how the id was obtained and is what makes the
rule honest rather than cosmetic:

    participant     the corpus identifies the human (SVD SprecherID, Coswara id).
                    Speaker-disjoint splitting is possible.
    recording_proxy the corpus only identifies the *recording*. The id is a
                    stand-in and CANNOT support a speaker-disjoint claim,
                    because one person may have contributed many recordings.
                    COUGHVID is in this category (see PREPROCESSING_STATUS.md).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsp_reader import NSPError, read_nsp  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
INTERIM = REPO / "data" / "interim"
TARGET_SR = 16000

REQUIRED_COLUMNS = [
    "path", "corpus", "speaker_id", "session_id", "label",
    "sex", "age", "duration_s", "orig_format", "sha256",
]
EXTRA_COLUMNS = [
    "pathology", "task", "speaker_id_provenance", "orig_sample_rate", "src_sha256",
]


@dataclass
class Row:
    path: str = ""
    corpus: str = ""
    speaker_id: str = ""
    session_id: str = ""
    label: str = ""
    sex: str = ""
    age: str = ""
    duration_s: float = 0.0
    orig_format: str = ""
    sha256: str = ""
    pathology: str = ""
    task: str = ""
    speaker_id_provenance: str = ""
    orig_sample_rate: int = 0
    src_sha256: str = ""


@dataclass
class Stats:
    found: int = 0
    decoded: int = 0
    failed: int = 0
    skipped_no_speaker: int = 0
    incomplete_reason: str = ""  # set when a run stops before exhausting the corpus
    failures: list[tuple[str, str]] = field(default_factory=list)

    def fail(self, name: str, reason: str) -> None:
        self.failed += 1
        self.failures.append((name, reason))


# --------------------------------------------------------------------------
# audio i/o
# --------------------------------------------------------------------------

def to_target_sr(x: np.ndarray, sr: int) -> np.ndarray:
    """Resample to TARGET_SR. Uses an exact rational ratio (50 kHz -> 16 kHz
    is 8/25), which resample_poly does with a polyphase FIR -- no drift and
    proper anti-aliasing, unlike naive decimation."""
    if sr == TARGET_SR:
        return x.astype(np.float32, copy=False)
    from math import gcd
    g = gcd(int(sr), TARGET_SR)
    return resample_poly(x, TARGET_SR // g, int(sr) // g).astype(np.float32)


def write_wav(dest: Path, x: np.ndarray) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Guard the float32 contract: clip rather than let a resampler overshoot
    # wrap around in a downstream int conversion.
    wavfile.write(dest, TARGET_SR, np.clip(x, -1.0, 1.0).astype(np.float32))


def dir_size_gb(p: Path) -> float:
    return sum(f.stat().st_size for f in p.glob("*.wav")) / 1e9


def free_disk_gb(p: Path) -> float:
    return shutil.disk_usage(p).free / 1e9


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def ffmpeg_decode(src: Path) -> np.ndarray:
    """Decode any container ffmpeg understands to 16 kHz mono float32.

    ffmpeg does the resample itself (soxr), so this returns final-rate audio.
    """
    cmd = [
        "ffmpeg", "-v", "error", "-nostdin", "-i", str(src),
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ar", str(TARGET_SR), "-ac", "1", "-",
    ]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg: {p.stderr.decode('utf-8', 'replace').strip()[:200]}")
    x = np.frombuffer(p.stdout, dtype="<f4")
    if x.size == 0:
        raise RuntimeError("ffmpeg produced no samples")
    return x.copy()


def audio_quality_flag(x: np.ndarray) -> str | None:
    """Return a reason string if the waveform is unusable, else None.

    Catches the two failure modes that a decoder can produce while still
    'succeeding': all-zero output (wrong offset / empty payload) and a
    constant-DC block. Both would otherwise flow silently into training.
    """
    if x.size < TARGET_SR // 10:  # < 100 ms
        return f"too short ({x.size / TARGET_SR:.3f}s)"
    peak = float(np.abs(x).max())
    if peak == 0.0:
        return "digital silence"
    if float(x.std()) < 1e-6:
        return "constant signal (no variation)"
    return None


# --------------------------------------------------------------------------
# SVD
# --------------------------------------------------------------------------
# Filenames are "<AufnahmeID>-<task>.nsp", e.g. "10-a_h.nsp" -> session 10,
# task "a_h" (vowel /a/, high pitch). The numeric prefix is the session id and
# joins to svd_inventory.csv / voice_data.csv, which carry SprecherID.
SVD_NAME = re.compile(r"^(\d+)-(.+)$")


def svd_metadata() -> pd.DataFrame:
    """Session-level metadata keyed by AufnahmeID.

    svd_inventory.csv is voice_data.csv plus an `_archive` column naming the
    pathology folder, so it is preferred; we fall back to voice_data.csv.
    """
    inv = RAW / "svd_meta" / "svd_inventory.csv"
    vd = RAW / "svd_meta" / "voice_data.csv"
    df = pd.read_csv(inv if inv.exists() else vd)
    if "_archive" not in df.columns:
        df["_archive"] = ""
    return df.drop_duplicates(subset="AufnahmeID").set_index("AufnahmeID")


def svd_age(born: str, recorded: str) -> str:
    try:
        b, r = pd.to_datetime(born), pd.to_datetime(recorded)
        return str(int((r - b).days // 365.25))
    except Exception:
        return ""


def svd_rows(meta: pd.DataFrame, files: list[tuple[str, Path]], stats: Stats,
             out_dir: Path) -> list[Row]:
    """files: (display_name, path_on_disk) for .nsp files already on disk."""
    rows: list[Row] = []
    for name, src in files:
        stats.found += 1
        stem = Path(name).stem
        m = SVD_NAME.match(stem)
        if not m:
            stats.skipped_no_speaker += 1
            stats.fail(name, "filename has no numeric session prefix -> no speaker_id")
            continue
        session = int(m.group(1))
        task = m.group(2)

        if session not in meta.index:
            stats.skipped_no_speaker += 1
            stats.fail(name, f"session {session} absent from SVD metadata -> no speaker_id")
            continue
        md = meta.loc[session]
        speaker = md.get("SprecherID")
        if pd.isna(speaker):
            stats.skipped_no_speaker += 1
            stats.fail(name, f"session {session} has null SprecherID")
            continue

        try:
            sr, x = read_nsp(src)
            y = to_target_sr(x, sr)
        except (NSPError, Exception) as e:
            stats.fail(name, f"{type(e).__name__}: {e}")
            continue
        bad = audio_quality_flag(y)
        if bad:
            stats.fail(name, bad)
            continue

        archive = str(md.get("_archive", "") or "")
        pathology = "" if archive == "healthy" else str(md.get("Pathologien", "") or archive)
        label = "healthy" if archive == "healthy" else "pathological"

        dest = out_dir / f"{session}-{task}.wav"
        write_wav(dest, y)
        stats.decoded += 1
        rows.append(Row(
            path=str(dest.relative_to(REPO)).replace("\\", "/"),
            corpus="svd",
            speaker_id=f"svd_{int(speaker)}",
            session_id=f"svd_sess_{session}",
            label=label,
            sex={"w": "F", "m": "M"}.get(str(md.get("Geschlecht", "")).strip(), ""),
            age=svd_age(md.get("Geburtsdatum"), md.get("AufnahmeDatum")),
            duration_s=round(len(y) / TARGET_SR, 4),
            orig_format="nsp",
            sha256=sha256_bytes(y.tobytes()),
            pathology=pathology,
            task=task,
            speaker_id_provenance="participant",
            orig_sample_rate=sr,
            src_sha256=sha256_file(src),
        ))
    return rows


def run_svd(args) -> tuple[list[Row], Stats]:
    out_dir = INTERIM / "svd"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = svd_metadata()
    stats = Stats()

    files: list[tuple[str, Path]] = []
    pilot = RAW / "svd_pilot"
    if pilot.exists():
        files += [(p.name, p) for p in sorted(pilot.rglob("*.nsp"))]

    # Extract the pathology zips, then treat them like the pilot directory.
    extracted = RAW / "svd_extracted"
    zips = sorted((RAW / "svd").glob("*.zip"))
    for z in zips:
        target = extracted / z.stem
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(target)
            except Exception as e:
                stats.fail(z.name, f"zip extract failed: {e}")
                continue
        files += [(p.name, p) for p in sorted(target.rglob("*.nsp"))]

    print(f"[svd] {len(zips)} pathology zips, {len(files)} .nsp files total")
    rows = svd_rows(meta, files, stats, out_dir)
    return rows, stats


# --------------------------------------------------------------------------
# COUGHVID
# --------------------------------------------------------------------------
# Every recording carries a unique uuid and NOTHING links two recordings to the
# same person, so speaker_id_provenance is 'recording_proxy'. See the module
# docstring and PREPROCESSING_STATUS.md.

def run_coughvid(args) -> tuple[list[Row], Stats]:
    out_dir = INTERIM / "coughvid"
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = Stats()
    rows: list[Row] = []

    zpath = RAW / "coughvid" / "public_dataset_v3.zip"
    meta = pd.read_csv(RAW / "coughvid" / "metadata_compiled.csv").set_index("uuid")

    # Standard CoughVID quality protocol: keep recordings the dataset's own
    # cough classifier is confident about, and that carry a status label.
    keep = meta
    if args.cough_threshold is not None:
        keep = keep[keep["cough_detected"] >= args.cough_threshold]
    if not args.include_unlabeled:
        keep = keep[keep["status"].notna()]
    wanted = set(keep.index)

    with zipfile.ZipFile(zpath) as zf:
        members = [
            n for n in zf.namelist()
            if n.rsplit(".", 1)[-1].lower() in ("webm", "ogg", "wav")
            and Path(n).stem in wanted
        ]
    members.sort()
    if args.limit:
        members = members[: args.limit]
    print(f"[coughvid] {len(wanted)} uuids pass filter, {len(members)} media members to decode "
          f"({args.workers} workers)")

    # The work is one ffmpeg subprocess per file, so it is dominated by process
    # spawn and is embarrassingly parallel; threads are fine because the real
    # work happens outside the GIL. ZipFile is NOT thread-safe, so each worker
    # keeps its own handle.
    tmpdir = Path(tempfile.mkdtemp(prefix="coughvid_"))
    local = threading.local()
    lock = threading.Lock()
    done = [0]

    def handle(name: str):
        zfh = getattr(local, "zf", None)
        if zfh is None:
            zfh = local.zf = zipfile.ZipFile(zpath)
        uuid = Path(name).stem
        ext = name.rsplit(".", 1)[-1].lower()
        tmp = tmpdir / f"{threading.get_ident()}_{Path(name).name}"
        try:
            # Stream one member at a time: the zip is 2.9 GB uncompressed and
            # full extraction would not fit the free disk budget.
            with zfh.open(name) as fsrc, open(tmp, "wb") as fdst:
                shutil.copyfileobj(fsrc, fdst)
            src_hash = sha256_file(tmp)
            y = ffmpeg_decode(tmp)
        except Exception as e:
            return name, None, f"{type(e).__name__}: {e}"
        finally:
            tmp.unlink(missing_ok=True)

        bad = audio_quality_flag(y)
        if bad:
            return name, None, bad

        md = meta.loc[uuid]
        status = md.get("status")
        write_wav(out_dir / f"{uuid}.wav", y)
        return name, Row(
            path=f"data/interim/coughvid/{uuid}.wav",
            corpus="coughvid",
            speaker_id=f"coughvid_{uuid}",
            session_id=f"coughvid_{uuid}",
            label=("" if pd.isna(status) else str(status)),
            sex={"male": "M", "female": "F"}.get(str(md.get("gender", "")).strip(), ""),
            age=("" if pd.isna(md.get("age")) else str(int(float(md["age"])))),
            duration_s=round(len(y) / TARGET_SR, 4),
            orig_format=ext,
            sha256=sha256_bytes(y.tobytes()),
            pathology="" if pd.isna(status) or status == "healthy" else str(status),
            task="cough",
            speaker_id_provenance="recording_proxy",
            orig_sample_rate=0,  # container-dependent; ffmpeg resamples internally
            src_sha256=src_hash,
        ), None

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            for name, row, err in ex.map(handle, members):
                stats.found += 1
                if err:
                    stats.fail(name, err)
                else:
                    stats.decoded += 1
                    rows.append(row)
                with lock:
                    done[0] += 1
                    if done[0] % 1000 == 0:
                        print(f"  [coughvid] {done[0]}/{len(members)} "
                              f"decoded={stats.decoded} failed={stats.failed}", flush=True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return rows, stats


# --------------------------------------------------------------------------
# COSWARA
# --------------------------------------------------------------------------
# Layout: data/raw/coswara/<date>/<date>.tar.gz.a{a,b,c,...} -- a single tarball
# split across parts. Parts must be concatenated in sorted order before
# untarring. Inside: <participant_id>/<recording>.wav, and the participant dir
# name IS the speaker id (it joins to combined_data.csv `id`).

def run_coswara(args) -> tuple[list[Row], Stats]:
    out_dir = INTERIM / "coswara"
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = Stats()
    rows: list[Row] = []

    root = RAW / "coswara"
    meta = pd.read_csv(root / "combined_data.csv").drop_duplicates("id").set_index("id")

    dates = sorted(d for d in root.iterdir() if d.is_dir() and d.name.isdigit())
    if args.limit_dates:
        dates = dates[: args.limit_dates]
    print(f"[coswara] {len(dates)} date archives to process")

    stopped_early = None
    for di, ddir in enumerate(dates):
        # Coswara is ~16 GB once decoded, which does not fit the free disk on
        # this host. Stop cleanly between dates rather than filling the volume
        # out from under the rest of the machine; the manifest written so far
        # stays valid and PREPROCESSING_STATUS.md records the shortfall.
        produced = dir_size_gb(out_dir)
        free = free_disk_gb(out_dir)
        if args.max_output_gb and produced >= args.max_output_gb:
            stopped_early = (f"output budget reached ({produced:.1f} GB >= "
                             f"--max-output-gb {args.max_output_gb})")
        elif free < args.min_free_gb:
            stopped_early = (f"free disk {free:.1f} GB below --min-free-gb "
                             f"{args.min_free_gb}")
        if stopped_early:
            msg = (f"{stopped_early}; processed {di} of {len(dates)} date archives, "
                   f"{len(dates) - di} NOT processed")
            print(f"  [coswara] STOPPING EARLY: {msg}", flush=True)
            stats.incomplete_reason = msg
            stats.fail("<run>", f"INCOMPLETE: {msg}")
            break

        parts = sorted(ddir.glob(f"{ddir.name}.tar.gz.*"))
        if not parts:
            stats.fail(ddir.name, "no tar.gz parts found")
            continue

        tmpdir = Path(tempfile.mkdtemp(prefix=f"coswara_{ddir.name}_"))
        tarball = tmpdir / f"{ddir.name}.tar.gz"
        try:
            with open(tarball, "wb") as out:
                for p in parts:
                    with open(p, "rb") as f:
                        shutil.copyfileobj(f, out, 1 << 22)
            with tarfile.open(tarball, "r:gz") as tf:
                tf.extractall(tmpdir)
            tarball.unlink(missing_ok=True)

            def handle(wav: Path):
                participant = wav.parent.name
                if participant not in meta.index:
                    return wav, None, f"participant {participant} absent from combined_data.csv", True
                try:
                    src_hash = sha256_file(wav)
                    y = ffmpeg_decode(wav)
                except Exception as e:
                    return wav, None, f"{type(e).__name__}: {e}", False
                bad = audio_quality_flag(y)
                if bad:
                    return wav, None, bad, False

                md = meta.loc[participant]
                status = str(md.get("covid_status", "") or "")
                write_wav(out_dir / f"{participant}__{wav.stem}.wav", y)
                return wav, Row(
                    path=f"data/interim/coswara/{participant}__{wav.stem}.wav",
                    corpus="coswara",
                    speaker_id=f"coswara_{participant}",
                    session_id=f"coswara_{participant}_{ddir.name}",
                    label=status,
                    sex={"male": "M", "female": "F"}.get(str(md.get("g", "")).strip(), ""),
                    age=("" if pd.isna(md.get("a")) else str(md["a"])),
                    duration_s=round(len(y) / TARGET_SR, 4),
                    orig_format="wav",
                    sha256=sha256_bytes(y.tobytes()),
                    pathology="" if status.startswith("healthy") else status,
                    task=wav.stem,
                    speaker_id_provenance="participant",
                    orig_sample_rate=0,
                    src_sha256=src_hash,
                ), None, False

            wavs = sorted(tmpdir.rglob("*.wav"))
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                for wav, row, err, no_speaker in ex.map(handle, wavs):
                    stats.found += 1
                    if err:
                        if no_speaker:
                            stats.skipped_no_speaker += 1
                        stats.fail(f"{wav.parent.name}/{wav.name}", err)
                    else:
                        stats.decoded += 1
                        rows.append(row)
        except Exception as e:
            stats.fail(ddir.name, f"archive failed: {type(e).__name__}: {e}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        print(f"  [coswara] {di + 1}/{len(dates)} {ddir.name} decoded={stats.decoded} failed={stats.failed}", flush=True)
    return rows, stats


# --------------------------------------------------------------------------

RUNNERS = {"svd": run_svd, "coughvid": run_coughvid, "coswara": run_coswara}


def write_outputs(corpus: str, rows: list[Row], stats: Stats) -> None:
    out_dir = INTERIM / corpus
    out_dir.mkdir(parents=True, exist_ok=True)

    mpath = out_dir / "manifest.csv"
    with open(mpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS + EXTRA_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))

    fpath = out_dir / "failures.csv"
    with open(fpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "reason"])
        w.writerows(stats.failures)

    df = pd.DataFrame([asdict(r) for r in rows])
    summary = {
        "corpus": corpus,
        "files_found": stats.found,
        "files_decoded": stats.decoded,
        "files_failed": stats.failed,
        "excluded_no_speaker_id": stats.skipped_no_speaker,
        "complete": not stats.incomplete_reason,
        "incomplete_reason": stats.incomplete_reason,
        "total_duration_s": round(float(df.duration_s.sum()), 2) if len(df) else 0.0,
        "n_speakers": int(df.speaker_id.nunique()) if len(df) else 0,
        "n_sessions": int(df.session_id.nunique()) if len(df) else 0,
        "label_counts": df.label.value_counts().to_dict() if len(df) else {},
        "speaker_id_provenance": df.speaker_id_provenance.value_counts().to_dict() if len(df) else {},
        "speaker_disjoint_split_possible": bool(
            len(df) and (df.speaker_id_provenance == "participant").all()
        ),
        "duplicate_audio_sha256": int(df.sha256.duplicated().sum()) if len(df) else 0,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # ASCII only: the Windows console is cp1252 and will crash on unicode.
    print("\n" + "=" * 62)
    print(f"CORPUS: {corpus}")
    print("=" * 62)
    for k, v in summary.items():
        print(f"  {k:32s} {v}")
    print(f"  manifest -> {mpath}")
    print(f"  failures -> {fpath}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", required=True, choices=sorted(RUNNERS))
    ap.add_argument("--limit", type=int, default=0,
                    help="cap number of media files (coughvid)")
    ap.add_argument("--limit-dates", type=int, default=0,
                    help="cap number of date archives (coswara)")
    ap.add_argument("--cough-threshold", type=float, default=0.8,
                    help="coughvid: min cough_detected (default 0.8; pass -1 to disable)")
    ap.add_argument("--include-unlabeled", action="store_true",
                    help="coughvid: keep recordings with no status label")
    ap.add_argument("--workers", type=int, default=8,
                    help="parallel ffmpeg decoders (default 8)")
    ap.add_argument("--max-output-gb", type=float, default=0.0,
                    help="coswara: stop between dates once output exceeds this (0 = no cap)")
    ap.add_argument("--min-free-gb", type=float, default=4.0,
                    help="coswara: stop between dates if free disk drops below this")
    args = ap.parse_args()
    if args.cough_threshold is not None and args.cough_threshold < 0:
        args.cough_threshold = None

    rows, stats = RUNNERS[args.corpus](args)
    write_outputs(args.corpus, rows, stats)


if __name__ == "__main__":
    main()
