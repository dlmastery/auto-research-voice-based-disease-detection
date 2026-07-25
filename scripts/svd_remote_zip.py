"""Read the Saarbruecken Voice Database zips on Zenodo via HTTP range requests.

The SVD Zenodo deposit (DOI 10.5281/zenodo.16874898, CC-BY-4.0) is 38 GB in total;
`healthy.zip` alone is 6.0 GB. Zenodo serves `Accept-Ranges: bytes`, so the ZIP
central directory can be read from the tail of the file and individual members
extracted without downloading the whole archive. This keeps the pilot to a few MB.

Uses curl as the HTTP client: Python's ssl stack rejects this host's certificate
chain in this environment, while `curl --ssl-no-revoke` works.

Commands:
    python scripts/svd_remote_zip.py list <archive.zip> [--limit N]
    python scripts/svd_remote_zip.py pilot <archive.zip> --speakers N --outdir DIR
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import zlib
from pathlib import Path

RECORD = "16874898"
BASE = f"https://zenodo.org/api/records/{RECORD}/files"

EOCD_SIG = b"PK\x05\x06"
EOCD64_SIG = b"PK\x06\x06"
EOCD64_LOC_SIG = b"PK\x06\x07"
CEN_SIG = b"PK\x01\x02"


def _url(archive: str) -> str:
    from urllib.parse import quote
    return f"{BASE}/{quote(archive)}/content"


def fetch_range(url: str, start: int, end: int) -> bytes:
    """Inclusive byte range fetch via curl."""
    proc = subprocess.run(
        ["curl", "-sS", "--ssl-no-revoke", "-L", "--max-time", "300",
         "-r", f"{start}-{end}", "--output", "-", url],
        capture_output=True, timeout=360,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: {proc.stderr.decode(errors='replace')[:300]}")
    return proc.stdout


def total_size(url: str) -> int:
    proc = subprocess.run(
        ["curl", "-sS", "--ssl-no-revoke", "-L", "--max-time", "120", "-I", url],
        capture_output=True, text=True, timeout=180,
    )
    for line in proc.stdout.splitlines():
        if line.lower().startswith("content-length:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError("no content-length")


def central_directory(url: str, size: int) -> list[dict]:
    """Locate and parse the (ZIP64-aware) central directory."""
    tail_len = min(65_536 + 64, size)
    tail = fetch_range(url, size - tail_len, size - 1)

    idx = tail.rfind(EOCD_SIG)
    if idx < 0:
        raise RuntimeError("EOCD not found")

    cd_size, cd_off, n_entries = struct.unpack("<IIH", tail[idx + 12:idx + 20] + tail[idx + 10:idx + 12])
    # unpack above reads: cd_size(4) cd_off(4) then n_entries(2) taken from offset 10
    n_entries = struct.unpack("<H", tail[idx + 10:idx + 12])[0]
    cd_size = struct.unpack("<I", tail[idx + 12:idx + 16])[0]
    cd_off = struct.unpack("<I", tail[idx + 16:idx + 20])[0]

    # ZIP64: sentinel values mean the real numbers live in the ZIP64 EOCD record.
    if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF or n_entries == 0xFFFF:
        loc = tail.rfind(EOCD64_LOC_SIG)
        if loc < 0:
            raise RuntimeError("ZIP64 locator not found")
        eocd64_off = struct.unpack("<Q", tail[loc + 8:loc + 16])[0]
        blk = fetch_range(url, eocd64_off, eocd64_off + 55)
        if blk[:4] != EOCD64_SIG:
            raise RuntimeError("bad ZIP64 EOCD signature")
        n_entries = struct.unpack("<Q", blk[32:40])[0]
        cd_size = struct.unpack("<Q", blk[40:48])[0]
        cd_off = struct.unpack("<Q", blk[48:56])[0]

    cd = fetch_range(url, cd_off, cd_off + cd_size - 1)

    entries: list[dict] = []
    p = 0
    while p < len(cd) - 4 and cd[p:p + 4] == CEN_SIG:
        method = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize = struct.unpack("<I", cd[p + 20:p + 24])[0]
        usize = struct.unpack("<I", cd[p + 24:p + 28])[0]
        n_len = struct.unpack("<H", cd[p + 28:p + 30])[0]
        e_len = struct.unpack("<H", cd[p + 30:p + 32])[0]
        c_len = struct.unpack("<H", cd[p + 32:p + 34])[0]
        lho = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + n_len].decode("utf-8", errors="replace")
        extra = cd[p + 46 + n_len:p + 46 + n_len + e_len]

        # ZIP64 extra field 0x0001 overrides the 0xFFFFFFFF sentinels, in order.
        if 0xFFFFFFFF in (csize, usize, lho):
            q = 0
            while q + 4 <= len(extra):
                hid, hsz = struct.unpack("<HH", extra[q:q + 4])
                if hid == 0x0001:
                    vals = extra[q + 4:q + 4 + hsz]
                    v = 0
                    if usize == 0xFFFFFFFF and v + 8 <= len(vals):
                        usize = struct.unpack("<Q", vals[v:v + 8])[0]; v += 8
                    if csize == 0xFFFFFFFF and v + 8 <= len(vals):
                        csize = struct.unpack("<Q", vals[v:v + 8])[0]; v += 8
                    if lho == 0xFFFFFFFF and v + 8 <= len(vals):
                        lho = struct.unpack("<Q", vals[v:v + 8])[0]; v += 8
                    break
                q += 4 + hsz

        entries.append({"name": name, "method": method, "csize": csize,
                        "usize": usize, "offset": lho})
        p += 46 + n_len + e_len + c_len

    return entries


def extract_many(url: str, entries: list[dict]) -> dict[str, bytes]:
    """Extract many members with ONE range request.

    Zip members are stored contiguously in the order they were added, so for a
    block of consecutive speakers the union of their byte ranges is a single span.
    Fetching that span once turns ~2N latency-bound requests into 1 bandwidth-bound
    request - the difference between hours and seconds for a 20-speaker pilot.
    """
    if not entries:
        return {}
    lo = min(e["offset"] for e in entries)
    # Local header (30 B) + name + extra precedes each member's data; 4 KB of slack
    # comfortably covers the longest header in this archive.
    hi = max(e["offset"] + e["csize"] for e in entries) + 4096
    blob = fetch_range(url, lo, hi)

    out: dict[str, bytes] = {}
    for e in entries:
        p = e["offset"] - lo
        if blob[p:p + 4] != b"PK\x03\x04":
            continue
        n_len = struct.unpack("<H", blob[p + 26:p + 28])[0]
        e_len = struct.unpack("<H", blob[p + 28:p + 30])[0]
        start = p + 30 + n_len + e_len
        raw = blob[start:start + e["csize"]]
        out[e["name"]] = raw if e["method"] == 0 else zlib.decompress(raw, -15)
    return out


def extract_member(url: str, e: dict) -> bytes:
    """Range-fetch one member and decompress it."""
    head = fetch_range(url, e["offset"], e["offset"] + 29)
    n_len = struct.unpack("<H", head[26:28])[0]
    e_len = struct.unpack("<H", head[28:30])[0]
    data_start = e["offset"] + 30 + n_len + e_len
    raw = fetch_range(url, data_start, data_start + e["csize"] - 1)
    if e["method"] == 0:
        return raw
    return zlib.decompress(raw, -15)


# SVD member names look like "1-a_n.wav" / "1-phrase.wav": <speaker>-<task>.<ext>
SPEAKER_RE = re.compile(r"(?:^|/)(\d+)[-_]")


def speaker_of(name: str) -> str | None:
    m = SPEAKER_RE.search(name)
    return m.group(1) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "pilot"])
    ap.add_argument("archive")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--speakers", type=int, default=20)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    url = _url(args.archive)
    size = total_size(url)
    entries = central_directory(url, size)

    speakers: dict[str, list[dict]] = {}
    for e in entries:
        if e["name"].endswith("/"):
            continue
        sp = speaker_of(Path(e["name"]).name)
        speakers.setdefault(sp or "UNPARSED", []).append(e)

    summary = {
        "archive": args.archive,
        "archive_bytes": size,
        "n_members": len([e for e in entries if not e["name"].endswith("/")]),
        "n_speakers_parsed": len([k for k in speakers if k != "UNPARSED"]),
        "n_unparsed_members": len(speakers.get("UNPARSED", [])),
        "extensions": {},
    }
    for e in entries:
        ext = Path(e["name"]).suffix.lower()
        summary["extensions"][ext] = summary["extensions"].get(ext, 0) + 1

    if args.cmd == "list":
        print(json.dumps(summary, indent=2))
        print("--- sample members ---")
        for e in entries[:args.limit]:
            print(f"  {e['name']}  usize={e['usize']}")
        return

    outdir = Path(args.outdir or ".")
    outdir.mkdir(parents=True, exist_ok=True)
    # Pick speakers adjacent in archive order so their byte ranges form one span.
    ordered: list[str] = []
    for e in entries:
        sp = speaker_of(Path(e["name"]).name)
        if sp and sp not in ordered:
            ordered.append(sp)
    picked = ordered[:args.speakers]

    wanted = [e for sp in picked for e in speakers[sp]]
    print(f"fetching {len(wanted)} members for {len(picked)} speakers in one range...",
          flush=True)
    blobs = extract_many(url, wanted)

    manifest = []
    for sp in picked:
        for e in speakers[sp]:
            data = blobs.get(e["name"])
            if data is None:
                print(f"  MISS {e['name']}", flush=True)
                continue
            dest = outdir / Path(e["name"]).name
            dest.write_bytes(data)
            manifest.append({"speaker": sp, "member": e["name"],
                             "bytes": len(data), "file": dest.name})
    (outdir / "_pilot_manifest.json").write_text(
        json.dumps({"summary": summary, "speakers": picked, "files": manifest}, indent=2),
        encoding="utf-8")
    print(json.dumps({"n_speakers": len(picked), "n_files": len(manifest),
                      "total_bytes": sum(m["bytes"] for m in manifest)}, indent=2))


if __name__ == "__main__":
    sys.exit(main())
