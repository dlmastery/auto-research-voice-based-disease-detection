---
name: voice-claim-audit
description: >
  The program's signature skill. Use when re-testing a PUBLISHED voice-health
  claim. Six phases: locate the claim's exact metric / split policy / preprocessing
  scope, reproduce it under ITS OWN protocol (this is the champion), then re-run
  under (a) speaker-disjoint and (b) confound-matched protocols, and report the
  DELTA as the finding. Enforces the strictness ladder L0-L5, the five verdicts
  (HOLDS / ATTENUATED / BREAKS / INCONCLUSIVE / NOT_REPRODUCIBLE), the "cite the
  nearest work first and state the delta" rule, the tone policy (audit the claim,
  never the authors), and the retraction machinery.
---

# Skill — voice-claim-audit

> **This program does NOT try to build a better voice-disease detector.** The
> novelty is the audit target and the ledger of verdicts. Success is a defensible
> ledger — including, especially, the entries reading *"this published claim did
> not survive."* Negative results are the product. (`CLAUDE.md` §0, R8.)

---

## When to use

- Opening a new audit target (a published number becomes a hypothesis row).
- Writing a `PREREGISTRATION.md` for that target.
- Deciding whether a measured drop is a finding, an artifact, or a failure to
  reproduce.
- Before promoting anything to `FINDINGS.md` — the R11b gate lives here.

---

## 0. R11b in one line — you must be auditing an external published number

> The single strongest predictor of success across seven prior programs.

Repos anchored to an external benchmark with a public number produced real
results; repos climbing a **self-defined composite** produced rising curves and
zero information (`CLAUDE.md` R11b). The composite in `COMPOSITE.md` is an
**internal ranking device only**. Every promotion to `FINDINGS.md` must be
expressed as a delta against a published, citable number.

The three anchors currently in scope:

| corpus | published number | source |
|---|---|---|
| **SVD** | **UAR 85.22** (F 85.61 / M 84.69), with a public repo *and* a REFORMS checklist | Vrba et al., arXiv:2410.10537 |
| **Coswara** | AUC ≈ 0.92 intra-dataset (and 0.82 for Audio-MAE under a disjoint protocol) | `corpus/SURVEY_datasets.md`; arXiv:2511.14939 |
| **PROCESS-2** | macro-F1 **0.59** (3-way), F1 0.85 (2-way), MMSE RMSE 3.87 | arXiv:2605.14888 |

---

## 1. Phase 1 — Locate the claim, exactly

Extract these from the paper and record each with a **quote or a page/section
pointer**, or mark it `UNSTATED`:

| field | why it matters |
|---|---|
| **the exact metric** | UAR ≠ accuracy ≠ ROC-AUC ≠ macro-F1. arXiv:2410.10537 deliberately reports **UAR and omits accuracy** because class imbalance makes accuracy over-optimistic on voice-pathology corpora. Auditing a UAR claim with an AUC is not an audit. |
| **the split policy** | recording-level? session-level? speaker-level? fixed official folds? Is the grouping key named, or only implied? |
| **the preprocessing fit scope** | scaler/PCA/resampler fitted before or after the split? Usually `UNSTATED` — and that is itself a finding-shaped fact. |
| **the aggregation unit** | recording, session, or speaker-level scoring |
| **the exact subset** | SVD's reported accuracy "swings with which pathology subset and which audio material is used" (UCL Discovery 10139814). Pin the subset **in git before the first sweep**; silently re-choosing it later is HARKing. |
| **the head and its hyperparameters** | the axis most likely to be silently different between us and the paper (`AXIS_TAXONOMY.md` §A7) |
| **the class balance / any resampling** | oversampling before the split is a leak with a different signature |
| **n, and whether it is speakers or recordings** | |

**`UNSTATED` fields are logged as reproduction ambiguities, not guessed.** Where
a field is unstated and two readings are plausible, run **both** — that is a
documented two-cell reproduction, not a sweep, and both cells go in the ledger.

---

## 2. Phase 2 — Reproduce under the paper's own protocol (this is the champion)

The champion in `best_config.json` is a **reproduction**, not a method. It
advances when a *more faithful* reproduction is found — closer to the published
number **under the published protocol** — never when a better classifier is found
(`AXIS_TAXONOMY.md` §0).

**The gate:** if `AUC_full` / the paper's own metric cannot be brought within
**0.05** of the published value under the published protocol, we have not
reproduced the claim and therefore **cannot audit it**. Verdict:
`NOT_REPRODUCIBLE`, logged with the reproduction gap
(`PREREGISTRATION.md` §11.5). That is an honest, publishable outcome — and it is
*not* a claim that the paper is wrong; it is a claim about what we could rebuild
from what was written.

