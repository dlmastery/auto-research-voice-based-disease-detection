# Survey: Datasets for Voice/Speech-Based Disease Detection

**Verified on 2026-07-25.** Every number and access claim below was checked against a live
URL or arXiv abstract during this session (source list at the end). Items that could not be
confirmed are marked `[UNVERIFIED]`.

## Executive summary

Voice-based disease detection in mid-2026 is dominated by a structural mismatch: the datasets
with the best labels are small and gated, while the datasets that are large and open have weak
labels and severe acquisition confounds. The NIH Bridge2AI **Voice as a Biomarker of Health**
flagship reached v3.1.0 on 2026-05-01 (833 participants, five North American sites) but its
PhysioNet tier ships *derived features and spectrograms only* — raw audio requires a separate
Synapse application. The clinically-labelled neurodegenerative corpora (PC-GITA n=100,
NeuroVoz n=112, ADReSS ~156) are an order of magnitude too small for a `>=500/class` rigor bar
and can only support screening-tier claims. Conversely COUGHVID (>25,000 recordings) and
Coswara (2,635 participants) are one `git clone` away but carry self-reported labels and the
recording-device/recruitment confounds that produced this field's most important negative
result: Coppock et al. (*Nature Machine Intelligence* 2024) saw COVID-screening AUC fall from
0.846 to 0.619 once confounders were matched. The one dataset that satisfies all three of
open + large + benchmarked is the **Saarbrücken Voice Database** (1,356 pathological / 687
healthy, free download, published UAR 85.61 with public code). For a laptop-scale (RTX 4090,
16 GB) autonomous program the recommended ladder is SVD as the primary hill-climbing target,
Coswara/COUGHVID as the respiratory + OOD pair, PROCESS-2 (2026, HF-gated, unsaturated
baselines) as the highest-headroom cognitive task, and Bridge2AI credentialing started
immediately in the background because the lead time is long.

---

## 1. Dataset table

