# DATA_SPLIT_AUDIT — can these corpora support a speaker-disjoint evaluation claim?

**Auditor role:** adversarial data/leakage auditor (same-model-family agent).
**Date:** 2026-07-26 · **Scope:** `data/interim/{svd,coswara,coughvid}/manifest.csv`
(667 / 610 / 13,535 rows) plus `summary.json` per corpus, `autoresearch_results/F1_demographic_baseline.json`,
`autoresearch_results/bench_svd_egemaps.json`, `PREREGISTRATION.md` §4.
**Method:** every number below was **computed from the manifests by this audit**, on CPU, no model
loads. Nothing is quoted from a card or a paper. Where a number could not be computed it is marked
`[UNVERIFIED]`.

> **Internal QA pass — implementer and critic share a model family; independent external review
> pending.**

---

## Summary verdict — the PASS/FAIL table

| corpus | speaker id real? | speaker-disjoint split **mechanically** possible | supports a speaker-disjoint **evaluation claim** | verdict |
|---|---|---|---|---|
| **SVD** | YES — `speaker_id_provenance = participant` on 667/667 rows | YES — 49 speakers, 0 mixed-label, 13.6 rec/speaker | **NO at evaluation tier** — 49 speakers (29 healthy / 20 pathological) → ~4 positive speakers per test fold; speaker-level AUC CIs are ±0.13 wide | **CONDITIONAL PASS** (screening only) |
| **SVD, demographically-matched variant** (V1/`A3 = speaker_disjoint + demographically_matched`) | YES | YES | **NO** — only **9** healthy/pathological speaker pairs match within ±5 y (18 of 49 speakers survive) | **FAIL** |
| **Coswara** | YES — `participant` on 610/610 | YES — 72 speakers, 0 mixed-label, 8.47 rec/speaker | **NO** — the pre-registered label (`covid_positive vs covid_negative`) has **zero positive rows** in the acquired data; the best available substitute gives **9 positive speakers of 72** | **FAIL** |
| **COUGHVID** | **NO** — `speaker_id_provenance = recording_proxy` on 13,535/13,535 | **NO** — `speaker_id` is the recording UUID; 13,535 "speakers" for 13,535 recordings | **NO** — a speaker-disjoint split is *unverifiable*, not achieved | **HARD FAIL** |

The corpus `summary.json` files already carry `speaker_disjoint_split_possible: true/true/false`.
This audit confirms that flag and finds that it is **necessary but far from sufficient**: SVD and
Coswara pass the mechanical test and still fail the evaluation-claim test, for different reasons.

---

## 1. Speaker-id availability and provenance

| corpus | rows | `speaker_id` present | provenance (all rows) | unique speakers | unique sessions | sessions/speaker |
|---|---|---|---|---|---|---|
| svd | 667 | 667/667 | `participant` (667) | **49** | 49 | 1.00 (min 1, max 1) |
| coswara | 610 | 610/610 | `participant` (610) | **72** | 72 | 1.00 (min 1, max 1) |
| coughvid | 13,535 | 13,535/13,535 | **`recording_proxy` (13,535)** | 13,535 | 13,535 | 1.00 |

`src/voicehealth/embed.py:136-164` (`load_manifest`) raises if `speaker_id` is absent, and
`benchmark.py:61-75` (`assert_speaker_disjoint`) raises before any `.fit()`. Both gates are real and
have no bypass flag. **They do not, and cannot, detect that COUGHVID's `speaker_id` is a fiction** —
a per-recording UUID satisfies every disjointness assertion trivially. The provenance column is the
only signal, and nothing in `benchmark.py` reads it.

**Session structure caveat.** Inside the *acquired interim slices*, session == speaker (1.00
sessions/speaker on all three). That is a property of what was downloaded, not of the corpora.
`F1_demographic_baseline.json` (computed on the full SVD metadata, 2,225 sessions / 1,853 speakers)
records `speakers_with_multiple_sessions: 200`, `max_sessions_per_speaker: 24`. So the
multi-session leakage trap that `FINDINGS.md` F1 correctly warns about is **absent from the 49-speaker
slice the benchmark actually runs on**, and will re-appear the moment the slice is enlarged.

---

## 2. Recordings per speaker, and how much would leak under a recording-level split

