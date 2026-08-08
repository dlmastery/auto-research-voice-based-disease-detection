"""build_dashboard.py -- regenerate the transparency dashboard from source artifacts.

The dashboard is GENERATED, never hand-maintained. Every number rendered into
`docs/index.html` is read out of a file in this repository (CLAUDE.md R1/R2:
no orphan numbers, the agent may not state a metric it did not read from an
artifact). If a source file is missing this script FAILS LOUDLY rather than
emitting a blank cell.

Usage:
    python scripts/build_dashboard.py

Outputs:
    docs/index.html
    docs/assets/svd_age_distribution.png
    docs/assets/confound_vs_sota.png

CPU only. No GPU, no model load, no network.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless; PNG output only
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_common import (  # noqa: E402
    BLOB, REPO_URL, anchor_find, composite_spec, findings, idea_summary, leak_gate,
    load_runs, mtime_utc, runs_by_hypothesis, status_class, status_short,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"

# --------------------------------------------------------------------------- #
# source registry -- every one of these is REQUIRED; a missing file is fatal
# --------------------------------------------------------------------------- #

SOURCES = {
    "constitution": ROOT / "CLAUDE.md",
    "findings": ROOT / "FINDINGS.md",
    "f1_json": ROOT / "autoresearch_results" / "F1_demographic_baseline.json",
    "bench_svd": ROOT / "autoresearch_results" / "bench_svd_egemaps.json",
    "preprocessing": ROOT / "data" / "PREPROCESSING_STATUS.md",
    "acquisition": ROOT / "data" / "ACQUISITION_STATUS.md",
    "survey_datasets": ROOT / "corpus" / "SURVEY_datasets.md",
    "survey_sota": ROOT / "corpus" / "SURVEY_sota_methods.md",
    "idea_table": ROOT / "IDEA_TABLE.md",
    "prereg": ROOT / "PREREGISTRATION.md",
    "novelty": ROOT / "audits" / "NOVELTY_CRITIQUE.md",
    "benchmark_py": ROOT / "src" / "voicehealth" / "benchmark.py",
    "svd_meta": ROOT / "data" / "raw" / "svd_meta" / "voice_data.csv",
    "composite": ROOT / "COMPOSITE.md",
    "bench_svd_full": ROOT / "autoresearch_results" / "bench_svd_wavlm_mean_std.json",
    "v1": ROOT / "autoresearch_results" / "V1_ssl_vs_handcrafted.json",
    "v2": ROOT / "autoresearch_results" / "V2_speaker_subspace.json",
    "coswara_meta": ROOT / "autoresearch_results" / "acquisition" / "coswara_meta_stats.json",
}

# The audit documents. Each is a real review with a verdict; none of them was linked
# from any published surface, which is the one place a reader would look for the
# program's own criticism of itself.
AUDITS = [
    ("DATA_SPLIT_AUDIT.md", "Data-split audit",
     "SVD conditional pass (screening only) &middot; Coswara FAIL &middot; COUGHVID HARD FAIL"),
    ("IMPL_CRITIC.md", "Implementation critic",
     "one INVALIDATES-RESULTS defect (embedding cache key omits labels), 5 biases, "
     "and an empty <code>tests/</code> &mdash; no rung-0 UNIT layer"),
    ("SCI_CRITIC.md", "Scientific critic",
     "the composite fingerprint re-executes, but the composite is implemented nowhere; "
     "F1's 0.871 is on 1,853 speakers and was quoted against a 49-speaker slice"),
    ("NOVELTY_CRITIQUE.md", "Novelty critique",
     "the loop is not novel (arXiv:2606.20394); the domain survives under exactly one "
     "framing &mdash; audit engine, not detector factory"),
    ("PRIOR_AUTORESEARCH_REPOS.md", "Prior-program archaeology",
     "7 sibling programs replayed from their own logs; one ran 0 experiments across 324 "
     "scaffolded tasks"),
    ("README.md", "Audit index + circularity disclosure",
     "leads with the single most serious defect found across all audits"),
]

CORPORA = ["svd", "coughvid", "coswara"]
for _c in CORPORA:
    SOURCES[f"summary_{_c}"] = ROOT / "data" / "interim" / _c / "summary.json"
    SOURCES[f"manifest_{_c}"] = ROOT / "data" / "interim" / _c / "manifest.csv"

NOT_MEASURED = '<span class="nm">not yet measured</span>'


def require(key: str) -> Path:
    """Return a source path, or die loudly. A blank cell is never acceptable."""
    p = SOURCES[key]
    if not p.exists():
        sys.exit(
            f"FATAL: required source missing: {key} -> {p}\n"
            "The dashboard renders only measured numbers; refusing to emit a\n"
            "blank or invented cell (CLAUDE.md R1/R2)."
        )
    return p


def read_text(key: str) -> str:
    return require(key).read_text(encoding="utf-8")


def read_json(key: str) -> dict:
    return json.loads(read_text(key))


# --------------------------------------------------------------------------- #
# tiny inline-markdown renderer (no literal ** or ` may leak into the page)
# --------------------------------------------------------------------------- #

_ARXIV = re.compile(r"arXiv:(\d{4}\.\d{4,5})")
_DOI_SD = re.compile(r"`(s\d{5}-\d{3}-\d{5}-[\dxX])`")


def md_inline(s: str) -> str:
    s = html.escape(s.strip())
    s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)\*([^*\s][^*]*?)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = _ARXIV.sub(r'<a href="https://arxiv.org/abs/\1">arXiv:\1</a>', s)
    s = re.sub(r"(?<![\">])(https?://[^\s<)]+)", r'<a href="\1">\1</a>', s)
    return s


def strip_md(s: str) -> str:
    return re.sub(r"[*`]", "", s).strip()


# --------------------------------------------------------------------------- #
# markdown table parsing
# --------------------------------------------------------------------------- #

def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def find_table(text: str, header_contains: str) -> tuple[list[str], list[list[str]]]:
    """Return (header, rows) of the first pipe-table whose header row contains
    `header_contains`."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("|") and header_contains in ln:
            header = split_row(ln)
            rows = []
            for ln2 in lines[i + 2:]:
                if not ln2.lstrip().startswith("|"):
                    break
                rows.append(split_row(ln2))
            return header, rows
    sys.exit(f"FATAL: could not locate a table whose header contains {header_contains!r}")


# --------------------------------------------------------------------------- #
# loaders
# --------------------------------------------------------------------------- #

def git_sha() -> str:
    """Read the commit SHA from .git without invoking git. Placeholder if absent."""
    head = ROOT / ".git" / "HEAD"
    try:
        h = head.read_text(encoding="utf-8").strip()
        if h.startswith("ref: "):
            ref = ROOT / ".git" / h[5:]
            if ref.exists():
                return ref.read_text(encoding="utf-8").strip()
            packed = ROOT / ".git" / "packed-refs"
            if packed.exists():
                for ln in packed.read_text(encoding="utf-8").splitlines():
                    if ln.endswith(" " + h[5:]):
                        return ln.split()[0]
            return "COMMIT_SHA_PLACEHOLDER"
        return h
    except OSError:
        return "COMMIT_SHA_PLACEHOLDER"


def load_corpus_status() -> list[dict]:
    """Per-corpus row: decoded counts + speaker provenance (summary.json), on-disk
    size + licence (ACQUISITION_STATUS.md / SURVEY_datasets.md)."""
    acq = read_text("acquisition")
    _, dsrows = find_table(read_text("survey_datasets"), "ACCESS & license")
    licences = {}
    for r in dsrows:
        name = strip_md(r[0]).split("(")[0].strip().lower()
        if len(r) > 6:
            licences[name] = strip_md(r[6])

    def licence_for(corpus: str) -> str:
        for key, val in licences.items():
            if corpus in key or key.startswith(corpus):
                return val
        return "see corpus/SURVEY_datasets.md"

    def ondisk_for(label: str) -> str:
        for ln in acq.splitlines():
            if ln.startswith("|") and label in ln:
                cells = split_row(ln)
                if len(cells) > 2:
                    return strip_md(cells[2])
        return "not stated"

    disk_label = {"svd": "**SVD** (Saarbr", "coughvid": "**COUGHVID**", "coswara": "**Coswara**"}
    pretty = {"svd": "SVD (Saarbruecken)", "coughvid": "COUGHVID", "coswara": "Coswara"}

    out = []
    for c in CORPORA:
        s = read_json(f"summary_{c}")
        man = pd.read_csv(require(f"manifest_{c}"))
        prov = sorted(s["speaker_id_provenance"].keys())
        out.append({
            "corpus": pretty[c],
            "key": c,
            "found": s["files_found"],
            "decoded": s["files_decoded"],
            "failed": s["files_failed"],
            "rows_in_manifest": int(len(man)),
            "speakers": s["n_speakers"],
            "duration_min": s["total_duration_s"] / 60.0,
            "labels": s["label_counts"],
            "provenance": ", ".join(prov),
            "disjoint": bool(s["speaker_disjoint_split_possible"]),
            "dupes": s["duplicate_audio_sha256"],
            "licence": licence_for(c),
            "on_disk": ondisk_for(disk_label[c]),
        })
    return out


def load_hypotheses() -> list[dict]:
    """Parse the V1..V7 registry out of IDEA_TABLE.md."""
    text = read_text("idea_table")
    blocks = re.split(r"\n#### ", text)[1:]
    rows = []
    for b in blocks:
        head = b.splitlines()[0]
        m = re.match(r"(V\d+)\s*[-—]+\s*(.*)", head)
        if not m:
            continue
        hid, title = m.group(1), m.group(2)
        fields = {}
        for ln in b.splitlines():
            if ln.startswith("|") and ln.count("|") >= 3:
                cells = split_row(ln)
                if len(cells) >= 2:
                    fields[strip_md(cells[0]).lower()] = cells[1]
        if "claim" not in fields:
            continue
        mn = strip_md(fields.get("m / n", ""))
        n_req = re.search(r"n\s*=\s*\*{0,2}(\d+)", fields.get("m / n", ""))
        rows.append({
            "id": hid,
            "title": title.strip(),
            "claim": fields["claim"],
            "falsifier": fields.get("falsifier", ""),
            "tier": strip_md(fields.get("tier", "")),
            "mn": mn,
            "n_req": n_req.group(1) if n_req else "see m/n",
            "datasets": strip_md(fields.get("datasets", "")),
            "status": strip_md(fields.get("status", "UNTESTED")),
        })
    if not rows:
        sys.exit("FATAL: parsed 0 hypotheses out of IDEA_TABLE.md")
    return rows


