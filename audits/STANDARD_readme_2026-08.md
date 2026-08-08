# SPEC — Autoresearch top-level README house standard

Derived from (READ ONLY):
- PRIMARY: `C:\Users\evija\autoresearchindexspy\autoresearchspy\README.md` (+ `CLAUDE.md`, `docs/`)
- `C:\Users\evija\autoresearch\README.md`
- `C:\Users\evija\AUTORESEARCHTABULAR\README.md`
- `C:\Users\evija\AUTORESEARCHIMAGE\README.md`
- `C:\Users\evija\autoresearchqqq_local\README.md`

Status: COMPLETE — sections 0–8 + CHECKLIST (45 gradeable assertions).

---

<!-- SECTIONS APPENDED BELOW -->

## 0. Reference inventory + line budget (raw numbers)

| repo | README lines | shape | notes |
|---|---:|---|---|
| `autoresearchindexspy/autoresearchspy` (PRIMARY) | 967 | full manual | near-verbatim descendant of `autoresearch` (966 lines); the two differ only in module name (`autoresearchspy` vs `autoresearch`) and instrument |
| `autoresearch` | 966 | full manual | the ancestor template |
| `AUTORESEARCHIMAGE` | 763 | rigor-forward campaign report | the most *epistemically* disciplined of the set |
| `AUTORESEARCHTABULAR` | 217 | lean protocol card | protocol + gates only, no results yet |
| `autoresearchqqq_local` | 150 | lean status card | headline + layout + status + citations |

**Two legitimate shapes exist in the house style.** Both are in-family; do not
force a young repo into the 900-line shape.

- **LONG form (760–970 lines)** — a program with a defended champion and a
  finished campaign. spy / autoresearch / IMAGE.
- **SHORT form (150–220 lines)** — a program whose campaign is in flight or
  whose contribution is the protocol. TABULAR / QQQ.

The SHORT form is a strict subset: badges → thesis → live-dashboard link →
headline-result table → repo layout → quick start → methodology/gates →
status table → citations → provenance → license. It never drops the
headline table, the gates, or the citations.

---

## 1. Section arc — ordered, with REQUIRED / OPTIONAL marking

Heading text below is **verbatim** from the references. `R` = appears in
most/all references (REQUIRED). `O` = appears in one (OPTIONAL).

| # | Heading (verbatim, pick the variant that fits) | R/O | Appears in |
|---:|---|:--:|---|
| 1 | *(H1 title line)* `# AUTORESEARCHIMAGE` / `# AutoResearch QQQ — Nasdaq-100 Index/Stock Autoresearch Loop` / `# AUTORESEARCHTABULAR — Higgs UCI tabular benchmark`, or the centered `<p align="center"><h1 align="center">AutoResearch · SPY</h1>` block | R | all 5 |
| 2 | *(badge row — no heading)* | R | spy, autoresearch, TABULAR, QQQ (4/5) |
| 3 | *(blockquote thesis — no heading)* `> **An autonomous ML research loop for …**` | R | IMAGE, QQQ, TABULAR (prose form) |
| 4 | `## 🌐 Live links` / `## Live dashboard` | R | IMAGE, QQQ; spy carries it as a badge + `## Dashboard` late section |
| 5 | `## ⚠️ Read this first — what's real vs. what's synthetic` | **O but high-value** | IMAGE only — the single most distinctive rigor element in the set |
| 6 | `## Quick stats` / `## Headline result (post-exp 216)` / `## Champion Model Results` | R | IMAGE, QQQ, spy, autoresearch |
| 7 | `## Table of contents` / `## Table of Contents` | R **in LONG form only** | spy, autoresearch, IMAGE (all 3 long ones); absent in both short ones |
| 8 | `## Highlights` | O | spy, autoresearch |
| 9 | `## What this is` / `## What this repo contains` | R | IMAGE, TABULAR |
| 10 | `## Why MedMNIST PathMNIST + blur OOD?` / `## Why Higgs?` — i.e. **`## Why <dataset>?`** | R | IMAGE, TABULAR |
| 11 | `## Quickstart` / `## Quick Start` / `## Running the campaign` / `## Quick start` | R | all 5 |
| 12 | `## The autoresearch protocol` / `## Key Innovation: Claude Code as the Research Agent` / `## The Agent Loop` / `## Key methodology` | R | all 5 |
| 13 | `## The three gates` / `## Triple-check data-split audit` + `## Citation Rigor & Reasoning Blob Completeness` | R | IMAGE, TABULAR |
| 14 | `## Goodhart-fingerprinted composite metric` / `## Composite metric (fingerprinted)` / `### Composite Score` | R | all 5 (QQQ inline under `## Key methodology`) |
| 15 | `## Repo layout` / `## Repository layout` / `## Project Structure` / `## What this repo contains` | R | all 5 — always a fenced ASCII tree with `#` end-of-line comments |
| 16 | `## Architecture` (+ `### <Champion model>`, `### Champion Configuration`, `### Available Backbones`) | O | spy, autoresearch |
| 17 | `## Data Pipeline` (+ `### Instruments`, `### Feature Engineering (104 Features)`, `### Targets`) | O | spy, autoresearch |
| 18 | `## Evaluation Framework` (+ `### Super-Fold Design`, `### Data Integrity Guarantees`, `### Metrics`, `### Composite Score`) | O | spy, autoresearch |
| 19 | `## Uncertainty Estimation` | O | spy, autoresearch |
| 20 | `## The 18-experiment campaign` / `## Experiment History` / `## Backbone status (216+ experiments)` | R | IMAGE, spy, autoresearch, QQQ |
| 21 | `## Three central findings` / `### Key Discoveries` | R | IMAGE, spy, autoresearch |
| 22 | `## How to reproduce` | R (folded into Quickstart in short form) | IMAGE, spy (`### Run the Champion`) |
| 23 | `## CLI Reference` | O | spy, autoresearch |
| 24 | `## Production deployment guide` | O | IMAGE |
| 25 | `## Hardware notes` / `## Hardware contract` / (QQQ: inline under `## Provenance`) | R | IMAGE, TABULAR, QQQ |
| 26 | `## Limitations & threats to validity` | **O but high-value** | IMAGE only |
| 27 | `## Open axes for the next campaign` / `## Phase D / E roadmap (per CLAUDE.md)` | R | IMAGE, QQQ |
| 28 | `## Citations` / `## References` / `## Citations (top backbone papers)` | R | all 5 |
| 29 | `## Dependencies` | O | spy, autoresearch |
| 30 | `## Dashboard` | O | spy, autoresearch |
| 31 | `## Contributing` (+ `### Running the Test Suite`, `### Adding a New Backbone`, `### Experiment Protocol`) | O | spy, autoresearch |
| 32 | `## Provenance` | O | QQQ |
| 33 | `## License` / `## License & credits` | R | all 5 |

