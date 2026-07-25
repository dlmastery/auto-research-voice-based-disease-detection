# SOTA Methods for Voice/Speech-Based Disease Detection

**Verified on 2026-07-25.** Every arXiv id below was fetched from `arxiv.org/abs/<id>` and
title + author-verified unless explicitly marked `[UNVERIFIED]`. Numbers taken from secondary
sources (not the primary PDF) are marked `[UNVERIFIED number]`. Nothing here is cited from
memory.

---

## Executive summary

Four facts dominate the field as of mid-2026:

1. **General-purpose speech encoders currently beat health-specific ones on average.** The
   largest honest multi-task evaluation to date — **SpeechDx** (arXiv:2606.17339, 15 Jun 2026,
   12 datasets / 27 tasks / 12 encoders, all speaker-disjoint) — ranks **Whisper encoder (MRR
   0.44) > Qwen3-TTS-Tokenizer (0.40) > WavLM (0.38)**. Domain-specific encoders win *only* on
   closely matched tasks. Its verdict is quotable: *"No current representation generalizes
   reliably across the clinical speech landscape."*
2. **Health-pretrained encoders (HeAR, OPERA) buy sample-efficiency, not a higher ceiling.**
   HeAR reaches near-full performance with ~50 labeled samples where OPERA needs ~400
   (arXiv:2606.15436).
3. **The field has a documented replication crisis.** Speaker leakage, demographic leakage,
   scaling-before-split leakage, and diagnostic non-specificity are all now quantified in
   peer-reviewed 2025-2026 work. Cross-corpus COVID-cough AUC collapses to **0.43-0.68**
   (arXiv:2511.14939). A DAIC-WOZ systematic review found **only 5 of 414 deduplicated papers
   met minimal reproducibility standards**.
4. **This makes the field unusually attackable at laptop scale.** The open questions are about
   *protocol* (splits, confounds, calibration), not about compute. A frozen-embedding + linear
   probe pipeline on a 16 GB GPU can falsify several headline claims.

---

## (a) Backbone landscape

### The reference evaluation

**SpeechDx: A Multi-Task Benchmark for Clinical Speech AI**
arXiv:**2606.17339** — Sejal Bhalla, Larry Kieu, Aina Merchant, Eyal de Lara, Alex Mariakakis
(submitted 15 Jun 2026).

- 12 datasets, 27 tasks, organized by **speech-production stage**: conceptualization
  (EDAIC-WOZ, RAVDESS, IEMOCAP), formulation (DementiaBank, AphasiaBank), articulation-
  neuromuscular (TORGO, UASpeech, MDVR-KCL, KSoF-C), articulation-phonatory/respiratory
  (COVID-19 Sounds, Coswara, AVFAD).
- 12 encoders: wav2vec 2.0, HuBERT, WavLM, MMS, Qwen3-TTS-Tokenizer, Whisper, AudioMAE,
  WavJEPA, AST, CLAP, emotion2vec+, OPERA.
- **Splits:** speaker-disjoint throughout — 70/10/20 stratified by label/sex/age on large
  datasets, speaker-disjoint 5-fold CV on small ones. **The COVID-19 Sounds official split was
  replaced because of speaker leakage.** This is the cleanest protocol currently published.
- **Overall (mean reciprocal rank):** Whisper 0.44, Qwen3-TTS-Tokenizer 0.40, WavLM 0.38.
- **Per-stage winners:** conceptualization — emotion2vec+ (0.77); neuromuscular articulation —
  AST (0.60) and Whisper (0.44); phonatory/respiratory — Qwen3 (0.54), Whisper (0.53).
- **Asymmetric transfer:** representations trained on phonatory/respiratory data transfer *into*
  conceptualization/formulation tasks at AUC 0.83 and 0.88; the reverse direction does **not
  exceed 0.60**.

### Health-specific encoders

