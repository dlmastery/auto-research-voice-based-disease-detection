# HOUSE STANDARD — Autoresearch HTML Dashboard Specification

Status: IN PROGRESS (sections appended as completed)

Sources surveyed:
- `C:\Users\evija\autoresearchindexspy\autoresearchspy\docs\spy_dashboard\` (PRIMARY)
- `C:\Users\evija\autoresearchindexspy\autoresearchspy\docs\index.md`
- `C:\Users\evija\autoresearchindexspy\autoresearchspy\docs\_forex_reference_dashboard\index.html`
- `C:\Users\evija\autoresearch\docs\`
- `C:\Users\evija\AUTORESEARCHTABULAR\docs\`
- `C:\Users\evija\AUTORESEARCHIMAGE\docs\`
- `C:\Users\evija\autoresearchqqq_local\docs\`
- `C:\Users\evija\steeringresearch\CLAUDE.md` §11 (written mandate)

## Sections
1. Page hierarchy
2. Master page anatomy
3. The inline script
4. Styling
5. Charts
6. Rigor furniture
7. Data flow / generator scripts
8. GitHub Pages wiring
9. CHECKLIST

---

## 1. PAGE HIERARCHY

### 1.1 What actually exists (per repo)

**A. `autoresearchindexspy` (PRIMARY reference) — GitHub Pages root = `docs/`**

```
docs/
├── .nojekyll                      (empty, 0 bytes)
├── _config.yml                    (Jekyll theme config)
├── index.md                       ← Jekyll-rendered LANDING page (markdown, layout: default)
├── medium_article.md              ← long-form narrative, rendered by Jekyll
├── paper.md / paper_v1.md         ← the paper
├── EXPLAINABILITY_REPORT.md, FEATURES_AND_DATA.md, TRADING_STRATEGIES.md
├── spy_dashboard/                 ← THE MASTER DASHBOARD (this project)
│   ├── index.html                 (2,994 lines, 232 KB, SELF-CONTAINED, no CDN)
│   ├── experiment_log.jsonl       (4.2 MB — the append-only ledger, fetched at runtime)
│   ├── best_config.json           (champion config + full results)
│   ├── reasoning_annotations.json (per-experiment 7-step entries)
│   ├── running.json               (transient; presence => "Currently Running" panel)
│   ├── autoresearch_report.md, experiment_summary.md, AUTORESEARCH_PROCESS.md,
│   │   DEPLOYMENT.md, EXPLAINABILITY_REPORT.md, FEATURES_AND_DATA.md, TRADING_STRATEGIES.md
│   ├── autoresearch_equity.xlsx   (downloadable all-experiment workbook w/ charts)
│   ├── oos_*.json / oos_*.csv     (~200 out-of-sample artifacts, auto-globbed)
│   └── trade_logs/
│       ├── manifest.json          ← INDEX of which per-experiment CSVs exist
│       ├── expNNN_trades.csv      (per-experiment per-day win/loss)
│       └── <ensemble>_trades.csv + <ensemble>_trade_summary.json
├── _forex_reference_dashboard/index.html   ← the PREDECESSOR dashboard, frozen (972 lines)
├── clustering_olivetti/index.html          ← sibling example dashboards
└── fraud_ecommerce/index.html
```

**B. `AUTORESEARCHIMAGE` — the two-tier pattern, clearest example**

```
docs/
├── .nojekyll
├── index.html      ← LANDING / narrative page (226 lines, hand-written, static)
├── index.md
└── dashboard/
    ├── index.html                       ← the LIVE MASTER DASHBOARD
    ├── dashboard.html                   (same file under its source name)
    ├── experiment_log.jsonl             ← data
    ├── best_config.json
    ├── reasoning_annotations.json
    ├── composite_fingerprint.json       ← RIGOR: the SHA-256 of the composite formula
    ├── data_split_audit.json / .md
    ├── data_split_audit_fingerprint.json
    ├── third_party_audit.md, publish_quality_audit.md
    ├── real_wilds_3seed_report.md, top3_finalized_comparison.md
    ├── research_journal.md, experiment_summary.md
```

**C. `AUTORESEARCHTABULAR`** — `docs/{.nojekyll, index.html (landing), dashboard.html (live), data.json (data)}`

**D. `autoresearch` (the FX parent)** — `docs/{index.md, docs.html, dashboard/index.html, clustering_olivetti/, fraud_ecommerce/, index_stock_dashboard/}`

**E. `autoresearchqqq_local`** — `docs/dashboard/{index.html + all data artifacts}`

### 1.2 THE HOUSE PATTERN (common to all five)

Exactly **TWO tiers**, not three:

```
TIER 1  docs/index.{html,md}          LANDING page — narrative, headline cards, links out,
                                      caveats, reproduce-in-one-block, companion projects.
                                      STATIC. Hand-written. Jekyll-or-plain.
                                          │
                                          └── links to ──▶
TIER 2  docs/<name>/index.html        MASTER DASHBOARD — one giant self-contained HTML
                                      that fetch()es the JSON/JSONL data files sitting
                                      NEXT TO IT and renders every panel client-side.
                                          │
                                          └── per-experiment detail is an IN-PAGE
                                              EXPANDING PANEL (`#detail-panel`), not a
                                              separate expNNN.html file.
```

**CRITICAL FINDING — there is NO per-experiment HTML file and NO per-hypothesis
sub-dashboard in ANY reference repo.** The steeringresearch CLAUDE.md §11 mandate
(`ideas/<NN>/dashboard/index.html`, `docs/dashboard/experiments/expNNN.html`) is
*aspirational and not implemented anywhere in the reference set*. The reference
implements the drill-down as a **row-click → in-page detail panel** that renders:
the config, the full 7-step reasoning entry, an equity/curve chart, the per-fold
metric table, and a "transparency" block. This is a single-file design decision:
one HTML, N panels, zero navigation.

**Sub-project dashboards** (`clustering_olivetti/`, `fraud_ecommerce/`,
`index_stock_dashboard/`, `spy_dashboard/`, `_forex_reference_dashboard/`) are
SIBLINGS under `docs/`, each a full copy of the master-dashboard file. The
hierarchy is by *project*, not by *hypothesis*.

### 1.3 Linking rules observed
- Landing → dashboard: relative (`dashboard/`, `./dashboard/`, `spy_dashboard/`).
- Dashboard → sibling docs: relative (`autoresearch_report.md`, `experiment_summary.md`).
- Dashboard/landing → source code: **absolute GitHub blob URLs**
  (`https://github.com/dlmastery/<repo>/blob/master/<path>`).