| corpus | rec/speaker mean | min | max | distribution | speakers with >1 recording | % recordings leakable |
|---|---|---|---|---|---|---|
| svd | 13.61 | 4 | 14 | 45 speakers x 14, 2 x 13, 1 x 7, 1 x 4 | **49 / 49 (100 %)** | **100.0 %** |
| coswara | 8.47 | 1 | 9 | 65 x 9, 2 x 8, 1 x 4, 1 x 2, 3 x 1 | **69 / 72 (95.8 %)** | **99.5 %** |
| coughvid | 1.00 | 1 | 1 | 13,535 x 1 | 0 | 0.0 % |

**Simulated recording-level 5-fold split** (200 random assignments per corpus, computed by this
audit):

| corpus | speakers spanning >=2 folds (mean) | % of speakers leaking | % of test recordings whose speaker is also in train |
|---|---|---|---|
| svd | **49.0 / 49** | **100.0 %** | **100.0 %** |
| coswara | **68.7 / 72** | **95.5 %** | **99.4 %** |
| coughvid | 0.0 / 13,535 | 0.0 % | 0.0 % |

Read this correctly: on SVD, a naive `train_test_split` puts **every single speaker on both sides**,
and **every** test recording has 13 sibling recordings of the same larynx in train. This is the
strongest possible statement of why the speaker-disjoint assertion is load-bearing — and it is the
number the program should quote, not the 200/1,853 figure from the full metadata.

COUGHVID's 0.0 % is **not** a pass. It is the arithmetic consequence of one recording per
pseudo-speaker: there is nothing to leak *because the grouping variable carries no information*.

---

## 3. Class balance, per corpus and per speaker

### Recording level (raw manifest labels)

| corpus | labels |
|---|---|
| svd | healthy 387 · pathological 280 |
| coswara | healthy 529 · no_resp_illness_exposed 45 · resp_illness_not_identified 36 |
| coughvid | healthy 10,132 · symptomatic 2,683 · COVID-19 720 |

### Speaker level, and the binary task each corpus can actually support

| corpus | binary task used here | n rec | pos rec | neg rec | base rate | **pos speakers** | **neg speakers** | speakers with mixed labels |
|---|---|---|---|---|---|---|---|---|
| svd | pathological vs healthy | 667 | 280 | 387 | 0.420 | **20** | **29** | **0** |
| coswara | (no_resp_illness_exposed + resp_illness_not_identified) vs healthy | 610 | 81 | 529 | 0.133 | **9** | **63** | **0** |
| coughvid | (COVID-19 + symptomatic) vs healthy | 13,535 | 3,403 | 10,132 | 0.251 | 3,403 | 10,132 | 0 |

**Zero mixed-label speakers in all three corpora.** This is good for the split assertion and *bad*
for the science: it means each speaker carries exactly one label, which is precisely the condition
`PREREGISTRATION.md` §4.1 identifies as the mechanism by which a probe can reach high AUC by
memorising speaker-characteristic directions. The pre-registration is right to name this the single
most likely way V2 produces a spurious positive.

**The Coswara finding is a blocker.** `PREREGISTRATION.md` §4 pins Coswara's A2 as
`covid_positive vs covid_negative`, `recovered` excluded, heavy-cough stream only. The acquired
interim manifest contains **no `positive_*` label at all** — the three labels present are
`healthy`, `no_resp_illness_exposed`, `resp_illness_not_identified`. The full Coswara metadata
*does* contain 681 positives (`autoresearch_results/acquisition/coswara_meta_stats.json`:
`positive_mild 426 / positive_moderate 165 / positive_asymp 90`), so this is a shortfall of the
72-participant slice that was downloaded, not of the corpus. **As acquired, the pre-registered
Coswara replication cell cannot be run**, and the substitute task has 9 positive speakers.

---

## 4. Age / sex distribution by class — the F1 confound, measured on the data the benchmark uses

### Age

| corpus | class | n | mean | sd | median | min | max |
|---|---|---|---|---|---|---|---|
| svd | pathological | 280 | **48.85** | 22.27 | 49 | 6 | 89 |
| svd | healthy | 387 | **30.68** | 16.04 | 23 | 19 | 68 |
| coswara | positive | 81 | 31.00 | 8.41 | 26 | 23 | 49 |
| coswara | healthy | 529 | 34.34 | 11.84 | 30 | 19 | 72 |
| coughvid | positive | 3,256 | 34.23 | 13.01 | 33 | 1 | 97 |
| coughvid | healthy | 9,631 | 37.09 | 14.29 | 35 | 1 | 99 |

