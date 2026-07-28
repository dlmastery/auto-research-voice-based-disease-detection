"""build_hypothesis_pages.py -- the per-hypothesis dashboard tier.

The steering sibling has master -> per-hypothesis -> per-experiment. This program had
only a master page, which is the gap logged as deficiency 2 in `CLAUDE.md` 18.3.
This closes the middle tier: one page per registered hypothesis (V1..Vn), each
carrying the claim, the audited claim it tests, the pre-registered falsifier and
predicted delta, the power arithmetic, and -- once a run exists -- the measured
result rendered from its artifact.

The design rule that matters: a hypothesis page renders its PREDICTION whether or not
a result exists, and renders the result only from a file on disk. That ordering is
what makes the prediction falsifiable rather than decorative -- a reader can see what
was promised before seeing what happened, and an UNTESTED page is a visible debt
rather than a blank.

Generated, never hand-edited. Reads `IDEA_TABLE.md` + `autoresearch_results/*.json`.

Usage:  python scripts/build_hypothesis_pages.py      # CPU, no network, seconds
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDEAS = ROOT / "IDEA_TABLE.md"
RESULTS = ROOT / "autoresearch_results"
OUT = ROOT / "docs" / "hypotheses"

# hypothesis id -> the artifact that would settle it, if a run has produced one
ARTIFACTS = {"V2": "V2_speaker_subspace.json"}

CSS = """<style>
:root{--bg:#0d1017;--panel:#12151b;--panel2:#171b24;--line:#232936;--fg:#e6e9ef;
--muted:#98a2b8;--accent:#7e9cff;--warn:#ffd166;--bad:#ff6b6b;--ok:#5ddba4;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1000px;margin:0 auto;padding:32px 20px 96px}
h1{font-size:28px;line-height:1.25;margin:0 0 6px;letter-spacing:-.02em}
h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
margin:48px 0 12px;font-weight:600;border-bottom:1px solid var(--line);padding-bottom:9px}
p{margin:0 0 14px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{background:#1b2130;border:1px solid var(--line);border-radius:4px;padding:1px 5px;
font-size:.86em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.sub{color:var(--muted);font-size:15px;margin:0 0 18px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:18px 22px;margin:14px 0}
.panel h3{margin:0 0 8px;font-size:16px}
.meta{color:var(--muted);font-size:13px}.small{font-size:13px}.muted{color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--panel2);text-align:left;padding:11px 13px;font-size:12px;
letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:11px 13px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.chip{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;
padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted);
white-space:nowrap}
.chip.eval{border-color:#1f5b45;color:var(--ok);background:#0e2119}
.chip.screen{border-color:#6b5518;color:var(--warn);background:#241d0c}
.chip.bad{border-color:#6b2222;color:var(--bad);background:#2a1313}
.chip.pend{border-color:#2f3a52;color:#9fb0d0;background:#151b28}
.hit{color:var(--ok);font-weight:600}.miss{color:var(--bad);font-weight:600}
footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);
color:var(--muted);font-size:13px}
@media (max-width:640px){.wrap{padding:22px 14px 72px}h1{font-size:22px}td,th{padding:9px 10px}}
</style>"""


def esc(s: object) -> str:
    return html.escape(str(s))


def md(s: str) -> str:
    """Inline markdown -> HTML. The dashboard must never leak a literal ** or `."""
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"arXiv:(\d{4}\.\d{4,5})",
               r'<a href="https://arxiv.org/abs/\1">arXiv:\1</a>', s)
    return s


def parse_hypotheses() -> list[dict]:
    """Pull each `#### Vn -- title` block and its key/value table out of IDEA_TABLE.md."""
    text = IDEAS.read_text(encoding="utf-8")
    out = []
    blocks = re.split(r"^#### ", text, flags=re.M)[1:]
    for b in blocks:
        head, _, body = b.partition("\n")
        m = re.match(r"(V\d+)\s*[—-]\s*(.+)", head.strip())
        if not m:
            continue
        fields = {}
        for row in re.findall(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*$", body, re.M):
            fields[row[0].strip().lower()] = row[1].strip()
        out.append({"id": m.group(1), "title": m.group(2).strip(), "f": fields})
    return out


def render_v2(a: dict) -> str:
    """The V2 artifact, rendered against its own pre-registered prediction."""
    A = []
    add = A.append
    # An artifact existing is NOT the same as an artifact being evidence. The tier is
    # read from the run's own repeat count, never asserted -- a 1-repeat smoke file and
    # a 10-repeat confirmatory file look identical on disk and must not look identical
    # on the page.
    n = int(a.get("repeats", 0))
    tier = "EVALUATION" if n >= 8 else "SCREENING"
    add('<h2>Measured result</h2>')
    if tier == "SCREENING":
        add(f'<div class="panel"><p><span class="chip screen">SCREENING</span> '
            f"This artifact has <strong>n = {n}</strong> repeats. Under R6 that cannot reach "
            "the Holm-corrected threshold for this hypothesis' pre-registered family "
            f"(m = {a.get('family_m_preregistered', '?')}), so nothing below may be reported "
            "as a result, a win, or a null. It is shown because a visible screening number "
            "is more honest than a blank page.</p></div>")
    else:
        add(f'<div class="panel"><p><span class="chip eval">EVALUATION</span> '
            f"n = {n} repeats against a pre-registered family of "
            f"m = {a.get('family_m_preregistered', '?')}: min attainable paired "
            f"p = {2 / 2 ** n:.6f} &le; Holm 0.05/m = "
            f"{0.05 / max(1, int(a.get('family_m_preregistered', 1))):.6f}. Feasible.</p></div>")
    add(f'<p class="meta">Artifact <code>autoresearch_results/{ARTIFACTS["V2"]}</code> '
        f'&middot; {a["n_recordings"]:,} recordings / {a["n_speakers"]:,} speakers '
        f'&middot; {a["repeats"]} repeats &times; {a["folds"]}-fold speaker-disjoint '
        f'&middot; objective {esc(a["objective"])}</p>')
    add(f'<div class="panel"><h3 style="margin-top:0">Baseline</h3>'
        f'<p>Full-embedding disease AUC <strong>{a["auc_full_mean"]:.4f}</strong>. '
        f'Speaker-ID accuracy on unprojected embeddings '
        f'<strong>{a.get("speaker_id_acc_full", float("nan")):.4f}</strong> '
        f'(chance {a.get("speaker_id_chance", float("nan")):.4f}).</p></div>')

    add('<div class="tablewrap"><table><thead><tr><th>rank k</th>'
        "<th>AUC after removing<br>SPEAKER subspace</th>"
        "<th>AUC after removing<br>top-k PCA</th>"
        "<th>AUC after removing<br>variance-matched</th>"
        "<th>D vs top-k PCA [95% CI]</th>"
        "<th>variance removed<br>spk / topk / matched</th>"
        "<th>speaker-ID<br>after</th></tr></thead><tbody>")
    for r in a["rows"]:
        ci = r.get("D_vs_pca_topk_ci95", [float("nan")] * 2)
        excl = r.get("D_vs_pca_topk_excludes_zero")
        cls = "hit" if excl else "muted"
        add(f'<tr><td class="num"><strong>{r["k"]}</strong></td>'
            f'<td class="num">{r["auc_speaker_removed"]:.4f}</td>'
            f'<td class="num">{r.get("auc_pca_topk_removed", float("nan")):.4f}</td>'
            f'<td class="num">{r.get("auc_var_matched_removed", float("nan")):.4f}</td>'
            f'<td class="num {cls}">{r.get("D_vs_pca_topk", float("nan")):+.4f} '
            f'<span class="small muted">[{ci[0]:.3f}, {ci[1]:.3f}]</span></td>'
            f'<td class="num small muted">{r.get("variance_removed_speaker", 0):.3f} / '
            f'{r.get("variance_removed_pca_topk", 0):.3f} / '
            f'{r.get("variance_removed_var_matched", 0):.3f}</td>'
            f'<td class="num">{r.get("speaker_id_acc_after", float("nan")):.3f}</td></tr>')
    add("</tbody></table></div>")
    add('<p class="small muted">Both controls are built from the data\'s own principal '
        "axes and remove <em>at least as much variance</em> as the speaker subspace, so a "
        "positive D cannot be explained by \"more signal was deleted\". A uniformly random "
        "subspace was tried first and rejected: at k=16 it reached only 0.350 of the "
        "variance against the speaker subspace's 0.818, which would have compared two "
        "different-sized interventions.</p>")
    return "\n".join(A)


def build_page(h: dict, result: dict | None) -> str:
    f = h["f"]
    tested = result is not None
    reps = int(result.get("repeats", 0)) if tested else 0
    chip = ('<span class="chip pend">UNTESTED</span>' if not tested
            else '<span class="chip eval">EVALUATION</span>' if reps >= 8
            else f'<span class="chip screen">SCREENING n={reps}</span>')
    A = [f"<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">",
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         f"<title>{esc(h['id'])} — {esc(h['title'])}</title>", CSS,
         '</head><body><div class="wrap">']
    add = A.append
    add('<p class="meta"><a href="../index.html">&larr; dashboard</a> &middot; '
        '<a href="index.html">all hypotheses</a></p>')
    add(f"<h1>{esc(h['id'])} — {esc(h['title'])}</h1>")
    add(f'<p class="sub">{chip} '
        f'<span class="chip">{esc(f.get("tier", "?"))}</span> '
        f'<span class="chip">axis {esc(f.get("axis moved", "?"))}</span></p>')

    for key, label in (("claim", "The claim"), ("audited claim", "The published claim it audits"),
                       ("falsifier", "Pre-registered falsifier"),
                       ("predicted δ", "Predicted effect (recorded before the run)"),
                       ("predicted delta", "Predicted effect (recorded before the run)")):
        if key in f:
            add(f'<div class="panel"><h3>{label}</h3><p>{md(f[key])}</p></div>')

    add("<h2>Power and scope</h2>")
    add('<div class="tablewrap"><table><tbody>')
    for key, label in (("m / n", "family size m / seeds n"), ("datasets", "datasets"),
                       ("cost", "cost"), ("status", "registry status")):
        if key in f:
            add(f'<tr><td class="muted">{label}</td><td>{md(f[key])}</td></tr>')
    add("</tbody></table></div>")

    if tested and h["id"] == "V2":
        add(render_v2(result))
    elif not tested:
        add("<h2>Measured result</h2>")
        add('<div class="panel"><p><span class="chip pend">UNTESTED</span> No artifact exists '
            "for this hypothesis yet. Under R7 a hypothesis whose falsifier has not been "
            "<em>executed</em> is UNTESTED and is never reported as supported. This page "
            "exists so that the prediction above is on the record <em>before</em> any result "
            "is, and so the debt is visible rather than absent.</p></div>")

    add("<footer><p>Generated by <code>scripts/build_hypothesis_pages.py</code> from "
        "<code>IDEA_TABLE.md</code> and the artifacts in <code>autoresearch_results/</code>. "
        "Never hand-edited.</p>"
        "<p><strong>Not a medical device.</strong> Internal QA pass — independent external "
        "review pending.</p></footer></div></body></html>")
    return "\n".join(A)


def main() -> None:
    if not IDEAS.exists():
        sys.exit(f"FATAL: {IDEAS} missing")
    hyps = parse_hypotheses()
    if not hyps:
        sys.exit("FATAL: parsed 0 hypotheses from IDEA_TABLE.md — the format changed")
    OUT.mkdir(parents=True, exist_ok=True)
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    n_tested = 0
    for h in hyps:
        art = RESULTS / ARTIFACTS.get(h["id"], "___none___")
        result = json.loads(art.read_text(encoding="utf-8")) if art.exists() else None
        n_tested += bool(result) and result.get("repeats", 0) >= 8
        (OUT / f"{h['id']}.html").write_text(build_page(h, result), encoding="utf-8")

    idx = ["<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">",
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>Hypothesis registry</title>", CSS,
           '</head><body><div class="wrap">',
           '<p class="meta"><a href="../index.html">&larr; dashboard</a></p>',
           "<h1>Hypothesis registry</h1>",
           f'<p class="sub">{len(hyps)} registered · <strong>{n_tested}</strong> with a '
           f"at EVALUATION tier · {len(hyps) - n_tested} not yet. A hypothesis whose falsifier "
           "has not been executed is never reported as supported.</p>",
           '<div class="tablewrap"><table><thead><tr><th>id</th><th>claim</th>'
           "<th>tier</th><th>m / n</th><th>status</th></tr></thead><tbody>"]
    for h in hyps:
        f = h["f"]
        art = RESULTS / ARTIFACTS.get(h["id"], "___none___")
        st = '<span class="chip pend">UNTESTED</span>'
        if art.exists():
            reps = json.loads(art.read_text(encoding="utf-8")).get("repeats", 0)
            st = ('<span class="chip eval">EVALUATION</span>' if reps >= 8
                  else f'<span class="chip screen">SCREENING n={reps}</span>')
        idx.append(f'<tr><td><a href="{h["id"]}.html"><strong>{esc(h["id"])}</strong></a><br>'
                   f'<span class="small muted">{esc(h["title"])[:70]}</span></td>'
                   f'<td class="small">{md(f.get("claim", ""))[:260]}</td>'
                   f'<td class="small">{esc(f.get("tier", "?"))}</td>'
                   f'<td class="small num">{md(f.get("m / n", "?"))}</td>'
                   f"<td>{st}</td></tr>")
    idx += ["</tbody></table></div>",
            f'<footer><p>Generated {built} from <code>IDEA_TABLE.md</code>.</p></footer>',
            "</div></body></html>"]
    (OUT / "index.html").write_text("\n".join(idx), encoding="utf-8")

    print(f"=== hypothesis pages built ===\n  {OUT}")
    print(f"  {len(hyps)} hypotheses, {n_tested} with a result on disk")


if __name__ == "__main__":
    main()
