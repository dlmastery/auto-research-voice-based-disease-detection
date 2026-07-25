# `skills/` — the voice-health domain pack

This directory holds the **domain layer** of the program's skill system. It is
the voice-health instantiation of the portable process in
[`../meta-skills/`](../meta-skills/README.md).

## The split: `meta-skills/` (portable) vs `skills/` (domain)

| | `meta-skills/` | `skills/` (this directory) |
|---|---|---|
| **what it encodes** | the autoresearch *process* — experiment ritual, ladder rungs, split-audit gate, shuffle test, statistical rigor floor, findings ledger, dashboard, multi-agent dispatch | the *domain* — voice corpora, speaker leakage, acquisition confounds, embedding extraction, claim auditing, clinical calibration |
| **domain-agnostic?** | **yes** — 29 skills, portable verbatim to any topic | **no** — every rule cites a measured fact about a specific voice corpus or a specific published voice-health claim |
| **relationship** | the spine | the instantiation; a domain skill *extends* its meta counterpart and may add constraints, never relax them |
| **provenance** | copied verbatim from the sibling steering program | written for this repo against `CLAUDE.md`, `corpus/`, `AXIS_TAXONOMY.md`, `COMPOSITE.md`, `PREREGISTRATION.md`, `FINDINGS.md` |

A process improvement learned here is ported back to `meta-skills/`; a domain
fact learned here stays here.

## The pack

| skill | one line | run it when |
|---|---|---|
| [voice-speaker-disjoint-splits](voice-speaker-disjoint-splits/SKILL.md) | Never split on recordings. Group on the **speaker** id, assert disjointness before **every** fit. | before every fit, always — this is the gate the rest of the pack assumes |
| [voice-confound-baseline](voice-confound-baseline/SKILL.md) | Compute the strongest trivial-confound baseline **first**; claim only the margin above it. | before the audio is even loaded |
| [voice-dataset-onboarding](voice-dataset-onboarding/SKILL.md) | Eight gates for adding a corpus: licence/DUA, access path, **speaker-id availability**, balance + base rate, ≥500/class, confound audit, data card, ethics. | adding any corpus; starting any DUA |
| [voice-embedding-extraction](voice-embedding-extraction/SKILL.md) | Frozen SSL/foundation embeddings on a 16 GB laptop; content-hash `.npz` cache; extract **once**. | first time audio is touched; adding an A5 value |
| [voice-claim-audit](voice-claim-audit/SKILL.md) | **The signature skill.** Reproduce a published claim under its own protocol, then descend the strictness ladder and report the delta. | opening any audit target; before any `FINDINGS.md` promotion |
| [voice-calibration-and-subgroups](voice-calibration-and-subgroups/SKILL.md) | Reliability curves, ECE, worst-subgroup performance. A model that works only for one subgroup is a **finding**, not a footnote. | every rung ≥ 2 result; every cross-corpus row |

## The order they run in

```
onboarding ──> speaker-disjoint splits ──> confound baseline ──> embedding extraction
                        │                          │                      │
                        └──────────────────────────┴──────────────────────┘
                                             │
                                        claim audit  ──>  calibration + subgroups
                                             │
                                   verdict -> EXPERIMENT_LEDGER.md -> FINDINGS.md
```

Splits and the confound baseline are **gates**, not steps: nothing downstream is
interpretable until both have passed and both have written artifacts.

## The four facts the whole pack is built on

All measured in this repo, all traceable to a JSON artifact (`CLAUDE.md` R1/R2) —
none quoted from a paper.

1. On SVD, **age alone reaches ROC-AUC 0.8709** and age+sex 0.8768 speaker-disjoint,
   with no audio at all (`FINDINGS.md` F1). Healthy 28.3 yr vs pathological 51.0 yr.
2. **200 of 1,853 SVD speakers contribute more than one session** (max 24); under
   the archive manifest's obvious key, **40.88 % of rows** are at leakage risk —
   and 21 speakers appear as both healthy and pathological.
3. **COUGHVID has no participant identifier at all** (34,434 rows, 34,434 uuids),
   so it cannot carry an evaluation-tier claim regardless of its size.
4. The published anchors this program audits against are **SVD UAR 85.22**
   (arXiv:2410.10537), **Coswara AUC ≈ 0.92**, and **PROCESS-2 macro-F1 0.59**
   (arXiv:2605.14888) — R11b requires every promotion to be a delta against one
   of them, never against the internal composite.

## Where the constitution and the domain do not fit cleanly

Recorded rather than silently resolved; see `AXIS_TAXONOMY.md` §5 for the two the
scaffold already flagged.

1. **KEEP/DISCARD has no meaning on protocol axes.** A P-axis move that lowers
   AUC is the *finding*. The champion-health monitor (`CLAUDE.md` §6, "must
   advance or the loop is broken") must be scoped to N-axis experiments or it
   fires spuriously on a program working exactly as designed.
2. **`n` is not i.i.d.** Repeated speaker-disjoint partitions come from one finite
   speaker pool and are positively correlated, so Wilcoxon is anti-conservative.
   Report a correlation-corrected interval alongside and let the more
   conservative bind.
3. **R11b vs the speaker-id gate.** COUGHVID has a published number (~0.93) and
   no speaker ids. The external-anchor rule and the evaluation-tier rule collide;
   resolved in favour of the split gate — COUGHVID is OOD/negative-control only.
4. **Metric mismatch at the anchor.** SVD's published anchor is **UAR**; our
   composite and confound bar are in **ROC-AUC**. Phase 2 of an audit must
   reproduce the paper's own metric, or the delta is not a delta.
5. **R3 "validate the judge" has no LLM judge here.** The instruments in this
   program are the feature extractor, the subspace estimator and the probe.
   `JUDGE_CARD.md` should be read as an **instrument card** (the manipulation
   check in `PREREGISTRATION.md` §6 is its concrete form).
6. **R11c cuts against this directory.** A skills pack is scaffold. It is
   minimally sufficient now; per R11c the next action is the **first real
   experiment**, not another process artifact. Track
   `scaffold_files_written / experiments_run`.

---

*Internal QA pass — independent external review pending (R5, R16). Every arXiv id
in this pack is carried over from `corpus/SURVEY_datasets.md` /
`corpus/SURVEY_sota_methods.md`, mechanically verified 2026-07-25; none was
introduced from memory (R10). Every measured number is carried over from a JSON
artifact produced by a script in `scripts/` (R1/R2).*
