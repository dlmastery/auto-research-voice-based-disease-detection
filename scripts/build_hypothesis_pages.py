"""build_hypothesis_pages.py -- the per-hypothesis dashboard tier.

The hierarchy is master -> per-hypothesis -> per-run. This file owns the middle tier:
one page per registered hypothesis (V1..Vn), each carrying the claim, the audited
claim it tests, the pre-registered falsifier and predicted delta, the power
arithmetic, and -- once a run exists -- the measured result rendered from its
artifact plus a link to the full per-run page.

The design rule that matters: a hypothesis page renders its PREDICTION whether or not
a result exists, and renders the result only from a file on disk. That ordering is
what makes the prediction falsifiable rather than decorative -- a reader can see what
was promised before seeing what happened, and an UNTESTED page is a visible debt
rather than a blank.

Two defects this file used to have, both fixed and both worth naming because they are
the same defect in different clothes:

* `ARTIFACTS` was a one-entry dict (`{"V2": ...}`) and the result branch was
  `if tested and h["id"] == "V2"`. Three executed hypotheses sat on disk while every
  page said UNTESTED. The build succeeded, the leak gate passed, and the page
  published the opposite of the truth. Artifact discovery now goes through the
  declared registry in `build_common`, which fails the build on an undeclared run.
* The registry status was read from each block's own `| **Status** |` cell, which is
  maintained by hand per block and is internally inconsistent. It is now read from
  the `## Summary` table, which the author maintains as a set.

Generated, never hand-edited. Reads `IDEA_TABLE.md` + `autoresearch_results/*.json`.

Usage:  python scripts/build_hypothesis_pages.py      # CPU, no network, seconds
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_common import (  # noqa: E402
    BLOB, DOCS, ROOT, built_stamp, composite_spec, esc, fatal, fmt, git_sha,
    idea_summary, leak_gate, load_runs, md_inline, runs_by_hypothesis, status_class,
    status_short, strip_md,
)
from build_experiment_pages import DETAIL  # noqa: E402

IDEAS = ROOT / "IDEA_TABLE.md"
OUT = DOCS / "hypotheses"

CSS = """<style>
:root{--bg:#0d1017;--panel:#12151b;--panel2:#171b24;--line:#232936;--fg:#e6e9ef;
--muted:#98a2b8;--accent:#7e9cff;--warn:#ffd166;--bad:#ff6b6b;--ok:#5ddba4;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1040px;margin:0 auto;padding:32px 20px 96px}
h1{font-size:28px;line-height:1.25;margin:0 0 6px;letter-spacing:-.02em}
h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
margin:48px 0 12px;font-weight:600;border-bottom:1px solid var(--line);padding-bottom:9px}
h3{font-size:16px;margin:0 0 8px}
p{margin:0 0 14px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{background:#1b2130;border:1px solid var(--line);border-radius:4px;padding:1px 5px;
font-size:.86em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;word-break:break-all}
pre{background:#0a0d13;border:1px solid var(--line);border-radius:8px;padding:13px 15px;
overflow-x:auto;font-size:12.5px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.sub{color:var(--muted);font-size:15px;margin:0 0 18px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:18px 22px;margin:14px 0}
.panel.debt{border-left:4px solid var(--warn)}
.panel.pred{border-left:4px solid var(--accent)}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.stat .n{font-size:27px;font-weight:650;letter-spacing:-.02em;line-height:1.15;
font-variant-numeric:tabular-nums}
.stat .k{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.1em;
margin-top:7px}
.stat .s{color:var(--muted);font-size:12.5px;margin-top:7px}
.meta{color:var(--muted);font-size:13px}.small{font-size:13px}.muted{color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--panel2);text-align:left;padding:11px 13px;font-size:12px;
letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
border-bottom:1px solid var(--line);white-space:nowrap;position:sticky;top:0;
cursor:pointer;user-select:none}
th:hover{color:var(--fg)}
th.sort-asc::after{content:" \\25B2";color:var(--accent)}
th.sort-desc::after{content:" \\25BC";color:var(--accent)}
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
.hit,.ok{color:var(--ok);font-weight:600}.miss,.bad{color:var(--bad);font-weight:600}
.warnc{color:var(--warn)}
.filter{width:100%;max-width:340px;background:var(--panel2);border:1px solid var(--line);
border-radius:8px;color:var(--fg);padding:9px 12px;font-size:14px;margin:0 0 12px}
.filter:focus{outline:none;border-color:var(--accent)}
footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);
color:var(--muted);font-size:13px}
@media (max-width:640px){.wrap{padding:22px 14px 72px}h1{font-size:22px}td,th{padding:9px 10px}}
</style>"""

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
    var t=document.getElementById(inp.dataset.filters),q=inp.value.toLowerCase(),n=0;
    Array.prototype.slice.call(t.tBodies[0].rows).forEach(function(r){
      var hit=r.innerText.toLowerCase().indexOf(q)>-1;
      r.style.display=hit?'':'none';if(hit)n++;
    });
    var c=document.getElementById(inp.dataset.count);
    if(c)c.textContent=n+' of '+t.tBodies[0].rows.length+' shown';
  });
});
"""


