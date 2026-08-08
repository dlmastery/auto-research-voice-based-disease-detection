# Inventory — `auto-research-voice-based-disease-detection`

Read-only inventory. Repo: `C:\Users\evija\auto-research-voice-based-disease-detection`

- [x] A. README inventory
- [x] B. Dashboard inventory
- [x] C. Available content
- [x] D. Discrepancy list

---

## A. README inventory

`README.md` — **289 lines**. Modified 2026-07-28 09:27 (same minute as `docs/index.html` and
the two PNGs — i.e. README and dashboard were last regenerated/edited together).

### A.1 Exact section arc (verbatim headings, in order, with line ranges)

| line | level | verbatim heading | span |
|---|---|---|---|
| 1 | H1 | `Voice-Health AutoResearch` | 1–8 |
| 9 | H2 | `Background — start here` | 9–123 |
| 11 | H3 | `What is "voice-based disease detection"?` | 11–27 |
| 28 | H3 | `What the data actually supports` | 28–72 |
| 73 | H3 | `The rest of the field` | 73–110 |
| 111 | H3 | `Why this program exists` | 111–123 |
| 125 | H2 | `Goal` | 125–139 |
| 140 | H2 | `Status — honest` | 140–171 |
| 151 | H3 | `The result, in four steps` | 151–171 |
| 172 | H3 | `F3 — the audio model loses to a single demographic variable` | 172–191 |
| 192 | H2 | `F1 — on SVD, age alone reaches ROC-AUC 0.871 without hearing any audio` | 192–217 |
| 218 | H2 | `Corpora` | 218–231 |
| 232 | H2 | `The rules that make this trustworthy` | 232–246 |
| 247 | H2 | `Layout` | 247–269 |
| 270 | H2 | `Quickstart` | 270–280 |
| 281 | H2 | `Novelty — stated plainly` | 281–286 |
| 287 | H2 | `Ethics` | 287–289 |

Note the **inconsistent heading level for findings**: `F3` is an H3 nested under
`Status — honest`, while `F1` is a top-level H2. There is no `F2`, `F4`, `F5`, `F6`, `F7a` or
`F7b` section at all — those findings are only referenced inside the four-step table.

### A.2 What it opens with

