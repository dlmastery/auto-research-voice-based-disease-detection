"""build_experiment_pages.py -- the per-run (third) dashboard tier.

The house hierarchy is master -> per-hypothesis -> per-experiment. This program had
two tiers; `docs/dashboard/experiments/` was scaffolded on 2026-07-25 and stayed
empty. This closes it: one page per artifact-backed run, generated from the artifact
and nothing else.

What a page here is, and is not:

* It IS a full rendering of one artifact -- every metric, every CI, every bootstrap
  count, the power arithmetic, the reproduction provenance (command, config hash,
  run commit, content hashes), and the per-repeat / per-rank / per-cell arrays that
  the master page has no room for.
* It is NOT the 7-step reasoning entry the sibling convention renders, because this
  program has no `reasoning_annotations.json` and never wrote one. Every page states
  that absence in place of the panel rather than omitting the panel silently. An
  empty section a reader can see is a debt; a section that was never mentioned is a
  gap nobody can audit.

Generated, never hand-edited. Reads `autoresearch_results/*.json` via the declared
registry in `build_common.RUN_REGISTRY`.

Usage:  python scripts/build_experiment_pages.py     # CPU, no network, seconds
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_common import (  # noqa: E402
    BLOB, DOCS, built_stamp, esc, fatal, fmt, git_sha, leak_gate, load_runs,
    md_inline, mtime_utc,
)

OUT = DOCS / "dashboard" / "experiments"

CSS = """
:root{--bg:#0d1017;--panel:#12151b;--panel2:#171b24;--line:#232936;--fg:#e6e9ef;
--muted:#98a2b8;--accent:#7e9cff;--warn:#ffd166;--bad:#ff6b6b;--ok:#5ddba4;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 96px}
h1{font-size:26px;line-height:1.28;margin:0 0 6px;letter-spacing:-.02em}
h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
margin:48px 0 12px;font-weight:600;border-bottom:1px solid var(--line);padding-bottom:9px}
h3{font-size:16px;margin:0 0 8px}
p{margin:0 0 14px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{background:#1b2130;border:1px solid var(--line);border-radius:4px;padding:1px 5px;
font-size:.86em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;
word-break:break-all}
pre{background:#0a0d13;border:1px solid var(--line);border-radius:8px;padding:13px 15px;
overflow-x:auto;font-size:12.5px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.sub{color:var(--muted);font-size:15px;margin:0 0 18px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:18px 22px;margin:14px 0}
.panel.debt{border-left:4px solid var(--warn)}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.stat .n{font-size:27px;font-weight:650;letter-spacing:-.02em;line-height:1.15;
font-variant-numeric:tabular-nums}
.stat .k{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.1em;
margin-top:7px}
.stat .s{color:var(--muted);font-size:12.5px;margin-top:7px}
.meta{color:var(--muted);font-size:13px}.small{font-size:13px}.muted{color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{background:var(--panel2);text-align:left;padding:10px 13px;font-size:11.5px;
letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
border-bottom:1px solid var(--line);white-space:nowrap;position:sticky;top:0}
td{padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.chip{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;
padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted);
white-space:nowrap}
.chip.eval{border-color:#1f5b45;color:var(--ok);background:#0e2119}
.chip.screen{border-color:#6b5518;color:var(--warn);background:#241d0c}
.chip.bad{border-color:#6b2222;color:var(--bad);background:#2a1313}
.chip.pend{border-color:#2f3a52;color:#9fb0d0;background:#151b28}
.ok{color:var(--ok)}.bad{color:var(--bad)}.warnc{color:var(--warn)}
footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);
color:var(--muted);font-size:13px}
@media (max-width:640px){.wrap{padding:22px 14px 72px}h1{font-size:21px}td,th{padding:9px 10px}}
"""


def chip(tier: str) -> str:
    cls = {"EVALUATION": "eval", "SCREENING": "screen", "CONTROL": "pend"}.get(tier, "pend")
    return f'<span class="chip {cls}">{esc(tier)}</span>'


def verdict_chip(v: str) -> str:
    cls = "bad" if ("NOT" in v.upper() or "PARTIAL" in v.upper()) else "eval"
    return f'<span class="chip {cls}">{esc(v)}</span>'


# --------------------------------------------------------------------------- #
# per-shape detail renderers -- each reads ONLY the artifact it is handed
# --------------------------------------------------------------------------- #

def detail_bench(d: dict) -> str:
    A: list[str] = []
    spk, rec = d["speaker_level"], d["recording_level"]
    mvc = d["margins_vs_confound"]
    A.append("<h2>Every head and every confound baseline</h2>")
    A.append('<div class="tablewrap"><table><thead><tr><th>head / baseline</th>'
             "<th>speaker AUC</th><th>95% CI</th><th>recording AUC</th><th>UAR</th>"
             "<th>ECE</th><th>per-repeat mean &plusmn; std</th><th>verdict</th>"
             "</tr></thead><tbody>")
    order = [k for k in spk if not k.startswith("confound::")] + \
            [k for k in spk if k.startswith("confound::")]
    for k in order:
        s, r = spk[k], rec.get(k, {})
        ci = s.get("roc_auc_ci95", {})
        is_conf = k.startswith("confound::")
        name = k.replace("confound::", "")
        label = (f'<span class="muted">confound</span> <code>{esc(name)}</code>'
                 if is_conf else f"<code>{esc(k)}</code>")
        if is_conf:
            v = ('<span class="chip screen">THE BAR</span>'
                 if k == mvc["confound_bar_name"] else '<span class="chip pend">baseline</span>')
        else:
            v = verdict_chip(d["verdicts"].get(k, "?"))
        A.append(
            f"<tr><td>{label}</td><td class=\"num\"><strong>{fmt(s['roc_auc'])}</strong></td>"
            f'<td class="num muted">[{fmt(ci.get("lo"), 3)}, {fmt(ci.get("hi"), 3)}] '
            f'<span class="small">n_boot={ci.get("n_boot", "?")}</span></td>'
            f'<td class="num">{fmt(r.get("roc_auc"))}</td>'
            f'<td class="num">{fmt(s.get("uar"))}</td>'
            f'<td class="num">{fmt(s.get("ece"), 3)}</td>'
            f'<td class="num muted">{fmt(s.get("per_repeat_auc_mean"))} &plusmn; '
            f'{fmt(s.get("per_repeat_auc_std"), 4)}</td><td>{v}</td></tr>')
    A.append("</tbody></table></div>")
    A.append('<p class="small muted">ECE is expected calibration error: the gap between '
             "stated confidence and observed frequency. It is reported here because "
             "clinical usability is a probability question, not a ranking question "
             "(CLAUDE.md &sect;4.3). A head can rank well and still be badly calibrated "
             "&mdash; compare the ensemble's ECE against the plain logistic head.</p>")

    A.append("<h2>Margin against the confound bar, per head</h2>")
    A.append('<div class="tablewrap"><table><thead><tr><th>head</th>'
             "<th>recording-level delta [95% CI]</th><th>speaker-level delta [95% CI]</th>"
             "<th>paired Wilcoxon over repeats</th><th>cleared?</th></tr></thead><tbody>")
    for head, ph in mvc["per_head"].items():
        rd, sd = ph["recording_level_delta_auc"], ph["speaker_level_delta_auc"]
        w = ph["paired_wilcoxon_over_repeats"]
        cleared = ph["cleared_confound_bar_speaker"] or ph["cleared_confound_bar_recording"]
        A.append(
            f"<tr><td><code>{esc(head)}</code></td>"
            f'<td class="num">{rd["delta"]:+.4f} <span class="small muted">'
            f'[{fmt(rd["lo"], 3)}, {fmt(rd["hi"], 3)}], p&gt;0 = {fmt(rd["p_gt_zero"], 4)}</span></td>'
            f'<td class="num">{sd["delta"]:+.4f} <span class="small muted">'
            f'[{fmt(sd["lo"], 3)}, {fmt(sd["hi"], 3)}], p&gt;0 = {fmt(sd["p_gt_zero"], 4)}</span></td>'
            f'<td class="num">W = {fmt(w["statistic"], 1)}, p = {fmt(w["p_value"], 6)}</td>'
            f'<td>{"<span class=\'ok\'>YES</span>" if cleared else "<span class=\'bad\'>NO</span>"}</td></tr>')
    A.append("</tbody></table></div>")

    pra = d.get("per_repeat_auc") or {}
    if pra:
        A.append("<h2>Per-repeat traces</h2>")
        A.append('<div class="tablewrap"><table><thead><tr><th>head / baseline</th>'
                 "<th>AUC per repeated partition</th></tr></thead><tbody>")
        for k, arr in pra.items():
            vals = " &middot; ".join(fmt(v, 4) for v in arr) if isinstance(arr, list) else esc(arr)
            A.append(f'<tr><td><code>{esc(k)}</code></td><td class="num small">{vals}</td></tr>')
        A.append("</tbody></table></div>")
        A.append('<p class="small muted">The spread across repeated speaker-disjoint '
                 "partitions is the empirical noise band. A delta smaller than this spread "
                 "is not a result whatever its point estimate says.</p>")
    return "\n".join(A)


def detail_v1(d: dict) -> str:
    A = ["<h2>Per-seed detail &mdash; every repeat, not a summary</h2>",
         '<div class="tablewrap"><table><thead><tr><th>seed</th><th>speakers</th>'
         "<th>recordings</th><th>age healthy</th><th>age patho</th><th>age gap</th>"
         "<th>AUC age only</th><th>AUC WavLM</th><th>AUC eGeMAPS</th></tr></thead><tbody>"]
    for r in d["repeats_detail"]:
        win = r["auc_egemaps"] > r["auc_wavlm"]
        A.append(
            f'<tr><td class="num">{r["seed"]}</td>'
            f'<td class="num">{r["n_speakers"]:,}</td>'
            f'<td class="num">{r["n_recordings"]:,}</td>'
            f'<td class="num muted">{fmt(r["age_healthy"], 2)}</td>'
            f'<td class="num muted">{fmt(r["age_patho"], 2)}</td>'
            f'<td class="num">{fmt(r["age_gap"], 3)}</td>'
            f'<td class="num">{fmt(r["auc_age_only"])}</td>'
            f'<td class="num">{fmt(r["auc_wavlm"])}</td>'
            f'<td class="num {"ok" if win else ""}">{fmt(r["auc_egemaps"])}</td></tr>')
    A.append("</tbody></table></div>")
    n_win = sum(1 for r in d["repeats_detail"] if r["auc_egemaps"] > r["auc_wavlm"])
    ci = d["wavlm_minus_egemaps_ci95"]
    A.append(f'<div class="panel"><p>eGeMAPS beats WavLM on <strong>{n_win} of '
             f'{len(d["repeats_detail"])} seeds</strong>. Paired difference '
             f'<strong>{d["wavlm_minus_egemaps"]:+.5f}</strong> '
             f'(95% CI [{fmt(ci[0], 5)}, {fmt(ci[1], 5)}]) &mdash; the interval excludes '
             "zero, and it excludes it on the <em>losing</em> side for the SSL model.</p>"
             f'<p class="small muted">Encoders registered: '
             + ", ".join(f"<code>{esc(e)}</code>" for e in d["encoders_registered"])
             + "; encoders actually run: "
             + ", ".join(f"<code>{esc(e)}</code>" for e in d["encoders_run"])
             + f'. Scope stated in the artifact: {md_inline(d["note_scope"])}. '
             "A registered-but-unrun encoder is a hole in the family, not a free pass "
             "&mdash; it is why the falsifier is not formally closed.</p></div>")
    A.append(f'<div class="panel"><h3>The matching is checked, not assumed</h3>'
             f'<p>Age matching at a &plusmn;{d["age_tolerance_years"]}-year tolerance '
             f'collapses the age-only AUC to <strong>{fmt(d["mean_auc_age_only"])}</strong> '
             f'and leaves a mean age gap of <strong>{fmt(d["mean_age_gap"], 4)} years</strong>. '
             f'The artifact records <code>matching_worked = {d["matching_worked"]}</code>. '
             "Without that collapse the comparison beneath it would be meaningless, so it "
             "is measured every run rather than assumed once.</p></div>")
    return "\n".join(A)


def detail_v2(d: dict) -> str:
    shuffled = bool(d.get("shuffle_control"))
    A = ["<h2>Rank sweep &mdash; the subspace against variance-matched controls</h2>"]
    if shuffled:
        A.append('<div class="panel"><p><span class="chip pend">NEGATIVE CONTROL</span> '
                 "Labels are shuffled. If the main run's effect were an artefact of the "
                 "projection machinery rather than of identity, it would survive here. "
                 "It does not: full AUC falls to "
                 f"<strong>{fmt(d['auc_full_mean'])}</strong>, i.e. chance.</p></div>")
    A.append('<div class="tablewrap"><table><thead><tr><th>rank k</th>'
             "<th>AUC, speaker subspace removed</th><th>AUC, top-k PCA removed</th>"
             "<th>AUC, variance-matched removed</th><th>D vs top-k [95% CI]</th>"
             "<th>variance removed spk / topk / matched</th><th>speaker-ID after</th>"
             "</tr></thead><tbody>")
    for r in d["rows"]:
        ci = r.get("D_vs_pca_topk_ci95", [float("nan")] * 2)
        cls = "ok" if r.get("D_vs_pca_topk_excludes_zero") else "muted"
        A.append(
            f'<tr><td class="num"><strong>{r["k"]}</strong></td>'
            f'<td class="num">{fmt(r["auc_speaker_removed"])}</td>'
            f'<td class="num">{fmt(r.get("auc_pca_topk_removed"))}</td>'
            f'<td class="num">{fmt(r.get("auc_var_matched_removed"))}</td>'
            f'<td class="num {cls}">{r.get("D_vs_pca_topk", float("nan")):+.4f} '
            f'<span class="small muted">[{fmt(ci[0], 3)}, {fmt(ci[1], 3)}]</span></td>'
            f'<td class="num small muted">{fmt(r.get("variance_removed_speaker"), 3)} / '
            f'{fmt(r.get("variance_removed_pca_topk"), 3)} / '
            f'{fmt(r.get("variance_removed_var_matched"), 3)}</td>'
            f'<td class="num">{fmt(r.get("speaker_id_acc_after"), 3)}</td></tr>')
    A.append("</tbody></table></div>")
    A.append('<p class="small muted">Both controls are built from the data\'s own principal '
             "axes and remove <em>at least as much variance</em> as the speaker subspace, so "
             "a positive D cannot be explained by &quot;more signal was deleted&quot;.</p>")
    if d.get("auc_full"):
        A.append("<h2>Per-repeat full-embedding AUC</h2>")
        A.append('<div class="panel"><p class="num">'
                 + " &middot; ".join(fmt(v) for v in d["auc_full"])
                 + f'</p><p class="small muted">Mean {fmt(d["auc_full_mean"])} over '
                 f'{len(d["auc_full"])} repeats. Speaker-ID accuracy on unprojected '
                 f'embeddings {fmt(d.get("speaker_id_acc_full"), 4)} against a chance rate of '
                 f'{fmt(d.get("speaker_id_chance"), 4)} &mdash; the manipulation check, and it '
                 "is WEAK: mean-pooled WavLM is not an x-vector, so the identity subspace "
                 "estimated here is a partial one.</p></div>")
    return "\n".join(A)


def detail_cells(d: dict, cols: list[tuple[str, str, int]], note: str) -> str:
    """V6/V7 share a `cells` shape: one row per pre-registered (corpus, condition) cell,
    including the cells that did NOT run. Rendering the unrun cells is the point."""
    A = ["<h2>Pre-registered cells &mdash; including the ones that did not run</h2>",
         '<div class="tablewrap"><table><thead><tr>'
         + "".join(f"<th>{esc(label)}</th>" for label, _, _ in cols)
         + "<th>status</th></tr></thead><tbody>"]
    for c in d["cells"]:
        ran = c.get("status") == "RUN"
        tds = []
        for _, key, dec in cols:
            v = c.get(key)
            if v is None or v == "":
                tds.append('<td class="muted small">not yet measured</td>')
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                tds.append(f'<td class="num">{fmt(v, dec)}</td>' if dec
                           else f'<td class="num">{v:,}</td>')
            elif isinstance(v, list):
                tds.append(f'<td class="num small muted">[{fmt(v[0], 4)}, {fmt(v[1], 4)}]</td>')
            else:
                tds.append(f"<td>{esc(v)}</td>")
        st = ('<span class="chip eval">RUN</span>' if ran
              else f'<span class="chip pend">{esc(c.get("status", "NOT RUN"))}</span>')
        A.append("<tr>" + "".join(tds) + f"<td>{st}</td></tr>")
    A.append("</tbody></table></div>")
    A.append(f'<div class="panel debt"><p>{note}</p></div>')
    return "\n".join(A)


def detail_v6(d: dict) -> str:
    return detail_cells(
        d,
        [("corpus", "corpus", 0), ("backbone", "backbone", 0),
         ("recordings", "n_recordings", 0), ("speakers", "n_speakers", 0),
         ("AUC, scaler fit on ALL", "auc_fit_on_all", 4),
         ("AUC, scaler fit per fold", "auc_fit_per_fold", 4),
         ("delta (leak - honest)", "delta_mean", 5),
         ("95% CI on delta", "delta_ci95", 4)],
        f'<strong>{d["cells_run"]} of {len(d["cells"])} pre-registered cells ran.</strong> '
        "The unrun cells are the corpus-specificity arm &mdash; the part of this "
        "hypothesis that is actually novel. The near-null reproduced on SVD is a "
        "reproduction of the audited paper's point, not the new claim, so the falsifier "
        "is <em>not evaluable</em> and the finding is PARTIAL. "
        f'Artifact self-report: <code>all_within_pm_0.01 = {d["all_within_pm_0.01"]}</code>.')


def detail_v7(d: dict) -> str:
    return detail_cells(
        d,
        [("corpus", "corpus", 0), ("features", "features", 0),
         ("recordings", "n_recordings", 0), ("speakers", "n_speakers", 0),
         ("AUC", "auc", 4), ("95% CI", "auc_ci95", 4),
         ("AUC directionless", "auc_directionless", 4)],
        f'<strong>{d["cells_run"]} of {len(d["cells"])} pre-registered cells ran</strong>, '
        "and the artifact reports its own limitation in a field: "
        f'<code>falsifier_fully_evaluable = {d["falsifier_fully_evaluable"]}</code>. '
        f'<code>all_below_0.60 = {d["all_below_0.60"]}</code>. The corpora measured here are '
        "sustained vowels and coughs; Pitt, where the audited shortcut was found, is "
        "spontaneous speech in which pause structure carries cognitive load. So this is "
        "<em>not</em> evidence that the Pitt effect was spurious &mdash; it is evidence "
        "that the shortcut does not transfer to these acoustic conditions.")


def detail_f1(d: dict) -> str:
    A = ["<h2>Predictors</h2>",
         '<div class="tablewrap"><table><thead><tr><th>predictor</th><th>ROC-AUC</th>'
         "<th>n</th></tr></thead><tbody>",
         f'<tr><td>age alone</td><td class="num"><strong>{fmt(d["auc_age_only"])}</strong></td>'
         f'<td class="num muted">{d["n_sessions"]:,} sessions</td></tr>',
         f'<tr><td>sex alone <span class="small muted">(negative control)</span></td>'
         f'<td class="num">{fmt(d["auc_sex_only"])}</td>'
         f'<td class="num muted">{d["n_sessions"]:,} sessions</td></tr>',
         f'<tr><td>age + sex, logistic, speaker-disjoint <code>GroupKFold</code></td>'
         f'<td class="num"><strong>{fmt(d["auc_age_sex_speaker_disjoint"])}</strong></td>'
         f'<td class="num muted">{d["n_sessions"]:,} sessions / {d["n_speakers"]:,} '
         "speaker groups</td></tr>",
         "</tbody></table></div>",
         f'<div class="panel"><h3>The recruitment asymmetry underneath it</h3>'
         f'<p>Mean age <strong>{fmt(d["mean_age_healthy"], 1)}</strong> years healthy vs '
         f'<strong>{fmt(d["mean_age_pathological"], 1)}</strong> pathological &mdash; a gap of '
         f'<strong>{d["mean_age_pathological"] - d["mean_age_healthy"]:.1f} years</strong> over '
         f'{d["n_pathological"]:,} pathological and {d["n_healthy"]:,} healthy sessions.</p>'
         f'<p><strong>{d["speakers_with_multiple_sessions"]} of {d["n_speakers"]:,} speakers</strong> '
         f'contribute more than one session (max {d["max_sessions_per_speaker"]}). A '
         "recording-level split leaks every one of them across folds.</p></div>",
         f'<div class="panel"><p class="small muted">Published benchmark for orientation: '
         f'{md_inline(d["published_benchmark"])}</p></div>']
    return "\n".join(A)


DETAIL = {
    "run-bench-egemaps": detail_bench,
    "run-bench-wavlm": detail_bench,
    "run-f1-demographics": detail_f1,
    "run-v1-ssl-vs-handcrafted": detail_v1,
    "run-v2-speaker-subspace": detail_v2,
    "run-v2-shuffle-control": detail_v2,
    "run-v6-preprocessing-leakage": detail_v6,
    "run-v7-silence-shortcut": detail_v7,
}


# --------------------------------------------------------------------------- #

def page(r: dict) -> str:
    d = r["raw"]
    A = ['<!doctype html>\n<html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         f'<title>{esc(r["id"])} &mdash; {esc(r["title"])}</title>',
         f"<style>{CSS}</style></head><body><div class=\"wrap\">"]
    add = A.append
    add('<p class="meta"><a href="../../index.html">&larr; dashboard</a> &middot; '
        '<a href="index.html">all runs</a>'
        + (f' &middot; <a href="../../hypotheses/{r["hypothesis"]}.html">'
           f'hypothesis {esc(r["hypothesis"])}</a>' if r["hypothesis"] else "")
        + "</p>")
    add(f'<h1>{esc(r["title"])}</h1>')
    add(f'<p class="sub">{chip(r["tier"])} {verdict_chip(r["verdict"])} '
        + (f'<span class="chip screen">SCOPE-LIMITED</span> ' if r["scope"] else "")
        + f'<span class="chip">{esc(r["corpus"])}</span> '
        f'<span class="chip">{esc(r["backbone"])}</span></p>')
    if r["scope"]:
        add(f'<div class="panel debt"><p><strong>Scope caveat.</strong> This run is a '
            f'{esc(r["scope"])}. It may satisfy the repeat contract and still be a '
            "narrower measurement than a later run on the same corpus; both facts are "
            "shown because either alone would mislead.</p></div>")

    # headline stats
    add('<div class="grid">')
    add(f'<div class="stat"><div class="n">{fmt(r["headline"])}</div>'
        f'<div class="k">{esc(r["headline_label"])}</div>'
        + (f'<div class="s">95% CI [{fmt(r["headline_ci"][0] if isinstance(r["headline_ci"], list) else r["headline_ci"].get("lo"), 3)}, '
           f'{fmt(r["headline_ci"][1] if isinstance(r["headline_ci"], list) else r["headline_ci"].get("hi"), 3)}]</div>'
           if r["headline_ci"] else '<div class="s">no CI in the artifact</div>')
        + "</div>")
    bar_val = (fmt(r["bar"]) if r.get("bar") is not None else esc(r.get("bar_text", "&mdash;")))
    add(f'<div class="stat"><div class="n">{bar_val}</div>'
        f'<div class="k">{esc(r["bar_label"])}</div></div>')
    add(f'<div class="stat"><div class="n">n = {r["n_repeats"]}</div>'
        f'<div class="k">repeats &times; {r["n_folds"]} folds</div>'
        f'<div class="s">{esc(r["tier_why"])}</div></div>')
    add(f'<div class="stat"><div class="n">'
        f'{(f"{r['n_speakers']:,}" if r["n_speakers"] else "&mdash;")}</div>'
        f'<div class="k">speakers</div><div class="s">'
        + (f'{r["n_recordings"]:,} recordings' if r["n_recordings"] else "recording count not in artifact")
        + "</div></div>")
    add("</div>")

    # power contract
    p = r.get("power")
    if p and p.get("min_attainable_p"):
        ok = (p.get("feasible") if "feasible" in p
              else p["min_attainable_p"] <= (p.get("holm_tightest_threshold") or 1))
        add("<h2>Power contract (R6)</h2>")
        add(f'<div class="panel"><p>Paired Wilcoxon over {p["n_paired"]} repeats gives a '
            f'minimum attainable p of <strong>{fmt(p["min_attainable_p"], 6)}</strong> = '
            f'2/2<sup>{p["n_paired"]}</sup>, against a Holm-tightest threshold of '
            f'<strong>{fmt(p.get("holm_tightest_threshold"), 6)}</strong> = 0.05/'
            f'{p.get("family_size")} for the pre-registered family. '
            + ('<span class="ok">Feasible.</span>' if ok
               else '<span class="bad">NOT feasible &mdash; no result here can reach '
                    "significance whatever the data says.</span>")
            + " This is arithmetic on the design, computed before the data: it says what "
            "the run <em>could</em> have shown, not what it did.</p></div>")

    add(DETAIL[r["id"]](d))

    # provenance
    add("<h2>Reproduction provenance</h2>")
    add('<div class="tablewrap"><table><tbody>')
    add(f'<tr><td class="muted">artifact</td><td><code>autoresearch_results/'
        f'{esc(r["artifact"])}</code> &middot; '
        f'<a href="{BLOB}/autoresearch_results/{esc(r["artifact"])}">view raw</a> &middot; '
        f'last written {esc(r["mtime"])}</td></tr>')
    for k, v in (r.get("provenance") or {}).items():
        if v:
            add(f'<tr><td class="muted">{esc(k)}</td><td><code>{esc(v)}</code></td></tr>')
    if r.get("elapsed_s"):
        add(f'<tr><td class="muted">wall clock</td><td class="num">{r["elapsed_s"]:,.1f} s '
            f'({r["elapsed_s"] / 3600:.2f} h)</td></tr>')
    if r["finding"]:
        add(f'<tr><td class="muted">written up as</td><td>{esc(r["finding"])} in '
            f'<a href="{BLOB}/FINDINGS.md">FINDINGS.md</a></td></tr>')
    add("</tbody></table></div>")

    # the debt this tier cannot pay from artifacts
    add("<h2>What this page does not have</h2>")
    add('<div class="panel debt"><p><strong>No 7-step reasoning entry exists for this '
        "run.</strong> The sibling convention renders Diagnosis &middot; Citations &middot; "
        "Hypothesis &middot; Prediction &middot; Verdict &middot; Learning on every "
        "per-experiment page, sourced from a <code>reasoning_annotations.json</code>. This "
        "program never wrote one, and neither does it keep an append-only "
        "<code>experiment_log.jsonl</code>; the run history is the set of artifact files "
        "listed on the <a href=\"index.html\">run ledger</a>, ordered only by their write "
        "time. The pre-registered prediction for this run does exist &mdash; it is on the "
        + (f'<a href="../../hypotheses/{esc(r["hypothesis"])}.html">{esc(r["hypothesis"])} '
           "hypothesis page</a>, recorded before the run"
           if r["hypothesis"] else
           "hypothesis registry, but this run predates the registry and has no "
           "pre-registered prediction of its own")
        + ". Everything else on that convention&rsquo;s checklist is absent here and is "
        "shown as absent rather than quietly dropped.</p></div>")

    add("<footer><p>Generated by <code>scripts/build_experiment_pages.py</code> from "
        f"<code>autoresearch_results/{esc(r['artifact'])}</code>. Never hand-edited; every "
        "number on this page is read from that file.</p>"
        f'<p>Built {built_stamp()} &middot; commit <code>{esc(git_sha())}</code></p>'
        "<p><strong>Not a medical device.</strong> Internal QA pass &mdash; independent "
        "external review pending.</p></footer></div></body></html>")
    return "\n".join(A)


def index(runs: list[dict]) -> str:
    A = ['<!doctype html>\n<html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>Run ledger</title>", f"<style>{CSS}</style></head><body><div class=\"wrap\">",
         '<p class="meta"><a href="../../index.html">&larr; dashboard</a></p>',
         "<h1>Run ledger &mdash; every artifact-backed run</h1>",
         f'<p class="sub">{len(runs)} runs, newest first. Each has a page rendering its '
         "artifact in full: every metric, every interval, the power arithmetic, and the "
         "reproduction provenance. There is no "
         "<code>experiment_log.jsonl</code> in this repository, so this ledger is "
         "assembled from the artifact files themselves &mdash; a declared registry, not a "
         "directory listing, so a renamed or undeclared artifact fails the build instead "
         "of vanishing from the page.</p>",
         '<div class="tablewrap"><table><thead><tr><th>run</th><th>tier</th>'
         "<th>n</th><th>corpus / backbone</th><th>headline</th><th>verdict</th>"
         "<th>hypothesis</th><th>finding</th><th>written</th></tr></thead><tbody>"]
    for r in runs:
        A.append(
            f'<tr><td><a href="{esc(r["id"])}.html"><strong>{esc(r["id"])}</strong></a><br>'
            f'<span class="small muted">{esc(r["title"])}</span></td>'
            f'<td>{chip(r["tier"])}'
            + ('<br><span class="chip screen">SCOPE-LIMITED</span>' if r["scope"] else "")
            + f'</td><td class="num">{r["n_repeats"]}&times;{r["n_folds"]}</td>'
            f'<td class="small">{esc(r["corpus"])}<br>'
            f'<span class="muted">{esc(r["backbone"])}</span></td>'
            f'<td class="num">{fmt(r["headline"])}<br>'
            f'<span class="small muted">{esc(r["headline_label"])}</span></td>'
            f'<td>{verdict_chip(r["verdict"])}</td>'
            + (f'<td><a href="../../hypotheses/{esc(r["hypothesis"])}.html">'
               f'{esc(r["hypothesis"])}</a></td>' if r["hypothesis"]
               else '<td class="muted small">none &mdash; predates the registry</td>')
            + f'<td class="small">{esc(r["finding"]) or "<span class=\'muted\'>none</span>"}</td>'
            f'<td class="small muted">{esc(r["mtime"])}</td></tr>')
    A += ["</tbody></table></div>",
          f'<footer><p>Generated {built_stamp()} by '
          "<code>scripts/build_experiment_pages.py</code> &middot; commit "
          f"<code>{esc(git_sha())}</code></p>"
          "<p><strong>Not a medical device.</strong> Internal QA pass &mdash; independent "
          "external review pending.</p></footer></div></body></html>"]
    return "\n".join(A)


def main() -> None:
    runs = load_runs()
    missing = [r["id"] for r in runs if r["id"] not in DETAIL]
    if missing:
        fatal("no detail renderer for run(s): " + ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)

    written = []
    for r in runs:
        p = OUT / f'{r["id"]}.html'
        p.write_text(page(r), encoding="utf-8")
        written.append(p)
    idx = OUT / "index.html"
    idx.write_text(index(runs), encoding="utf-8")
    written.append(idx)

    n = leak_gate(written)
    print("=== per-run experiment pages built ===")
    print(f"  {OUT}")
    print(f"  {len(runs)} run pages + 1 index")
    print(f"  markdown-leak gate: clean across {n} pages")
    for r in runs:
        print(f"    {r['id']:<32} {r['tier']:<11} n={r['n_repeats']:<3} {r['verdict']}")


if __name__ == "__main__":
    main()