| Dataset | Disease / task | #subjects & #recordings | Language(s) | Modality | Label quality | ACCESS & license | Host | Published SOTA | Known confounds / leakage traps |
|---|---|---|---|---|---|---|---|---|---|
| **Bridge2AI-Voice v3.1.0** (2026-05-01) | 5 cohorts: voice disorders, neuro/neurodegenerative, mood/psychiatric, respiratory, pediatric voice/speech | 833 participants (v3.1), 5 sites; VoiceFM reports 984 participants / 40,056 recordings / 176 h | English (North America) | sustained vowels, read speech, spontaneous, cough, breathing | clinician-confirmed + validated questionnaires | **credentialed user + signed DUA**, Bridge2AI Voice Registered Access License, *no training course required* | PhysioNet `b2ai-voice/3.1.0` — **derived features / spectrograms / MFCC / PPG only**; raw audio via Synapse + DACO committee (`DACO@b2ai-voice.org`) | VoiceFM contrastive baseline (medRxiv 2026.05.28) | 5-site device/site effect; feature-only tier blocks end-to-end audio models |
| **SVD (Saarbrücken Voice Database)** | 71 voice pathologies (functional + organic) vs healthy | **2,043 speakers: 687 healthy / 1,356 pathological**, >2,000 sessions, ~5 h | German | /a/ /i/ /u/ at normal/high/low pitch + rising/falling, one German sentence, + EGG signal | clinically validated | **free to use** ("free for reproducible voice science") | `stimmdb.coli.uni-saarland.de`; bulk via `github.com/rijulg/svd-downloader`; Zenodo mirror advertised, DOI `[UNVERIFIED]` | **UAR 85.61 (F) / 84.69 (M) / 85.22 (combined)** — arXiv:2410.10537 | reported accuracy swings with which pathology subset and which audio material is used (UCL Discovery 10139814); class imbalance; must split by sex |
| **PC-GITA** | Parkinson's disease | 100 speakers (50 PD / 50 HC), 25 M + 25 F per group | Spanish (Colombian) | vowels, DDK, read sentences, monologue | neurologist diagnosis + MDS-UPDRS, Hoehn & Yahr | on request from authors | — | early-PD F1 **0.73** / AUC **0.80** (RECA-PD, DDK task) — arXiv:2605.14066 | tiny n; disease-stage and sex effects; only PC-GITA and NeuroVoz carry enough metadata to isolate *early*-stage PD |
| **NeuroVoz** | Parkinson's disease | 112 speakers (54 PD / 58 HC), ON state | Spanish (Castilian) | vowels, DDK, read speech | clinician diagnosis, UPDRS | **Zenodo restricted + DUA**: paste the full DUA text into the request-message box | Zenodo (Sci Data `s41597-024-04186-z`); tooling at `github.com/BYO-UPM/Neurovoz_Dababase` | same EarlyPD benchmark as PC-GITA | ON-medication state only; tiny n |
| **PROCESS-2** (arXiv:2605.14888, 2026-05-14) | HC / MCI / dementia 3-way + MMSE regression | **400 participants (200 HC, 150 MCI, 50 dementia), 1,200 recordings, ~21 h**, 80/20 split | British English | semantic fluency, phonemic fluency, Cookie Theft description (+ manual transcripts) | NHS memory-service clinical diagnosis; MMSE for 174/400 (43.5%) | **HuggingFace gated repo + data use agreement** | HuggingFace (exact repo id `[UNVERIFIED]`) | macro-F1 **0.59** (3-way), F1 **0.85** (2-way), MMSE RMSE **3.87** (DistilBERT) | strong class imbalance (200/150/50); MMSE missing for 56.5%; transcript-quality dependence |
| **ADReSS / ADReSSo / ADReSS-M / TAUKADIAL** | Alzheimer's dementia, MCI, MMSE regression | ADReSS ~156 subjects `[UNVERIFIED n]`; **balanced for age and gender by design** | English; ADReSS-M multilingual (incl. Greek) | picture description (Cookie Theft), spontaneous speech | clinical diagnosis + MMSE | DementiaBank consortium password + T&C agreement | TalkBank / DementiaBank (`dementia.talkbank.org/ADReSS-M/`) | ADReSS F-score ~0.79 (with age+sex as inputs); ADReSSo acoustic F-score ~0.76 | balanced-by-design removes age/sex only — session, administration and transcription effects remain |
| **Coswara** | COVID-19 | **2,635 individuals** (1,819 negative, 674 positive, 142 recovered), Apr-2020 → Feb-2022 | multiple (India) | breathing ×2, cough ×2, sustained vowels ×3, continuous speech ×2 | **mostly self-reported** COVID status | **open** | `github.com/iiscleap/Coswara-Data` (Nature Sci Data `s41597-023-02266-0`) | AUC ~0.92 intra-dataset | device + demographic (age/sex) shortcuts; self-report label noise; collapses cross-dataset |
| **COUGHVID** | COVID-19 | **>25,000 crowdsourced cough recordings**; ~35 h at `cough_detected > 0.8` | global | cough only | self-report + expert-labelled subset | **open (Creative Commons via Zenodo)** | `zenodo.org/records/7024894` (Sci Data `s41597-021-00937-4`) | AUC ~0.93 intra-dataset | heavy label noise; no PCR reference; crowd-recording device variance |
| **UK ONS / Turing vocal audio (Cambridge-adjacent)** | COVID-19 | **67,842 individuals, 23,514 PCR-positive** | English (UK) | cough, breathing, speech | **PCR-referenced** (strongest labels in the respiratory family) | restricted | Nature Sci Data `s41597-024-03492-w` | AUC 0.846 unadjusted → **0.619 after matching on confounders** | *the* recruitment-bias case study (symptomatic-only recruitment) |
| **VOICED (VOice ICar fEDerico II)** | voice pathology | 208 voices (150 pathological / 58 healthy) | Italian | sustained vowel /a/ | clinical | **open** | PhysioNet `voiced/1.0.0` | — | very small; single vowel |
| **PVQD (Perceptual Voice Qualities Database)** | dysphonia severity (CAPE-V) | 296 recordings | English | sustained vowels /a/ /i/ + CAPE-V standard sentences | expert perceptual ratings (CAPE-V protocol) | **open, free for public use** | Mendeley Data `9dz247gnyb` (v4) | — | inter-rater noise; controlled studio conditions ⇒ optimistic |
| **DAIC-WOZ / E-DAIC (AVEC)** | depression, PTSD, anxiety | 189 sessions | English | Wizard-of-Oz clinical interview (audio + text + video) | PHQ-8 | USC EULA | USC ICT | — | **interviewer-prompt shortcut** (see traps §3); gender effects |
| **SAP (Speech Accessibility Project)** | dysarthria: Parkinson's, ALS, cerebral palsy, stroke, Down syndrome | **524 participants, ~415 h** (SAP-240430); 430 participants in the 2024-11-30 release | English | prompted / elicited speech | etiology-labelled, severity | UIUC data agreement (partner institutions first, then general researchers) | Univ. of Illinois Urbana-Champaign | Interspeech 2025 SAP Challenge (ASR WER) | **explicitly designed for speaker-independent ASR** — the positive example |
| **TORGO / UASpeech** | dysarthria | TORGO 15 speakers (8 dysarthric / 7 control), 21 h; UASpeech 19 speakers × 765 isolated words | English | isolated words, short phrases | severity ratings | open / registration | — | — | **not** designed speaker-independent; tiny speaker counts ⇒ identity leakage is near-guaranteed with random splits |
| **HPP-Voice** (arXiv:2505.16490, 2025) | 15 phenotypes across 6 systems: sleep apnea, insomnia, asthma, smoking, sinusitis, anemia, thyroid, migraine, headache, depression, anxiety, COVID, allergy … | **7,188 recordings from 6,760 adults** (3,211 M / 3,549 F), mean age ~52 | Hebrew | single 30-second counting task, controlled lab | linked deep clinical phenotyping (Human Phenotype Project) | qualified researchers at recognized institutions, **upon request** | Weizmann Institute project site | sleep apnea (males) AUC **0.64 ± 0.03** with x-vector embeddings vs MFCC 0.56 and demographic baseline 0.57 | strong sex-specific effects; single language; effect sizes are genuinely small — a useful realism check |
| **mPower (Parkinson)** | Parkinson's disease | large longitudinal smartphone cohort (tens of thousands of voice tasks) | English | 10-second sustained /a/ ("aaah") via iPhone app | **self-reported** PD status + surveys | Synapse account + qualified-researcher terms | Synapse `syn4993293` (`synapse.org/mpower`) | — | self-report labels; device model = iPhone only but OS/mic vary; repeated measures per participant ⇒ severe leakage risk |
| **ICBHI 2017 respiratory sound** | crackles / wheezes (acoustic events, not diagnosis) | 126 subjects / 920 recordings | — | lung/chest auscultation sounds | expert annotation | open | ICBHI challenge site | ICBHI score (event-level) | fixed recording equipment per site; event-level not nosological |
| **RRP-Voice** (arXiv:2606.01639, 2026-06) | recurrent respiratory papillomatosis | longitudinal | English | voice | clinical | see paper | — | new benchmark released with the paper | small; longitudinal repeats ⇒ subject leakage |
| **PARLO Dementia Corpus** (arXiv:2603.03471, 2026-03) | Alzheimer's disease | German multi-centre | German | spontaneous speech | clinical | see paper | — | `[UNVERIFIED]` | multi-centre site effects |
| *HeAR* (model, listed for completeness) | bioacoustic foundation model | trained on 313 M two-second clips | — | cough, breathing, throat-clearing, laughing, speaking | — | open weights, Google Health terms | HuggingFace `google/hear` | SOTA on 33 health-acoustic tasks across 6 datasets | **training corpus is not released**; using HeAR embeddings imports its (undisclosed) distribution |

