# FINDINGS — voice-health claim audit

> Rigor-gated only. Negative and inconvenient results appear here with equal
> prominence (R8). Every number carries a pointer to the artifact that produced it
> (R1). Nothing here is a clinical claim.

---

## F1 — On SVD, patient AGE alone reaches ROC-AUC 0.871 without hearing any audio

**Status:** SCREENING-tier, metadata-only. Reproducible in seconds on CPU.
**Date:** 2026-07-25 · **Artifact:** `data/raw/svd_meta/voice_data.csv`
(md5 `2ee9852a…`, 167,457 B, fetched from `stimmdb.coli.uni-saarland.de/data/voice_data.csv`)

### The measurement

Using **only** the demographic metadata distributed with the Saarbrücken Voice
Database — no audio, no features, no model of speech:

| predictor | ROC-AUC (pathological vs healthy) |
|---|---|
| **age alone** | **0.8709** |
| sex alone | 0.5172 |
| age + sex, logistic, **speaker-disjoint** 5-fold `GroupKFold` | **0.8768** |

n = 2,225 sessions (1,356 pathological / 869 healthy), 1,853 unique speakers.

**Underlying cause — a recruitment asymmetry:**

| class | mean age | sd |
|---|---|---|
| healthy | 28.3 | 11.6 |
| pathological | 51.0 | 15.8 |

Healthy speakers are young volunteers; pathological speakers are older clinic
patients. The classes differ by ~23 years of age.

### Why it matters

The published SVD benchmark this program intends to hill-climb against reports
**UAR 85.22** (arXiv:2410.10537). A demographic-only model reaches AUC ≈0.877 on the
same corpus. **Any audio model on SVD must therefore demonstrate a margin above the
demographic bar to support the claim that it detects laryngeal pathology rather than
patient age.**

This is the field's documented "recruitment / symptom confound" (`corpus/SURVEY_datasets.md`
§3.2), instantiated in its most widely used open voice-pathology corpus.

### What this does NOT claim — read before citing

1. **This does not show any published result is wrong.** UAR and ROC-AUC are different
   metrics and are not directly comparable; the comparison above is indicative, not a
   like-for-like contest. A proper audit must recompute the published pipeline's metric
   on matched splits — that is the next experiment, not this one.
2. Several published pipelines may already control for age, use age-matched subsets, or
   report demographic baselines. **The audit question is whether the margin above the
   demographic bar is reported at all** — not whether these researchers were careless.
3. Metadata-only baselines say nothing about whether voice *does* carry pathology
   signal. It very likely does. The claim is strictly about **attribution**.

### Second observation, same artifact — a live leakage trap

**200 of 1,853 speakers contribute more than one session** (max 24 sessions for a single
speaker; mean 1.20). Splitting SVD at the *recording* level — the default in any naive
`train_test_split` — leaks those 200 speakers across folds. All work in this repository
splits on `SprecherID` via `GroupKFold`, and asserts speaker-disjointness before every
fit (pre-registered in `PREREGISTRATION.md` §A3).

### Pre-registered follow-up

- **F1-a** Recompute the published pipeline's own metric under (i) its original split and
  (ii) an age-matched, speaker-disjoint split. Report the delta. *This is the actual audit.*
- **F1-b** Report the margin of a frozen-embedding audio model **above** the 0.877
  demographic bar, per the constitution's "claim only the margin above the strongest
  confound baseline" rule.
- **F1-c** Repeat the demographic-baseline audit on Coswara and COUGHVID.

### Reproduce

```bash
# metadata (167 KB), then the baseline — CPU, seconds, no audio required
python scripts/fetch_svd.py --metadata-only
python scripts/audit_demographic_baseline.py --dataset svd
```

---

## F2 — WavLM embeddings do NOT clear the demographic bar on SVD (pilot)

**Status:** SCREENING, and formally **UNDERPOWERED** — the harness refused to certify it.
**Date:** 2026-07-27 · **Artifact:** `autoresearch_results/bench_svd_wavlm_mean_std.json`
(config_hash `d8ab0b7584b7fdb7`) · embeddings cached, speaker-disjoint `GroupKFold`,
3 repeats × 5 folds, scaler fit train-only inside each fold.

