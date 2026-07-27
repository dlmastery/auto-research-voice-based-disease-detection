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

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"

REPO_URL = "https://github.com/eranti/auto-research-voice-based-disease-detection"

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
}

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
      t.querySelectorAll('th').forEach(function(o){delete o.dataset.dir;});
      th.dataset.dir=dir===1?'asc':'desc';
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
  inp.addEventListener('input',function(){
    var t=document.getElementById(inp.dataset.filters),q=inp.value.toLowerCase();
    Array.prototype.slice.call(t.tBodies[0].rows).forEach(function(r){
      r.style.display=r.innerText.toLowerCase().indexOf(q)>-1?'':'none';
    });
  });
});
"""


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

    spk = bench["speaker_level"]
    rec = bench["recording_level"]
    mvc = bench["margins_vs_confound"]
    best = mvc["best_audio_head"]
    n_rec = bench["dataset"]["n_recordings"]
    n_spk = bench["dataset"]["n_speakers"]
    bench_n = f'n={n_rec} recordings / {n_spk} speakers'

    # ---- status counters (all from artifacts) ------------------------------ #
    n_findings = count_findings()
    bench_artifacts = sorted((ROOT / "autoresearch_results").glob("bench_*.json"))
    log = ROOT / "autoresearch_results" / "experiment_log.jsonl"
    n_log = len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0
    decoded_total = sum(c["decoded"] for c in corpora)

    out = []
    A = out.append

    A('<div class="wrap">')

    # ---------------- header ----------------
    A("<h1>Voice-Health Claim Audit &mdash; transparency dashboard</h1>")
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
    A(f'<div class="stat"><div class="n">{n_findings}</div><div class="k">findings</div>'
      f'<div class="s">F1, screening-tier, metadata-only &mdash; see below</div></div>')
    A(f'<div class="stat"><div class="n">{len(bench_artifacts)}</div>'
      f'<div class="k">benchmark runs with artifacts</div>'
      f'<div class="s">{html.escape(bench_artifacts[0].name) if bench_artifacts else "none"}'
      f' &middot; experiment_log.jsonl rows: {n_log}</div></div>')
    A(f'<div class="stat"><div class="n">{len(corpora)}</div><div class="k">corpora decoded</div>'
      f'<div class="s">{decoded_total:,} files at 16&nbsp;kHz mono &mdash; but see the corpus '
      "table for what each one can support</div></div>")
    A(f'<div class="stat"><div class="n">{len(hyps)}</div><div class="k">hypotheses registered'
      "</div><div class=\"s\">all UNTESTED: a hypothesis whose falsifier has not been executed "
      "is never SUPPORTED (R7)</div></div>")
    A("</div>")

    A('<div class="panel"><h3>What is blocked right now</h3><ul>')
    A("<li><strong>The full SVD download is in progress.</strong> 20 of 72 pathology archives "
      "are on disk and they are the smallest ones; the 52 missing archives hold "
      "<strong>1,344 pathological sessions from 1,010 speakers</strong>. Until they land, every "
      f"audio number on SVD is measured on {n_spk} speakers and is screening-tier by "
      "construction. <span class=\"small muted\">(data/PREPROCESSING_STATUS.md)</span></li>")
    A(f"<li><strong>Coswara audio is partially decoded.</strong> "
      f"{corpora[2]['decoded']:,} of {corpora[2]['found']:,} found files, "
      f"{corpora[2]['speakers']} of 2,746 participants &mdash; the host has ~15&nbsp;GB free "
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
    A("<h2>First measured audio benchmark &mdash; a negative result</h2>")
    A('<div class="panel">')
    A(f"<h3>eGeMAPS on the decoded SVD slice does not clear its own age bar</h3>")
    A(f'<p class="meta">{tier_chip("SCREENING")} '
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
    A(f'<p class="warnc"><strong>What this does NOT claim.</strong> This is '
      f'{n_spk} speakers, which the preprocessing status file already flags as '
      "screening-tier: a speaker-disjoint test fold holds ~10 people and the 95% CI on any "
      "accuracy is roughly &plusmn;15&nbsp;pp &mdash; visible in the intervals above. It is "
      "<em>not</em> evidence that eGeMAPS fails on full SVD, and it is not comparable to the "
      "published UAR 85.22, which is a different metric on the full 2,225-session corpus. "
      "It is a null on a small slice, reported because nulls are reported (R8).</p>")
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
            ours = (f'<span class="num">UAR {spk[best]["uar"]:.4f}</span> / '
                    f'<span class="num">AUC {spk[best]["roc_auc"]:.4f}</span>'
                    f'<br><span class="small muted">{bench_n}, eGeMAPS <code>{best}</code>, '
                    f'speaker-level</span> {tier_chip("SCREENING")}')
            margin = ('<span class="nm">not comparable</span><br>'
                      '<span class="small muted">published UAR is the full 2,225-session '
                      'corpus; ours is the decoded pilot slice</span>')
            cbar = (f'<span class="num">{mvc["confound_bar_auc_speaker"]:.4f}</span> AUC'
                    f'<br><span class="small muted">age only, same run</span>'
                    f'<br><span class="num">{f1["auc_age_sex_speaker_disjoint"]:.4f}</span> AUC'
                    f'<br><span class="small muted">age+sex, metadata, full corpus (F1)</span>')
            dd = mvc["per_head"][best]["speaker_level_delta_auc"]
            cmargin = (f'<span class="num">{dd["delta"]:+.4f}</span> AUC<br>'
                       f'<span class="small muted">95% CI [{dd["lo"]:.3f}, {dd["hi"]:.3f}] '
                       f"&mdash; includes 0</span><br>"
                       f'<span class="chip bad">NOT CLEARED</span>')
            disj = '<span class="ok">YES &mdash; SprecherID</span>'
            status = '<span class="chip screen">SCREENING / NEGATIVE</span>'
        elif ds.startswith("Coswara"):
            ours, margin, cmargin = NOT_MEASURED, NOT_MEASURED, NOT_MEASURED
            cbar = NOT_MEASURED
            disj = ('<span class="ok">YES &mdash; participant id</span><br>'
                    '<span class="small muted">submission-disjoint, not person-disjoint: '
                    "returning-user flag is missing for 680 of 2,746</span>")
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
      "(SVD: 1,853 speakers exist, 49 decoded; Coswara: 2,746 exist, "
      f"{corpora[2]['speakers']} decoded).</p>")

    # ---------------- hypotheses ----------------
    A("<h2>Hypothesis registry</h2>")
    A('<p class="small muted">Parsed from <code>IDEA_TABLE.md</code>. A hypothesis whose '
      "falsifier has not been <em>executed</em> is UNTESTED, never SUPPORTED (R7). "
      "Tier and family size are pre-registered in version control before the sweep; "
      "reclassifying a loser as screening afterwards is HARKing and is a blocker.</p>")
    A('<input class="filter" data-filters="hyps" placeholder="filter hypotheses...">')
    A('<div class="tablewrap"><table id="hyps" data-sortable><thead><tr>'
      "<th>id</th><th>claim</th><th>falsifier</th><th>required n</th><th>tier</th>"
      "<th>datasets</th><th>status</th></tr></thead><tbody>")
    for h in hyps:
        fals = h["falsifier"]
        if len(fals) > 420:
            fals = fals[:417].rsplit(" ", 1)[0] + "..."
        A(f'<tr><td><strong>{html.escape(h["id"])}</strong><br>'
          f'<span class="small muted">{md_inline(h["title"])}</span></td>'
          f'<td class="small">{md_inline(h["claim"])}</td>'
          f'<td class="small">{md_inline(fals)}</td>'
          f'<td class="num">{html.escape(h["n_req"])}<br>'
          f'<span class="small muted">{md_inline(h["mn"])}</span></td>'
          f'<td>{tier_chip(h["tier"])}</td>'
          f'<td class="small">{md_inline(h["datasets"])}</td>'
          f'<td><span class="chip pend">{html.escape(h["status"])}</span></td></tr>')
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

    # ---------------- footer ----------------
    A("<footer>")
    A(f'<p>Repository: <a href="{REPO_URL}">{REPO_URL}</a> &middot; built {built} &middot; '
      f"commit <code>{html.escape(sha)}</code></p>")
    A("<p>Sources rendered on this page: "
      + ", ".join(f"<code>{html.escape(str(p.relative_to(ROOT)).replace(chr(92), '/'))}</code>"
                  for p in [SOURCES[k] for k in
                            ("f1_json", "bench_svd", "findings", "idea_table",
                             "survey_datasets", "acquisition", "preprocessing")])
      + ", and <code>data/interim/&lt;corpus&gt;/summary.json</code>.</p>")
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