---

## 2. Ranked shortlist for a laptop-scale autonomous program

Criteria: (a) genuinely open or fast-DUA, (b) large enough for `>=500` per class, (c) has a
published benchmark number to hill-climb against.

### 1. Saarbrücken Voice Database (SVD) — **the primary target**
The only dataset that satisfies all three criteria cleanly.
- **Open:** free download, no login, no DUA.
- **Size:** 1,356 pathological / 687 healthy speakers → after balancing to the healthy pool you
  still get ~687/class, comfortably over the 500/class bar; unbalanced use gives 1,356 positives.
- **Benchmark:** UAR **85.61 (female) / 84.69 (male) / 85.22 (combined)**, arXiv:2410.10537,
  with a public GitHub repo and a REFORMS reproducibility checklist — i.e. a *reproducible*
  target, not a paper-only number.
- **Compute fit:** sustained vowels are 1–3 s each; the whole corpus is a few GB. Trivially
  4090-scale, and EGG signals give a second modality for free.
- **Caveat to pre-register:** the pathology subset and the audio material both materially move
  the score. Fix both in git before the first sweep.

### 2. Coswara — **the respiratory workhorse**
- **Open:** `git clone`, no gate.
- **Size:** 2,635 participants; 674 positives is below 500/class only for the positive class at
  full split — use the 1,819 negatives subsampled, or pool positives+recovered (816).
  Report the pool cap honestly.
