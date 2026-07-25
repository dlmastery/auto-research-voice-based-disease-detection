# IDEA_TABLE.md — hypothesis registry

**Instantiation step 7** (`meta-skills/autoresearch-meta/SKILL.md` §5, §11). Written
2026-07-25. Composite fingerprint in force: `37e745ed9b0b` (`COMPOSITE.md`).

**Every row below is `UNTESTED`.** Per `CLAUDE.md` R7 a hypothesis whose falsifier has not been
*executed* is `UNTESTED`, never `SUPPORTED` — the sibling program shipped six `SUPPORTED`
verdicts whose falsifiers never ran. Nothing in this file may be cited as a result.

---

## How to read this table

| field | meaning |
|---|---|
| **Claim** | the one-line proposition this program will test |
| **Audited claim** | the *specific published statement* being re-tested, with its citation. An audit hypothesis without a named target is not an audit — it is an experiment. |
| **Falsifier** | the pre-registered quantitative condition that refutes the claim. Registered *before* the run and executed (R7). |
| **Predicted Δ** | numeric effect + direction, stored before the run (7-step ritual, step 4) |
| **Tier** | `SCREENING` (n ≤ 3, may never be called a result) or `EVALUATION` (n ≥ 8 + the full statistical contract). **Pre-classified here, in version control, before the sweep.** Reclassifying a loser as screening afterwards is HARKing and a BLOCKER. |
| **m / n** | `m` = the pre-declared multiplicity family size for that hypothesis; `n` = required paired replicates. Both must satisfy the power check below. |
| **Axis moved** | the single axis from `AXIS_TAXONOMY.md` this hypothesis perturbs |
| **Status** | `UNTESTED` → `RUNNING` → `HOLDS` / `ATTENUATED` / `BREAKS` / `INCONCLUSIVE` / `NOT_REPRODUCIBLE` / `BROKEN` |

### The power check (R6), and what `n` counts here

`CLAUDE.md` R6: a paired Wilcoxon at n has minimum attainable two-sided
`p = 2/2ⁿ`; Holm's tightest threshold for a family of m is `0.05/m`; the plan is satisfiable
only if `2/2ⁿ ≤ 0.05/m`.

| n | `min_attainable_p(n) = 2/2ⁿ` | largest satisfiable m |
|---|---|---|
| 7 | 0.015625 | **3** — this is why R6 raised the floor; n=7 dies at m≥4 |
| 8 | 0.007813 | 6 |
| 9 | 0.003906 | 12 |
| 10 | 0.001953 | **25** |
| 12 | 0.000488 | 102 |

**`n` counts paired repeated speaker-disjoint partitions**, not weight seeds — the dominant
variance in a frozen-embedding + probe pipeline is *which speakers land where*, not
initialisation (`AXIS_TAXONOMY.md` §3). Because probes are near-free, n is cheap here and every
evaluation-tier row below is set to n ≥ 10 rather than the R6 minimum of 8.

**Multiplicity is per-hypothesis and not pooled.** Each row declares its own family m; the
program does not apply a single program-wide Holm correction across hypotheses, because the
hypotheses are not a single sweep family. Every logged test records its family membership so a
reviewer can re-correct differently if they disagree.

**Correlation caveat (carried from `AXIS_TAXONOMY.md` §5(i)).** Repeated partitions of one
finite speaker pool are positively correlated, so Wilcoxon over them is anti-conservative. Every
evaluation-tier row therefore reports the Wilcoxon p **and** a speaker-level cluster-bootstrap
interval, and **the more conservative binds the verdict**. This adds to the rigor contract; it
does not relax it.

---

## The registry

### Core family (V1–V5) — the five laptop-scale gaps from `corpus/SURVEY_sota_methods.md` §(e)

---

#### V1 — "SSL beats handcrafted features" may be an artifact of leaky protocols

