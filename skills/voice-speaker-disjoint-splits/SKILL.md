---
name: voice-speaker-disjoint-splits
description: >
  Use before EVERY fit, probe, scaler, or subspace estimate on any voice corpus.
  Voice corpora ship multiple recordings per speaker, so a recording-level split
  leaks speaker identity and the model learns WHO rather than WHAT. Defines the
  split unit, the GroupKFold recipe, the pre-fit disjointness assertion that the
  runner cannot bypass, sex/age stratification, and the controlled-overlap(rho)
  design that makes leakage measurable instead of merely asserted. This is the
  A3 axis of AXIS_TAXONOMY.md and the program's primary audit dial.
---

# Skill — voice-speaker-disjoint-splits

This is the voice-health instantiation of
[meta-skills/autoresearch-data-split-audit/SKILL.md](../../meta-skills/autoresearch-data-split-audit/SKILL.md).
Read that file for the general audit-gate machinery; this file supplies the
domain facts, the split unit per corpus, and the assertion code.

**It is the most important skill in the pack.** Every other voice skill assumes
its gate has already passed.

---

## When to use

- Before the **first** fit on a new corpus — and before every subsequent one.
- When writing any loader, `cross_val_*` call, scaler, LDA/PCA basis, calibrator,
  or subspace estimator (all of these are fits; all of them leak).
- When reproducing a published number: the paper's split policy is the thing
  being audited, so it must be identified and reproduced *before* it is replaced
  (see [voice-claim-audit](../voice-claim-audit/SKILL.md)).
- When a result looks too good. A voice AUC above ~0.95 on a clinical label is a
  leakage hypothesis until the disjointness assertion is shown in the artifact.

---

## 1. The motivating measurement — SVD leaks under the obvious key

Two independent manifests in this repo were measured, and **both** show the trap.
Neither number is quoted from a paper (R1/R2).

**Manifest A — `data/raw/svd_meta/voice_data.csv`** (md5 `2ee9852a…`, 167,457 B;
producer `scripts/audit_demographic_baseline.py`, artifact
`autoresearch_results/F1_demographic_baseline.json`):

| quantity | value |
|---|---|
| sessions | 2,225 (1,356 pathological / 869 healthy) |
| unique speakers (`SprecherID`) | 1,853 |
| **speakers with > 1 session** | **200** |
| max sessions for one speaker | **24** |
| mean sessions per speaker | 1.20 |

**Manifest B — the 72-archive `overview.csv` inventory**
(producer `scripts/analyze_svd_inventory.py`, artifact
`autoresearch_results/acquisition/svd_inventory_analysis.json`):

| quantity | value |
|---|---|
| speakers holding multiple sessions | **378, covering 1,020 sessions** |
| **share of rows at risk if you group by the zip folder name** | **40.88 %** |
| speakers spanning multiple pathology archives | 306 |
| **speakers appearing as BOTH healthy and pathological** | **21** |

**The trap is specific and worth memorising: the obvious key is the wrong one.**
`AufnahmeID` is the *session* id and is the zip folder name — it is what any
directory-walking loader will naturally group by. `SprecherID` is the *speaker*
id and exists only inside `overview.csv`. Grouping on the folder name looks like
a group split, passes a naive "did you use GroupKFold?" review, and still leaks
40.88 % of rows.

The 21 speakers who appear as both healthy and pathological are worse than
leakage: under a recording-level split the same voice carries both labels, so
part of the task is unlearnable and part is memorisable.

---

## 2. The split unit, per corpus (pinned)