- Data: relative + cache-buster (`fetch('experiment_log.jsonl?t=' + Date.now())`).

---

## 2. MASTER PAGE ANATOMY

Two families exist. **Family A** = the SPY/FX lineage (`spy_dashboard/index.html`,
`_forex_reference_dashboard/index.html`, `autoresearchqqq_local/docs/dashboard/index.html`,
`autoresearch/docs/dashboard/index.html`) — vertically stacked `.section-title` +
content. **Family B** = the ML lineage (`AUTORESEARCHIMAGE/docs/dashboard/index.html`,
`AUTORESEARCHTABULAR/docs/dashboard.html`) — header + toolbar + tabs + panels.
Family B is the NEWER, cleaner design and the one to copy for a fresh build. Both
share the same palette, the same runtime-fetch data model, and the same sort code.

### 2.A Ordered panel list — Family B (RECOMMENDED TEMPLATE, `AUTORESEARCHIMAGE`)

| # | Panel | Element | What it shows | Data source |
|---|---|---|---|---|
| 1 | **Header bar** | `<header>` flex row | `<h1>` project name; `.sub` one-line scope; `.warn` amber caveat chip (e.g. "synthetic OOD — not real WILDS-Camelyon17"); `#status` right-aligned "auto-refresh 5 s · HH:MM:SS" | live clock + fetch |
| 2 | **Toolbar** | `.toolbar` flex row | `input[type=search]` free text; N `select` facet filters; `Reset` button; `CSV` and `JSON` export buttons; `#filter-count` right-aligned "N of M experiments" | client-side over `logs[]` |
| 3 | **Tab strip** | `.tabs` > `.tab` divs | one tab per method/backbone family labelled `NAME (count)`, plus `ALL (total)`; active tab styled | `new Set(logs.map(l=>l.backbone))` |
| 4 | **KPI card grid** | `.panel > .grid > .card` | filtered-experiment count; top composite (with `exp# · backbone` sub-line); top REAL-data composite; **best multi-seed median with `n=` shown**; last experiment | derived from filtered rows |
| 5 | **Composite bar chart** | `.bar-chart > .bar` divs | one CSS-height bar per experiment in experiment order, colour-coded good/mid/bad, `data-tip` hover tooltip, clickable to select the experiment | `composite` per row |
| 6 | **Runs table + reasoning pane** | `.twocol` grid (1.4fr / 1fr) | LEFT: sortable runs table inside `.table-container` (`max-height:70vh; overflow-x:auto`, sticky `thead`). RIGHT: the 7-step reasoning detail for the selected row | `experiment_log.jsonl` + `reasoning_annotations.json` |
| 7 | **Compare panel** | `#compare-panel`, hidden by default | shift-click two rows gives a side-by-side metric table with `delta (b-a)` and `delta %` columns, green/red colouring, plus both rows' diagnosis + learning | two selected rows |
| 8 | **Aggregate table** | `.card > #agg-table` | grouped by (backbone, data_mode, augmentation): `n seeds`, composite mean, **std**, min, max, headline-metric mean, seed list, exp-number list. Sorted by mean desc | groupby over filtered rows |
| 9 | **Footer** | `.footer` | "Auto-refreshes JSONL + reasoning every 5 s · click column headers to sort · Shift-click rows to compare 2 · Ctrl-F not needed (use search box)" | static |

### 2.B Ordered panel list — Family A (`spy_dashboard/index.html`, 2,994 lines)

1. `h1` + `.subtitle` — a dense paragraph naming data streams, optimisation target, split, and baseline; ends with `span#last-update` and inline links to `autoresearch_report.md` / `experiment_summary.md`.
2. `.status-bar` — a pulsing `.status-dot` (`running` = green + `@keyframes pulse`; `idle` = grey) + `#status-text` ("Running -- 166 experiments, last 42s ago" / "Idle -- N experiments completed"). Running iff the last row's timestamp is under 600 s old.
3. `#error` — hidden red div, shown on fetch failure or JSONL parse errors, carrying the count of unparseable lines.
4. `.grid#summary-cards` — auto-fit `minmax(180px,1fr)` KPI cards. Each `.card` = `.label` (uppercase, muted, 0.75em) + `.value` (1.8em, weight 700). Champion cards get `border:2px solid #fbbf24` plus a `title=` tooltip explaining WHY that metric is the winner metric.
5. `Currently Running` — `.section-title` + `.config-box` (monospace, `white-space:pre`), both `display:none` unless the `running.json` fetch succeeds.
6. `Best Config` — a `.config-box` with the champion's full config.
7. `Winner` — `.winner-box` (green `#0d2818` background, `2px solid #3fb950`) with a `BEST COMPOSITE SCORE` label, title, and monospace metrics block.
8. **Metrics Glossary** — a `details` block: "Metrics Glossary — what every column / number means (click to expand)". Inside is an auto-fit grid of themed sub-lists: Headline metrics, Direction-prediction, Statistical reliability, Uncertainty heads, Experiment tracking, Targets, Fold/regime reference, **Decision rules (KEEP / NEAR-MISS / DISCARD / multi-seed lock)**, a per-method catalogue where **every method carries an author-year-venue citation**, **"Strategies NOT YET implemented (roadmap)"**, and **"Important Caveats — Read Before Trading"**. This is the house version of the "how to read this" block, and it is much larger than four bullets: it defines every column, cites every method, and states the honest limits.
9. **Experiment Log** — `.section-title` with grey hint "(click row for per-window breakdown, click header to sort)"; then `#backbone-tabs` (filter tabs rendered from data); then a row-count hint line; then `#exp-table-scroll` (`max-height:75vh; overflow-y:auto`) wrapping `table#exp-table` with sticky `thead th`.
10. **`#detail-panel`** — hidden until a row is clicked. Contains: title + Close button; `.detail-config` monospace config; **`#detail-reasoning`** — a blue left-border block headed `DIAGNOSIS · CITATIONS · HYPOTHESIS · PREDICTION · VERDICT`; test/val/train tab buttons; a target A/B/D selector; the equity-curve chart; the per-fold metric table (22 columns incl. `n`); and `#detail-transparency`.
11. **Best Run Per-Window Breakdown** — the same per-fold table for the champion with its own test/val/train tabs.
12. **Fold Reference table** — the split definition: per fold, regime name, train / val / test windows; a final full-width row asserting **"Zero overlap verified: train-val = 0 | train-test = 0 | val-test = 0 (Lopez de Prado 2018 §7 walk-forward + purge + embargo)"**.
13. **OOS section** — a green `3px solid` divider heading, then several colour-coded sub-panels (`#oos-ensemble-section` amber, `#oos-smart-section` purple, `#oos-section` green, `#oos-top30-section`), each with its own independently sortable table and its own `setInterval` reload.