- **Benchmark:** AUC ~0.92 intra-dataset is the number to reproduce *and then attack* — the
  interesting research question is how much of it survives confound matching.
- **Bonus:** nine modality streams per subject (breathing ×2, cough ×2, vowels ×3, speech ×2)
  make modality-ablation experiments free.

### 3. COUGHVID — **the scale / OOD partner**
- **Open:** Zenodo, ~1 GB, no gate.
- **Size:** >25,000 recordings — the only open corpus at true scale.
- **Use:** self-supervised pretraining and out-of-distribution transfer testing for a
  Coswara-trained model. Labels are too noisy to headline. Published intra-set AUC ~0.93 exists
  but should be treated as an upper bound inflated by label noise and demographics.

### 4. PROCESS-2 — **the highest-headroom cognitive task**
- **Fast DUA:** HuggingFace gated repo; accept the agreement in the UI.
- **Size:** 400 participants / 1,200 recordings — **fails the 500/class bar**, so this is a
  screening-tier dataset under the project's rigor rules. Listed anyway because:
- **Benchmark:** macro-F1 **0.59** (3-way) and **0.85** (2-way) with MMSE RMSE **3.87**,
  published 2026-05 — essentially unsaturated. Highest expected improvement per GPU-hour of
  anything in this table.

### 5. Bridge2AI-Voice v3.1 — **start the paperwork now, hill-climb later**
- **Slow DUA:** PhysioNet credentialing takes weeks (institutional reference required).
- **Size:** 833 participants across five cohorts; the associated VoiceFM work used 984
  participants / 40,056 recordings / 176 h — enough for 500/class in the larger cohorts.
- **Catch:** the PhysioNet tier is **derived features only**. End-to-end audio work needs the
  separate Synapse/DACO application. Begin both applications immediately in parallel with
  work on datasets 1–3.

**Explicitly not shortlisted:** PC-GITA, NeuroVoz, VOICED, PVQD, ADReSS, TORGO, UASpeech —
all are clinically excellent but at n=100–300 they cannot support an evaluation-tier claim
(`n>=7` seeds + paired Wilcoxon + Holm-Bonferroni). Use them only as OOD probes.

---

## 3. Known methodological traps (with citations)

### 3.1 Speaker-dependent splits — the #1 leakage failure
Nearly every corpus here has multiple recordings per speaker (SVD has ~10 vocalisations per
session; mPower has longitudinal repeats; TORGO has hours per speaker). A random
recording-level split leaks speaker identity, and the model learns *who* rather than *what*.
The correct pattern is the fixed speaker-independent k-fold used by the 2026 EarlyPD benchmark:
5 folds, each test fold holding 6 early-PD + 6 HC speakers, with age and sex balanced *within*
each fold — Zhong, Tejedor-Garcia, Truong, Maas, ten Bosch & Bloem, Interspeech 2026,
"A Benchmark for Early-stage Parkinson's Disease Detection from Speech" (arXiv:2605.14066).
The Speech Accessibility Project is the one large corpus explicitly *designed* for
speaker-independent evaluation, unlike UA-Speech, Nemours and TORGO.

**Rule for this program:** group-aware `GroupKFold` on speaker id, always. Never
`train_test_split` on recordings. Report the speaker-level n alongside the recording-level n.