Age missingness: svd 0.0 %, coswara 0.0 %, coughvid 4.8 %.

### Sex

| corpus | class | M | F | unknown |
|---|---|---|---|---|
| svd | pathological | 210 | 70 | 0 |
| svd | healthy | 189 | 198 | 0 |
| coswara | positive | 63 | 18 | 0 |
| coswara | healthy | 421 | 108 | 0 |
| coughvid | positive | 1,927 | 1,451 | 25 |
| coughvid | healthy | 6,712 | 3,383 | 37 |

### Measured confound AUCs (univariate, computed by this audit)

| corpus | age (rec) | age (speaker) | sex (rec) | sex (speaker) | duration (rec) | duration (speaker) |
|---|---|---|---|---|---|---|
| **svd** | **0.7362** | **0.7414** | 0.6308 | 0.6336 | 0.4369 | 0.4534 |
| coswara | 0.4135 | 0.4215 | 0.4910 | 0.4921 | 0.4044 | 0.3157 |
| coughvid | 0.4468 | 0.4468 | 0.4519 | 0.4519 | 0.5076 | 0.5076 |

**A material discrepancy with FINDINGS.md F1.** F1 headlines "on SVD, patient AGE alone reaches
ROC-AUC **0.871**", and `src/voicehealth/benchmark.py:6` repeats it in the module docstring as the
bar the harness exists to enforce. That 0.871 is measured on the **full SVD session metadata**
(2,225 sessions / 1,853 speakers, `data/raw/svd_meta/voice_data.csv`,
`scripts/audit_demographic_baseline.py:59`). On the **49-speaker interim slice the benchmark
actually runs**, age-only AUC is **0.7362 (recording) / 0.7414 (speaker)** — 0.13 AUC lower. The
executed benchmark's own fitted `confound::age_only` lands at **0.7027 (rec) / 0.7086 (spk)**
(`bench_svd_egemaps.json`), consistent with this audit's univariate figure and **not** with 0.871.

F1's caveat section is careful about UAR-vs-AUC and about not accusing anyone; it is **silent on
the fact that the two populations differ**. Any sentence of the form "the audio model must clear
0.877" is, on the current data, quoting a bar from a different sample of 1,853 speakers than the 49
it is applied to. This should be stated wherever 0.871/0.877 appears.

**Sex is a live confound on SVD too** (0.63 AUC, driven by pathological 75 % M vs healthy 49 % M)
and is not currently caveated anywhere.

---

## 5. Per-corpus PASS/FAIL, with reasons

### SVD — CONDITIONAL PASS (screening tier only)

- **PASS** on speaker-id integrity: `participant` provenance on 667/667, 49 real speakers,
  0 mixed-label speakers, 13 duplicate-SHA256 groups (30 files) that this audit confirms are
  **all within-speaker and within-label** (`dup_groups_crossing_speakers: 0`,
  `dup_groups_crossing_labels: 0`) — so the duplicates cannot cross a speaker-disjoint fold boundary.
- **FAIL** on evaluation-tier n. 49 speakers / 20 positive. At 5 folds a test partition holds ~10
  speakers, ~4 of them positive. The executed run's own speaker-level bootstrap CIs are
  [0.663, 0.925] for the best head — a width of 0.26 AUC. `PREREGISTRATION.md` §11 abandonment
  condition 3 fires when the 2-sigma seed band on `D(k)` exceeds 0.10 AUC; the observed
  per-repeat sd of 0.0235 for `gbt` is the *re-partition* spread of the same 49 speakers, not the
  sampling spread of the estimate, so it understates the real band by roughly an order of magnitude.
- **FAIL** on the demographically-matched variant that V1 and V6 both pin. Greedy 1:1 speaker
  matching within ±5 years yields **9 pairs = 18 of 49 speakers**. A matched SVD cell is a
  9-vs-9-speaker experiment. It should be declared unrunnable rather than run and reported.
- Recording-level splitting would leak **100 % of speakers and 100 % of test recordings**.

### Coswara — FAIL

- **PASS** on speaker-id integrity (`participant`, 610/610; 72 speakers; 0 mixed-label;
  0 duplicate SHA256).