This phase also produces `AUC_leaky`: the number under the paper's own looser
protocol. **Measuring it is what makes the audit an audit** (`COMPOSITE.md` §2).

---

## 3. Phase 3 — Descend the strictness ladder

The ladder is monotone by construction; each row is exactly **one axis** from the
row above, so the marginal cost of each rigor step is directly readable in AUC
points. **This table is the program's core deliverable shape**
(`AXIS_TAXONOMY.md` §4).

| row | A3 split | A4 fit scope | A9 confound control | A11 unit | what it adds |
|---|---|---|---|---|---|
| **L0** | paper's stated split | paper's stated scope | none | paper's | the reproduction champion |
| **L1** | `speaker_disjoint` | paper's | none | paper's | + identity disjointness |
| **L2** | `speaker_disjoint` | `fit_per_fold` | none | paper's | + preprocessing hygiene |
| **L3** | `speaker_disjoint + demographically_matched` | `fit_per_fold` | none (forced) | `speaker_level` | + demographic deconfounding |
| **L4** | L3 | `fit_per_fold` | `subspace_projection` + A12 controls | `speaker_level` | + mechanistic identity ablation |
| **L5** | `cross_corpus` | `fit_per_fold` | as L4 | `speaker_level` | + transfer |

**The deliverable is the trajectory, and every intermediate point is a ledger
row.** Coordinate descent here is *not* hill-climbing toward a maximum — it is a
systematic descent from the paper's protocol toward the strictest one, measuring
the drop at each step.

Two rules that keep the ladder honest:

- **A P-axis move that lowers AUC is a positive finding**, not a DISCARD. The
  Karpathy KEEP/DISCARD rule is a maximisation rule and has no meaning on
  protocol axes; on P-axes the runner records `HOLDS`/`ATTENUATED`/`BREAKS`
  against the **pre-registered falsifier**, and the champion does not move
  (`AXIS_TAXONOMY.md` §5(ii)).
- **The budget axis here is statistical power, not norm.** Every strictness step
  shrinks the usable evaluation set (matching discards speakers; speaker-level
  aggregation shrinks n). Stack until the pre-registered minimum effective
  speaker count is hit, then **stop and say so**.

---

## 4. Phase 4 — The controls that make a drop interpretable

A drop is only a finding if it survives these. All are required; none is optional.

| control | rules out | pass condition |
|---|---|---|
| **label shuffle** | the whole pipeline being an artifact | shuffled-label AUC within `0.5 ± 2σ_null`, with **σ_null measured empirically** across the same partitions, never a rule of thumb. Priced at `lambda_ctrl = 3.00` — near-fatal by design. |
| **confound battery** | the claim living below the honest bar | `AUC_conf_max` reported; the finding is claimed only for the margin above it |
| **variance-matched random projection** | "any rank-k removal hurts" | mandatory companion to any `subspace_projection`; a *plain* random subspace removes less variance and is a strawman |
| **class-direction positive control** | the projection machinery not working at all | projecting out `μ_pos − μ_neg` **must** collapse AUC; if it does not, the code is `BROKEN` |
| **leaky reference** | "speaker-disjoint" doing nothing | `AUC_leaky − AUC_honest` is its own ledger row |
| **manipulation check** | a null that is really a blind instrument | e.g. speaker-ID top-1 must fall ≥ 60 % relative at k=16. **A null under a failed manipulation check is `BROKEN`, not a null** — this is the exact defect that invalidated five weeks of the sibling program (`CLAUDE.md` §1). |

**σ below the instrument's own noise is not a result.** A measured delta smaller
than the instrument's re-measurement variance is reported as *"below detection
floor"*, never as a null (R4).

---

## 5. Phase 5 — Verdict, and the sentence you are allowed to write

Five verdicts, decided against the **pre-registered falsifier** on the
**pre-registered primary metric**. The composite does not appear in this decision
at all (`COMPOSITE.md` §7).

| verdict | meaning |
|---|---|
| **HOLDS** | the number survives the strictness ladder. A positive control the field currently lacks — published with equal prominence. |
| **ATTENUATED** | it survives but shrinks; report the surviving margin above `AUC_conf_max` and the exact AUC cost of each rigor step |
| **BREAKS** | at some ladder row the discrimination falls to the confound bar or to chance; report the row at which it collapses |
| **INCONCLUSIVE / UNDERPOWERED** | CIs overlap but the noise band is wider than the predicted effect. Report the achieved noise band **and the n that would be needed** — do not report it as a null. |
| **NOT_REPRODUCIBLE** | Phase 2's 0.05 gate failed; log the reproduction gap |