### 2.C The runs table — exact specification

**Columns (Family B / IMAGE):**
`# | backbone | data | aug | seed | composite | test_ood | val_ood | id_val | id_ood gap | ECE_ood | status`

**Columns (Family A / SPY, 23 columns):**
`# | Status | Description | Composite | Test Sharpe | Val Sharpe | Train Sharpe | IC | Hit% | PSR | $Equity | Conf | Ale | Prec | Rec | F1 | F2 | MCC | Acc | T+/V+ | Time | When | Trades`

Rules that hold in both families:

- Every sortable header carries `data-sort="<jsonl field name>"`. The attribute value **is the raw field key in `experiment_log.jsonl`**, so sorting needs no column-to-field mapping table.
- The identity column is first; `status` renders as a chip; `composite` is the decision column and is **bold and colour-coded**.
- **Default sort:** Family A uses `sortKey = null`, which falls through to `entries.slice().reverse()` — i.e. **newest experiment first**. Family B uses `sortKey="experiment_num", sortDir="asc"`. *Neither defaults to composite-descending*; the champion is surfaced by the KPI cards and by the row highlight instead.
- **Champion-row highlighting is computed live, never stored.** Family A: `const bestComposite = Math.max(...validEntries.map(e => e.composite))` where `validEntries` excludes rows with `composite == null` or `status === 'CRASH'`; the matching row gets `class="best-row"` styled `background:#0d2818 !important; border-left:4px solid #00d26a !important` with `td { font-weight:600 }`.
- **Status stripes:** `tr.keep { border-left:3px solid #3fb950 }`, `tr.discard { border-left:3px solid #f85149 }`, `tr.crash { border-left:3px solid #d29922 }`, `tr.selected { background:#1a2332 !important; border-left:3px solid #58a6ff !important }`.
- **Chips/pills:** base `.pill { display:inline-block; padding:1px 7px; border-radius:99px; font-size:10px; background:#21262d; color:var(--fg) }`. Variants `.kept` (`#0e3a1f` on green), `.disc` (`#441111` on red), `.champ` (`#2c1b53` on `#d2a8ff`), plus domain facets. The class is derived from the status string: `includes("CHAMPION") -> champ`, else `includes("KEEP") -> kept`, else `disc`.
- **`n=` annotation** appears on aggregated numbers only: the KPI card sub-line `n=${bestMedian.n}` and the aggregate table's `n seeds` column next to `std` / `min` / `max` over the seed group. Individual experiment rows carry no `n=` because n=1 is implied by the row identity.
- **Null handling:** every numeric cell passes through `fmt(x, d = 4)`, which returns an em-dash for null/NaN. Never blank, never literal `NaN`.
- **Empty state:** the tbody is replaced by an explanatory row that names the likely failure (`allEntries.length=0` means the JSONL fetch failed — check the DevTools console).
- **Row interaction:** plain click selects and renders the reasoning detail; **shift-click** adds to a max-2 compare set (Family B); Family A click toggles the in-page `#detail-panel`.

---

## 3. THE INLINE SCRIPT

There is **one** `<script>` block in Family B (lines 209-634 of the IMAGE
dashboard). Family A has several `<script>` blocks (one per bolt-on OOS panel) —
that is drift, not the standard. **Build to one.** No frameworks, no imports, no
CDN, no build step, no module system. Plain ES2020 in the global scope.

### 3.1 Module state (top of script)

```js
const RESULTS_BASE = ".";
const COLOR_THRESH = { goodAUC: 0.99, badAUC: 0.95 };
let logs = [], annotations = {}, active = "ALL";
let sortKey = "experiment_num", sortDir = "asc";
let selectedExp = null;
let compareExps = [];            // max 2, for shift-click compare
```

### 3.2 Function inventory (Family B, in file order)

| function | role |
|---|---|
| `fmt(x, d=4)` | number to fixed-decimal string, em-dash for null/NaN |
| `fmtSci(x, d=3)` | fixed for `abs(x) >= 0.001`, else `toExponential(2)` |
| `aucClass(v)` | maps a value to `good` / `mid` / `bad` via `COLOR_THRESH` |
| `deriveExtras(r)` | computes derived columns not in the JSONL (e.g. `id_ood_gap`, nested `ece_test`) — the only place derived metrics are defined |
| `fetchJSONL(path)` | fetch with `{cache:"no-store"}`, split on `/\n+/`, trim, JSON.parse each line inside try/catch, drop nulls, map through `deriveExtras` |
| `fetchJSON(path)` | fetch, `r.ok ? r.json() : {}`, never throws |
| `backboneList()` | `["ALL", ...new Set(logs.map(l=>l.backbone)).sort()]` |
| `searchHit(r, term)` | builds a lowercase haystack from row fields **and the reasoning annotation** and does `includes` |
| `applyFilters()` | tab + search + each select, in that order, returns a filtered copy |
| `sortRows(rows)` | in-place sort, see 3.4 |
| `renderTabs / renderKPIs / renderBarChart / renderRows / renderReasoning / renderCompare / renderAggTable` | pure render functions, each owns one DOM node |
| `fieldDiv(label, value, classes)` | one reasoning field; renders `(empty - TODO REWRITE)` in grey italic when the field is missing |
| `exportCSV / exportJSON` | Blob + object URL + synthetic `a.click()` download of the CURRENTLY FILTERED rows |
| `render()` | calls every render function; picks the last experiment as the default selection |
| `refresh()` | async: re-fetch JSONL + annotations, `render()`, stamp `#status` with the time |