| Model | Paper | Pretraining | Notes |
|---|---|---|---|
| **HeAR** | arXiv:**2403.02522** — Baur, Nabulsi, Weng, Garrison, Blankemeier, Fishman, Chen, Kakarmath, Maimbolwa, Sanjase, Shuma, Matias, Corrado, Patel, Shetty, Prabhakara, Muyoyeta, Ardila (4 Mar 2024) | 313M 2-s clips (~174k h) | ViT-L masked autoencoder, **512-d embeddings**, SOTA on 33 health-acoustic tasks / 6 datasets. On HF as `google/hear`. |
| **OPERA** | arXiv:**2406.16148** — Zhang, Xia, Han, Wu, Rizos, Liu, Mosuily, Chauhan, Mascolo (23 Jun 2024, rev. 7 Nov 2024; NeurIPS 2024 Datasets & Benchmarks) | ~136k clips / 400+ h | Three open respiratory foundation models + 19-task benchmark; beats general-audio models on **16/19** tasks. Code public. |
| **VoiceFM** | medRxiv 2026.05.28.26354346 (`10.64898/2026.05.28.26354346`) | Bridge2AI-Voice: 984 participants, 40,056 recordings, 176 h, 5 academic medical centers | Contrastive (symmetric InfoNCE) alignment of a fine-tuned **Whisper-large-v2** encoder with a tabular transformer over 44 clinical features. Frozen linear probes: **AUROC 0.952 ± 0.005** across five tasks vs frozen Whisper 0.926 ± 0.013 (138 held-out participants). |
| **WavRx** | arXiv:**2406.18731** — "WavRx: a Disease-Agnostic, Generalizable, and Privacy-Preserving Speech Health Diagnostic Model" | — | WavLM + modulation-dynamics module; disease-agnostic framing. |

### Independent 2026 re-benchmarks (the sobering ones)

- **Beyond Classification: A Cough Regression Benchmark for Respiratory Acoustic Foundation
  Models** — arXiv:**2606.15436**, Mayur Sanap, Prasanna Desikan, Edgar Lobaton (13 Jun 2026;
  ICML 2026 Workshop on Structured Data for Health). Benchmarks OPERA-CT/CE/GT, HeAR,
  M2D+Resp on age / BMI / disease-probability regression, **subject-disjoint**.
  - HeAR leads within-dataset age regression on Coswara: **9.12 yr MAE**.
  - **Sample efficiency:** HeAR and M2D+Resp hit near-full performance at **50 samples**;
    OPERA models need **400**.
  - Transfer is asymmetric: large diverse → small clinical works (CoughVID→CIDRZ: −0.17 yr);
    the reverse fails (CIDRZ→Coswara: +2.43 yr, +26.6%).
  - MLP-small head beat linear probing in **23 of 30** model-task combinations.
- **BCoughBench: Benchmarking Respiratory Acoustic Foundation Models Under Body-Coupled
  Wearable Sensor Conditions** — arXiv:**2606.25116**, same authors (23 Jun 2026).
  Mean AUROC **0.785 (smartphone) → 0.689-0.723 (wearable)**. Temple vibration worst
  (Δ = −0.096). Sex classification on CIDRZ collapses **0.954 → 0.596-0.628** (Δ = −0.341).
  COVID detection barely moves (Δ = −0.004). Age regression on CoughVID *improves* with a
  forehead accelerometer (MAE 9.61 → 8.97 yr).

### What to run on a 16 GB laptop GPU

**Default recommendation: frozen embeddings + small probe head.**

1. **HeAR** (`google/hear`, ViT-L encoder, 512-d output) — health-acoustic prior, best
   sample-efficiency, tiny downstream head. Inference-only fits comfortably.
2. **WavLM-base+** and **Whisper-small/medium encoder** — the SpeechDx general-purpose winners;
   frozen-feature extraction is cheap, and a mean-pooled 768/1024-d vector + MLP trains on CPU.
