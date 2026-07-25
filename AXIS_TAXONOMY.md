# AXIS_TAXONOMY.md — what "change exactly one thing" means in a voice-health claim audit

**Instantiation step 1** (`meta-skills/autoresearch-meta/SKILL.md` §9, §11). Written
2026-07-25. This file defines the unit of a single-axis perturbation, scopes the hill-climb
cube, and tells the combo ladder which axes may be stacked. Nothing here has been executed;
this is a specification, not a result.

---

## 0. The domain inversion — read this before using the taxonomy

In the sibling steering program the champion was **a method** and an experiment asked *does
this change make the method better?* Here the champion is **a reproduction** and an experiment
asks *does this protocol change make the published claim survive?*

That inverts the sign of the whole loop, and it splits the axis space in two:

| family | role | what moving it means | what we do with it |
|---|---|---|---|
| **P-axes (protocol)** | the audit dial | changes the *conditions under which a number is legitimate* | this is the **independent variable**; moving it is the experiment |
| **N-axes (nuisance / pipeline)** | the design dial | changes *how the number is computed* | held at the audited paper's stated values; swept only to test whether a verdict is representation-specific |

**The single-axis rule applies to both families, but the KEEP/DISCARD rule does not.** A
P-axis move that *lowers* AUC is a positive finding (the claim was priced on the protocol). An
N-axis move that lowers AUC is just a worse pipeline. Confusing these two is the most likely
way this program fools itself, and it is the reason the composite (`COMPOSITE.md`) is built on
the *honest margin* rather than on raw discrimination.

**The champion.** `best_config.json` holds the current **reproduction champion**: the
configuration that most faithfully reproduces the audited paper's stated pipeline under the
paper's own protocol. It advances when a *more faithful* reproduction is found (closer to the
published number under the published protocol), not when a better classifier is found. Any
experiment is exactly one axis away from that champion, or from an explicitly-documented
baseline when a new axis is being opened (`CLAUDE.md` §R9 exploration quota).

---

## 1. The axes

Twelve axes. `P` = protocol, `N` = nuisance, `C` = control.

### A1 (P) — Corpus / corpus pairing

**Admissible values.** `SVD` · `Coswara` · `COUGHVID` · `PROCESS-2` (screening-tier only,
n<500/class) · `Bridge2AI-Voice v3.1` (pending DUA) · `VOICED`, `PVQD`, `PC-GITA`, `NeuroVoz`,
`ADReSS*` (OOD probes only — `corpus/SURVEY_datasets.md` §2 excludes them from
evaluation-tier claims). A *pairing* value is an ordered `(train_corpus → eval_corpus)` tuple;
`(X → X)` is within-corpus.

**Mechanism.** Each corpus carries its own recruitment process, acquisition chain, label
provenance and demographic composition. Changing the corpus changes the *joint* distribution
of (signal, confound, label) — which is precisely why cross-corpus AUC collapses to 0.43–0.68
on COUGHVID↔Coswara (arXiv:2511.14939) while within-corpus AUC is 0.82–0.93.

**Notes.** Label provenance is not interchangeable across values (self-report vs clinician vs
PCR; `SURVEY_datasets.md` §3.9). A `(self-report → clinician)` pairing confounds the corpus
axis with the label axis A2 and is therefore a **two-axis move** unless A2 is explicitly held
by restricting to a shared label definition.

---

### A2 (P) — Task / label definition

**Admissible values.** `binary_pathology_vs_healthy` · `k-way_diagnosis` · `severity_regression`
· `label_provenance ∈ {self_report, clinician, PCR, questionnaire}` ·
`alternate_diagnosis_control` (train on a *different* label with partial overlap) ·
`pathology_subset` (which of SVD's 71 pathologies count as positive).

**Mechanism.** The label defines what the probe is allowed to learn. Diagnostic
**non-specificity** is a measured failure mode: six DAIC-WOZ architectures retained most of
their accuracy when retrained on synthetic GAD-7 labels instead of PHQ-8, i.e. they detect
broad distress, not MDD (ICMI 2025 Companion, `doi:10.1145/3747327.3763034`). The
`alternate_diagnosis_control` value operationalises exactly that test.

**Notes.** SVD's reported accuracy "swings with which pathology subset is used" (UCL Discovery
10139814) — so `pathology_subset` must be **pinned in git before the first sweep** and treated
as a protocol axis, not a tuning knob. Silently re-choosing it is HARKing.

---