| | |
|---|---|
| **Claim** | Under simultaneously speaker-disjoint *and* demographically balanced splits, frozen SSL/health embeddings do not reliably beat eGeMAPS. |
| **Audited claim** | SpeechDx ranks Whisper-enc (MRR 0.44) > Qwen3-TTS-Tokenizer (0.40) > WavLM (0.38) and states "no current representation generalizes reliably across the clinical speech landscape" — Bhalla, Kieu, Merchant, de Lara, Mariakakis, 2026, *SpeechDx: A Multi-Task Benchmark for Clinical Speech AI* (arXiv:2606.17339). The audited proposition is the field's *derived* habit of treating SSL > handcrafted as settled; SpeechDx itself already qualifies it, and the head-to-head against eGeMAPS under both controls simultaneously has not been run with seed statistics. |
| **Falsifier** | If eGeMAPS lands **within 2σ_seed** of the best of {HeAR, WavLM-base+, Whisper-small-enc} on **≥ 2 of 3 corpora** under `A3 = speaker_disjoint + demographically_matched`, `A4 = fit_per_fold`, the "SSL wins" claim is falsified for this task family. |
| **Predicted Δ** | eGeMAPS trails the best SSL encoder by **0.02–0.06 AUC** on SVD (a real but small gap) and by **< 0.02** — i.e. inside the noise band — on Coswara and COUGHVID. Direction: the gap *shrinks* by ≥ 0.03 AUC relative to the same comparison under `A3 = random_recording`. |
| **Tier** | `EVALUATION` |
| **m / n** | m = **9** (3 encoders × 3 corpora, each vs eGeMAPS) · n = **10** → 0.001953 ≤ 0.05/9 = 0.005556 ✓ |
| **Axis moved** | A5 (representation), with A3 pinned at the strict value; the *leaky* comparison at A3 = `random_recording` is the paired reference condition |
| **Datasets** | SVD · Coswara · COUGHVID |
| **Cost** | openSMILE is CPU-only; embeddings extracted once and cached. No GPU beyond one extraction pass per encoder. |
| **Status** | **UNTESTED** |

---

#### V2 — Speaker-identity subspace ablation: how much of the "disease" signal is identity?

| | |
|---|---|
| **Claim** | A large fraction of frozen-embedding disease discrimination lives in a low-rank speaker-identity subspace, and removing it collapses AUC further than a variance-matched random projection of the same rank does. |
| **Audited claim** | Yeh, Sun, Mahapatra, Chandra, Mower Provost, Sisman, 2026, *Who is Speaking or Who is Depressed? A Controlled Study of Speaker Leakage in Speech-Based Depression Detection* (arXiv:2604.14354): speaker overlap significantly boosts performance, accuracy drops sharply on unseen speakers, and a DANN **fails to close the gap**; they conclude identity reliance is "a property of current speech representations rather than a model-specific limitation." That paper establishes the effect by *measurement*. The mechanistic test — estimate the identity subspace, project it out, re-measure — has not been run, and their DANN result predicts it will be hard to remove. |
| **Falsifier** | Two-sided, both pre-registered. **(a)** If projecting out the rank-k speaker subspace collapses disease AUC toward chance while a **variance-matched** same-rank random projection does not — i.e. `D(k) = AUC_rand(k) − AUC_spk(k)` has a Holm-corrected 95% CI excluding 0 and `AUC_spk(k)`'s CI includes 0.5 — the clinical-validity claim for that model/dataset pair is falsified. **(b)** Conversely, if `D(k)` is within the noise band for all k while `AUC_spk(k)` stays well above chance, the *hypothesis* is falsified and the audited result is **strengthened** — that becomes the positive control the field currently lacks. |
| **Predicted Δ** | At k = 16: `AUC_spk` drops **0.10–0.25** from `AUC_full`; the variance-matched random control drops **< 0.05**; so `D(16)` ∈ **[0.06, 0.22]**, positive. Manipulation check: speaker-verification accuracy on the projected embeddings falls from ~0.90 to **< 0.30**. |
| **Tier** | `EVALUATION` |
| **m / n** | m = **14** (7 ranks k ∈ {1,2,4,8,16,32,64} × 2 corpora) · n = **10** → 0.001953 ≤ 0.05/14 = 0.003571 ✓ |
| **Axis moved** | A9 (`subspace_projection`), with its mandatory A12 controls |
| **Datasets** | SVD (≥ 2 vocalisations/speaker, 2,043 speakers) · Coswara (9 streams/participant). **COUGHVID is excluded** — no speaker identifiers, so the subspace cannot be estimated. |
| **Cost** | Pure linear algebra on cached embeddings. Essentially free — this is the cheapest decisive hypothesis in the registry and is therefore **first** (see `PREREGISTRATION.md`). |
| **Status** | **UNTESTED** |

---

#### V3 — Where does health-specific pretraining actually cross general-purpose pretraining?