### 3.2 Recruitment / symptom confound — the field's canonical negative result
Coppock et al., *Nature Machine Intelligence* 2024, "Audio-based AI classifiers show no
evidence of improved COVID-19 screening over simple symptoms checkers"
(arXiv:2212.08570, DOI `s42256-023-00773-8`). Audio from 67,842 individuals, 23,514
PCR-positive. Unadjusted ROC-AUC **0.846**; after matching on measured confounders including
self-reported symptoms, ROC-AUC fell to **0.619**. Cause: UK Test-and-Trace recruited
predominantly symptomatic people, so "audible symptoms" became a proxy for infection status.
Any respiratory claim in this program must report a confounder-matched number alongside the
raw number, or it is not a claim.

### 3.3 Recording-device and site confounds
COVID cough corpora are the notorious case. Datasets "differ substantially in acquisition and
diagnostic validation" — Coswara relies on self-report while Virufy uses qRT-PCR under
controlled conditions. High intra-dataset performance (AUC 0.92 Coswara, 0.93 COUGHVID) was
typically obtained *without* demographic stratification of the splits, and the substantial
drop in cross-dataset evaluation is the tell. Bridge2AI spans five sites; ICBHI is "limited by
specific recording equipment". Mitigations in the literature include adversarial learning for
confounder-invariant features (PMC10813025).

**Rule:** every headline number needs a cross-corpus companion number. Log the recording
device / site as a feature and check that a device-only classifier is near chance.

### 3.4 Interviewer / prompt shortcut
Burdisso, Reyes-Ramírez, Villatoro-Tello, Sánchez-Vega, López-Monroy & Motlicek,
ClinicalNLP @ NAACL 2024, "DAIC-WOZ: On the Validity of Using the Therapist's prompts in
Automatic Depression Detection from Clinical Interviews" (arXiv:2404.14463,
`aclanthology.org/2024.clinicalnlp-1.8/`, code at `github.com/idiap/bias_in_daic-woz`).
The *interviewer's* side is consistently stronger than the participant's:
I-Longformer 0.73 vs P-Longformer 0.71; I-GCN 0.88 vs P-GCN 0.85. Ellie's prompts are
highly discriminative shortcuts. A follow-up, "When Consistency Becomes Bias: Interviewer
Effects in Semi-Structured Clinical Interviews" (arXiv:2603.24651), extends this.

**Rule:** strip all interviewer audio and text from any interview-based corpus before training.

### 3.5 Age and sex confounds
ADReSS was constructed "balanced in terms of age and gender" precisely because unbalanced
dementia corpora let models classify on demographics (Luz, Haider, de la Fuente, Fromm &
MacWhinney, Interspeech 2020, arXiv:2004.06833). The EarlyPD benchmark finds female speakers
score consistently *higher* across all models and tasks — contrary to prior reports — which is
itself evidence that sex-pooled numbers are unstable. HPP-Voice reports sleep-apnea AUC
separately for males (0.64) because the pooled number is not meaningful. The SVD reference
result is reported per sex (85.61 F / 84.69 M) for the same reason.

**Rule:** report per-sex and per-age-band metrics; include a demographics-only baseline
classifier in every experiment and claim only the margin above it.

### 3.6 Language and accent confounds
PC-GITA and NeuroVoz are both Spanish; PROCESS-2 is British English; SVD is German; HPP-Voice
is Hebrew. Cross-lingual generalisation is a separate, harder claim — ADReSS-M
(ICASSP 2023 SPGC) exists specifically to test it (PMC11218814). Do not report a
cross-lingual result as if it were an in-language one.

### 3.7 Tiny-n overfitting
PC-GITA (100), NeuroVoz (112), VOICED (208), PVQD (296 recordings), DAIC-WOZ (189),
TORGO (15), UASpeech (19). Under the project's rigor contract these are screening-tier only:
`n<=3` seeds cannot reach `p<0.05` under paired Wilcoxon, and a 12-speaker test fold has a
standard error of roughly ±0.14 on accuracy. Any "winner" language applied to these corpora is
a rigor violation.

### 3.8 "Balanced" is not "deconfounded", and ASR quality is a hidden variable
ADReSS-style age/sex balancing removes exactly two variables. It does not remove
recording-session, task-administration, or transcription-pipeline effects. The 2026
reproducible-benchmark study on ASR quality and Alzheimer's detection (arXiv:2603.18239)
shows lexical-model results move with the transcription front-end; weight-masking approaches
to confound mitigation are explored in arXiv:2506.05610.