3. Use an **MLP-small head, not linear probing** — 2606.15436 shows it wins 23/30.
4. **PEFT if you must fine-tune:** LoRA/DoRA on wav2vec2/WavLM fits in 16 GB — see
   arXiv:**2507.14898** ("Parameter-Efficient Fine-Tuning of Foundation Models for CLP Speech
   Classification").
5. **Audio-LLMs (Qwen2-Audio-7B) at 4-bit** fit but are slow; use them as a *zero-shot
   reference*, not a training target. Host RAM, not VRAM, is usually the binding constraint.

Because probes are near-free, **the entire compute budget should go to protocol rigor** —
repeated speaker-disjoint splits, seed sweeps, confound audits — which is exactly where the
field's open questions live.

---

## (b) Benchmark SOTA table

| Task | Dataset | Metric | Best number | Model | Paper / arXiv | Speaker-independent? |
|---|---|---|---|---|---|---|
| Clinical multi-task (aggregate) | SpeechDx (12 datasets, 27 tasks) | mean MRR | **0.44** | Whisper encoder | arXiv:2606.17339 | **Yes** — speaker-disjoint; COVID-19 Sounds official split replaced for leakage |
| Conceptualization stage | EDAIC-WOZ / RAVDESS / IEMOCAP | MRR | 0.77 | emotion2vec+ | arXiv:2606.17339 | Yes |
| Neuromuscular articulation | TORGO / UASpeech / MDVR-KCL / KSoF-C | MRR | 0.60 | AST | arXiv:2606.17339 | Yes |
| Clinical voice probe | Bridge2AI-Voice | AUROC (5-task mean) | **0.952 ± 0.005** | VoiceFM (Whisper-lg-v2 + tabular contrastive) | medRxiv 2026.05.28.26354346 | Yes — 138 held-out participants |
| Respiratory foundation model | OPERA benchmark (19 tasks) | tasks won vs general-audio | **16 / 19** | OPERA-CT | arXiv:2406.16148 | Per-task official splits |
| Health acoustics (original) | 33 tasks / 6 datasets | — | SOTA claimed | HeAR | arXiv:2403.02522 | Per-task |
| Cough age regression | Coswara | MAE | **9.12 yr** | HeAR | arXiv:2606.15436 | **Yes** — subject-disjoint |
| Cough, wearable sensing | 5 datasets, 9 clf + 3 regr tasks | mean AUROC | 0.785 phone → **0.689-0.723** wearable | OPERA / HeAR / M2D+Resp | arXiv:2606.25116 | Yes |
| Voice pathology | Saarbrücken Voice Database | UAR | **85.22%** (F 85.61 / M 84.69) | pitch-difference + NaN features, classical ML | arXiv:2410.10537 (Vrba et al., rev. 14 Mar 2025) | Dedup'd, no full-set oversampling, REFORMS checklist |
| Alzheimer's detection | ADReSSo | Accuracy | 88.7% (text, RoBERTa) | RoBERTa on transcripts | secondary source — **[UNVERIFIED number]** | Challenge split (speaker-independent by design) |
| Alzheimer's, audio-only | ADReSSo | Accuracy | 74.65% acoustic / 84.51% linguistic | wav2vec 2.0 + TDNN | secondary source — **[UNVERIFIED number]** | Challenge split |
| Parkinson's, early stage | multi-corpus, public | — | benchmark only; no single SOTA claimed | multiple | arXiv:2605.14066 (Zhong, Tejedor-Garcia, Truong, Maas, ten Bosch, Bloem; Interspeech 2026) | **Yes — speaker-independent by construction**, stratified by dataset/aggregation/gender/severity |
| Parkinson's, multi-view | (single corpus) | Acc / F1 / AUC | 91.51 / 91.24 / 95.97 | ResNet-18 + BiLSTM + HuBERT, cross-modal attention | arXiv:2606.09271 — **[UNVERIFIED number]**, single-corpus, split protocol unconfirmed | Unconfirmed — treat with suspicion |
| COVID from cough | Coswara | AUC | 0.82 (within-dataset) | Audio-MAE | arXiv:2511.14939 | Yes |
| COVID from cough | COUGHVID ↔ Coswara | AUC | **0.43-0.68 (cross-dataset)**; Audio-MAE F1 0.00-0.08 | Audio-MAE, PANNs CNN6/10/14 | arXiv:2511.14939 | Yes |
| Respiratory sounds | ICBHI 2017 | ICBHI Score | CNN-TSA + Frequency Band Selection claims SOTA | CNN-TSA+FBS | arXiv:2507.20052 — **[UNVERIFIED number]** | Official 60/40 split |
| TB screening | CODA TB DREAM / cough | — | reproducible baseline + uncertainty quantification | HeAR + clinical variables | arXiv:2601.07969 (Kafentzis & Selisios; *Sensors* 2026, 26(4):1223) | Yes |
| Interpretable assessment | depression + dysarthria | — | beats openSMILE and SSL baselines | ALM concept-bottleneck | arXiv:2607.16967 (Chen & Hirschberg, 18 Jul 2026) | Not stated in abstract |
| Cognitive impairment, zero-shot | 1 English + 1 multilingual | — | "comparable to supervised" | Qwen2-Audio, prompt-only | arXiv:2506.17351 (Shahin, Ahmed, Epps) | N/A — no training split exists |

**Reading note.** The three highest single numbers in this table (0.952, 91.51%, 88.7%) are the
three least comparable: different corpora, different aggregation, and in one case an unverified
split protocol. The *most* trustworthy numbers are the low ones — SpeechDx's 0.44 MRR and the
0.43-0.68 cross-corpus COVID AUC — because they come from the strictest protocols.

---

## (c) 2025-2026 frontier ideas, ranked by laptop-testability

**Rank 1 — Frozen probing vs PEFT under matched compute.**
SpeechDx (2606.17339) establishes the frozen-probe ranking; 2606.15436 shows MLP-small > linear
in 23/30 cases. Both are directly re-runnable with a 16 GB GPU. PEFT reference:
arXiv:**2507.14898**. *Testability: very high — this is a pure embedding-extraction + sklearn
exercise.*

**Rank 2 — Interpretable concept bottlenecks driven by audio LLMs.**
arXiv:**2607.16967** — Yu-Wen Chen, Julia Hirschberg, "An Audio Language Model-Based Voice
Concept Bottleneck Framework for Interpretable Health Assessment" (18 Jul 2026). Fine-tunes an
ALM to emit discrete, human-readable voice-quality scores, then predicts *only* from those
concepts; consistently beats openSMILE-based and SSL-based baselines on depression and
dysarthria. *Testability: high — the downstream classifier is lightweight; only the ALM scoring
pass needs GPU.*

**Rank 3 — Zero/few-shot audio-LLM diagnosis.**
arXiv:**2506.17351** — Mostafa Shahin, Beena Ahmed, Julien Epps (20 Jun 2025): first zero-shot
speech-based cognitive-impairment detection, Qwen2-Audio, prompt-based instructions, performance
"comparable to supervised methods" with consistency across languages/tasks/datasets.
arXiv:**2605.24806** — Muhammad Ashad Kabir, Sirajam Munira (24 May 2026), PD across four
languages: **handcrafted acoustic features + text LLM are more reliable than raw audio for
low-resource languages (Bengali)**; raw audio gives inconsistent, dataset-dependent gains.
*Testability: medium-high — 4-bit inference fits; throughput is the constraint.*

**Rank 4 — Calibration and uncertainty quantification for clinical deployment.**
arXiv:**2601.07969** — George P. Kafentzis, Efstratios Selisios, "Tuberculosis Screening from
Cough Audio: Baseline Models, Clinical Variables, and Uncertainty Quantification" (12 Jan 2026,
rev. 13 Feb 2026; *Sensors* 26(4):1223). Explicitly motivated by the field's protocol
heterogeneity: *"existing studies vary substantially in datasets, cohort definitions, feature
representations, model families, validation protocols, and reported metrics"* — improvements
cannot be attributed to modeling. *Testability: very high — calibration metrics are free once
you have predictions.*