| | |
|---|---|
| **Claim** | Health-acoustic pretraining buys sample-efficiency, not ceiling: HeAR leads at small labelled-set size and is overtaken by Whisper-enc as n grows. |
| **Audited claim** | Two results in apparent tension. (i) SpeechDx (arXiv:2606.17339) ranks general encoders above domain-specific ones on average. (ii) Sanap, Desikan, Lobaton, 2026, *Beyond Classification: A Cough Regression Benchmark for Respiratory Acoustic Foundation Models* (arXiv:2606.15436): HeAR and M2D+Resp reach near-full performance at **50** samples where OPERA needs **400**. Both can be true only if the crossover exists — and it has never been plotted head-to-head. |
| **Falsifier** | Sweep labelled-set size n_train ∈ {25, 50, 100, 200, 400, 800, all}, subject-disjoint. **If HeAR never crosses Whisper-enc at any n_train on any of the 3 tasks** (Holm-corrected), the "health pretraining is the right prior" claim is falsified and reduces to a low-data convenience argument. If HeAR wins low and loses high, the crossover point is the deliverable. |
| **Predicted Δ** | HeAR leads by **0.04–0.10 AUC** at n_train ≤ 50; crossover at n_train ∈ **[200, 800]**; Whisper-enc leads by **0.01–0.04 AUC** at full data. |
| **Tier** | `EVALUATION` |
| **m / n** | m = **42** (2 contrasts {HeAR vs Whisper-enc, HeAR vs WavLM} × 7 sizes × 3 tasks) · n = **12** → 0.000488 ≤ 0.05/42 = 0.001190 ✓ |
| **Axis moved** | A5 (representation), with training-set size as the pre-registered sweep parameter |
| **Datasets** | SVD (voice pathology) · Coswara (respiratory) · COUGHVID (respiratory, OOD) |
| **Cost** | One embedding-extraction pass per encoder, then trivial probe training. |
| **Status** | **UNTESTED** |

---

#### V4 — Does calibration degrade *with* distribution shift, or independently of it?

| | |
|---|---|
| **Claim** | Calibration error does **not** track AUC collapse under corpus shift, so model confidence is unusable as an out-of-domain detector. |
| **Audited claim** | Kafentzis & Selisios, 2026, *Tuberculosis Screening from Cough Audio: Baseline Models, Clinical Variables, and Uncertainty Quantification* (arXiv:2601.07969, *Sensors* 26(4):1223) introduces uncertainty quantification for cough screening and motivates it by the field's protocol heterogeneity. Separately, de Brito, de Souza, Gauy, Finger, Candido Junior, 2025, *Fine-tuning Pre-trained Audio Models for COVID-19 Detection* (arXiv:2511.14939) documents cross-dataset AUC collapse to **0.43–0.68**. **Nobody reports cross-corpus ECE / Brier decomposition** — the implicit assumption that uncertainty flags shift is untested. |
| **Falsifier** | Measure ECE, Brier, and reliability curves within- and cross-corpus on COUGHVID↔Coswara (both directions) and on SVD→VOICED. **If ECE stays flat within its own seed noise band while AUC falls from ~0.80 to ~0.55**, confidence is falsified as a shift detector — a negative result with direct deployment consequences. Raw and temperature-scaled variants reported separately. |
| **Predicted Δ** | AUC falls **0.18–0.30** cross-corpus; raw ECE rises only **0.00–0.04**, i.e. inside or barely outside its noise band. Temperature scaling fitted in-domain **worsens** cross-corpus ECE by **0.02–0.08**. |
| **Tier** | `EVALUATION` |
| **m / n** | m = **6** (3 corpus pairings × {raw, temperature-scaled}) · n = **10** → 0.001953 ≤ 0.05/6 = 0.008333 ✓ |
| **Axis moved** | A8 (calibration), with A1 corpus-pairing as the pre-registered shift condition |
| **Datasets** | Coswara ↔ COUGHVID · SVD → VOICED |
| **Cost** | Free once predictions exist; reuses the V1/V3 runs. |
| **Status** | **UNTESTED** |

---

#### V5 — Zero-shot audio-LLMs as a leakage-free reference point

