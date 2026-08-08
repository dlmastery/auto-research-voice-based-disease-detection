"""build_common.py -- shared spine for the three dashboard generators.

Everything the master page, the hypothesis tier and the per-run tier need to agree
on lives here exactly once: the run registry, the tier rule, the composite
fingerprint, the markdown-leak gate, and the anchor assertions.

Three rules this module exists to enforce, each paid for by a real defect:

1. **Stamp your inputs.** `load_runs()` declares every artifact it expects by name.
   A renamed or deleted artifact is FATAL, and an artifact on disk that no generator
   knows about is ALSO fatal -- that is what stops a completed run from silently
   never reaching the dashboard (the defect that had 4 executed hypotheses rendering
   as UNTESTED).
2. **Assert your anchors.** `anchor_find` / `anchor_replace` refuse to return
   quietly when the thing they were looking for is absent. A lookup that matches
   nothing must fail, not pass.
3. **Gate at build time.** `leak_gate` runs over the emitted HTML, not over the
   author's intentions. A check that must be remembered will eventually be skipped.

CPU only. No network, no model load.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "autoresearch_results"
DOCS = ROOT / "docs"

# The real remote. The previous value (`github.com/eranti/...`) 404s, which made the
# single "go to the source" link on a transparency dashboard untraceable.
REPO_OWNER = "dlmastery"
REPO_NAME = "auto-research-voice-based-disease-detection"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
BLOB = f"{REPO_URL}/blob/master"

NOT_MEASURED = '<span class="nm">not yet measured</span>'


# --------------------------------------------------------------------------- #
# fail-loud primitives
# --------------------------------------------------------------------------- #

def fatal(msg: str) -> "NoReturn":  # noqa: F821
    sys.exit(f"FATAL: {msg}")


def require(path: Path, what: str) -> Path:
    if not path.exists():
        fatal(f"required source missing: {what} -> {path}\n"
              "The dashboard renders only measured numbers; refusing to emit a\n"
              "blank or invented cell (CLAUDE.md R1/R2).")
    return path


def anchor_find(text: str, pattern: str, where: str, flags: int = 0) -> re.Match:
    """Search, or die. A regex that matches nothing is a silent-failure generator:
    the build succeeds, the page is well-formed, and the content is wrong."""
    m = re.search(pattern, text, flags)
    if m is None:
        fatal(f"anchor not found in {where}: {pattern!r}\n"
              "The source format changed under the generator. Refusing to emit a page\n"
              "built on a lookup that matched nothing.")
    return m


def anchor_replace(text: str, old: str, new: str, where: str) -> str:
    """str.replace that cannot no-op. The house rule: a replace that matches nothing
    must raise, not pass silently (it once shipped a page with literal markdown)."""
    if old not in text:
        fatal(f"anchor_replace found no occurrence of {old!r} in {where}")
    return text.replace(old, new)


def leak_gate(paths: list[Path]) -> int:
    """Refuse to ship a page with literal markdown syntax showing.

    Patterns: a bold span, a table rule, an ATX heading at line start. These are the
    three that have actually leaked in this repo's history (a chip once rendered a
    whole tier paragraph, asterisks and all, because chips bypass the md() helper).
    """
    bad = []
    for p in paths:
        text = p.read_text(encoding="utf-8")
        for pat in (r"\*\*[^*\n]+\*\*", r"\|\s*-{3,}", r"(?m)^#{2,}\s"):
            hit = re.search(pat, text)
            if hit:
                bad.append(f"{p.name}: {hit.group(0)[:60]!r}")
    if bad:
        fatal("literal markdown leaked into generated HTML:\n  " + "\n  ".join(bad))
    return len(paths)


# --------------------------------------------------------------------------- #
# text helpers
# --------------------------------------------------------------------------- #

_ARXIV = re.compile(r"arXiv:(\d{4}\.\d{4,5})")


def esc(s: object) -> str:
    return html.escape(str(s))


def md_inline(s: str) -> str:
    """Inline markdown -> HTML. Nothing that reaches a page may keep its syntax."""
    s = html.escape(str(s).strip())
    s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)\*([^*\s][^*]*?)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = _ARXIV.sub(r'<a href="https://arxiv.org/abs/\1">arXiv:\1</a>', s)
    s = re.sub(r"(?<![\">])(https?://[^\s<)]+)", r'<a href="\1">\1</a>', s)
    return s


def strip_md(s: str) -> str:
    return re.sub(r"[*`]", "", str(s)).strip()


def fmt(x: object, d: int = 4) -> str:
    """Numbers to fixed decimals; an em-dash for missing. Never blank, never NaN."""
    try:
        v = float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "&mdash;"
    if v != v:  # NaN
        return "&mdash;"
    return f"{v:.{d}f}"


def git_sha() -> str:
    """Commit SHA from .git without invoking git."""
    head = ROOT / ".git" / "HEAD"
    try:
        h = head.read_text(encoding="utf-8").strip()
        if not h.startswith("ref: "):
            return h
        ref = ROOT / ".git" / h[5:]
        if ref.exists():
            return ref.read_text(encoding="utf-8").strip()
        packed = ROOT / ".git" / "packed-refs"
        if packed.exists():
            for ln in packed.read_text(encoding="utf-8").splitlines():
                if ln.endswith(" " + h[5:]):
                    return ln.split()[0]
        return "COMMIT_SHA_PLACEHOLDER"
    except OSError:
        return "COMMIT_SHA_PLACEHOLDER"


def built_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def mtime_utc(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# --------------------------------------------------------------------------- #
# the composite fingerprint
# --------------------------------------------------------------------------- #

def composite_spec() -> dict:
    """Parse COMPOSITE.md's canonical spec string, recompute its SHA-256, and check
    it against the pinned value in the same document.

    The fingerprint is over the SPECIFICATION, not the code, so a refactor cannot move
    it and a lambda edit cannot hide in one. This function also reports whether the
    spec is IMPLEMENTED anywhere -- `audits/SCI_CRITIC.md` found that it is not, and a
    fingerprint rendered without that caveat would imply a live gate that does not exist.
    """
    md = require(ROOT / "COMPOSITE.md", "COMPOSITE.md").read_text(encoding="utf-8")
    m = anchor_find(md, r"```\s*\n(\{\"confound_battery\".+?\})\s*\n```", "COMPOSITE.md", re.S)
    canon = m.group(1).strip()
    digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    pinned = anchor_find(md, r"→\s*`([0-9a-f]{64})`", "COMPOSITE.md").group(1)
    if digest != pinned:
        fatal("COMPOSITE.md canonical string does not hash to its own pinned "
              f"fingerprint:\n  recomputed {digest}\n  pinned     {pinned}\n"
              "Either the spec or the pin was edited without the other.")
    spec = json.loads(canon)
    impl = ROOT / "src" / "voiceaudit" / "composite.py"
    return {
        "fingerprint": digest,
        "formula": spec["formula"],
        "version": spec["version"],
        "name": spec["name"],
        "lambdas": spec["lambdas"],
        "battery": spec["confound_battery"],
        "null_policy": spec["null_policy"],
        "implemented": impl.exists(),
        "impl_path": "src/voiceaudit/composite.py",
    }


# --------------------------------------------------------------------------- #
# the run registry -- every artifact that is a RUN, declared by name
# --------------------------------------------------------------------------- #

# artifact filename -> (run id, hypothesis id or None, finding ids, one-line title)
RUN_REGISTRY: dict[str, tuple[str, str | None, str, str]] = {
    "F1_demographic_baseline.json": (
        "run-f1-demographics", None, "F1",
        "SVD demographic baseline -- age and sex only, no audio"),
    "bench_svd_egemaps.json": (
        "run-bench-egemaps", None, "",
        "eGeMAPS on the decoded SVD pilot slice vs its own confound battery"),
    "bench_svd_wavlm_mean_std.json": (
        "run-bench-wavlm", None, "F2, F3",
        "WavLM-base+ on full-corpus SVD vs its own confound battery"),
    "V1_ssl_vs_handcrafted.json": (
        "run-v1-ssl-vs-handcrafted", "V1", "F7",
        "SSL vs handcrafted features under age-matched speaker-disjoint splits"),
    "V2_speaker_subspace.json": (
        "run-v2-speaker-subspace", "V2", "F4",
        "Speaker-identity subspace ablation against variance-matched controls"),
    "V2_speaker_subspace_SHUFFLE.json": (
        "run-v2-shuffle-control", "V2", "F4",
        "Label-shuffle negative control for the V2 subspace ablation"),
    "V6_preprocessing_leakage.json": (
        "run-v6-preprocessing-leakage", "V6", "F5",
        "Scaler-fit-before-split leakage, measured on embeddings"),
    "V7_silence_shortcut.json": (
        "run-v7-silence-shortcut", "V7", "F6",
        "Silence-only features across three corpora -- the Clever-Hans probe"),
}

# Artifacts that exist on disk but are deliberately NOT runs. Declaring them is what
# lets the unknown-artifact gate below stay strict.
NON_RUN_ARTIFACTS = {
    "V2_speaker_subspace_SHUFFLE.partial.json":
        "resumable checkpoint for the shuffle control, superseded by the final file",
}


def _tier(repeats: int, *, control: bool = False) -> tuple[str, str]:
    """(tier, why). R6: n <= 3 is screening and may never be called a result;
    n >= 8 can reach a Holm-corrected threshold for the families registered here."""
    if control:
        return "CONTROL", f"negative control, n={repeats}"
    if repeats >= 8:
        return "EVALUATION", f"n={repeats} repeats"
    if repeats >= 1:
        return "SCREENING", f"n={repeats} repeats -- cannot reach the Holm threshold"
    return "SCREENING", "metadata-only, no repeated partitions"


def _row(art: Path, d: dict) -> dict:
    """Normalise one artifact into a ledger row. Every field is read, never assumed."""
    rid, hyp, finding, title = RUN_REGISTRY[art.name]
    base = {
        "id": rid, "artifact": art.name, "hypothesis": hyp, "finding": finding,
        "title": title, "path": art, "mtime": mtime_utc(art),
        "elapsed_s": d.get("elapsed_s"), "raw": d,
    }

    if art.name.startswith("bench_"):
        cfg, ds, mvc = d["config"], d["dataset"], d["margins_vs_confound"]
        best = mvc["best_audio_head"]
        n = int(cfg["n_repeats"])
        tier, why = _tier(n)
        bar = mvc["confound_bar_name"].replace("confound::", "")
        delta = mvc["per_head"][best]["speaker_level_delta_auc"]
        base.update({
            "kind": "benchmark", "corpus": cfg["corpus"], "backbone": cfg["backbone"],
            "n_repeats": n, "n_folds": int(cfg["n_folds"]),
            "n_recordings": ds["n_recordings"], "n_speakers": ds["n_speakers"],
            "tier": tier, "tier_why": why,
            "headline_label": f"speaker-level ROC-AUC, {best}",
            "headline": d["speaker_level"][best]["roc_auc"],
            "headline_ci": d["speaker_level"][best].get("roc_auc_ci95"),
            "bar_label": f"confound bar ({bar})",
            "bar": mvc["confound_bar_auc_speaker"],
            "delta": delta["delta"], "delta_ci": [delta["lo"], delta["hi"]],
            "verdict": "NOT CLEARED" if any("NOT" in v for v in d["verdicts"].values())
                       else "CLEARED",
            "power": d["power_check_R6"],
            "provenance": {
                "command": d["command"], "git_sha": d["git_sha"],
                "config_hash": d["config_hash"], "generated_utc": d["generated_utc"],
                "embedding_content_hash": d.get("embedding_content_hash"),
            },
        })
        return base

    if art.name == "F1_demographic_baseline.json":
        tier, why = _tier(0)
        base.update({
            "kind": "baseline", "corpus": d["dataset"], "backbone": "metadata only",
            "n_repeats": 0, "n_folds": 5,
            "n_recordings": d["n_sessions"], "n_speakers": d["n_speakers"],
            "tier": tier, "tier_why": why,
            "headline_label": "ROC-AUC, age alone", "headline": d["auc_age_only"],
            "headline_ci": None,
            "bar_label": "ROC-AUC, sex alone (negative control)", "bar": d["auc_sex_only"],
            "delta": None, "delta_ci": None,
            "verdict": "CONFOUND ESTABLISHED", "power": None,
            "provenance": {"artifact_md5": d["artifact_md5"], "source": d["artifact"]},
        })
        return base

    # the V-runs
    n = int(d.get("repeats", 0))
    control = bool(d.get("shuffle_control"))
    tier, why = _tier(n, control=control)
    base.update({
        "kind": "hypothesis", "corpus": d.get("corpus", "svd"),
        "backbone": d.get("backbone", "see artifact"),
        "n_repeats": n, "n_folds": int(d.get("folds", 0)),
        "n_recordings": d.get("n_recordings"), "n_speakers": d.get("n_speakers"),
        "tier": tier, "tier_why": why, "power": {
            "n_paired": n, "family_size": d.get("family_m_preregistered"),
            "min_attainable_p": 2 / 2 ** n if n else None,
            "holm_tightest_threshold": (0.05 / d["family_m_preregistered"]
                                        if d.get("family_m_preregistered") else None),
        },
        "provenance": {"objective": d.get("objective"), "audited": d.get("audited")},
    })

    if art.name.startswith("V1_"):
        base.update({
            "headline_label": "mean ROC-AUC, eGeMAPS (age-matched)",
            "headline": d["mean_auc_egemaps"], "headline_ci": None,
            "bar_label": "mean ROC-AUC, WavLM (same folds)",
            "bar": d["mean_auc_wavlm"],
            "delta": d["wavlm_minus_egemaps"], "delta_ci": d["wavlm_minus_egemaps_ci95"],
            "verdict": "SSL DOES NOT BEAT HANDCRAFTED",
            "n_recordings": None,
            "n_speakers": int(round(d["mean_n_speakers"])),
        })
    elif art.name.startswith("V2_"):
        k8 = next((r for r in d["rows"] if r["k"] == 8), d["rows"][-1])
        base.update({
            "headline_label": f"full-embedding disease AUC ({'shuffled labels' if control else 'real labels'})",
            "headline": d["auc_full_mean"], "headline_ci": None,
            "bar_label": f"AUC after removing the speaker subspace (k={k8['k']})",
            "bar": k8["auc_speaker_removed"],
            "delta": k8.get("D_vs_pca_topk"), "delta_ci": k8.get("D_vs_pca_topk_ci95"),
            "verdict": ("CONTROL PASSES -- effect vanishes under shuffling" if control
                        else "CLAIM SUPPORTED -- falsifier did NOT fire"),
        })
    elif art.name.startswith("V6_"):
        base.update({
            "headline_label": "max |delta AUC| across the cells that ran",
            "headline": max(abs(c["delta_mean"]) for c in d["cells"] if c["status"] == "RUN"),
            "headline_ci": None,
            "bar_label": "cells run / cells pre-registered",
            "bar": None,
            "bar_text": f'{d["cells_run"]} / {len(d["cells"])}',
            "delta": None, "delta_ci": None,
            "verdict": "PARTIAL -- near-null reproduced; falsifier NOT evaluable",
            "n_recordings": max((c.get("n_recordings") or 0) for c in d["cells"]),
            "n_speakers": max((c.get("n_speakers") or 0) for c in d["cells"]),
        })
    elif art.name.startswith("V7_"):
        runs = [c for c in d["cells"] if c["status"] == "RUN"]
        worst = max(runs, key=lambda c: c["auc"])
        base.update({
            "headline_label": f'highest silence-only AUC of {len(runs)} cells ({worst["corpus"]})',
            "headline": worst["auc"], "headline_ci": worst.get("auc_ci95"),
            "bar_label": "cells run / cells pre-registered",
            "bar": None, "bar_text": f'{d["cells_run"]} / {len(d["cells"])}',
            "delta": None, "delta_ci": None,
            "verdict": "PARTIAL -- shortcut does NOT generalise",
            "n_recordings": max((c.get("n_recordings") or 0) for c in d["cells"]),
            "n_speakers": max((c.get("n_speakers") or 0) for c in d["cells"]),
        })
    else:
        fatal(f"no ledger extractor for {art.name} -- add one to build_common._row")
    return base


def load_runs() -> list[dict]:
    """Every artifact-backed run, newest first.

    Two gates, both fatal:
      * a DECLARED artifact that is missing (a run vanished, or was renamed);
      * an UNDECLARED `*.json` in autoresearch_results/ (a run completed and no
        generator knows about it). The second is the one that matters: it is exactly
        how V1/V6/V7 sat on disk for days while every surface said UNTESTED.
    """
    require(RESULTS, "autoresearch_results/")
    on_disk = {p.name for p in RESULTS.glob("*.json")}
    declared = set(RUN_REGISTRY) | set(NON_RUN_ARTIFACTS)

    missing = sorted(set(RUN_REGISTRY) - on_disk)
    if missing:
        fatal("declared run artifacts are missing from autoresearch_results/:\n  "
              + "\n  ".join(missing))

    unknown = sorted(on_disk - declared)
    if unknown:
        fatal("undeclared artifact(s) in autoresearch_results/:\n  "
              + "\n  ".join(unknown)
              + "\nA completed run that no generator knows about renders as UNTESTED\n"
                "everywhere. Add it to build_common.RUN_REGISTRY (with an extractor in\n"
                "_row) or to NON_RUN_ARTIFACTS with a reason.")

    rows = [_row(RESULTS / name, json.loads((RESULTS / name).read_text(encoding="utf-8")))
            for name in RUN_REGISTRY]

    # SCOPE, not just tier. A run can satisfy R6 on repeats and still be measured on a
    # slice a later run superseded -- the eGeMAPS pilot cleared n=10 on 49 speakers while
    # the WavLM run covered 1,679. Repeats alone would rank them alike, so scope is
    # derived here by comparing each run against the largest slice measured on the same
    # corpus. Nothing is hand-entered: the comparison is between artifacts.
    widest: dict[str, int] = {}
    for r in rows:
        if r["n_speakers"]:
            widest[r["corpus"]] = max(widest.get(r["corpus"], 0), int(r["n_speakers"]))
    for r in rows:
        top = widest.get(r["corpus"], 0)
        mine = int(r["n_speakers"] or 0)
        if top and mine and mine < 0.5 * top:
            r["scope"] = (f"pilot slice -- {mine:,} of the {top:,} speakers measured "
                          f"elsewhere on {r['corpus']}")
        else:
            r["scope"] = ""

    rows.sort(key=lambda r: r["path"].stat().st_mtime, reverse=True)
    return rows


def runs_by_hypothesis(runs: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in runs:
        if r["hypothesis"]:
            out.setdefault(r["hypothesis"], []).append(r)
    return out


# --------------------------------------------------------------------------- #
# IDEA_TABLE.md -- the authoritative status is the Summary table
# --------------------------------------------------------------------------- #

def idea_summary() -> dict[str, dict]:
    """Parse the `## Summary` table of IDEA_TABLE.md.

    Deliberately NOT the per-hypothesis `| **Status** |` cell: that cell is updated
    by hand per block and is already internally inconsistent (V1's block still says
    UNTESTED while the Summary says CLAIM SUPPORTED). One source of truth, and it is
    the one the author maintains as a set.
    """
    text = require(ROOT / "IDEA_TABLE.md", "IDEA_TABLE.md").read_text(encoding="utf-8")
    anchor_find(text, r"(?m)^## Summary\s*$", "IDEA_TABLE.md")
    sect = text.split("## Summary", 1)[1]
    out: dict[str, dict] = {}
    for ln in sect.splitlines():
        if not ln.startswith("|") or "**V" not in ln:
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) < 10:
            continue
        out[strip_md(c[0])] = {
            "axis": strip_md(c[1]), "tier": strip_md(c[2]), "m": strip_md(c[3]),
            "n": strip_md(c[4]), "min_p": strip_md(c[5]), "holm": strip_md(c[6]),
            "satisfiable": strip_md(c[7]), "datasets": strip_md(c[8]),
            "status_md": c[9], "status": strip_md(c[9]),
        }
    if len(out) < 7:
        fatal(f"IDEA_TABLE.md Summary table parsed {len(out)} hypotheses, expected >= 7. "
              "The table format changed.")
    return out


def status_class(status: str) -> str:
    """Registry status -> chip class. UNTESTED is debt and is styled as debt."""
    s = status.upper()
    if s.startswith("UNTESTED") or s == "":
        return "pend"
    if "PARTIAL" in s:
        return "screen"
    if "SUPPORTED" in s or "FALSIFIED" in s or "CLEARED" in s:
        return "eval"
    return "pend"


def status_short(status: str) -> str:
    """The chip label: a chip holds a label, never a paragraph."""
    s = status.upper()
    if s.startswith("UNTESTED"):
        return "UNTESTED"
    if "PARTIAL" in s:
        return "PARTIAL"
    if "FALSIFIED" in s:
        return "FALSIFIED"
    if "SUPPORTED" in s:
        return "CLAIM SUPPORTED"
    return status[:28]


# --------------------------------------------------------------------------- #
# FINDINGS.md
# --------------------------------------------------------------------------- #

def findings() -> list[dict]:
    """One row per `## Fn -- title`, with the tier line that follows it."""
    text = require(ROOT / "FINDINGS.md", "FINDINGS.md").read_text(encoding="utf-8")
    heads = list(re.finditer(r"(?m)^## (F\d+[a-z]?)\s*[—-]\s*(.+)$", text))
    if not heads:
        fatal("parsed 0 findings out of FINDINGS.md")
    out = []
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        tier_m = re.search(r"(?m)^\*\*(?:Tier|Status):\*\*?\s*(.+)$", body) or \
                 re.search(r"(?m)^\*\*Tier:\s*([^*]+)\*\*(.*)$", body)
        raw = (" ".join(tier_m.groups()) if tier_m else "")
        raw = " ".join(strip_md(raw).split())
        up = raw.upper()
        tier = ("EVALUATION" if "EVALUATION" in up else
                "PARTIAL" if "PARTIAL" in up else
                "CERTIFIED" if "CERTIFIED" in up else
                "SCREENING" if "SCREENING" in up else "UNSTATED")
        if "CERTIFIED" in body.upper() and tier == "UNSTATED":
            tier = "CERTIFIED"
        art = re.search(r"Artifact:\*?\*?\s*`([^`]+)`", body)
        out.append({
            "id": h.group(1), "title": h.group(2).strip(),
            "tier": tier, "tier_raw": raw or "stated in prose; see FINDINGS.md",
            "artifact": art.group(1) if art else None,
        })
    return out