**Rank 5 — Fairness and subgroup robustness.**
arXiv:**2605.01597** — Yi-Cheng Lin et al., "Toward Fair Speech Technologies: A Comprehensive
Survey of Bias and Fairness in Speech AI" (2 May 2026). Note also that demographic balancing is
now a *leakage control*, not just a fairness measure (arXiv:2511.14939). *Testability: high —
requires only subgroup metadata, which several corpora ship.*

**Rank 6 — Sensor / channel robustness.**
BCoughBench (arXiv:**2606.25116**) shows body-coupled sensing costs 0.06-0.10 AUROC. Simulable
offline with filter banks. *Testability: high; but needs the wearable simulation code.*

**Rank 7 — Federated / privacy-preserving voice health.**
arXiv:**2506.11069** — "Regularized Federated Learning for Privacy-Preserving Dysarthric and
Elderly Speech Recognition." *Testability: medium — simulable single-host, but the interesting
claims are about scale.*

**Rank 8 — Synthetic / generative augmentation.**
arXiv:**2606.02212** — "C2GA: A Class-Controllable Generative Augmentation Framework for
Respiratory Sound Classification." *Testability: medium-low — requires training a generator.*

---

## (d) The replication crisis in voice-disease detection

This section is the most important part of the survey. The evidence is specific and recent.

### 1. Speaker leakage (identity, not pathology)