### 3.3 Type-to-filter — the exact pattern

```js
function searchHit(r, term) {
  if (!term) return true;
  const t = term.toLowerCase();
  const ann = annotations[String(r.experiment_num)] || {};
  const hay = [
    r.description, r.backbone, r.status, r.data_mode,
    ann.diagnosis, ann.citations, ann.hypothesis, ann.prediction,
    ann.verdict, ann.learning,
  ].join(" ").toLowerCase();
  return hay.includes(t);
}

function applyFilters() {
  const term = (document.getElementById("search").value || "").trim();
  const fStatus = document.getElementById("filter-status").value;
  let rows = logs.slice();
  if (active !== "ALL") rows = rows.filter(r => r.backbone === active);
  if (term)   rows = rows.filter(r => searchHit(r, term));
  if (fStatus) rows = rows.filter(r => (r.status || "") === fStatus);
  return rows;
}
```

**The load-bearing detail:** the search haystack includes the **reasoning
annotation text** (diagnosis, citations, hypothesis, prediction, verdict,
learning), so typing an arXiv id or a phrase from a hypothesis finds the
experiment. A search over table cells alone does NOT meet the standard.

### 3.4 Sort — the exact pattern

```js
function sortRows(rows) {
  const dir = sortDir === "asc" ? 1 : -1;
  rows.sort((a, b) => {
    let va = a[sortKey], vb = b[sortKey];
    if (va == null) va = -Infinity; if (vb == null) vb = -Infinity;
    if (typeof va === "string" || typeof vb === "string") {
      return String(va).localeCompare(String(vb)) * dir;
    }
    return (va - vb) * dir;
  });
  return rows;
}
```

Header wiring (re-attached at the end of every `renderRows()`):

```js
document.querySelectorAll("thead th").forEach(th => {
  th.classList.remove("sort-asc", "sort-desc");
  if (th.dataset.sort === sortKey)
    th.classList.add(sortDir === "asc" ? "sort-asc" : "sort-desc");
  th.onclick = () => {
    if (sortKey === th.dataset.sort) sortDir = sortDir === "asc" ? "desc" : "asc";
    else { sortKey = th.dataset.sort; sortDir = "asc"; }
    renderRows();
  };
});
```

Indicators are **CSS pseudo-elements**, not text mutation:
`thead th.sort-asc::after { content: " \25B2"; color: var(--accent); }` /
`thead th.sort-desc::after { content: " \25BC"; }`.

*(Family A does the same job with a single delegated listener on the table and
`e.target.closest('th[data-sort]')`, mutating `h.textContent` to append the
arrow. That variant is more fragile — it rewrites header text — and Family B's
CSS-pseudo-element approach is the one to build to.)*

### 3.5 Event wiring + refresh loop (bottom of script)

```js
document.getElementById("search").addEventListener("input", () => render());
document.getElementById("filter-status").addEventListener("change", () => render());
document.getElementById("reset-btn").onclick = () => { /* clear all state, render() */ };
document.getElementById("export-csv").onclick = exportCSV;
document.getElementById("export-json").onclick = exportJSON;

refresh();
setInterval(refresh, 5000);           // IMAGE / TABULAR: 5 s
// SPY: const REFRESH_MS = 300000;    // 5 min for the main table,
//      60 s / 30 s for the OOS sub-panels
```

Every render is a full re-render from `logs[]`. There is no incremental DOM
patching and no virtual list, even at 166 rows.

---

## 4. STYLING

### 4.1 Where the CSS lives
One `<style>` block in `<head>`. Fully inline. **Zero external stylesheets, zero
webfonts, zero CDN references** in every reference dashboard checked. Verified:
no `<link rel=stylesheet>`, no `cdn.`, no `unpkg`, no `googleapis`.

### 4.2 The palette — GitHub-dark, declared as CSS custom properties

```css
:root {
  --bg:     #0d1117;   /* page background            */
  --fg:     #e6edf3;   /* body text (SPY uses #c9d1d9) */
  --muted:  #8b949e;   /* labels, secondary text     */
  --accent: #58a6ff;   /* headings, links, sort arrows */
  --good:   #3fb950;   /* KEEP / positive            */
  --bad:    #f85149;   /* DISCARD / negative         */
  --mid:    #d29922;   /* CRASH / warning / amber    */
  --card:   #161b22;   /* card + thead background    */
  --border: #30363d;   /* all borders                */
  --hover:  #1f2733;
  --selected: #21314d;
}
```
Additional literals used consistently across repos: `#0d2818` (champion / winner
green-black), `#00d26a` (champion left border), `#fbbf24` (gold, the
winner-metric accent), `#0a0d12` (toolbar / inset background), `#21262d`
(neutral chip), `#0e3a1f` / `#441111` / `#3a330e` (chip backgrounds for
good/bad/warn), `#2c1b53` + `#d2a8ff` (champion chip), `#484f58` (timestamp
grey), `#c779dd` (secondary purple panel).

**It is NOT theme-aware.** No `prefers-color-scheme`, no light/dark toggle,
no `data-theme`. Dark is hard-coded. The only light-themed file in the whole
set is the TABULAR *landing* page (`#fafafa` background, `#0d4a8a` headings) —
its dashboard is dark.