def md(s: str) -> str:
    return md_inline(s)


def tier_label(s: str) -> str:
    """The one-word tier for a chip. The registry's `tier` cell is prose for some
    hypotheses (V5 carries its whole promotion condition there), and a chip must hold a
    label, not a paragraph -- the full text is rendered separately, through md()."""
    for word in ("EVALUATION", "SCREENING"):
        if word in s.upper():
            return word
    return "?"


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
    if not out:
        fatal("parsed 0 hypotheses from IDEA_TABLE.md -- the format changed")
    return out


def result_card(r: dict) -> str:
    """The compact, tier-stamped summary of one run, above its full detail."""
    ci = ""
    if r.get("delta_ci"):
        lo, hi = r["delta_ci"][0], r["delta_ci"][1]
        ci = f' <span class="small muted">95% CI [{fmt(lo, 5)}, {fmt(hi, 5)}]</span>'
    cls = {"EVALUATION": "eval", "SCREENING": "screen", "CONTROL": "pend"}[r["tier"]]
    A = [f'<div class="panel"><h3><a href="../dashboard/experiments/{esc(r["id"])}.html">'
         f'{esc(r["title"])}</a></h3>',
         f'<p><span class="chip {cls}">{esc(r["tier"])}</span> '
         f'<span class="chip">{esc(r["verdict"])}</span> '
         f'<span class="chip">n = {r["n_repeats"]} &times; {r["n_folds"]} folds</span>'
         + (f' <span class="chip screen">SCOPE-LIMITED</span>' if r["scope"] else "") + "</p>",
         '<div class="grid">',
         f'<div class="stat"><div class="n">{fmt(r["headline"])}</div>'
         f'<div class="k">{esc(r["headline_label"])}</div></div>']
    bar = fmt(r["bar"]) if r.get("bar") is not None else esc(r.get("bar_text", "&mdash;"))
    A.append(f'<div class="stat"><div class="n">{bar}</div>'
             f'<div class="k">{esc(r["bar_label"])}</div></div>')
    if r.get("delta") is not None:
        A.append(f'<div class="stat"><div class="n">{r["delta"]:+.4f}</div>'
                 f'<div class="k">difference</div><div class="s">{ci}</div></div>')
    if r.get("n_speakers"):
        A.append(f'<div class="stat"><div class="n">{r["n_speakers"]:,}</div>'
                 f'<div class="k">speakers</div>'
                 f'<div class="s">'
                 + (f'{r["n_recordings"]:,} recordings' if r.get("n_recordings")
                    else "recording count not in artifact")
                 + "</div></div>")
    A.append("</div>")
    A.append(f'<p class="small muted">Artifact <code>autoresearch_results/'
             f'{esc(r["artifact"])}</code> &middot; written {esc(r["mtime"])} &middot; '
             f'<a href="../dashboard/experiments/{esc(r["id"])}.html">full run page &rarr;</a>'
             + (f' &middot; written up as {esc(r["finding"])} in '
                f'<a href="{BLOB}/FINDINGS.md">FINDINGS.md</a>' if r["finding"] else "")
             + "</p></div>")
    return "\n".join(A)