**The rigor contract for any "beats"/"significant"/"outside noise" sentence:**
paired Wilcoxon + BCa bootstrap CI (10,000 resamples, **resampled at the speaker
level** — recording-level resampling understates the interval because recordings
within a speaker are not independent) + Holm–Bonferroni across the confirmatory
family + an **empirically measured** noise band. `EXTERNAL-READY` additionally
requires the **ordinal gate**: the worst evaluation partition must beat the best
comparator partition.

**Power must be arithmetically possible.** `min_attainable_p(n) = 2/2ⁿ` vs Holm's
tightest `0.05/m`, computed **for the actual family size, every time**. The
current pre-registration has m = 14, where n = 7, 8 and 9 are all infeasible and
**n = 10** is the minimum. n ≥ 8 is a floor, never the rule (R6).

**The domain caveat:** repeated speaker-disjoint partitions are drawn from one
finite speaker pool, so they are positively correlated and Wilcoxon over them is
**anti-conservative**. Report the Wilcoxon p **and** a correlation-corrected
interval (Nadeau–Bengio corrected resampled-t, or a speaker-level cluster
bootstrap), and let **the more conservative bind the verdict**
(`AXIS_TAXONOMY.md` §5(i)).

---

## 6. Phase 6 — Cite the nearest work first, and state the delta

**The rule:** in any write-up, the **nearest competing work is cited first**, in
the same paragraph as the claim, with the delta stated explicitly. Not in a
related-work section at the end. Novelty decays — in the sibling program two of
three planned contributions were **scooped within six weeks** while the plan sat
unrun (R11).

**Re-run the prior-art check immediately before any promotion to "contribution",
not once at the start.** Every arXiv id is mechanically verified (fetch the abs
page, confirm title + authors) before it ships; unverifiable ids are marked
`[UNVERIFIED]`; ids `26MM.NNNNN` are 2026 (R10). **Cite nothing from memory.**

**Tone policy — audit the claim, never the authors**
(`audits/NOVELTY_CRITIQUE.md` §d.2, `PREREGISTRATION.md` §15). What we will not
claim:

- Not that voice-health detection does not work.
- Not that any named authors made an error — only that a stated number does or
  does not survive a stated protocol change, on the corpora we could access.
- Not a clinical or diagnostic conclusion of any kind.
- Not methods novelty: the audit *loop* is not novel (Jain & Linares, 2026,
  arXiv:2606.20394 published an auditable autoresearch loop). We claim **domain +
  verdict-ledger** novelty only.

**Retraction machinery is mandatory** (R11d). The most trustworthy artifacts in
the whole prior lineage are the `WHY_QUARANTINED.md` records of results a program
**withdrew**. `autoresearch_results/_quarantined/` exists to be used. A program
that cannot retract cannot be believed.

---

## 7. Worked example — auditing SVD UAR 85.22

**Phase 1.** Metric = **UAR**, reported per sex (85.61 F / 84.69 M), accuracy
deliberately omitted. Public repo + REFORMS checklist (code archive Zenodo
`10.5281/zenodo.13771573`). Pathology subset and audio material must be read out
of the repo and pinned in git — SVD's number moves with both.

**Phase 2.** Reproduce UAR under the paper's own split and preprocessing. Gate:
within 0.05 of 85.22, else `NOT_REPRODUCIBLE`.

**Phase 3.** Descend L0 → L5. Note what is already known before a single
embedding is loaded: **200 of 1,853 speakers contribute more than one session
(max 24)** in the metadata manifest, and **378 speakers / 1,020 sessions =
40.88 % of rows** are at risk under the archive manifest's obvious key — so L1 is
expected to bite. Independently, **age alone reaches ROC-AUC 0.8709 and age+sex
0.8768** speaker-disjoint (`FINDINGS.md` F1) — so L3 is expected to bite hard.

**Phase 4.** Full battery + label shuffle + leaky reference. `AUC_conf_max` is
already known to be ≈ 0.877 on this corpus.

**Phase 5.** The likely honest outcome is `ATTENUATED`: the audio number survives
but the *margin above demographics* is the only defensible quantity. The finding
is then the **table of AUC costs per rigor step**, not a rival detector.