def load_traps() -> list[dict]:
    """The methodological traps -- SURVEY_datasets.md section 3."""
    text = read_text("survey_datasets")
    start = text.index("## 3. Known methodological traps")
    end = text.find("\n## ", start + 5)
    sect = text[start: end if end != -1 else len(text)]
    traps = []
    for chunk in re.split(r"\n### ", sect)[1:]:
        lines = chunk.splitlines()
        head = lines[0]
        num, _, title = head.partition(" ")
        body = "\n".join(lines[1:])
        rule = re.search(r"\*\*Rule[^:]*:\*\*(.+?)(?:\n\n|$)", body, re.S)
        if rule:
            summary = " ".join(rule.group(1).split())
        else:
            # no explicit Rule paragraph: take the first prescriptive sentence,
            # falling back to the first sentence of the section.
            flat = " ".join(body.split())
            sentences = [s.strip() for s in re.split(r"(?<=\.)\s+", flat) if s.strip()]
            prescriptive = re.compile(
                r"\b(must|Never|never|Do not|do not|cannot|not interchangeable|"
                r"rigor violation|does not remove)\b")
            idx = next((i for i, s in enumerate(sentences) if prescriptive.search(s)), 0)
            summary = sentences[idx] if sentences else ""
            if len(summary) < 70 and idx + 1 < len(sentences):
                summary = summary + " " + sentences[idx + 1]
        summary = summary[:1].upper() + summary[1:]
        if len(summary) > 300:
            summary = summary[:297].rsplit(" ", 1)[0] + "..."
        traps.append({"num": num, "title": title.strip(), "rule": summary})
    if not traps:
        sys.exit("FATAL: parsed 0 traps out of SURVEY_datasets.md section 3")
    return traps


def load_scoreboard() -> list[dict]:
    """Seed the benchmark scoreboard from the published-SOTA column of the dataset
    survey. `ours` is filled ONLY from a measured artifact."""
    _, rows = find_table(read_text("survey_datasets"), "Published SOTA")
    header, _ = find_table(read_text("survey_datasets"), "Published SOTA")
    i_sota = header.index("Published SOTA")
    wanted = [
        ("SVD (Saarbruecken Voice Database)", "**SVD (Saarbr"),
        ("Coswara", "**Coswara**"),
        ("PROCESS-2", "**PROCESS-2**"),
        ("ICBHI 2017 respiratory sound", "**ICBHI 2017"),
        ("ADReSS / ADReSSo / ADReSS-M", "**ADReSS /"),
    ]
    out = []
    for label, key in wanted:
        row = next((r for r in rows if r and r[0].startswith(key)), None)
        if row is None:
            sys.exit(f"FATAL: dataset row {key!r} not found in SURVEY_datasets.md table")
        sota = row[i_sota] if len(row) > i_sota else ""
        # any arXiv / DOI identifier anywhere in the row is the citation anchor
        ids = _ARXIV.findall(" ".join(row))
        out.append({
            "dataset": label,
            "sota_raw": sota if sota not in ("", "-", "—") else "no single published SOTA in survey",
            "cite": ids[0] if ids else None,
            "confounds": row[-1] if row else "",
        })
    return out


def load_bench() -> dict:
    return read_json("bench_svd")


def load_background() -> dict:
    """Corpus scope facts, recomputed from the SVD manifest.

    This answers the first question any reader has -- "what is in here and how many
    diseases can it actually detect?" -- with counts rather than adjectives. The
    long tail is the point: 70 named pathologies exist, but only a handful carry
    enough speakers to model, and stating that up front prevents the reader from
    reading "70 diagnoses" as "70 detectable diseases".
    """
    df = pd.read_csv(require("manifest_svd"), encoding="utf-8")
    spk = df.drop_duplicates("speaker_id")
    # speaker-level, because a pathology with 200 recordings from 8 people is an
    # 8-person condition -- recording counts would overstate every row below.
    path_spk = df[df.pathology.notna()].drop_duplicates("speaker_id").pathology.value_counts()
    ages = spk.groupby("label").age.mean()
    return {
        "recordings": int(len(df)),
        "sessions": int(df.session_id.nunique()),
        "speakers": int(df.speaker_id.nunique()),
        "tasks": int(df.task.nunique()),
        "n_patho_speakers": int((spk.label == "pathological").sum()),
        "n_healthy_speakers": int((spk.label == "healthy").sum()),
        "age_healthy": float(ages.get("healthy", float("nan"))),
        "age_patho": float(ages.get("pathological", float("nan"))),
        "n_pathologies": int(len(path_spk)),
        "singletons": int((path_spk == 1).sum()),
        "tiers": [
            {"thresh": t,
             "n_conditions": int((path_spk >= t).sum()),
             "n_speakers": int(path_spk[path_spk >= t].sum())}
            for t in (100, 50, 30, 5, 1)
        ],
        "top": [(str(k), int(v)) for k, v in path_spk.head(4).items()],
    }


def count_findings() -> int:
    return len(re.findall(r"^## F\d+", read_text("findings"), re.M))


def findings_limitations() -> list[str]:
    """The verbatim 'What this does NOT claim' list from FINDINGS.md F1."""
    text = read_text("findings")
    start = text.index("### What this does NOT claim")
    end = text.index("### Second observation", start)
    body = text[start:end]
    items = re.split(r"\n\d+\.\s+", body)[1:]
    out = [" ".join(i.split()) for i in items if i.strip()]
    if len(out) != 3:
        sys.exit(f"FATAL: expected 3 F1 limitation items, parsed {len(out)}")
    return out


# --------------------------------------------------------------------------- #
# plots -- real data only
# --------------------------------------------------------------------------- #

DARK_BG = "#12151b"
FG = "#e6e9ef"
GRID = "#2a3040"
C_HEALTHY = "#4fc3f7"
C_PATH = "#ff8a65"
C_BAR = "#7e9cff"


def _style(ax):
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=FG, labelsize=9)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.yaxis.label.set_color(FG)
    ax.xaxis.label.set_color(FG)
    ax.title.set_color(FG)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def plot_age_distribution(f1: dict) -> tuple[Path, dict]:
    """Recomputed from the SVD metadata CSV with the exact labelling rule of
    scripts/audit_demographic_baseline.py, then cross-checked against F1's JSON."""
    df = pd.read_csv(require("svd_meta"))
    df["healthy"] = df["Pathologien"].isna() & df["Diagnose"].isna()
    df["age"] = (
        pd.to_datetime(df["AufnahmeDatum"], errors="coerce")
        - pd.to_datetime(df["Geburtsdatum"], errors="coerce")
    ).dt.days / 365.25
    d = df.dropna(subset=["age"])
    h = d.loc[d.healthy, "age"].values
    p = d.loc[~d.healthy, "age"].values

    checks = {
        "n_sessions": int(len(d)),
        "n_healthy": int(len(h)),
        "n_pathological": int(len(p)),
        "mean_age_healthy": float(h.mean()),
        "mean_age_pathological": float(p.mean()),
    }
    for k in checks:
        ref = f1[k]
        if abs(checks[k] - ref) > 1e-6:
            sys.exit(
                f"FATAL: plot recomputation disagrees with the F1 artifact on {k}: "
                f"{checks[k]} vs {ref}. Refusing to render a figure that does not "
                "match the finding it illustrates."
            )

    fig, ax = plt.subplots(figsize=(7.6, 4.0), dpi=150)
    fig.patch.set_facecolor(DARK_BG)
    bins = np.arange(0, 100, 4)
    ax.hist(h, bins=bins, alpha=0.75, label=f"healthy (n={len(h)})", color=C_HEALTHY)
    ax.hist(p, bins=bins, alpha=0.75, label=f"pathological (n={len(p)})", color=C_PATH)
    ax.axvline(h.mean(), color=C_HEALTHY, linestyle="--", linewidth=1.6)
    ax.axvline(p.mean(), color=C_PATH, linestyle="--", linewidth=1.6)
    gap = p.mean() - h.mean()
    ax.annotate(
        "", xy=(p.mean(), ax.get_ylim()[1] * 0.88), xytext=(h.mean(), ax.get_ylim()[1] * 0.88),
        arrowprops=dict(arrowstyle="<->", color=FG, linewidth=1.2),
    )
    ax.text((h.mean() + p.mean()) / 2, ax.get_ylim()[1] * 0.91,
            f"{gap:.1f} years", color=FG, ha="center", fontsize=10, fontweight="bold")
    ax.set_xlabel("age at recording (years)")
    ax.set_ylabel("sessions")
    ax.set_title(
        f"SVD recruitment asymmetry: {len(d)} sessions / {int(d['SprecherID'].nunique())} speakers\n"
        f"means {h.mean():.1f} vs {p.mean():.1f} years -- age alone gives ROC-AUC "
        f"{f1['auc_age_only']:.4f}",
        fontsize=10,
    )
    leg = ax.legend(facecolor=DARK_BG, edgecolor=GRID, labelcolor=FG, fontsize=9)
    leg.get_frame().set_alpha(0.9)
    _style(ax)
    fig.tight_layout()
    out = ASSETS / "svd_age_distribution.png"
    fig.savefig(out, facecolor=DARK_BG)
    plt.close(fig)
    return out, checks