### The measurement

667 recordings / **49 speakers** (20 pathological / 29 healthy).

| model | rec-AUC | rec-UAR | spk-AUC | spk-UAR | ECE |
|---|---|---|---|---|---|
| ens_rank3 (best audio) | 0.6190 | 0.5829 | **0.7448** | 0.6853 | 0.159 |
| mlp | 0.6184 | 0.5931 | 0.7241 | 0.6810 | 0.238 |
| gbt | 0.6043 | 0.5895 | 0.6862 | 0.5905 | 0.234 |
| logreg | 0.5845 | 0.5750 | 0.6879 | 0.6810 | 0.255 |
| linsvm | 0.5653 | 0.5166 | 0.6224 | 0.5000 | 0.049 |
| **confound: age only** | **0.7146** | 0.6665 | **0.7207** | 0.6716 | 0.247 |
| confound: age+sex | 0.6979 | 0.7026 | 0.7017 | 0.7060 | 0.243 |
| confound: sex only | 0.5013 | 0.5989 | 0.5009 | 0.6009 | 0.218 |
| confound: duration only | 0.4591 | 0.5000 | 0.4759 | 0.5000 | 0.001 |
| confound: intensity (RMS) only | 0.4253 | 0.4974 | 0.4276 | 0.5000 | 0.026 |

### Verdict: NOT CLEARED

**Age alone (rec-AUC 0.7146) beats every audio head (best 0.6190) at the recording
level.** At speaker level the ensemble leads 0.7448 vs 0.7207 — a margin of **+0.024**
against speaker-level CIs of roughly **±0.13** (`audits/DATA_SPLIT_AUDIT.md`). That is
not a result; it is noise around a demographic prior.

The power check refused certification: `n_paired=3, m=5, min_attainable_p=0.25 vs
Holm α=0.01 → feasible=False`. Every head is labelled **NOT CLEARED | UNDERPOWERED (R6)**.

### Why this is the point of the program

A naive write-up of this same run would report *"WavLM reaches spk-AUC 0.74 on voice
pathology"* — a number that looks publishable and is, on this corpus, indistinguishable
from asking the patient's age. The two-bar standard (R11b + the confound baseline on
identical folds) turned a plausible headline into an honest negative on the program's
**first** experiment.

Note also what the confound row rules OUT: duration (0.459) and loudness (0.425) are
*below* chance, so the tell is specifically **age**, not recording length or level.

### Limitations — do not over-read this either

1. **49 speakers.** The full SVD corpus (1,853 speakers) is still downloading. This
   result may not survive more data, in either direction.
2. WavLM-base-plus, mean+std pooling, one layer choice. Other backbones
   (wav2vec2, Whisper-encoder, HeAR) and poolings are untested.
3. This says nothing about whether voice *carries* pathology signal — only that **these
   embeddings, on this corpus, at this n, do not beat age.**

---

## F3 — At FULL corpus scale (1,679 speakers), WavLM still does not clear the age bar

**Supersedes F2's pilot numbers.** Same protocol, 34× the speakers.
**Date:** 2026-07-27 · **Artifact:** `autoresearch_results/bench_svd_wavlm_mean_std.json`
(config_hash `f267bc4b705e8645`) · **28,509 recordings / 1,679 speakers**
(1,002 pathological / 677 healthy speakers), speaker-disjoint `GroupKFold`, 5 folds,
scaler fit train-only inside each fold.

### The measurement

| model | rec-AUC | rec-UAR | spk-AUC | spk-UAR | ECE |
|---|---|---|---|---|---|
| logreg (WavLM) | 0.7386 | 0.6402 | 0.8665 | 0.6845 | 0.059 |
| linsvm (WavLM) | 0.7375 | 0.6008 | **0.8676** | 0.5598 | 0.022 |
| ens_rank3 | 0.7385 | 0.6702 | 0.8632 | 0.7678 | 0.164 |
| **confound: age only** | **0.8744** | **0.8067** | 0.8645 | 0.7964 | 0.067 |
| confound: age+sex | **0.8751** | **0.8136** | 0.8650 | 0.8055 | 0.075 |
| confound: age+sex+duration+RMS | **0.8752** | 0.8142 | 0.8653 | 0.8045 | 0.074 |
| confound: sex only | 0.5293 | 0.5000 | 0.5246 | 0.5000 | 0.000 |
| confound: duration only | 0.4859 | 0.5000 | 0.4947 | 0.5000 | 0.010 |
| confound: intensity (RMS) only | 0.5090 | 0.5000 | 0.5190 | 0.5000 | 0.006 |

