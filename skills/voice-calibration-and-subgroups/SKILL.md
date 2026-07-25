---
name: voice-calibration-and-subgroups
description: >
  Use whenever a voice-health result is reported — clinical usability is a
  probability question, not a ranking question. Covers reliability curves, ECE
  (15 equal-mass bins, raw AND temperature-scaled, calibrator fitted per fold),
  Brier decomposition, cross-corpus calibration as a candidate shift detector,
  and worst-subgroup performance by sex / age band / language / site. A model
  that works only for one subgroup is a FINDING, not a footnote.
---

# Skill — voice-calibration-and-subgroups

Two constitutional requirements meet in this skill:

> **Calibration** — report reliability, not just AUC. Clinical usability is a
> probability question. (`CLAUDE.md` §4.3.5)
>
> **Subgroups** — subgroup performance is reported whenever labels permit; a
> model that works only for one demographic is a **finding, not a footnote**.
> (`CLAUDE.md` §7)

Both are priced in the composite: `lambda_cal = 0.50`, `lambda_sub = 0.75`. Both
are **required terms** at rung 3 — and a missing required term makes the
composite `null`, never zero (`COMPOSITE.md` §4).

---

## When to use

- Any rung-2 result or above (ECE becomes required at DEV, subgroups at STANDARD).
- Before any sentence about clinical usefulness, deployment, or screening.
- On every cross-corpus evaluation — that is where calibration is most
  informative and least reported.
- When a pooled number looks good and you have not yet looked underneath it.

---

## 1. Calibration — the exact recipe

**Pinned by `COMPOSITE.md`:** ECE over **15 equal-mass bins**, computed on the
**same speaker-level predictions** as `AUC_honest`. Raw and temperature-scaled
variants are reported separately (arXiv:2601.07969); the **raw** value enters the
composite. `ECE_ref = 0.05`; the penalty is `lambda_cal * max(0, ECE − 0.05)`.

```python
def ece_equal_mass(y_true, p, n_bins=15):
    """Equal-MASS binning (equal counts per bin), not equal-width.
    Equal-width bins are dominated by whichever bin happens to be empty."""
    import numpy as np
    order = np.argsort(p)
    y, p = np.asarray(y_true)[order], np.asarray(p)[order]
    bins = np.array_split(np.arange(len(p)), n_bins)
    n, ece, rows = len(p), 0.0, []
    for b in bins:
        if len(b) == 0:
            continue
        conf, acc = p[b].mean(), y[b].mean()
        ece += (len(b) / n) * abs(acc - conf)
        rows.append({"n": len(b), "conf": float(conf), "acc": float(acc)})
    return float(ece), rows          # rows ARE the reliability curve
```

**Rules:**

1. **The calibrator is fitted per fold**, on an inner validation slice of the
   *training* partition (`A4 = fit_per_fold`). A calibrator fitted on test data
   is an A4 violation, not an A8 value (`AXIS_TAXONOMY.md` §A8).
2. **Calibration is AUC-invariant.** Temperature scaling is monotone, so it
   cannot change the ranking and cannot change AUC. If your AUC moves after
   calibration, you have a bug — probably a re-fit or a re-split.
3. **`isotonic` is pre-declared expected-unstable** on our per-fold validation
   sizes; report it with its own seed band, never head-to-head at n < 10.
4. Report the **reliability curve as a plot AND as the table above** — the table
   is what a reviewer can check; the plot is what a reader understands.
5. Report **Brier**, decomposed into reliability / resolution / uncertainty. The
   uncertainty term is fixed by the base rate, which is why a Brier score on a
   balanced subset is not comparable to one at the natural base rate.

---

## 2. Calibration under shift — an open question, framed as a falsifier

Nobody reports cross-corpus ECE / Brier decomposition, while cross-corpus AUC
collapse is well documented (arXiv:2511.14939: within-corpus 0.82–0.93 →
cross-corpus **0.43–0.68**). Clinical deployment needs to know whether a model
*knows* it is out of domain (`corpus/SURVEY_sota_methods.md` Gap 4).

**The falsifier, stated in advance:** measure ECE, Brier and reliability curves
within- and cross-corpus. **If ECE stays flat (within its own seed noise band)
while AUC falls from ~0.80 to ~0.55**, confidence is falsified as a shift
detector — a negative result with direct deployment consequences. If ECE rises in
lockstep with the AUC collapse, confidence is a usable shift signal, which is a
positive result the field currently lacks. Report temperature-scaled and raw
variants separately, because temperature scaling fitted in-domain is exactly what
would *hide* the effect.

