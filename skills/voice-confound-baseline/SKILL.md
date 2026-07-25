---
name: voice-confound-baseline
description: >
  Use BEFORE any voice model claim, and before the audio is even loaded. Computes
  the strongest trivial-confound baseline on the same corpus, same split policy
  and same head, so the claim can be stated as the MARGIN ABOVE it rather than as
  a raw AUC. Covers the pinned nine-member battery (age, sex, age+sex, duration,
  RMS intensity, SNR, silence-only, device/site, metadata-only) plus corpus-of-
  origin and language. The motivating measurement: on SVD, AGE ALONE reaches
  ROC-AUC 0.8709 without hearing a single sample of audio.
---

# Skill — voice-confound-baseline

The constitution's rule, in one line (`CLAUDE.md` §4.3.2):

> Before claiming a model detects pathology, show that device / duration / age /
> sex alone do **not** achieve it. Claim only the margin **above** the strongest
> confound baseline.

This skill is how that rule is executed. It is cheap, it runs on CPU in seconds,
and it must run **first** — a confound baseline computed after the audio result
is a rationalisation, not a control.

---

## When to use

- Before the first audio experiment on any corpus (it is a rung-0/1 activity).
- Whenever a new corpus is onboarded — the battery is part of the data card.
- Before writing any sentence containing "detects", "predicts", or "identifies"
  a disease from voice.
- When a published claim is being audited: the paper's number and our confound
  bar go in the same table ([voice-claim-audit](../voice-claim-audit/SKILL.md)).
- When the composite is computed: `AUC_conf_max` is a **required** term, and a
  missing term makes the composite `null`, never zero (`COMPOSITE.md` §4).

---

## 1. The motivating measurement — SVD, no audio, AUC 0.871

Finding F1 (`FINDINGS.md`), reproducible on CPU in seconds. Artifact:
`data/raw/svd_meta/voice_data.csv` (md5 `2ee9852a…`, 167,457 B) →
`autoresearch_results/F1_demographic_baseline.json`, produced by
`scripts/audit_demographic_baseline.py`.

| predictor (no audio, no features, no model of speech) | ROC-AUC |
|---|---|
| **age alone** | **0.8709** |
| sex alone | 0.5172 |
| **age + sex, logistic, speaker-disjoint 5-fold `GroupKFold`** | **0.8768** |

n = 2,225 sessions (1,356 pathological / 869 healthy), 1,853 unique speakers.

**The cause is a recruitment asymmetry, not a subtle statistical artifact:**

| class | mean age | sd |
|---|---|---|
| healthy | 28.3 | 11.6 |
| pathological | 51.0 | 15.8 |

Healthy speakers are young volunteers; pathological speakers are older clinic
patients. The classes differ by ~23 years.

**Why it binds this program.** The published SVD benchmark we intend to audit
reports **UAR 85.22** (F 85.61 / M 84.69; Vrba et al., arXiv:2410.10537). A
model that hears nothing reaches AUC ≈ 0.877 on the same corpus. Any audio model
on SVD must therefore demonstrate a **margin above the demographic bar** to
support the claim that it detects laryngeal pathology rather than patient age.

**Three things F1 does not claim** — repeat them whenever it is cited:

1. It does **not** show any published result is wrong. UAR and ROC-AUC are
   different metrics and are not like-for-like; the comparison is indicative. A
   proper audit recomputes the published pipeline's own metric on matched splits.
2. Several published pipelines may already age-match or report demographic
   baselines. The audit question is **whether the margin above the bar is
   reported at all** — not whether anyone was careless.
3. A metadata-only baseline says nothing about whether voice carries pathology
   signal. It very likely does. The claim is strictly about **attribution**.

---

## 2. The pinned battery (part of the composite fingerprint)

`AUC_conf_max = max` over every member computable on the corpus
(`COMPOSITE.md` §3, inside fingerprint `37e745ed9b0b`):

| member | feature set | notes |
|---|---|---|
| `age_only` | patient age | SVD: derive from `Geburtsdatum` + `AufnahmeDatum` |
| `sex_only` | sex | weak alone (0.5172 on SVD) but interacts |
| `age_sex_only` | both | the SVD champion confound (0.8768) |
| `duration_only` | recording length in seconds | recording-protocol shortcut |
| `intensity_rms_only` | mean RMS level | recording-protocol shortcut |
| `snr_only` | estimated SNR | acquisition-chain proxy |
| `silence_only` | features from **silent segments only** | the Clever-Hans probe: near-100 % Alzheimer's detection from silence alone in the Pitt corpus (arXiv:2406.07410) |
| `device_or_site_only` | device / site / recording-centre metadata | `NOT_APPLICABLE(single-device corpus)` where it does not exist |
| `metadata_only` | every non-audio field jointly | the ceiling of "no audio required" |