### Verdict: NOT CLEARED — and the gap WIDENED with more data

- **Recording level:** age alone **0.8744** vs the best audio head **0.7386** — age wins
  by **+0.136**. In the 49-speaker pilot this gap was +0.096; more data made it *larger*,
  not smaller, which is the opposite of what a noise explanation predicts.
- **Speaker level:** audio 0.8676 vs age 0.8645 — a margin of **+0.003**. Essentially tied.
- **The negative controls hold:** duration (0.4859) and loudness (0.5090) sit at chance,
  so the tell is specifically **age**, not recording length or level.

### The observation that matters most

**The published SVD benchmark is UAR 85.22** (arXiv:2410.10537). Patient **age alone**
reaches **UAR 0.8067** at recording level, and age+sex **0.8136** — i.e. a model that
hears nothing lands within a few points of the published headline, while our WavLM heads
reach only 0.60–0.67.

This does **not** prove any published result is wrong: the metric definitions, splits and
preprocessing differ, and a proper audit must recompute a published pipeline under
matched conditions (that is F1-a, still to run). But it does establish the bar. **Any
voice-pathology claim on SVD that does not report its margin above a demographic
baseline is uninterpretable**, because the demographic baseline is already close to the
number being claimed.

### Statistical status — CERTIFIED (2026-07-27)

The repeat=8 run cleared the power contract: `power R6: n_paired=8, m=2,
min_attainable_p=0.00781 vs Holm α=0.02500 → **feasible=True**`. The heads are no longer
labelled UNDERPOWERED; the verdict is simply **NOT CLEARED**.

Certified numbers (8 repeats × 5 speaker-disjoint folds):

| model | rec-AUC | rec-UAR | spk-AUC |
|---|---|---|---|
| logreg (WavLM) | 0.7438 | 0.6409 | 0.8671 |
| ens_rank3 | 0.7443 | 0.6759 | 0.8650 |
| **confound: age only** | **0.8737** | **0.8078** | 0.8642 |
| **confound: age+sex+duration+RMS** | **0.8747** | 0.8127 | 0.8649 |
| confound: sex only | 0.4898 | 0.5000 | 0.5027 |
| confound: duration only | 0.4724 | 0.5000 | 0.5021 |
| confound: RMS only | 0.5121 | 0.5000 | 0.5206 |

The conclusion is unchanged and now carries statistical power: **at recording level the
demographic bar (0.8747) exceeds the best audio head (0.7443) by +0.130**, and at speaker
level they are tied (0.8671 vs 0.8649, +0.002). The negative controls remain at chance.

### Limitations

1. One backbone (WavLM-base-plus), one pooling (mean+std), one layer. wav2vec2,
   Whisper-encoder and HeAR are untested — a better representation may yet clear the bar.
2. Speaker-level aggregation is a simple mean over a speaker's recordings; a better
   aggregator might help the audio side.
3. This says nothing about whether voice *carries* pathology signal. It says these
   embeddings, on this corpus, do not beat knowing the patient's age.

---

## F4 — About a third of WavLM's disease discrimination is speaker IDENTITY, not pathology

**Tier: EVALUATION** (n = 10 repeats × 5-fold speaker-disjoint, m = 14 pre-registered,
min attainable paired p = 0.001953 ≤ Holm 0.05/14 = 0.003571). Judge-free.
Artifact: `autoresearch_results/V2_speaker_subspace.json` · 4h15m CPU ·
negative control: `V2_speaker_subspace_SHUFFLE.json`.