### A3 (P) — Split policy · **the primary audit axis**

**Admissible values.**
`random_recording` (the leaky reference) · `session_disjoint` · `speaker_disjoint` ·
`speaker_disjoint + sex_stratified` · `speaker_disjoint + demographically_matched` ·
`site_or_device_disjoint` · `cross_corpus` · `controlled_overlap(ρ)` where ρ ∈ [0,1] is the
fraction of test speakers also seen in training, **with training-set size held constant**.

**Mechanism.** Multiple recordings per speaker (SVD ~10 vocalisations per session; Coswara 9
streams per participant; mPower longitudinal) mean a recording-level random split lets the
probe learn *who* rather than *what*. Yeh et al. (arXiv:2604.14354) show accuracy drops
sharply on unseen speakers and that a DANN fails to close the gap, concluding identity
reliance is "a property of current speech representations rather than a model-specific
limitation." SpeechDx (arXiv:2606.17339) had to *replace* the official COVID-19 Sounds split
for leakage.

**Notes.** `controlled_overlap(ρ)` is the value that makes the leakage effect *measurable
rather than merely asserted*, because it holds training-set size fixed — this is Yeh et al.'s
control and it is the correct one. A3 owns **who is in which partition**. It does not own
post-partition adjustment; that is A9. `speaker_disjoint + demographically_matched` sits on
the boundary and is assigned to A3 by fiat: when it is selected, A9 **must** be held at
`none`, or the move is two-axis.

---

### A4 (P) — Preprocessing-fit scope

**Admissible values.** `fit_on_all` (leaky) · `fit_on_train_only` · `fit_per_fold` ·
`fit_per_speaker` (a subtler leak). Sub-knobs, each with the same three scopes: feature
scaler/normaliser, VAD/silence trimming thresholds, duration crop/pad statistics, PCA or
whitening basis, class-balancing resampler.

**Mechanism.** Any statistic estimated over the whole dataset before splitting transports test
information into training. The measured magnitude is dataset-specific and **not always
inflationary**: −0.14 to +0.14 pp on SVD but −8.3 to +7.8 pp on VOICED over 1,000 repetitions
per configuration (*Applied Soft Computing*, `S1568494626007970`). "We scaled before splitting
but it is only a small effect" is therefore not a defensible claim on an unmeasured corpus.

**Notes.** A4 is only interpretable *relative to* A3 — leakage is an A3×A4 interaction. The
program's default and the audit reference are both pinned: champion `fit_per_fold`, leaky
reference `fit_on_all`.

---

### A5 (N) — Feature representation

**Admissible values.**
*Handcrafted:* `eGeMAPS` · `ComParE-2016` (openSMILE, CPU-only).
*General SSL/ASR:* `wav2vec2-base` · `WavLM-base+` · `Whisper-small-enc` · `Whisper-medium-enc`
· `AST` · `emotion2vec+`.
*Health-pretrained:* `HeAR` (512-d) · `OPERA-CT/CE/GT`.
*Confound-only feature sets (see A12):* `duration` · `rms_intensity` · `snr` ·
`device_or_site_metadata` · `age` · `sex` · `age+sex` · `silence_segments_only`.

**Mechanism.** The representation fixes what is linearly decodable downstream. SpeechDx ranks
Whisper-enc (MRR 0.44) > Qwen3-TTS-Tokenizer (0.40) > WavLM (0.38) across 27 speaker-disjoint
tasks, and concludes "no current representation generalizes reliably across the clinical speech
landscape" (arXiv:2606.17339). Health pretraining appears to buy sample-efficiency rather than
ceiling: HeAR reaches near-full performance at ~50 labelled samples where OPERA needs ~400
(arXiv:2606.15436).