**arXiv:2604.14354** — Hsiang-Chen Yeh, Luqi Sun, Aurosweta Mahapatra, Shreeram Suresh Chandra,
Emily Mower Provost, Berrak Sisman, *"Who is Speaking or Who is Depressed? A Controlled Study of
Speaker Leakage in Speech-Based Depression Detection"* (15 Apr 2026). Uses a splitting strategy
that varies speaker overlap **while holding training-set size constant** — this is the right
control. Findings: speaker overlap significantly boosts performance; accuracy drops sharply on
unseen speakers; a Domain-Adversarial Neural Network **fails to close the gap**. Critically,
they conclude identity reliance is *"a property of current speech representations rather than a
model-specific limitation."* Dataset: DAIC-WOZ.

Corroborating: **arXiv:2206.11045** (COVYT) explicitly recommends against speaker-inclusive
partitions to obtain accurate generalization estimates.

### 2. Diagnostic non-specificity (the label doesn't mean what you think)

*"Most DAIC-WOZ Depression Classifiers Are Invalid, They Don't Learn Task-Specific Features:
Preliminary Findings From a Large-Scale Reproducibility Study"* — ICMI 2025 Companion,
**doi:10.1145/3747327.3763034**. Six representative architectures were trained separately on
PHQ-8 and on *synthetic GAD-7* labels. The strongest multimodal models **retained most of their
predictive accuracy on the alternate diagnosis** despite only moderate label overlap. Conclusion:
SOTA DAIC-WOZ "depression detectors" primarily capture **broad psychological distress**, not
MDD-specific features.

