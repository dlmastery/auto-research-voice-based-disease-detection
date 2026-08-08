# Voice-Health AutoResearch — a claim-audit ledger

> **An autonomous, pre-registered audit harness for voice-based disease detection.**
> A Karpathy-style experiment loop where Claude Code is the researcher: it diagnoses,
> cites the literature, pre-registers a falsifier, predicts a number, runs one
> experiment at a time, analyses, checkpoints. It re-tests *published* voice-health
> classification claims for speaker leakage, acquisition confounds and cross-corpus
> collapse — and publishes a transparent ledger of which claims survive.
> **7 findings from 4 of 7 registered hypotheses; 3 hypotheses are still unrun debt.**

[![Dashboard](https://img.shields.io/badge/dashboard-live-success)](https://dlmastery.github.io/auto-research-voice-based-disease-detection/)
[![Findings](https://img.shields.io/badge/findings-7-blue)](FINDINGS.md)
[![Hypotheses](https://img.shields.io/badge/hypotheses-4%2F7%20with%20results-orange)](IDEA_TABLE.md)
[![Headline](https://img.shields.io/badge/SVD%20audio%20vs%20age%20bar-NOT%20CLEARED-red)](#headline--the-four-numbers-every-time)
[![Composite](https://img.shields.io/badge/composite-37e745ed9b0b%20(unimplemented)-lightgrey)](#the-composite--declared-fingerprinted-and-not-yet-implemented)
[![Not a medical device](https://img.shields.io/badge/not%20a-medical%20device-critical)](#ethics)

Eighth instantiation of a portable autoresearch process ([`meta-skills/`](meta-skills), 29 skills)
previously run on FX, equities, tabular, medical imaging,
[DSBench](https://github.com/dlmastery/autoresearch_dsbench),
[DARE-bench](https://github.com/dlmastery/autoresearch_darebench) and activation steering.
Runs on a single RTX 4090 laptop (16 GB). Every number below is CPU-measured and judge-free.

---

## Live links

- **Master dashboard:** [dlmastery.github.io/auto-research-voice-based-disease-detection](https://dlmastery.github.io/auto-research-voice-based-disease-detection/) — the primary deliverable: benchmark scoreboard, corpus census, the four-number contract rendered from artifacts
- **Per-hypothesis pages (V1–V7):** [`/hypotheses/`](https://dlmastery.github.io/auto-research-voice-based-disease-detection/hypotheses/) — renders each hypothesis's pre-registered **prediction and falsifier whether or not a result exists**, so an untested hypothesis is visible debt
- **The dataset landscape:** [`/datasets.html`](https://dlmastery.github.io/auto-research-voice-based-disease-detection/datasets.html) — 25 corpora across 7 disease families, each scored on *could a result on this dataset mean anything?*
- **Findings ledger:** [`FINDINGS.md`](FINDINGS.md) — all 7 findings in full, positive and negative, with limits sections
- **Hypothesis registry:** [`IDEA_TABLE.md`](IDEA_TABLE.md) — V1–V7 with falsifier, predicted Δ, tier, and the R6 power arithmetic per row
- **Pre-registration:** [`PREREGISTRATION.md`](PREREGISTRATION.md) — V2 fixed in git before the run: metrics, splits, six controls, abandonment conditions
- **Experiment ledger:** [`EXPERIMENT_LEDGER.md`](EXPERIMENT_LEDGER.md) — promotion/demotion log, one row per executed run, with rung and cost
- **Audits:** [`audits/`](audits) — data-split, implementation, scientific, novelty, and prior-repo archaeology (6 documents, every one carrying the R16 circularity banner)

---

## Read this first — what this program does and does not claim

**This program is not trying to build a better voice-disease detector.** Google HeAR,
NIH Bridge2AI-Voice and a dozen funded companies own that, and a laptop adds nothing
([`audits/NOVELTY_CRITIQUE.md`](audits/NOVELTY_CRITIQUE.md)). It is an **audit engine**: the
product is the ledger of which published claims survive re-testing.

| | scope | what it is worth |
|---|---|---|
| **F1 · F2** | metadata-only and 49-speaker pilot | **SCREENING** — reproducible in seconds, and formally underpowered; may never be called a result |
| **F3 · F4 · F7** | full 1,679-speaker SVD, speaker-disjoint, n = 8–10 paired partitions | **EVALUATION / CERTIFIED** — the R6 power contract is machine-checked and passes |
| **F5 · F6** | 3 of 6 and 4 of 6 pre-registered cells | **PARTIAL** — the falsifier formally requires all cells; both are reported open |

**What this program actually demonstrates:**

1. On SVD, a model that hears nothing — **patient age alone** — reaches rec-AUC **0.8737**,
   beating a frozen WavLM probe at **0.7438** by **+0.130**. The audio model does not clear
   the demographic bar (F3).
2. About **24–39 %** of what WavLM discrimination remains is **speaker identity**, shown
   mechanistically by subspace projection against a stricter-than-random control, with a
   passing shuffle control (F4).
3. Once age is matched away to a **0.77-year** gap, **88 handcrafted eGeMAPS features beat a
   1536-dim self-supervised model** (0.6496 vs 0.6227, CI [−0.032, −0.022], 10/10 seeds) (F7).
4. Two published shortcuts **do not generalise** to these corpora: scaler-before-split leakage
   is worth 0.00004 AUC on SVD embeddings (F5), and the Clever-Hans silence shortcut never
   exceeds 0.527 on any of the three corpora (F6).

**What this program does NOT demonstrate:**

- **It does not show any published result is wrong.** UAR and ROC-AUC are different metrics;
  the comparison against UAR 85.22 is indicative, not like-for-like. Recomputing a published
  pipeline under matched splits is F1-a — **still unrun**.
- **It does not show voice carries no pathology signal.** F7 measures AUC ≈ 0.65 after the
  confounds are removed: real, well above chance, far below the ~0.85 the literature reports
  on this corpus, and nowhere near clinical usefulness.
- **It is not a cross-corpus result.** Every evaluation-tier number is SVD-only. Coswara's
  classifier sits at chance (0.4906); COUGHVID may never carry an evaluation claim at all.
- **It has no composite score.** [`COMPOSITE.md`](COMPOSITE.md) defines one and fingerprints
  it; it has **never been computed on a real row** — see below.
- **It has no independent external review.** Implementer, critic and auditor share a model
  family (R16): *Internal QA pass — independent external review pending.*

> **Not a medical device.** Nothing here is a clinical claim, a diagnosis, or fit for any
> care decision.

---

## Headline — the four numbers, every time

The goal, stated as a contract: *beat the published number on every corpus **and** clear the
demographic-confound bar on the identical folds, under speaker-disjoint splits — reporting all
four numbers every time.* A win that does not clear the confound bar is logged **NOT CLEARED**,
not announced.

| condition | published SOTA | ours | confound baseline | margin above confound | verdict |
|:---|---:|---:|---:|---:|:--|
| **SVD full, recording level** · n=8×5, 28,509 rec / 1,679 spk | UAR **85.22** (arXiv:2410.10537) — *different metric, indicative only* | WavLM+logreg **0.7438** [0.7287, 0.7578] · UAR 0.6409 | age+sex+dur+RMS **0.8747** [0.8572, 0.8920] · UAR 0.8127 | **−0.1310** [−0.1471, −0.1149], Wilcoxon p = 0.0078 | **NOT CLEARED** |
| **SVD full, speaker level** · n=8×5 | UAR **85.22** — *indicative only* | ens_rank3 **0.8650** | age+sex+dur+RMS **0.8649** | **+0.0001** [−0.0170, +0.0182], p(>0) = 0.503 | **NOT CLEARED** (tied) |
| **SVD age-matched subset** · n=10×5, ~613 spk/seed | *no published number on an age-matched subset* — `not yet measured` | eGeMAPS **0.6496** | residual age-only **0.5534** | **+0.0962** | **CLEARED** |
| **SVD age-matched subset** · n=10×5 | *as above* — `not yet measured` | WavLM **0.6227** | residual age-only **0.5534** | **+0.0693** [+0.0598, +0.0789] | **CLEARED**, but loses to eGeMAPS |
| **SVD pilot** · n=3×5, 667 rec / **49 spk** | UAR **85.22** — *indicative only* | ens_rank3 **0.6190** rec / 0.7448 spk | age-only **0.7146** rec / 0.7207 spk | **−0.0956** rec (no CI recorded) | **NOT CLEARED · UNDERPOWERED (R6)** |
| **Coswara** · WavLM, 610 rec / 72 spk | AUC ≈ 0.92 | **0.4906** (chance) | `not yet measured` | `not yet measured` | **NOT RUN as a benchmark** |
| **COUGHVID** | — | — | — | — | **BARRED** — 0 speaker ids, may never carry an evaluation claim |

Sources: rows 1–2 and 5 `autoresearch_results/bench_svd_wavlm_mean_std.json`
(`config_hash 815673703168e601`, `git_sha 5cab307`) and `FINDINGS.md` F2/F3; rows 3–4
`V1_ssl_vs_handcrafted.json` + `FINDINGS.md` F7; row 6 `V6_preprocessing_leakage.json`.
All intervals are 2,000-resample bootstrap unless stated.

**The pilot row's artifact no longer exists as cited.** `FINDINGS.md` F2 names
`config_hash d8ab0b7584b7fdb7` at the same path that now holds
`815673703168e601` — the full-corpus run **overwrote** the pilot artifact. F2's numbers
survive only in prose, which is why that row is the only one in this table without a CI.
Recorded here rather than quietly dropped.

---

## Findings ledger

| id | claim | tier | n | artifact | verdict |
|:--|:--|:--|:--|:--|:--|
| **F1** | On SVD, patient **age alone** reaches ROC-AUC **0.8709** without hearing any audio | `SCREENING` | 1 fit × 5-fold, no repeats | [`F1_demographic_baseline.json`](autoresearch_results/F1_demographic_baseline.json) | established; **no CI** |
| **F2** | WavLM does not clear the demographic bar on SVD (49-speaker pilot) | `SCREENING` · **UNDERPOWERED** | 3 × 5-fold, m=5 → `feasible=false` | superseded (see above) | **NOT CLEARED**; harness refused to certify |
| **F3** | At full scale (1,679 speakers) WavLM **still** does not clear the age bar, and the gap **widened** | `CERTIFIED` (EVALUATION) | 8 × 5-fold, m=2, min p 0.0078 < Holm 0.025 | [`bench_svd_wavlm_mean_std.json`](autoresearch_results/bench_svd_wavlm_mean_std.json) | **NOT CLEARED** |
| **F4** | ~a third of WavLM's discrimination is **speaker identity**, not pathology | `EVALUATION` | 10 × 5-fold, m=14, min p 0.00195 < Holm 0.00357 | [`V2_speaker_subspace.json`](autoresearch_results/V2_speaker_subspace.json) + [`_SHUFFLE`](autoresearch_results/V2_speaker_subspace_SHUFFLE.json) | claim SUPPORTED; **falsifier did NOT fire** |
| **F5** | Scaler-before-split leakage is **nothing** on SVD embeddings (+0.00004 AUC) | `PARTIAL` — 3 of 6 cells | 10 × 5-fold, m=6 | [`V6_preprocessing_leakage.json`](autoresearch_results/V6_preprocessing_leakage.json) | reproduced; corpus-specificity claim **not evaluable** |
| **F6** | The Clever-Hans **silence shortcut does not generalise** — ≤ 0.527 on all three corpora | `PARTIAL` — 4 of 6 cells | 10 × 5-fold, m=6 | [`V7_silence_shortcut.json`](autoresearch_results/V7_silence_shortcut.json) | shortcut is Pitt-specific here; **my mechanism was wrong** |
| **F7** | With age matched away, **88 handcrafted features beat a 1536-dim SSL model** | `EVALUATION` for the cell that ran | 10 × 5-fold, m=9 | [`V1_ssl_vs_handcrafted.json`](autoresearch_results/V1_ssl_vs_handcrafted.json) | claim SUPPORTED; V1 **not formally closed** (falsifier wants ≥2 corpora) |

### The result, in four steps

Each step removes something the model was getting for free, and asks what survives.

| step | finding | tier | what it establishes |
|---|---|---|---|
| 1 | **F1/F3** — **age alone** 0.8737 rec-AUC vs WavLM 0.7438 · n=8×5 | `CERTIFIED` | the audio model loses to one demographic variable |
| 2 | **F4** — projecting out the speaker subspace costs WavLM **more** AUC than removing *more* variance any other way · n=10×5 | `EVALUATION` | **24–39 %** of its discrimination is *who is speaking* |
| 3 | **F7a** — with age matched to a **0.77-year** gap, age-only collapses **0.8737 → 0.5534** · n=10×5 | `EVALUATION` | the confound is genuinely removed, not assumed away |
| 4 | **F7b** — on that matched subset **eGeMAPS 0.6496 > WavLM 0.6227**, CI [−0.032, −0.022], **10/10 seeds** · n=10×5 | `EVALUATION` | **88 handcrafted features beat 1,536 learned ones** |

What is left when demographics and identity are stripped out is **AUC ≈ 0.65** — real, well
above chance, far below the ~0.85 the literature reports on this corpus, and nowhere near
clinical usefulness. Whatever WavLM's extra 1,448 dimensions were buying at 0.7438, it was
substantially age and identity rather than pathology. This converges with SpeechDx
([arXiv:2606.17339](https://arxiv.org/abs/2606.17339)) — *"no current representation
generalises reliably across clinical speech"* — from a different direction, and more
specifically: here the confounds are **measured** rather than assumed.

---

## Table of contents

[Background](#background--start-here) ·
[Corpora](#corpora) ·
[The findings in detail](#the-findings-in-detail) ·
[Hypothesis registry — including the debt](#hypothesis-registry--including-the-debt) ·
[The rules that make this trustworthy](#the-rules-that-make-this-trustworthy) ·
[The gates, and the bugs they caught](#the-gates-and-the-bugs-they-caught) ·
[The composite](#the-composite--declared-fingerprinted-and-not-yet-implemented) ·
[Layout](#layout) ·
[Quickstart & reproduction](#quickstart--reproduction) ·
[Hardware contract](#hardware-contract) ·
[Cost accounting](#cost-accounting-r14) ·
[Limitations](#limitations--threats-to-validity) ·
[Open axes](#open-axes-for-the-next-campaign) ·
[Citations](#citations) ·
[Novelty](#novelty--stated-plainly) ·
[Ethics](#ethics) ·
[Provenance](#provenance--credits)

---

## Background — start here

### What is "voice-based disease detection"?

A person speaks; a model listens and predicts a health condition. It is attractive because the
sensor is a microphone everyone already owns — no blood draw, no scanner, no clinic visit. Two
mechanisms make it plausible rather than magical:

1. **The larynx is the instrument.** Anything that changes the vocal folds — a paralysis, a
   polyp, swelling, a tumour, scar tissue from surgery — changes the sound directly and audibly.
   This is where the evidence is strongest, and it is what the corpus below actually contains.
2. **Speech is a motor act.** Producing fluent speech needs breath control, timing, and fine
   neuromuscular coordination, so neurological and respiratory disease can leave traces in
   speech even when the larynx is healthy. This is the claim behind Parkinson's, Alzheimer's,
   and COVID screening from voice. It is a much longer causal chain and correspondingly weaker
   evidence.

The literature also claims depression, diabetes, heart failure, and more. **This program tests
none of those**, for the reason in the next section.

### What the data actually supports

The primary corpus is the **Saarbrücken Voice Database (SVD)** — a clinical archive from
Saarland University Hospital. Each participant records **13 short vocalisations**: the sustained
vowels `/a/`, `/i/`, `/u/` at normal, high, low, and rising-falling pitch (12 clips), plus one
spoken German sentence (*"Guten Morgen, wie geht es Ihnen?"*).

| | decoded corpus |
|---|---|
| Recordings | **28,509** (18,944 pathological / 9,565 healthy) |
| **Speakers** | **1,679** (1,009 pathological / 670 healthy) |
| Distinct named pathologies | **71** |
| Mean age (speaker level) | healthy **27.3** · pathological **49.4** |
| Speakers with mixed labels across sessions | 21 |

*Source: `data/interim/svd/manifest.csv` (28,509 rows, committed) and
`autoresearch_results/bench_svd_wavlm_mean_std.json → dataset`. The full corpus census —
2,225 sessions / 1,853 speakers before decoding — is in
`autoresearch_results/acquisition/svd_inventory_analysis.json`.*

Seventy-one diagnoses sounds like seventy-one detectable diseases. It is not. Counting **speakers
per pathology label** (a speaker carrying two labels counts in both, so the speaker column
exceeds 1,009):

| condition has ≥ N speakers | number of conditions | speaker-labels covered |
|---|---|---|
| ≥ 100 | **2** | 281 |
| ≥ 50 | 7 | 636 |
| **≥ 30** (this program's data floor) | **12** | 837 |
| ≥ 5 | 30 | 1,054 |
| ≥ 1 | 71 | 1,130 |

**20 of the 71 conditions are represented by a single speaker.** So the honest answer to
*"how many diseases can this detect?"* is:

- **1 task is properly powered** — binary *healthy vs. pathological* (1,009 vs. 670 speakers).
  This is what every headline number in this repository refers to.
- **At most 12 named conditions** clear a ≥30-speaker floor, and would need one-vs-rest
  treatment with wide confidence intervals. The largest are *Rekurrensparese*
  (recurrent-laryngeal-nerve palsy, 146), *Hyperfunktionelle Dysphonie* (135),
  *Laryngitis* (83), *Dysphonie* (75).
- **59 conditions cannot be modelled at all** at any defensible sample size.

And note what those twelve *are*: they are almost all **dysphonias and structural larynx
disorders** — the category where sound changes because the sound-producing organ changed. The
corpus contains essentially no systemic disease. A model trained here detects **disordered
voice**, not disease in general, and it is a category error to describe it otherwise.

### The rest of the field

SVD is one corpus of many.
**[The dataset landscape](https://dlmastery.github.io/auto-research-voice-based-disease-detection/datasets.html)**
catalogues every dataset the field uses to claim a disease can be heard in a voice — **25 corpora
across 7 disease families**, 8 of them released or audited in **2026** — each scored on the
question the published surveys do not ask: *could a result on this dataset mean anything?*

| family | mechanism | notable corpora |
|---|---|---|
| **Voice & larynx pathology** | the sound-producing organ itself changed — shortest causal chain, strongest evidence | SVD, **Bridge2AI-Voice v3.1** (2026), **RRP-Voice** (2026), VOICED, PVQD |
| **Parkinson's & motor-neurological** | hypokinetic dysarthria appears early | PC-GITA, NeuroVoz, mPower, MDVR-KCL |
| **Dementia, MCI & cognition** | language production degrades before motor speech | **PROCESS-2** (2026), ADReSS/ADReSSo/TAUKADIAL, **PARLO** (2026) |
| **Dysarthria & motor speech** | direct motor impairment of articulation | **SAP** (524 participants, 415 h), TORGO, UASpeech |
| **Respiratory & infectious** | airway obstruction changes cough/breath acoustics | Coswara, COUGHVID, **UK ONS** (67,842 PCR-referenced), ICBHI |
| **Mental health** | prosody and pause structure shift with mood — weakest chain | DAIC-WOZ/E-DAIC, CMDC/ANDROIDS/MODMA, **Voice Biomarkers D&A** (2026) |
| **Multi-phenotype** | what one voice sample carries across many conditions | **SpeechDx** (2026), HPP-Voice, **RespiraMFM** (2026), Voice EHR |

Scored by what a result on each would be worth: **1 EVALUATION** · 9 SCREENING · 10 BLOCKED ·
**5 that may NEVER carry a generalisation claim** (COUGHVID has no speaker ids; TORGO/UASpeech
have 15–19 speakers; the depression interview corpora classify the interviewer).

**Three findings from that landscape are the empirical case for this whole program:**

- **UK ONS / Turing** (67,842 individuals, *PCR-referenced* — the best labels in the field):
  AUC **0.846 unadjusted → 0.619 after matching on recruitment confounders**
  ([arXiv:2212.08570](https://arxiv.org/abs/2212.08570)). The largest, cleanest respiratory
  study ever run lost a quarter of its AUC to confounds.
- **HPP-Voice** is the only large study in the table that reports a demographic baseline beside
  its headline — and once it does, its best effect is **AUC 0.64 ± 0.03 against a 0.57 bar**
  ([arXiv:2505.16490](https://arxiv.org/abs/2505.16490)). That is what an honest voice-phenotype
  effect size looks like.
- **SpeechDx** ([arXiv:2606.17339](https://arxiv.org/abs/2606.17339), 27 tasks over 12 datasets,
  Jun 2026) concludes that **no current representation generalises reliably across clinical
  speech** — converging with this repository's F3 from an entirely different direction.

And the closest published work to this program's *method*:
**[arXiv:2605.23977](https://arxiv.org/abs/2605.23977)** (Ishikawa & Duke, May 2026) audits five
depression benchmarks over 96 model configurations and finds development-phase CV rankings and
official test rankings share **minimal overlap in top performers**.

### Why this program exists

Published SVD results report UAR in the mid-80s. But healthy volunteers in this corpus average
27 years old and patients average 49, so **patient age alone reaches ROC-AUC 0.871 without
hearing a single audio sample** (F1). Any classifier that quietly learns "older ⇒ patient"
inherits that score for free.

That makes the interesting quantity not the accuracy but the **margin above the demographic
baseline on the identical folds** — a number the field does not currently report. Measuring it
is the entire purpose of this repository, and the first time we did (F3) the margin came out
**negative**.

---

## Corpora

| corpus | access | speakers (census) | decoded here | speaker-disjoint possible? | published target |
|---|---|---:|---:|:--|---|
| **Saarbrücken (SVD)** | open, CC-BY-4.0, [Zenodo 38.1 GB](https://zenodo.org/records/16874898) | 1,853 | **1,679** | **yes** (`SprecherID`) | UAR **85.22** ([arXiv:2410.10537](https://arxiv.org/abs/2410.10537)) |
| **Coswara** | open, `git clone` | 2,746 (1 row per id) | 72 | **partly** — `rU` flags self-declared returning users who are not linkable | AUC ≈ 0.92 |
| **COUGHVID** | open, Zenodo | 34,434 uuids, **0 real speaker ids** | 13,535 | **NO — blocker** | (OOD / pretraining only) |
| PROCESS-2 | fast DUA | 400 | 0 | yes | macro-F1 0.59 |
| Bridge2AI-Voice | slow DUA (PhysioNet) | 833 | 0 | yes | `not yet measured` |

COUGHVID is demoted permanently: a "speaker-disjoint" split over recording UUIDs is not
speaker-disjoint, because one person may contribute many recordings. Its own acquisition
artifact records the verdict machine-readably — *"NO participant identifier exists… speaker-
disjoint splitting is IMPOSSIBLE"* (`acquisition/coughvid_meta_stats.json`). It **may never
carry an evaluation claim**.

---

## The findings in detail

### F3 — the audio model loses to a single demographic variable · `CERTIFIED`

Speaker-disjoint `GroupKFold`, **8 repeats × 5 folds**, all 28,509 recordings / 1,679 speakers.
Power contract machine-checked in the artifact: `n_paired=8, m=2, min_attainable_p=0.0078 <
Holm 0.025 → feasible=true`.

| predictor | recording-AUC [95 % CI] | recording-UAR | speaker-AUC | ECE |
|:---|---:|---:|---:|---:|
| WavLM + logistic regression | 0.7438 [0.7287, 0.7578] | 0.6409 | 0.8671 [0.8498, 0.8830] | 0.049 |
| WavLM + rank-3 ensemble | 0.7443 [0.7293, 0.7583] | 0.6759 | 0.8650 | 0.164 |
| **age alone** (no audio) | **0.8737** [0.8561, 0.8909] | **0.8078** | 0.8642 | 0.064 |
| **age + sex + duration + RMS** | **0.8747** [0.8572, 0.8920] | 0.8127 | 0.8649 | 0.074 |
| *sex alone* (negative control) | *0.4898* [0.4546, 0.5239] | *0.5000* | *0.5027* | *0.000* |
| *duration alone* (negative control) | *0.4724* [0.4412, 0.5041] | *0.5000* | *0.5021* | *0.002* |
| *intensity (RMS) alone* (negative control) | *0.5121* [0.4968, 0.5274] | *0.5000* | *0.5206* | *0.003* |

The negative controls sitting at chance are what isolate the effect: it is **age**, not some
generic metadata leak. This is a *powered* negative rather than a small-sample curiosity — a
self-supervised speech model, given 28,509 clinical recordings, is beaten at the recording level
by asking the patient's age. **The gap widened with more data** (+0.096 at 49 speakers →
+0.130 at 1,679), which is the opposite of what a noise explanation predicts.

The observation that matters most: the published SVD benchmark is **UAR 85.22**, and **age+sex
alone reaches UAR 0.8118** — a model that hears nothing lands within a few points of the
published headline, while our WavLM heads reach 0.64–0.68.

### F4 — a third of the remaining discrimination is speaker identity · `EVALUATION`

Estimate the identity subspace from between-speaker scatter (training speakers only, inside each
fold), project it out, re-measure disease AUC — against controls that remove **at least as much
variance** a different way. n = 10 × 5-fold, m = 14 pre-registered.

| k | AUC, speaker subspace removed | AUC, top-k PCA removed | **D vs top-k [95 % CI]** | variance removed spk / topk | identity as % of headroom |
|---:|---:|---:|---:|:--:|---:|
| 1 | 0.6755 | 0.7320 | **+0.0565** [+0.0555, +0.0576] | 0.206 / 0.345 | 23.7 % |
| 4 | 0.6446 | 0.7189 | **+0.0743** [+0.072, +0.078] | 0.451 / 0.718 | 31.2 % |
| **8** | **0.6104** | 0.7025 | **+0.0921** [+0.0898, +0.0943] | 0.700 / 0.812 | **38.7 %** |
| 32 | 0.5661 | 0.6529 | **+0.0869** [+0.085, +0.088] | 0.893 / 0.926 | 36.5 % |
| 64 | 0.5398 | 0.6287 | **+0.0888** [+0.086, +0.091] | 0.940 / 0.959 | 37.3 % |
| *shuffled labels, k=8* | *0.5069 (full)* | — | *+0.0017* | — | *53× smaller* |

Full-embedding AUC **0.7382**; D is positive with a CI excluding zero at **all 7 ranks against
both controls**. The cleanest form: at *every* rank the speaker subspace removes **less**
variance yet costs **more** AUC. Deleting more signal a different way hurts less — the damage is
direction-specific, not a variance effect.

**The falsifier did NOT fire, and that is reported as prominently as the result.** It required
D's CI excluding zero **and** `AUC_spk` collapsing to include 0.5. Only the first holds: at k=64
the projected AUC is 0.5398 — near chance, not chance. So the strong conclusion the falsifier
would have licensed (*"the clinical-validity claim is falsified"*) **does not follow**. Two
pre-registered predictions also missed and are recorded rather than dropped: the control was
predicted to drop < 0.05 and dropped 0.069; and the manipulation check is **weak** — predicted
speaker-ID accuracy 0.90 → < 0.30, measured **0.278 → 0.193**, i.e. it cleared the bar only
because it started there. Mean-pooled WavLM-base+ is not an x-vector.

### F7 — with age matched away, handcrafted beats SSL · `EVALUATION` for the cell that ran

Greedy sex-exact age-±3y matching yields **308 pairs (mean 613 speakers/seed)**; `audits/DATA_SPLIT_AUDIT.md`
had **failed** this design at 49 speakers, where only 9 matched pairs existed. It became runnable
purely because the corpus grew 34×.

| | unmatched (F3) | **matched (F7)** |
|---|---:|---:|
| age gap, healthy vs pathological | **22.2 years** | **0.77 years** |
| age-only ROC-AUC | **0.8737** | **0.5534** |

| predictor, on the matched subset | ROC-AUC | margin above the residual age bar |
|:---|---:|---:|
| age only (the residual bar) | 0.5534 | — |
| WavLM-base+ (1536-dim SSL) | 0.6227 | +0.0693 [+0.0598, +0.0789] |
| **eGeMAPS (88 handcrafted features)** | **0.6496** | **+0.0962** |

`WavLM − eGeMAPS = −0.0269`, 95 % CI **[−0.0317, −0.0215]** — excluding zero — and eGeMAPS wins
in **10 of 10 seeds**. Both encoders clear the residual age bar in all 10 seeds: the first
evidence in this program that the audio itself carries pathology-relevant signal rather than
demographics. **But the SSL model is the weaker of the two.** My prediction (eGeMAPS lands
*within noise*) was directionally right and **quantitatively understated**.

### F5 — scaler-before-split leakage is nothing on SVD embeddings · `PARTIAL` (3 of 6 cells)

| cell | fit_on_all | fit_per_fold | **D [95 % CI]** | within ±0.01 |
|:---|---:|---:|---:|:--:|
| SVD / WavLM (28,509 rec) | 0.7382 | 0.7382 | **+0.00004** [+0.00001, +0.00007] | yes |
| SVD / eGeMAPS (667 rec) | 0.5315 | 0.5357 | **−0.00418** [−0.00627, −0.00221] | yes |
| Coswara / WavLM (610 rec) | 0.4929 | 0.4906 | **+0.00236** [+0.00044, +0.00483] | yes |
| Coswara / eGeMAPS · COUGHVID ×2 | — | — | `not yet measured` | — |

The published near-null on SVD reproduces and **extends from handcrafted features to
embeddings**. The eGeMAPS cell is *negative* with a CI excluding zero — leakage made performance
slightly **worse**, matching the audited paper's subtler point. **My prediction MISSED on the
half that mattered** (> 0.03 on Coswara or COUGHVID; measured +0.0024).
**The limitation that caps the Coswara cell:** its classifier sits at **AUC 0.4906, i.e.
chance**, and there is nothing to inflate in a model with no signal. Read it as a null
*observation*, not a null *result*.

### F6 — the Clever-Hans silence shortcut does not generalise · `PARTIAL` (4 of 6 cells)

| corpus | features | AUC [95 % CI] | directionless | ≥ 0.60 |
|:---|:---|---:|---:|:--:|
| SVD (28,509 rec) | silence_only | 0.5136 [0.5104, 0.5174] | 0.5136 | **no** |
| SVD | duration+intensity | 0.5048 [0.5020, 0.5077] | 0.5048 | **no** |
| Coswara (610 rec) | silence_only | 0.4854 [0.4668, 0.5037] | 0.5146 | **no** |
| COUGHVID (13,535 rec) | silence_only | 0.5264 [0.5251, 0.5277] | 0.5264 | **no** |
| Coswara · COUGHVID | duration+intensity | `not yet measured` | — | — |

The silence arm — the one the Pitt paper is actually about — ran on **all three corpora** and
never exceeded 0.527. **My predicted mechanism is WRONG, and that is the informative part:** I
predicted 0.55–0.70 on Coswara because it is crowd-recorded and heterogeneous; it came in
**lowest**. The caveat that limits the null: these are corpora of sustained vowels, coughs and
breathing — **short, prompted vocalisations** — while Pitt is spontaneous picture-description
speech where pause structure plausibly carries cognitive load directly. This is **not** evidence
the Pitt effect was spurious. The artifact self-reports `falsifier_fully_evaluable: false`.

### F1 — the demographic baseline that started the program · `SCREENING`

Using **only** the demographics shipped with the corpus — no audio, no features, no model of speech:

| predictor | ROC-AUC |
|:---|---:|
| **age alone** | **0.8709** |
| sex alone | 0.5172 |
| age + sex, logistic, **speaker-disjoint** 5-fold `GroupKFold` | **0.8768** |

n = 2,225 sessions / 1,853 speakers (1,356 pathological / 869 healthy). No CI, no repeats —
hence `SCREENING`. **Cause, a recruitment asymmetry:** healthy speakers average **28.3** years,
pathological **51.0**. **Second finding from the same 167 KB file:** 200 of 1,853 speakers
contribute more than one session (max 24); a default `train_test_split` leaks all of them.

**What this does NOT claim:** it does not show any published result is wrong. UAR and ROC-AUC
are different metrics and the comparison is indicative, not like-for-like. Some pipelines may
already age-match. The audit question is whether the margin above the demographic bar is
*reported at all* — recomputing a published pipeline under age-matched, speaker-disjoint splits
is the next experiment, not this one.

```bash
python scripts/audit_demographic_baseline.py --dataset svd   # CPU, seconds
```

---

## Hypothesis registry — including the debt

Four of seven hypotheses have results; **three have never been run and are shown here as debt**,
with the prediction that was registered before any data was seen. Full falsifiers, audited
claims and the R6 arithmetic per row are in [`IDEA_TABLE.md`](IDEA_TABLE.md); each row also has
a [generated page](https://dlmastery.github.io/auto-research-voice-based-disease-detection/hypotheses/).

| id | axis | what it tests | tier | m / n | status |
|:--|:--|:--|:--|:--|:--|
| **V1** | A5 | SSL vs handcrafted under speaker-disjoint **and** age-matched splits | `EVALUATION` | 9 / 10 | **CLAIM SUPPORTED on SVD** → F7; not formally closed (falsifier wants ≥ 2 corpora) |
| **V2** | A9 | how much "disease" signal is the speaker-identity subspace | `EVALUATION` | 14 / 10 | **CLAIM SUPPORTED, falsifier did NOT fire** → F4 |
| **V3** | A5 | where health-specific pretraining crosses general-purpose pretraining | `EVALUATION` | 42 / 12 | **UNTESTED.** Predicted: HeAR leads by 0.04–0.10 AUC at n_train ≤ 50; crossover at 200–800; Whisper-enc leads by 0.01–0.04 at full data |
| **V4** | A8 | does calibration degrade *with* shift, or independently of it | `EVALUATION` | 6 / 10 | **UNTESTED.** Predicted: AUC falls 0.18–0.30 cross-corpus while raw ECE rises only 0.00–0.04 — i.e. confidence is useless as a shift detector |
| **V5** | A12 | zero-shot audio-LLMs as a leakage-free reference point | `SCREENING` (promotion pre-declared) | 3 / ≤3 → 10 | **UNTESTED.** Predicted: `Δ_leaky − Δ_honest` ∈ [0.08, 0.25] AUC, positive, on SVD and Coswara |
| **V6** | A4 | is preprocessing-fit leakage corpus-specific | `EVALUATION` | 6 / 10 | **PARTIAL** — SVD near-null reproduced on embeddings; falsifier not evaluable → F5 |
| **V7** | A5 | does the Clever-Hans silence shortcut generalise beyond Pitt | `EVALUATION` | 6 / 10 | **PARTIAL** — shortcut does not generalise; my mechanism was wrong → F6 |

Execution order (pre-registered): V2 → V6 → V7 → V1 → V3 → V4 (free once V1/V3 predictions
exist) → V5 (GPU-gated, last). **V3, V4 and V5 are the outstanding debt**, and V5 is the only
row in the registry with a real GPU cost.

---

## The rules that make this trustworthy

Written against the July-2026 state of the art in autonomous research *and* a forensic
post-mortem of a sibling program that produced **124 experiments and zero external-ready
findings**. Every rule in [`CLAUDE.md`](CLAUDE.md) is paid for. The load-bearing ones:

- **R1 — no orphan numbers.** Every number carries a pointer to the artifact that produced it.
- **R3/R4 — validate the instrument before trusting it.** The sibling program ran 124
  experiments on a judge scoring AUC 0.68 against its own ≥ 0.85 bar; every result *and every
  null* was uninterpretable. **Consequence here: every number in this README is judge-free** —
  ROC-AUC against clinical labels, never an LLM verdict.
- **R6 — power must be arithmetically possible.** `n ≥ 7 + Holm` is *unsatisfiable* for families
  of m ≥ 4 (min p = 2/2ⁿ vs 0.05/m). Feasibility is computed per family and **stored in the
  artifact**; the first pre-registration here needed **n = 10**, not 8.
- **R7 — falsifiers must be executed**, not merely declared. F4's falsifier ran and **did not
  fire**; the README says so where the result is stated, not in a footnote.
- **R8 — negative results are first-class**, in the same tables, with the same detail. Five of
  seven findings are negative or partial.
- **R11b — every hill-climb targets an external published number.** Across seven prior programs
  this was the single strongest predictor of success: repos anchored to a public benchmark
  produced real results; repos climbing a self-defined composite produced rising curves and
  zero information.
- **R11c — ship the runner before the 300th scaffold.** A sibling built 324 task scaffolds and
  ran zero experiments.
- **R11d — retraction machinery.** [`autoresearch_results/_quarantined/`](autoresearch_results/_quarantined)
  exists so results can be *withdrawn*. It currently holds **zero retractions** — machinery
  installed, not yet needed.
- **R14 — cost accounting per confirmed finding**, published. See [below](#cost-accounting-r14).
- **R16 — same-family circularity disclosure.** Implementer, critic and auditor share a model
  family, so every internal verdict reads *"Internal QA pass — independent external review
  pending."*

### The gates, and the bugs they caught

A gate with no caught-bug anecdote is decoration. These four fired on real defects:

| gate | where | what it caught |
|:--|:--|:--|
| **R6 power check** | `power_check_R6` in every bench artifact | **F2 refused certification**: `n_paired=3, m=5, min_attainable_p=0.25 vs Holm α=0.01 → feasible=false`. The pilot was labelled UNDERPOWERED instead of headlined at spk-AUC 0.74. |
| **Embedding-cache label digest** | `src/voicehealth/embed.py:_label_hashes` | `audits/IMPL_CRITIC.md` finding 1, severity **INVALIDATES-RESULTS**: the cache key omitted `label`/`speaker_id`/`age`/`sex`, so a **relabelled manifest got a cache hit and the old labels**. Fixed — labels are now part of the cache identity, with the defect recorded in the function's own docstring. |
| **Arm-executed check** | `run_v1_ssl_vs_handcrafted.py` | The first V1 artifact claimed eGeMAPS had run: `encoders_run` was populated from *the cache file existing* rather than from *the arm producing a number*. A silently-skipped arm was reported as executed. Fixed in both script and artifact (F7). |
| **Dashboard fail-loud** | `scripts/build_dashboard.py` (see [`docs/README.md`](docs/README.md)) | If a source artifact is missing the generator exits `FATAL:` rather than emitting a blank or invented cell, and the age-distribution figure is cross-checked against the F1 JSON so a plot can never disagree with the finding it illustrates. Anything unmeasured renders as the literal words *not yet measured*. |

**There is no bypass flag** on the power check: it is computed from the config's own `m` and `n`
at launch and written into the artifact, so a reviewer can recheck it without rerunning anything.

**Gates this repo declares but has NOT implemented**, stated rather than implied:

- **No rung-0 UNIT layer.** `tests/` is empty (`audits/IMPL_CRITIC.md` BLOCKER 2), so
  `CLAUDE.md` §5's "never spend rung k+1 compute before rung k's gate is cleared" is currently
  unenforced from below.
- **No `experiment_log.jsonl`, no `best_config.json`, no `JUDGE_CARD.md`.** All three are named
  as state files by `CLAUDE.md` §6 and none exists; the dashboard reports
  `experiment_log.jsonl rows: 0` honestly. [`EXPERIMENT_LEDGER.md`](EXPERIMENT_LEDGER.md) was
  back-filled from the artifacts on 2026-08-08 and says so on line 1.
- **No reasoning-blob word-floor gate.** The 7-step ritual with its word floors is defined in
  [`meta-skills/`](meta-skills) and is not wired to a runner here.

---

## The composite — declared, fingerprinted, and not yet implemented

[`COMPOSITE.md`](COMPOSITE.md) pins `VOICE_AUDIT_COMPOSITE v1.0.0`, SHA-256
`37e745ed9b0bb4bd8803b16a2cdb3448611bdbebdebdbcb4dccf1d1f2db7da9a` (short `37e745ed9b0b`).
Its primary term is deliberately **not** raw discrimination — a composite whose top row is the
most efficient confound-exploiter is worse than no composite:

```
M         = AUC_honest - max(0.5, AUC_conf_max)

composite = M
          - lambda_disc * max(0, AUC_floor       - AUC_honest)    # discrimination floor
          - lambda_cal  * max(0, ECE             - ECE_ref)       # calibration tax
          - lambda_sub  * max(0, AUC_honest - AUC_subgroup_min - delta_sub)
          - lambda_xc   * max(0, AUC_honest      - AUC_crosscorpus)
          - lambda_leak * max(0, AUC_leaky       - AUC_honest)    # protocol inflation
          - lambda_ctrl * max(0, AUC_negctrl - 0.5 - 2*sigma_null)
```

`M` prices the honest margin above the strongest confound; each penalty is one-sided, so no term
can be traded against another. `lambda_ctrl = 3.00` is near-fatal by design: a row that fails its
negative control must be un-winnable, not merely penalised.

**It has never been computed on a real row.** `audits/SCI_CRITIC.md` §4(e) verified that
`src/voiceaudit/composite.py` — the module `COMPOSITE.md` §6 specifies, with the import-time
fingerprint assertion that would halt the runner on a mismatch — **does not exist**, so the
fingerprint is asserted at no import time and no artifact carries a `composite` field.
`lambda_sub` is additionally **structurally inert on SVD**. Per **R11b** the composite was only
ever an internal ranking device; every finding above is expressed as a delta against an external
published number instead. It is documented here as an unimplemented specification, not as a
reported metric.

---

## Layout

```
CLAUDE.md                  the constitution -- read before any work
README.md                  this file
FINDINGS.md                rigor-gated findings, positive and negative (F1-F7)
IDEA_TABLE.md              hypotheses V1-V7 + falsifiers + predicted delta + required n
EXPERIMENT_LEDGER.md       promotion/demotion log, one row per executed run
PREREGISTRATION.md         V2, fixed in git before the run
COMPOSITE.md               the Goodhart-resistant internal ranking metric (unimplemented)
AXIS_TAXONOMY.md           A1-A12: what "change exactly one thing" means here
ACQUISITION_STATUS.md      corpus acquisition state
SETUP.md                   environment + dependency notes

autoresearch_results/      THE LEDGER -- every number in this README lives here
  F1_demographic_baseline.json      F1
  bench_svd_wavlm_mean_std.json     F3 (voicehealth.bench/1 schema; git_sha + config_hash)
  bench_svd_egemaps.json            the 49-speaker eGeMAPS pilot
  V1_ssl_vs_handcrafted.json        F7      V2_speaker_subspace.json        F4
  V2_speaker_subspace_SHUFFLE.json  F4 negative control (+ .partial checkpoint)
  V6_preprocessing_leakage.json     F5      V7_silence_shortcut.json        F6
  acquisition/                      corpus census + split-key verdicts (4 files)
  _quarantined/                     retraction machinery (R11d) -- 0 retractions so far
  (absent: experiment_log.jsonl, best_config.json, JUDGE_CARD.md -- see the gates section)

docs/                      THE PUBLISHED SITE (GitHub Pages serves this directory)
  index.html               master dashboard      datasets.html   the 25-corpus landscape
  hypotheses/              V1-V7 pages + index   assets/         2 generated PNGs
  README.md                documents the generator contract and the fail-loud rule
scripts/build_dashboard.py · build_datasets_page.py · build_hypothesis_pages.py
                           the three generators; no hand-written HTML exists

src/voicehealth/           embed.py · features.py · benchmark.py
scripts/                   fetch_* · preprocess_audio.py · run_benchmark.py · run_v{1,2,6,7}_*.py
                           audit_demographic_baseline.py · extract_egemaps_resumable.py
data/                      cards, manifests, ACQUISITION/PREPROCESSING status (audio gitignored)
cache/                     embedding caches (gitignored; regenerable from manifest + backbone)
audits/                    data-split · impl-critic · sci-critic · novelty · prior-repo archaeology
corpus/                    citation-verified surveys (datasets, SOTA methods, autoresearch SOTA)
skills/                    6 domain skills      meta-skills/   29 portable autoresearch skills

tests/ configs/ memory/ ideas/ hypotheses/ backlog/ dashboard/
                           EMPTY -- scaffolded and never filled (R11c alarm; see the gates section)
```

---

## Quickstart & reproduction

Tested on Python 3.12.3, PyTorch 2.6.0+cu124, transformers 4.55.0, Windows 11, single
RTX 4090 Laptop (16 GB) — the host string is recorded in every bench artifact under `host`.
There is no packaging file; install the pinned dependencies directly per
[`SETUP.md`](SETUP.md).

```bash
# 1. install -- CUDA build; do NOT let pip pick the CPU wheel. Full list in SETUP.md.
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# 2. metadata only (167 KB, no DUA) -- enough to reproduce F1
python scripts/fetch_svd.py --metadata-only

# 3. the demographic baseline: F1, CPU, seconds
python scripts/audit_demographic_baseline.py --dataset svd

# 4. full corpus (38.1 GB) + decode. See data/ACQUISITION_STATUS.md before starting.
python scripts/fetch_svd_resumable.py
python scripts/preprocess_audio.py --corpus svd

# 5. the benchmark that produced F3. The R6 power check runs at launch and
#    REFUSES to certify an underpowered plan -- there is no bypass flag.
python scripts/run_benchmark.py --corpus svd --backbone wavlm --head logreg --folds 5 --repeats 8

# 6. the pre-registered hypotheses, in their registered execution order
python scripts/run_v2_speaker_subspace.py            # F4  (~4h15m CPU)
V2_SHUFFLE=1 python scripts/run_v2_speaker_subspace.py   # F4 negative control (~46m)
python scripts/run_v6_preprocessing_leakage.py       # F5  (~41m)
python scripts/run_v7_silence_shortcut.py            # F6  (~78s)
python scripts/run_v1_ssl_vs_handcrafted.py          # F7  (~8m)

# 7. rebuild the published site from the artifacts (fails loudly on a missing source)
python scripts/build_dashboard.py
python scripts/build_datasets_page.py
python scripts/build_hypothesis_pages.py
```

**Reproducing the headline (F3).** The command in step 5 is the literal string stored in the
artifact's `command` field. Expected output:

- `recording_level.logreg.roc_auc` = **0.7438** [0.7287, 0.7578], `per_repeat_auc_std` 0.0017
- `recording_level["confound::age_sex_duration_rms"].roc_auc` = **0.8747**
- `margins_vs_confound.per_head.logreg.recording_level_delta_auc.delta` = **−0.1310**
- `verdicts` = `{"logreg": "NOT CLEARED", "ens_rank3": "NOT CLEARED"}`
- `power_check_R6.feasible` = `true` (`n_paired=8, family_size=2`)
- wall-clock **1,282 s**; artifact written to `autoresearch_results/bench_svd_wavlm_mean_std.json`

The run reproduces the **8-repeat** headline, not a single partition: `n` counts paired repeated
speaker-disjoint partitions, because the dominant variance in a frozen-embedding + probe pipeline
is *which speakers land where*, not initialisation.

**Resuming the agent.** A fresh session reads, in this order: [`CLAUDE.md`](CLAUDE.md) →
[`audits/NOVELTY_CRITIQUE.md`](audits/NOVELTY_CRITIQUE.md) (what may and may not be claimed) →
[`corpus/SURVEY_datasets.md`](corpus/SURVEY_datasets.md) + [`SURVEY_sota_methods.md`](corpus/SURVEY_sota_methods.md) →
[`IDEA_TABLE.md`](IDEA_TABLE.md) + [`EXPERIMENT_LEDGER.md`](EXPERIMENT_LEDGER.md) +
[`FINDINGS.md`](FINDINGS.md) → the newest artifact in `autoresearch_results/` → then the next
row of the pre-registered execution order.

## Hardware contract

- **Single RTX 4090 Laptop, 16 GB VRAM.** Only one GPU job at a time; check
  `nvidia-smi --query-compute-apps` before launching.
- **Host RAM, not VRAM, is the binding constraint** for the embedding-extraction passes.
- **Everything reported above is CPU.** V2 alone is 4h15m of CPU linear algebra on a
  28,509 × 1,536 matrix — "free in concept" was wrong, and the artifact records the wall-clock.
- **Long jobs must be resumable.** Background jobs get reaped on this host; two non-resumable
  extractors were killed at 74 % and 8.5 % and discarded everything, which is why
  `extract_egemaps_resumable.py` and `fetch_svd_resumable.py` checkpoint.
- **Determinism envelope (R15):** `seed`, `n_folds`, `n_repeats`, `config_hash`, `git_sha`,
  `embedding_content_hash`, `host.platform` and `host.python` are written into every bench
  artifact. **Dataset access, not compute, is the binding constraint on this program.**

---

## Cost accounting (R14)

Wall-clock is read from each artifact's own `elapsed_s`. A program that spends hours for zero
findings should be able to see that.

| finding | run | wall-clock | h |
|:--|:--|---:|---:|
| F4 | `V2_speaker_subspace` | 15,304 s | 4.25 |
| F4 (control) | `V2_speaker_subspace_SHUFFLE` | 2,767 s | 0.77 |
| F5 | `V6_preprocessing_leakage` | 2,487 s | 0.69 |
| F3 | `bench_svd_wavlm_mean_std` (8×5) | 1,282 s | 0.36 |
| F5 (input) | `bench_svd_egemaps` (49-spk pilot) | 3,461 s | 0.96 |
| F7 | `V1_ssl_vs_handcrafted` | 500 s | 0.14 |
| F6 | `V7_silence_shortcut` | 78 s | 0.02 |
| F1 | `audit_demographic_baseline` | not recorded (seconds, CPU) | — |
| F2 | superseded artifact | not recoverable | — |
| **Total recorded** | 7 runs | **25,880 s** | **7.19** |

**Not included, because no artifact times them:** corpus download (38.1 GB), audio decode of
28,509 files, and the WavLM/eGeMAPS extraction passes. Token cost per finding is
`not yet measured` — R14 asks for it and this program does not yet record it.

---

## Limitations & threats to validity

- **One corpus.** Every evaluation-tier number is SVD. The registry names Coswara and COUGHVID
  in five of seven falsifiers, so V1, V2, V6 and V7 are all formally **open**, not closed. A
  cross-corpus result is the single largest missing piece.
- **One backbone, one pooling, one layer.** WavLM-base-plus, mean+std. HeAR, Whisper-encoder and
  wav2vec2 were registered and never extracted on this host. A better representation may yet
  clear the age bar — F3 does not rule that out.
- **`n` counts partitions of one finite speaker pool, and they are positively correlated**, so
  Wilcoxon over them is anti-conservative. `IDEA_TABLE.md` requires a speaker-level cluster
  bootstrap alongside, with the more conservative binding the verdict.
- **n = 8 is the floor, not the ceiling.** R6 sets it from the arithmetic (`2/2ⁿ ≤ 0.05/m`), not
  from a power analysis of the effect sizes actually seen here; a family of m = 14 already
  forces n = 10, and no row's n was chosen by pre-specifying a minimum detectable effect.
- **Five known implementation biases remain open** (`audits/IMPL_CRITIC.md` findings 2–6, 8–10):
  two NaN policies in adjacent lines; age mean-imputation computed across train and test *inside
  the confound baseline*; the confound battery getting one bare `LogisticRegression` while the
  audio side gets four heads plus an ensemble; `ens_rank3` ECE computed on rank fractions;
  equal-width rather than the specified equal-mass ECE bins; Holm never actually applied in code.
  **Two of these bias toward over-crediting the audio model**, which makes the `NOT CLEARED`
  verdict *more* trustworthy, not less — but they are open defects and the next re-run should
  close them.
- **The manipulation check for F4 is weak.** Speaker-ID accuracy moved 0.278 → 0.193 against a
  predicted 0.90 → < 0.30, so *"the subspace removed is the identity subspace"* is supported only
  weakly. A stronger identity probe is the obvious next step.
- **F1's 0.871 is measured on a different population than the pilot it was originally quoted
  against** (`audits/SCI_CRITIC.md` §1: 1,853 speakers vs 49, where age-only is 0.741). F3
  resolves this by measuring the fitted bar at full scale (0.8737 on 1,679 speakers), but the
  older comparison is why F1 stays `SCREENING`.
- **No independent external review.** Every audit in this repo was produced by the same model
  family as the implementation (R16).

---

## Open axes for the next campaign

1. **V3 — the health-pretraining crossover** (`m=42, n=12`, registered). Requires extracting
   HeAR and Whisper-encoder, neither of which exists on this host. Motivated by the tension
   between [arXiv:2606.17339](https://arxiv.org/abs/2606.17339) (general encoders win on average)
   and [arXiv:2606.15436](https://arxiv.org/abs/2606.15436) (HeAR reaches near-full performance
   at 50 samples where OPERA needs 400).
2. **V4 — calibration under shift** (`m=6, n=10`). Free once V1/V3 predictions exist; ECE is
   already computed on every head and every confound in the bench artifacts and is rendered
   nowhere. Motivated by [arXiv:2601.07969](https://arxiv.org/abs/2601.07969) and the cross-corpus
   collapse to 0.43–0.68 documented in [arXiv:2511.14939](https://arxiv.org/abs/2511.14939).
3. **V5 — zero-shot audio-LLM as a leakage estimator** (`SCREENING`, promotion pre-declared).
   The only real GPU cost in the registry; 4-bit Qwen2-Audio-7B, per
   [arXiv:2506.17351](https://arxiv.org/abs/2506.17351), cross-checked in both input formats per
   [arXiv:2605.24806](https://arxiv.org/abs/2605.24806).
4. **F1-a — the actual audit.** Recompute the published SVD pipeline's *own* metric under (i) its
   original split and (ii) an age-matched speaker-disjoint split, and report the delta. This is
   the experiment the whole program is named after and it has never been run.
5. **Close the falsifiers.** V1, V6 and V7 each need Coswara/COUGHVID cells that are currently
   `not yet measured`; V2 needs its Coswara half.
6. **Fix the open implementation defects** and build a rung-0 `tests/` layer, so the ladder is
   enforced from below rather than assumed.

---

## Citations

Every identifier below was mechanically verified (abs page fetched, title + authors confirmed)
before it shipped, per R10; the verification date and list are in
`corpus/SURVEY_sota_methods.md`. Nothing here is cited from memory.

**The published numbers this program audits**

- Vrba et al., 2025 (rev. 14 Mar 2025), *Reproducible voice-pathology detection with a
  pitch-difference feature* ([arXiv:2410.10537](https://arxiv.org/abs/2410.10537)) — **UAR 85.22**
  (F 85.61 / M 84.69) on SVD, with a public repo and a REFORMS checklist. The external anchor for
  every SVD claim here (R11b).
- Yeh, Sun, Mahapatra, Chandra, Mower Provost, Sisman, 2026, *Who is Speaking or Who is
  Depressed? A Controlled Study of Speaker Leakage in Speech-Based Depression Detection*
  ([arXiv:2604.14354](https://arxiv.org/abs/2604.14354)) — establishes speaker leakage by
  measurement and reports that a DANN fails to close the gap. **Audited by V2 → F4**, which runs
  the mechanistic test they did not.
- *Feature scaling induced data leakage quantification in machine learning-based voice pathology
  detection*, *Applied Soft Computing* (`S1568494626007970`) — −0.14/+0.14 pp on SVD,
  −8.3/+7.8 pp on VOICED, on handcrafted features. **Audited by V6 → F5**, extended to embeddings.
- Liu, Feng, Yuan, Ling, Interspeech 2024, *Clever Hans Effect Found in Automatic Detection of
  Alzheimer's Disease through Speech* ([arXiv:2406.07410](https://arxiv.org/abs/2406.07410)) —
  near-100 % AD detection from silent segments alone on Pitt. **Audited by V7 → F6.**

**The field context**

- Bhalla, Kieu, Merchant, de Lara, Mariakakis, 2026, *SpeechDx: A Multi-Task Benchmark for
  Clinical Speech AI* ([arXiv:2606.17339](https://arxiv.org/abs/2606.17339), 15 Jun 2026) —
  12 datasets / 27 tasks / 12 encoders, all speaker-disjoint; Whisper-enc (MRR 0.44) >
  Qwen3-TTS-Tokenizer (0.40) > WavLM (0.38); *"no current representation generalizes reliably."*
- Coppock et al., 2024, *Audio-based AI classifiers show no evidence of improved COVID-19
  screening over simple symptoms checkers*, *Nature Machine Intelligence*
  ([arXiv:2212.08570](https://arxiv.org/abs/2212.08570)) — 67,842 individuals; ROC-AUC
  0.846 → **0.619** after matching on recruitment confounders. The canonical negative result.
- Sanap, Desikan, Lobaton, 2026, *Beyond Classification: A Cough Regression Benchmark for
  Respiratory Acoustic Foundation Models* ([arXiv:2606.15436](https://arxiv.org/abs/2606.15436),
  ICML 2026 Workshop) — HeAR near-full performance at 50 samples vs OPERA's 400. **Motivates V3.**
- Kafentzis & Selisios, 2026, *Tuberculosis Screening from Cough Audio: Baseline Models, Clinical
  Variables, and Uncertainty Quantification* ([arXiv:2601.07969](https://arxiv.org/abs/2601.07969),
  *Sensors* 26(4):1223) — **motivates V4.**
- de Brito, de Souza, Gauy, Finger, Candido Junior, 2025, *Fine-tuning Pre-trained Audio Models
  for COVID-19 Detection* ([arXiv:2511.14939](https://arxiv.org/abs/2511.14939)) — cross-dataset
  AUC collapse to 0.43–0.68. **Motivates V4.**
- Shahin, Ahmed, Epps, 2025 ([arXiv:2506.17351](https://arxiv.org/abs/2506.17351)) — Qwen2-Audio
  zero-shot cognitive-impairment detection "comparable to supervised methods". **Motivates V5**,
  cross-checked against Kabir & Munira, 2026
  ([arXiv:2605.24806](https://arxiv.org/abs/2605.24806)) so the reference is not
  language-confounded.
- Ishikawa & Duke, 2026, *A Multi-Probe Audit of Clinical-Interview Depression Detection
  Benchmarks* ([arXiv:2605.23977](https://arxiv.org/abs/2605.23977)) — 96 configurations across
  five corpora; CV and official-test rankings share minimal top-performer overlap.
- HPP-Voice ([arXiv:2505.16490](https://arxiv.org/abs/2505.16490)) — 7,188 recordings from 6,760
  adults; sleep apnea (males) AUC **0.64 ± 0.03** against a **0.57 demographic baseline**. The
  realism check for what an honest effect size looks like.
- Eyben, Scherer, Schuller et al., 2016, *The Geneva Minimalistic Acoustic Parameter Set (GeMAPS)
  for Voice Research and Affective Computing*, IEEE T-AFFC
  ([doi:10.1109/TAFFC.2015.2457417](https://doi.org/10.1109/TAFFC.2015.2457417)) — the 88
  eGeMAPS features that beat WavLM in F7; extracted with `opensmile-python 2.6.0`, recorded in
  the artifact's `backend` field.
- `microsoft/wavlm-base-plus` — the pre-registered headline representation, chosen because
  SpeechDx ranks it (MRR 0.38); recorded in the artifact's `backend.evidence` field.

**The method**

- Jain & Linares, 2026, *Agentic AutoResearch for Space Autonomy*
  ([arXiv:2606.20394](https://arxiv.org/abs/2606.20394), 18 Jun 2026) — a Karpathy-style LLM
  research loop with an in-loop credibility layer gating results on measured seed noise.
  **Near-identical architecture to this loop, and the most damaging single citation to any
  methods-novelty claim here** — which is why no such claim is made.

---

## Novelty — stated plainly

The agentic autoresearch loop is **not** novel
([arXiv:2606.20394](https://arxiv.org/abs/2606.20394) published an auditable autoresearch loop in
June 2026). Building a better voice detector is **not** the goal — Google HeAR, NIH Bridge2AI and
a dozen funded companies own that, and a laptop adds nothing. The claim here is **domain +
verdict-ledger**: systematically re-testing published voice-health claims and publishing what
survives. See [`audits/NOVELTY_CRITIQUE.md`](audits/NOVELTY_CRITIQUE.md), which argues this case
adversarially and concludes the domain survives under exactly one framing — **audit engine, not
detector factory**.

---

## Ethics

No PHI is committed. No restricted corpus is redistributed. No clinical claims are made — this
produces no diagnosis and is not therapy or medical care. Every dataset is used under its own
licence (SVD: CC-BY-4.0, [Zenodo 10.5281/zenodo.16874898](https://zenodo.org/records/16874898)).
Subgroup performance is reported whenever labels permit; a model that works only for one
demographic is a finding, not a footnote. **Not a medical device.**

---

## Provenance & credits

Built with **Claude Code as the autonomous research agent** on a single RTX 4090 Laptop (16 GB),
2026-07-25 → 2026-08-08. Eighth instantiation of the portable process in
[`meta-skills/`](meta-skills). Repository:
[github.com/dlmastery/auto-research-voice-based-disease-detection](https://github.com/dlmastery/auto-research-voice-based-disease-detection)
— the git history pins every number to the commit that produced it, and each bench artifact
carries its own `git_sha`. Composite specification fingerprint in force: `37e745ed9b0b`
(unimplemented — see above).

*Internal QA pass — independent external review pending.* Every audit in `audits/` was produced
by the same model family as the implementation (R16), so none of them is external validation.

**Licence:** no `LICENSE` file has been committed yet, so the code carries **no declared licence**
and is not yet open for reuse. Data licences are per-corpus and unchanged by this repository.
