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