**Two more that the battery does not name but the domain requires:**

- **`corpus_of_origin`** — for any pooled or cross-corpus experiment, train a
  probe to predict *which corpus a recording came from*. If that is near-perfect
  (it usually is), a pooled disease probe can route on corpus identity, and a
  cross-corpus number is the only honest one. Cross-corpus COVID AUC collapses to
  **0.43–0.68** (some configurations worse than chance) while within-corpus sits
  at 0.82–0.93 (arXiv:2511.14939).
- **`language_or_accent`** — PC-GITA and NeuroVoz are Spanish, PROCESS-2 British
  English, SVD German, HPP-Voice Hebrew. A cross-lingual result reported as if it
  were in-language is a confound claim, not a disease claim
  (`corpus/SURVEY_datasets.md` §3.6).

**Shrinking the battery is the one attack the composite arithmetic cannot stop**
(`COMPOSITE.md` §5, D5): `∂composite/∂AUC_conf_max = −1`, so every additional
baseline can only lower your score. It is defended by the fingerprint, by the
required `NOT_APPLICABLE(reason)` field, and by the fact that this program's
deliverable is the verdict, not a high composite. Never silently drop a member.

---

## 3. The protocol — same everything

A confound baseline is a **single-axis perturbation of the champion on A5**
(`AXIS_TAXONOMY.md` §A5, §A12). That is what makes it mechanically honest:

- same split policy (`A3 = speaker_disjoint`, sex-stratified),
- same fit scope (`A4 = fit_per_fold`),
- same head (`A7`, same regularisation grid, same inner CV),
- same aggregation unit (`A11 = speaker_level(mean_prob)`),
- same seeds / same partitions, so every comparison is **paired**.

Only the feature matrix changes. If you use a different splitter or a different
head for the baseline, you have not measured a bar — you have measured two
pipelines.

**The margin, and how to state it:**

```
M = AUC_honest − max(0.5, AUC_conf_max)
```

Floored at 0.5 so a below-chance confound cannot manufacture margin. `M`, not
AUC, is the primary efficacy term of the whole program. If `primary_efficacy =
AUC`, Coppock et al.'s 0.846 cough-COVID classifier would top the table and its
honest 0.619 would be a footnote — the exact failure this program exists to
expose (`COMPOSITE.md` §1).

---

## 4. Working implementation

`scripts/audit_demographic_baseline.py` is the reference. It is small on purpose;
read it before writing a new one. Its shape:

```python
auc_age = roc_auc_score(y, age)                    # single-feature: AUC directly
auc_sex = roc_auc_score(y, sex)

X = np.c_[age, sex]                                # multi-feature: CV'd probe
proba = cross_val_predict(
    LogisticRegression(max_iter=1000), X, y,
    cv=GroupKFold(5), groups=groups, method="predict_proba",
)[:, 1]
auc_both = roc_auc_score(y, proba)
```

Note the two idioms and when each applies:

- **Single monotone feature** (age, duration, RMS): `roc_auc_score(y, feature)`
  needs no fit at all, therefore cannot leak. Report the raw AUC, and flip the
  sign convention if it lands below 0.5 (report `max(auc, 1-auc)` explicitly
  labelled — a confound that predicts *inversely* is still a confound).
- **Multi-feature** (age+sex, metadata_only, silence_only): a fitted probe, so
  it needs the **speaker-disjoint CV**, or the bar itself is leakage-inflated.

Extending the script to a new corpus means adding a `load_<corpus>()` and a
`--dataset` choice; the audit body is corpus-independent. Every run writes a JSON
artifact with the input file's md5 (R1) — a confound number without an artifact
pointer is deleted, not debated.

---

## 5. Worked example — the sentence you are allowed to write

Suppose a frozen WavLM probe reaches `AUC_honest = 0.91` on SVD under
speaker-disjoint, speaker-level evaluation.

**Not allowed:**

> "Our probe detects laryngeal pathology from voice at AUC 0.91."

**Allowed:**

