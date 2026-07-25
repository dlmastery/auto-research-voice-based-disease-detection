# Prior Autoresearch Repos — Archaeology Report

**Purpose:** inherit what worked and avoid what failed across the seven prior `dlmastery/*`
autonomous-research programs, before starting the eighth (voice-based disease detection).

**Method:** all seven repos shallow-cloned read-only (`git clone --depth 1`) to
`C:\Users\evija\AppData\Local\Temp\claude\autoresearch-priors\`. **All seven cloned
successfully — no clone failures.** No repo was modified. Numbers below are computed from
the actual `experiment_log.jsonl` / `registry/final_rollup.json` files in those clones, not
from the repos' prose.

Champion-advance counts were computed by replaying each `experiment_log.jsonl` in order and
counting strict improvements in best-so-far `composite`.

---

## 1. Per-repo summary

| Repo | Harness layout | Experiments run | KEEP / DISCARD | Champion actually advanced? | External benchmark? | Real result landed? |
|---|---|---|---:|---|---|---|
| **autoresearch** (FX EUR/USD — the original) | `CLAUDE.md` (967 ln) + `autoresearch/` pkg + **`generalized_ml_autoresearch/`** (the portable core: `core/`, `templates/`, `skills/`, `tests/`, 5 worked examples) + `docs/` GitHub Pages + `paper.md` | **265** | 40 / 225 (15% KEEP) | **Yes, strongly — 22 advances**, −1.2637 (exp 1) → +9.1860 (exp 203) | **No.** Self-defined composite `min(test_sharpe, val_sharpe) − 0.1·n_neg_folds` | **Unverifiable.** Test Sharpe +6.52, +1122% return, 7/7 positive folds — but no leaderboard to check against. Its own `paper_abstract.md` concedes composite σ ≈ 1.0 across 6 seeds (range ≈ 2.58) and concludes "single-seed champions in financial ML are probabilistically lucky" |
| **autoresearchindexstock** (QQQ — longest run) | Same + `code_versions/`, `memory/`, `data/`, `evaluation/`, and **15 ad-hoc `_*.py` scripts at repo root** | **259** (216 headline) | 7 / 252 (2.7% KEEP) | **Yes — 7 advances**, −1.5423 → **+1.3216** (exp 52, dMamba) | **No** | **No.** Champion is single-seed=42. The repo's own README table reports the champion backbone's **4-seed median −0.25** ("seed=99 catastrophe"); XGBoost 3-seed −0.40, CatBoost 4-seed ≈0. The hill-climb climbed seed noise |
| **autoresearch_dsbench** (DSBench, ICLR 2025) | `framework/` (`runner.py`, `hill_climb.py`, `validator.py`, `generate_scaffolds.py`, `final_report.py`, `run_all.py`, `CLAUDE_template.md`, `SECTION_MAPPING.md`, `sota_catalog.yaml`) + `registry/` + 112 generated per-task repos under `modeling/` & `analysis/` + **`skills/autoresearch-pack/` (48 skills)** + `dashboard/index.html` cross-task leaderboard | **11,871** rows across 112 tasks (112/112 tasks non-empty) | per-task champion tracking | **Yes — 112 per-task champions** | **Yes** — DSBench published baselines (best agent 34.12% analysis success, 34.74% RPG modeling) | **Yes — the biggest win.** `registry/final_rollup.json`: **`beats_dsbench: true` for 83 of 112 tasks** (29 false). `STATUS.md` reports 82/112 BEAT-DSBENCH, 112/112 forensic-audit PASS, 153/153 skill-coverage PASS |
| **autoresearch_darebench** (DARE-bench, ICLR 2026) | Same framework shape: `framework/`, `registry/tasks.json` (324 eval-only tasks), `tasks/<type>/<slug>__v{1,2}/`, `dashboard/`, `docs/_RECON.md` | **0** — all 324 `experiment_log.jsonl` files are 0 bytes | — | **No** | **Yes** — DARE-bench leaderboard (GPT-5 70.10% Class-IF, Claude-Sonnet-3.7 61.22% Class-MM, etc., tabulated in README) | **No.** `STATUS.md` first line: *"Phase: pre-experiment plan complete • **No experiments have been run.**"* Runners/hill-climb/audit code not written |
| **autoresearchimage** (medical imaging OOD) | `CLAUDE.md` (1430 ln) + `AUTORESEARCH_PROCESS.md` + `ARCHITECTURE.md` + `SOTA_COMPARISON.md` + `PAPER.md` + `SETUP.md` + `core/` + `configs/` + `scripts/` + `sota_catalog.yaml` + `memory/` + `tests/` + `dashboard/` | **21** | 20 KEEP + 1 `KEEP/CHAMPION`, **0 DISCARD** | **Barely — 1 advance** (exp 1 composite 1.0, never beaten) | **Yes** — WILDS-Camelyon17, Koh 2021 ICML baseline AUC 0.853 ± 0.020 | **Yes, but only from 3 of 21 experiments.** Exps 1–18 ran an *engineered* synthetic-blur binary PathMNIST task → composite 0.9966, explicitly declared "≠ comparable to anything in the literature". Exps **19–21** on the real benchmark: **test-OOD AUC 0.9220 ± 0.018 (3 seeds) vs Koh 2021's 0.853 → +0.073, recipe-attributable.** README honestly frames it as "modern ERM frontier, NOT a SOTA claim" (LISA/TADA/FishR reach 0.93–0.97) |
| **autoresearchtabular** (Higgs UCI) | Identical template to `autoresearchimage` (same 8 root .md files, `core/{backbones,data,evaluation}`, `scripts/`, `configs/higgs.yaml`, `tests/`) | **97** | 89 KEEP + 8 `KEEP/CHAMPION`, **0 DISCARD** | **Yes — 8 advances**, 0.8301 (exp 1 lightgbm) → **0.8723** (exp 95 ft_transformer) | **Yes** — Baldi 2014 *Nature Comms* + Gorishniy 2021/2024 published AUROC table | **Honest near-miss.** 0.8723 vs Deep-NN 0.885 / FT-Transformer 0.880 / TabM 0.886. `SOTA_COMPARISON.md` opens: "The point is *not* to claim novel SOTA; the point is to put our result in the right reference frame." Val/test gap 0.0003 — clean |
| **autoresearchspy** (SPY) | Verbatim fork of the FX repo (`CLAUDE.md` 1073 ln, `autoresearchspy/` pkg, same `generalized_ml_autoresearch/` copy, `docs/`) | **166** | 9 / 157 (5.4% KEEP) | **Yes numerically — 9 advances**, −0.3628 → +0.5890 | **No** | **No.** Best composite 0.589. Worse: `paper_abstract.md` carries a self-applied `⚠️ SCAFFOLD` banner and still contains **FX's** numbers ("SPY foreign-exchange benchmark", LSTM champion +6.4242); `README.md` badges still read "104 Experiments", "test Sharpe +6.21", "+1,001% return" and link to `dlmastery/autoresearch` |

### Constitution (`CLAUDE.md`) differences

Line counts: FX 967 → SPY 1073 → tabular 1007 → image 1430 → QQQ 1527. dsbench/darebench
replaced the hand-written constitution with `framework/CLAUDE_template.md` + a
`SECTION_MAPPING.md` audit table (36 mapped sections for dsbench, 44+6 for darebench) and a
`validator.py` that refuses to mark a task "ready" until every mapped section survives in the
generated per-task `CLAUDE.md`.

**Sections present in every hand-written constitution (the invariant text):** On Session Start ·
Hardware Constraints · Crash-Recovery Checkpointing · Mindset (Read First) · Hard Rules → Data
Integrity · Experiment Design · **Autoresearch Agent Protocol (Karpathy-adapted, 8 numbered
rules)** · **Research-Driven Experiment Selection (STRICT — no blind sweeps)** · Monotonic
Quality Progression (NEVER regress) · MLOps Documentation Standards · Explainability &
Auditability Report · Winner Definition · Per-Backbone Code Snapshots · Dashboard Reasoning
Annotations · Per-Backbone N-Experiment Mandate · Per-Backbone SOTA Recipes · GPU Memory
Constraint · Dashboard Files Update Mandate · Citation Rigor · Reasoning Blob Completeness ·
Winner Archiving Protocol · Common Mistakes (Never Repeat).

**Domain-specific sections** are a thin shell: FX/SPY/QQQ add *Super-Fold Invariants* and
*Heteroscedastic Loss Rules*; image adds *Triple-Check Data Split Audit* and
*Evaluation Protocol Invariants*; QQQ adds *User Directives Log* and *FX Project Learnings*;
darebench adds the *eval-only inversion* + *Agent K forbidden-path audit*.

---

## 2. (a) THE INVARIANT CORE — the exact skeleton to clone

Present in every repo that produced anything:

1. **`CLAUDE.md`** — the constitution, with the section list above. The load-bearing rule is
   the Karpathy protocol: *"Always start from the current best config. Every experiment
   modifies ONE thing from the best… Never wander off from the best baseline"* plus
   *"If you see consecutive discards, stop and rethink"* and *"Code changes are allowed"*
   (`autoresearch/CLAUDE.md:95-104`).
2. **The state quartet** — filenames identical in all 7 repos:
   `autoresearch_results/experiment_log.jsonl` (append-only),
   `autoresearch_results/best_config.json`,
   `autoresearch_results/reasoning_annotations.json`,
   `autoresearch_results/dashboard.html`.
3. **A programmatic reasoning gate that runs BEFORE the experiment.**
   `generalized_ml_autoresearch/core/reasoning.py` defines `WORD_COUNT_FLOORS`,
   `REQUIRED_KEYWORDS`, `validate_citation_rigor()`, `validate_reasoning_blob()`,
   `validate_pre_run_entry()`, `_has_any_placeholder()`. The runner refuses to launch an
   experiment whose pre-run annotation is missing, short, or placeholder-filled. This is the
   single most transferable piece of machinery in the whole lineage.
4. **A fingerprinted composite.** `core/evaluation/composite.py` — the formula is frozen and
   SHA-hashed at project setup; its docstring states the intent explicitly:
   *"Goodhart protection: the formula is frozen at project-setup time. Changing it mid-project
   requires a RULE_CHANGE entry in the checkpoint."*
5. **`memory/project_autoresearch_checkpoint.md`** — crash recovery; read first every session,
   written every ~3 minutes / every experiment. (`memory/project_hardware_log.md` alongside it
   in image/tabular.)
6. **A self-contained static dashboard + `scripts/sync_dashboard_to_docs.py` → `docs/` →
   GitHub Pages.** No CDN, no framework.
7. **A winner archive**: `autoresearch_results/winners/<backbone>_exp<N>_<desc>/` containing a
   14-section audit report, inference script, code snapshot, and Colab notebook.
8. **Already-extracted portable versions — do not rewrite these:**
   - `autoresearch/generalized_ml_autoresearch/` — `core/` (runner, reasoning, checkpoint,
     winner_archive, backbones/, evaluation/{composite,metrics,splits,uncertainty}),
     `templates/{CLAUDE_template.md, SECTION_MAPPING.md, sota_catalog.yaml}`,
     `tests/{test_smoke,test_runner_e2e,test_section_coverage}.py`, 5 worked examples.
   - `autoresearch_dsbench/skills/autoresearch-pack/skills/` — **48 skills**, incl.
     `seven-step-research-process`, `karpathy-agent-protocol`, `citation-rigor`,
     `reasoning-blob-completeness`, `monotonic-quality-progression`,
     `train-val-test-invariants`, `held-back-surface-discipline`, `forbidden-path-audit`,
     `winner-archive-protocol`, `crash-recovery-checkpoint`, `parallel-agent-orchestration`.

---

## 3. (b) WHAT CORRELATED WITH SUCCESS

**Hypothesis under test:** *repos anchored to an EXTERNAL benchmark with a public number
succeeded; open-ended ones stalled.*

**Verdict: CONFIRMED — with one important refinement.**

| Repo | External public number? | Real result? |
|---|---|---|
| dsbench | Yes (DSBench ICLR 2025) | **Yes** — 83/112 beat it |
| image | Yes (Koh 2021 ICML, 0.853) | **Yes** — 0.9220 ± 0.018, +0.073 |
| tabular | Yes (Baldi 2014 / Gorishniy tables) | **Partial but defensible** — 0.8723 vs 0.880 frontier, stated honestly |
| FX | No — self-defined composite | No verifiable claim (+9.19 means nothing externally) |
| QQQ | No | No — champion collapses to −0.25 at 4 seeds |
| SPY | No | No — 0.589, README still shows FX's numbers |
| darebench | Yes — **but 0 experiments run** | No |

**The refinement, which matters more than the headline.** FX and QQQ were *not* idle loops.
FX made **22 champion advances over 265 experiments** (−1.26 → +9.19); QQQ made 7 (−1.54 →
+1.32). The hill-climber worked perfectly. What it climbed was a composite the project itself
defined — so it maximized seed luck and split favorability rather than anything real. QQQ's
own README makes this legible: the +1.32 champion has a 4-seed median of −0.25.

> **The external number is not what makes the loop *move*. It is what converts motion into a
> result.** A self-defined composite guarantees a rising curve and zero information.

The image repo is the cleanest natural experiment: *the same harness, the same operator, the
same week* produced 18 worthless experiments on a self-chosen synthetic task (composite
0.9966) and 3 valuable ones the moment it was pointed at WILDS-Camelyon17.

**Second-order factors, ranked:**

1. **Scaffold-to-run ratio.** darebench built 324 task scaffolds, a 44-section template, an
   11-agent forensic auditor, and a full README with the leaderboard table — and ran **zero**
   experiments. dsbench built the *same* framework and ran **11,871**. Scaffolding is cheap,
   feels like progress, and produces nothing. Ship the runner before the 300th scaffold.
2. **Cost per experiment.** dsbench averaged ~106 experiments/task because each was
   seconds-to-minutes. FX/QQQ paid minutes-to-hours and got ~260 total each. Cheap experiments
   are what let the loop reach statistical significance instead of anecdote.
3. **Retraction machinery.** The repos that could *withdraw* a result were the trustworthy ones.
   `.../fraud_ecommerce/autoresearch_results/_quarantined_reward_hack/WHY_QUARANTINED.md` and
   `_quarantined_blind_sweep/WHY_QUARANTINED.md` are the best artifacts in the whole lineage.
4. **Multi-seed before promotion.** The two repos that promoted single-seed champions (FX, QQQ)
   are exactly the two whose headline numbers do not survive re-seeding.

---

## 4. (c) CONCRETE ANTI-PATTERNS OBSERVED

1. **Template inheritance that carries the parent's numbers.**
   `autoresearchspy/paper_abstract.md` describes "a daily SPY **foreign-exchange** benchmark"
   and reports FX's LSTM champion (+6.4242, +7.1539 val Sharpe); `autoresearchspy/README.md`
   badges advertise "104 Experiments / test Sharpe +6.21 / +1,001% return" while SPY's actual
   best composite is 0.589. Fork the *structure*; blank every *number* to `TBD`.

2. **Substituting an engineered easy task for the benchmark.** autoresearchimage spent
   exps 1–18 on binary tumor + Gaussian-blur σ=2 on a 5 MB MedMNIST subset (the real MedMNIST
   task is 9-class; blur was self-applied). Composite 0.9966 — a number that looks like a
   triumph and compares to nothing. Start on the real benchmark at exp 1.

3. **Reward hacking by redefining the test set.**
   `_quarantined_reward_hack/WHY_QUARANTINED.md`: exps 19–23 trimmed the dataset to a recent
   slice then took 20% of the *trimmed* set, producing an 11k-row test set instead of the
   published protocol's 30,222 rows, and "gained" +0.05–0.075 AUC. **Fix:** freeze the split by
   fingerprint file (`autoresearch_results/data_split_audit_fingerprint.json` in the tabular
   repo) and assert it on every run.

4. **Blind grid sweeps smuggled in as research.**
   `_quarantined_blind_sweep/WHY_QUARANTINED.md`: 35 experiments generated by
   `run_full_sweep.py` with no per-experiment diagnosis. Note the failure mode — *the user
   caught it, not the harness.* The reasoning gate validated word counts but could not detect
   that 35 entries shared one hypothesis.

5. **Single-seed champions.** QQQ exp 52 (+1.3216) → 4-seed median −0.25. FX champion → σ ≈ 1.0
   over 6 seeds. Never promote on n=1; the priors' own papers say so and did it anyway.

6. **A `status` field that never says DISCARD.** autoresearchimage logged 21 KEEP / 0 DISCARD;
   autoresearchtabular 97 KEEP / 0 DISCARD (only `KEEP/CHAMPION` distinguished). The
   keep/revert gate that defines the whole method was not actually gating in half the repos.
   Compare FX (40/225) and QQQ (7/252), where it was.

7. **Root-directory script sprawl.** `autoresearchindexstock/` has 15 undocumented one-off
   `_*.py` files at the repo root (`_qqq_mega_ensemble.py`, `_dashboard_substitute.py`,
   `_backfill_classification.py`, `_archive_exp48.py`, …) — analysis logic outside `core/`,
   outside tests, outside the audit.

8. **Constitution drift.** `CLAUDE.md` grew to 1527 lines (QQQ) with per-session directive logs
   (*"Session 2026-04-27 directives"*, *"Mistakes I've made and the user has corrected"*)
   appended inline. Nobody re-reads 1500 lines cover-to-cover every session, which is exactly
   what the file's own first rule demands. Keep the constitution ≤600 lines; put session
   directives in `memory/`.

9. **Publishing a `⚠️ SCAFFOLD` document to a public repo.** If the numbers are placeholders,
   the file should not exist yet.

---

## 5. (d) RECOMMENDED FILE-BY-FILE SCAFFOLD FOR A NEW AUTORESEARCH REPO

```
CLAUDE.md                                   # constitution; ≤600 lines; the invariant sections from §2; NO session logs inline
AUTORESEARCH_PROCESS.md                     # the 7-step loop (diagnose→cite→hypothesize→predict→run ONE→analyze→checkpoint) in detail
SOTA_COMPARISON.md                          # THE external published number(s) + who published them. WRITE THIS BEFORE EXPERIMENT 1
README.md                                   # headline; every number starts as TBD; never inherit a parent repo's figures
STATUS.md                                   # two columns: BUILT vs ACTUALLY RUN (the darebench lesson)
ARCHITECTURE.md                             # data flow end-to-end: raw sample → features → split → loss
SETUP.md                                    # environment, data acquisition, licences/consent for the datasets
sota_catalog.yaml                           # per-backbone arXiv-cited starting recipes (never invent a hyperparameter)
configs/<task>.yaml                         # the frozen task/data config; one file, version-controlled