- **FAIL** on label availability: the pre-registered `covid_positive vs covid_negative` task has
  **0 positive rows** in the acquired slice.
- **FAIL** on evaluation-tier n under any substitute: **9 positive speakers of 72**, base rate
  0.133. A 5-fold speaker-disjoint partition puts ~1.8 positive speakers in each test fold;
  `stratified_group_folds` (`benchmark.py:109`) will silently `continue` past folds whose train
  side goes single-class, and the resulting all-NaN predictions are converted to 0.0 by
  `benchmark.py:497` (see `IMPL_CRITIC.md` finding 2).
- The measured confound AUCs are all **below 0.5** here, so a Coswara "margin above the confound
  bar" is trivially satisfied and carries no information — the bar is floored at 0.5 by
  `COMPOSITE.md` §1 for exactly this reason, and that flooring should be applied in code.

### COUGHVID — HARD FAIL

The reason, stated plainly: **`speaker_id` is manufactured from the recording UUID.**
`speaker_id_provenance = recording_proxy` on all 13,535 rows;
`speaker_id == session_id == "coughvid_" + recording uuid`; exactly 1.00 recordings per "speaker".

Consequences, each of which is independently disqualifying:

1. **The grouping variable carries zero grouping information.** `GroupKFold` on it is arithmetically
   identical to a recording-level random split. `assert_speaker_disjoint` passes vacuously — it is
   asserting that no UUID equals another UUID.
2. **Repeat uploaders are undetectable.** COUGHVID is an open web-collection; the public metadata
   ships no participant identifier, so a person who submitted several coughs appears as several
   independent "speakers" in both train and test. The magnitude of that contamination is
   **`[UNVERIFIED]` and unverifiable from the released data** — which is the point: an unbounded,
   unmeasurable leak cannot be caveated away.
3. **A "speaker-disjoint" claim on COUGHVID would be false as stated**, not merely weak. Any
   COUGHVID number in this program must be labelled `recording-level split; speaker structure
   unknown`, and may never be described as speaker-disjoint.
4. The label is self-reported and present on only 60 % of the archive
   (`data/cards/CARD_coughvid.md` §3: `status` on 20,664 / 34,434 rows), so the 13,535-row interim
   is already a `cough_detected >= 0.8` + label-present subselection whose selection effect on the
   speaker population is unmeasured.

`PREREGISTRATION.md` §4 already excludes COUGHVID from V2 for exactly this reason ("no speaker
identifiers, subspace is unestimable"). **`IDEA_TABLE.md` V1, V3, V4, V5, V6 and V7 all still list
COUGHVID as a dataset** and all six pin `A3 = speaker_disjoint`. That is an unresolved contradiction
between the registry and the data, and it is the registry that must change.

---

## 6. What would have to be true for these corpora to support the claims

| requirement | current state | fix |
|---|---|---|
| SVD evaluation-tier n | 49 speakers | enlarge the interim slice from the 1,853-speaker corpus; re-run the multi-session leakage check (200 speakers have >1 session there) |
| SVD demographic matching | 9 matchable pairs | either enlarge, or drop `demographically_matched` from V1/V6 falsifiers and report age-stratified AUC instead |
| Coswara pre-registered label | 0 positives acquired | re-fetch the participant set that contains `positive_*` (681 available per the metadata census) |
| Coswara evaluation-tier n | 9 positive speakers | same |
| COUGHVID speaker structure | proxy ids only | none available from the released data — relabel every COUGHVID claim as recording-level, or drop the corpus from any speaker-disjoint hypothesis |

---

## 7. Reproduce

Every number in this document comes from `data/interim/*/manifest.csv` and was produced by a
standalone CPU script (manifest census, per-speaker histograms, univariate rank-based AUCs, and a
200-trial recording-level split simulation at K=5). The confound AUCs are Mann-Whitney rank AUCs
with tie correction; the fitted comparisons quoted from `bench_svd_egemaps.json` are the harness's
own 5-fold x 10-repeat speaker-disjoint numbers.

---

*Internal QA pass — implementer and critic share a model family; independent external review
pending. This audit states what the data can and cannot support; it makes no clinical claim and
does not assert that any published result is wrong.*

---

> **Internal QA pass — implementer and critic share a model family; independent external review pending.**