### 4.3 Fonts
```css
body { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
       font-size: 13px; }                                  /* Family B */
body { font-family: 'Segoe UI', system-ui, sans-serif; }    /* Family A */
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
```
System stack only. Numeric comparison cells use
`font-variant-numeric: tabular-nums`.

### 4.4 Table styling (quoted)
```css
table { width: 100%; border-collapse: collapse; font-size: 12px; }
thead th { padding: 6px 8px; border-bottom: 1px solid var(--border); text-align: left;
           color: var(--muted); font-weight: 500; cursor: pointer; user-select: none;
           position: sticky; top: 0; background: var(--card); z-index: 1; }
thead th:hover { color: var(--fg); }
thead th.sort-asc::after  { content: " \25B2"; color: var(--accent); }
thead th.sort-desc::after { content: " \25BC"; color: var(--accent); }
tbody td { padding: 5px 8px; border-bottom: 1px solid var(--border); }
tr.row { cursor: pointer; }
tr.row:hover    { background: var(--hover); }
tr.row.selected { background: var(--selected); }
.table-container { background: var(--card); border: 1px solid var(--border);
                   border-radius: 6px; overflow-x: auto; max-height: 70vh; }
```
Family A adds uppercase 0.75em letter-spaced `th`, and
`#exp-table thead th { position: sticky; top: 0; z-index: 10; }` inside a
`max-height:75vh; overflow-y:auto` wrapper.

### 4.5 Card / chip / field styling (quoted)
```css
.grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 10px; }
.card h3 { margin: 0 0 6px 0; font-size: 11px; color: var(--muted); font-weight: 500;
           text-transform: uppercase; letter-spacing: 0.05em; }
.card .v { font-size: 20px; font-weight: 600; }
.v.good { color: var(--good); } .v.bad { color: var(--bad); } .v.mid { color: var(--mid); }

.pill { display: inline-block; padding: 1px 7px; border-radius: 99px; font-size: 10px;
        background: #21262d; color: var(--fg); }
.pill.kept  { background: #0e3a1f; color: var(--good); }
.pill.disc  { background: #441111; color: var(--bad); }
.pill.champ { background: #2c1b53; color: #d2a8ff; }

.field { background: #0a0d12; border: 1px solid var(--border); padding: 9px 10px;
         border-radius: 5px; white-space: pre-wrap; font-size: 12px; line-height: 1.45;
         max-height: 200px; overflow-y: auto; }
.field.warn { border-color: var(--bad); }
.small { font-size: 11px; color: var(--muted); }
```
`white-space: pre-wrap` on `.field` is how the 7-step reasoning text keeps its
paragraph breaks **without a markdown renderer**.

### 4.6 Emoji
Emoji ARE used liberally in the reference dashboards (section headings, chips,
buttons: chart, target, shield, book, warning, download). This **contradicts**
steeringresearch CLAUDE.md §11 "no emoji unless asked". The local rule wins for
steeringresearch; note the divergence and do not copy the emoji.

---

## 5. CHARTS

**The house standard is NOT PNG.** Zero `<img>` tags and zero PNG files are
referenced by any reference dashboard. Charts are drawn at runtime, two ways:

1. **Inline SVG built as a template string by JS** (Family A, `#detail-chart`):
   `<svg id="detail-chart" width="100%" height="220" viewBox="0 0 900 220" preserveAspectRatio="none">`
   is emptied and refilled with hand-emitted `<line>`, `<rect>`, `<polyline>`,
   `<circle>`, `<text>` and `<title>` (hover tooltip) elements. Implemented
   features: gridlines with axis tick labels, **automatic log-scale when the
   dynamic range exceeds 4x**, alternating fold-band shading with per-fold
   name / date-range / regime labels, a dashed `$1000 investment baseline`
   reference line, the strategy polyline in `--good`, and end-of-fold marker
   dots. Roughly 120 lines of generator code.
2. **Pure-CSS bar chart** (Family B, `#bar-chart`): a flex row of
   `div.bar` elements whose `style.height` encodes the composite, class encodes
   good/mid/bad, `data-tip` drives a `:hover::after` tooltip, and `onclick`
   selects the experiment. No SVG at all.

**Small multiples:** the "many small charts" idea is expressed as the
`.bar-chart` strip (one bar per experiment = one small multiple per run) and as
the aggregate table, not as a grid of separate plot images.

**Storage:** none. There is no `figures/` or `plots/` directory anywhere in the
reference set — nothing to regenerate, nothing to go stale. The one static
binary artifact is `autoresearch_equity.xlsx` (an Excel workbook with embedded
charts) regenerated by `_export_equity_excel.py` and offered as a download.

*Divergence note:* steeringresearch CLAUDE.md §11 mandates "PNG not SVG for
plots". The reference implements runtime SVG/CSS. A build to the house standard
should keep charts self-contained and runtime-generated; if the local PNG rule
is enforced, the PNGs must be produced by a named script and referenced with
relative paths, because inline data-URI PNGs would balloon the file.

---

## 6. RIGOR FURNITURE

### 6.1 What the footer actually contains
The reference footers are **thin** — usage hints plus a timestamp:

- IMAGE dashboard: `Auto-refreshes JSONL + reasoning every 5 s · click column headers to sort · Shift-click rows to compare 2 · Ctrl-F not needed (use search box)`
- TABULAR landing: `Generated by AUTORESEARCHTABULAR. License MIT. Last sync: <span id="sync-ts">—</span>`, filled by `fetch("data.json").then(d => d.generated_utc)`.
- IMAGE landing: build provenance prose — who built it, wall-clock hours, and the statement that *"the reasoning trace (90 KB JSON, every entry arXiv-cited with numeric prediction ranges) is the primary scientific deliverable."*
- SPY: the freshness stamp lives in the **header** (`#last-update` + the pulsing status dot), not the footer.

**Neither the composite fingerprint nor the commit SHA is rendered in any
reference footer.** This is a genuine gap against steeringresearch §11.