| | |
|---|---|
| **Claim** | The gap between a supervised probe and a zero-shot audio-LLM is a cheap, model-free estimate of how much leakage a protocol admits, because a zero-shot model has no training split and therefore cannot leak speaker identity, demographics, or preprocessing statistics. |
| **Audited claim** | Shahin, Ahmed, Epps, 2025 (arXiv:2506.17351) report Qwen2-Audio zero-shot cognitive-impairment detection "comparable to supervised methods" and frame it as a convenience result, **not** as a measurement instrument. Cross-check required against Kabir & Munira, 2026 (arXiv:2605.24806): handcrafted features + a text LLM are more reliable than raw audio for low-resource languages, so the zero-shot reference must be reported in **both** input formats or it is language-confounded. |
| **Falsifier** | Compute `Δ_leaky = AUC_sup(random_recording split) − AUC_zeroshot` and `Δ_honest = AUC_sup(speaker_disjoint + demographically_matched) − AUC_zeroshot`. **If Δ_leaky ≈ Δ_honest (overlapping bootstrap CIs) on ≥ 2 of 3 datasets**, the proposed leakage estimator is falsified — the gap tracks supervised capacity, not leakage. If `Δ_leaky ≫ Δ_honest` consistently across ≥ 3 datasets, the field gains a leakage audit that needs no re-splitting of the original data. |
| **Predicted Δ** | `Δ_leaky − Δ_honest` ∈ **[0.08, 0.25] AUC**, positive, on SVD and Coswara. Zero-shot absolute AUC is expected to be **low (0.55–0.68)** — the hypothesis is about the *gap*, not the zero-shot number. |
| **Tier** | **`SCREENING` at registration** (n ≤ 3), with a pre-declared promotion condition: promote to `EVALUATION` at n = 10, m = 3 **only if** zero-shot throughput permits ≥ 10 full passes per dataset inside the foreground GPU windows available. If it does not, V5 ships as screening and is labelled as such — it is never re-described as a result. |
| **m / n** | screening n ≤ 3 · promotion target m = **3** (3 datasets), n = **10** → 0.001953 ≤ 0.016667 ✓ (n = 8 would also satisfy m = 3) |
| **Axis moved** | A12 (control condition: `zero-shot audio-LLM`), paired across A3 values |
| **Datasets** | SVD · Coswara · COUGHVID |
| **Cost** | **The only real GPU cost in the registry.** 4-bit Qwen2-Audio-7B inference; one foreground eval window per dataset, N capped per condition. Host RAM, not VRAM, is the binding constraint. |
| **Status** | **UNTESTED** |

---

### Exploration family (V6–V7) — the R9 off-champion quota

`CLAUDE.md` R9 requires ≥ 1 in 5 experiments to be off-champion, because pure coordinate
descent produced **zero original ideas** across a measured 3,222-run loop. V6 and V7 exist so
that quota is satisfiable by *registered* work rather than improvised work. Both also have high
prior odds of breaking, which `audits/NOVELTY_CRITIQUE.md` §d.3 identifies as the correct
target-selection criterion.

---

#### V6 — Preprocessing-fit leakage is corpus-specific and cannot be assumed small

| | |
|---|---|
| **Claim** | The inflation from fitting the scaler/normaliser before splitting varies by an order of magnitude across corpora, so "we scaled before splitting but it's a small effect" is not defensible on an unmeasured corpus. |
| **Audited claim** | *Feature scaling induced data leakage quantification in machine learning-based voice pathology detection*, *Applied Soft Computing* (`S1568494626007970`): 1,000 repetitions per configuration; effect **−0.14 to +0.14 pp on SVD** but **−8.3 to +7.8 pp on VOICED**. Leakage can *degrade* as well as inflate. This is a published measurement on two corpora; the audited proposition is its generalisation to the corpora this program actually uses, and to *embedding* features rather than handcrafted ones. |
| **Falsifier** | If the `fit_on_all` − `fit_per_fold` AUC difference has a 95% CI contained within ±0.01 AUC on **all** of SVD, Coswara, COUGHVID for **both** eGeMAPS and a frozen SSL representation, the "corpus-specific magnitude" claim is falsified for this pipeline family and preprocessing scope can be de-prioritised as an audit axis. |
| **Predicted Δ** | Effect **< 0.01 AUC on SVD** (reproducing the published near-null) and **> 0.03 AUC on at least one** of Coswara/COUGHVID; sign not predicted (the published result shows both directions). |
| **Tier** | `EVALUATION` |
| **m / n** | m = **6** (3 corpora × 2 representations) · n = **10** → 0.001953 ≤ 0.008333 ✓ |
| **Axis moved** | A4 (preprocessing-fit scope), A3 pinned at `speaker_disjoint` |
| **Datasets** | SVD · Coswara · COUGHVID |
| **Cost** | Free — re-fits a scaler on cached features. |
| **Status** | **UNTESTED** |

---

#### V7 — The Clever-Hans silence shortcut beyond the Pitt corpus