**Ordering invariant (the arc):** identity → proof-of-liveness (badges +
dashboard link) → honesty caveat → headline numbers → navigation (TOC) →
what/why → how to run → protocol/gates → composite → layout → results →
findings → reproduction → limits → roadmap → citations → license.
Numbers come **before** methods; methods come **before** code layout;
limitations come **after** findings and **before** citations.

---

## 2. The opening — first ~40 lines

Two sanctioned openings.

### 2a. PRIMARY (spy / autoresearch): centered HTML masthead + badge row

Verbatim, `autoresearchspy/README.md` lines 1–23:

```html
<p align="center">
  <h1 align="center">AutoResearch · SPY</h1>
  <p align="center">
    <strong>Autonomous S&amp;P 500 ETF (SPY) Prediction Optimization</strong>
  </p>
  <p align="center">
    An AI-driven machine learning research system for SPY (S&amp;P 500 ETF) directional return prediction,<br>
    powered by a Karpathy-style experiment loop where Claude Code acts as the researcher.<br>
    Three causally-anchored feature streams: <em>daily yfinance</em> + <em>Asian/European pre-market block</em> + <em>Barchart hourly intraday</em>.
  </p>
  <p align="center">
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
    <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-2.5%2B-ee4c2c.svg" alt="PyTorch 2.5+"></a>
    <a href="#license"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
    <a href="https://github.com/dlmastery/autoresearch"><img src="https://img.shields.io/badge/experiments-104-orange.svg" alt="104 Experiments"></a>
    <a href="https://dlmastery.github.io/autoresearch/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg" alt="GitHub Pages"></a>
    <a href="#champion-model-results"><img src="https://img.shields.io/badge/test%20Sharpe-+6.21-brightgreen.svg" alt="Test Sharpe +6.21"></a>
    <a href="#champion-model-results"><img src="https://img.shields.io/badge/total%20return-+1%2C001%25-brightgreen.svg" alt="Total Return +1,001%"></a>
    <a href="#champion-model-results"><img src="https://img.shields.io/badge/positive%20folds-7%2F7-brightgreen.svg" alt="7/7 Folds Positive"></a>
  </p>
</p>

---
```