### 3.9 Label-provenance asymmetry
Self-reported (Coswara, mPower, most of COUGHVID) vs clinician-confirmed (SVD, PC-GITA,
NeuroVoz, PROCESS-2, Bridge2AI) vs PCR-referenced (UK ONS). These are not interchangeable.
A high AUC on a self-report corpus may be measuring self-report behaviour.

### 3.10 Anonymisation degrades diagnostic signal
Voice anonymisation, increasingly required for sharing, measurably harms downstream diagnostic
classification (arXiv:2304.02181, COVID-19 case study). If a dataset ships anonymised audio,
its ceiling is lower than the literature's non-anonymised numbers.

---

## 4. Exact programmatic access paths

### Shortlist datasets

**1. SVD (Saarbrücken)**
- Browse / export: `https://stimmdb.coli.uni-saarland.de/` — free, no login, web export form.
- Bulk download utility: `github.com/rijulg/svd-downloader`.
- Contents: WAV + EGG per session; GB-scale total (~5 h audio + EGG). Exact archive size
  `[UNVERIFIED]`.
- License: "free to use for reproducible voice science" (no click-through DUA observed).
- Hosting note: currently maintained by Essen University Hospital; contacts
  `ahoy.ship@uk-essen.de` (technical), `manfred.puetzer@gmail.com` (data).
- A Zenodo mirror is advertised on the site; the DOI is `[UNVERIFIED]`.
- Reference implementation to reproduce the 85.61 UAR: repo linked from arXiv:2410.10537
  (Zenodo `10.5281/zenodo.13771573` for the code archive).

**2. Coswara**
```
git clone https://github.com/iiscleap/Coswara-Data
```
- Data is stored as split tar shards with an extraction script in-repo.
- No gate, no account.
- Paper: Nature Scientific Data `s41597-023-02266-0`.

**3. COUGHVID**
- `https://zenodo.org/records/7024894` (record also resolvable via DOI
  `10.5281/zenodo.4048312`).
- ~1 GB: webm/ogg audio + a metadata CSV with `cough_detected` confidence, self-reported
  status, age, gender, geography.
- No gate. Paper: Nature Scientific Data `s41597-021-00937-4`.

**4. PROCESS-2**
- HuggingFace **gated** repository: accept the data use agreement in the repo UI, then load
  with an HF token (`huggingface-cli login`; `load_dataset(<id>)`).
- The exact HF repo id is not stated in the arXiv abstract — resolve it from the paper's
  data-availability section: arXiv:2605.14888. Marked `[UNVERIFIED]`.
- Contents: 1,200 recordings (~21 h) + manual transcripts + MMSE where available.

**5. Bridge2AI-Voice v3.1.0**
- `https://physionet.org/content/b2ai-voice/3.1.0/`
- Steps: (i) create a PhysioNet account; (ii) apply for **credentialed** status — requires
  identity verification and a supervisor/institutional reference; (iii) sign the Bridge2AI
  Voice Registered Access DUA on the project page. **No CITI/training course is required**
  for this dataset (unlike MIMIC).
- What you get: Parquet files of dense features (spectrograms, Mel-spectrograms, MFCCs, pitch,
  articulatory features, phonetic posteriorgrams, prosodic measures) plus TSV phenotype tables
  with JSON data dictionaries. Download size not published — `[UNVERIFIED]`.
- **Raw audio is a separate application**: Synapse, via the data access committee at
  `DACO@b2ai-voice.org`, requiring institutional approval.

### Other datasets

