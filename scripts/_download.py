"""Shared polite/resumable HTTP download helpers for the dataset fetchers.

Design notes (hard-won on this host, 2026-07-25):

* **Norton Antivirus MITM-intercepts all TLS on this machine** (issuer
  ``CN=Norton Web/Mail Shield Root``). ``certifi`` therefore fails every HTTPS
  handshake with ``CERTIFICATE_VERIFY_FAILED``. ``truststore`` reads the Windows
  system trust store, which *does* carry the Norton root, so we inject it. This
  is a no-op on hosts without interception, so it is safe everywhere.
* **Downloads must be resumable.** Two ``git clone`` attempts of Coswara (13 GB)
  were killed mid-transfer on this host. Every fetch here streams to a ``.part``
  file and resumes with an HTTP ``Range`` request.
* **Be polite.** One connection at a time, a sleep between files, retries with
  exponential backoff. These are free academic hosts; do not hammer them.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from pathlib import Path

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:  # pragma: no cover - truststore is expected but optional
    print("[warn] truststore not installed; HTTPS may fail behind a TLS-intercepting AV",
          file=sys.stderr)

import requests

USER_AGENT = "auto-research-voice/1.0 (academic dataset acquisition; contact via repo)"
CHUNK = 1 << 20  # 1 MiB


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def download(
    url: str,
    dest: Path,
    *,
    sess: requests.Session | None = None,
    expect_size: int | None = None,
    expect_md5: str | None = None,
    sleep: float = 1.0,
    retries: int = 5,
    timeout: int = 120,
) -> Path:
    """Stream ``url`` to ``dest``, resuming a partial ``.part`` file if present.

    Skips the download entirely when ``dest`` already exists and matches
    ``expect_size`` (so re-running a fetch script is cheap and idempotent).
    """
    sess = sess or session()
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")

    if dest.exists():
        if expect_size is None or dest.stat().st_size == expect_size:
            print(f"  [skip] {dest.name} already complete ({human(dest.stat().st_size)})")
            return dest
        print(f"  [warn] {dest.name} exists with wrong size "
              f"({dest.stat().st_size} != {expect_size}); re-downloading")
        dest.unlink()

    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            with sess.get(url, headers=headers, stream=True, timeout=timeout) as r:
                if have and r.status_code == 200:
                    # Server ignored the Range header - restart from scratch.
                    have = 0
                    part.unlink(missing_ok=True)
                elif have and r.status_code == 416:
                    # Already have the whole thing.
                    break
                r.raise_for_status()

                total = expect_size
                if total is None:
                    cl = r.headers.get("Content-Length")
                    if cl:
                        total = int(cl) + have

                mode = "ab" if have else "wb"
                last = time.time()
                with open(part, mode) as fh:
                    for chunk in r.iter_content(CHUNK):
                        if not chunk:
                            continue
                        fh.write(chunk)
                        have += len(chunk)
                        if time.time() - last > 5:
                            pct = f" ({100 * have / total:.1f}%)" if total else ""
                            print(f"    {dest.name}: {human(have)}{pct}", flush=True)
                            last = time.time()
            break
        except (requests.RequestException, OSError) as exc:
            if attempt == retries:
                raise
            back = min(60, 2 ** attempt)
            print(f"  [retry {attempt}/{retries}] {dest.name}: {type(exc).__name__}; "
                  f"sleeping {back}s (resuming from {human(have)})", file=sys.stderr)
            time.sleep(back)

    if expect_size is not None and part.stat().st_size != expect_size:
        raise RuntimeError(
            f"{dest.name}: size mismatch, got {part.stat().st_size} expected {expect_size}")

    if expect_md5:
        h = hashlib.md5()
        with open(part, "rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK), b""):
                h.update(chunk)
        if h.hexdigest() != expect_md5:
            raise RuntimeError(f"{dest.name}: md5 mismatch, got {h.hexdigest()} expected {expect_md5}")

    part.replace(dest)
    print(f"  [ok] {dest.name} ({human(dest.stat().st_size)})")
    time.sleep(sleep)  # be polite to the host
    return dest


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def raw_dir(name: str) -> Path:
    """``data/raw/<name>`` - gitignored, never committed."""
    d = repo_root() / "data" / "raw" / name
    d.mkdir(parents=True, exist_ok=True)
    return d