Anatomy: **title → bold one-line thesis → 2–3-line "what this is" with the
method named ("Karpathy-style experiment loop where Claude Code acts as the
researcher") → badge row → `---`.**

**Badge row composition (the house pattern):** 3 infrastructure badges
(python / framework / license) + 3 *result* badges that deep-link to
in-document anchors (`#champion-model-results`) + 1 experiment-count badge
+ 1 GitHub-Pages badge. Result badges carrying live numbers is the
distinguishing habit — badges are not decoration, they are the headline.

### 2b. LEAN (IMAGE / QQQ / TABULAR): H1 + blockquote thesis + live links

Verbatim, `AUTORESEARCHIMAGE/README.md` lines 1–16:

```markdown
# AUTORESEARCHIMAGE

> **An autonomous ML research loop for medical-imaging out-of-distribution
> classification.** A Karpathy-style experiment loop where Claude Code is
> the researcher: it diagnoses, cites the literature, hypothesizes, predicts,
> runs one experiment at a time, analyses, checkpoints — for 18 experiments
> straight.

## 🌐 Live links

- **📊 Dashboard:** [dlmastery.github.io/autoresearchimage/dashboard/](https://dlmastery.github.io/autoresearchimage/dashboard/) — sortable / filterable / searchable; click any of the 21 experiments for arXiv-cited reasoning
- **📖 Pages landing page:** [dlmastery.github.io/autoresearchimage](https://dlmastery.github.io/autoresearchimage/)
- **📑 Real WILDS 3-seed report:** [→](https://dlmastery.github.io/autoresearchimage/dashboard/real_wilds_3seed_report.md)
- **🔍 Third-party audit (9/9 PASS):** [→](https://dlmastery.github.io/autoresearchimage/dashboard/third_party_audit.md)
- **📚 Research journal:** [→](https://dlmastery.github.io/autoresearchimage/dashboard/research_journal.md)
- **🔬 Top-3 finalized winners:** [→](https://dlmastery.github.io/autoresearchimage/dashboard/top3_finalized_comparison.md)
```

The blockquote thesis is a **fixed two-sentence template**:
sentence 1 = *"An autonomous ML research loop for `<domain>`."* in bold;
sentence 2 = *"A Karpathy-style experiment loop where Claude Code is the
researcher: it diagnoses, cites the literature, hypothesizes, predicts, runs
one experiment at a time, analyses, checkpoints — for `<N>` experiments
straight."*

QQQ's variant (lines 3–9) shows the badge row and blockquote can be stacked:

```markdown
[![Dashboard](https://img.shields.io/badge/dashboard-live-success)](https://dlmastery.github.io/autoresearchindexstock/dashboard/)
[![Experiments](https://img.shields.io/badge/experiments-216%2B-blue)](./autoresearch_results/experiment_log.jsonl)
[![Backbones](https://img.shields.io/badge/backbones%20complete-5%2F6-brightgreen)](./autoresearch_results/winners/)

> **Top-level project** spawned from `dlmastery/autoresearch` (FX) for the
> equity-index variant. Self-contained successor; FX project remains at the
> parent repo.
```

### 2c. The honesty block (IMAGE, lines 18–79) — the highest-leverage optional

Immediately after the live links, **before any result**:

```markdown
## ⚠️ Read this first — what's real vs. what's synthetic

**The campaign has TWO sets of results.** Read them separately:

| | scope | headline |
|---|---|---|
| **exps 1–18** (synthetic-blur PathMNIST) | engineered task — binary tumor + Gaussian-blur OOD on a 5 MB MedMNIST subset | composite **0.9966** ≠ comparable to anything in the literature |
| **exps 19–21** (real WILDS-Camelyon17) | the real cross-hospital benchmark Koh 2021 ICML defined | test_ood AUC **0.9220 ± 0.018** (3-seed) vs Koh 2021's 0.853 ± 0.020 — **+0.073, recipe-attributable** |
```

…followed by two explicitly headed lists:

```markdown
**What this campaign actually demonstrates:**
1. …
**What this campaign does NOT demonstrate:**
- …
```

This is the pattern a non-conforming README most often lacks: an
above-the-fold, table-formatted statement separating the defensible claim
from the engineered one, plus a literal *does NOT demonstrate* list.

---

## 3. Results presentation

### 3a. Table shapes

Four canonical result-table shapes appear. Use all four in a LONG-form
README; at minimum the first in a SHORT-form one.

**(i) Headline / champion key-value table.** Two columns, right-aligned
value, every value bolded. `spy` lines 163–176 (verbatim, truncated):

```markdown
| Metric | Value |
|:-------|------:|
| **Test Sharpe Ratio** | **+6.21** (annualized) |
| **Composite Score** | **+5.50** |
| **Total Return** | **+1,001%** ($1,000 --> $11,011) |
| **PSR** | **1.0000** (statistically significant) |
| **Positive Folds** | **7 / 7** (all regimes profitable) |
| **Training Time** | **~36 seconds** (CPU) |
| **Trainable Parameters** | **301,196** |
```

QQQ's variant adds a third `Notes` column carrying the provenance of the
number (`mamba dmamba exp 52 (single-seed=42)`) — **strictly better**,
because it forces seed/experiment attribution into the headline itself:

```markdown
| Metric | Value | Notes |
|---|---:|---|
| **Global champion composite** | **+1.3216** | mamba dmamba exp 52 (single-seed=42) |
| Champion test folds | 7/7 positive | F1-F7 all positive |
| Buy-and-hold baseline | +0.87 Sharpe | strategy excess +0.45 |
```

Note the **baseline row inside the headline table** — the champion is never
quoted without the thing it beats.

**(ii) The full campaign table — one row per experiment.** IMAGE lines
394–413. A row is ONE runner invocation. Column set:
`# | backbone | data | aug | seed | composite | <primary metric> | <secondary
metrics…> | <gap metric> | <calibration metric> | role`.
Champion/landmark rows are **bolded cell-by-cell** (the `#`, the config
cells, and the composite), and the final `role` column is a plain-English
label of *why that row exists* — including failures:

```markdown
| # | backbone | data | aug | seed | composite | test_ood | val_ood | id_val | id_ood gap | ECE_ood | role |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sim_tiny | sim | — | 0 | 1.0000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.276 | pipeline smoke |
| 7 | ConvNeXt-T | medmnist | — | 42 | 0.9526 | 0.957 | 0.996 | 0.999 | 0.043 | 0.085 | seed luck check (failed prediction!) |
| **11** | **ConvNeXt-T** | **medmnist** | **σ ≤ 2.5** | 0 | **0.9973** | **0.998** | **1.000** | 0.999 | **0.002** | **0.014** | **breakthrough** |
| **18** | **EffNet-B0** | **medmnist** | **σ ≤ 2.5** | 99 | **0.9971** | 0.997 | 0.999 | 0.999 | 0.002 | 0.014 | **production-frontier 3-seed champion** |
```

`role` values seen: `pipeline smoke`, `seed-stability check`,
`LR sensitivity (1e-4)`, `first real-medical baseline`,
`seed luck check (failed prediction!)`, `3-seed median locked`,
`breakthrough`, `aug is arch-agnostic`, `production-frontier 3-seed champion`.

**(iii) Per-fold / per-regime breakdown.** One row per evaluation window,
centre-aligned index, right-aligned metrics, plus a **`Key observations:`
bullet list underneath that names the WORST fold explicitly.** spy 182–196:

```markdown
| Fold | Period | Regime | Sharpe | Return | Win Rate | IC | Sortino | Max DD |
|:----:|:------:|:-------|-------:|-------:|---------:|----:|--------:|-------:|
| 2 | 2009-2010 | Post-crash recovery | +1.17 | +5.5% | 53.3% | +0.08 | +2.02 | 3.47% |
| 4 | 2014-2016 | Strong USD downturn | +9.78 | +90.3% | 75.5% | +0.67 | +19.42 | 1.81% |
```
> - Fold 2 (post-crash recovery, 2009-2010) is the hardest regime -- still profitable at +1.17 Sharpe

**(iv) Cross-seed reproducibility table** — mandatory before any champion
claim, with a **`| **Median** |` row**, not a mean. spy 202–207:

```markdown
| Seed | Composite | Test Sharpe | Val Sharpe | Positive Folds |
|-----:|----------:|------------:|-----------:|:--------------:|
| 0 | +5.50 | +6.21 | +5.60 | 7/7 |
| 42 | +4.45 | +4.69 | -- | 6/7 |
| 99 | +4.46 | +4.76 | -- | 6/7 |
| **Median** | **+4.46** | **+4.76** | | |
```

### 3b. How n / tier / CI are chipped

The house style does **not** use a literal `n=` column or a `SCREENING`/
`EVALUATION` chip in the README (those live in the dashboard). It carries
the same information **inline in the number's own cell or its label**:

- `**0.9966** on this synthetic OOD (3-seed median, std 0.00065)`
- `test_ood AUC **0.9220 ± 0.018** (3-seed)`
- `dmamba 4-seed -0.25 (seed=99 catastrophe)`
- `exp 95 +0.61 (single-seed luck)`
- `5-seed median +0.43, 3-seed median +0.52`
- column headers that *are* the tier: `Best multi-seed median | Best single-seed`

**Rule extracted:** every headline number is followed, in the same cell, by
`(<k>-seed median|mean, std <x>)` or `± <sd> (<k>-seed)`. A single-seed
number is explicitly labelled `single-seed` and, where it was luck, says so
(`single-seed luck`, `seed=99 catastrophe`). **No bare number is ever the
headline.**

### 3c. Champion highlighting

- Bolded cells in the campaign table (whole row, cell by cell).
- A dedicated `### Champion Configuration` JSON block (spy 301–318) followed
  by a **per-parameter justification table** — `| Parameter | Value |
  Justification |` — where every justification names a paper
  (`follows Gu, Kelly & Xiu (2020) capacity guidance`).
- A **champion-lineage ASCII ladder** with the delta on each arrow
  (IMAGE 417–427):

```
exp4 sim_tiny medmnist 0.8709
   ↓ +0.086 (ImageNet transfer)
exp5 ResNet50           0.9571
   ↓ +0.022 (matched-corruption augmentation)
exp11 ConvNeXt-T+blur   0.9973   ← 3-seed median (locked at exp13)
   ↓ -0.0007 (5x cheaper backbone, essentially tied)
exp16 EffNet-B0+blur    0.9966   ← 3-seed median (locked at exp18) — production champion
```

### 3d. Negative results

Kept, named, and given equal typographic weight:

- `(not measured)` and `—` are written literally into result tables rather
  than omitting the row (IMAGE 448–453).
- Failed predictions are labelled in the `role` column:
  `seed luck check (failed prediction!)`.
- QQQ's backbone table headlines the *bad* multi-seed medians next to the
  good single-seed numbers: `dmamba 4-seed -0.25 (seed=99 catastrophe) |
  exp 52 +1.32 (champion)` — the champion and its own failure to replicate
  sit in the same row.
- `## Experiment History` phases include the ones that lost:
  `Het-loss adds variance instability, hurts mean prediction on small data`.
- Explicit standing sentence: *"Every artifact is **append-only**. Negative
  results are kept. The experiment log is the project's institutional
  memory."* (IMAGE 255–256)

---

## 4. Rigor furniture — the standing disclosure blocks

### 4a. Composite formula + SHA-256 fingerprint (REQUIRED, all 5 repos)

Gets its **own `##` section**, positioned after the gates and before the repo
layout. Fixed three-part shape: (1) fenced formula, (2) one paragraph on what
each term prices, (3) the fingerprint sentence naming the file and the
exception class. IMAGE 324–341, verbatim:

> ## Goodhart-fingerprinted composite metric
>
> The composite formula is
>
> ~~~
> composite = min(test_ood_auc, val_ood_auc) − 0.1 × |id_val_auc − test_ood_auc|
> ~~~
>
> It penalizes both **the worst OOD AUC** (the `min` term) and **the gap
> between in-distribution AUC and OOD test AUC** (the absolute-difference
> term). A model can't game one fold at the expense of another.
>
> `core/evaluation/composite.py` hashes the formula string with SHA-256 on
> first run and stores it in `.composite_fingerprint.json`. Every
> subsequent run verifies the hash matches; mid-project rewrites raise
> `CompositeFingerprintError`. **Cross-experiment composite comparability is
> a contract, not a convention.**

TABULAR's variant (163–174) adds the fingerprint *file path*
(`autoresearch_results/composite.fingerprint`) and the phrase
"embedded in every result row".

**Note:** the reference READMEs state the fingerprint mechanism and the file
path but do **not** print the hash literal itself in the README. The hash
lives in the dashboard footer and in the result rows.

### 4b. The gates block (REQUIRED)

Either as one `## The three gates` section (TABULAR 97–160) or as three
consecutive `##` sections (IMAGE 260–322). Every gate is documented with:
its code path in backticks, an enumerated/tabulated list of its checks, the
artifact files it writes, **and the phrase "There is no bypass flag."**

The single most important habit here: **each gate section names a real bug
the gate actually caught.**

> The audit caught a real bug during bootstrap: the SIM dataset's slide-level
> disjointness was violated because train and id_val were drawing from the
> same hospital pool with overlapping `slide_id`s. The fix was a one-line
> namespace offset … — exactly what the audit is for. *(IMAGE 289–293)*

> During this campaign **exp12 was caught and rejected** at 76 words
> multi-paper citations (floor 80). The Reasoning Blob Completeness gate
> fired exactly as designed; we extended the citations to 108 words and
> reran. *(IMAGE 312–315)*

A gate with no caught-bug anecdote reads as decorative.

### 4c. Word-floor table for the reasoning blob (REQUIRED where the gate exists)

Rendered as a table, not prose. Two variants — TABULAR 147–155
(`| Section | Min words | What goes there |`) and IMAGE 302–310
(`| field | minimum | what it must contain |`). Both state the pre-run vs
post-run asymmetry explicitly ("Pre-run: only the first 5 sections are
required. Post-run: all 7.").

### 4d. Data-split fingerprint invalidation clause (REQUIRED where a split audit exists)

TABULAR 122–125, verbatim:

> The fingerprint file is a hash of the union of train/val/test row indices.
> **Every experiment row records this fingerprint** — if it ever changes,
> every prior leaderboard row is invalidated by definition.

### 4e. Seed / tier disclosure

There is **no `SCREENING`/`EVALUATION` chip vocabulary** in these READMEs.
The equivalent furniture is:
- the cross-seed table with a `**Median**` row (§3a-iv);
- the inline `(k-seed median, std x)` suffix on every headline number;
- an explicit floor statement in Limitations:
  *"**3 seeds is the floor, not the ceiling.** Bouthillier 2021 MLSys
  recommends 5+ seeds for precise comparisons. Our 3-seed median is
  defensible at the 1.5 σ level for some comparisons."*

### 4f. Self-grading / external-review qualifier

The literal string "Internal QA pass — external review pending" does **not**
appear in any reference. The functional equivalents that DO appear, and which
a conforming README must carry at least one of:
- a linked **third-party audit** with its pass count in the link text:
  `**🔍 Third-party audit (9/9 PASS):**`;
- a **self-audit script + count**: `> Reasoning entries passing all gates: **18/18**`
  with the script named (`publish_quality_audit.py`);
- a **negative comparability row inside the stats table**:
  `| **Comparable to WILDS leaderboards?** | **NO** — see caveats above |`;
- an explicit frontier-not-SOTA sentence:
  *"On real WILDS we are at the **modern ERM frontier**, NOT a SOTA claim:
  methods specifically designed for OOD … push 0.93–0.97 … We did not run
  those."*

### 4g. Limitations & threats to validity (high-value; IMAGE only)

A `##` section of 5–7 bullets placed **after findings/reproduction, before
citations**. Each bullet: **bolded one-phrase name** → why it limits the
claim → what would fix it, with a citation where one exists (IMAGE 648–652):

> - **Single dataset.** All 18 experiments are on PathMNIST. The campaign
>   asserts cross-architecture generalization but not cross-dataset.
> - **Single corruption family.** We tested Gaussian blur. Hendrycks 2019
>   shows that training on one corruption family transfers partially to
>   others (≈ 50 % gain), but our campaign has no direct evidence on this.

### 4h. Falsifier / prediction furniture

Predictions are surfaced two ways, neither as a dedicated section:
1. inside the protocol section as a **worked example with numbers**:
   *"**Predict** the numeric outcome range on the composite plus at least one
   sub-metric (e.g., `test_ood_auc` from 0.961 to 0.985 ± 0.008)."*
2. as a `role`-column label when a prediction failed:
   `seed luck check (failed prediction!)`.

A per-claim falsifier statement is **absent** from all five references.

### 4i. `[NEEDS VERIFICATION]` / `[UNVERIFIED]` markers

**Absent** from all five reference READMEs. The house analogue is the literal
`(not measured)` / `—` cell in result tables and the `*(this repo)*` /
`— 350 experiments planned` status qualifier on unfinished work.

### 4j. Commit SHA

**Not carried in the README** in any reference. Provenance is carried instead
by `## Provenance` (fork point + date + experiment number, QQQ 138–146) and
the `## License & credits` closing paragraph naming the agent, the model, the
date, and the git URL that pins it (IMAGE 756–763).

---

## 5. Links

### 5a. Link classes and their form

| target | form | example |
|---|---|---|
| GitHub Pages dashboard | **absolute https**, always | `https://dlmastery.github.io/autoresearchindexstock/dashboard/` |
| sibling autoresearch repos | **absolute https** to github.com | `[autoresearch](https://github.com/dlmastery/autoresearch)` |
| files in THIS repo | **relative** | `docs/paper.md`, `LICENSE`, `./autoresearch_results/experiment_log.jsonl` |
| files in ANOTHER repo | **absolute blob URL** | `https://github.com/dlmastery/autoresearch/blob/master/generalized_ml_autoresearch/templates/SECTION_MAPPING.md` |
| within this README | **anchor** | `[*Open axes for the next campaign*](#open-axes-for-the-next-campaign)` |
| badges | link every badge to something real — an anchor, a Pages URL, or an in-repo artifact | `[![Experiments](…)](./autoresearch_results/experiment_log.jsonl)` |

### 5b. The live-links block (the "link table")

The house form is a **bulleted link block directly under the thesis**, one
line per artifact, with **bolded label + emoji marker + a trailing em-dash
gloss saying what the reader will find there** (IMAGE 9–16). Six links is the
observed size. It always includes: dashboard, Pages landing page, research
journal, and at least one audit/report artifact.

QQQ's minimal form is a `## Live dashboard` section containing the bare URL
in bold on its own line plus a two-sentence gloss of what it tracks.

### 5c. Cross-project link list

TABULAR 15–23: a numbered list positioning this repo within the series, each
entry carrying repo link + domain + headline composite + experiment count +
dashboard link, with the current repo marked `*(this repo)*`.

### 5d. Ledger / findings files

Linked from the **repo-layout tree** (as `#` comments on the tree lines)
rather than from a prose paragraph — `experiment_log.jsonl`,
`best_config.json`, `reasoning_annotations.json`, `research_journal.md`,
`experiment_summary.md`, `publish_quality_audit.md`, `winners/`. The layout
tree is therefore load-bearing documentation, not decoration.

---

## 6. Reproduction section

Two required surfaces.

**(i) `## Quickstart` — numbered, comment-led, one fenced block.** Every step
is a numbered `#` comment inside the fence, and the mandatory gate is called
out in the comment itself. TABULAR 179–194 verbatim:

> ~~~bash
> # 1. install
> pip install -e .
>
> # 2. download (~2.8 GB; one-time)
> python scripts/download_higgs.py
>
> # 3. audit the split (must pass before any experiment)
> python -m core.evaluation.audit --config configs/higgs.yaml --triple-check
>
> # 4. run one experiment (recipe id from sota_catalog.yaml)
> python -m core.runner --config configs/higgs.yaml --recipe lightgbm_default
>
> # 5. or: run the full 350-experiment campaign
> python scripts/run_campaign.py --config configs/higgs.yaml
> ~~~

IMAGE 194–195 prefixes the block with the tested environment:
> Tested on Python 3.12.3, PyTorch 2.6.0+cu124, Windows 11, NVIDIA RTX 4090 Mobile (16 GB).

**(ii) `## How to reproduce` / `### Run the Champion` — the exact champion
command with every flag written out**, followed by an **expected-output
block**. spy 641–668 (condensed, verbatim text preserved):

> ### Run the Champion
>
> ~~~bash
> python -m autoresearchspy.run_autoresearch \
>     --backbone mlp --lr 5e-4 --batch-size 32 --seq-len 10 --epochs 50 \
>     --weight-decay 1e-5 --patience 10 --grad-clip 1.0 \
>     --huber-delta 0.5 --head-dropout 0.15 --seed 0 \
>     --description "champion run"
> ~~~
>
> Expected output:
> - Training: ~36 seconds on CPU
> - Test Sharpe: +6.21
> - Composite: +5.50
> - All 7 folds positive
>
> Results are saved to:
> - `autoresearch/autoresearch_results/experiment_log.jsonl` (appended)
> - `autoresearch/autoresearch_results/best_config.json` (overwritten if new champion)

IMAGE 508–529 wraps the same in a `for SEED in 0 42 99; do … done` loop —
**the reproduction command reproduces the multi-seed result, not one seed** —
and states per-seed wall-clock (`≈ 2–3 min on an RTX 4090 Mobile`).

**(iii) Resume-the-agent instructions (REQUIRED).** spy 690–698: a numbered
list of exactly what a fresh Claude Code session reads, in order, to continue
the loop (`CLAUDE.md` → `memory/…_checkpoint.md` → tail of
`experiment_log.jsonl` + `best_config.json` → start dashboard → resume).

**(iv) Hardware note (REQUIRED)** — its own `## Hardware notes` /
`## Hardware contract` section, a bullet list of hard constraints each with
its *reason*: VRAM cap, precision policy, CPU-core pinning with the WHEA
justification, determinism seeding, and named override env vars.

---

## 7. Tone and hard rules (as practised in the references)

1. **Emoji ARE used**, sparingly, in two places only: as a single leading icon
   on a `##` heading (`## 🌐 Live links`, `## ⚠️ Read this first`,
   `## 🧬 Generalized ML AutoResearch`, `## 📄 Paper & Article`) and as bullet
   markers in the live-links block (`**📊 Dashboard:**`). Never inside tables
   (except `✓` as a completion mark), never in body prose.
   *Divergence flag:* `steeringresearch/CLAUDE.md` §11 says "no emoji unless
   asked" — the sibling repos' house standard permits heading icons. Surface
   this conflict to the user rather than silently picking a side.
2. **Heading depth stops at `###`.** No `####` in any reference.
3. **`---` horizontal rule between every top-level section.** Universal, 5/5.
4. **Table over prose, always.** Any enumeration of ≥3 items with ≥2
   attributes is a table — parameter justifications, gate checks, metrics,
   dependencies, instruments, backbones, hardware.
5. **Numeric columns right-aligned** (`|---:|`), label columns left-aligned
   (`|:---|`), index/flag columns centred (`|:--:|`). Alignment markers are
   used deliberately, not defaulted.
6. **Fenced ASCII diagrams instead of images.** Architecture, the agent loop,
   the super-fold split, the champion lineage, and the repo tree are all
   ASCII/box-drawing inside fences. Zero embedded image files in any
   reference README; badges are the only `<img>`.
7. **Bold carries meaning:** a headline number, a champion row, a named
   concept on first use, or a warning. Not general prose emphasis.
8. **Numbers are always attributed in-place** — never a bare figure without
   its seed count, its baseline, or its source experiment id.
9. **Claims are hedged with the specific untested thing, in the same
   sentence:** *"is production-cost-frontier-best for *this synthetic shift on
   this dataset*"*; *"**This is a replication, not novelty.**"*
10. **Every method mention carries its paper inline** — `(He et al., 2016)`,
    `per Hendrycks & Dietterich 2019 ICLR`, `follows Gu, Kelly & Xiu (2020)
    capacity guidance` — including inside tables.
11. **Unicode is free in markdown** (σ, ×, ≈, ≥, ±, ↓, ←, —, ✓). The
    ASCII-only rule applies to console output in scripts, not the README.
    spy/autoresearch happen to be ASCII-only (`-->`, `+/-`) because their
    diagrams are ASCII box-drawn; IMAGE/TABULAR/QQQ use unicode. Both are
    in-family.
12. **Prose hard-wraps at ~72–78 chars** in IMAGE/TABULAR/QQQ (3/5, and the
    newer style); spy/autoresearch leave paragraphs unwrapped. Prefer wrapped.
13. **A closing credit line** — either a centered `<sub>` footer (spy 965–967:
    *"Built with Claude Code as the autonomous research agent. 90 experiments.
    Zero human intervention during experimentation."*) or a
    `## License & credits` paragraph naming the agent, model, date, and the
    git URL that pins the history.
14. **No self-graded ACCEPT banner.** No reference contains a bare "PASS" or
    "VALIDATED" banner about its own science; every pass count is attached to
    a named script or a third-party audit link (§4f).

---

## 8. Length + shape budget (actual measured numbers)

### 8a. LONG form — `autoresearchspy/README.md`, 967 lines

| section | lines | % |
|---|---:|---:|
| Masthead + badges | 23 | 2.4 |
| Generalized-framework spotlight (optional) | 54 | 5.6 |
| Paper & Article links | 13 | 1.3 |
| Table of Contents | 48 | 5.0 |
| Highlights | 15 | 1.6 |
| **Champion Model Results** | 53 | 5.5 |
| Key Innovation (agent-as-researcher) | 45 | 4.7 |
| Architecture | 97 | 10.0 |
| Data Pipeline | 45 | 4.7 |
| Evaluation Framework | 69 | 7.1 |
| Uncertainty Estimation | 47 | 4.9 |
| The Agent Loop (7 steps) | 57 | 5.9 |
| Experiment History + Key Discoveries | 40 | 4.1 |
| Quick Start | 81 | 8.4 |
| CLI Reference | 77 | 8.0 |
| Project Structure | 56 | 5.8 |
| Dependencies | 27 | 2.8 |
| Dashboard | 23 | 2.4 |
| Contributing | 36 | 3.7 |
| References | 33 | 3.4 |
| License + footer | 9 | 0.9 |

### 8b. LONG form, rigor-forward — `AUTORESEARCHIMAGE/README.md`, 763 lines

| section | lines | % |
|---|---:|---:|
| H1 + thesis + Live links | 17 | 2.2 |
| **Read this first (real vs synthetic)** | 63 | **8.3** |
| Quick stats | 21 | 2.8 |
| Table of contents | 21 | 2.8 |
| What this is | 38 | 5.0 |
| Why this dataset | 26 | 3.4 |
| Quickstart | 40 | 5.2 |
| The autoresearch protocol | 27 | 3.5 |
| Triple-check data-split audit | 36 | 4.7 |
| Citation Rigor & Reasoning Blob | 26 | 3.4 |
| Goodhart-fingerprinted composite | 19 | 2.5 |
| Repo layout | 42 | 5.5 |
| The 18-experiment campaign (the big table) | 43 | 5.6 |
| **Three central findings** | 71 | **9.3** |
| How to reproduce | 41 | 5.4 |
| Production deployment guide | 77 | 10.1 |
| Hardware notes | 15 | 2.0 |
| **Limitations & threats to validity** | 25 | 3.3 |
| Open axes for the next campaign | 20 | 2.6 |
| **Citations** | 62 | **8.1** |
| License & credits | 17 | 2.2 |

### 8c. SHORT form — `AUTORESEARCHTABULAR/README.md`, 217 lines

| section | lines | % |
|---|---:|---:|
| Title + badges + thesis + series context | 31 | 14 |
| Why `<dataset>` (with the SOTA-headroom table) | 28 | 13 |
| What this repo contains (layout tree) | 34 | 16 |
| **The three gates** | 65 | **30** |
| Composite metric (fingerprinted) | 13 | 6 |
| Running the campaign | 25 | 12 |
| Hardware contract | 11 | 5 |
| License | 3 | 1 |

### 8d. SHORT form — `autoresearchqqq_local/README.md`, 150 lines

| section | lines | % |
|---|---:|---:|
| Title + badges + provenance blockquote | 10 | 7 |
| Live dashboard | 8 | 5 |
| Headline result table | 12 | 8 |
| Repository layout | 26 | 17 |
| Quick start | 21 | 14 |
| Key methodology | 14 | 9 |
| Backbone status table | 12 | 8 |
| Citations | 17 | 11 |
| Roadmap | 17 | 11 |
| Provenance | 10 | 7 |
| License | 3 | 2 |

### 8e. Budget rules extracted

- **Results + findings together ≈ 15–20 %** of the document in both long
  forms (spy 9.6 % results; IMAGE 5.6 % campaign table + 9.3 % findings).
- **Protocol / gates / composite ≈ 10–30 %** — it grows as the results shrink.
  A pre-results repo spends 30 % on gates (TABULAR); a finished one ~10 %.
- **Citations ≈ 3–11 %**, and never fewer than ~15 entries in a finished
  campaign.
- **Repo layout ≈ 5–17 %** — always present, always a fenced tree with inline
  `#` comments.
- **Front matter (title → TOC) ≤ 15 %** in long form; the honesty block is the
  only front-matter item allowed to exceed 5 % on its own.
- **License ≤ 2 %**, always last.

---

## CHECKLIST — binary, gradeable assertions

Grade each PASS/FAIL. A conforming README should pass all unmarked items;
`[opt]` items are high-value optional elements taken from the strongest
reference.

1. The document opens with an H1 (or centered `<h1>`) naming the project, before any other content.
2. A bold one-line thesis appears within the first 10 lines, stating the domain and that this is an autonomous research loop.
3. The thesis names the method — "Karpathy-style experiment loop where Claude Code is the researcher" or a direct paraphrase — and gives the experiment count.
4. A badge row is present and at least three badges carry live numbers (experiment count, headline metric, status), not only infrastructure badges.
5. Every badge links to a real target (in-document anchor, Pages URL, or in-repo artifact) — no unlinked `<img>`.
6. A live-links block or `## Live dashboard` section appears within the first 25 lines, with an absolute `https://` GitHub Pages URL.
7. Each live link carries a trailing em-dash gloss saying what the reader will find there.
8. A headline-result table appears before any methods section, one metric per row, values right-aligned.
9. The headline table includes at least one baseline row (the thing the champion is measured against), not champion numbers alone.
10. Every headline number is followed in the same cell by its seed count and dispersion — `(k-seed median, std x)` or `± sd (k-seed)`.
11. No single-seed number appears without the literal word "single-seed" (plus a luck/catastrophe note where applicable).
12. A cross-seed reproducibility table exists with a bolded `**Median**` row (median, not mean).
13. A full campaign table exists where one row = one experiment, including a `seed` column and a final plain-English `role` column.
14. At least one campaign-table row records a failure, a null, or a failed prediction, and says so in the `role` column.
15. Champion/landmark rows in the campaign table are bolded cell-by-cell.
16. A champion-lineage block shows each promotion with its numeric delta on the arrow.
17. `(not measured)` or `—` is written literally into result tables rather than the row being omitted.
18. A `## Table of contents` exists if the README exceeds ~400 lines (and is absent below ~250).
19. The composite metric has its own `##` section with a fenced formula, a paragraph on what each term prices, and the SHA-256 fingerprint mechanism naming the file and the exception raised on mismatch.
20. A gates section documents each gate with its code path in backticks, its checks as a list or table, the artifacts it writes, and an explicit statement that there is no bypass flag.
21. At least one gate section names a real bug that gate actually caught, with the fix.
22. A reasoning-blob word-floor table is present and states the pre-run vs post-run requirement difference.
23. A repo-layout fenced tree is present with inline `#` comments, naming `experiment_log.jsonl`, `best_config.json`, `reasoning_annotations.json`, the checkpoint file, and the dashboard file.
24. A quickstart fenced block exists whose steps are numbered `# 1.`, `# 2.` … comments, with the mandatory audit/gate step called out in its comment.
25. The environment the quickstart was tested on (Python, framework version, OS, GPU) is stated adjacent to that block.
26. A reproduce-the-champion command gives every flag written out, followed by an expected-output list and the artifact paths written.
27. The reproduction reproduces the multi-seed headline (loop or explicit seed list), not a single seed, and states per-run wall-clock.
28. A resume-the-agent instruction lists, in order, exactly which files a fresh session reads to continue the loop.
29. A hardware section states VRAM cap, precision policy, CPU-core pinning with its reason, and determinism seeding.
30. A citations section lists every paper referenced anywhere in the campaign, each with author surnames + year + venue + italic/quoted title + arXiv ID + an em-dash relevance note.
31. Every hyperparameter or design choice discussed in prose or tables carries an inline paper attribution.
32. `---` separates every top-level section.
33. No heading is deeper than `###`.
34. Emoji appear only as a single leading `##`-heading icon or as live-link bullet markers — never in prose, never in table cells (except `✓`).
35. Numeric table columns use explicit right-align (`|---:|`) and label columns explicit left-align.
36. Diagrams are fenced ASCII/box-drawing, not embedded images.
37. `[opt, high-value]` A limitations / threats-to-validity section sits after the findings and before the citations, each bullet naming the limit in bold, why it limits the claim, and what would fix it.
38. `[opt, high-value]` An above-the-fold honesty block separates the defensible claim from the engineered/weak one in table form, with an explicit "what this does NOT demonstrate" list.
39. At least one comparability disclaimer states plainly what the numbers are NOT comparable to.
40. Every self-assessed pass count is attached to a named audit script or a linked third-party audit — no bare self-graded PASS/ACCEPT banner.
41. A seed-floor statement appears in limitations (e.g. "3 seeds is the floor, not the ceiling") with the citation that sets the floor.
42. A roadmap / open-axes section enumerates the next campaign's experiments, each with its motivating paper where one exists.
43. In-repo files are linked relatively; cross-repo files use absolute `github.com/.../blob/...` URLs; in-document jumps use anchors.
44. A provenance or credits block names the agent, the model, the date, and the git URL that pins the history.
45. The license section is last and occupies ≤ 2 % of the file.

---

*Spec complete. Sections 0–8 + checklist. Sources read: 5 READMEs
(967/966/763/217/150 lines), `autoresearchspy/CLAUDE.md`, and
`autoresearchspy/docs/index.md`. No files were modified in any reference repo.*