| corpus | split unit | status | consequence |
|---|---|---|---|
| **SVD** | `SprecherID` (from `overview.csv` / `voice_data.csv`) — **never** `AufnahmeID`, never the folder name | **SUPPORTED** | primary evaluation-tier target |
| **Coswara** | `id` (unique per row, 2,746/2,746) | **PARTIAL** — `rU` marks **63 self-declared returning users** who re-submitted under a new `id` with **no linking field**; 680 further rows leave `rU` blank | residual leakage ≤ 2.3 % of rows, irreducible from shipped metadata. State the bound in every Coswara row. |
| **COUGHVID** | *none exists* — 34,434 rows, 34,434 unique `uuid`s, **no participant identifier of any kind** | **IMPOSSIBLE** | **cannot support an evaluation-tier claim.** Use as OOD probe / negative control only. Every published COUGHVID number is an upper bound of unknown tightness. |
| **PROCESS-2** | `PROCESS-2_rec__NNN/` directory name (expected; confirm on receipt) | pending DUA | screening-tier only (n < 500/class) |
| **Bridge2AI-Voice** | participant id (expected) | pending credentialing | feature-tier only until DACO approves raw audio |

A corpus with no speaker id does not get a footnote — it gets a demotion. Write
that demotion into the data card ([voice-dataset-onboarding](../voice-dataset-onboarding/SKILL.md))
at onboarding time, not at claim time.

---

## 3. The recipe

```python
import numpy as np
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

# groups MUST be the speaker id, aligned row-for-row with X and y.
# For SVD: groups = df["SprecherID"].values   (NOT AufnahmeID, NOT the folder name)
cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
for tr, te in cv.split(X, y, groups=groups):
    assert_speaker_disjoint(groups, tr, te)     # §4 — before ANY fit
    scaler = StandardScaler().fit(X[tr])        # fit_per_fold (A4), never fit_on_all
    ...
```

**Rules that come with it:**

1. **`groups` is passed to every splitter, every time.** `train_test_split` has
   no `groups` parameter — that is why it is banned outright on this program's
   corpora, not merely discouraged.
2. **Stratify on label AND sex.** SVD's own reference number is reported per sex
   (UAR 85.61 F / 84.69 M, arXiv:2410.10537) precisely because sex-pooled numbers
   are unstable; the EarlyPD benchmark balances age and sex *within* each fold
   (Zhong, Tejedor-Garcia, Truong, Maas, ten Bosch & Bloem, Interspeech 2026,
   arXiv:2605.14066 — 5 folds, each test fold holding 6 early-PD + 6 HC speakers).
   `StratifiedGroupKFold` stratifies on one label only; for sex-stratification,
   stratify on the interaction `label * sex` or draw the partition manually and
   assert the per-fold sex balance.
3. **Everything is fitted per fold** (`A4 = fit_per_fold`): scaler, PCA basis,
   LDA/subspace, class-balancer, calibrator, and the head's hyperparameter search
   (inner CV *inside* the training partition). Scaling fitted before splitting
   moves SVD by −0.14 to +0.14 pp but VOICED by **−8.3 to +7.8 pp** over 1,000
   repetitions per configuration (*Applied Soft Computing*, `S1568494626007970`),
   so "it's only a small effect" is not defensible on an unmeasured corpus.
4. **Report speaker-level n alongside recording-level n**, always
   (`corpus/SURVEY_datasets.md` §3.1). n = 2,225 sessions is not n = 2,225.
5. **Aggregate at speaker level for headline numbers** (`A11 =
   speaker_level(mean_prob)`). A recording-level metric counts a 24-session
   speaker 24 times.

---

## 4. The assertion — copy this verbatim

It runs **before every fit**, not once per experiment. There is no bypass flag.

```python
def assert_speaker_disjoint(groups, train_idx, test_idx, *, name="split"):
    """Hard gate. Raises before any estimator sees data.

    groups : array of speaker ids, aligned row-for-row with X and y.
    """
    import numpy as np
    g = np.asarray(groups)
    tr, te = set(g[train_idx].tolist()), set(g[test_idx].tolist())
    overlap = tr & te
    if overlap:
        raise AssertionError(
            f"{name}: SPEAKER LEAKAGE — {len(overlap)} speakers in both partitions "
            f"(e.g. {sorted(map(str, overlap))[:5]}). "
            f"train={len(tr)} spk / {len(train_idx)} rows, "
            f"test={len(te)} spk / {len(test_idx)} rows."
        )
    if len(te) < 8:
        raise AssertionError(f"{name}: only {len(te)} test speakers — below the floor.")
    return {
        "n_train_speakers": len(tr), "n_test_speakers": len(te),
        "n_train_rows": int(len(train_idx)), "n_test_rows": int(len(test_idx)),
        "speaker_overlap": 0,
    }
```

