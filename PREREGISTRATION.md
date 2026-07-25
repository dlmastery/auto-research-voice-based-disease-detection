# PREREGISTRATION — V2: Speaker-identity subspace ablation

**Hypothesis id:** V2 (`IDEA_TABLE.md`) · **Axis moved:** A9 `subspace_projection`
(`AXIS_TAXONOMY.md`) · **Composite fingerprint in force:** `37e745ed9b0b` (`COMPOSITE.md`)
**Written:** 2026-07-25 · **Status: FROZEN-PENDING-COMMIT — no data has been touched.**

> **Freeze rule.** This document must be committed **before** the first embedding is loaded, and
> its commit SHA recorded in `experiment_log.jsonl` for every V2 row. Any edit after the freeze
> commit is a protocol amendment: it must be a new section appended below (§14), dated, with the
> reason — never an in-place edit. Reclassifying, re-choosing the primary rank, or re-defining
> the falsifier after seeing data is HARKing and is a BLOCKER (`CLAUDE.md` R6/§9 failure 4).

**Why V2 is first.** It is the cheapest decisive hypothesis in the registry: pure linear algebra
on cached frozen embeddings, no GPU beyond one extraction pass, and it has a two-sided falsifier
so *both* outcomes are publishable (`CLAUDE.md` R8).

---

## 1. Hypothesis

> In frozen speech-embedding spaces, a substantial fraction of apparent voice-disease
> discrimination is carried by a low-rank **speaker-identity** subspace. Removing that subspace
> reduces disease AUC significantly more than removing a **variance-matched random** subspace of
> the same rank does.

**Mechanism.** Speech encoders are trained on objectives (ASR, masked reconstruction, contrastive
alignment) for which speaker identity is highly predictive, so identity occupies dominant
directions of the representation. Because each speaker carries exactly one disease label and
several recordings, a probe can reach high AUC by memorising speaker-characteristic directions
that happen to correlate with the label in the training partition. Yeh et al. show this survives
adversarial training, which is why we test *explicit geometric removal* rather than another
adversarial method.

**Audited claim.** Yeh, Sun, Mahapatra, Chandra, Mower Provost & Sisman, 2026, *Who is Speaking or
Who is Depressed? A Controlled Study of Speaker Leakage in Speech-Based Depression Detection*
(arXiv:2604.14354) — speaker overlap significantly boosts performance, accuracy drops sharply on
unseen speakers, and a DANN fails to close the gap; they conclude identity reliance is "a property
of current speech representations rather than a model-specific limitation." Their evidence is
*measurement* (varying overlap). The direct mechanistic test — estimate the subspace, project it
out, re-measure — has not been run, and their DANN result predicts it will be hard.

**Prior-art re-check (R11).** The nearest competing work must be re-searched immediately before
any promotion of a V2 result to a contribution, and cited first. As of the corpus verification
date (2026-07-25) no voice-health paper in `corpus/` performs an identity-subspace projection with
a variance-matched control.

---

## 2. Pre-registered falsifier (two-sided)

Let, for rank k, on held-out speaker-disjoint test partitions:

- `AUC_full` — disease AUC on unmodified embeddings
- `AUC_spk(k)` — disease AUC after projecting out the rank-k speaker subspace
- `AUC_rand(k)` — disease AUC after projecting out a **variance-matched** random rank-k subspace
- `D(k) = AUC_rand(k) − AUC_spk(k)` — **the primary statistic**

**(F-a) The clinical-validity claim is falsified** for a given (representation, corpus) pair if,
at any pre-registered k, the Holm-corrected 95% CI on `D(k)` excludes 0 **and** the 95% CI on
`AUC_spk(k)` includes 0.5. Interpretation: the reported performance was priced on identity, not
pathology.

**(F-b) This hypothesis (V2) is falsified** if, for all seven k, `D(k)`'s 95% CI lies entirely
within the measured noise band ±2σ_seed **and** `AUC_spk(k)`'s CI excludes 0.5 at k ≥ 16
**and** the §6 manipulation check passed. Interpretation: the discrimination survives identity
ablation, the audited concern does not bind for this pair, and **the result is a positive control
the field currently lacks** — which is a publishable outcome of equal standing (R8).

Anything else is `INCONCLUSIVE`. There is no third interpretive option available after the fact.

---

## 3. Metrics

**Primary metric.** `D(k)`, computed per test partition, paired across the three conditions
(unmodified / speaker-projected / variance-matched-random-projected) on **identical** partitions.

