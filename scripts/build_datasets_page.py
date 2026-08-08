"""build_datasets_page.py -- render the voice-health dataset landscape.

Reads `corpus/datasets.json` (the single source) and writes `docs/datasets.html`.
The page is GENERATED, never hand-edited, so nothing on it can drift from the
registry (CLAUDE.md R1/R2: no orphan numbers).

What makes this page different from the published surveys it draws on: a
`claim` column stating what each corpus can actually support under a rigor
contract -- EVALUATION / SCREENING / BLOCKED / NEVER. A survey tells you a
dataset exists; this tells you whether a result on it would mean anything.

Usage:  python scripts/build_datasets_page.py      # CPU, no network, seconds
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_common import BLOB, git_sha, leak_gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "corpus" / "datasets.json"
OUT = ROOT / "docs" / "datasets.html"

# claim tier -> (css chip class, one-line meaning shown in the legend)
CLAIM = {
    "EVALUATION": ("eval", "real speaker ids and enough of them to carry an external claim"),
    "SCREENING": ("screen", "speaker-disjoint is possible, but n is too small to claim from"),
    "BLOCKED": ("pend", "obtainable in principle -- paperwork, gate or DUA, not compute"),
    "NEVER": ("bad", "a structural defect means it may never carry a generalisation claim"),
}
ACCESS = {"open": "open", "request": "on request", "dua": "DUA", "gated": "gated",
          "closed": "not released"}


def esc(s: object) -> str:
    return html.escape(str(s))


def linkify(s: str) -> str:
    """arXiv:XXXX.XXXXX -> a real link. Ids are verified before they enter the registry."""
    import re
    return re.sub(r"arXiv:(\d{4}\.\d{4,5})",
                  r'<a href="https://arxiv.org/abs/\1">arXiv:\1</a>', esc(s))


def main() -> None:
    if not SRC.exists():
        sys.exit(f"FATAL: registry missing: {SRC}")
    reg = json.loads(SRC.read_text(encoding="utf-8"))
    fams = reg["families"]
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    n_ds = sum(len(f["datasets"]) for f in fams)
    n_new = sum(1 for f in fams for d in f["datasets"] if d.get("new"))
    tally: dict[str, int] = {}
    for f in fams:
        for d in f["datasets"]:
            tally[d["claim"]] = tally.get(d["claim"], 0) + 1

    A: list[str] = []
    add = A.append
    add("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">")
    add('<meta name="viewport" content="width=device-width,initial-scale=1">')
    add("<title>Voice-health dataset landscape</title>")
    # same palette as index.html so the two pages read as one site
    add("""<style>