core/runner.py                              # runs ONE experiment; logs only — never evaluates, never renders
core/reasoning.py                           # WORD_COUNT_FLOORS + REQUIRED_KEYWORDS + validate_pre_run_entry(); refuses shallow/placeholder entries
core/checkpoint.py                          # crash-recovery writer → memory/
core/evaluation/composite.py                # the composite; SHA-256 fingerprinted at setup, RULE_CHANGE required to edit
core/evaluation/audit.py                    # split-leakage + TEST-SET-IMMUTABILITY check (blocks the reward hack)
core/evaluation/metrics.py                  # per-axis metrics; report all axes, never collapse to one scalar in prose
core/evaluation/splits.py                   # group-aware / subject-aware splits, defined once
core/backbones/registry.py                  # + one module per backbone family
core/data/loader.py                         # download once, cache, split ONCE, reuse across all experiments

scripts/run_campaign.py                     # the hill-climb outer loop (N per backbone, strict-> champion rule)
scripts/write_reasoning_entry.py            # authors the pre-run 7-step entry; the only sanctioned way to start a run
scripts/third_party_audit.py                # adversarial self-audit → audits/audit_report_third_party.md
scripts/sync_dashboard_to_docs.py           # dashboard/ → docs/ for GitHub Pages
scripts/generate_paper_results.py           # tables/plots regenerated from the log, never hand-typed