### 6.2 Where the fingerprint DOES live
`AUTORESEARCHIMAGE` ships `docs/dashboard/composite_fingerprint.json`:
```json
{ "fingerprint": "bd1e4be21a0249cd",
  "formula": "min(test_ood_auc, val_ood_auc) - 0.1 * abs(id_val_auc - test_ood_auc)" }
```
plus `data_split_audit_fingerprint.json`. The enforcement is at the **runner**,
not the page: the formula string is SHA-256 hashed at runner boot, the hash is
embedded in **every result row**, and the runner refuses to start if the formula
changed silently. The dashboard publishes the fingerprint file as a sibling
artifact but does not currently display it. **The upgrade a new build should
make: fetch `composite_fingerprint.json` and print `formula` + `fingerprint`
in the footer.**

### 6.3 Tier / provenance chips
Status chips exist (`KEEP` / `KEEP/CHAMPION` / `DISCARD` / `CRASH`) and facet
chips exist (`sim` vs `medmnist` vs `wilds` data mode; `sigma<=X` augmentation).
An explicit `SCREENING` / `EVALUATION` chip does **not** exist in any reference.
The closest equivalents:
- the `n seeds` column and `n=${bestMedian.n}` sub-line, which make sample size
  visible wherever an aggregate is quoted;
- the amber `header .warn` chip that permanently labels the whole page
  ("synthetic OOD — not real WILDS-Camelyon17");
- the `data_mode` chip, which distinguishes simulated from real data per row.

### 6.4 CI / uncertainty rendering
- Aggregate table: `mean`, **`std`**, `min`, `max`, `n seeds`, and the explicit
  seed list, so a reader can recompute.
- Headlines state dispersion inline: `0.9220 ± 0.018` with `3-seed median ± std`.
- The SPY transparency block computes CIs client-side and prints them:
  hit-rate `+-2 * 50/sqrt(n_traded)`, Sharpe `+-2 * sqrt((1 + 0.5*S^2)/n) * sqrt(252)`.

### 6.5 The transparency block (SPY "Directive 71") — the strongest rigor artifact
On every row click, six collapsible `details` sub-blocks are built:
1. **Member Roster** — per contributing member: exp#, backbone, seed, train composite, individual realised metrics, weight; with the note *"per-member realised OOS metrics are shown here for inspection — they were NOT used in the selection (selection used train-time metrics only)"*.
2. **Data Sources & Timing** — ticker, OOS window start/end, days available vs days traded (exposure %), feature-count and the exact function that computes them, proxy assumptions, and the compounding formula.
3. **Backtest Assumptions — what was NOT modeled** (heading in red).
4. **Statistical Caveats — read before believing the headline** (heading in amber).
5. **Last 5 trade-days**, loaded live from the per-experiment CSV.
6. **Naive Baselines** — what trivial alternatives would have scored in the same window.

A second block ("Directive 71b") renders five more: **WHAT** (plain-English
narrative), **HOW** (exact formulas at every step), **WHEN** (a causality audit
stating when each input becomes observable), **WHY** (per-metric formula +
intuition + caveat), and **HONEST LIMITS — what you CAN and CANNOT conclude**.

### 6.6 Self-assessment qualifiers
Present as prose, not as a banner component. Examples that ship:
`"methodology demo only · NOT a SOTA claim"`; `"at the modern-ERM frontier, NOT
at SOTA"`; `"⚠️ synthetic OOD — not real WILDS-Camelyon17"` as a permanent
header chip; a `Third-party audit (9/9 PASS)` link where the audit re-derives
every claim from raw artifacts. **No self-graded ACCEPT banner appears
anywhere** — the pattern is a caveat chip plus a link to the audit document.

### 6.7 The reasoning surface
The 7-step entry is a first-class panel, not a tooltip. Rendered fields in
order: **Diagnosis · Citations · Hypothesis · Prediction · Verdict · Learning**.
Missing fields render as `(empty — TODO REWRITE)` in grey italic, and an
annotation flagged `_needs_rewrite` turns every field's border red
(`.field.warn`) and adds a red `(needs rewrite)` marker. **Incompleteness is
displayed, not hidden.**

---

## 7. DATA FLOW — GENERATED OR HAND-WRITTEN?

**The answer is: BOTH, split along a deliberate seam.** This is the single most
important structural fact in the spec.

```
  experiment runner  ──writes──▶  autoresearch_results/
                                    experiment_log.jsonl        (append-only)
                                    best_config.json
                                    reasoning_annotations.json
                                    running.json                (transient)
                                    .composite_fingerprint.json
                                    data_split_audit.{json,md}
                                    dashboard.html   ◀── HAND-WRITTEN, version-controlled
                                          │
                    sync script ──copies──┤
                                          ▼
                                  docs/dashboard/
                                    index.html      (= dashboard.html, renamed)
                                    experiment_log.jsonl
                                    reasoning_annotations.json
                                    ...
                                          │
                       browser ──fetch()──┘   every panel rendered client-side
```

- **The HTML shell is hand-written** and lives in version control. It contains
  zero data. `generalized_ml_autoresearch/core/runner.py:26` states it
  explicitly: *"winners/*, or dashboard.html. Those are Claude's responsibility."*
  The runner never writes HTML.
- **All data is fetched at runtime** from JSON/JSONL siblings. The page cannot go
  stale relative to the data, because it holds none. This is the reference set's
  structural answer to the "artifact that cannot be regenerated from the code
  beside it" defect: the artifact contains no derived numbers at all.
- **The LANDING page IS generated** in TABULAR — `scripts/sync_dashboard_to_docs.py`
  holds the full landing HTML in an `INDEX_HTML` triple-quoted constant and does
  `idx.write_text(INDEX_HTML)`.

### 7.1 Generator / sync scripts, named

