"""Pure-Python reader for Kay/CSL NSP (`.nsp`) and EGG (`.egg`) files.

The Saarbruecken Voice Database ships audio as Kay Elemetrics Computerized Speech
Lab containers, which neither `soundfile` nor `ffmpeg` can open. The layout was
recovered by hexdumping `data/raw/svd_pilot/healthy/10-a_h.nsp` and verified
against all 778 audio files in the pilot directory:

    offset  bytes  content
    0       8      magic b"FORMDS16"
    8       4      uint32 LE  size of everything after byte 12 (== filesize - 12)
    12      ...    chunk stream

Each chunk is a 4-byte ASCII id, a uint32 LE payload size, then the payload
(padded to an even boundary, IFF-style). Two chunks appear in SVD:

    HEDR   32 bytes   0..19  ASCII timestamp e.g. b"Nov 20 14:49:57 1997"
                      20..23 uint32 LE sample rate      (50000 throughout SVD)
                      24..27 uint32 LE sample count
                      28..29 int16  peak amplitude, channel A (-1 => absent)
                      30..31 int16  peak amplitude, channel B (-1 => absent)
    SDA_   N bytes    int16 LE PCM, channel A

Note the byte order: unlike canonical IFF/RIFF the form type ("DS16") precedes
the size field, and sizes are little- not big-endian.

The HEDR sample count and the SDA_ payload can disagree slightly (observed on
`10-iau-egg.egg`: header says 1884799 samples, payload holds 1883775). The
payload is authoritative, so we take the smaller of the two.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

NSP_MAGIC = b"FORMDS16"
_HEDR = b"HEDR"
# Channel-A audio. NSP also defines SD_B / SDAB for two-channel captures; SVD
# stores the microphone and the electroglottograph in separate files, so every
# file we have is single-channel SDA_. Listed for forward compatibility.
_DATA_CHUNKS = (b"SDA_", b"SD_B", b"SDAB")


class NSPError(ValueError):
    """Raised when a file is not a well-formed NSP container."""


def read_nsp(path: str | Path) -> tuple[int, np.ndarray]:
    """Decode an NSP/EGG file to (sample_rate, float32 mono in [-1, 1]).

    Raises NSPError if the magic, the chunk stream, or the audio payload is
    malformed. Callers are expected to treat that as a decode failure and
    record the reason rather than substituting silence.
    """
    path = Path(path)
    raw = path.read_bytes()

    if len(raw) < 12 or raw[:8] != NSP_MAGIC:
        raise NSPError(f"bad magic {raw[:8]!r} (expected {NSP_MAGIC!r})")

    declared = struct.unpack("<I", raw[8:12])[0]
    if declared + 12 != len(raw):
        # Not fatal on its own -- some writers pad -- but worth surfacing when
        # the gap is large enough to mean a truncated download.
        if declared + 12 > len(raw):
            raise NSPError(
                f"truncated: header declares {declared + 12} bytes, file has {len(raw)}"
            )

    chunks: dict[bytes, tuple[int, int]] = {}
    off = 12
    while off + 8 <= len(raw):
        cid = raw[off : off + 4]
        size = struct.unpack("<I", raw[off + 4 : off + 8])[0]
        chunks[cid] = (off + 8, size)
        off += 8 + size + (size & 1)  # IFF word alignment

    if _HEDR not in chunks:
        raise NSPError(f"no HEDR chunk (found {sorted(chunks)})")
    hoff, hsize = chunks[_HEDR]
    if hsize < 32:
        raise NSPError(f"HEDR too short ({hsize} bytes, need 32)")
    sample_rate, n_samples = struct.unpack("<II", raw[hoff + 20 : hoff + 28])
    if not (1000 <= sample_rate <= 192000):
        raise NSPError(f"implausible sample rate {sample_rate}")

    data_id = next((c for c in _DATA_CHUNKS if c in chunks), None)
    if data_id is None:
        raise NSPError(f"no audio chunk (found {sorted(chunks)})")
    doff, dsize = chunks[data_id]
    dsize = min(dsize, len(raw) - doff)

    # The payload is authoritative when it disagrees with the header count.
    n = min(n_samples, dsize // 2)
    if n == 0:
        raise NSPError("zero-length audio payload")

    pcm = np.frombuffer(raw, dtype="<i2", count=n, offset=doff)
    return sample_rate, (pcm.astype(np.float32) / 32768.0)