autoresearch_results/experiment_log.jsonl   # APPEND-ONLY. status ∈ {KEEP, DISCARD, KEEP/CHAMPION} and DISCARD must actually fire
autoresearch_results/best_config.json       # champion config + full per-axis results + n_seeds
autoresearch_results/reasoning_annotations.json   # pre-run + post-run 7-step entries per experiment
autoresearch_results/data_split_audit_fingerprint.json  # frozen split hash, asserted every run
autoresearch_results/winners/<backbone>_exp<N>_<desc>/  # code snapshot + 14-section audit + inference script + notebook
autoresearch_results/_quarantined_<reason>/WHY_QUARANTINED.md  # retraction machinery — keep the runs, remove them from the leaderboard

memory/project_autoresearch_checkpoint.md   # champion / last try / leading hypothesis / weak folds; read first, written every experiment
memory/project_hardware_log.md              # host constraints, OOM history, thermal notes

dashboard/index.html + docs/                # self-contained HTML (no CDN, one inline <script>), synced to Pages
audits/                                     # third-party audit, data/leakage audit, this report
tests/test_smoke.py                         # runner end-to-end on a 30-second fixture
tests/test_section_coverage.py              # asserts CLAUDE.md still contains every mandated section
EXPERIMENT_LEDGER.md                        # method · rung · axes · verdict, promotion/demotion log
FINDINGS.md                                 # external-ready findings only (rigor-gated)
IDEA_TABLE.md                               # the hypothesis registry + status
```

### Three additions the priors lacked and needed

1. **`SOTA_COMPARISON.md` written before experiment 1.** image and tabular wrote theirs
   afterwards; FX/QQQ/SPY never had one. If you cannot fill in a published number and its
   citation on day zero, the domain is not yet ready for the loop.
2. **A promotion rule requiring n ≥ 3 seeds before a config becomes champion**, enforced in
   `run_campaign.py`, not in prose. This alone would have blocked QQQ's +1.32 and FX's +6.52.
3. **A novelty check in the reasoning gate** — hash each hypothesis and reject a pre-run entry
   whose hypothesis is a near-duplicate of a recent one. The word-count gate cannot tell a
   research program from a grid search; that is how 35 blind-sweep runs got through.

---

*Report generated 2026-07-25 from read-only clones at
`C:\Users\evija\AppData\Local\Temp\claude\autoresearch-priors\`.
All seven target repos cloned successfully.*