| repo | script | what it does |
|---|---|---|
| `AUTORESEARCHIMAGE` | **`scripts/sync_dashboard_to_docs.py`** | declarative `MIRROR` list of `(src, dst)` pairs; `dashboard.html -> docs/dashboard/index.html`; copies log, annotations, best_config, both audit files + both fingerprints, 5 markdown reports; prints `copied:` / `skip (missing):` per file and a final count; idempotent; docstring says run it before every push per the "Dashboard Files Update Mandate". |
| `AUTORESEARCHTABULAR` | **`scripts/sync_dashboard_to_docs.py`** | copies `dashboard/dashboard.html` + `dashboard/data.json` to `docs/`, **writes `docs/index.html` from the embedded `INDEX_HTML` template**, and writes `docs/.nojekyll`. `data.json` itself is written by `scripts/run_campaign.py:351`. |
| `autoresearchindexspy` | **`autoresearchspy/_sync_dashboard_to_docs.py`** | `REQUIRED` / `OPTIONAL` / `PACKAGE_ROOT_DOCS` lists; `dashboard.html -> index.html`; **globs `oos_*.json` and `oos_*.csv`** so new artifacts need no code change; copies `trade_logs/` and **synthesises `trade_logs/manifest.json`** (which experiment CSVs exist + per-ensemble summary stats) so the page can grey out missing links; shells out to `_export_equity_excel.py` to refresh the workbook; prints file count + total MB. |
| `generalized_ml_autoresearch` examples | `examples/<name>/sync_dashboard.py` | same `("dashboard.html", "index.html")` rename pattern, per example project. |
| `autoresearchqqq_local` | `_sync_dashboard_to_docs.py` | same lineage. |

**Every reference repo has a generator/sync script. None ships a
hand-copied `docs/` tree.** The template itself is shared:
`generalized_ml_autoresearch/dashboard/dashboard.html` is copied into each new
example's results dir by `run_example.py`, which is how the design propagated.

### 7.2 The runtime contract a build must satisfy

| file | shape | consumed by |
|---|---|---|
| `experiment_log.jsonl` | one JSON object per line; **flat keys matching the `data-sort` attributes**; must include `experiment_num`, `status`, `description`, `composite`, `timestamp`, `seed`, plus per-axis metrics | the runs table, KPIs, bar chart, aggregate table |
| `reasoning_annotations.json` | `{ "<experiment_num>": { diagnosis, citations, hypothesis, prediction, verdict, learning, _needs_rewrite? } }` — **keys are STRINGS** | reasoning pane, compare panel, search haystack |
| `best_config.json` | champion config + full results | Best Config / Winner panels |
| `running.json` | `{ backbone, description, config{...}, started }`; **absent when idle** — a 404 is the "not running" signal | Currently Running panel |
| `composite_fingerprint.json` | `{ fingerprint, formula }` | (should be) the footer |
| `manifest.json` | index of which per-row detail artifacts exist | disables dead links |

Robustness rules the loaders enforce: `{cache:"no-store"}` or a `?t=Date.now()`
cache-buster on every fetch; `split(/\r?\n/)` so CRLF works; **per-line
try/catch so one bad JSONL line cannot blank the table**, with the bad-line
count surfaced in `#error`; every optional fetch wrapped so a missing file
degrades the panel instead of throwing.

---

## 8. GITHUB PAGES WIRING

- **Serving:** the `docs/` folder on the default branch (`master` for the spy/FX
  lineage, `main` for tabular). No Actions workflow, no `gh-pages` branch.
  Served at `https://<owner>.github.io/<repo>/`.
- **`.nojekyll`** — an empty file at `docs/.nojekyll`. Present in
  `autoresearchindexspy`, `AUTORESEARCHTABULAR`, `AUTORESEARCHIMAGE`.
  TABULAR's sync script writes it every run: `(DOCS/".nojekyll").write_text("")`.
  It is what stops Jekyll from swallowing `_`-prefixed directories such as
  `_forex_reference_dashboard/`.
- **`_config.yml`** — present in `autoresearchindexspy/docs/` and
  `autoresearch/docs/`, absent in TABULAR/IMAGE (which are pure static HTML).
  When present:
  ```yaml
  title: AutoResearch
  description: ...
  theme: jekyll-theme-cayman
  url: https://dlmastery.github.io
  baseurl: /autoresearch
  markdown: kramdown
  highlighter: rouge
  kramdown: { input: GFM, syntax_highlighter: rouge, hard_wrap: false }
  show_downloads: true
  github: { repository_url: ..., repository_nwo: dlmastery/autoresearch, owner_name: dlmastery }
  exclude: [Gemfile, Gemfile.lock, vendor, .bundle]
  ```
  Note `.nojekyll` and `_config.yml` coexist in the spy repo — the `.nojekyll`
  wins, so the `.md` pages are effectively served raw; that is an inconsistency
  in the reference, not a pattern to copy. **Choose one:** either Jekyll (drop
  `.nojekyll`, keep `index.md`) or pure static (keep `.nojekyll`, write
  `index.html`). The newer repos chose pure static.
- **URL layout:** landing at `/`, dashboard at `/dashboard/` (directory index),
  data files as siblings of the dashboard so relative `fetch()` works with no
  base-path configuration. Never fetch across directories.
- **Cache defeat:** the SPY dashboard adds
  `<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">`,
  `Pragma: no-cache`, `Expires: 0` — because GitHub Pages caches aggressively and
  a stale dashboard silently shows old numbers.
- **Build stamp in the title:** `<title>AutoResearch SPY Dashboard (build 20260510-090000 + transparency-always-shown + ensemble_pct)</title>` — the title carries a build tag so you can tell from the browser tab whether the deployed page is the one you just pushed.

---

## 9. CHECKLIST — binary, gradeable assertions

A build meets the house standard iff every line below is TRUE.

### Structure & wiring
1. `docs/.nojekyll` exists and is empty (0 bytes).
2. `docs/index.html` (or `index.md`) exists and is the narrative LANDING page, distinct from the dashboard.
3. The landing page links to the dashboard with a **relative** href.
4. `docs/dashboard/index.html` exists and is the master dashboard.
5. Every data file the dashboard fetches sits in the SAME directory as the dashboard (no cross-directory relative fetches).
6. A named sync/generator script exists (e.g. `scripts/sync_dashboard_to_docs.py`), is idempotent, prints one line per copied file, and prints a `skip (missing)` line rather than crashing on an absent optional file.
7. The sync script renames the source `dashboard.html` to `docs/dashboard/index.html`.
8. Running the sync script twice in a row produces no diff on the second run.