**Headline cell (declared now).** k\* = **16**, representation = **WavLM-base+ mean-pooled**,
corpus = **SVD**. All 14 confirmatory cells are Holm-corrected together (§7); the headline cell is
designated in advance only so that the abstract sentence is fixed before the data are seen.

**Secondary metrics** (reported for every cell, never substituted for the primary):

| metric | why |
|---|---|
| `AUC_spk(k)` and `AUC_rand(k)` absolute, with CIs | the levels behind the difference |
| `AUC_full` | the reference level |
| retention `AUC_spk(k) / AUC_full` | comparability across corpora |
| UAR at the Youden threshold | SVD's reference metric is UAR (arXiv:2410.10537 deliberately omits accuracy because of class imbalance) |
| ECE (raw and temperature-scaled, fitted in-fold) | `COMPOSITE.md` calibration term |
| per-sex and per-age-band AUC | subgroup term; SVD's own reference number is reported per sex (85.61 F / 84.69 M) |
| variance removed by each projection (fraction of total feature variance) | proves the variance match held |
| speaker-ID top-1 accuracy before/after | the manipulation check (§6) |
| `AUC_conf_max` over the pinned confound battery (`COMPOSITE.md` §3) | the honest bar |
| `AUC_leaky` under `A3 = random_recording` | the protocol-inflation term |

---

## 4. The pipeline, fully specified

Everything below is pinned. Any deviation makes the run a different experiment.

| axis | pinned value |
|---|---|
| **A1 corpus** | SVD (primary) · Coswara (replication). COUGHVID **excluded** — no speaker identifiers, subspace is unestimable. |
| **A2 label** | SVD: `binary_pathology_vs_healthy`, pathology subset pinned to the full organic+functional set as distributed, sustained vowel /a/ at normal pitch only, one session per speaker. Coswara: `covid_positive vs covid_negative`, `recovered` excluded, heavy-cough stream only. |
| **A3 split** | `speaker_disjoint`, sex-stratified, 80/20, `GroupKFold`-style grouping on `speaker_id`; **10 repeated partitions, seeds 0–9**. Speaker-overlap assertion runs before every fit. |
| **A4 preprocessing scope** | `fit_per_fold` for **everything**: scaler, LDA/subspace estimation, PCA for the variance match, probe, calibrator. Nothing is fitted on or across the test partition. |
| **A5 representation** | `WavLM-base+` (headline) and `HeAR` (secondary), frozen, extracted once, cached to disk. No fine-tuning. |
| **A6 pooling** | `mean` over frames for WavLM; HeAR's native 2-s clip embeddings averaged over clips. |
| **A7 head** | `logistic_regression`, L2, `C` selected by inner 5-fold CV **inside the training partition only**, grid `C ∈ {0.01, 0.1, 1, 10, 100}`. Identical head and identical grid in every condition. |
| **A8 calibration** | `temperature_scaling`, fitted on an inner validation slice of the training partition. Raw scores also retained. |
| **A9 confound control** | `subspace_projection(k, source=speaker_LDA_within_class)`, k ∈ {1, 2, 4, 8, 16, 32, 64} |
| **A10 augmentation** | `none` |
| **A11 aggregation** | `speaker_level(mean_prob)` for all headline numbers; recording-level reported alongside |

### 4.1 Subspace estimation — and the hazard that would break this experiment

Each speaker carries exactly **one** disease label. A naive between-speaker scatter matrix
therefore *contains* the between-class scatter: projecting it out would destroy disease AUC by
construction, and the result would be an artifact, not a finding. **This is the single most
likely way V2 produces a spurious positive.**

**Pinned mitigation — within-class between-speaker scatter.** On the training partition only:

