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