### Self-containment
9. The dashboard HTML contains exactly ONE `<style>` block and ONE `<script>` block, both inline.
10. Zero `<link rel="stylesheet">`, zero external `<script src>`, zero references to any CDN host, zero webfont loads.
11. Zero framework usage (no React/Vue/jQuery/D3/Chart.js/Plotly).
12. Opening the file over `file://` with the data files beside it renders every panel.

### Data flow
13. The HTML contains **no experiment numbers** — every metric shown is fetched at runtime from JSON/JSONL.
14. `experiment_log.jsonl` is parsed line-by-line inside a per-line `try/catch`; a single malformed line does not blank the table, and the bad-line count is displayed.
15. Every fetch uses `{cache:"no-store"}` or a `?t=${Date.now()}` cache-buster.
16. Line splitting uses `/\r?\n/` (CRLF-safe).
17. `reasoning_annotations.json` is keyed by the experiment number **as a string**.
18. A missing optional file (`running.json`, `manifest.json`, `best_config.json`) degrades one panel and never throws.
19. `setInterval(refresh, N)` re-fetches and re-renders on a fixed interval, and the interval value is stated in the visible UI.

### Runs table
20. Every sortable `<th>` carries `data-sort="<exact jsonl field key>"`.
21. Clicking a header sorts; clicking the same header again reverses; the active column shows an up/down indicator.
22. Sorting handles `null` (coerced to `-Infinity`) and strings (`localeCompare`) without throwing.
23. `thead th` is `position: sticky; top: 0` inside a `max-height: 70vh` scroll container.
24. The champion row is computed live as `max(composite)` over rows with non-null composite and non-CRASH status, and receives a distinct background + left border.
25. `status` renders as a `.pill` chip whose variant is derived from the status string, never as bare text.
26. Every null numeric cell renders an em-dash via a shared `fmt()` helper — never blank, never `NaN`.
27. The empty-results state renders an explanatory row naming the likely cause, not an empty tbody.

### Filter & search
28. A `<input type="search">` filters rows on input with no submit step.
29. The search haystack includes the **reasoning annotation text** (diagnosis, citations, hypothesis, prediction, verdict, learning), not just visible table cells.
30. At least one `<select>` facet filter exists, plus a `Reset` button that clears search, all facets, sort, and selection in one click.
31. A live `N of M experiments` count is displayed and updates with the filters.
32. `CSV` and `JSON` export buttons export the **currently filtered** rows via a Blob download.

### Reasoning & rigor
33. Clicking a row renders the 7-step entry with the labels **Diagnosis, Citations, Hypothesis, Prediction, Verdict, Learning** in that order.
34. A missing reasoning field renders a visible `(empty — TODO REWRITE)` placeholder rather than collapsing silently.
35. An annotation flagged `_needs_rewrite` visibly marks every field (red border + marker).
36. Reasoning text preserves paragraph breaks via `white-space: pre-wrap` (no markdown renderer, and no literal `##`/`**`/`|---|` visible on the page).
37. Every aggregated number is accompanied by its sample size (`n seeds` / `n=`), and the aggregate table reports mean **and** std **and** min **and** max **and** the seed list.
38. `composite_fingerprint.json` (formula + SHA) is published beside the dashboard **and its `formula` and `fingerprint` are rendered in the footer**.
39. The footer states the generated/last-sync timestamp and the commit SHA.
40. Any headline claim carries an explicit scope caveat in the page itself (a permanent `.warn` header chip and/or an inline "NOT a SOTA claim"-style qualifier); no self-graded ACCEPT banner appears without the "Internal QA pass — external review pending" qualifier.
41. Absolute links to source go to `https://github.com/<owner>/<repo>/blob/<branch>/<path>` and resolve (HEAD-tested).

### Presentation
42. The palette is declared as `:root` custom properties using the GitHub-dark values (`--bg:#0d1117`, `--card:#161b22`, `--border:#30363d`, `--accent:#58a6ff`, `--good:#3fb950`, `--bad:#f85149`, `--mid:#d29922`, `--muted:#8b949e`).
43. Fonts are system stacks only; numeric comparison cells use `font-variant-numeric: tabular-nums`.
44. Charts are self-contained and runtime-generated (inline SVG built by JS, or CSS-height bars) — no external image requests.
45. There is a per-experiment visual strip (one bar per run) that is click-linked to row selection.
46. No emoji in the steeringresearch build (the reference uses them; the local §11 rule overrides).

### Known gaps in the reference — decide explicitly
47. Per-hypothesis sub-dashboards (`ideas/<NN>/dashboard/index.html`) and per-experiment pages (`experiments/expNNN.html`) do **not** exist in any reference; the reference uses an in-page detail panel. A build that wants the three-tier hierarchy of steeringresearch §11 is **extending** the standard, not matching it — and must then also generate those pages from data with the same no-embedded-numbers rule.
48. `SCREENING` / `EVALUATION` tier chips do **not** exist in the reference; the nearest equivalent is the `n seeds` column plus a permanent scope chip in the header. Adding them is an extension.

---

*Compiled from: `autoresearchindexspy/autoresearchspy/docs/` (spy_dashboard/index.html, index.md,
_forex_reference_dashboard/index.html, _config.yml, autoresearchspy/_sync_dashboard_to_docs.py);
`AUTORESEARCHIMAGE/docs/` + `scripts/sync_dashboard_to_docs.py`;
`AUTORESEARCHTABULAR/docs/` + `scripts/sync_dashboard_to_docs.py`;
`autoresearch/docs/`; `autoresearchqqq_local/docs/`;
`steeringresearch/CLAUDE.md` §11 (rules only). Read-only; nothing was modified.*