def build_page(h: dict, runs: list[dict], summary: dict) -> str:
    f = h["f"]
    s = summary.get(h["id"], {})
    reg_status = s.get("status", "UNTESTED")
    tested = bool(runs)
    primary = next((r for r in runs if r["tier"] != "CONTROL"), runs[0] if runs else None)

    chip = f'<span class="chip {status_class(reg_status)}">{esc(status_short(reg_status))}</span>'
    A = ['<!doctype html>\n<html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         f"<title>{esc(h['id'])} &mdash; {esc(h['title'])}</title>", CSS,
         '</head><body><div class="wrap">']
    add = A.append
    add('<p class="meta"><a href="../index.html">&larr; dashboard</a> &middot; '
        '<a href="index.html">all hypotheses</a> &middot; '
        '<a href="../dashboard/experiments/index.html">run ledger</a></p>')
    add(f"<h1>{esc(h['id'])} &mdash; {esc(h['title'])}</h1>")
    add(f'<p class="sub">{chip} '
        f'<span class="chip">registered {esc(tier_label(f.get("tier", "?")))}</span> '
        f'<span class="chip">axis {esc(f.get("axis moved", s.get("axis", "?")))}</span> '
        + (f'<span class="chip eval">{len(runs)} run(s) on disk</span>' if tested
           else '<span class="chip pend">no run</span>') + "</p>")

    add('<div class="panel pred"><p class="small muted">Everything in this block was '
        "recorded in version control <em>before</em> any run. It is rendered above the "
        "result on purpose: a prediction a reader meets after the number it predicted is "
        "not a prediction.</p>")
    for key, label in (("claim", "The claim"),
                       ("audited claim", "The published claim it audits"),
                       ("falsifier", "Pre-registered falsifier"),
                       ("predicted δ", "Predicted effect (recorded before the run)"),
                       ("predicted delta", "Predicted effect (recorded before the run)")):
        if key in f:
            add(f"<h3>{label}</h3><p>{md(f[key])}</p>")
    add("</div>")

    add("<h2>Power and scope</h2>")
    add('<div class="tablewrap"><table><tbody>')
    for key, label in (("tier", "tier (as registered)"),
                       ("m / n", "family size m / seeds n"), ("datasets", "datasets"),
                       ("cost", "cost")):
        if key in f:
            add(f'<tr><td class="muted">{label}</td><td>{md(f[key])}</td></tr>')
    if s:
        add(f'<tr><td class="muted">min attainable paired p</td>'
            f'<td class="num">{esc(s["min_p"])}</td></tr>')
        add(f'<tr><td class="muted">Holm-tightest threshold 0.05/m</td>'
            f'<td class="num">{esc(s["holm"])}</td></tr>')
        add(f'<tr><td class="muted">arithmetically satisfiable under R6</td>'
            f'<td>{esc(s["satisfiable"])}</td></tr>')
        add(f'<tr><td class="muted">registry status</td><td>{md(s["status_md"])}</td></tr>')
    add("</tbody></table></div>")
    add('<p class="small muted">Registry status is read from the <code>## Summary</code> '
        "table of <code>IDEA_TABLE.md</code>, which the author maintains as a set. The "
        "per-block status cells are maintained one at a time and disagree with it; one "
        "source of truth, and this is it.</p>")

    add("<h2>Measured result</h2>")
    if not tested:
        add('<div class="panel debt"><p><span class="chip pend">UNTESTED</span> No artifact '
            "exists for this hypothesis. Under R7 a hypothesis whose falsifier has not been "
            "<em>executed</em> is UNTESTED and is never reported as supported. This page "
            "exists so that the prediction above is on the record <em>before</em> any result "
            "is, and so the debt is visible rather than absent. It is counted as debt on the "
            '<a href="../index.html">master dashboard</a> and in the '
            '<a href="index.html">registry table</a>.</p></div>')
    else:
        if primary:
            n = primary["n_repeats"]
            m = (f.get("m / n") or "").strip()
            if primary["tier"] == "SCREENING":
                add(f'<div class="panel debt"><p><span class="chip screen">SCREENING</span> '
                    f"The artifact behind this page has <strong>n = {n}</strong> repeats. "
                    "Under R6 that cannot reach the Holm-corrected threshold for this "
                    f"hypothesis&rsquo; pre-registered family ({md(m) if m else 'see above'}), "
                    "so nothing below may be reported as a result, a win, or a null. It is "
                    "shown because a visible screening number is more honest than a blank "
                    "page.</p></div>")
            else:
                add(f'<div class="panel"><p><span class="chip eval">EVALUATION</span> '
                    f"n = {n} repeats against the pre-registered family "
                    f"({md(m) if m else 'see above'}): min attainable paired "
                    f"p = {2 / 2 ** n:.6f}"
                    + (f' &le; Holm 0.05/m = {esc(s["holm"])}' if s else "")
                    + ". Feasible. Feasibility is a property of the design, not of the "
                    "result &mdash; it says what this run could have shown.</p></div>")
        for r in runs:
            add(result_card(r))
        add("<h2>Full detail from the primary artifact</h2>")
        add('<p class="small muted">Rendered from '
            f'<code>autoresearch_results/{esc(primary["artifact"])}</code>. Every other run '
            "for this hypothesis, including controls, has its own page linked above.</p>")
        add(DETAIL[primary["id"]](primary["raw"]))

    add("<footer><p>Generated by <code>scripts/build_hypothesis_pages.py</code> from "
        "<code>IDEA_TABLE.md</code> and the declared artifacts in "
        "<code>autoresearch_results/</code>. Never hand-edited.</p>"
        f'<p>Built {built_stamp()} &middot; commit <code>{esc(git_sha())}</code></p>'
        "<p><strong>Not a medical device.</strong> Internal QA pass &mdash; independent "
        "external review pending.</p></footer></div>"
        f"<script>{JS}</script></body></html>")
    return "\n".join(A)