| Dataset | Path | Gate |
|---|---|---|
| NeuroVoz | Zenodo restricted record (linked from Sci Data `s41597-024-04186-z`); copy the repository's full DUA text into the request-message box with institutional details. Tooling: `github.com/BYO-UPM/Neurovoz_Dababase` | request-based |
| PC-GITA | email the authors — no programmatic path | request-based |
| VOICED | `https://physionet.org/content/voiced/1.0.0/` — open, `wget -r -N -c -np` | none |
| PVQD | `https://data.mendeley.com/datasets/9dz247gnyb/4` — direct download | none |
| ADReSS / ADReSSo / ADReSS-M / TAUKADIAL | `https://dementia.talkbank.org/` (ADReSS-M at `/ADReSS-M/`); password-protected, restricted to DementiaBank consortium members; accept T&C | consortium membership |
| DAIC-WOZ / E-DAIC | USC ICT distribution, EULA | EULA |
| SAP | University of Illinois Urbana-Champaign data agreement (`pubs.asha.org/doi/10.1044/2024_JSLHR-24-00122` describes the infrastructure) | institutional agreement |
| mPower | `https://www.synapse.org/mpower` (Synapse `syn4993293`); Synapse account + qualified-researcher terms | registration |
| HPP-Voice | request via the Human Phenotype Project site; qualified researchers at recognized institutions | request-based |
| ICBHI 2017 | ICBHI challenge distribution | open |
| HeAR encoder (model) | `https://huggingface.co/google/hear`; code at `github.com/Google-Health/hear`; model card at `developers.google.com/health-ai-developer-foundations/hear/model-card` | Google Health terms |

---

## 5. Verified sources

- PhysioNet Bridge2AI-Voice v3.1.0 — https://physionet.org/content/b2ai-voice/3.1.0/
- arXiv:2605.14066 — EarlyPD benchmark (Interspeech 2026) — https://arxiv.org/abs/2605.14066
- arXiv:2605.14888 — PROCESS-2 corpus — https://arxiv.org/html/2605.14888v1
- arXiv:2410.10537 — Reproducible voice pathology detection / pitch-difference feature — https://arxiv.org/abs/2410.10537
- arXiv:2212.08570 / Nature Mach. Intell. `s42256-023-00773-8` — Coppock et al., COVID audio classifiers — https://www.nature.com/articles/s42256-023-00773-8
- arXiv:2404.14463 — Burdisso et al., DAIC-WOZ interviewer bias — https://arxiv.org/abs/2404.14463
- arXiv:2004.06833 — Luz et al., ADReSS Challenge — https://arxiv.org/abs/2004.06833
- arXiv:2505.16490 — HPP-Voice — https://arxiv.org/html/2505.16490v1
- arXiv:2508.14089 — FAIRness assessment of 27 open voice biomarker datasets (TSD 2025) — https://arxiv.org/abs/2508.14089
- arXiv:2606.01639 — RRP-Voice — https://arxiv.org/html/2606.01639
- Saarbrücken Voice Database — https://stimmdb.coli.uni-saarland.de/
- Coswara data — https://github.com/iiscleap/Coswara-Data ; paper https://www.nature.com/articles/s41597-023-02266-0
- COUGHVID — https://zenodo.org/records/7024894 ; paper https://www.nature.com/articles/s41597-021-00937-4
- UK ONS PCR-referenced vocal audio dataset — https://www.nature.com/articles/s41597-024-03492-w
- VOICED — https://physionet.org/content/voiced/1.0.0/
- NeuroVoz — https://www.nature.com/articles/s41597-024-04186-z
- PVQD — https://data.mendeley.com/datasets/9dz247gnyb/4
- SVD pathology-subset effects — https://discovery.ucl.ac.uk/id/eprint/10139814/
- VoiceFM (Bridge2AI foundation model) — https://www.medrxiv.org/content/10.64898/2026.05.28.26354346v1.full
- HeAR — https://huggingface.co/google/hear
- Speech Accessibility Project infrastructure — https://pubs.asha.org/doi/10.1044/2024_JSLHR-24-00122
- ADReSS-M overview — https://pmc.ncbi.nlm.nih.gov/articles/PMC11218814/
- DementiaBank — https://dementia.talkbank.org/
- mPower — https://www.synapse.org/mpower

### Flagged as unverified
- ADReSS exact participant count (~156) — the age/sex balancing is confirmed, the n is not. `[UNVERIFIED]`
- PROCESS-2 HuggingFace repository id. `[UNVERIFIED]`
- SVD Zenodo mirror DOI and total archive size. `[UNVERIFIED]`
- Bridge2AI-Voice download size. `[UNVERIFIED]`
- PARLO Dementia Corpus (arXiv:2603.03471) size and access terms — paper surfaced in search but not fetched. `[UNVERIFIED]`
- ICBHI 2017 "126 subjects / 920 recordings" — widely cited but not confirmed against a primary source this session. `[UNVERIFIED]`