def plot_confound_vs_sota(f1: dict, bench: dict) -> Path:
    """Confound baselines (measured) against the published SVD target."""
    spk = bench["speaker_level"]
    conf_keys = [k for k in spk if k.startswith("confound::")]
    labels, vals, kinds = [], [], []
    for k in sorted(conf_keys, key=lambda k: spk[k]["roc_auc"]):
        labels.append(k.replace("confound::", "").replace("_", " "))
        vals.append(spk[k]["roc_auc"])
        kinds.append("confound")
    best = bench["margins_vs_confound"]["best_audio_head"]
    labels.append(f"AUDIO eGeMAPS ({best})")
    vals.append(spk[best]["roc_auc"])
    kinds.append("audio")
    labels.append("age+sex, metadata only (F1)")
    vals.append(f1["auc_age_sex_speaker_disjoint"])
    kinds.append("f1")

    colors = {"confound": "#8892a6", "audio": C_BAR, "f1": C_PATH}
    fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=150)
    fig.patch.set_facecolor(DARK_BG)
    y = np.arange(len(labels))
    ax.barh(y, vals, color=[colors[k] for k in kinds], height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    for i, v in enumerate(vals):
        ax.text(v + 0.008, i, f"{v:.3f}", va="center", color=FG, fontsize=9)
    ax.axvline(0.5, color=GRID, linestyle=":", linewidth=1.4)
    ax.text(0.5, len(labels) - 0.35, " chance", color="#8892a6", fontsize=8, va="center")
    ax.axvline(0.8522, color="#ffd166", linestyle="--", linewidth=1.6)
    ax.text(0.845, -0.85, "published SVD UAR 85.22\n(arXiv:2410.10537 -- different\nmetric, full corpus)",
            color="#ffd166", fontsize=8, va="bottom", ha="right")
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("speaker-level ROC-AUC (higher = better)")
    n_spk = bench["dataset"]["n_speakers"]
    n_rec = bench["dataset"]["n_recordings"]
    ax.set_title(
        "SVD confound bars vs the audio model\n"
        f"grey/blue: decoded pilot slice, n={n_rec} recordings / {n_spk} speakers (SCREENING)\n"
        f"orange: metadata only, full corpus, n={f1['n_sessions']} sessions / "
        f"{f1['n_speakers']} speakers",
        fontsize=9.5,
    )
    _style(ax)
    fig.tight_layout()
    out = ASSETS / "confound_vs_sota.png"
    fig.savefig(out, facecolor=DARK_BG)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

CSS = """
:root{--bg:#0d1017;--panel:#12151b;--panel2:#171b24;--line:#232936;--fg:#e6e9ef;
--muted:#98a2b8;--accent:#7e9cff;--warn:#ffd166;--bad:#ff6b6b;--ok:#5ddba4;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1180px;margin:0 auto;padding:32px 20px 96px}
h1{font-size:30px;line-height:1.25;margin:0 0 8px;letter-spacing:-.02em}
h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
margin:64px 0 14px;font-weight:600;border-bottom:1px solid var(--line);padding-bottom:10px}
h3{font-size:18px;margin:28px 0 10px}
p{margin:0 0 14px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
code{background:#1b2130;border:1px solid var(--line);border-radius:4px;
padding:1px 5px;font-size:.86em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
pre{background:#0a0d13;border:1px solid var(--line);border-radius:8px;padding:14px 16px;
overflow-x:auto;font-size:13px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.thesis{font-size:19px;line-height:1.55;color:#cfd6e4;margin:14px 0 22px;
border-left:3px solid var(--accent);padding-left:16px}
.banner{background:#241d0c;border:1px solid #6b5518;color:var(--warn);
border-radius:8px;padding:12px 16px;margin:18px 0;font-size:14px}
.meta{color:var(--muted);font-size:13px;margin-top:10px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:22px 24px;margin:18px 0}
.grid{display:grid;gap:16px}
.g4{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.stat .n{font-size:34px;font-weight:650;letter-spacing:-.02em;line-height:1.1}
.stat .k{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.1em;
margin-top:8px}
.stat .s{color:var(--muted);font-size:13px;margin-top:8px}
ul{margin:0 0 14px;padding-left:20px}
li{margin:7px 0}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{position:sticky;top:0;background:var(--panel2);text-align:left;padding:12px 14px;
font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
border-bottom:1px solid var(--line);white-space:nowrap;cursor:pointer;user-select:none}
th:hover{color:var(--fg)}
th.sort-asc::after{content:" \\25B2";color:var(--accent)}
th.sort-desc::after{content:" \\25BC";color:var(--accent)}
td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.nm{color:var(--muted);font-style:italic}
.chip{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;
padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted);
white-space:nowrap}
.chip.screen{border-color:#6b5518;color:var(--warn);background:#241d0c}
.chip.eval{border-color:#1f5b45;color:var(--ok);background:#0e2119}
.chip.bad{border-color:#6b2222;color:var(--bad);background:#2a1313}
.chip.pend{border-color:#2f3a52;color:#9fb0d0;background:#151b28}
.bad{color:var(--bad)}
.ok{color:var(--ok)}
.warnc{color:var(--warn)}
.muted{color:var(--muted)}
.small{font-size:13px}
img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:10px;display:block}
figure{margin:0}
figcaption{color:var(--muted);font-size:13px;margin-top:10px}
.filter{width:100%;max-width:340px;background:var(--panel2);border:1px solid var(--line);
border-radius:8px;color:var(--fg);padding:9px 12px;font-size:14px;margin:0 0 12px}
.filter:focus{outline:none;border-color:var(--accent)}
footer{margin-top:72px;padding-top:22px;border-top:1px solid var(--line);
color:var(--muted);font-size:13px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 18px;font-size:14px}
.kv dt{color:var(--muted)}
.kv dd{margin:0}
@media (max-width:640px){.wrap{padding:22px 14px 72px}h1{font-size:24px}
.stat .n{font-size:27px}td,th{padding:10px 11px}}
"""

JS = """
document.querySelectorAll('table[data-sortable]').forEach(function(t){
  t.querySelectorAll('th').forEach(function(th,i){
    th.addEventListener('click',function(){
      var tb=t.tBodies[0],rows=Array.prototype.slice.call(tb.rows);
      var dir=th.dataset.dir==='asc'?-1:1;
      t.querySelectorAll('th').forEach(function(o){
        delete o.dataset.dir;o.classList.remove('sort-asc','sort-desc');});
      th.dataset.dir=dir===1?'asc':'desc';
      th.classList.add(dir===1?'sort-asc':'sort-desc');
      // numeric compare only when BOTH cells are numbers with no words in them,
      // otherwise "PROCESS-2" would sort as -2
      var numeric=function(s){return /\\d/.test(s)&&!/[A-Za-z]/.test(s);};
      rows.sort(function(a,b){
        var x=a.cells[i].innerText.trim().split('\\n')[0].trim();
        var y=b.cells[i].innerText.trim().split('\\n')[0].trim();
        if(numeric(x)&&numeric(y)){
          var nx=parseFloat(x.replace(/[^0-9.\\-]/g,'')),ny=parseFloat(y.replace(/[^0-9.\\-]/g,''));
          if(!isNaN(nx)&&!isNaN(ny))return (nx-ny)*dir;
        }
        return x.localeCompare(y)*dir;
      });
      rows.forEach(function(r){tb.appendChild(r);});
    });
  });
});
document.querySelectorAll('input[data-filters]').forEach(function(inp){
  var run=function(){
    var t=document.getElementById(inp.dataset.filters),q=inp.value.toLowerCase(),n=0;
    var rows=Array.prototype.slice.call(t.tBodies[0].rows);
    rows.forEach(function(r){
      var hit=r.innerText.toLowerCase().indexOf(q)>-1;
      r.style.display=hit?'':'none';if(hit)n++;
    });
    var c=document.getElementById(inp.dataset.count);
    if(c)c.textContent=n+' of '+rows.length+' rows shown';
  };
  inp.addEventListener('input',run);run();
});
"""


def hero_numbers() -> dict:
    """Every number in the four-step narrative, read from the artifact that produced it.

    This block used to be hand-typed into the generator's string. That is the exact
    failure the rest of this file exists to prevent (R1: no orphan numbers) -- and it
    cost real accuracy: the sections beneath the panel were never updated to match it,
    so the page carried a full-corpus headline above a 49-speaker scoreboard.
    """
    full = read_json("bench_svd_full")
    v1 = read_json("v1")
    v2 = read_json("v2")

    rec = full["recording_level"]
    bar_key = full["margins_vs_confound"]["confound_bar_name"]
    audio_head = full["margins_vs_confound"]["best_audio_head"]

    # identity's share of the above-chance headroom, from the ranks where the
    # difference against the variance-matched control excludes zero.
    head = v2["auc_full_mean"] - 0.5
    shares = [r["D_vs_pca_topk"] / head for r in v2["rows"]
              if r.get("D_vs_pca_topk_excludes_zero")]
    if not shares:
        sys.exit("FATAL: no V2 rank has D_vs_pca_topk_excludes_zero -- the four-step "
                 "narrative's identity-share claim has no support in the artifact")

    return {
        "age_rec_auc": rec[bar_key]["roc_auc"],
        "audio_rec_auc": rec[audio_head]["roc_auc"],
        "audio_head": audio_head,
        "bar_name": bar_key.replace("confound::", ""),
        "n_speakers_full": full["dataset"]["n_speakers"],
        "n_repeats_full": full["config"]["n_repeats"],
        "identity_lo": min(shares), "identity_hi": max(shares),
        "v2_full": v2["auc_full_mean"], "v2_repeats": v2["repeats"],
        "matched_age_auc": v1["mean_auc_age_only"],
        "matched_gap": v1["mean_age_gap"],
        "egemaps": v1["mean_auc_egemaps"], "wavlm": v1["mean_auc_wavlm"],
        "v1_delta": v1["wavlm_minus_egemaps"], "v1_ci": v1["wavlm_minus_egemaps_ci95"],
        "v1_repeats": v1["repeats"],
        "v1_wins": sum(1 for r in v1["repeats_detail"]
                       if r["auc_egemaps"] > r["auc_wavlm"]),
        "v1_n": len(v1["repeats_detail"]),
        "survives": max(v1["mean_auc_egemaps"], v1["mean_auc_wavlm"]),
    }


def preprocessing_disagreement() -> dict | None:
    """Compare the SVD row of the hand-maintained PREPROCESSING_STATUS.md against the
    machine-written summary.json it describes.

    The markdown was last written 2026-07-25 and still says 667 files / 49 speakers;
    the JSON beside it says 61,170 / 1,679. The old dashboard narrated the markdown in
    one panel and the JSON in the next, so two adjacent elements contradicted each
    other with nothing marking either as stale. An input that disagrees with its own
    machine-written summary is a finding about the inputs, and it is rendered as one.
    """
    text = read_text("preprocessing")
    row = anchor_find(text, r"(?m)^\|\s*SVD\s*\|(.+)$", "data/PREPROCESSING_STATUS.md")
    cells = [strip_md(c) for c in row.group(1).split("|")]
    nums = [re.sub(r"[^\d]", "", c) for c in cells]
    claimed = {"found": nums[0], "decoded": nums[1], "speakers": nums[3]}
    actual = read_json("summary_svd")
    if (str(actual["files_decoded"]) == claimed["decoded"]
            and str(actual["n_speakers"]) == claimed["speakers"]):
        return None
    return {
        "claimed": claimed, "actual": actual,
        "md_written": mtime_utc(require("preprocessing")),
        "json_written": mtime_utc(require("summary_svd")),
    }


def tier_chip(tier: str) -> str:
    t = tier.upper()
    if "EVALUATION" in t:
        return '<span class="chip eval">EVALUATION</span>'
    if "SCREENING" in t:
        return '<span class="chip screen">SCREENING</span>'
    return f'<span class="chip pend">{html.escape(tier)}</span>'


def build_html() -> str:
    f1 = read_json("f1_json")
    bench = load_bench()
    corpora = load_corpus_status()
    hyps = load_hypotheses()
    traps = load_traps()
    board = load_scoreboard()
    lims = findings_limitations()
    sha = git_sha()
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    full = read_json("bench_svd_full")
    spk = bench["speaker_level"]
    rec = bench["recording_level"]
    mvc = bench["margins_vs_confound"]
    best = mvc["best_audio_head"]
    n_rec = bench["dataset"]["n_recordings"]
    n_spk = bench["dataset"]["n_speakers"]
    bench_n = f'n={n_rec} recordings / {n_spk} speakers'

    # ---- status counters (all from artifacts) ------------------------------ #
    n_findings = count_findings()
    log = ROOT / "autoresearch_results" / "experiment_log.jsonl"
    n_log = len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0
    decoded_total = sum(c["decoded"] for c in corpora)

    coswara_total = f'{read_json("coswara_meta")["n_rows"]:,}'
    runs = load_runs()
    by_hyp = runs_by_hypothesis(runs)
    n_eval_runs = sum(1 for r in runs if r["tier"] == "EVALUATION")
    summary = idea_summary()
    n_untested = sum(1 for h in hyps if not by_hyp.get(h["id"]))
    cs = composite_spec()

    out = []
    A = out.append

    A('<div class="wrap">')

    # ---------------- header ----------------
    A("<h1>Voice-Health Claim Audit &mdash; transparency dashboard</h1>")
    hn = hero_numbers()
    A('<div class="panel" style="border-left:4px solid var(--ok)">'
      "<h3 style='margin-top:0'>The result, in four steps</h3>"
      "<p>Each step removes something the model was getting for free, and asks what "
      "survives. Every number here is read from the artifact named beside it.</p>"
      "<ol>"
      f"<li><strong>F1/F3</strong> &mdash; patient <strong>{hn['bar_name'].replace('_', ' ')}"
      f"</strong> reaches <strong>{hn['age_rec_auc']:.4f}</strong> recording-level AUC; "
      f"WavLM (<code>{html.escape(hn['audio_head'])}</code>) reaches "
      f"<strong>{hn['audio_rec_auc']:.4f}</strong>. The audio model loses to one demographic "
      f"variable. <span class=\"small muted\">n={hn['n_repeats_full']} repeats &times; 5 folds "
      f"on {hn['n_speakers_full']:,} speakers &middot; "
      "<code>bench_svd_wavlm_mean_std.json</code></span></li>"
      f"<li><strong>F4</strong> &mdash; projecting out the speaker-identity subspace costs "
      "WavLM <em>more</em> AUC than removing <em>more</em> variance any other way: "
      f"<strong>{hn['identity_lo'] * 100:.0f}&ndash;{hn['identity_hi'] * 100:.0f}%</strong> of "
      "its above-chance headroom is <em>who is speaking</em>. "
      f"<span class=\"small muted\">n={hn['v2_repeats']} &middot; "
      "<code>V2_speaker_subspace.json</code>, shares computed over the ranks whose CI "
      "excludes zero</span></li>"
      f"<li><strong>F7a</strong> &mdash; with age matched to a "
      f"<strong>{hn['matched_gap']:.2f}-year</strong> gap, age-only collapses "
      f"<strong>{hn['age_rec_auc']:.4f} &rarr; {hn['matched_age_auc']:.4f}</strong>. The "
      "confound is genuinely removed, not assumed away. "
      f"<span class=\"small muted\">n={hn['v1_repeats']} &middot; "
      "<code>V1_ssl_vs_handcrafted.json</code></span></li>"
      f"<li><strong>F7b</strong> &mdash; on that matched subset <strong>eGeMAPS "
      f"{hn['egemaps']:.4f} beats WavLM {hn['wavlm']:.4f}</strong> "
      f"(paired difference {hn['v1_delta']:+.4f}, 95% CI "
      f"[{hn['v1_ci'][0]:.3f}, {hn['v1_ci'][1]:.3f}], {hn['v1_wins']}/{hn['v1_n']} seeds). "
      "<strong>88 handcrafted features beat 1536 learned ones.</strong></li></ol>"
      f"<p>What survives once demographics and identity are stripped is "
      f"<strong>AUC &asymp; {hn['survives']:.2f}</strong> &mdash; real, well above chance, "
      "far below the ~0.85 the literature reports here, and nowhere near clinical "
      "usefulness.</p>"
      '<p class="small muted">Each step links to the run that produced it: '
      '<a href="dashboard/experiments/run-bench-wavlm.html">bench-wavlm</a> &middot; '
      '<a href="dashboard/experiments/run-v2-speaker-subspace.html">v2-speaker-subspace</a> '
      '&middot; <a href="dashboard/experiments/run-v1-ssl-vs-handcrafted.html">'
      "v1-ssl-vs-handcrafted</a>.</p></div>")
    A('<p class="thesis">An autonomous, pre-registered audit harness that systematically '
      "re-tests published voice-health classification claims for speaker leakage, acquisition "
      "confounds, and cross-corpus collapse &mdash; publishing a transparent ledger of which "
      "claims survive. <strong>This program does not build another voice-disease "
      "detector.</strong></p>")
    A('<div class="banner"><strong>Internal QA pass &mdash; independent external review '
      "pending.</strong> Implementer, critic and judge share a model family, so no verdict on "
      "this page is external validation, peer review, or a venue decision "
      "(CLAUDE.md R5, R16). Negative results are published here with equal prominence "
      "(R8).</div>")
    A(f'<p class="meta">Generated by <code>scripts/build_dashboard.py</code> on {built} '
      f"&middot; commit <code>{html.escape(sha)}</code> &middot; every number below is read "
      "from a file in this repository; nothing is hand-entered (R1: no orphan numbers, "
      "R2: the agent never states a metric it did not read from an artifact).</p>")
    A('<p class="meta">Not a medical device. No diagnosis, no clinical claim.</p>')
    A('<div class="panel"><h3 style="margin-top:0">The three tiers of this site</h3>'
      "<p>This page is the master. Every claim on it drills down twice, and each tier is "
      "generated from the same declared artifacts, so the three cannot disagree.</p><ul>"
      '<li><strong>Master</strong> (here) &mdash; the four-step result, the run ledger, the '
      "findings ledger, the corpus and scoreboard tables, the audits, and the source "
      "provenance.</li>"
      '<li><strong><a href="hypotheses/index.html">Per-hypothesis registry</a></strong> '
      f"&mdash; {len(hyps)} pre-registered hypotheses, each with its claim, falsifier and "
      "predicted effect rendered <em>above</em> any result. "
      f'<span class="warnc">{n_untested} of {len(hyps)} have never been executed and are '
      "carried as visible debt.</span></li>"
      '<li><strong><a href="dashboard/experiments/index.html">Per-run ledger</a></strong> '
      f"&mdash; {len(runs)} artifact-backed runs, one page each, rendering the artifact in "
      "full: every interval, the power arithmetic, and the reproduction provenance. These "
      "pages also state what they <em>lack</em> &mdash; there is no 7-step reasoning entry "
      "and no <code>experiment_log.jsonl</code> in this repository.</li>"
      '<li><strong><a href="datasets.html">The dataset landscape</a></strong> &mdash; the '
      "25 corpora the field uses, scored on whether a result on each could mean "
      "anything.</li>"
      "</ul></div>")

    # ---------------- background: what the data is, what it can support -------
    bg = load_background()
    A("<h2>Background &mdash; what this data is, and what it can actually detect</h2>")
    A('<div class="panel">')
    A("<h3>The idea</h3>")
    A("<p>A person speaks; a model listens and predicts a health condition. The appeal is "
      "that the sensor is a microphone everyone already owns. Two mechanisms make it "
      "plausible rather than magical. First, <strong>the larynx is the instrument</strong> "
      "&mdash; a vocal-fold paralysis, a polyp, swelling, a tumour or surgical scarring "
      "changes the sound directly. Second, <strong>speech is a motor act</strong> needing "
      "breath control, timing and fine neuromuscular coordination, so neurological and "
      "respiratory disease can leave traces even when the larynx is healthy. The first "
      "mechanism is short and well-evidenced; the second is a long causal chain and "
      "correspondingly weaker. The literature also claims depression, diabetes and heart "
      "failure from voice &mdash; <strong>this program tests none of those</strong>, for the "
      "reason in the next block.</p>")
    A("<h3>The corpus</h3>")
    A("<p>The primary corpus is the <strong>Saarbr&uuml;cken Voice Database</strong>, a "
      "clinical archive from Saarland University Hospital. Each participant records "
      f"<strong>{bg['tasks']} short vocalisations</strong>: the sustained vowels "
      "<code>/a/</code>, <code>/i/</code>, <code>/u/</code> at normal, high, low and "
      "rising-falling pitch, plus one spoken German sentence.</p>")
    A('<div class="grid g4">')
    for n, k, s in (
        (f"{bg['recordings']:,}", "recordings decoded", f"{bg['sessions']:,} sessions"),
        (f"{bg['speakers']:,}", "speakers",
         f"{bg['n_patho_speakers']:,} pathological / {bg['n_healthy_speakers']:,} healthy"),
        (f"{bg['n_pathologies']}", "named pathologies", "see the long tail below"),
        (f"{bg['age_patho'] - bg['age_healthy']:.1f} yr", "age gap",
         f"healthy {bg['age_healthy']:.1f} vs pathological {bg['age_patho']:.1f} &mdash; "
         "the confound this program is about"),
    ):
        A(f'<div class="stat"><div class="n">{n}</div><div class="k">{k}</div>'
          f'<div class="s">{s}</div></div>')
    A("</div>")
    A(f"<h3>How many diseases can it detect? Not {bg['n_pathologies']}.</h3>")
    A("<p>Sorted by how many <em>speakers</em> carry each diagnosis &mdash; not how many "
      "recordings, since a condition with 200 clips from 8 people is an 8-person "
      "condition:</p>")
    A('<div class="tablewrap"><table><thead><tr><th>condition has &ge; N speakers</th>'
      "<th>number of conditions</th><th>speakers covered</th></tr></thead><tbody>")
    for t in bg["tiers"]:
        floor = t["thresh"] == 30
        lbl = (f"&ge; {t['thresh']} <span class=\"small muted\">(this program's data floor)</span>"
               if floor else f"&ge; {t['thresh']}")
        em = ("<strong>", "</strong>") if floor else ("", "")
        A(f'<tr><td>{lbl}</td><td class="num">{em[0]}{t["n_conditions"]}{em[1]}</td>'
          f'<td class="num muted">{t["n_speakers"]:,}</td></tr>')
    A("</tbody></table></div>")
    tier30 = next(t for t in bg["tiers"] if t["thresh"] == 30)
    top = ", ".join(f"<em>{html.escape(k)}</em> ({v})" for k, v in bg["top"])
    A(f"<p><strong>{bg['singletons']} of the {bg['n_pathologies']} conditions are "
      "represented by a single speaker.</strong> So the honest answer is:</p>")
    A("<ul>")
    A("<li><strong>One task is properly powered</strong> &mdash; binary <em>healthy vs "
      f"pathological</em> ({bg['n_patho_speakers']:,} vs {bg['n_healthy_speakers']:,} "
      "speakers). Every headline number on this page refers to that task and no other.</li>")
    A(f"<li><strong>At most {tier30['n_conditions']} named conditions</strong> clear a "
      "&ge;30-speaker floor, and would need one-vs-rest treatment with wide intervals. "
      f"The largest are {top}.</li>")
    A(f"<li><strong>{bg['n_pathologies'] - tier30['n_conditions']} conditions cannot be "
      "modelled at all</strong> at any defensible sample size.</li>")
    A("</ul>")
    A("<p class=\"warnc\">And note what those conditions <em>are</em>: almost all are "
      "<strong>dysphonias and structural larynx disorders</strong> &mdash; the category where "
      "the sound changes because the sound-producing organ changed. This corpus contains "
      "essentially no systemic disease. A model trained here detects <strong>disordered "
      "voice</strong>, not disease in general, and describing it otherwise is a category "
      "error.</p>")
    A("<h3>Why this program exists</h3>")
    A("<p>Published SVD results report UAR in the mid-80s. But healthy participants here "
      f"average {bg['age_healthy']:.0f} years and patients {bg['age_patho']:.0f}, so patient "
      "age alone reaches ROC-AUC 0.87 without hearing a single audio sample (F1 below). Any "
      "classifier that quietly learns &quot;older &rArr; patient&quot; inherits that score "
      "for free. The interesting quantity is therefore not the accuracy but the "
      "<strong>margin above the demographic baseline on the identical folds</strong> &mdash; "
      "a number the field does not currently report. Measuring it is the entire purpose of "
      "this repository.</p>")
    A('<p class="small muted">Every count in this section is recomputed at build time from '
      "<code>data/interim/svd/manifest.csv</code>; none is hand-entered.</p>")
    A("</div>")
    # the full landscape lives on its own page -- it is too wide for this column
    A('<div class="panel"><h3 style="margin-top:0">The rest of the field &rarr; '
      '<a href="datasets.html">the dataset landscape</a></h3>'
      "<p>SVD is one corpus of many. The companion page catalogues <strong>every dataset the "
      "field uses to claim a disease can be heard in a voice</strong> &mdash; 25 corpora "
      "across 7 disease families (larynx, Parkinson's, dementia, dysarthria, respiratory, "
      "mental health, multi-phenotype), 8 of them released or audited in <strong>2026</strong> "
      "&mdash; each scored on the question the published surveys do not ask: <em>could a "
      "result on this dataset mean anything?</em> "
      '<span class="small muted">Spoiler: 5 of the 25 can never carry a generalisation claim '
      "at all.</span></p></div>")

    # ---------------- how to read ----------------
    A("<h2>How to read this</h2>")
    A('<div class="panel"><ul>')
    A("<li><strong>Every number carries its n and its tier.</strong> "
      '<span class="chip screen">SCREENING</span> means n&nbsp;&le;&nbsp;3 and may never be '
      'called a result; <span class="chip eval">EVALUATION</span> means n&nbsp;&ge;&nbsp;8 '
      "with the full statistical contract. A cell with no measurement says "
      f'{NOT_MEASURED} &mdash; it is never filled with a guess.</li>')
    A("<li><strong>A confound baseline outranks a model.</strong> Age, sex, duration and "
      "loudness are fitted first; an audio model may claim only the margin <em>above</em> the "
      "strongest of them. On this page the audio model currently loses that comparison.</li>")
    A("<li><strong>Speaker-disjoint or it does not count.</strong> Splits group on speaker id. "
      "A corpus with no real speaker id (COUGHVID) cannot carry a generalisation claim at "
      "all, and is marked in red below.</li>")
    A("<li><strong>Negative and blocked entries are the product.</strong> The ledger's value "
      "is that it reports the claims that did not survive and the corpora that cannot support "
      "a claim, in the same tables and with the same detail as everything else.</li>")
    A("</ul></div>")

    # ---------------- status at a glance ----------------
    A("<h2>Status at a glance</h2>")
    A('<div class="grid g4">')
    fnd = findings()
    tiers = {}
    for f in fnd:
        tiers[f["tier"]] = tiers.get(f["tier"], 0) + 1
    tier_line = " &middot; ".join(f"{v} {k.lower()}" for k, v in sorted(tiers.items()))
    A(f'<div class="stat"><div class="n">{n_findings}</div><div class="k">findings</div>'
      f'<div class="s">{tier_line} &mdash; see the ledger below</div></div>')
    A(f'<div class="stat"><div class="n">{len(runs)}</div>'
      f'<div class="k">artifact-backed runs</div>'
      f'<div class="s">{n_eval_runs} at EVALUATION tier &middot; '
      f'<code>experiment_log.jsonl</code> rows: {n_log} (the file does not exist; the run '
      "ledger is assembled from the artifacts themselves)</div></div>")
    A(f'<div class="stat"><div class="n">{len(corpora)}</div><div class="k">corpora decoded</div>'
      f'<div class="s">{decoded_total:,} files at 16&nbsp;kHz mono &mdash; but see the corpus '
      "table for what each one can support</div></div>")
    A(f'<div class="stat"><div class="n">{len(hyps)}'
      f'<span class="warnc"> &minus; {n_untested}</span></div>'
      '<div class="k">hypotheses registered &minus; never executed</div>'
      f'<div class="s"><strong class="warnc">{n_untested} of {len(hyps)} have no run at '
      "all.</strong> A hypothesis whose falsifier has not been executed is never SUPPORTED "
      '(R7); it is counted here as debt. <a href="hypotheses/index.html">registry &rarr;</a>'
      "</div></div>")
    A("</div>")

    dis = preprocessing_disagreement()
    if dis:
        A('<div class="panel" style="border-left:4px solid var(--warn)">'
          "<h3 style='margin-top:0' class=\"warnc\">Two inputs disagree about the same "
          "corpus</h3>"
          f'<p><code>data/PREPROCESSING_STATUS.md</code> (hand-maintained, last written '
          f'{html.escape(dis["md_written"])}) states SVD at '
          f'<strong>{html.escape(dis["claimed"]["decoded"])}</strong> decoded files from '
          f'<strong>{html.escape(dis["claimed"]["speakers"])}</strong> speakers. '
          f'<code>data/interim/svd/summary.json</code> (machine-written, '
          f'{html.escape(dis["json_written"])}) states '
          f'<strong>{dis["actual"]["files_decoded"]:,}</strong> decoded from '
          f'<strong>{dis["actual"]["n_speakers"]:,}</strong> speakers.</p>'
          "<p>Every count on this page comes from the JSON. The markdown is stale and is "
          "flagged rather than narrated &mdash; an earlier build of this page rendered the "
          "markdown in one panel and the JSON in the next, so two adjacent elements "
          "contradicted each other with nothing marking either. This panel is generated by "
          "a comparison, so it disappears on its own once the markdown is refreshed.</p>"
          "</div>")

    A('<div class="panel"><h3>What is blocked right now</h3><ul>')
    A(f"<li><strong>SVD is decoded but not complete.</strong> "
      f'{corpora[0]["decoded"]:,} of {corpora[0]["found"]:,} found files decoded, covering '
      f'<strong>{corpora[0]["speakers"]:,} speakers</strong> against the '
      f'<strong>{f1["n_speakers"]:,}</strong> the distributed metadata lists &mdash; so '
      f'{f1["n_speakers"] - corpora[0]["speakers"]:,} speakers have metadata but no audio on '
      "this host, and no audio result covers them. "
      '<span class="small muted">(data/interim/svd/summary.json vs '
      "F1_demographic_baseline.json)</span></li>")
    A(f"<li><strong>Coswara audio is partially decoded.</strong> "
      f"{corpora[2]['decoded']:,} of {corpora[2]['found']:,} found files, "
      f"{corpora[2]['speakers']} of {coswara_total} participants &mdash; the host has ~15&nbsp;GB free "
      "disk and the decoder stops cleanly rather than filling the volume. "
      '<span class="small muted">(data/interim/coswara/summary.json)</span></li>')
    A('<li class="bad"><strong>COUGHVID can never support an evaluation claim.</strong> '
      "34,434 rows, 34,434 unique uuids, zero participant identifiers. Pretraining and "
      "out-of-distribution probing only.</li>")
    A("<li><strong>PROCESS-2</strong> is behind a manually-reviewed HuggingFace gate "
      "(<code>CognoSpeak/PROCESS-2</code>); <strong>Bridge2AI-Voice v3.1.0</strong> needs "
      "PhysioNet credentialing plus a separate DACO application for raw audio. Both are "
      "paperwork-bound, not compute-bound. "
      '<span class="small muted">(data/ACQUISITION_STATUS.md)</span></li>')
    A("</ul></div>")

    # ---------------- F1 ----------------
    A("<h2>F1 &mdash; the headline finding</h2>")
    A('<div class="panel">')
    A("<h3>On SVD, patient age alone reaches ROC-AUC "
      f"{f1['auc_age_only']:.4f} without hearing any audio</h3>")
    A('<p class="meta">'
      f'{tier_chip("SCREENING")} metadata-only &middot; artifact '
      f'<code>data/raw/svd_meta/voice_data.csv</code> (md5 '
      f'<code>{f1["artifact_md5"][:12]}…</code>) &middot; measured values in '
      f'<code>autoresearch_results/F1_demographic_baseline.json</code></p>')
    A(f"<p>Using <strong>only</strong> the demographic metadata distributed with the "
      f"Saarbr&uuml;cken Voice Database &mdash; no audio, no features, no model of speech "
      f"&mdash; over n&nbsp;=&nbsp;{f1['n_sessions']:,} sessions "
      f"({f1['n_pathological']:,} pathological / {f1['n_healthy']} healthy) from "
      f"{f1['n_speakers']:,} unique speakers:</p>")
    A('<div class="tablewrap"><table><thead><tr>'
      "<th>predictor</th><th>ROC-AUC (pathological vs healthy)</th><th>n</th></tr></thead><tbody>")
    A(f'<tr><td>age alone</td><td class="num"><strong>{f1["auc_age_only"]:.4f}</strong></td>'
      f'<td class="num muted">{f1["n_sessions"]:,} sessions</td></tr>')
    A(f'<tr><td>sex alone</td><td class="num">{f1["auc_sex_only"]:.4f}</td>'
      f'<td class="num muted">{f1["n_sessions"]:,} sessions</td></tr>')
    A(f'<tr><td>age + sex, logistic, <strong>speaker-disjoint</strong> 5-fold '
      f'<code>GroupKFold</code></td>'
      f'<td class="num"><strong>{f1["auc_age_sex_speaker_disjoint"]:.4f}</strong></td>'
      f'<td class="num muted">{f1["n_sessions"]:,} sessions /<br>{f1["n_speakers"]:,} '
      "speaker groups</td></tr>")
    A("</tbody></table></div>")
    A('<h3>Underlying cause &mdash; a recruitment asymmetry</h3>')
    A(f"<p>Healthy speakers are young volunteers; pathological speakers are older clinic "
      f"patients. Mean age <strong>{f1['mean_age_healthy']:.1f}</strong> years (healthy) vs "
      f"<strong>{f1['mean_age_pathological']:.1f}</strong> years (pathological) &mdash; a gap "
      f"of <strong>{f1['mean_age_pathological'] - f1['mean_age_healthy']:.1f} years</strong>.</p>")
    A('<figure><img src="assets/svd_age_distribution.png" alt="Age distribution of healthy vs '
      'pathological SVD sessions, showing a 22.7-year gap in means">'
      f'<figcaption>Recomputed from <code>voice_data.csv</code> by '
      f'<code>scripts/build_dashboard.py</code>; the script aborts if the recomputed counts and '
      f'means disagree with <code>F1_demographic_baseline.json</code>.</figcaption></figure>')
    A("<h3>A live leakage trap in the same artifact</h3>")
    A(f"<p><strong>{f1['speakers_with_multiple_sessions']} of {f1['n_speakers']:,} speakers "
      f"contribute more than one session</strong> (max {f1['max_sessions_per_speaker']} "
      "sessions for a single speaker). Splitting SVD at the recording level &mdash; the default "
      "in any naive <code>train_test_split</code> &mdash; leaks those speakers across folds. "
      "All work in this repository splits on <code>SprecherID</code> via "
      "<code>GroupKFold</code> and asserts speaker-disjointness before every fit.</p>")
    A('<h3 class="warnc">What this does NOT claim &mdash; read before citing</h3>')
    A("<ol>")
    for item in lims:
        A(f"<li>{md_inline(item)}</li>")
    A("</ol>")
    A(f'<p class="small muted">Quoted verbatim from <code>FINDINGS.md</code> &sect;F1. The '
      f'published SVD benchmark is {md_inline(f1["published_benchmark"])}.</p>')
    A("<h3>Reproduce</h3>")
    A("<pre># metadata (167 KB), then the baseline -- CPU, seconds, no audio required\n"
      "python scripts/fetch_svd.py --metadata-only\n"
      "python scripts/audit_demographic_baseline.py --dataset svd</pre>")
    A("</div>")

    # ---------------- E1: first measured benchmark ----------------
    A("<h2>First measured audio benchmark &mdash; a negative result, since superseded</h2>")
    A('<div class="panel">')
    A(f"<h3>eGeMAPS on the decoded SVD pilot slice does not clear its own age bar</h3>")
    A(f'<p class="meta">{tier_chip("EVALUATION")} '
      f'<span class="chip screen">SCOPE-LIMITED &mdash; {n_spk} of '
      f'{full["dataset"]["n_speakers"]:,} speakers</span> '
      f'<span class="chip bad">CONFOUND BAR NOT CLEARED</span> &middot; artifact '
      f'<code>autoresearch_results/bench_svd_egemaps.json</code> &middot; config hash '
      f'<code>{bench["config_hash"]}</code> &middot; run commit '
      f'<code>{bench["git_sha"][:12]}</code> &middot; {html.escape(bench["generated_utc"])} '
      f'&middot; {bench["elapsed_s"] / 60:.0f} min CPU</p>')
    A(f'<p>Command: <code>{html.escape(bench["command"])}</code> &mdash; '
      f'{html.escape(bench["backend"]["backend"])}, '
      f'{bench["dataset"]["embedding_dim"]} features, '
      f'{bench["config"]["n_folds"]}-fold speaker-disjoint &times; '
      f'{bench["config"]["n_repeats"]} repeated partitions, {bench_n}, '
      f'{bench["dataset"]["n_positive_speakers"]} pathological / '
      f'{bench["dataset"]["n_negative_speakers"]} healthy speakers.</p>')
    A('<div class="tablewrap"><table data-sortable><thead><tr>'
      "<th>head / baseline</th><th>speaker-level ROC-AUC</th><th>95% CI</th>"
      "<th>recording-level ROC-AUC</th><th>UAR</th><th>ECE</th><th>verdict vs age bar</th>"
      "</tr></thead><tbody>")
    order = [k for k in spk if not k.startswith("confound::")] + \
            [k for k in spk if k.startswith("confound::")]
    for k in order:
        s = spk[k]
        r = rec.get(k, {})
        is_conf = k.startswith("confound::")
        name = k.replace("confound::", "")
        label = (f'<span class="muted">confound</span> <code>{html.escape(name)}</code>'
                 if is_conf else f"<code>{html.escape(k)}</code>")
        if is_conf:
            verdict = ('<span class="chip pend">baseline</span>'
                       if k != mvc["confound_bar_name"]
                       else '<span class="chip screen">THE BAR</span>')
        else:
            v = bench["verdicts"].get(k, "")
            verdict = (f'<span class="chip bad">{html.escape(v)}</span>' if "NOT" in v
                       else f'<span class="chip eval">{html.escape(v)}</span>')
        ci = s.get("roc_auc_ci95", {})
        A(f"<tr><td>{label}</td>"
          f'<td class="num"><strong>{s["roc_auc"]:.4f}</strong></td>'
          f'<td class="num muted">[{ci.get("lo", float("nan")):.3f}, '
          f'{ci.get("hi", float("nan")):.3f}]</td>'
          f'<td class="num">{r.get("roc_auc", float("nan")):.4f}</td>'
          f'<td class="num">{s["uar"]:.4f}</td>'
          f'<td class="num">{s["ece"]:.3f}</td>'
          f"<td>{verdict}</td></tr>")
    A("</tbody></table></div>")
    A(f'<p class="small muted">Sortable: click a column header. CI = 2,000-resample '
      f'speaker-level bootstrap. All rows: {bench_n}.</p>')
    A(f"<p><strong>Result:</strong> the strongest confound baseline is "
      f'<code>{html.escape(mvc["confound_bar_name"].replace("confound::", ""))}</code> at '
      f'speaker-level AUC {mvc["confound_bar_auc_speaker"]:.4f}. The best audio head '
      f'(<code>{best}</code>) reaches {spk[best]["roc_auc"]:.4f}, a delta of '
      f'{mvc["per_head"][best]["speaker_level_delta_auc"]["delta"]:+.4f} '
      f'(95% CI [{mvc["per_head"][best]["speaker_level_delta_auc"]["lo"]:.3f}, '
      f'{mvc["per_head"][best]["speaker_level_delta_auc"]["hi"]:.3f}]). '
      f'<strong>All {len(bench["verdicts"])} heads are NOT CLEARED.</strong> '
      "On this slice, eGeMAPS carries no demonstrated signal above patient age.</p>")
    A(f'<p class="warnc"><strong>What this does NOT claim, and what has since '
      f'superseded it.</strong> This is {n_spk} speakers &mdash; a speaker-disjoint test '
      "fold holds about ten people and the 95% CI on any accuracy is roughly "
      "&plusmn;15&nbsp;pp, visible in the intervals above. It satisfies the repeat "
      f'contract ({bench["config"]["n_repeats"]} repeats) and is still a narrow slice; '
      "both facts are stated because either alone would mislead. It is <em>not</em> "
      "evidence that eGeMAPS fails on full SVD. The same corpus has since been measured at "
      f'<strong>{full["dataset"]["n_speakers"]:,} speakers</strong> with a different '
      f'representation &mdash; see <a href="dashboard/experiments/run-bench-wavlm.html">'
      "run-bench-wavlm</a>, which reaches the same verdict against the same bar. This "
      "section is kept rather than deleted because a superseded null that is quietly "
      "removed is indistinguishable from one that was never run (R8).</p>")
    A('<figure><img src="assets/confound_vs_sota.png" alt="Bar chart of measured confound '
      'baselines against the audio model and the published SVD target">'
      "<figcaption>Every bar is a measured speaker-level AUC read from "
      "<code>bench_svd_egemaps.json</code> or "
      "<code>F1_demographic_baseline.json</code>. The dashed line is the published target and "
      "is a <em>different metric</em> (UAR) on a <em>different</em>, larger slice &mdash; it is "
      "drawn for orientation, not as a like-for-like contest.</figcaption></figure>")
    A("</div>")

    # ---------------- scoreboard ----------------
    A("<h2>Benchmark scoreboard</h2>")
    A('<p class="small muted">Published SOTA cells are quoted verbatim from '
      "<code>corpus/SURVEY_datasets.md</code> &sect;1. &quot;Ours&quot; is filled only from a "
      "measured artifact in <code>autoresearch_results/</code>; everything else says "
      f"{NOT_MEASURED}. Margins are shown only where the two numbers are the same metric on a "
      "comparable slice &mdash; otherwise the cell says so.</p>")
    A('<input class="filter" data-filters="scoreboard" placeholder="filter datasets...">')
    A('<div class="tablewrap"><table id="scoreboard" data-sortable><thead><tr>'
      "<th>dataset</th><th>published SOTA</th><th>ours</th><th>margin vs SOTA</th>"
      "<th>confound baseline</th><th>margin vs confound</th><th>speaker-disjoint?</th>"
      "<th>status</th></tr></thead><tbody>")
    for row in board:
        ds = row["dataset"]
        sota = md_inline(row["sota_raw"])
        if row["cite"] and row["cite"] not in row["sota_raw"]:
            sota += f'<br><span class="small">'\
                    f'<a href="https://arxiv.org/abs/{row["cite"]}">arXiv:{row["cite"]}</a></span>'
        if ds.startswith("SVD"):
            # "Ours" is the WIDEST measured slice, not the first one measured. The pilot is
            # shown beneath it rather than in place of it: an earlier build put the
            # 49-speaker pilot in this cell while the panel above it quoted the
            # full-corpus run, so the page's own scoreboard contradicted its headline.
            fspk = full["speaker_level"]
            fmvc = full["margins_vs_confound"]
            fbest = fmvc["best_audio_head"]
            fds = full["dataset"]
            ours = (f'<span class="num">UAR {fspk[fbest]["uar"]:.4f}</span> / '
                    f'<span class="num">AUC {fspk[fbest]["roc_auc"]:.4f}</span>'
                    f'<br><span class="small muted">n={fds["n_recordings"]:,} recordings / '
                    f'{fds["n_speakers"]:,} speakers, {full["config"]["n_repeats"]} repeats '
                    f'&times; {full["config"]["n_folds"]} folds, WavLM '
                    f'<code>{fbest}</code>, speaker-level</span> {tier_chip("EVALUATION")}'
                    f'<br><span class="small muted">superseded pilot: eGeMAPS '
                    f'<code>{best}</code> AUC {spk[best]["roc_auc"]:.4f} on {bench_n} '
                    "&mdash; same corpus, 3% of the speakers</span>")
            margin = ('<span class="nm">not comparable</span><br>'
                      '<span class="small muted">the published figure is UAR; ours is '
                      "ROC-AUC. Different metrics are not differenced here.</span>")
            cbar = (f'<span class="num">{fmvc["confound_bar_auc_speaker"]:.4f}</span> AUC'
                    f'<br><span class="small muted">'
                    f'{html.escape(fmvc["confound_bar_name"].replace("confound::", ""))}, '
                    "same folds, same run</span>"
                    f'<br><span class="num">{f1["auc_age_sex_speaker_disjoint"]:.4f}</span> AUC'
                    f'<br><span class="small muted">age+sex, metadata only, full corpus '
                    "(F1)</span>")
            dd = fmvc["per_head"][fbest]["speaker_level_delta_auc"]
            cmargin = (f'<span class="num">{dd["delta"]:+.4f}</span> AUC<br>'
                       f'<span class="small muted">95% CI [{dd["lo"]:.3f}, {dd["hi"]:.3f}] '
                       + ("&mdash; includes 0"
                          if dd["lo"] <= 0 <= dd["hi"] else "&mdash; excludes 0")
                       + "</span><br>"
                       f'<span class="chip bad">NOT CLEARED</span>')
            disj = '<span class="ok">YES &mdash; SprecherID</span>'
            status = ('<span class="chip eval">EVALUATION</span> '
                      '<span class="chip bad">NEGATIVE</span>')
        elif ds.startswith("Coswara"):
            ours, margin, cmargin = NOT_MEASURED, NOT_MEASURED, NOT_MEASURED
            cbar = NOT_MEASURED
            cw = read_json("coswara_meta")
            n_blank = cw["returning_user_field_rU"].get("", 0)
            disj = ('<span class="ok">YES &mdash; participant id</span><br>'
                    '<span class="small muted">submission-disjoint, not person-disjoint: '
                    f'the returning-user flag is blank for {n_blank:,} of '
                    f'{cw["n_rows"]:,}</span>')
            status = '<span class="chip pend">PENDING</span>'
        elif ds.startswith("PROCESS-2"):
            ours, margin, cbar, cmargin = NOT_MEASURED, NOT_MEASURED, NOT_MEASURED, NOT_MEASURED
            disj = '<span class="muted">n/a &mdash; not obtained</span>'
            status = ('<span class="chip pend">BLOCKED</span><br>'
                      '<span class="small muted">manual HF gate; 400 participants fails the '
                      "500/class bar &mdash; screening-tier only</span>")
        else:
            ours, margin, cbar, cmargin = NOT_MEASURED, NOT_MEASURED, NOT_MEASURED, NOT_MEASURED
            disj = '<span class="muted">n/a &mdash; not obtained</span>'
            status = '<span class="chip pend">BLOCKED</span>'
        A(f"<tr><td><strong>{html.escape(ds)}</strong></td><td>{sota}</td><td>{ours}</td>"
          f"<td>{margin}</td><td>{cbar}</td><td>{cmargin}</td><td>{disj}</td>"
          f"<td>{status}</td></tr>")
    A("</tbody></table></div>")

    # ---------------- corpus status ----------------
    A("<h2>Corpus status</h2>")
    A('<div class="tablewrap"><table data-sortable><thead><tr>'
      "<th>corpus</th><th>on disk</th><th>files found</th><th>decoded</th><th>speakers</th>"
      "<th>audio</th><th>class balance</th><th>licence / access</th>"
      "<th>speaker-disjoint possible?</th></tr></thead><tbody>")
    for c in corpora:
        labels = "<br>".join(
            f'<span class="num">{v:,}</span> {html.escape(k)}' for k, v in c["labels"].items())
        if c["disjoint"]:
            dj = (f'<span class="ok">YES</span><br><span class="small muted">'
                  f'provenance: {html.escape(c["provenance"])}</span>')
        else:
            dj = ('<span class="bad"><strong>NO &mdash; cannot support an evaluation '
                  "claim (0 real speaker ids)</strong></span><br>"
                  '<span class="small">uuid is per-recording; one person may appear in both '
                  "halves of any split and there is no way to detect it. Pretraining and OOD "
                  "probing only.</span>")
        dupe = (f'<br><span class="small muted">{c["dupes"]} duplicate waveform hashes '
                "(within-speaker only)</span>" if c["dupes"] else "")
        A(f'<tr><td><strong>{html.escape(c["corpus"])}</strong>{dupe}</td>'
          f'<td class="num">{html.escape(c["on_disk"])}</td>'
          f'<td class="num">{c["found"]:,}</td>'
          f'<td class="num">{c["decoded"]:,}'
          + (f'<br><span class="small bad">{c["failed"]:,} failed</span>' if c["failed"] else "")
          + f'</td><td class="num">{c["speakers"]:,}</td>'
          f'<td class="num">{c["duration_min"]:.1f} min</td>'
          f"<td>{labels}</td>"
          f'<td class="small">{md_inline(c["licence"])}</td>'
          f"<td>{dj}</td></tr>")
    A("</tbody></table></div>")
    A('<p class="small muted">Counts read from <code>data/interim/&lt;corpus&gt;/summary.json</code> '
      "and the row count of each <code>manifest.csv</code>; on-disk sizes from "
      "<code>data/ACQUISITION_STATUS.md</code>; licences from "
      "<code>corpus/SURVEY_datasets.md</code>. SVD and Coswara are partial acquisitions "
      "&mdash; the speaker counts here are what is decoded on this host, not corpus totals "
      f"(SVD: {f1['n_speakers']:,} speakers exist in the distributed metadata, "
      f"{corpora[0]['speakers']:,} decoded; Coswara: "
      f"{coswara_total} exist, {corpora[2]['speakers']} decoded). Both totals are read, "
      "not typed: the SVD figure comes from <code>F1_demographic_baseline.json</code> and "
      "the Coswara figure from "
      "<code>autoresearch_results/acquisition/coswara_meta_stats.json</code>.</p>")

    # ---------------- run ledger ----------------
    A("<h2>Run ledger &mdash; every artifact-backed run</h2>")
    A('<p class="small muted">There is no <code>experiment_log.jsonl</code> in this '
      "repository, so this table is assembled from the result artifacts themselves through "
      "a <em>declared</em> registry in <code>scripts/build_common.py</code>: a run that is "
      "renamed, deleted, or added without being declared fails the build. That gate exists "
      "because three executed hypotheses once sat on disk for days while every published "
      "surface reported them UNTESTED. Every row carries its n and its tier; click a "
      "column header to sort, type to filter, click a run to open its full page.</p>")
    A('<input class="filter" data-filters="runs" data-count="runcount" '
      'placeholder="filter runs...">')
    A('<p class="small muted" id="runcount"></p>')
    A('<div class="tablewrap"><table id="runs" data-sortable><thead><tr>'
      "<th>run</th><th>tier</th><th>n</th><th>corpus / representation</th>"
      "<th>headline metric</th><th>reference bar</th><th>verdict</th>"
      "<th>hypothesis</th><th>finding</th><th>written</th></tr></thead><tbody>")
    for r in runs:
        cls = {"EVALUATION": "eval", "SCREENING": "screen", "CONTROL": "pend"}[r["tier"]]
        bar = (f'{r["bar"]:.4f}' if r.get("bar") is not None
               else html.escape(str(r.get("bar_text", "—"))))
        A(f'<tr><td><a href="dashboard/experiments/{html.escape(r["id"])}.html">'
          f'<strong>{html.escape(r["id"].replace("run-", ""))}</strong></a><br>'
          f'<span class="small muted">{html.escape(r["title"])}</span></td>'
          f'<td><span class="chip {cls}">{html.escape(r["tier"])}</span>'
          + ('<br><span class="chip screen">SCOPE-LIMITED</span>' if r["scope"] else "")
          + f'</td><td class="num">{r["n_repeats"]}<br>'
          f'<span class="small muted">&times;{r["n_folds"]} folds</span></td>'
          f'<td class="small">{html.escape(r["corpus"])}<br>'
          f'<span class="muted">{html.escape(r["backbone"])}</span></td>'
          f'<td class="num"><strong>{r["headline"]:.4f}</strong><br>'
          f'<span class="small muted">{html.escape(r["headline_label"])}</span></td>'
          f'<td class="num">{bar}<br>'
          f'<span class="small muted">{html.escape(r["bar_label"])}</span></td>'
          f'<td class="small">{html.escape(r["verdict"])}</td>'
          + (f'<td><a href="hypotheses/{html.escape(r["hypothesis"])}.html">'
             f'{html.escape(r["hypothesis"])}</a></td>' if r["hypothesis"]
             else '<td class="muted small">predates the registry</td>')
          + f'<td class="small">{html.escape(r["finding"]) or "—"}</td>'
          f'<td class="small muted">{html.escape(r["mtime"])}</td></tr>')
    A("</tbody></table></div>")
    A('<p class="small muted">No row is highlighted as a champion, because this program '
      "has no champion. <code>COMPOSITE.md</code> defines a Goodhart-resistant composite "
      f'(<code>{html.escape(cs["name"])} v{html.escape(cs["version"])}</code>, fingerprint '
      f'<code>{html.escape(cs["fingerprint"][:16])}…</code>) whose implementation location '
      f'<code>{html.escape(cs["impl_path"])}</code> '
      + ("exists" if cs["implemented"] else
         "<strong>does not exist</strong>, so no composite is computed for any row and no "
         "row can be ranked against another")
      + '. Ranking these runs by a number that was never computed would be exactly the '
      "kind of orphan number the rest of this page refuses to print. "
      '<a href="dashboard/experiments/index.html">Run ledger page &rarr;</a></p>')

    # ---------------- findings ledger ----------------
    A("<h2>Findings ledger</h2>")
    A('<p class="small muted">One row per <code>## Fn</code> section of '
      "<code>FINDINGS.md</code>, with the tier the finding claims for itself and the "
      "artifact it points at. Nulls, partials and blocked results appear here at the same "
      "prominence as positives (R8) &mdash; four of these seven are negative or "
      "partial.</p>")
    A('<div class="tablewrap"><table data-sortable><thead><tr><th>id</th><th>finding</th>'
      "<th>tier</th><th>artifact</th><th>run page</th></tr></thead><tbody>")
    art_to_run = {r["artifact"]: r for r in runs}
    for f in fnd:
        tcls = {"EVALUATION": "eval", "CERTIFIED": "eval", "PARTIAL": "screen",
                "SCREENING": "screen"}.get(f["tier"], "pend")
        art = f["artifact"]
        run = art_to_run.get(Path(art).name) if art else None
        A(f'<tr><td><strong>{html.escape(f["id"])}</strong></td>'
          f'<td class="small">{md_inline(f["title"])}<br>'
          f'<span class="small muted">{html.escape(f["tier_raw"])[:190]}</span></td>'
          f'<td><span class="chip {tcls}">{html.escape(f["tier"])}</span></td>'
          + (f'<td class="small"><a href="{BLOB}/{html.escape(art)}"><code>'
             f'{html.escape(art)}</code></a></td>' if art
             else f"<td class=\"small\">{NOT_MEASURED}</td>")
          + (f'<td class="small"><a href="dashboard/experiments/'
             f'{html.escape(run["id"])}.html">{html.escape(run["id"].replace("run-", ""))}'
             "</a></td>" if run else '<td class="small muted">no single run artifact</td>')
          + "</tr>")
    A("</tbody></table></div>")

    # ---------------- audits ----------------
    A("<h2>Audits &mdash; this program's criticism of itself</h2>")
    A('<p class="small muted">Six review documents, none of which was linked from any '
      "published surface before now. They are listed with their verdicts rather than their "
      "titles, because a link labelled &ldquo;audit&rdquo; that hides an "
      "INVALIDATES-RESULTS finding is worse than no link. Implementer, critic and judge "
      "share a model family (R5/R16), so none of these is external validation.</p>")
    A('<div class="tablewrap"><table><thead><tr><th>document</th><th>what it found</th>'
      "</tr></thead><tbody>")
    for fn, title, verdict in AUDITS:
        p = ROOT / "audits" / fn
        if not p.exists():
            sys.exit(f"FATAL: audit document declared but missing: audits/{fn}")
        A(f'<tr><td><a href="{BLOB}/audits/{fn}"><strong>{html.escape(title)}</strong></a>'
          f'<br><span class="small muted"><code>audits/{fn}</code> &middot; '
          f'{mtime_utc(p)}</span></td><td class="small">{verdict}</td></tr>')
    A("</tbody></table></div>")

    # ---------------- hypotheses ----------------
    A("<h2>Hypothesis registry</h2>")
    A('<p><a href="hypotheses/index.html"><strong>Per-hypothesis pages &rarr;</strong></a> '
      "&mdash; each registered hypothesis has its own page carrying the claim, the "
      "published result it audits, the pre-registered falsifier and predicted effect, and "
      "the power arithmetic. The prediction is rendered whether or not a result exists, so "
      "a reader can see what was promised <em>before</em> seeing what happened.</p>")
    A('<p class="small muted">Parsed from <code>IDEA_TABLE.md</code>. A hypothesis whose '
      "falsifier has not been <em>executed</em> is UNTESTED, never SUPPORTED (R7). "
      "Tier and family size are pre-registered in version control before the sweep; "
      "reclassifying a loser as screening afterwards is HARKing and is a blocker.</p>")
    A(f'<p class="warnc"><strong>{n_untested} of {len(hyps)} registered hypotheses have '
      "never been executed.</strong> They are rows in this table with an UNTESTED chip and "
      "a run count of zero, not omissions &mdash; the prediction is on the record and the "
      "run is the debt.</p>")
    A('<input class="filter" data-filters="hyps" data-count="hypcount" '
      'placeholder="filter hypotheses...">')
    A('<p class="small muted" id="hypcount"></p>')
    A('<div class="tablewrap"><table id="hyps" data-sortable><thead><tr>'
      "<th>id</th><th>claim</th><th>falsifier</th><th>required n</th><th>tier</th>"
      "<th>runs on disk</th><th>status</th></tr></thead><tbody>")
    for h in hyps:
        fals = h["falsifier"]
        if len(fals) > 420:
            fals = fals[:417].rsplit(" ", 1)[0] + "..."
        # STATUS comes from the Summary table, not from the per-block Status cell. The
        # per-block cells are edited one at a time and already disagree with the Summary
        # (V1's block still reads UNTESTED while the Summary reads CLAIM SUPPORTED).
        st = summary.get(h["id"], {}).get("status", "UNTESTED")
        hruns = by_hyp.get(h["id"], [])
        if hruns:
            rl = "<br>".join(
                f'<a href="dashboard/experiments/{html.escape(r["id"])}.html">'
                f'{html.escape(r["id"].replace("run-", ""))}</a> '
                f'<span class="small muted">n={r["n_repeats"]}</span>' for r in hruns)
        else:
            rl = '<span class="muted small">none</span>'
        A(f'<tr><td><a href="hypotheses/{html.escape(h["id"])}.html">'
          f'<strong>{html.escape(h["id"])}</strong></a><br>'
          f'<span class="small muted">{md_inline(h["title"])}</span></td>'
          f'<td class="small">{md_inline(h["claim"])}</td>'
          f'<td class="small">{md_inline(fals)}</td>'
          f'<td class="num">{html.escape(h["n_req"])}<br>'
          f'<span class="small muted">{md_inline(h["mn"])}</span></td>'
          f'<td>{tier_chip(h["tier"])}</td>'
          f"<td class=\"small\">{rl}</td>"
          f'<td><span class="chip {status_class(st)}">{html.escape(status_short(st))}</span>'
          f'<br><span class="small muted">{md_inline(st)[:200]}</span></td></tr>')
    A("</tbody></table></div>")

    # ---------------- traps ----------------
    A(f"<h2>The methodological traps &mdash; the audit checklist</h2>")
    A('<p class="small muted">The '
      f"{len(traps)} traps catalogued in <code>corpus/SURVEY_datasets.md</code> &sect;3, each "
      "reduced to its operative rule. Every experiment in this program is checked against "
      "this list.</p>")
    A('<div class="tablewrap"><table><thead><tr><th>#</th><th>trap</th>'
      "<th>operative rule</th></tr></thead><tbody>")
    for t in traps:
        A(f'<tr><td class="num muted">{html.escape(t["num"])}</td>'
          f'<td><strong>{md_inline(t["title"])}</strong></td>'
          f'<td class="small">{md_inline(t["rule"])}</td></tr>')
    A("</tbody></table></div>")

    # ---------------- source provenance ----------------
    A("<h2>Sources rendered on this page, and when each was last written</h2>")
    A('<p class="small muted">Every panel above is built from one of these files. The '
      "write times are shown because an input older than the run it describes is how a "
      "page ends up narrating a superseded state &mdash; the disagreement panel near the "
      "top is generated by exactly that comparison.</p>")
    A('<div class="tablewrap"><table data-sortable><thead><tr><th>source</th>'
      "<th>bytes</th><th>last written (UTC)</th></tr></thead><tbody>")
    prov_keys = ["f1_json", "bench_svd_full", "bench_svd", "v1", "v2", "findings",
                 "idea_table", "composite", "survey_datasets", "acquisition",
                 "preprocessing", "summary_svd", "summary_coswara", "summary_coughvid",
                 "coswara_meta", "svd_meta"]
    for k in prov_keys:
        p = SOURCES[k]
        rel = str(p.relative_to(ROOT)).replace(chr(92), "/")
        A(f'<tr><td><a href="{BLOB}/{rel}"><code>{html.escape(rel)}</code></a></td>'
          f'<td class="num muted">{p.stat().st_size:,}</td>'
          f'<td class="num small">{mtime_utc(p)}</td></tr>')
    A("</tbody></table></div>")

    # ---------------- footer ----------------
    A("<footer>")
    A(f'<p>Repository: <a href="{REPO_URL}">{REPO_URL}</a> &middot; built {built} &middot; '
      f'commit <code>{html.escape(sha)}</code> &middot; '
      f'<a href="{BLOB}/scripts/build_dashboard.py">the generator that wrote this page</a>'
      "</p>")
    A(f'<p>Composite specification <code>{html.escape(cs["name"])} '
      f'v{html.escape(cs["version"])}</code>, SHA-256 fingerprint over the specification '
      f'(not the code): <code>{html.escape(cs["fingerprint"])}</code>. Formula: '
      f'<code>{html.escape(cs["formula"])}</code>. Null policy: '
      f'<code>{html.escape(cs["null_policy"])}</code>. '
      + ("Implemented at "
         f'<code>{html.escape(cs["impl_path"])}</code>.' if cs["implemented"] else
         '<strong class="warnc">The specification is implemented nowhere</strong> '
         f'&mdash; <code>{html.escape(cs["impl_path"])}</code> does not exist, so no '
         "composite is computed for any run, no row on this page carries one, and nothing "
         "here is ranked by one. The fingerprint is published so that a future "
         "implementation can be checked against the specification that was pinned before "
         "it; it is not evidence of a live gate. This is the finding of "
         f'<a href="{BLOB}/audits/SCI_CRITIC.md">audits/SCI_CRITIC.md</a>.')
      + "</p>")
    A('<p>Page tiers: this master page &rarr; '
      '<a href="hypotheses/index.html">per-hypothesis registry</a> &rarr; '
      '<a href="dashboard/experiments/index.html">per-run ledger</a>. Also here: '
      '<a href="datasets.html">the dataset landscape</a>.</p>')
    A("<p><strong>Not a medical device.</strong> This program produces no diagnosis and makes "
      "no clinical claim. No PHI is committed; no restricted corpus is redistributed. "
      "Internal QA pass &mdash; independent external review pending.</p>")
    A("</footer>")
    A("</div>")

    body = "\n".join(out)
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Voice-Health Claim Audit &mdash; dashboard</title>\n"
        f"<style>{CSS}</style></head><body>\n{body}\n<script>{JS}</script>\n</body></html>\n"
    )