**Notes.** All values are **frozen encoders, extracted once and cached**. Fine-tuning is
off-thesis (`audits/NOVELTY_CRITIQUE.md` §d.4: "if the program finds itself fine-tuning large
audio encoders, it has drifted off-thesis"). The confound-only sets are members of this axis
so that a confound baseline is a *single-axis perturbation of the champion*, which keeps the
comparison mechanically honest.

---

### A6 (N) — Pooling / temporal aggregation

**Admissible values.** `mean` · `mean+std` · `max` · `attention` · `first/last frame` ·
`per-layer selection (layer ℓ)` · `clip-level mean over 2-s windows` (HeAR's native unit).

**Mechanism.** Pooling decides which temporal statistics survive into the probe. Duration and
intensity are known recording-protocol shortcuts (*PLOS Digital Health*
`10.1371/journal.pdig.0000516`); `mean+std` and `max` expose more of that signal than `mean`.

**Notes.** **Conditional on A5.** Undefined for `HeAR` (which emits one vector per 2-s clip) and
for the handcrafted sets (functionals are already applied). A5×A6 is therefore a partially
ragged grid, not a full cross-product — the hill-climb cube must enumerate valid pairs, not
multiply cardinalities.

---

### A7 (N) — Classifier head

**Admissible values.** `logistic_regression(C)` · `linear_SVM(C)` · `MLP-small(h, dropout)` ·
`gradient_boosting(depth, n_est)` · `kNN`. Regularisation strength is part of the value, not a
separate axis.

**Mechanism.** Head capacity sets how much of the representation's non-linear structure is
exploitable. MLP-small beat linear probing in **23 of 30** model-task combinations
(arXiv:2606.15436), so `logistic_regression` is not a neutral default — it is a capacity
choice that can itself flip a comparison.

**Notes.** A7 is the axis most likely to be *silently different* between us and an audited
paper. Reproduction fidelity requires pinning it to the paper's stated head; where the paper
does not state one, that is logged as a reproduction ambiguity and both plausible values are
run (this is a documented two-cell reproduction, not a sweep).

---

### A8 (N) — Calibration method

**Admissible values.** `none` · `Platt/sigmoid` · `temperature_scaling` · `isotonic` ·
`beta_calibration`. Each carries a fit scope, which must equal A4's scope (calibration fitted
on test data is an A4 violation, not an A8 value).

**Mechanism.** Calibration maps scores to probabilities without changing the ranking, so AUC is
invariant and ECE/Brier are not. This makes A8 **orthogonal to A5/A6/A7 in AUC** and coupled to
them in ECE — the cleanest orthogonality in the taxonomy, and the reason calibration is a free
secondary axis (arXiv:2601.07969).

**Notes.** `isotonic` overfits small validation sets; on our per-fold validation sizes it is
pre-declared as expected-unstable and reported with its own seed band rather than compared
head-to-head at n<10.

---

### A9 (P) — Confound-control method

**Admissible values.** `none` · `covariate_matching` · `stratified_reporting` ·
`residualisation (regress out age/sex/duration from features)` ·
`adversarial (DANN)` · `subspace_projection(k, source)` where
`source ∈ {speaker_LDA, speaker_verification, age, sex, device}` ·
`reweighting (IPW)`.

**Mechanism.** These operate *after* partitioning, on features or on the loss, to remove a
nuisance direction. The canonical demonstration of why it matters: Coppock et al. saw
COVID-screening ROC-AUC fall 0.846 → 0.619 once confounders were matched (*Nature Machine
Intelligence* 2024, arXiv:2212.08570). The canonical demonstration of why it is hard: DANN
does not close the speaker-identity gap (arXiv:2604.14354).

**Notes.** `subspace_projection` is the axis value that hypothesis **V2** moves; it is pure
linear algebra on cached embeddings, and its rank `k` is conditional on A5's dimensionality.
Every use of `subspace_projection` **requires** its same-rank random-projection control (A12)
in the same experiment — the control is part of the value's definition, not an optional extra
(`CLAUDE.md` §4.3.3).

---

### A10 (N) — Augmentation / channel simulation

**Admissible values.** `none` · `additive_noise(SNR)` · `speed_perturb` · `pitch_shift` ·
`codec/telephony_simulation` · `body-coupled_wearable_filterbank` · `room_IR`.

**Mechanism.** Augmentation changes the training distribution's coverage of acquisition
nuisance. BCoughBench measures the real-world size of this effect: mean AUROC 0.785
(smartphone) → 0.689–0.723 (wearable), with sex classification on CIDRZ collapsing 0.954 →
0.596–0.628 (arXiv:2606.25116).

**Notes.** The only axis whose values require **re-extracting embeddings** (cost coupling to
A5, not statistical coupling). Deprioritised to rung ≥3 for that reason.

---

### A11 (N) — Scoring / aggregation unit

**Admissible values.** `recording_level` · `session_level` · `speaker_level(mean_prob)` ·
`speaker_level(majority_vote)`.

**Mechanism.** Corpora with k recordings per speaker let a recording-level metric count the
same speaker k times, which both inflates apparent n and lets one easy speaker dominate.
`SURVEY_datasets.md` §3.1 mandates reporting the speaker-level n alongside the recording-level
n; A11 makes the choice explicit and auditable rather than implicit in the eval script.

**Notes.** Interacts with A3: under `random_recording` the aggregation unit is nearly
meaningless because the same speaker straddles the split. Report A3 and A11 as a pair, always.

---

### A12 (C) — Reference / control condition

**Admissible values.** `same-rank_random_projection` · `variance-matched_random_projection` ·
`label_shuffle` · `silence-only_input` · `confound-only baseline` (each member of the pinned
battery in `COMPOSITE.md`) · `demographics-only` · `zero-shot audio-LLM` (no training split,
therefore structurally leak-free) · `base-rate predictor`.

**Mechanism.** Controls establish what a number means. A same-rank random projection removes
the same number of dimensions but no identity information, so the *difference* between it and
`subspace_projection` isolates the identity contribution. A label shuffle must fail — a method
that still "works" on shuffled labels is measuring an artifact
(`meta-skills/autoresearch-shuffle-test`). Silence-only is the Clever-Hans probe: near-100% AD
detection from silent segments alone in the Pitt corpus (arXiv:2406.07410).

**Notes.** A12 is not optional and is not a sweep. Its values are **required companions** to
specific A9/A3 values, enumerated in each pre-registration. `variance-matched_random_projection`
is the stronger control and is mandatory alongside the plain one: LDA directions are typically
high-variance, so a naive random projection removes *less* variance and is a strawman.

---

## 2. Orthogonality matrix

`O` = orthogonal (safe to stack, single-axis attribution holds) · `C` = coupled (a move in one
changes the meaning of the other; never stack in one experiment) · `c` = conditional (the
second axis's admissible set depends on the first's value) · `$` = cost-coupled only.

|      | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 |
|------|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| **A1** corpus        | — | c | O | O | O | O | O | O | O | O | c | O |
| **A2** label         | c | — | O | O | O | O | O | O | O | O | O | c |
| **A3** split         | O | O | — | **C** | O | O | O | O | **C** | O | **C** | c |
| **A4** prep-scope    | O | O | **C** | — | c | O | O | **C** | O | O | O | O |
| **A5** representation| O | O | O | c | — | **c** | O | O | **c** | $ | O | c |
| **A6** pooling       | O | O | O | O | **c** | — | O | O | O | O | O | O |
| **A7** head          | O | O | O | O | O | O | — | **C** | O | O | O | O |
| **A8** calibration   | O | O | O | **C** | O | O | **C** | — | O | O | O | O |
| **A9** confound-ctrl | O | O | **C** | O | **c** | O | O | O | — | O | O | **C** |
| **A10** augmentation | O | O | O | O | $ | O | O | O | O | — | O | O |
| **A11** aggregation  | c | O | **C** | O | O | O | O | O | O | O | — | O |
| **A12** controls     | O | c | c | O | c | O | O | O | **C** | O | O | — |

**The five coupled pairs, and the rule that resolves each:**

1. **A3 × A4** — leakage *is* the interaction. Rule: A4 is pinned at `fit_per_fold` in every
   experiment except V6, whose entire purpose is to move A4 with A3 held at `speaker_disjoint`.
2. **A3 × A9** — demographic balancing can be done by sampling (A3) or by adjustment (A9).
   Rule: A3 owns partitioning; when A3 = `demographically_matched`, A9 is forced to `none`.
3. **A3 × A11** — aggregation unit is meaningless under a leaky split. Rule: always reported as
   a pair; A11 is pinned to `speaker_level(mean_prob)` for all headline numbers.
4. **A7 × A8** — head capacity and calibrator interact through the score distribution
   (an over-regularised head produces compressed scores that temperature scaling then
   over-corrects). Rule: calibrate *after* the head is fixed; never move both.
5. **A9 × A12** — a projection value without its matched control is meaningless. Rule: the
   control is part of the A9 value's definition; the runner refuses an A9 =
   `subspace_projection` config with no A12 companion.

**Cleanly orthogonal, and therefore the legitimate stack set:** {A1, A3, A5, A7, A8, A10} —
subject to the conditional-cardinality caveats on A5×A6 and A5×A9.

---

## 3. The two cubes

The hill-climb cube from `meta-skills/autoresearch-meta` §5 splits, because this program has
two different search problems.

**The audit cube (the science).** `A3 × A4 × A9 × A1-pairing × A2`. Coordinate descent here is
**not** hill-climbing toward a maximum — it is a systematic descent from the audited paper's
protocol toward the strictest protocol, measuring the drop at each step. The deliverable is the
*trajectory*, and every intermediate point is a ledger row.

**The nuisance cube (the robustness check).** `A5 × A6 × A7 × A8 × seed`, valid pairs only.
Swept to answer one question: **is the verdict representation-specific?** A break that appears
only under `eGeMAPS` and vanishes under `HeAR` is a weaker finding than one that holds across
the cube, and the ledger must record which.

**Seed, in this domain, is not a model seed.** The dominant variance source is *which speakers
land in which partition*, not weight initialisation. `n` therefore counts **paired repeated
speaker-disjoint partitions** (seeded partition draws), each evaluated under every condition
being compared. See the statistical caveat in §5.

---

## 4. Combo-ladder implications

- Stacking is **additive 2→N**, one new orthogonal axis per row (`meta-skills` §6). The
  "everything-on" hybrid is forbidden.
- The natural audit ladder is a *strictness* ladder on P-axes, and it is monotone by
  construction:

  | row | A3 | A4 | A9 | A11 | what it adds |
  |---|---|---|---|---|---|
  | L0 | paper's stated split | paper's stated scope | none | paper's unit | the reproduction champion |
  | L1 | `speaker_disjoint` | paper's | none | paper's | + identity disjointness |
  | L2 | `speaker_disjoint` | `fit_per_fold` | none | paper's | + preprocessing hygiene |
  | L3 | `speaker_disjoint + demographically_matched` | `fit_per_fold` | none (forced) | `speaker_level` | + demographic deconfounding |
  | L4 | L3 | `fit_per_fold` | `subspace_projection` + A12 controls | `speaker_level` | + mechanistic identity ablation |
  | L5 | `cross_corpus` | `fit_per_fold` | as L4 | `speaker_level` | + transfer |

  Each row is exactly one axis from the row above, so the marginal cost of each protocol
  correction in AUC points is directly readable. **This ladder is the program's core
  deliverable shape**: a per-claim table of "how many AUC points each rigor step costs."
- The **budget axis** (the accumulating cost term, `meta-skills` §6) here is *statistical
  power*, not norm: every strictness step shrinks the usable evaluation set (matching discards
  speakers; speaker-level aggregation shrinks n). Stack until the pre-registered minimum
  effective speaker count is hit, then stop and say so.

---

## 5. Two places where the constitution and this domain do not fit cleanly

Flagged here rather than silently resolved; both need a decision from the lead.

**(i) `n` is not i.i.d. across repeated splits.** `CLAUDE.md` R6 mandates paired Wilcoxon over
n ≥ 8 replicates. In this domain the replicates are repeated speaker-disjoint partitions drawn
from **one finite speaker pool**, so they share training data and are positively correlated.
Wilcoxon (and any test assuming independence) is therefore **anti-conservative** on them: the
nominal p is optimistic. The constitution's arithmetic (`min_attainable_p(n) = 2/2ⁿ`) is a
statement about the *test's resolution*, and remains correct; the *validity* concern is
separate and unaddressed. Proposed resolution, adopted throughout `IDEA_TABLE.md` and
`PREREGISTRATION.md` unless the lead overrules: report the Wilcoxon p **and** a
correlation-corrected interval (Nadeau–Bengio corrected resampled-t, or a speaker-level cluster
bootstrap), and let **the more conservative of the two bind the verdict**. This adds a term to
the rigor contract rather than relaxing one, per `CLAUDE.md` §9's closing rule.

**(ii) KEEP/DISCARD has no meaning on P-axes.** The Karpathy invariant ("keep iff the composite
improves") is a *maximisation* rule. On a P-axis, the composite falling is the finding. The
runner must therefore branch on axis family: on N-axes it applies KEEP/DISCARD against the
champion; on P-axes it records `HOLDS` / `ATTENUATED` / `BREAKS` against the **pre-registered
falsifier**, and the champion does not move. `CLAUDE.md` §6's champion-health monitor
("`best_config.json` must advance or the loop is broken") must be scoped to N-axis experiments
only, or it will fire spuriously on a program that is working exactly as designed.

---

*Internal QA pass — independent external review pending. All arXiv identifiers cited here are
carried over from `corpus/SURVEY_datasets.md` and `corpus/SURVEY_sota_methods.md`, which were
mechanically verified on 2026-07-25; no citation in this file was introduced from memory
(`CLAUDE.md` R10).*