1. Standardise features (scaler fit on the training partition).
2. Compute each speaker's mean embedding `μ_s`, and each **class**'s mean `μ_c(s)`.
3. Centre each speaker mean by *its own class* mean: `ν_s = μ_s − μ_c(s)`.
4. `S_B = Σ_s n_s · ν_s ν_sᵀ` over training speakers (`n_s` = that speaker's recording count).
5. `U_k` = top-k eigenvectors of `S_B`, orthonormalised.
6. Projection `P_k = I − U_k U_kᵀ`, applied identically to training and test embeddings.

**Pre-run orthogonality gate.** Let `w = μ_positive − μ_negative` (the class direction on the
training partition). Require `max_j |cos(U_k[:,j], w)| < 0.10` and
`‖U_kᵀ ŵ‖ < 0.20` for every k. **If this gate fails the experiment is `BROKEN`, not a result** —
the subspace is contaminated with class information and any collapse it produces is circular.
This gate runs and is logged before any AUC is computed.

### 4.2 The variance-matched random control

A plain random orthonormal rank-k subspace removes *less* variance than the top-k eigenvectors of
a scatter matrix, so comparing against it is a strawman and would manufacture a positive result.
Both controls are therefore run:

- **C-rand-plain** — k directions drawn uniformly from the Haar measure on the Stiefel manifold,
  orthonormalised. Reported, but **not** the primary comparator.
- **C-rand-varmatched** — the **primary comparator**. Built from the training-partition PCA basis
  by greedily selecting k principal directions whose cumulative fraction of total feature variance
  matches the fraction removed by `U_k` to within **1.0 percentage point**. If no k-subset matches
  within tolerance, the tolerance failure is logged and that cell is `INCONCLUSIVE` — the tolerance
  is never widened after the fact.

`D(k)` is defined against **C-rand-varmatched**. `D_plain(k)` is reported as a secondary.

---

## 5. Controls — all six are required, none is optional

| # | control | what it rules out | pre-registered pass condition |
|---|---|---|---|
| C1 | **variance-matched random projection** (§4.2) | "any rank-k removal hurts" | is the comparator; no separate pass condition |
| C2 | **plain random projection** | quantifies how much of C1's effect is variance removal per se | reported |
| C3 | **label shuffle** — labels permuted within the training partition, whole pipeline re-run | the whole result being an artifact (`meta-skills/autoresearch-shuffle-test`) | `AUC_full` under shuffle must lie within `0.5 ± 2σ_null`; a leak here fails the row via `COMPOSITE.md`'s `lambda_ctrl = 3.00` and blocks promotion |
| C4 | **class-direction positive control** — project out the rank-1 `μ_positive − μ_negative` direction | that the projection machinery works at all | disease AUC **must** fall substantially; if it does not, the code is `BROKEN` |
| C5 | **confound battery** (`COMPOSITE.md` §3): age, sex, age+sex, duration, RMS intensity, SNR, silence-only, device/site where applicable, metadata-only | the claim living below the honest bar | reported as `AUC_conf_max`; the V2 finding is claimed only for the margin **above** it (`CLAUDE.md` §4.3.2) |
| C6 | **leaky reference** — the identical pipeline under `A3 = random_recording` | that "speaker-disjoint" is doing anything | reported as `AUC_leaky`; the gap `AUC_leaky − AUC_full` is itself a ledger row |

---

## 6. The manipulation check — the instrument gate (R3)

`CLAUDE.md` §1: *no claim may rest on an unvalidated instrument.* Here the instrument is the
**subspace estimator**, and it must be shown to do what it claims before its output is
interpreted.

**Check.** Closed-set speaker identification over the training speakers, using a held-out slice of
*their own* recordings that is disjoint from the disease-evaluation partition. Multinomial logistic
regression, fitted on the training partition, evaluated before and after `P_k`.

**Gate:** top-1 speaker-ID accuracy must fall by **≥ 60 % relative** at k = 16 (e.g. 0.90 → ≤ 0.36).

- **Gate passes** → `D(k)` is interpretable.
- **Gate fails** → the row is `BROKEN`, not a null. A null `D(k)` under a failed manipulation
  check is exactly the "cannot distinguish no-effect from cannot-detect-an-effect" defect that
  invalidated five weeks of the sibling program (`CLAUDE.md` §1). It is logged with
  `failure_reason: subspace_estimator_ineffective` and the hypothesis returns to `UNTESTED`.

**σ_null** (used by the `lambda_ctrl` term and the C3 pass condition) is measured empirically as
the SD of the shuffled-label AUC across the same 10 partitions. It is never a rule-of-thumb (R4).

---

## 7. n, multiplicity, and the power calculation

- **n = 10** paired repeated speaker-disjoint partitions (seeds 0–9). Every condition is evaluated
  on **identical** partitions so all comparisons are paired.
- **Confirmatory family: m = 14** — 7 ranks × 2 corpora, on the headline representation. The HeAR
  secondary representation is **exploratory** and is labelled as such; it is not folded into m and
  no confirmatory claim rests on it.
- **Power check (R6):** `min_attainable_p(10) = 2/2¹⁰ = 0.001953`; Holm's tightest threshold is
  `0.05/14 = 0.003571`. **0.001953 ≤ 0.003571 ⇒ the plan is arithmetically satisfiable.**
  (For contrast: n = 8 gives 0.007813 > 0.003571 and **would not be satisfiable** at m = 14 — which
  is why n is set above the R6 floor rather than at it.)
- The runner recomputes this at launch from the config's own `m` and `n` and **refuses to start**
  if it fails.

**Independence caveat, pre-registered (`AXIS_TAXONOMY.md` §5(i)).** The 10 partitions are drawn
from one finite speaker pool and are positively correlated, so Wilcoxon over them is
anti-conservative. Both intervals below are computed and **the more conservative binds the
verdict**. This is declared now, not chosen after seeing which is friendlier.

---

## 8. Statistical tests

1. **Paired Wilcoxon signed-rank** on `D(k)` across the 10 partitions, two-sided.
2. **95 % BCa bootstrap CI** on `D(k)`, **10,000 resamples**, resampled at the **speaker** level
   (cluster bootstrap). Recording-level resampling would understate the interval because
   recordings within a speaker are not independent.
3. **Holm–Bonferroni** across the m = 14 confirmatory cells.
4. **Empirical noise band** — 2σ from same-config, different-seed runs, measured on this corpus and
   representation. Never assumed.
5. **Ordinal gate for `EXTERNAL-READY`** — the worst of the 10 `AUC_spk(k)` partitions must beat
   the best of the 10 `AUC_rand(k)` partitions (or vice versa, for F-b). The four-part contract
   alone is not sufficient.

---

## 9. Pre-registered outcome table

Filled in **after** the run. The interpretation column is fixed now, so no post-hoc reading is
available.

| observed | verdict | what goes in the ledger |
|---|---|---|
| Holm-corrected CI on `D(k*)` excludes 0, `AUC_spk(k*)` CI includes 0.5, manipulation check passed, C3/C4 pass | **BREAKS** | the audited pair's discrimination is priced on speaker identity; report the k at which it collapses |
| Holm-corrected CI on `D(k)` excludes 0 but `AUC_spk(k)` CI excludes 0.5 | **ATTENUATED** | identity carries part of the signal; report the surviving margin above `AUC_conf_max` |
| `D(k)` inside ±2σ_seed for all k, `AUC_spk(k≥16)` CI excludes 0.5, manipulation check passed | **HOLDS** (V2 falsified by F-b) | a positive control: discrimination survives identity ablation. Published with equal prominence (R8). |
| manipulation check fails, or the §4.1 orthogonality gate fails, or C4 does not collapse AUC | **BROKEN** | `failure_reason` logged; hypothesis returns to `UNTESTED`; no scientific interpretation is offered |
| C3 label-shuffle AUC outside `0.5 ± 2σ_null` | **BROKEN** | the pipeline measures an artifact; fix before any interpretation |
| CIs overlap 0 but the noise band is wider than the predicted effect (0.06–0.22) | **INCONCLUSIVE / UNDERPOWERED** | report the achieved noise band and the n needed; do **not** report it as a null |
| variance match cannot be achieved within 1.0 pp | **INCONCLUSIVE** for that cell | tolerance is not widened |

---

## 10. Predictions, stored before the run (7-step ritual, step 4)

At k\* = 16 on SVD / WavLM-base+:

- `AUC_full` ∈ **[0.80, 0.90]** (SVD's published reference is UAR 85.22, arXiv:2410.10537)
- `AUC_spk(16)` drops **0.10–0.25** from `AUC_full`
- `AUC_rand(16)` drops **< 0.05** from `AUC_full`
- **`D(16)` ∈ [0.06, 0.22], positive**
- speaker-ID top-1 falls from ≈ 0.90 to **< 0.30**
- `AUC_conf_max` ∈ **[0.55, 0.68]** (age+sex expected to be the strongest battery member)
- `AUC_leaky − AUC_full` ∈ **[0.03, 0.12]**
- composite (rung 3, `37e745ed9b0b`) for the unmodified champion condition ∈ **[−0.05, +0.15]**

Coswara is predicted to show a **larger** `D(k)` than SVD, because its labels are self-reported and
its acquisition is crowd-sourced, giving identity more room to correlate with label.

---

## 11. Abandonment conditions

V2 is abandoned — not quietly re-scoped — if any of these hold:

1. The §4.1 orthogonality gate cannot be satisfied at any k after **two** documented estimator
   revisions. The construct is then not separable in this corpus and the hypothesis is
   `UNFALSIFIABLE` **on this data**, which is itself a logged verdict.
2. The §6 manipulation check fails at every k after two documented revisions — the instrument
   cannot remove identity, so nothing downstream is interpretable.
3. The measured 2σ_seed noise band on `D(k)` exceeds **0.10 AUC**, making the predicted effect
   undetectable at n = 10. Then either n is raised (a protocol amendment logged in §14) or the
   hypothesis is `UNTESTED_ON_RIGHT_DATASET`.
4. C4 (the class-direction positive control) does not collapse AUC — the projection code is wrong
   and must be fixed and re-run from rung 0.
5. `AUC_full` cannot be brought within **0.05 AUC** of SVD's published reference under the
   published protocol. Then we have not reproduced the claim and cannot audit it:
   `NOT_REPRODUCIBLE`, logged with the reproduction gap.

---

## 12. Rung plan and gates

| rung | what runs | gate to next |
|---|---|---|
| **0 UNIT** | synthetic embeddings; `P_k` idempotence and orthonormality; speaker-overlap assertion; §4.1 gate fires on a deliberately contaminated subspace; composite returns `null` on a missing term | all tests green |
| **1 SMOKE** | SVD, 1 partition, k ∈ {16}, all six controls | `D(16)` has the predicted sign; C3 within `0.5 ± 2σ_null`; C4 collapses; manipulation check passes |
| **2 DEV** | SVD, 3 partitions, full k sweep | effect direction stable across partitions; holds on a second SVD audio-material slice |
| **3 STANDARD** | SVD, n = 10, full k sweep, full statistical contract | Holm-corrected result + ordinal gate + confound battery + `AUC_leaky`; composite defined at rung 3 |
| **4 FULL** | + Coswara replication, subgroup breakdown, calibration, independent re-run from a clean checkout | cross-corpus + calibration + subgroup + re-run agreement |

No rung *k+1* compute before rung *k*'s gate is cleared (`CLAUDE.md` §5; the sibling program
launched 11 rung-3 runs with zero passing rung-2 gates beneath them).

---

## 13. Provenance, determinism, ethics

- **R1/R2:** every number lands in `autoresearch_results/runs/V2-<rung>-<config_hash>/` containing
  the command line, resolved config, config hash, `pip freeze`, GPU/CPU/driver identifiers, seeds,
  stdout/stderr, and the raw per-partition metric JSON. A number without such a pointer is deleted,
  not debated. The agent never states a metric it did not read from one of these files.
- **R15:** library versions and hardware are recorded; a dependency change invalidates by staleness
  and requires a re-run.
- **R5/R16:** any critique of this document produced by an agent in this project is internal
  red-teaming and carries *"Internal QA pass — independent external review pending."*
- **R13:** an independent critic agent, with separate context, reviews this pre-registration
  **before** the run — not in a later audit pass.
- **Ethics (`CLAUDE.md` §7):** no audio, no embeddings derived from restricted corpora, and no
  speaker-identifiable artifact is ever committed. Only split manifests (speaker ids hashed),
  metrics, and code. Voice is a biometric. No clinical claim is made; this is not a medical device.
- **Tone policy (`audits/NOVELTY_CRITIQUE.md` §d.2):** we audit the *claim*, never the authors.

## 14. Protocol amendments

*None. Any amendment is appended here with a date, the reason, and the commit SHA of the state it
supersedes. In-place edits above this line after the freeze commit are a BLOCKER.*

---

## 15. What we will not claim

- Not that voice-health detection does not work.
- Not that any named authors made an error — only that a stated number does or does not survive a
  stated protocol change, on the corpora we could access.
- Not a clinical or diagnostic conclusion of any kind.
- Not methods novelty. The audit *loop* is not novel: Jain & Linares, 2026, *Agentic AutoResearch
  for Space Autonomy* (arXiv:2606.20394) published an auditable autoresearch loop with in-loop
  seed-noise gating. We claim **domain + verdict-ledger** novelty only (`CLAUDE.md` §0).

---

*Internal QA pass — independent external review pending. Every citation is carried over from
`corpus/` or `audits/NOVELTY_CRITIQUE.md`, mechanically verified 2026-07-25; none introduced from
memory (R10). This document contains no results — §10 is pre-registration, not measurement.*