---

## 3. Subgroups — the worst cell, not the average

`AUC_subgroup_min` = the **minimum** AUC over the pre-registered subgroup
partition, among subgroups with **n ≥ 30** (`min_subgroup_n`). The penalty is
`lambda_sub * max(0, AUC_honest − AUC_subgroup_min − delta_sub)` with
`delta_sub = 0.05`, a tolerance band sized to the sampling spread of subgroup
AUCs at our n — without it the term fires on noise.

**Pre-registered partitions**, in priority order:

| partition | why it is mandatory |
|---|---|
| **sex** | SVD's own reference number is reported **per sex** (UAR 85.61 F / 84.69 M) because pooled numbers are unstable. The EarlyPD benchmark finds female speakers score consistently *higher* across all models and tasks — contrary to prior reports (arXiv:2605.14066). HPP-Voice reports sleep-apnea AUC for males only (0.64 ± 0.03) because the pooled number is not meaningful (arXiv:2505.16490). |
| **age band** | On SVD, age *is* the label's strongest confound (age alone AUC 0.8709, `FINDINGS.md` F1). Within-age-band AUC is the only number that separates pathology from recruitment. Use pre-registered bands, never quantiles chosen after seeing results. |
| **language / accent** | PC-GITA and NeuroVoz Spanish, PROCESS-2 British English, SVD German, HPP-Voice Hebrew. A cross-lingual result reported as in-language is a confound claim (`SURVEY_datasets.md` §3.6). |
| **site / device** | where the corpus has it (Bridge2AI spans five sites). Body-coupled sensing costs 0.06–0.10 AUROC, and sex classification on CIDRZ collapses **0.954 → 0.596–0.628** under a wearable sensor (arXiv:2606.25116). |

**The age-band subgroup carries the most weight in this domain.** The SVD classes
differ by ~23 years of mean age (healthy 28.3 ± 11.6, pathological 51.0 ± 15.8).
A within-band AUC near chance while the pooled AUC is 0.87 is not a fairness
footnote — it is the finding that the model is an age detector.

**Reporting rules:**

- Report **every** subgroup's AUC with its n and CI, **including** subgroups below
  `min_subgroup_n = 30`. Those are reported but *excluded from the min* — the
  exclusion is a stated rule, not a quiet drop, otherwise the term is dominated
  by whichever cell happens to be smallest.
- Report the **pooled-to-worst gap** explicitly. `COMPOSITE.md`'s degenerate row
  D4 is exactly this attack: 0.89 pooled, 0.58 for the worst sex band, composite
  **−0.0420** — a losing row despite the second-highest AUC in the table.
- **Do not pool sexes on SVD** for a headline number without also giving the
  per-sex pair, because the corpus's own published reference does not.
- Subgroup CIs at these n are wide. Say so; do not read a 0.04 gap between two
  n = 40 cells as a subgroup effect.

---

## 4. The power collision — flag it, do not paper over it

Subgroup analysis multiplies the family size m and simultaneously shrinks n per
cell. R6 requires `min_attainable_p(n) = 2/2ⁿ ≤ 0.05/m` computed **for the actual
family**, so a subgroup breakdown can make an otherwise-feasible plan
under-powered by its own arithmetic.

**Resolution — declare it before the run, never after:** subgroup metrics are
reported as **descriptive with CIs** and enter the composite through
`AUC_subgroup_min`, but they are **not** members of the confirmatory family
unless pre-registered as such with the power recomputed for the enlarged m. A
pre-declared smaller primary family with the remainder explicitly labelled
exploratory is the sanctioned route (`CLAUDE.md` R6).

Reclassifying a subgroup result as "exploratory" *after* seeing it is HARKing and
is a BLOCKER.

---

## 5. Worked example — the reporting block

For any rung-3 row, this is the minimum that ships:

```
AUC_honest (speaker-level, n=10 paired speaker-disjoint partitions) : 0.842 [0.811, 0.869]
AUC_conf_max (age+sex, same protocol)                               : 0.877   -> M = -0.035
ECE  raw / temperature-scaled (15 equal-mass bins, fit per fold)     : 0.118 / 0.041
Brier (reliability / resolution / uncertainty)                       : 0.171 (0.021 / 0.093 / 0.243)
subgroup AUC   female (n=612) : 0.851 [0.812, 0.886]
               male   (n=744) : 0.834 [0.797, 0.868]
               age<40 (n=498) : 0.612 [0.548, 0.673]   <- AUC_subgroup_min
               age>=40 (n=858): 0.706 [0.663, 0.748]
               age<25 (n=22)  : 0.58  [--]  reported, EXCLUDED from min (n < 30)
pooled-to-worst gap                                                  : 0.230
```