| | |
|---|---|
| **Claim** | Non-phonatory signal alone (silence/pause structure, recording-level duration and intensity statistics) achieves a substantial fraction of headline performance on voice-health corpora outside the one where the effect was first documented. |
| **Audited claim** | Liu, Feng, Yuan, Ling, Interspeech 2024, *Clever Hans Effect Found in Automatic Detection of Alzheimer's Disease through Speech* (arXiv:2406.07410): **near-100% AD detection accuracy from silent segments alone** in the Pitt corpus, dropping to ~80% on other datasets or preprocessed Pitt. The audited proposition is the implicit assumption that this is a Pitt-specific artifact. `audits/NOVELTY_CRITIQUE.md` §d.3 warns that re-deriving known Pitt/DAIC-WOZ results is redundant — **so this hypothesis deliberately targets corpora that have not been checked**, and Pitt itself is DUA-gated for us anyway. |
| **Falsifier** | If `silence_only` and `duration+intensity_only` baselines both score **< 0.60 AUC** on all of SVD, Coswara and COUGHVID under `A3 = speaker_disjoint`, the generalisation claim is falsified and the shortcut is confirmed Pitt-specific for this corpus set. |
| **Predicted Δ** | `silence_only` AUC ∈ **[0.55, 0.70]** on Coswara (crowd-recorded, heterogeneous protocol) and ∈ **[0.50, 0.60]** on SVD (controlled studio protocol, sustained vowels) — i.e. the shortcut is predicted to scale with acquisition heterogeneity, not with disease. |
| **Tier** | `EVALUATION` |
| **m / n** | m = **6** (3 corpora × 2 shortcut feature sets) · n = **10** → 0.001953 ≤ 0.008333 ✓ |
| **Axis moved** | A5 (representation → confound-only feature sets), which is also the `AUC_conf_max` battery of `COMPOSITE.md` §3 |
| **Datasets** | SVD · Coswara · COUGHVID |
| **Cost** | CPU-only; VAD + functionals. |
| **Status** | **UNTESTED** |

---

## Summary

| id | axis | tier | m | n | min p | Holm 0.05/m | satisfiable | datasets | status |
|---|---|---|---|---|---|---|---|---|---|
| **V1** | A5 | EVALUATION | 9 | 10 | 0.001953 | 0.005556 | ✓ | SVD, Coswara, COUGHVID | UNTESTED |
| **V2** | A9 | EVALUATION | 14 | 10 | 0.001953 | 0.003571 | ✓ | SVD, Coswara | UNTESTED |
| **V3** | A5 | EVALUATION | 42 | 12 | 0.000488 | 0.001190 | ✓ | SVD, Coswara, COUGHVID | UNTESTED |
| **V4** | A8 | EVALUATION | 6 | 10 | 0.001953 | 0.008333 | ✓ | Coswara↔COUGHVID, SVD→VOICED | UNTESTED |
| **V5** | A12 | SCREENING (promotion pre-declared) | 3 | ≤3 → 10 | 0.001953 | 0.016667 | ✓ | SVD, Coswara, COUGHVID | UNTESTED |
| **V6** | A4 | EVALUATION | 6 | 10 | 0.001953 | 0.008333 | ✓ | SVD, Coswara, COUGHVID | UNTESTED |
| **V7** | A5 | EVALUATION | 6 | 10 | 0.001953 | 0.008333 | ✓ | SVD, Coswara, COUGHVID | UNTESTED |

**Every plan in this table is arithmetically satisfiable under R6.** The runner must recompute
`2/2ⁿ ≤ 0.05/m` at launch from the config's own declared `m` and `n` and refuse to start
otherwise — a rule that is checked only in a markdown table is the "decorative rigor" failure
mode (`CLAUDE.md` §9 failure 4).

**Execution order.** V2 first (cheapest decisive, pure linear algebra, pre-registered in
`PREREGISTRATION.md`) → V6 (free, and its result determines whether A4 must be pinned in every
later run) → V7 (free, and it populates the `COMPOSITE.md` confound battery that V1/V3 depend
on) → V1 → V3 → V4 (free once V1/V3 predictions exist) → V5 (GPU-gated, last).

**Dataset dependency.** V1–V7 run entirely on the three open corpora (SVD, Coswara, COUGHVID) —
no row in this registry is blocked on a DUA. PROCESS-2 and Bridge2AI-Voice are deliberately
absent: PROCESS-2 fails the ≥500/class bar and is screening-tier only, and Bridge2AI's raw
audio needs institutional sign-off. Both applications should nonetheless be started in parallel
now (`CLAUDE.md` §4.1: "dataset access is the binding constraint, not compute"), so that a
second registry generation is not gated on paperwork.

---

*Internal QA pass — independent external review pending. Every citation above is carried over
from `corpus/SURVEY_sota_methods.md`, `corpus/SURVEY_datasets.md` or
`audits/NOVELTY_CRITIQUE.md`, all mechanically verified 2026-07-25; no identifier in this file
was introduced from memory (R10). No number here is a result — the "Predicted Δ" column is
pre-registration, not measurement (R2).*