def build_index(hyps: list[dict], by_hyp: dict, summary: dict) -> str:
    n_untested = sum(1 for h in hyps if not by_hyp.get(h["id"]))
    n_with_runs = len(hyps) - n_untested
    n_eval = sum(1 for h in hyps
                 if any(r["tier"] == "EVALUATION" for r in by_hyp.get(h["id"], [])))
    cs = composite_spec()

    A = ['<!doctype html>\n<html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>Hypothesis registry</title>", CSS,
         '</head><body><div class="wrap">',
         '<p class="meta"><a href="../index.html">&larr; dashboard</a> &middot; '
         '<a href="../dashboard/experiments/index.html">run ledger</a></p>',
         "<h1>Hypothesis registry</h1>",
         f'<p class="sub"><strong>{len(hyps)}</strong> registered &middot; '
         f'<strong>{n_with_runs}</strong> with at least one run on disk '
         f'(<strong>{n_eval}</strong> reaching EVALUATION tier) &middot; '
         f'<strong class="warnc">{n_untested} never executed</strong>. '
         "A hypothesis whose falsifier has not been executed is never reported as "
         "supported, and is counted here as debt rather than omitted.</p>",
         '<div class="grid">',
         f'<div class="stat"><div class="n">{len(hyps)}</div><div class="k">registered</div>'
         '<div class="s">pre-registered in version control before any sweep</div></div>',
         f'<div class="stat"><div class="n">{n_eval}</div><div class="k">at EVALUATION tier'
         '</div><div class="s">n &ge; 8 repeats against a pre-registered family</div></div>',
         f'<div class="stat"><div class="n warnc">{n_untested}</div>'
         '<div class="k">never executed</div>'
         '<div class="s">visible debt: the prediction is on the record, the run is not</div>'
         "</div>",
         "</div>",
         '<input class="filter" data-filters="hyps" data-count="hypcount" '
         'placeholder="filter hypotheses...">',
         '<p class="small muted" id="hypcount"></p>',
         '<div class="tablewrap"><table id="hyps" data-sortable><thead><tr><th>id</th>'
         "<th>claim</th><th>tier</th><th>m / n</th><th>runs</th><th>status</th>"
         "</tr></thead><tbody>"]
    for h in hyps:
        f = h["f"]
        s = summary.get(h["id"], {})
        runs = by_hyp.get(h["id"], [])
        st = s.get("status", "UNTESTED")
        chip = f'<span class="chip {status_class(st)}">{esc(status_short(st))}</span>'
        if runs:
            links = "<br>".join(
                f'<a href="../dashboard/experiments/{esc(r["id"])}.html">'
                f'{esc(r["id"].replace("run-", ""))}</a> '
                f'<span class="small muted">n={r["n_repeats"]}</span>' for r in runs)
        else:
            links = '<span class="muted small">none</span>'
        claim = md(f.get("claim", ""))
        A.append(f'<tr><td><a href="{h["id"]}.html"><strong>{esc(h["id"])}</strong></a><br>'
                 f'<span class="small muted">{esc(h["title"])[:70]}</span></td>'
                 f'<td class="small">{claim[:400]}</td>'
                 f'<td class="small">{esc(tier_label(f.get("tier", s.get("tier", "?"))))}</td>'
                 f'<td class="small num">{md(f.get("m / n", "?"))}</td>'
                 f'<td class="small">{links}</td>'
                 f"<td>{chip}</td></tr>")
    A += ["</tbody></table></div>",
          '<p class="small muted">Click a column header to sort; type to filter. Status is '
          "read from the <code>## Summary</code> table of <code>IDEA_TABLE.md</code>; runs "
          "are the artifacts declared in <code>scripts/build_common.py</code>, so a "
          "completed run that no generator knows about fails the build rather than "
          "disappearing from this column.</p>",
          f'<footer><p>Generated {built_stamp()} from <code>IDEA_TABLE.md</code> &middot; '
          f'commit <code>{esc(git_sha())}</code></p>'
          f'<p>Composite spec <code>{esc(cs["name"])} v{esc(cs["version"])}</code> '
          f'fingerprint <code>{esc(cs["fingerprint"])}</code> &mdash; '
          + ("implemented" if cs["implemented"] else
             f'<strong class="warnc">NOT implemented</strong> (<code>{esc(cs["impl_path"])}</code> '
             "does not exist), so no composite score is computed or shown anywhere in this "
             "repository")
          + ".</p>"
          "<p><strong>Not a medical device.</strong> Internal QA pass &mdash; independent "
          "external review pending.</p></footer></div>"
          f"<script>{JS}</script></body></html>"]
    return "\n".join(A)