> "Under a speaker-disjoint, sex-stratified protocol with all statistics fitted
> per fold, a frozen WavLM-base+ probe reaches speaker-level ROC-AUC 0.91
> (95 % CI …, n = 10 paired partitions). The strongest member of the pinned
> confound battery on this corpus is age+sex at ROC-AUC 0.8768
> (`autoresearch_results/F1_demographic_baseline.json`), giving an honest margin
> of **M = 0.033**. The audio contribution above demographics is therefore small
> and is the quantity we report; the raw 0.91 is not."

If instead the probe reaches 0.86, the margin is **negative** and the honest
sentence is that the audio model does not clear the demographic bar on this
corpus. That is a publishable negative result (R8), reported in the same table
with the same detail.

---

## 6. What a confound baseline does NOT fix

- **It is not a substitute for a speaker-disjoint split.** Age and identity are
  different leaks; clearing the age bar under a leaky split proves nothing. Run
  [voice-speaker-disjoint-splits](../voice-speaker-disjoint-splits/SKILL.md) first.
- **It does not remove the confound from the model.** Removal is the A9 axis
  (matching, residualisation, subspace projection) and needs its own controls.
- **"Balanced" is not "deconfounded."** ADReSS-style age/sex balancing removes
  exactly two variables; recording-session, task-administration and transcription
  effects survive it (`corpus/SURVEY_datasets.md` §3.8).
- **It does not address label provenance.** A high AUC on a self-report corpus
  may be measuring self-report behaviour (§3.9).

---

## 7. Anti-patterns

| anti-pattern | consequence | do instead |
|---|---|---|
| Running the battery *after* the audio result | the bar gets read as an excuse, and the temptation to shrink it is live | run it first; it is a rung-0/1 activity and costs seconds |
| Reporting raw AUC as the headline | Coppock's 0.846 tops your table; its honest 0.619 is a footnote | headline the margin `M`; report AUC alongside it |
| Fitting the age+sex probe with `train_test_split` | the *bar* is leakage-inflated, which flatters the audio model by lowering the bar | speaker-disjoint CV for every fitted baseline |
| Omitting `device_or_site_only` because the corpus is single-device | a silently dropped member makes the composite `null` | record `NOT_APPLICABLE(single-device corpus)` explicitly |
| Skipping `silence_only` as "obviously chance" | near-100 % AD detection from silence alone is measured, not hypothetical (arXiv:2406.07410) | run it; it is the cheapest Clever-Hans probe available |
| Pooling corpora without a `corpus_of_origin` probe | the disease probe routes on corpus identity | run the corpus-id probe; report cross-corpus AUC, not pooled |
| Reporting `max(auc, 1-auc)` silently | hides an inverse confound behind a symmetric statistic | report the raw value and the flip, both labelled |
| Comparing a baseline computed on one split against a model computed on another | not a bar, just two pipelines | identical A3/A4/A7/A11 and identical partitions; paired |

---

## Definition of done

- [ ] Every computable battery member has a number, from an artifact, with an
      md5/SHA pointer to the input file.
- [ ] Non-computable members carry `NOT_APPLICABLE(reason)` — never a bare gap.
- [ ] `corpus_of_origin` probed for any pooled/multi-corpus row; language stated.
- [ ] Every baseline used the champion's A3/A4/A7/A11 and the **same partitions**.
- [ ] `AUC_conf_max` recorded, and the claim is stated as `M = AUC_honest −
      max(0.5, AUC_conf_max)`.
- [ ] No sentence in the write-up states a raw AUC without the margin beside it.
- [ ] A negative margin is reported as prominently as a positive one (R8).

---

## Cross-references

- Working implementation: `scripts/audit_demographic_baseline.py`
- The finding this skill exists to generalise: `FINDINGS.md` F1
- Composite terms `M`, `AUC_conf_max`, `lambda_leak`: `../../COMPOSITE.md` §1–§3
- Confound-only feature sets as A5 values / controls as A12: `../../AXIS_TAXONOMY.md`
- Splits (run first): [`../voice-speaker-disjoint-splits/SKILL.md`](../voice-speaker-disjoint-splits/SKILL.md)
- Subgroup + calibration reporting: [`../voice-calibration-and-subgroups/SKILL.md`](../voice-calibration-and-subgroups/SKILL.md)
- Negative-control discipline (label shuffle): [`../../meta-skills/autoresearch-shuffle-test/SKILL.md`](../../meta-skills/autoresearch-shuffle-test/SKILL.md)
- Field evidence: Coppock et al., *Nature Machine Intelligence* 2024,
  arXiv:2212.08570 (AUC 0.846 → 0.619 after confounder matching);
  `corpus/SURVEY_datasets.md` §3.2, §3.3, §3.5, §3.6