The returned dict is **written into the run artifact** for every fold. R1: a
disjointness claim with no artifact is deleted, not debated. A reviewer must be
able to read `speaker_overlap: 0` out of the JSON without rerunning anything.

**Also assert the label-consistency check on SVD**, because 21 speakers carry
both labels in the inventory:

```python
bad = df.groupby("SprecherID")["healthy"].nunique()
assert (bad <= 1).all(), f"{(bad > 1).sum()} speakers carry BOTH labels — resolve before fitting"
```

Resolution is a **pre-registered protocol decision** (drop them, or pin one
session per speaker), never a silent filter chosen after seeing the AUC.

---

## 5. `controlled_overlap(rho)` — make leakage measurable, not asserted

The leaky reference is not a strawman to be avoided; it is a **required
measurement**. `AUC_leaky − AUC_honest` is the protocol-inflation term priced at
`lambda_leak = 1.00` in `COMPOSITE.md`, and it is a ledger row in its own right.

The correct design is Yeh et al.'s: vary the fraction rho of test speakers also
seen in training **while holding training-set size constant** (Yeh, Sun,
Mahapatra, Chandra, Mower Provost & Sisman, 2026, *Who is Speaking or Who is
Depressed? A Controlled Study of Speaker Leakage in Speech-Based Depression
Detection*, arXiv:2604.14354). Without the size control, the comparison confounds
leakage with training-set size and measures nothing.

Sweep `rho ∈ {0.0, 0.25, 0.5, 0.75, 1.0}` at fixed `n_train_rows`. `rho = 0` is
the honest protocol; `rho = 1` approximates `A3 = random_recording`. Their
finding sets the expectation: accuracy drops sharply on unseen speakers, and a
DANN **fails to close the gap** — identity reliance is "a property of current
speech representations rather than a model-specific limitation."

---

## 6. Worked example — the SVD gate, end to end

```python
df = pd.read_csv("data/raw/svd_meta/voice_data.csv")
df["healthy"] = df["Pathologien"].isna() & df["Diagnose"].isna()
groups = df["SprecherID"].values           # THE split unit
y      = (~df["healthy"]).astype(int).values
sex    = (df["Geschlecht"] == "w").astype(int).values

# 1. inventory the leakage exposure and WRITE IT to the artifact
per_spk = df.groupby("SprecherID").size()
meta = {"n_rows": len(df), "n_speakers": df.SprecherID.nunique(),
        "speakers_multi_session": int((per_spk > 1).sum()),
        "max_sessions_per_speaker": int(per_spk.max())}
#    -> expect 2225 / 1853 / 200 / 24 on this manifest

# 2. speaker-disjoint, sex-stratified partition
strat = y * 2 + sex                        # label x sex interaction
cv = StratifiedGroupKFold(5, shuffle=True, random_state=0)

# 3. assert BEFORE every fit; log the returned dict per fold
for k, (tr, te) in enumerate(cv.split(df, strat, groups=groups)):
    meta[f"fold{k}"] = assert_speaker_disjoint(groups, tr, te, name=f"svd/fold{k}")
```

Note what the audio path adds: SVD ships **Kay Elemetrics `.nsp`**, and
`overview_healthy.csv` lists 869 sessions while `healthy.zip` ships 687 folders —
**182 rows have no audio**. Any loader must **inner-join** the manifest to the
files on disk, and the join must happen *before* the split, or the fold sizes in
the artifact will not match the fold sizes that were fitted.

