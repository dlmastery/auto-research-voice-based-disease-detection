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