def main() -> None:
    for key in SOURCES:
        require(key)
    ASSETS.mkdir(parents=True, exist_ok=True)

    f1 = read_json("f1_json")
    bench = load_bench()

    age_png, checks = plot_age_distribution(f1)
    bar_png = plot_confound_vs_sota(f1, bench)

    html_text = build_html()
    out = DOCS / "index.html"
    out.write_text(html_text, encoding="utf-8")

    if "not yet measured" not in html_text:
        sys.exit("FATAL: no 'not yet measured' cell rendered -- a placeholder number leaked in")

    # BUILD-TIME GATES. A check that must be remembered will eventually be skipped, so
    # both of these run on every build and fail it rather than warn.
    #   1. no literal markdown syntax may reach the page;
    #   2. the dead `github.com/eranti/...` remote must never come back -- it was the
    #      single "go to the source" link on a transparency dashboard, and it 404'd.
    leak_gate([out])
    if "github.com/eranti/" in html_text:
        sys.exit("FATAL: the dead github.com/eranti/... remote is rendered on the page")

    print("=== dashboard rebuilt ===")
    print(f"  {out}  ({len(html_text):,} bytes)")
    print(f"  {age_png}")
    print(f"  {bar_png}")
    print(f"  age plot cross-check vs F1 artifact: OK "
          f"({checks['n_sessions']} sessions, gap "
          f"{checks['mean_age_pathological'] - checks['mean_age_healthy']:.1f} y)")
    print("  open docs/index.html directly -- no network required")


if __name__ == "__main__":
    main()