Lines 1–5: a one-sentence thesis in bold ("An autonomous, pre-registered audit harness for
voice-based disease detection"), then a lineage line naming this as the **eighth instantiation**
of a portable autoresearch process, linking `meta-skills/` (29 skills) and two sibling GitHub
repos (dsbench, darebench), and naming the hardware (single RTX 4090 laptop, 16 GB).

There is **no badge row, no table of contents, no dashboard link in the opening block.** The
only link to the live site anywhere in the README is buried at line 75 as an inline link on the
words "The dataset landscape" pointing at `datasets.html` — **not** at `index.html`. The master
dashboard is never linked from the README at all.

Then ~115 lines of *domain background before any result* — an unusually long expository ramp:
what voice-based disease detection is, the two causal mechanisms (larynx-as-instrument vs
speech-as-motor-act) with an explicit strength-of-evidence ranking, the SVD corpus census, a
"how many diseases can this actually detect" deflation table, a survey of 25 corpora across 7
disease families, and only then "Why this program exists."

### A.3 How it presents results

Three distinct presentations, in decreasing rigor:

1. **`Status — honest` (140–149)** — a 2-column borderless summary table (Findings / Benchmark
   results / Corpora decoded / Headline). Claims **3 findings** (F1, F2, F3 "certified").
   *This count contradicts `FINDINGS.md`, which carries 7 — see §D.*
2. **`The result, in four steps` (151–171)** — the narrative spine. A 3-column table
   (step / finding / what it establishes) walking F1/F3 → F4 → F7a → F7b, each step framed as
   "removes something the model was getting for free." Ends with an explicit ceiling statement
   ("AUC ≈ 0.65 — real, well above chance, far below the ~0.85 the literature reports … nowhere
   near clinical usefulness") and a convergence note against SpeechDx.
3. **Per-finding tables (172–216)** — F3 and F1 get full predictor-vs-metric tables.

Rigor furniture that IS present in these tables:
- **Negative controls rendered in the same table, italicised** (`sex alone` 0.4898,
  `duration alone` 0.4724) with an explicit sentence saying they are what isolates the effect.
- **The power contract stated inline** for F3: `n=8, m=2, min p=0.0078 < Holm 0.025`, and the
  word "powered" used deliberately.
- **One CI** in the whole README (F7b: `CI [−0.032, −0.022]`) plus a seed count (`10/10 seeds`).
- **A "What this does NOT claim" paragraph** (208) for F1 — explicitly says UAR vs ROC-AUC is
  not like-for-like, that the comparison is "indicative", and that no published result is shown
  wrong.
- **n stated in prose** for F1 (`n = 2,225 sessions / 1,853 speakers`).
- **Reproduce-command + raw-artifact link** for F1 only (210–214).

### A.4 Rigor furniture carried

- The **four-number contract** is declared at line 131–136: every claim carries
  `published SOTA | ours | confound baseline | margin above confound` — rendered as an
  **empty table with a header row and no body**. It is a promise, not an instrument; no
  finding in the README is actually rendered in that four-column shape.
- **"A win that does not clear the confound bar is logged NOT CLEARED, not announced."** (136)
- **Not-a-medical-device disclaimer twice** (121 blockquote, 149 plain line, and again at 289).
- **`The rules that make this trustworthy` (232–246)** — 8 bulleted rules (R1, R3/R4, R6, R7,
  R8, R11b, R11c, R11d), each with the failure it was paid for. R6 carries the actual
  arithmetic (`min p = 2/2ⁿ vs 0.05/m`).
- **`Novelty — stated plainly` (281–286)** — explicitly disclaims loop novelty (cites
  arXiv:2606.20394) and detector novelty; claims domain+ledger only.
- **`Ethics` (287–289)** — PHI, redistribution, subgroup reporting.

### A.5 Link table

There is **no dedicated link/navigation table**. Links are scattered inline. Full inventory of
outbound links:

| line | target | kind |
|---|---|---|
| 5 | `meta-skills` (relative dir) | internal |
| 5 | `github.com/dlmastery/autoresearch_dsbench`, `…_darebench` | external repo |
| 75 | `dlmastery.github.io/auto-research-voice-based-disease-detection/datasets.html` | **live site — the only one** |
| 102, 167 | `arxiv.org/abs/2606.17339` (SpeechDx) | paper |
| 106 | `arxiv.org/abs/2605.23977` | paper |
| 214 | `FINDINGS.md`, `autoresearch_results/F1_demographic_baseline.json` | internal |
| 222 | `zenodo.org/records/16874898`, `arxiv.org/abs/2410.10537` | dataset / paper |
| 234 | `CLAUDE.md` | internal |
| 243 | `autoresearch_results/_quarantined` | internal |
| 277 | `data/ACQUISITION_STATUS.md` | internal |
| 283 | `arxiv.org/abs/2606.20394`, `audits/NOVELTY_CRITIQUE.md` | paper / internal |

**Two of these are dead as written** — see §D.

### A.6 Where it stops short

- **No link to the master dashboard** (`docs/index.html` / the Pages root). A reader has no
  path from README to the primary deliverable except by guessing the URL.
- **No per-hypothesis navigation.** V1–V7 exist as generated pages and as a whole tier in
  `IDEA_TABLE.md`; the README never mentions the hypothesis registry, the V-numbering, or that
  4 of 7 hypotheses are untested. The "visible debt" surface exists in HTML and is invisible
  in the README.
- **No findings table.** F1–F7b are named but there is no one-row-per-finding ledger with
  tier / n / status. The reader must reconstruct it from prose.
- **Finding count is stale** (says 3; `FINDINGS.md` has 7).
- **No tier chips.** Nothing in the README says which numbers are SCREENING and which are
  EVALUATION, even though `CLAUDE.md` §5 defines a 5-rung ladder and R6 makes the distinction
  load-bearing. F7a/F7b/F4 numbers appear with no tier at all.
- **No CI on all but one number.** 14 of the ~15 headline AUCs are bare point estimates.
- **No `n=` on the four-step table**, the F3 table, or the corpora table.
- **No composite score anywhere**, despite `COMPOSITE.md` (17 KB) defining one.
- **No cost accounting** (R14 mandates GPU-hours per finding be published; the README does not).
- **No `EXPERIMENT_LEDGER.md`** — referenced by `CLAUDE.md` §6 as a state file and by the
  reading order; the README's Layout block omits it and **the file does not exist in the repo**.
- **No footer** — no commit SHA, no build timestamp, no composite fingerprint, no
  "last updated". The README's own provenance is unstamped.
- **Layout block (249–266) is stale** — lists `AXIS_TAXONOMY.md`, `COMPOSITE.md`,
  `IDEA_TABLE.md`, `PREREGISTRATION.md`, `FINDINGS.md` but omits `docs/`, `hypotheses/`,
  `ideas/`, `autoresearch_results/`, `backlog/`, `cache/`, `memory/`, `configs/`, `tests/`.
  It describes a repo smaller than the one that exists.

---

## B. Dashboard inventory

### B.1 Root `dashboard/` — CONFIRMED EMPTY

```
dashboard/
.
..
```

`ls -a dashboard/` returns nothing but `.` and `..`. Zero files, zero subdirectories. It is an
empty directory created 2026-07-25 13:45 (repo-scaffold time) and never populated. Since git
does not track empty directories, this exists only in the working tree.

The sibling-repo convention of `dashboard/` + a mirror in `docs/dashboard/` is **not** followed
here: this repo publishes from `docs/` directly.

### B.2 `docs/` full tree

```
docs/
├── README.md                 1,413 B   hand-written; documents the generator (see B.3)
├── index.html               46,560 B   THE MASTER DASHBOARD          [generated]
├── datasets.html            34,275 B   the 25-corpus dataset landscape [generated]
├── assets/
│   ├── confound_vs_sota.png 83,370 B   [generated]
│   └── svd_age_distribution.png 51,178 B [generated]
├── hypotheses/
│   ├── index.html            7,665 B   V1–V7 registry                [generated]
│   ├── V1.html               6,378 B                                 [generated]
│   ├── V2.html              11,132 B   (largest — the only one with a full result) [generated]
│   ├── V3.html               6,269 B                                 [generated]
│   ├── V4.html               6,426 B                                 [generated]
│   ├── V5.html               6,994 B                                 [generated]
│   ├── V6.html               6,186 B                                 [generated]
│   └── V7.html               6,339 B                                 [generated]
└── dashboard/
    └── experiments/          EMPTY — zero files
```

**13 files total. 10 HTML files. 2 PNGs. 1 markdown.**

`docs/dashboard/experiments/` is **empty** — the per-experiment page tier that the sibling
convention requires (`docs/dashboard/experiments/expNNN.html`) has **zero pages**. The directory
was scaffolded 2026-07-25 and never filled. So the hierarchy is two levels deep
(master → per-hypothesis), not three (→ per-experiment).

### B.3 GENERATED or hand-written? — **GENERATED. Three generators, all present and named.**

This is the headline answer: **the dashboard is fully generated from code that lives beside it.**

| generator | size | writes | evidence |
|---|---|---|---|
| `scripts/build_dashboard.py` | **61,801 B** | `docs/index.html` | `out = DOCS / "index.html"; out.write_text(html_text, encoding="utf-8")` — `scripts/build_dashboard.py:1160-1161` |
| `scripts/build_datasets_page.py` | 12,667 B | `docs/datasets.html` | linked from index at `build_dashboard.py:782` |
| `scripts/build_hypothesis_pages.py` | 16,397 B | `docs/hypotheses/*.html` (index + V1–V7) | linked from index at `build_dashboard.py:1081` |

Grep for `.html` across `scripts/`, `src/`, `tests/`, `skills/`, `meta-skills/` returns
**exactly these three files and no others** — there is no hand-written HTML anywhere and no
fourth writer.

`docs/README.md` (hand-written, 1,413 B) documents the contract explicitly and is worth quoting
because it is a strong artifact:

> `docs/index.html` and everything in `docs/assets/` are **generated, not hand-written**. …
> reads every number it renders out of a source artifact in this repository —
> `autoresearch_results/F1_demographic_baseline.json`, `autoresearch_results/bench_svd_egemaps.json`,
> `data/interim/<corpus>/summary.json` and `manifest.csv`, `data/ACQUISITION_STATUS.md`,
> `data/PREPROCESSING_STATUS.md`, `corpus/SURVEY_datasets.md`, `IDEA_TABLE.md` and `FINDINGS.md`
> … If a source file is missing the generator exits with a `FATAL:` message rather than emitting
> a blank or invented cell (CLAUDE.md R1: no orphan numbers; R2: the agent never states a metric
> it did not read from an artifact), and the age-distribution figure is additionally
> cross-checked against the F1 JSON so a plot can never disagree with the finding it illustrates.
> Anything not yet measured renders as the literal words *not yet measured*.

So: **fail-loud on missing sources, an anchor assertion between plot and JSON, and an explicit
"not yet measured" sentinel.** This repo does *not* have the "artifact that cannot be regenerated
from the code beside it" defect.

Self-containment: inline CSS, one inline `<script>` for sort/filter, PNG (not SVG) plots, no CDN,
no JS framework, no network request. Matches the house hard-rules.

### B.4 Link graph

```
docs/index.html  (master)
   ├──> docs/datasets.html            "the dataset landscape"        [build_dashboard.py:782]
   └──> docs/hypotheses/index.html    "Per-hypothesis pages ->"      [build_dashboard.py:1081]
            └──> V1.html … V7.html
   (embeds) assets/svd_age_distribution.png, assets/confound_vs_sota.png
   (no link to) docs/dashboard/experiments/*   -- none exist
```

README.md → `datasets.html` only. **No README → index.html link.**

### B.5 GitHub Pages wiring — **NOT wired in-repo**

- `_config.yml` — **absent** (neither at repo root nor in `docs/`).
- `.nojekyll` — **absent** (neither at repo root nor in `docs/`).

The site is nonetheless live at
`https://dlmastery.github.io/auto-research-voice-based-disease-detection/` (README line 75),
so Pages must be configured through the **GitHub repo settings UI** (source = `master` branch,
`/docs` folder), not through a committed config. That is a real fragility: the publish
configuration is not in version control and cannot be reviewed, diffed, or restored from the
repo. Serving directory is `docs/`.

Without `.nojekyll`, Jekyll processes the output — any future asset directory beginning with
`_` would be silently dropped. Currently nothing starts with `_`, so it happens to work.

---

## C. Available content — what COULD be rendered

### C.1 `autoresearch_results/` — 11 JSON files, 1 README, 0 JSONL

**No `experiment_log.jsonl`. No `best_config.json`. No `JUDGE_CARD.md`.** All three are
mandated by `CLAUDE.md` §6 as state files. None exists. `find . -name "*.jsonl"` returns
**nothing** repo-wide. There is no append-only history and no champion record; the program's
"history" is 11 loose result files whose only ordering is their mtime.

**Top level (7 files + 2 dirs):**

| file | size | mtime | schema |
|---|---|---|---|
| `F1_demographic_baseline.json` | 689 B | 07-25 14:28 | flat dict, 15 keys |
| `V1_ssl_vs_handcrafted.json` | 4,282 B | 07-28 09:05 | dict, 21 keys, `repeats_detail` list[10] |
| `V2_speaker_subspace.json` | 6,700 B | 07-28 03:59 | dict, 17 keys, `rows` list[7] |
| `V2_speaker_subspace_SHUFFLE.json` | 4,091 B | 07-28 14:11 | same shape + `shuffle_control:true`, `rows` list[4], `repeats:3` |
| `V2_speaker_subspace_SHUFFLE.partial.json` | 2,931 B | 07-28 14:11 | checkpoint: `{completed_repeats, of, ranks, acc}` |
| `V6_preprocessing_leakage.json` | 1,937 B | 07-28 07:03 | dict, 10 keys, `cells` list[6] |
| `V7_silence_shortcut.json` | 2,020 B | 07-28 05:56 | dict, 11 keys, `cells` list[6] |
| `bench_svd_egemaps.json` | 18,813 B | 07-25 16:55 | `schema: voicehealth.bench/1`, 20 keys |
| `bench_svd_wavlm_mean_std.json` | 12,894 B | 07-28 04:47 | `schema: voicehealth.bench/1`, 20 keys |
| `_quarantined/README.md` | 766 B | — | retraction machinery — **exists, empty of retractions** |
| `acquisition/*.json` | 4 files | 07-25 | corpus census artifacts |

**Schemas in detail.**

`F1_demographic_baseline.json` (689 B) — flat, 15 keys, no nesting:
```
dataset "svd" · artifact <abs path to voice_data.csv> · artifact_md5 "2ee9852a19ede31c68107684b97bd308"
n_sessions 2225 · n_speakers 1853 · n_pathological 1356 · n_healthy 869
mean_age_healthy 28.320… · mean_age_pathological 51.047…
auc_age_only 0.87086… · auc_sex_only 0.51720… · auc_age_sex_speaker_disjoint 0.87681…
speakers_with_multiple_sessions 200 · max_sessions_per_speaker 24
published_benchmark "UAR 85.22 (arXiv:2410.10537) — different metric, indicative only"
```
Carries an md5 of its source — good provenance. **No CI, no seed, no repeats, no n_boot.**

`bench_svd_egemaps.json` / `bench_svd_wavlm_mean_std.json` — **the richest schema in the repo,
`voicehealth.bench/1`**, and the only one with a version tag. 20 top-level keys:
`schema, generated_utc, elapsed_s, command, git_sha, host{platform,python}, manifest, backend,
embedding_artifact, embedding_manifest, embedding_content_hash, config{13}, config_hash,
dataset, power_check_R6, recording_level, speaker_level, per_repeat_auc, margins_vs_confound,
verdicts`.

- `command` — the literal CLI (`run_benchmark.py --corpus svd --backbone wavlm --head logreg --folds 5 --repeats 8`)
- `git_sha` — `5cab307b744df840d8a16ac305c47192e2ab0aaf` (wavlm) / `a640ceb19f59b474daa3daede4a81904cf9e60d2` (egemaps)
- `config_hash` — `815673703168e601` (wavlm) / `3ffad10ed6634618` (egemaps)
- `power_check_R6` — `{n_paired:8, family_size:2, min_attainable_p:0.0078125, holm_tightest_threshold:0.025, feasible:true, min_n_for_feasibility:7, rule:"CLAUDE.md R6 — paired Wilcoxon min p = 2/2^n vs Holm 0.05/m"}`. **The power contract is machine-recorded, not prose.**
- `recording_level` — one entry per head *and* per confound: `logreg, ens_rank3, confound::age_only, confound::sex_only, confound::age_sex, confound::duration_only, confound::intensity_rms_only, confound::age_sex_duration_rms`. Each carries `roc_auc, uar, accuracy, f1, ece, roc_auc_ci95{lo,hi,n_boot}, per_repeat_auc_mean, per_repeat_auc_std`. **ECE is computed** — calibration is available and never rendered.
- `margins_vs_confound` — `confound_bar_name`, `confound_bar_auc_recording/speaker`, `best_audio_head`, and per-head `{recording_level_delta_auc{delta,lo,hi,p_gt_zero,n_boot}, speaker_level_delta_auc{…}, paired_wilcoxon_over_repeats{statistic,p_value}, cleared_…}`
- `verdicts` — `{"logreg":"NOT CLEARED","ens_rank3":"NOT CLEARED"}` (egemaps: 5 heads, all NOT CLEARED)

**This is a fully-formed multi-axis record with CIs, bootstrap counts, Wilcoxon p-values, ECE,
recording- AND speaker-level views, and per-repeat traces — and the dashboard renders a small
fraction of it.**

`V1_ssl_vs_handcrafted.json` — 21 keys. `hypothesis, objective:"ROC-AUC vs clinical labels
(JUDGE-FREE)", corpus:"svd", age_tolerance_years:3.0, repeats:10, folds:5,
family_m_preregistered:9, encoders_registered:["HeAR","WavLM-base+","Whisper-small-enc"],
encoders_run:["WavLM-base+","eGeMAPS"], note_scope:"HeAR and Whisper not extracted on this host;
COUGHVID excluded per F2", repeats_detail:list[10]` (each: `{seed, n_speakers, n_recordings,
age_healthy, age_patho, age_gap, auc_age_only, auc_wavlm, …}`), `mean_auc_age_only 0.5534,
mean_auc_wavlm 0.6227, mean_auc_egemaps 0.6496, mean_age_gap 0.7732, mean_n_speakers 613.2,
matching_worked true, wavlm_minus_egemaps −0.02693, wavlm_minus_egemaps_ci95 [−0.03172, …],
ssl_beats_handcrafted false, elapsed_s 499.7`.

`V2_speaker_subspace.json` — 17 keys. `audited:"arXiv:2604.14354"` (the audited paper is a
first-class field), `n_recordings 28509, n_speakers 1679, folds 5, repeats 10,
family_m_preregistered 14, ranks [1,2,4,8,16,32,64], rows list[7]` — each row
`{k, auc_speaker_removed, variance_removed_speaker, drop_from_full, auc_pca_topk_removed,
variance_removed_pca, …}` — plus `auc_full_mean 0.73818, auc_full list[10],
speaker_id_acc_full 0.27799, speaker_id_chance 0.01667, elapsed_s 15304.4` (4h15m).

`V2_speaker_subspace_SHUFFLE.json` — identical shape, `shuffle_control:true`, `repeats:3`,
`ranks[4]`, `auc_full_mean 0.50688`. **A shuffle control exists as its own artifact.** Its
`.partial.json` sibling is the resumable checkpoint.

`V6_preprocessing_leakage.json` — `cells list[6]` each `{corpus, backbone, status:"RUN"|…,
n_recordings, n_speakers, auc_fit_on_all, auc_fit_per_fold, delta_mean, …}`; `cells_run:3`,
`all_within_pm_0.01: true`.

`V7_silence_shortcut.json` — `cells list[6]` each `{corpus, features:"silence_only", status,
n_recordings, n_speakers, auc, auc_ci95[lo,hi], auc_directionless, …}`; `cells_run:4`,
`all_below_0.60: true`, **`falsifier_fully_evaluable: false`** — the artifact self-reports that
its own falsifier could not be fully evaluated. Excellent field; rendered nowhere.

`acquisition/` (4 files) — each carries `artifact, source_file/source_zip, source_sha256,
repo_commit` and a `split_key_verdict` prose field:
- `svd_inventory_analysis.json` — 2,495 rows / 2,225 sessions / 1,853 speakers, `zenodo_doi`,
  `license: CC-BY-4.0`, a `LEAKAGE` block with 9 keys (`session_id_is_the_zip_folder_name`,
  `n_speakers_with_multiple_sessions`, `pct_rows_at_risk_if_split_on_session`,
  `n_speakers_on_both_healthy_and_pathological_sides`, example lists).
- `svd_inventory_stats.json` (11,574 B) — 72 archives processed, 0 failed, 2,312 speaker dirs,
  32,276 `.nsp` files, `per_archive` dict with **72 named pathologies**.
- `coswara_meta_stats.json` — 2,746 rows / 2,746 unique ids, `binary_task.meets_500_per_class`,
  `confounds{gender_by_class, country_by_class_top, age}`.
- `coughvid_meta_stats.json` — 34,434 rows / 34,434 uuids, `speaker_id_field_present: false`,
  `split_key_verdict: "NO participant identifier exists…"` — the F2 blocker, machine-recorded.

`_quarantined/README.md` (766 B) exists. **Zero quarantined artifacts.** R11d machinery is
installed and unused.

### C.2 `hypotheses/` and `ideas/` — BOTH EMPTY DIRECTORIES

```
hypotheses/   0 files
ideas/        0 files
```
Also empty: `backlog/` (0), `configs/` (0), `memory/` (0), **`tests/` (0 — no rung-0 UNIT
layer at all, which `audits/IMPL_CRITIC.md` already flags)**.

The V1–V7 hypothesis content lives **entirely in `IDEA_TABLE.md`** (22,243 B), which
`scripts/build_hypothesis_pages.py` parses. Each hypothesis is a 10-row markdown table:
`Claim · Audited claim · Falsifier · Predicted Δ · Tier · m / n · Axis moved · Datasets ·
Cost · Status`. This is rich, well-formed content — full falsifiers, numeric pre-registered
predictions, and the power arithmetic per hypothesis.

**Status per `IDEA_TABLE.md` §Summary (lines 196–202):**

| id | axis | tier | m | n | min p | Holm | feasible | scope | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| **V1** | A5 | EVALUATION | 9 | 10 | 0.001953 | 0.005556 | yes | SVD, 1 of 3 encoders | **RESULT — CLAIM SUPPORTED** (eGeMAPS 0.6496 > WavLM 0.6227, CI [−0.032,−0.022], 10/10 seeds); not formally closed (falsifier wants ≥2 corpora) → F7 |
| **V2** | A9 | EVALUATION | 14 | 10 | 0.001953 | 0.003571 | yes | SVD (Coswara unrun) | **RESULT — CLAIM SUPPORTED, falsifier did NOT fire** → F4 |
| **V3** | A5 | EVALUATION | 42 | 12 | 0.000488 | 0.001190 | yes | SVD, Coswara, COUGHVID | **UNTESTED** |
| **V4** | A8 | EVALUATION | 6 | 10 | 0.001953 | 0.008333 | yes | Coswara↔COUGHVID, SVD→VOICED | **UNTESTED** |
| **V5** | A12 | SCREENING (promotion pre-declared) | 3 | ≤3→10 | 0.001953 | 0.016667 | yes | SVD, Coswara, COUGHVID | **UNTESTED** |
| **V6** | A4 | EVALUATION | 6 | 10 | 0.001953 | 0.008333 | yes | SVD only (4 cells unrun) | **PARTIAL** — SVD near-null reproduced; falsifier NOT evaluable → F5 |
| **V7** | A5 | EVALUATION | 6 | 10 | 0.001953 | 0.008333 | yes | all 3 (silence arm complete) | **PARTIAL** — shortcut does NOT generalise; stated mechanism was wrong → F6 |

**Count: 4 of 7 have results (V1, V2 full; V6, V7 partial) · 3 of 7 UNTESTED (V3, V4, V5).**
Each of the four has a matching JSON in `autoresearch_results/`.

**Caveat that matters for a rebuild:** `IDEA_TABLE.md` is **internally inconsistent**. The
Summary table (line 196) says V1 is `CLAIM SUPPORTED`, but V1's own registry block
(line ~85) still has `| **Status** | **UNTESTED** |`. Only V2's registry Status cell was
updated ("RUN 2026-07-28 → F4. CLAIM SUPPORTED; FALSIFIER DID NOT FIRE."). Any rebuilt
generator must read the Summary, not the per-hypothesis Status cell, or must fix the source.

### C.3 `audits/` — 6 files (5 audits + an index README), 111 KB total

| file | size | date | scope | verdict (verbatim gist) |
|---|---|---|---|---|
| `README.md` | 5,273 B | 07-26 | index + circularity disclosure | leads with a "single most serious defect across all audits" section |
| `DATA_SPLIT_AUDIT.md` | 16,043 B | 07-26 | `data/interim/{svd,coswara,coughvid}/manifest.csv` — speaker ids, sessions/speaker, class balance, age/sex confounds, recording-level leakage simulation | **SVD CONDITIONAL PASS (screening only, 49 speakers) · Coswara FAIL · COUGHVID HARD FAIL**; a recording-level split would leak 100% of SVD speakers and 99.4% of Coswara test recordings |
| `IMPL_CRITIC.md` | 26,512 B | 07-28 | `src/voicehealth/{benchmark,embed,features}.py`, `run_benchmark.py`, `audit_demographic_baseline.py` | **one INVALIDATES-RESULTS defect** (embedding cache key omits labels/speaker-ids → relabelled manifest gets a cache hit with *old* labels), 5 BIASES, 9 cosmetic; **`tests/` is empty — no rung-0 UNIT layer** |
| `SCI_CRITIC.md` | 23,501 B | 07-26 | `FINDINGS.md` F1, `PREREGISTRATION.md` V2, `IDEA_TABLE.md` V1–V7, `COMPOSITE.md` | composite fingerprint + 8 degenerate rows re-execute exactly; but `lambda_sub` **cannot fire on SVD**, `lambda_ctrl` self-weakens, **the formula is implemented nowhere** (`src/voiceaudit/composite.py` does not exist); F1's 0.871 is on 1,853 speakers but quoted against 49 where the real figure is **0.741** |
| `NOVELTY_CRITIQUE.md` | 25,137 B | 07-25 | prior art for framing/target | loop not novel (arXiv:2606.20394); **domain survives under exactly one framing — audit engine, not detector factory** |
| `PRIOR_AUTORESEARCH_REPOS.md` | 21,455 B | 07-26 | archaeology of 7 prior `dlmastery/*` programs replayed from their own `experiment_log.jsonl` | 2 landed real results; 1 ran **0 experiments** across 324 scaffolded tasks; 1 shipped a paper abstract with another project's numbers |

Every audit carries the R5/R16 circularity banner. **None of these six is linked from the
dashboard**; only `NOVELTY_CRITIQUE.md` is linked from the README.

### C.4 PNG plots already generated — 2, both in `docs/assets/`

| path | size | rendered as |
|---|---|---|
| `docs/assets/svd_age_distribution.png` | 51,178 B | the F1 recruitment-asymmetry figure; cross-checked at build time against `F1_demographic_baseline.json` so plot and finding cannot disagree |
| `docs/assets/confound_vs_sota.png` | 83,370 B | published-SOTA vs confound-bar comparison |

`find . -name "*.png"` outside `.git` returns **exactly these two**. There are **no plots for
V1, V2, V6 or V7** — no rank-sweep curve for V2's 7 ranks, no per-seed bar for V1's 10 repeats,
no cell grid for V6/V7 — even though every one of those artifacts contains plot-ready arrays
(`rows`, `repeats_detail`, `cells`, `auc_full` list[10], `per_repeat_auc`).

### C.5 Other renderable content

- `corpus/datasets.json` (25,296 B) — the structured registry behind `datasets.html`;
  **25 corpora across 7 disease families**. Already rendered.
- `corpus/SURVEY_datasets.md` (27,279 B), `SURVEY_sota_methods.md` (27,793 B),
  `SURVEY_autoresearch_sota_2026.md` (41,106 B) — citation-verified. Only the first is read
  by a generator.
- `data/`: `ACQUISITION_STATUS.md` (14,726 B), `PREPROCESSING_STATUS.md` (11,557 B),
  `CARD_svd.md` / `CARD_coswara.md` / `CARD_coughvid.md`, plus `data/interim/` summaries and
  manifests. **`PREPROCESSING_STATUS.md` last written 07-25 — 3 days before the last dashboard
  build, and the dashboard renders its stale "49 speakers" state verbatim.**
- Root docs never rendered anywhere: `AXIS_TAXONOMY.md` (22,319 B — the A1…A12 axis
  definitions the hypothesis pages cite by number), `COMPOSITE.md` (17,244 B),
  `PREREGISTRATION.md` (21,698 B), `SETUP.md` (6,519 B), `ACQUISITION_STATUS.md` (10,264 B).
- `skills/` 7 files · `meta-skills/` 29 files.

### C.6 `FINDINGS.md` — 7 findings, 28,302 B

| id | title | claimed tier / status (verbatim) |
|---|---|---|
| **F1** | On SVD, patient AGE alone reaches ROC-AUC 0.871 without hearing any audio | `SCREENING-tier, metadata-only` |
| **F2** | WavLM embeddings do NOT clear the demographic bar on SVD (pilot) | `SCREENING, and formally UNDERPOWERED — the harness refused to certify it` |
| **F3** | At FULL corpus scale (1,679 speakers), WavLM still does not clear the age bar | `Statistical status — CERTIFIED (2026-07-27)`; verdict `NOT CLEARED — and the gap WIDENED with more data` |
| **F4** | About a third of WavLM's disease discrimination is speaker IDENTITY, not pathology | `Tier: EVALUATION` (n=10 × 5-fold speaker-disjoint, m=14 pre-registered) |
| **F5** | Scaler-before-split leakage is *nothing* on SVD embeddings (0.00004 AUC), but the corpus-specificity claim is UNTESTED | `Tier: PARTIAL` — 3 of 6 cells; one underpowered by construction |
| **F6** | The Clever-Hans silence shortcut does NOT generalise: near chance on all three corpora | `Tier: PARTIAL` — 4 of 6 cells; silence arm ran on all three corpora |
| **F7** | With age matched away, 88 handcrafted features BEAT a 1536-dim SSL model | `Tier: EVALUATION for the cell that ran` (n=10 × 5-fold speaker-disjoint, m=9); split in prose into F7a / F7b |

**Tally: 2 SCREENING (F1, F2) · 1 CERTIFIED (F3) · 2 EVALUATION (F4, F7) · 2 PARTIAL (F5, F6).**

Structural quality is high. Every finding has a `### The measurement` section, an artifact
pointer, and — notably — a *limits* section under varying names: `What this does NOT claim —
read before citing` (F1), `Limitations — do not over-read this either` (F2), `Limitations`
(F3), `What this does NOT show — the falsifier did not fire` (F4), `Scope` (F4). F4 also has
`The negative control passes` and `Composed with F3`. F7 has `Feasibility, re-checked — a
design that used to be impossible`, `The matching worked — and it is checked, not assumed`,
and **`A bug in my own harness, on the way here`**. **This is the strongest content in the
repo and almost none of it reaches the dashboard.**

---

## D. Discrepancy list — self-evidently substandard on the repo's own terms

Ordered by severity. Every item is judged against `CLAUDE.md` / `docs/README.md` /
`FINDINGS.md` — this repo's own written standards — not an external one.

### D1. The hypothesis registry says 6 of 7 UNTESTED. Four have results. — ROOT CAUSE FOUND

`docs/hypotheses/index.html` renders `UNTESTED` chips for **V1, V3, V4, V5, V6, V7** and
`EVALUATION` only for V2. `IDEA_TABLE.md` §Summary says V1 = CLAIM SUPPORTED, V2 = CLAIM
SUPPORTED, V6 = PARTIAL, V7 = PARTIAL. Result JSONs exist on disk for all four.

Cause is a **hardcoded one-entry lookup table**:

```python
# scripts/build_hypothesis_pages.py:35
ARTIFACTS = {"V2": "V2_speaker_subspace.json"}
```

`V1_ssl_vs_handcrafted.json`, `V6_preprocessing_leakage.json` and `V7_silence_shortcut.json`
sit beside it in the same directory and are never looked up, so
`tested = result is not None` (line 187) is False and line 189 stamps `UNTESTED`. The
result-rendering branch is hardcoded the same way:

```python
# scripts/build_hypothesis_pages.py:220
if tested and h["id"] == "V2":
```

so the renderer **structurally cannot display any hypothesis's results except V2's**.

This is precisely the repo's own documented failure mode: the build succeeded, the markdown-leak
gate passed, the page is well-formed — and it publishes the opposite of the truth. The page's
own subtitle asserts *"A hypothesis whose falsifier has not been executed is never reported as
supported"* while suppressing three executed falsifiers. It violates **R7 in the inverse
direction** and **R8** (negative/partial results are not shown at equal prominence — they are
shown as nothing).

### D2. The dashboard tells two contradictory stories on the same page

`docs/index.html`, single build, `2026-07-28 16:27 UTC`, commit `d6487c8c3812`:

| line | element | says |
|---|---|---|
| 78 | hero panel "The result, in four steps" | F1/F3/F4/F7a/F7b · WavLM **0.7438** · 24–39% identity · **full corpus** |
| 125 | stat tile | `7 findings` — caption still reads *"F1, screening-tier, metadata-only — see below"* |
| 126 | stat tile | `2 benchmark runs with artifacts · experiment_log.jsonl rows: 0` |
| 128 | stat tile | `7 hypotheses registered` — *"**all UNTESTED**"* |
| 131 | blocked panel | *"20 of 72 pathology archives are on disk… every audio number on SVD is measured on **49 speakers** and is screening-tier by construction"* |
| 189 | scoreboard, SVD "ours" | `UAR 0.6655 / AUC 0.7983`, `n=667 recordings / **49 speakers**`, eGeMAPS `gbt`, chip `SCREENING` |
| 197 | corpus table, SVD | speakers `**1,679**`, files found `61,178`, decoded `61,170` |
| 203 | footnote directly beneath | *"SVD: 1,853 speakers exist, **49 decoded**"* |

Rows 197 and 203 are **adjacent elements that contradict each other**. The scoreboard — the
page's "four numbers" contract surface — is still the 49-speaker pilot, three days after the
full-corpus run. The hero panel was evidently added by hand-editing the generator's string
without updating the sections beneath it.

`docs/index.html` also has **no F2, F3, F4, F5, F6 or F7 sections at all**. Its only finding
sections are `F1 — the headline finding` and `First measured audio benchmark — a negative
result` (the 49-speaker eGeMAPS pilot). F-numbers appearing in the page: F1 ×8, F3 ×1, F4 ×2,
F7a ×1, F7b ×1 — and F3/F4/F7a/F7b appear **only inside the hand-added hero panel**.

### D3. The dashboard footer's repository link is dead (404)

```python
# scripts/build_dashboard.py:38
REPO_URL = "https://github.com/eranti/auto-research-voice-based-disease-detection"
```
Rendered at `docs/index.html:231`. The actual remote (`.git/config`) is
`https://github.com/dlmastery/auto-research-voice-based-disease-detection.git`, and the README
links the live site at `dlmastery.github.io/…`. **`github.com/eranti/…` does not exist.** The
single "go to the source" link on the published page is broken. `CLAUDE.md` R1's whole point is
traceability to artifacts; the traceability link 404s.

### D4. Three mandated state files do not exist

`CLAUDE.md` §6 names them as *the* state files:

| file | status |
|---|---|
| `autoresearch_results/experiment_log.jsonl` | **MISSING** (no `.jsonl` anywhere in the repo) |
| `autoresearch_results/best_config.json` | **MISSING** |
| `autoresearch_results/JUDGE_CARD.md` | **MISSING** |
| `EXPERIMENT_LEDGER.md` | **MISSING** (named in §6 *and* in the §8 reading order) |

The dashboard is honest about one of them (`experiment_log.jsonl rows: 0`) and silent about the
other three. §6 further says *"Champion health is a monitored metric. If `best_config.json` has
not advanced in N experiments, the loop is wandering"* — the monitored metric has no file to
read. The README's `Layout` block also omits `EXPERIMENT_LEDGER.md` entirely, so a reader never
learns it is missing.

### D5. Finding count disagrees across all three surfaces

- `README.md:144` — *"Findings **3** — F1 (age baseline), **F2 (COUGHVID has no speaker ids)**, F3 (certified)"*
- `docs/index.html:125` — `7 findings`, caption *"F1, screening-tier, metadata-only"*
- `FINDINGS.md` — **7 sections, F1–F7**, and **F2 is "WavLM embeddings do NOT clear the demographic bar on SVD (pilot)"**, not the COUGHVID blocker.

So the README does not merely undercount, it **assigns a different claim to the identifier F2**
than the findings ledger does. A reader following "F2" from the README lands on a different
finding. The COUGHVID-has-no-speaker-ids result is real (it is in
`acquisition/coughvid_meta_stats.json` and `audits/DATA_SPLIT_AUDIT.md`) but is not F2.

### D6. The four-number contract is declared and never rendered

`README.md:131–136` declares that every claim carries
`published SOTA | ours | confound baseline | margin above confound` — and renders it as a
**table header with an empty body**. No finding in the README appears in that shape. The
dashboard's `Benchmark scoreboard` is the only place the four columns exist, and its "ours"
cell is the superseded 49-speaker pilot (D2), with three of five rows entirely
`not yet measured`.

### D7. Bare numbers without `n=`, without a tier chip, without a CI

- `README.md` "The result, in four steps": **no `n=` on any row**, **no tier on any row**,
  one CI total across four findings (F7b).
- `README.md` F3 table: 6 predictors, 12 AUCs, **zero CIs**, no `n=` in the table (n appears
  in the prose beneath).
- `README.md` F1 table: 3 numbers, **zero CIs**.
- `docs/index.html`: `n=` appears **3 times** in a 46 KB page; `SCREENING` 6×, `EVALUATION` 8×,
  `pend` 16×.
- The data to fix this exists: `bench_svd_*.json` carries `roc_auc_ci95{lo,hi,n_boot}` on every
  head **and every confound**, plus `per_repeat_auc_std` and `paired_wilcoxon_over_repeats`.
  Every CI the README omits is already computed and sitting in an artifact.

`CLAUDE.md` R6 makes the n/tier distinction load-bearing; presenting a CERTIFIED number (F3),
a SCREENING number (F1) and a PARTIAL number (F6) in the same untiered prose is the exact
collapse R6 exists to prevent.

### D8. A broken string template shipped to the published page

`docs/hypotheses/index.html:47` renders:

> "7 registered · **1** with a at EVALUATION tier · 6 not yet."

Source, `scripts/build_hypothesis_pages.py:260–261`:
```python
f'<p class="sub">{len(hyps)} registered · <strong>{n_tested}</strong> with a '
f"at EVALUATION tier · {len(hyps) - n_tested} not yet. …"
```
A word is missing between "with a" and "at". The repo has a build-time markdown-leak gate
(line 286-287, added after a chip once rendered V5's whole tier paragraph with asterisks
showing) — but no gate on template coherence, so this shipped.

### D9. The per-experiment tier is scaffolded and empty

`docs/dashboard/experiments/` — **0 files**, created 2026-07-25 and never populated. There is
no per-experiment page for any of the 4 executed hypotheses, and nothing links to the directory.
Root `dashboard/` is likewise **completely empty** (0 files). Two scaffolded surfaces, zero
content — `CLAUDE.md` R11c ("ship the runner before the 300th scaffold") flags exactly this
shape, as do the empty `tests/`, `hypotheses/`, `ideas/`, `backlog/`, `configs/` and `memory/`
directories.

### D10. GitHub Pages publication config is not in version control

No `_config.yml`, no `.nojekyll`, at root or in `docs/`. The site is live, so Pages is
configured through the repo settings UI. The publish configuration cannot be reviewed, diffed,
or restored from the repo — and without `.nojekyll`, Jekyll silently drops any future
underscore-prefixed asset path.

### D11. The dashboard renders a stale input verbatim, with no staleness signal

`data/PREPROCESSING_STATUS.md` was last written **2026-07-25 15:39**; the dashboard built
**2026-07-28 16:27** reads it and prints "20 of 72 pathology archives… 49 speakers" as current
state. Nothing on the page shows the age of an input relative to the build. `docs/index.html`
itself is now stale against `FINDINGS.md` (07-28 14:12 local ≈ 21:12 UTC, ~4h45m *after* the
build) and against `V2_speaker_subspace_SHUFFLE.json` (07-28 14:11) — **the shuffle control,
the single most important validity artifact in the repo, postdates every published page and
appears on none of them.**

### D12. Rich artifact fields that are computed and never surfaced

Not errors, but the gap between available and rendered content:

- `power_check_R6{n_paired, family_size, min_attainable_p, holm_tightest_threshold, feasible, min_n_for_feasibility}` — the R6 contract, machine-checked, in every bench JSON. Rendered as prose in one README sentence, nowhere on the dashboard.
- `ece` (expected calibration error) on **every head and every confound** — `CLAUDE.md` §4.3(5) says *"Calibration — report reliability, not just AUC. Clinical usability is a probability question."* **ECE appears on no surface.**
- `speaker_level` metrics — computed alongside `recording_level` in both bench files; the README shows a speaker-AUC column for F3 only, the dashboard shows none.
- `V7_silence_shortcut.json → falsifier_fully_evaluable: false` — a self-reported falsifier limitation, rendered nowhere.
- `V2_speaker_subspace_SHUFFLE.json` — the shuffle control, rendered nowhere.
- `embedding_content_hash`, `config_hash`, `git_sha`, `command` — full reproduction provenance in both bench files; only `config_hash` + a truncated commit reach one dashboard caption.
- Plot-ready arrays with no plot: `V2.rows[7]` (rank sweep), `V2.auc_full[10]` (seed spread), `V1.repeats_detail[10]` (per-seed), `V6.cells[6]`, `V7.cells[6]`, `per_repeat_auc` in both bench files. **Only 2 PNGs exist and both are F1-era.**
- All **6 audit documents** (111 KB, including one INVALIDATES-RESULTS defect) are unlinked from the dashboard.
- `AXIS_TAXONOMY.md` defines A1–A12; hypothesis pages print "axis A9" as a bare chip with no link and no gloss.

### D13. Minor

- Emoji: **none**. Only `U+2713 CHECK MARK` in the V-pages, `hypotheses/index.html`,
  `docs/index.html` and `IDEA_TABLE.md`. Clean.
- Literal markdown leak in HTML (`##`, `**`, `|---|`): **0 hits across all 10 HTML files.**
  The build-time gate works.
- Self-graded banner qualifier: **present and correct** — *"Internal QA pass — independent
  external review pending"* at `docs/index.html:233` and in `audits/README.md`.
- `datasets.html` footer names its generator and build time but carries **no commit SHA**
  (`index.html` does) — inconsistent provenance across sibling pages.
- README has **no link to the master dashboard**; its only live-site link points at
  `datasets.html`.
- README heading levels are inconsistent for findings (F3 is an H3 under `Status`, F1 is an H2).
- README `Layout` block omits `docs/`, `autoresearch_results/`, `audits/` sub-detail,
  `hypotheses/`, `ideas/`, `tests/`, `backlog/`, `configs/`, `memory/`.
- R14 (cost accounting: GPU-hours and tokens **per confirmed finding**, "and publish it") is
  published nowhere, though `elapsed_s` is recorded in every artifact (V2 alone: 15,304 s).
- `_quarantined/` exists with a README and **zero retractions** — machinery installed, unused.
- `COMPOSITE.md` (17 KB) defines a composite that `audits/SCI_CRITIC.md` states is
  **"implemented nowhere"** (`src/voiceaudit/composite.py` does not exist); no surface shows a
  composite score, and no surface says it is unimplemented.

---

*End of inventory. Read-only; no file in the target repo was modified.*
