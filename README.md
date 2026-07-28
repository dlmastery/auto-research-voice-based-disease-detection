# Voice-Health AutoResearch

**An autonomous, pre-registered audit harness for voice-based disease detection** — Karpathy-style hill-climbing that re-tests *published* voice-health classification claims for speaker leakage, acquisition confounds and cross-corpus collapse, and publishes a transparent ledger of which claims survive.

Eighth instantiation of a portable autoresearch process ([`meta-skills/`](meta-skills), 29 skills) previously run on FX, equities, tabular, medical imaging, [DSBench](https://github.com/dlmastery/autoresearch_dsbench), [DARE-bench](https://github.com/dlmastery/autoresearch_darebench) and activation steering. Runs on a single RTX 4090 laptop (16 GB).

---

## Background — start here

### What is "voice-based disease detection"?

A person speaks; a model listens and predicts a health condition. It is attractive because the sensor is a
microphone everyone already owns — no blood draw, no scanner, no clinic visit. Two mechanisms make it
plausible rather than magical:

1. **The larynx is the instrument.** Anything that changes the vocal folds — a paralysis, a polyp, swelling,
   a tumour, scar tissue from surgery — changes the sound directly and audibly. This is where the evidence
   is strongest, and it is what the corpus below actually contains.
2. **Speech is a motor act.** Producing fluent speech needs breath control, timing, and fine neuromuscular
   coordination, so neurological and respiratory disease can leave traces in speech even when the larynx is
   healthy. This is the claim behind Parkinson's, Alzheimer's, and COVID screening from voice. It is a much
   longer causal chain and correspondingly weaker evidence.

The literature also claims depression, diabetes, heart failure, and more. **This program tests none of those**,
for the reason in the next section.

### What the data actually supports

The primary corpus is the **Saarbrücken Voice Database (SVD)** — a clinical archive from Saarland
University Hospital. Each participant records **13 short vocalisations**: the sustained vowels `/a/`, `/i/`,
`/u/` at normal, high, low, and rising-falling pitch (12 clips), plus one spoken German sentence
(*"Guten Morgen, wie geht es Ihnen?"*).

| | |
|---|---|
| Recordings decoded | **28,509** |
| Sessions | 2,225 |
| **Speakers** | **1,679** (1,008 pathological / 671 healthy) |
| Distinct named pathologies | **70** |
| Mean age | healthy **27.2** · pathological **49.4** |

Seventy diagnoses sounds like seventy detectable diseases. It is not. Sorted by how many *speakers* carry
each label:

| condition has ≥ N speakers | number of conditions | speakers covered |
|---|---|---|
| ≥ 100 | **2** | 265 |
| ≥ 50 | **6** | 535 |
| **≥ 30** (this program's data floor) | **12** | 762 |
| ≥ 5 | 28 | 938 |
| ≥ 1 | 70 | 1,019 |

**19 of the 70 conditions are represented by a single speaker.** So the honest answer to *"how many diseases
can this detect?"* is:

- **1 task is properly powered** — binary *healthy vs. pathological* (1,008 vs. 671 speakers). This is what
  every headline number in this repository refers to.
- **At most 12 named conditions** clear a ≥30-speaker floor, and would need one-vs-rest treatment with wide
  confidence intervals. The largest are *Rekurrensparese* (recurrent-laryngeal-nerve palsy, 139),
  *Hyperfunktionelle Dysphonie* (126), *Laryngitis* (79), *Psychogene Dysphonie* (70).
- **58 conditions cannot be modelled at all** at any defensible sample size.

And note what those twelve *are*: they are almost all **dysphonias and structural larynx disorders** — the
category where sound changes because the sound-producing organ changed. The corpus contains essentially no
systemic disease. A model trained here detects **disordered voice**, not disease in general, and it is a
category error to describe it otherwise.

The two secondary corpora are respiratory: **Coswara** (72 participants, 9 tasks including cough and
breathing) and **COUGHVID** (13,535 cough clips, 720 COVID-19). COUGHVID ships **no speaker identifiers at
all**, so it is permanently barred from carrying an evaluation claim here — see *Corpora* below.

### The rest of the field

SVD is one corpus of many. **[The dataset landscape](https://dlmastery.github.io/auto-research-voice-based-disease-detection/datasets.html)**
catalogues every dataset the field uses to claim a disease can be heard in a voice — **25 corpora across 7
disease families**, 8 of them released or audited in **2026** — each scored on the question the published
surveys do not ask: *could a result on this dataset mean anything?*

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
**5 that may NEVER carry a generalisation claim** (COUGHVID has no speaker ids; TORGO/UASpeech have 15–19
speakers; the depression interview corpora classify the interviewer).

**Three findings from that landscape are the empirical case for this whole program:**

- **UK ONS / Turing** (67,842 individuals, *PCR-referenced* — the best labels in the field): AUC **0.846
  unadjusted → 0.619 after matching on recruitment confounders**. The largest, cleanest respiratory study
  ever run lost a quarter of its AUC to confounds.
- **HPP-Voice** is the only large study in the table that reports a demographic baseline beside its headline
  — and once it does, its best effect is **AUC 0.64 against a 0.57 bar**. That is what an honest voice-
  phenotype effect size looks like.
- **SpeechDx** ([arXiv:2606.17339](https://arxiv.org/abs/2606.17339), 27 tasks over 12 datasets, Jun 2026)
  concludes that **no current representation generalises reliably across clinical speech** — converging with
  this repository's F3 from an entirely different direction.

And the closest published work to this program's *method*: **[arXiv:2605.23977](https://arxiv.org/abs/2605.23977)**
(May 2026) audits five depression benchmarks and finds the official E-DAIC leaderboard is essentially noise —
the best cross-validation configuration ranks **20th** on the official test, the test winner ranks **41st** by
CV, and **top-3 overlap is zero**.

### Why this program exists

Published SVD results report UAR in the mid-80s. But healthy volunteers in this corpus average 27 years old
and patients average 49, so **patient age alone reaches ROC-AUC 0.871 without hearing a single audio sample**
(F1 below). Any classifier that quietly learns "older ⇒ patient" inherits that score for free.

That makes the interesting quantity not the accuracy but the **margin above the demographic baseline on the
identical folds** — a number the field does not currently report. Measuring it is the entire purpose of this
repository, and the first time we did (F3) the margin came out **negative**.

> **Not a medical device.** Nothing here is a clinical claim, a diagnosis, or fit for any care decision.

---

## Goal

> Beat the published number on every corpus **and** clear the demographic-confound bar on the identical folds, under speaker-disjoint splits — reporting all four numbers every time.

That second clause is the whole point. On the Saarbrücken Voice Database, **patient age alone reaches ROC-AUC 0.871** while the published benchmark is **UAR 85.22**. So "beating SOTA" here is achievable by leaning harder on who is old and who is young — a number that dies on first contact with another corpus. Nobody in this field currently reports the margin above the confound baseline. That is the gap this program exists to fill.

**Every claim carries four numbers:**

| published SOTA | ours | confound baseline | margin above confound |
|---|---|---|---|

A win that does not clear the confound bar is logged **NOT CLEARED**, not announced.

---

## Status — honest

| | |
|---|---|
| Findings | **3** — F1 (age baseline), F2 (COUGHVID has no speaker ids), **F3 (certified)** |
| Benchmark results | SVD measured at **full corpus**, 5-fold × 8 repeats, speaker-disjoint |
| Corpora decoded | **SVD 28,509 recs / 1,679 speakers**, Coswara, COUGHVID |
| Headline | **Strip the confounds and a 2016 feature set beats a self-supervised transformer.** See the four-step arc below. |

Nothing here is a clinical claim. This is not a medical device.

### The result, in four steps

Each step removes something the model was getting for free, and asks what survives.

| step | finding | what it establishes |
|---|---|---|
| 1 | **F1/F3** — patient **age alone** reaches **0.8737** rec-AUC; WavLM reaches **0.7438** | the audio model loses to one demographic variable |
| 2 | **F4** — projecting out the speaker-identity subspace costs WavLM **more** AUC than removing *more* variance any other way | **24–39%** of its discrimination is *who is speaking* |
| 3 | **F7a** — with age matched to a **0.77-year** gap, age-only collapses **0.8737 → 0.5534** | the confound is genuinely removed, not assumed away |
| 4 | **F7b** — on that matched subset **eGeMAPS 0.6496 > WavLM 0.6227**, CI [−0.032, −0.022], **10/10 seeds** | **88 handcrafted features beat 1536 learned ones** |

What is left when demographics and identity are stripped out is **AUC ≈ 0.65** — real,
well above chance, far below the ~0.85 the literature reports on this corpus, and
nowhere near clinical usefulness. Whatever WavLM's extra 1,448 dimensions were buying
at 0.7438, it was substantially age and identity rather than pathology.

This converges with SpeechDx ([arXiv:2606.17339](https://arxiv.org/abs/2606.17339)) —
"no current representation generalises reliably across clinical speech" — from a
different direction, and more specifically: here the confounds are *measured* rather
than assumed.

### F3 — the audio model loses to a single demographic variable

Speaker-disjoint `GroupKFold`, 5 folds × 8 repeats, on all 1,679 speakers:

| predictor | recording-AUC | speaker-AUC |
|---|---|---|
| WavLM + logistic regression | 0.7438 | 0.8671 |
| WavLM + rank-3 ensemble | 0.7443 | 0.8650 |
| **age alone** (no audio) | **0.8737** | 0.8642 |
| age + sex + duration + RMS | 0.8747 | 0.8649 |
| *sex alone* (negative control) | *0.4898* | — |
| *duration alone* (negative control) | *0.4724* | — |

The negative controls sitting at chance are what isolate the effect: it is **age**, not some generic
metadata leak. Power contract cleared (`n=8, m=2, min p=0.0078 < Holm 0.025`), so this is a *powered*
negative rather than a small-sample curiosity — a self-supervised speech model, given 28,509 clinical
recordings, is beaten at the recording level by asking the patient's age.

---

## F1 — on SVD, age alone reaches ROC-AUC 0.871 without hearing any audio

Using **only** the demographics shipped with the corpus — no audio, no features, no model of speech:

| predictor | ROC-AUC |
|---|---|
| **age alone** | **0.8709** |
| sex alone | 0.5172 |
| age + sex, logistic, **speaker-disjoint** 5-fold `GroupKFold` | **0.8768** |

n = 2,225 sessions / 1,853 speakers (1,356 pathological / 869 healthy).

**Cause — a recruitment asymmetry:** healthy speakers average **28.3 years**, pathological **51.0**. Young volunteers versus older clinic patients.

**Second finding from the same 167 KB file:** 200 of 1,853 speakers contribute more than one session (max 24). A default `train_test_split` leaks all of them across folds.

**What this does NOT claim:** it does not show any published result is wrong. UAR and ROC-AUC are different metrics and the comparison is indicative, not like-for-like. Some pipelines may already age-match. The audit question is whether the margin above the demographic bar is *reported at all* — recomputing a published pipeline under age-matched, speaker-disjoint splits is the next experiment, not this one.

```bash
python scripts/audit_demographic_baseline.py --dataset svd   # CPU, seconds
```

Full write-up: [`FINDINGS.md`](FINDINGS.md) · raw: [`autoresearch_results/F1_demographic_baseline.json`](autoresearch_results/F1_demographic_baseline.json)

---

## Corpora

| corpus | access | speakers | speaker-disjoint possible? | published target |
|---|---|---|---|---|
| **Saarbrücken (SVD)** | open, CC-BY-4.0, [Zenodo 38.1 GB](https://zenodo.org/records/16874898) | 1,853 | **yes** (`SprecherID`) | UAR **85.22** ([arXiv:2410.10537](https://arxiv.org/abs/2410.10537)) |
| **Coswara** | open, `git clone` | participant ids | **yes** | AUC ≈ 0.92 |
| **COUGHVID** | open, Zenodo | **0 real speaker ids** | **NO — blocker** | (OOD / pretraining only) |
| PROCESS-2 | fast DUA | 400 | yes | macro-F1 0.59 |
| Bridge2AI-Voice | slow DUA (PhysioNet) | 833 | yes | — |

COUGHVID is demoted permanently: a "speaker-disjoint" split over recording UUIDs is not speaker-disjoint, because one person may contribute many recordings. It **may never carry an evaluation claim**.

---

## The rules that make this trustworthy

Written against the July-2026 state of the art in autonomous research *and* a forensic post-mortem of a sibling program that produced **124 experiments and zero external-ready findings**. Every rule in [`CLAUDE.md`](CLAUDE.md) is paid for. The load-bearing ones:

- **R1 — no orphan numbers.** Every number carries a pointer to the artifact that produced it.
- **R3/R4 — validate the instrument before trusting it.** The sibling program ran 124 experiments on a judge scoring AUC 0.68 against its own ≥0.85 bar; every result *and every null* was uninterpretable.
- **R6 — power must be arithmetically possible.** `n ≥ 7 + Holm` is *unsatisfiable* for families of m ≥ 4 (min p = 2/2ⁿ vs 0.05/m). Feasibility is computed per family; the first pre-registration here needed **n = 10**, not 8.
- **R7 — falsifiers must be executed**, not merely declared.
- **R8 — negative results are first-class**, in the same tables, with the same detail.
- **R11b — every hill-climb targets an external published number.** Across seven prior programs this was the single strongest predictor of success: repos anchored to a public benchmark produced real results; repos climbing a self-defined composite produced rising curves and zero information.
- **R11c — ship the runner before the 300th scaffold.** A sibling built 324 task scaffolds and ran zero experiments.
- **R11d — retraction machinery.** [`autoresearch_results/_quarantined/`](autoresearch_results/_quarantined) exists so results can be *withdrawn*.

---

## Layout

```
CLAUDE.md                  the constitution — read before any work
meta-skills/               29 portable, domain-agnostic autoresearch skills
skills/                    6 domain skills (speaker-disjoint splits, confound
                           baseline, claim audit, dataset onboarding,
                           embedding extraction, calibration & subgroups)
corpus/                    citation-verified surveys (datasets, SOTA methods,
                           autoresearch state of the art)
audits/                    novelty critique · prior-repo archaeology
src/voicehealth/           embed.py · features.py · benchmark.py
scripts/                   fetch_* · preprocess_audio.py · audit_demographic_baseline.py
data/                      cards, manifests (audio gitignored)
AXIS_TAXONOMY.md           what "change exactly one thing" means here
COMPOSITE.md               the Goodhart-resistant internal ranking metric
IDEA_TABLE.md              hypotheses + falsifiers + required n
PREREGISTRATION.md         the first experiment, fixed before the run
FINDINGS.md                rigor-gated findings, positive and negative
```

---

## Quickstart

```bash
python scripts/fetch_svd.py --metadata-only          # 167 KB, no DUA
python scripts/audit_demographic_baseline.py --dataset svd
```

Reproduces F1 in seconds on CPU. Full corpus + benchmark: see [`data/ACQUISITION_STATUS.md`](data/ACQUISITION_STATUS.md).

---

## Novelty — stated plainly

The agentic autoresearch loop is **not** novel ([arXiv:2606.20394](https://arxiv.org/abs/2606.20394) published an auditable autoresearch loop in June 2026). Building a better voice detector is **not** the goal — Google HeAR, NIH Bridge2AI and a dozen funded companies own that, and a laptop adds nothing. The claim here is **domain + verdict-ledger**: systematically re-testing published voice-health claims and publishing what survives. See [`audits/NOVELTY_CRITIQUE.md`](audits/NOVELTY_CRITIQUE.md), which argues this case adversarially.

---

## Ethics

No PHI is committed. No restricted corpus is redistributed. No clinical claims are made — this produces no diagnosis and is not therapy or medical care. Every dataset is used under its own licence. Subgroup performance is reported whenever labels permit; a model that works only for one demographic is a finding, not a footnote.