**Phase 6.** The honesty note that must travel with it: **UAR and ROC-AUC are
different metrics and are not like-for-like.** The F1 comparison is indicative.
A proper audit recomputes the published pipeline's own metric on matched splits —
that is the experiment; F1 is only the reason to run it.

---

## 8. Anti-patterns

| anti-pattern | consequence | do instead |
|---|---|---|
| Auditing a UAR claim with an AUC number | not an audit; two metrics passing in the night | reproduce the paper's own metric first |
| Skipping Phase 2 and going straight to the strict protocol | you cannot attribute the gap to the protocol vs to your pipeline | reproduce under the paper's protocol; that gap is the champion's gate |
| Moving two ladder rows at once | the marginal cost of each rigor step becomes unreadable | one axis per row; the ladder is monotone by construction |
| Treating a P-axis drop as a DISCARD | you throw away the finding | P-axes record HOLDS/ATTENUATED/BREAKS; the champion does not move |
| Reporting a null without the manipulation check | cannot distinguish "no effect" from "cannot detect an effect" | failed manipulation check ⇒ `BROKEN`, not null |
| Guessing an `UNSTATED` field | silently audits a pipeline the paper never described | log the ambiguity; run both plausible cells |
| Re-choosing the pathology subset after seeing results | HARKing; a BLOCKER | pin the subset in git before the first sweep |
| Recording-level bootstrap for the CI | understates the interval | cluster-bootstrap at the speaker level |
| A prior-art check done once at kickoff | two of three sibling contributions were scooped in six weeks | re-run it immediately before promotion |
| "Their result is wrong" | outside what the evidence supports, and outside the tone policy | "this number does not survive this stated protocol change, on the corpora we could access" |
| Quietly deleting a result that turned out to be an artifact | the ledger loses its credibility | `autoresearch_results/_quarantined/` with a `WHY_QUARANTINED.md` |

---

## Definition of done

- [ ] Every Phase-1 field recorded with a quote/pointer or marked `UNSTATED`.
- [ ] Phase 2 reproduction within 0.05 of the published number under the
      published protocol, or `NOT_REPRODUCIBLE` logged with the gap.
- [ ] `AUC_leaky` measured and logged as its own row.
- [ ] Ladder rows L0…Lk each one axis apart, each with its own artifact.
- [ ] All six controls ran; σ_null measured empirically; manipulation check passed.
- [ ] Power computed for the **actual** family size m at launch; runner refused
      any under-powered plan.
- [ ] Both the Wilcoxon p and the correlation-corrected interval reported; the
      more conservative binds.
- [ ] Verdict decided against the pre-registered falsifier, not the composite.
- [ ] Nearest competing work re-checked and cited **first**, with the delta.
- [ ] Tone policy respected; the "what we will not claim" list holds.
- [ ] Negative/attenuated outcomes written up with the same detail as positives.

---

## Cross-references

- The constitution: `../../CLAUDE.md` (R1, R3, R4, R6, R7, R8, R10, R11, R11b, R11d)
- The live pre-registration this skill formalises: `../../PREREGISTRATION.md`
- Strictness ladder + P/N axis families: `../../AXIS_TAXONOMY.md` §0, §4, §5
- Composite terms `AUC_leaky`, `AUC_negctrl`, null policy: `../../COMPOSITE.md`
- Splits: [`../voice-speaker-disjoint-splits/SKILL.md`](../voice-speaker-disjoint-splits/SKILL.md)
- The honest bar: [`../voice-confound-baseline/SKILL.md`](../voice-confound-baseline/SKILL.md)
- Subgroups + calibration (rung-3/4 required terms): [`../voice-calibration-and-subgroups/SKILL.md`](../voice-calibration-and-subgroups/SKILL.md)
- Statistical contract: [`../../meta-skills/autoresearch-paper-rigor/SKILL.md`](../../meta-skills/autoresearch-paper-rigor/SKILL.md)
- Label-shuffle control: [`../../meta-skills/autoresearch-shuffle-test/SKILL.md`](../../meta-skills/autoresearch-shuffle-test/SKILL.md)
- Ladder rungs: [`../../meta-skills/autoresearch-tiered-ladder/SKILL.md`](../../meta-skills/autoresearch-tiered-ladder/SKILL.md)
- Ledger + findings discipline: [`../../meta-skills/autoresearch-findings-ledger/SKILL.md`](../../meta-skills/autoresearch-findings-ledger/SKILL.md)
- The replication evidence base: `corpus/SURVEY_sota_methods.md` (d)