---

## 7. Anti-patterns

| anti-pattern | consequence | do instead |
|---|---|---|
| `train_test_split(X, y)` on recordings | 200 SVD speakers (max 24 sessions) straddle the split; AUC measures identity | `StratifiedGroupKFold` on `SprecherID`, assertion before every fit |
| `GroupKFold` on the **session/folder** id (`AufnahmeID`) | looks correct, passes casual review, still leaks **40.88 %** of SVD rows | group on `SprecherID` from `overview.csv`; assert the key name in the config |
| Asserting disjointness once, then reusing the folds across conditions without re-asserting | a later filter/dropna silently re-indexes and breaks alignment | assert inside the fold loop, every condition, every fold |
| Fitting the scaler / PCA / calibrator on all data "because it's unsupervised" | −8.3 to +7.8 pp on VOICED; leakage can *degrade* as well as inflate | `fit_per_fold` for every fitted object, including the calibrator |
| Reporting n = number of recordings | inflates apparent power; one easy speaker dominates | report speaker-level n **and** recording-level n; aggregate at speaker level |
| Treating COUGHVID's AUC ~0.93 as a target to beat | there is no speaker id, so no honest number exists to beat | demote COUGHVID to OOD / negative control; say why in the card |
| Comparing leaky-vs-honest without holding training size fixed | measures training-set size, not leakage | `controlled_overlap(rho)` at fixed `n_train_rows` (arXiv:2604.14354) |
| Dropping the 21 both-label SVD speakers after seeing the AUC | HARKing; a post-hoc filter chosen for its effect | pre-register the resolution in `PREREGISTRATION.md` before the first fit |

---

## Definition of done

- [ ] The split unit is named explicitly in the config, and it is a **speaker**
      id (not a session, folder, file, or uuid).
- [ ] `assert_speaker_disjoint` runs before every fit; its returned dict is in
      the run artifact for every fold.
- [ ] Label-consistency per speaker asserted (SVD: the 21 dual-label speakers
      resolved by a pre-registered rule).
- [ ] Folds are stratified on label **and** sex; per-fold sex balance logged.
- [ ] `A4 = fit_per_fold` for scaler, basis, subspace, resampler, calibrator, and
      the inner hyperparameter search.
- [ ] Speaker-level n **and** recording-level n reported; headline metrics
      aggregated at `speaker_level(mean_prob)`.
- [ ] `AUC_leaky` measured under the paper's own looser protocol and logged as
      its own ledger row (it is a required `COMPOSITE.md` term at rung 3).
- [ ] For Coswara, the ≤ 2.3 % residual-leakage bound is stated in the row.

---

## Cross-references

- Meta-process split-audit gate: [`../../meta-skills/autoresearch-data-split-audit/SKILL.md`](../../meta-skills/autoresearch-data-split-audit/SKILL.md)
- Loader-contract gate (shape/dtype/alignment): [`../../meta-skills/autoresearch-data-contract-validator/SKILL.md`](../../meta-skills/autoresearch-data-contract-validator/SKILL.md)
- The confound bar that a disjoint split does **not** remove: [`../voice-confound-baseline/SKILL.md`](../voice-confound-baseline/SKILL.md)
- Onboarding a corpus and recording its split verdict: [`../voice-dataset-onboarding/SKILL.md`](../voice-dataset-onboarding/SKILL.md)
- Re-testing a published claim under this split: [`../voice-claim-audit/SKILL.md`](../voice-claim-audit/SKILL.md)
- Axis definition (A3, and the A3×A4 / A3×A11 couplings): `../../AXIS_TAXONOMY.md`
- Measured artifacts: `autoresearch_results/F1_demographic_baseline.json`,
  `autoresearch_results/acquisition/svd_inventory_analysis.json`
- Working implementation of the speaker-disjoint CV pattern:
  `scripts/audit_demographic_baseline.py`