def main() -> None:
    if not IDEAS.exists():
        fatal(f"{IDEAS} missing")
    hyps = parse_hypotheses()
    summary = idea_summary()

    unknown = [h["id"] for h in hyps if h["id"] not in summary]
    if unknown:
        fatal("hypothesis block(s) with no row in the IDEA_TABLE.md Summary table: "
              + ", ".join(unknown) + "\nThe Summary table is the status source of truth; "
              "a block missing from it would render with an invented status.")

    by_hyp = runs_by_hypothesis(load_runs())
    orphan = sorted(set(by_hyp) - {h["id"] for h in hyps})
    if orphan:
        fatal("run artifact(s) claim a hypothesis that IDEA_TABLE.md does not register: "
              + ", ".join(orphan))

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for h in hyps:
        p = OUT / f'{h["id"]}.html'
        p.write_text(build_page(h, by_hyp.get(h["id"], []), summary), encoding="utf-8")
        written.append(p)
    idx = OUT / "index.html"
    idx.write_text(build_index(hyps, by_hyp, summary), encoding="utf-8")
    written.append(idx)

    n = leak_gate(written)
    n_untested = sum(1 for h in hyps if not by_hyp.get(h["id"]))
    print("=== hypothesis pages built ===")
    print(f"  {OUT}")
    print(f"  {len(hyps)} hypotheses, {len(hyps) - n_untested} with runs on disk, "
          f"{n_untested} UNTESTED (rendered as debt)")
    for h in hyps:
        rs = by_hyp.get(h["id"], [])
        print(f"    {h['id']}  {status_short(summary[h['id']]['status']):<16} "
              f"{len(rs)} run(s): {', '.join(r['id'] for r in rs) or '-'}")
    print(f"  markdown-leak gate: clean across {n} pages")


if __name__ == "__main__":
    main()