:root{--bg:#0d1017;--panel:#12151b;--panel2:#171b24;--line:#232936;--fg:#e6e9ef;
--muted:#98a2b8;--accent:#7e9cff;--warn:#ffd166;--bad:#ff6b6b;--ok:#5ddba4;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1320px;margin:0 auto;padding:32px 20px 96px}
h1{font-size:30px;line-height:1.25;margin:0 0 8px;letter-spacing:-.02em}
h2{font-size:20px;margin:56px 0 6px;letter-spacing:-.01em}
h2 .fid{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
display:block;font-weight:600;margin-bottom:6px}
h3{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
margin:56px 0 14px;font-weight:600;border-bottom:1px solid var(--line);padding-bottom:10px}
p{margin:0 0 14px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{background:#1b2130;border:1px solid var(--line);border-radius:4px;padding:1px 5px;
font-size:.86em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.thesis{font-size:19px;line-height:1.55;color:#cfd6e4;margin:14px 0 22px;
border-left:3px solid var(--accent);padding-left:16px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:20px 22px;margin:18px 0}
.mech{color:var(--muted);font-size:14.5px;margin:0 0 14px;max-width:88ch}
.meta{color:var(--muted);font-size:13px}
.small{font-size:13px}.muted{color:var(--muted)}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.stat .n{font-size:34px;font-weight:650;letter-spacing:-.02em;line-height:1.1}
.stat .k{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.1em;
margin-top:8px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--panel2);text-align:left;padding:11px 13px;font-size:12px;
letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:12px 13px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
td.name{min-width:190px}td.note{min-width:330px;font-size:13.5px;color:#c3cbdb}
.num{font-variant-numeric:tabular-nums}
.chip{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;
padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted);
white-space:nowrap}
.chip.screen{border-color:#6b5518;color:var(--warn);background:#241d0c}
.chip.eval{border-color:#1f5b45;color:var(--ok);background:#0e2119}
.chip.bad{border-color:#6b2222;color:var(--bad);background:#2a1313}
.chip.pend{border-color:#2f3a52;color:#9fb0d0;background:#151b28}
.chip.new{border-color:#3d4f86;color:#a8bcff;background:#141a2c}
.here{display:inline-block;margin-top:6px;font-size:12px;color:var(--ok)}
.filter{width:100%;max-width:360px;background:var(--panel2);border:1px solid var(--line);
border-radius:8px;color:var(--fg);padding:9px 12px;font-size:14px;margin:0 0 14px}
.filter:focus{outline:none;border-color:var(--accent)}
.toc{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 8px}
.toc a{background:var(--panel);border:1px solid var(--line);border-radius:999px;
padding:6px 14px;font-size:13.5px;color:var(--fg)}
.toc a:hover{border-color:var(--accent);text-decoration:none}
footer{margin-top:72px;padding-top:22px;border-top:1px solid var(--line);
color:var(--muted);font-size:13px}
@media (max-width:640px){.wrap{padding:22px 14px 72px}h1{font-size:24px}td,th{padding:10px 11px}}
</style></head><body><div class="wrap">""")

    add('<p class="meta"><a href="index.html">&larr; back to the dashboard</a></p>')
    add("<h1>The voice-health dataset landscape</h1>")
    add('<p class="thesis">Every corpus the field uses to claim a disease can be heard in a '
        "voice &mdash; organised by <strong>what the sound is supposed to reveal</strong>, and "
        "scored on the one question the published surveys do not ask: <strong>could a result "
        "on this dataset mean anything?</strong></p>")

    add('<div class="grid">')
    for n, k in ((n_ds, "datasets catalogued"), (len(fams), "disease families"),
                 (n_new, "released or audited in 2026"),
                 (tally.get("NEVER", 0), "that may NEVER carry a claim")):
        add(f'<div class="stat"><div class="n">{n}</div><div class="k">{esc(k)}</div></div>')
    add("</div>")

    add('<div class="panel"><p><strong>The claim column.</strong> A survey tells you a dataset '
        "exists. This column tells you what a number measured on it would be worth, under a "
        "rigor contract that requires speaker-disjoint splits and a confound baseline:</p><ul>")
    for tier, (cls, meaning) in CLAIM.items():
        add(f'<li><span class="chip {cls}">{tier}</span> &mdash; {esc(meaning)} '
            f'<span class="small muted">({tally.get(tier, 0)} of {n_ds})</span></li>')
    add("</ul><p class=\"small muted\">These are this program's judgements about use "
        "<em>here</em>, not criticisms of the corpora or their authors &mdash; several of the "
        "BLOCKED rows are the best-designed datasets in the field, and the SAP row is the "
        "model everyone else should follow.</p></div>")

    add('<div class="toc">')
    for f in fams:
        add(f'<a href="#{esc(f["id"])}">{esc(f["name"])} '
            f'<span class="muted">({len(f["datasets"])})</span></a>')
    add("</div>")

    add('<input class="filter" id="q" placeholder="filter every table -- try \'open\', '
        "'2026', 'Parkinson', 'NEVER'...\">")

    for f in fams:
        add(f'<h2 id="{esc(f["id"])}"><span class="fid">{esc(f["name"])}</span></h2>')
        add(f'<p class="mech">{esc(f["mechanism"])}</p>')
        add('<div class="tablewrap"><table class="ds"><thead><tr>'
            "<th>dataset</th><th>conditions</th><th>size</th><th>language</th>"
            "<th>labels</th><th>access</th><th>published result</th>"
            "<th>claim &amp; why</th></tr></thead><tbody>")
        for d in f["datasets"]:
            cls = CLAIM[d["claim"]][0]
            newchip = ' <span class="chip new">2026</span>' if d.get("new") else ""
            here = (f'<span class="here">on this host &mdash; {esc(d["here"])}</span>'
                    if d.get("here") else "")
            add("<tr>"
                f'<td class="name"><a href="{esc(d["link"])}"><strong>{esc(d["name"])}</strong>'
                f'</a>{newchip}<br><span class="small muted">{esc(d["year"])}</span>{here}</td>'
                f'<td class="small">{esc(d["conditions"])}</td>'
                f'<td class="small num">{esc(d["n"])}</td>'
                f'<td class="small">{esc(d["lang"])}</td>'
                f'<td class="small">{esc(d["labels"])}</td>'
                f'<td class="small">{esc(ACCESS.get(d["access_tier"], d["access_tier"]))}'
                f'<br><span class="muted">{esc(d["access"])}</span></td>'
                f'<td class="small">{linkify(d["sota"])}</td>'
                f'<td class="note"><span class="chip {cls}">{esc(d["claim"])}</span><br>'
                f'{esc(d["claim_note"])}</td></tr>')
        add("</tbody></table></div>")

    add("<h3>The four studies that shaped this table</h3>")
    add('<div class="tablewrap"><table class="ds"><thead><tr><th>study</th><th>id</th>'
        "<th>why it matters here</th></tr></thead><tbody>")
    for m in reg["meta_studies"]:
        add(f'<tr><td class="name"><strong>{esc(m["name"])}</strong><br>'
            f'<span class="small muted">{esc(m["authors"])} &middot; {esc(m["date"])}</span></td>'
            f'<td class="small">{linkify(m["id"])}</td>'
            f'<td class="note">{esc(m["why"])}</td></tr>')
    add("</tbody></table></div>")

    add("<footer>")
    add('<p><a href="index.html">&larr; dashboard</a> &middot; '
        '<a href="hypotheses/index.html">hypothesis registry</a> &middot; '
        '<a href="dashboard/experiments/index.html">run ledger</a></p>')
    add(f'<p>Generated by <a href="{BLOB}/scripts/build_datasets_page.py">'
        f"<code>scripts/build_datasets_page.py</code></a> from "
        f"<code>corpus/datasets.json</code> on {built} &middot; commit "
        f"<code>{esc(git_sha())}</code>. The page is never hand-edited; every "
        "cell comes from the registry. Sizes and published results are <em>quoted from the "
        "cited source</em>, not measured here &mdash; except the green "
        "<span class=\"here\">on this host</span> lines, which are decoded counts from "
        "<code>data/interim/</code>.</p>")
    add("<p>Every arXiv id was fetched and its title and authors confirmed before it shipped. "
        "Anything that failed a fetch is marked <code>[UNVERIFIED]</code>. Nothing is cited "
        "from memory.</p>")
    add("<p><strong>Not a medical device.</strong> No diagnosis, no clinical claim. "
        "Internal QA pass &mdash; independent external review pending.</p></footer>")

    add("""</div><script>
// one filter box drives every table on the page
document.getElementById('q').addEventListener('input',function(){
  var v=this.value.toLowerCase();
  document.querySelectorAll('table.ds').forEach(function(t){
    var shown=0;
    Array.prototype.slice.call(t.tBodies[0].rows).forEach(function(r){
      var hit=r.innerText.toLowerCase().indexOf(v)>-1;
      r.style.display=hit?'':'none'; if(hit)shown++;
    });
    // hide a family heading entirely when nothing in it matches
    var sec=t.closest('.tablewrap');
    sec.style.display=shown?'':'none';
    var h=sec.previousElementSibling, m=h&&h.previousElementSibling;
    if(h)h.style.display=shown?'':'none';
    if(m&&m.tagName==='H2')m.style.display=shown?'':'none';
  });
});
</script></body></html>""")

    OUT.write_text("\n".join(A), encoding="utf-8")
    leak_gate([OUT])
    print(f"=== dataset landscape built ===\n  {OUT}  ({OUT.stat().st_size:,} bytes)")
    print("  markdown-leak gate: clean")
    print(f"  {n_ds} datasets across {len(fams)} families; {n_new} new in 2026")
    print("  claim tiers: " + " | ".join(f"{k} {v}" for k, v in sorted(tally.items())))


if __name__ == "__main__":
    main()