Read it the way a reviewer would: the pooled 0.842 is **below** the demographic
bar (`M` is negative), the raw ECE is badly uncalibrated even though temperature
scaling fixes it, and the within-young-band AUC of 0.612 says most of the pooled
discrimination is age. The honest headline is not "AUC 0.84" — it is that this
configuration does not clear the confound bar and its within-band performance is
weak. That sentence is a finding (R8) and is written up with the same detail a
positive would get.

---

## 6. Anti-patterns

| anti-pattern | consequence | do instead |
|---|---|---|
| Reporting AUC only | a perfectly-ranked, badly-calibrated model looks deployable | ECE + reliability curve + Brier decomposition, every rung ≥ 2 |
| Equal-**width** ECE bins | dominated by empty bins; not comparable across runs | 15 equal-**mass** bins, as pinned |
| Fitting the calibrator on the test fold | an A4 leakage violation wearing an A8 costume | inner validation slice of the training partition, per fold |
| Reporting only the temperature-scaled ECE | hides the raw miscalibration that the composite prices | report both; **raw** enters the composite |
| Reporting mean subgroup performance | averages away the collapse | report the **minimum** (n ≥ 30) and the pooled-to-worst gap |
| Dropping small cells silently | the min term becomes whatever cell is smallest | report all cells; exclude from the min by the stated n ≥ 30 rule |
| Choosing age bands after seeing results | HARKing | pre-register the bands |
| Pooling sexes on SVD for the headline | the corpus's own reference is per sex | give the per-sex pair alongside |
| Adding subgroups to the confirmatory family without recomputing power | an arithmetically unsatisfiable plan, silently violated | recompute `2/2ⁿ ≤ 0.05/m` for the enlarged m before launch |
| Cross-corpus AUC without cross-corpus ECE | misses the only question deployment actually asks | report ECE both within- and cross-corpus |
| "Fairness limitation" in the discussion section | buries a finding | subgroup collapse is a headline result (`CLAUDE.md` §7) |

---

## Definition of done

- [ ] ECE (raw **and** temperature-scaled), 15 equal-mass bins, on speaker-level
      predictions, calibrator fitted per fold — all in the artifact.
- [ ] Reliability curve shipped as both a plot and the bin table.
- [ ] Brier reported with its three-way decomposition and the base rate stated.
- [ ] Every pre-registered subgroup has an AUC, an n, and a CI — including cells
      below n = 30, explicitly marked as excluded from `AUC_subgroup_min`.
- [ ] Pooled-to-worst gap reported as a number.
- [ ] Age-band-conditional AUC reported on any corpus where age is a live
      confound (on SVD: always).
- [ ] Cross-corpus rows carry cross-corpus ECE, not just cross-corpus AUC.
- [ ] Confirmatory vs exploratory status of subgroup tests declared **before** the
      run, with power recomputed for the actual m.
- [ ] No sentence claims clinical usefulness on the strength of a ranking metric.

---

## Cross-references

- Composite terms `ECE`, `AUC_subgroup_min`, `lambda_cal`, `lambda_sub`,
  `min_subgroup_n`, and degenerate row D4: `../../COMPOSITE.md` §2, §5
- Calibration axis A8 and its A4 fit-scope coupling: `../../AXIS_TAXONOMY.md`
- Secondary-metric list for the live pre-registration: `../../PREREGISTRATION.md` §3
- The confound this skill's age-band split exists to isolate: [`../voice-confound-baseline/SKILL.md`](../voice-confound-baseline/SKILL.md)
- Speaker-level predictions this skill consumes: [`../voice-speaker-disjoint-splits/SKILL.md`](../voice-speaker-disjoint-splits/SKILL.md)
- Verdicts and the rigor contract: [`../voice-claim-audit/SKILL.md`](../voice-claim-audit/SKILL.md)
- Statistical floor and pre-registration: [`../../meta-skills/autoresearch-paper-rigor/SKILL.md`](../../meta-skills/autoresearch-paper-rigor/SKILL.md)
- Evidence: uncertainty quantification arXiv:2601.07969 · cross-corpus collapse
  arXiv:2511.14939 · sensor shift arXiv:2606.25116 · sex effects arXiv:2605.14066,
  arXiv:2505.16490 · fairness survey arXiv:2605.01597