Compounding this: DAIC-WOZ contains only a **single self-reported scale (PHQ-8)** and no second
diagnosis, so high accuracy cannot be attributed to depression markers rather than general
distress. Interviewer-prompt artifacts additionally enable shortcut learning (see *"DAIC-WOZ: On
the Validity of Using the Therapist's Prompts in Automatic Depression Detection from Clinical
Interviews"*). Gender bias in DAIC-WOZ leads to over-reported performance, and mel-spectrogram
features are not robust to it (Bailey & Plumbley, *Gender Bias in Depression Detection Using
Audio Features*).

### 3. Reproducibility base rate

*"Common Pitfalls and Recommendations for Use of Machine Learning in Depression Severity
Estimation: DAIC-WOZ Study"* — *Applied Sciences* **16(1):422** (2026); preprint on
PsyArXiv (`osf.io/preprints/psyarxiv/enrbq_v1`). Screened **536 papers → 414 after
deduplication → only 5 met minimal reproducibility standards.** They identify **subject leakage**
as the critical flaw and report that, once leakage is removed, the model **consistently performed
worse than a simple mean predictor.**

### 4. Cross-corpus collapse and demographic leakage

**arXiv:2511.14939** — Daniel Oliveira de Brito, Letícia Gabriella de Souza, Marcelo Matheus
Gauy, Marcelo Finger, Arnaldo Candido Junior, *"Fine-tuning Pre-trained Audio Models for
COVID-19 Detection: A Technical Report"* (18 Nov 2025). Audio-MAE + PANNs CNN6/10/14 on Coswara
and COUGHVID.

- Within-dataset: Audio-MAE 0.82 AUC / 0.76 F1 on Coswara; all models 0.58-0.63 AUC on COUGHVID.
- **Cross-dataset: AUC 0.43-0.68** (i.e. some configurations are *worse than chance*), Audio-MAE
  F1 **0.00-0.08** — complete generalization failure.
- **Demographic leakage:** demographic balancing lowers apparent performance but gives a
  realistic estimate; without it, models exploit spurious demographic-to-label correlations.

### 5. Pipeline leakage (preprocessing, not splits)

*"Feature scaling induced data leakage quantification in machine learning-based voice pathology
detection"* — *Applied Soft Computing* (ScienceDirect `S1568494626007970`). Scaling fitted on the
whole dataset before splitting, 1000 repetitions per configuration: effect ranges **−0.14 to
+0.14 pp on SVD** but **−8.3 to +7.8 pp on VOICED**. Leakage can *degrade* as well as inflate,
and its magnitude is dataset-specific — so "we scaled before splitting but it's only a small
effect" is not a defensible claim.

### 6. Recording-protocol shortcuts

Recording biases in **audio duration and intensity** create dataset-specific differences between
patients and controls that models exploit; a model that learns a dataset's recording
idiosyncrasies is unusable on any new protocol (see the vocal-fold-paralysis explainability
study, *PLOS Digital Health*, `10.1371/journal.pdig.0000516`; PMC7836138).

Also: class imbalance makes **accuracy** dangerously over-optimistic on voice-pathology corpora —
which is why arXiv:2410.10537 deliberately reports **UAR and omits accuracy**.

### 7. Field-level hygiene

- **arXiv:2503.04802** — Birger Moell, Fredrik Sand Aronsson, Per Östberg, Jonas Beskow, *"The
  order in speech disorder: a scoping review of state of the art machine learning methods for
  clinical speech classification"* (3 Mar 2025). 564 articles screened, 91 included; reports
  efficacy varying by condition and substantial "variability across studies."
- **arXiv:2508.14089** — *"Systematic FAIRness Assessment of Open Voice Biomarker Datasets for
  Mental Health and Neurodegenerative Diseases."*
- **arXiv:2406.04116** — *"Promoting the Responsible Development of Speech Datasets for Mental
  Health and Neurological Disorders Research."*
- **arXiv:2601.07969** — protocol heterogeneity makes TB-cough progress unmeasurable.
- **arXiv:2606.17339** — SpeechDx had to *replace* an official challenge split because of
  speaker leakage. When a benchmark's own split is leaky, every number published on it is suspect.

### Bottom line

The modal published voice-disease result is produced under at least one of: speaker-overlapping
splits, unbalanced demographics, single-corpus evaluation, preprocessing leakage, an
under-specified label, or an accuracy metric on an imbalanced set. **The honest numbers are much
lower than the headline numbers**, and the gap between them is itself a measurable quantity.

---

## (e) Five research gaps attackable at laptop scale

Each is stated with the reason it is open and an explicit falsifier. All five run on frozen
embeddings + small heads on a 16 GB GPU.

### Gap 1 — Is "SSL beats handcrafted features" an artifact of leaky splits?

**Why open.** eGeMAPS/openSMILE baselines are routinely reported as clearly inferior to SSL
embeddings, but almost always under protocols with speaker overlap and/or demographic imbalance.
SpeechDx (2606.17339) shows encoder ranking is fragile; ParkMAE reports eGeMAPS being beaten
"significantly" but under its own protocol. Nobody has run the comparison under
*simultaneously* speaker-disjoint **and** demographically balanced conditions with seed statistics.

**Falsifier.** Under strict speaker-disjoint + demographic-balanced splits with n ≥ 7 seeds, if
eGeMAPS lands **within 2σ_seed** of frozen HeAR/WavLM/Whisper embeddings on ≥ 2 of 3 corpora,
the "SSL wins" claim is falsified for that task family.

**Cost.** openSMILE is CPU-only; embeddings extract once and cache.

---

### Gap 2 — Speaker-identity subspace ablation: how much of the signal *is* identity?

**Why open.** arXiv:2604.14354 establishes that depression features are entangled with speaker
identity and that adversarial training does not disentangle them — but it treats this as a
*measurement* problem. Nobody has done the direct mechanistic test: estimate the speaker-identity
subspace in the frozen embedding space (e.g. from a speaker-verification objective or LDA over
speaker labels), project it out, and re-measure disease AUC. This is a directly transferable idea
from activation-steering methodology.

**Falsifier.** If projecting out a k-dimensional speaker subspace (k swept 1→64) collapses
disease AUC toward chance **while a same-rank random projection does not**, then the reported
performance is priced on identity rather than pathology — falsifying the clinical-validity claim
for that model/dataset pair. Conversely, if AUC survives identity ablation, the finding is
strengthened, and *that* becomes a publishable positive control the field currently lacks.

**Cost.** Pure linear algebra on cached embeddings. Essentially free.

---

### Gap 3 — Where does health-specific pretraining actually cross general-purpose pretraining?

**Why open.** Two results are in apparent tension: SpeechDx says general encoders win on average;
2606.15436 says HeAR hits near-full performance at 50 samples where OPERA needs 400. Both can be
true if health pretraining buys **sample-efficiency, not ceiling** — but the crossover curve has
never been plotted head-to-head.

**Falsifier.** Sweep labeled-set size n ∈ {25, 50, 100, 200, 400, 800, all} for HeAR vs
Whisper-enc vs WavLM on ≥ 3 tasks, subject-disjoint, ≥ 7 seeds. **If HeAR never crosses Whisper
at any n**, the "health pretraining is the right prior" claim is falsified and reduces to a
low-data convenience argument. If HeAR wins at low n and loses at high n, the crossover point is
the deliverable.

**Cost.** One embedding-extraction pass per encoder, then trivial probe training.

---

### Gap 4 — Does calibration degrade with distribution shift, or independently of it?

**Why open.** arXiv:2601.07969 introduces uncertainty quantification for TB cough, and 2511.14939
documents AUC collapse cross-corpus — but **nobody reports cross-corpus ECE / Brier
decomposition**. Clinical deployment needs to know whether a model *knows* it is out of domain.
If calibration error rose in lockstep with AUC collapse, confidence would be a usable shift
detector; if not, deployed models will be confidently wrong.

**Falsifier.** Measure ECE, Brier score, and reliability curves within- and cross-corpus on
COUGHVID↔Coswara and on two SpeechDx conditions that appear in ≥ 2 datasets. **If ECE stays flat
(within its own seed noise band) while AUC falls from ~0.80 to ~0.55**, then confidence is
falsified as a shift detector — a negative result with direct deployment consequences. Report
temperature-scaled and raw variants separately.

**Cost.** Free once predictions exist; reuses Gap 1/3 runs.

---

### Gap 5 — Zero-shot audio-LLMs as a leakage-free reference point

**Why open.** This is the most interesting structural idea available. A zero-shot model **has no
training split, therefore cannot leak speaker identity, demographics, or preprocessing
statistics.** arXiv:2506.17351 already reports Qwen2-Audio zero-shot ≈ supervised on cognitive
impairment — but frames it as a convenience result, not as a *measurement instrument*. If the
supervised-vs-zero-shot gap is large under leaky protocols and small under honest ones, then
**that gap is a direct, per-dataset estimate of how much leakage a protocol admits.**

**Falsifier.** For each dataset, compute Δ_leaky = (supervised AUC under speaker-overlapping
split) − (zero-shot AUC) and Δ_honest = (supervised AUC under speaker-disjoint, demographically
balanced split) − (zero-shot AUC). **If Δ_leaky ≈ Δ_honest** (overlapping bootstrap CIs), the
proposed leakage-estimator is falsified — the gap is tracking supervised capacity, not leakage.
**If Δ_leaky ≫ Δ_honest** consistently across ≥ 3 datasets, the field gains a cheap, model-free
leakage audit that requires no re-splitting of the original paper's data.

Cross-check with arXiv:2605.24806's finding that handcrafted features + a text LLM beat raw-audio
LLM input for low-resource languages — the zero-shot reference must be reported in both input
formats or it will be language-confounded.

**Cost.** The only real GPU cost in the five. 4-bit Qwen2-Audio-7B inference; budget one
foreground eval window per dataset and cap N per condition, labelling results screening-tier.

---

## Verification ledger

**Fetched and title + author-verified on 2026-07-25:**
2403.02522 · 2406.16148 · 2506.17351 · 2601.07969 · 2604.14354 · 2605.14066 · 2605.24806 ·
2606.15436 · 2606.17339 · 2606.25116 · 2607.16967 · 2410.10537 · 2503.04802 · 2511.14939

**Verified via search result metadata only (title confirmed, full author list not fetched):**
2406.18731 (WavRx) · 2406.04116 · 2508.14089 · 2507.14898 · 2507.20052 · 2606.02212 ·
2606.09271 · 2605.01597 · 2506.11069 · 2206.11045

**Marked `[UNVERIFIED number]` — claim appears only in a secondary source:**
ADReSSo 88.7% (RoBERTa, text) · ADReSSo 74.65% / 84.51% (wav2vec2 / TDNN) · ICBHI CNN-TSA+FBS
SOTA claim · arXiv:2606.09271 PD 91.51% accuracy (split protocol unconfirmed).

**Non-arXiv sources cited:**
medRxiv `10.64898/2026.05.28.26354346` (VoiceFM) · ICMI 2025 Companion
`doi:10.1145/3747327.3763034` · *Applied Sciences* 16(1):422 (2026) · *Applied Soft Computing*
`S1568494626007970` · *Sensors* 26(4):1223 (2026) · *PLOS Digital Health*
`10.1371/journal.pdig.0000516` · Bridge2AI-Voice on PhysioNet (v1.0 Feb 2025 → v3.1.0).

**Data-access caveat.** Bridge2AI-Voice releases on PhysioNet ship derived features; **raw audio
requires institutional sign-off**. Plan any Bridge2AI-dependent experiment around that gate.