Pre-registered as **V2** in `IDEA_TABLE.md` before the run. Audits Yeh et al., 2026,
*Who is Speaking or Who is Depressed?* ([arXiv:2604.14354](https://arxiv.org/abs/2604.14354)),
which established speaker leakage by **measurement**; the mechanistic test — estimate
the identity subspace, project it out, re-measure — had not been run.

### The result

Estimate the identity subspace from between-speaker scatter (training speakers only,
inside each fold), project it out, re-measure disease AUC. Compare against controls
that remove **at least as much variance** a different way.

| k | AUC, speaker subspace removed | AUC, top-k PCA removed | **D vs top-k [95% CI]** | variance removed spk / topk | identity as % of headroom |
|---|---|---|---|---|---|
| 1 | 0.6755 | 0.7320 | **+0.0565** [+0.056, +0.058] | 0.206 / 0.345 | 23.7% |
| 2 | 0.6739 | 0.7302 | **+0.0564** [+0.055, +0.058] | 0.261 / 0.616 | 23.7% |
| 4 | 0.6446 | 0.7189 | **+0.0743** [+0.072, +0.078] | 0.451 / 0.718 | 31.2% |
| **8** | **0.6104** | 0.7025 | **+0.0921** [+0.090, +0.094] | 0.700 / 0.812 | **38.7%** |
| 16 | 0.5959 | 0.6692 | **+0.0734** [+0.071, +0.076] | 0.819 / 0.879 | 30.8% |
| 32 | 0.5661 | 0.6529 | **+0.0869** [+0.085, +0.088] | 0.893 / 0.926 | 36.5% |
| 64 | 0.5398 | 0.6287 | **+0.0888** [+0.086, +0.091] | 0.940 / 0.959 | 37.3% |

Full-embedding AUC **0.7382**; headroom above chance 0.2382. `D` is positive with a
95% CI excluding zero at **all 7 ranks against both controls**.

**The cleanest form of the result:** at *every* rank the speaker subspace removes
**less** variance than top-k PCA (0.700 vs 0.812 at k=8) yet costs **more** AUC. Deleting
more signal a different way hurts less. The damage is direction-specific, not a
variance effect.

### The negative control passes

Permuting the speaker→label map (identical pipeline, `V2_SHUFFLE=1`) collapses
everything to chance: full AUC **0.5074**, and D at k=8 falls from **+0.0921 to
+0.0016** — a 58× reduction. This matters more than usual here because **D is a
difference**, so a systematic bug inflating every arm equally would have survived the
whole table above untouched. Speaker-ID accuracy is unchanged by the shuffle
(0.278 / 0.193), exactly as it should be — permuting *diagnoses* cannot affect *who is
speaking*.

### What this does NOT show — the falsifier did not fire

The pre-registered falsifier required **two** conditions: D's CI excluding zero **and**
`AUC_spk` collapsing to include 0.5. **Only the first holds.** At k=64 the projected AUC
is 0.5398 — near chance, but the intervals are tight and it does not reach it. So the
strong conclusion the falsifier would have licensed — *"the clinical-validity claim is
falsified"* — **does not follow**. Identity is a large, direction-specific component of
what this model uses. It is not the whole signal.

Two pre-registered predictions also missed, recorded rather than quietly dropped:

1. Predicted the control would drop **< 0.05**; top-k PCA dropped **0.069**. In fairness
   to the prediction, it assumed a *random* control, and the control actually used is far
   stricter — but the number missed and is reported as missed.
2. **The manipulation check remains uninformative.** Predicted speaker-ID accuracy
   ~0.90 → < 0.30; measured **0.278 → 0.193**. It cleared "< 0.30" only because it
   started there. Mean-pooled WavLM-base+ is not an x-vector, and my prediction assumed
   it was. **Consequence: the projection demonstrably removes something
   direction-specific and identity-correlated, but "the subspace removed *is* the
   identity subspace" is supported only weakly.** A stronger identity probe is the
   obvious next step.

### Composed with F3

F3: at full corpus scale WavLM reaches rec-AUC **0.7438** while patient **age alone**
reaches **0.8737** — the audio model does not clear the demographic bar. F4 adds that
roughly **a third of the discrimination it does have is speaker identity**. The two
together describe an audio representation that is beaten by a single demographic
variable, and whose remaining margin is substantially *who is talking* rather than
*what is wrong with them*.

### Scope

SVD only — the pre-registered family names SVD **and** Coswara, so half of it is
unexecuted, and `m = 14` was deliberately kept rather than shrunk to the m = 7 actually
run. One backbone (WavLM mean+std), one head (logistic regression); the audited paper
claims identity reliance is a property of speech representations *in general*, which
this single-representation result cannot establish.

> Not a medical device. No diagnosis, no clinical claim.
> Internal QA pass — independent external review pending.

---

## F5 — Scaler-before-split leakage is *nothing* on SVD embeddings (0.00004 AUC), but the corpus-specificity claim is UNTESTED

**Tier: PARTIAL** — 3 of 6 pre-registered cells ran; one is underpowered by construction. n = 10 × 5-fold speaker-disjoint,
m = 6 pre-registered. Judge-free. Artifact: `autoresearch_results/V6_preprocessing_leakage.json`.

Pre-registered as **V6**. Audits *Feature scaling induced data leakage quantification in
machine learning-based voice pathology detection*, *Applied Soft Computing*
(`S1568494626007970`), which measured −0.14/+0.14 pp on SVD and −8.3/+7.8 pp on VOICED
— on **handcrafted** features.

| cell | fit_on_all | fit_per_fold | **D [95% CI]** | within ±0.01 |
|---|---|---|---|---|
| SVD / WavLM | 0.7382 | 0.7382 | **+0.00004** [+0.00001, +0.00007] | yes |
| SVD / eGeMAPS | 0.5315 | 0.5357 | **−0.00418** [−0.00627, −0.00221] | yes |
| **Coswara / WavLM** | 0.4929 | 0.4906 | **+0.00236** [+0.00044, +0.00483] | yes |
| Coswara / eGeMAPS | — | — | NOT RUN — no cached eGeMAPS | — |
| COUGHVID ×2 | — | — | **DELIBERATELY EXCLUDED** — see below | — |

**Established.** The published near-null on SVD reproduces, and extends from handcrafted
features to **embeddings** — the representation the field actually uses, and one the
audited paper did not test. At 28,509 rows, fitting the scaler on everything versus on
train only is worth **0.00004 AUC**. That is not "small"; it is nothing.

**A reproduction of the paper's subtler point.** The eGeMAPS cell is **negative** with a
CI excluding zero: leakage made performance slightly *worse*. That matches the audited
observation that scaler leakage can degrade as well as inflate — a direction most
treatments of data leakage do not consider.

**My prediction MISSED on the half that mattered.** I predicted `< 0.01 on SVD`
(**confirmed**) and `> 0.03 on at least one of Coswara/COUGHVID`. Coswara measured
**+0.0024** — an order of magnitude below the predicted threshold. So across two corpora
and two representations, scaler-fit scope on embedding features is **uniformly
negligible**, and the "corpus-specific magnitude" claim is *not supported* for this
pipeline family. That is the direction of the falsifier, though it formally requires all
six cells.

**THE LIMITATION THAT CAPS THE COSWARA CELL — read before citing it.** Coswara's
classifier sits at **AUC 0.49, i.e. chance**. A leakage test asks whether preprocessing
scope *inflates* performance, and **there is nothing to inflate in a model with no
signal**. That cell therefore cannot detect the effect it was run to detect; it is
consistent with "no leakage" and equally consistent with "no power to see leakage." It
should be read as a null *observation*, not a null *result*. A corpus where the audio
model actually works is required to test this properly, and on the corpora available to
this program that means SVD alone — which is where the audited paper already reported a
near-null.

**COUGHVID: deliberately excluded, with cause.** Extraction was reaped twice at ~8.5% of
13,535 files, but that is not the reason it was abandoned. [F2](#f2--wavlm-embeddings-do-not-clear-the-demographic-bar-on-svd-pilot)
established COUGHVID ships **zero real speaker identifiers** — 13,535 unique ids for
13,535 recordings — so its `GroupKFold` degenerates to plain `KFold`. Populating cells
whose results could never carry an evaluation claim is not a good use of GPU hours in a
program whose subject is precisely that unclaimable numbers get reported as claims. This
is recorded as a judgement with its reasoning, not a silent omission: *a pre-registered
cell that becomes known-uninformative is a different thing from one that is merely
inconvenient.*

**Status: V6 is NOT closed.** 3 of 6 cells, one of them underpowered by construction.

---

## F6 — The Clever-Hans silence shortcut does NOT generalise: near chance on all three corpora

**Tier: PARTIAL** — 4 of 6 cells; but the **silence arm ran on all three corpora**.
n = 10 × 5-fold speaker-disjoint, m = 6 pre-registered. Judge-free.
Artifact: `autoresearch_results/V7_silence_shortcut.json` · 42,654 files VAD'd, 0 unreadable.

Pre-registered as **V7**. Audits Liu, Feng, Yuan, Ling, Interspeech 2024, *Clever Hans
Effect Found in Automatic Detection of Alzheimer's Disease through Speech*
([arXiv:2406.07410](https://arxiv.org/abs/2406.07410)) — near-100% AD detection from
**silent segments alone** on Pitt.

| corpus | features | AUC | directionless | ≥ 0.60 |
|---|---|---|---|---|
| SVD | silence_only | 0.5136 [0.5104, 0.5174] | 0.5136 | **no** |
| SVD | duration+intensity | 0.5048 [0.5020, 0.5077] | 0.5048 | **no** |
| Coswara | silence_only | 0.4854 [0.4668, 0.5037] | 0.5146 | **no** |
| COUGHVID | silence_only | 0.5264 [0.5251, 0.5277] | 0.5264 | **no** |
| Coswara, COUGHVID | duration+intensity | NOT RUN — no cached metadata | — | — |

**Every cell that ran is near chance.** The silence arm — the one the Pitt paper is
actually about — ran on **all three corpora** and never exceeded **0.527**.

**My predicted mechanism is WRONG, and that is the informative part.** I predicted
silence_only ∈ [0.55, 0.70] on Coswara because it is crowd-recorded and protocol-
heterogeneous, i.e. that the shortcut scales with **acquisition heterogeneity**.
Coswara measured **0.5146 — the lowest of the three**, below the predicted band. The
SVD half ([0.50, 0.60] predicted, 0.5136 measured) was confirmed, but the
heterogeneity mechanism it was meant to contrast with is not supported.

**The caveat that limits this null, stated plainly.** SVD, Coswara and COUGHVID are
corpora of sustained vowels, coughs and breathing — **short, prompted vocalisations**.
Pitt is spontaneous picture-description speech, where pause structure plausibly carries
cognitive load directly. So this is a fair test of *whether the shortcut generalises to
these corpora* — and it does not — but it is **not** evidence that the Pitt effect was
spurious. These corpora may simply lack the pause structure that could carry such a
signal at all. A generalisation test on another *spontaneous-speech* corpus would be the
sharper experiment, and PROCESS-2 is the obvious candidate once its gate clears.

**Useful either way:** these four numbers are now the measured confound floor for this
corpus set. A headline model here must beat ~0.53, not 0.50.

> Not a medical device. Internal QA pass — independent external review pending.

---

## F7 — With age matched away, 88 handcrafted features BEAT a 1536-dim SSL model

**Tier: EVALUATION for the cell that ran** (n = 10 × 5-fold speaker-disjoint, m = 9
pre-registered). Judge-free. Artifact: `autoresearch_results/V1_ssl_vs_handcrafted.json`.
Pre-registered as **V1**.

Every prior finding here was about what the model gets for free. F1/F3: patient **age
alone** reaches 0.8737 while WavLM reaches 0.7438. F4: ~a third of WavLM's
discrimination is **speaker identity**. That leaves the question those findings cannot
answer — **once age is removed by construction, is anything real left?**

### Feasibility, re-checked — a design that used to be impossible

`audits/DATA_SPLIT_AUDIT.md` **failed** this design at 49 speakers: only **9**
age-matched pairs existed. At the full 1,679-speaker corpus, greedy sex-exact
age-±3y matching yields **308 pairs (616 speakers)**. V1 became runnable purely because
the corpus grew 34×.

### The matching worked — and it is checked, not assumed

| | unmatched (F3) | **matched (F7)** |
|---|---|---|
| age gap, healthy vs pathological | **22.2 years** | **0.77 years** |
| age-only ROC-AUC | **0.8737** | **0.5534** |

The built-in falsifier for the construction — *an age-only classifier must collapse
toward chance* — is satisfied. Age went from the single best predictor in this corpus to
nearly uninformative.

### The result

| predictor, on the matched subset | ROC-AUC | margin above the residual age bar |
|---|---|---|
| age only (the residual bar) | 0.5534 | — |
| WavLM-base+ (1536-dim SSL) | 0.6227 | +0.0693 [+0.0598, +0.0789] |
| **eGeMAPS (88 handcrafted features)** | **0.6496** | **+0.0962** |

**The registered claim is SUPPORTED, and not marginally.** `WavLM − eGeMAPS =
**−0.0269**`, 95% CI **[−0.0317, −0.0215]** — excluding zero — and eGeMAPS wins in
**10 of 10 seeds**. Measured against the residual age bar, 88 handcrafted features
capture **39% more real signal** than a 1536-dimensional self-supervised model.

Both encoders clear the residual age bar in all 10 of 10 seeds — the first evidence in
this program that the audio itself carries pathology-relevant signal rather than
demographics. **But the SSL model is the weaker of the two.**

**My prediction was directionally right and quantitatively understated.** I predicted
eGeMAPS would land *within noise* of WavLM. It did not land within noise — it won
outright, with a CI excluding zero. Registered before the run, recorded as understated
rather than reframed after the fact.

**Converges with the 2026 literature from a different direction.** SpeechDx
([arXiv:2606.17339](https://arxiv.org/abs/2606.17339), 27 tasks / 12 datasets) concluded
that no current representation generalises reliably across clinical speech. This result
is sharper and more specific: on a corpus where the confounds have been *measured* rather
than assumed — age equalised to a 0.77-year gap, identity's contribution quantified at
24–39% by F4 — a 2016-era handcrafted feature set beats a self-supervised transformer.
Whatever WavLM's extra 1,448 dimensions were buying at 0.7438 unmatched, it was
substantially demographics and identity, not pathology.

**But read the size honestly.** WavLM fell from 0.7438 unmatched to **0.6227** matched.
Roughly *half* of its headroom above chance disappeared when age was equalised — which is
exactly what F1, F3 and F4 predicted between them. The real, non-demographic, non-identity
signal in these embeddings is **AUC ≈ 0.62** — well above chance, far below the ~0.85 the
literature reports on this corpus, and nowhere near clinical usefulness.

### A bug in my own harness, on the way here

The first V1 run reported only WavLM: the cached eGeMAPS covered just the 667-recording
pilot slice, so it could not align to the matched subset. Full-corpus extraction
(28,509 × 88, 0 unreadable) was needed and is now done — via a **resumable** extractor,
after two non-resumable attempts were killed at 74% and 8.5% and discarded everything.

Worse, **that first artifact claimed eGeMAPS had run.** `encoders_run` was populated
from *the cache file existing* rather than from *the arm producing a number*, so a
silently-skipped arm was reported as an executed one. Fixed in both the script and the
artifact, with the reason recorded rather than quietly overwritten. This is the same
failure class as everything in `CLAUDE.md` §18.8: it did not crash, it produced a
confident, well-formed, false field.

**Scope:** two of three registered encoders (HeAR and Whisper-small-enc not extracted);
one corpus of three (COUGHVID excluded per F2; Coswara's classifier is at chance, so it
cannot host this contrast either). `m` kept at the pre-registered 9. The falsifier asks
for ≥2 of 3 corpora, so **V1 is NOT formally closed** — but for the one corpus where the
audio model demonstrably works, the answer is unambiguous.

> Not a medical device. Internal QA pass — independent external review pending.
