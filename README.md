# auto-research-voice-based-disease-detection

An autonomous, pre-registered, falsification-driven research program on
**voice / speech as a biomarker of disease** (Parkinson's, Alzheimer's & MCI,
respiratory disease, laryngeal pathology, depression), run on a single
RTX 4090 laptop (16 GB) by an LLM agent team.

> **Status: BOOTSTRAPPING (2026-07-25).** Nothing here is a scientific claim yet.
> The repository currently contains the portable process pack and the scaffold.
> The first artifact required before any experiment runs is a *validated
> instrument* — see `CLAUDE.md` §0.

---

## What this is

This is the **eighth instantiation** of a portable autoresearch process
(`meta-skills/`, 29 skills) previously run on FX, equities, tabular, medical
imaging, DSBench, DARE-bench, and activation steering. The process is the
deliverable as much as the science: a Karpathy-style hill-climbing loop where

- every experiment is **pre-registered** with a falsifier and a numeric prediction,
- every claim is **rigor-gated** (n ≥ 7 seeds, paired Wilcoxon, bootstrap CI,
  Holm correction) before it may be called a result,
- **negative results are first-class** and published as prominently as wins,
- and the whole evidence trail is **auditable** from a transparent dashboard.

## Why voice-based disease detection

The domain is chosen because it is (a) clinically consequential, (b) laptop-scale
(seconds of audio, not gigapixel volumes), (c) anchored by **public benchmarks
with published numbers** to hill-climb against, and (d) known to have a
**replication problem** — published accuracies frequently fail to survive
speaker-independent splits, device/corpus shortcut audits, and cross-corpus
transfer. That last property is the opportunity: a rigorous, transparent,
negative-result-friendly program has something real to contribute here.

## The prime directive (learned the hard way)

A sibling program in this family produced *124 experiments and zero
external-ready findings*. The post-mortem is baked into this repository's
constitution as hard, checkable rules. The three that matter most:

1. **Validate the instrument before measuring anything.** The prior program's
   judge scored AUC 0.68 against its own ≥0.85 gate; every efficacy number and
   every null it produced was uninterpretable. **No claim may rest on an
   uncalibrated instrument — ever.**
2. **Never run on a substrate where the phenomenon cannot appear.** 74 % of the
   prior program's experiments ran on a model it had itself shown was incapable
   of the effect under study.
3. **A screening run is not a result.** 91 % of prior experiments were n=1, the
   champion never advanced past experiment 3, and the loop had nothing to climb.

See `CLAUDE.md` for the full constitution and `audits/` for the inherited
post-mortem.

## Layout

| path | role |
|---|---|
| `CLAUDE.md` | the constitution — read cover to cover before any work |
| `meta-skills/` | the portable, domain-agnostic process pack (29 skills) |
| `skills/` | domain-specific skills for voice-health research |
| `src/voicehealth/` | the research harness (data, features, models, eval, runner) |
| `ideas/<NN>/` | per-hypothesis sub-projects |
| `autoresearch_results/` | append-only experiment log, champion, reasoning entries |
| `IDEA_TABLE.md` | hypothesis registry + falsifiers + pre-classification |
| `EXPERIMENT_LEDGER.md` | promotion / demotion log |
| `FINDINGS.md` | external-ready findings (rigor-gated only) |
| `dashboard/`, `docs/dashboard/` | the transparent multi-page dashboard |
| `audits/` | implementation, science, data-split and meta-process audits |

## Ethics & data governance

Clinical audio is regulated and often carries a DUA. This repository will
**never** redistribute restricted corpora, commits no PHI, and makes **no
clinical claims**. Every dataset is recorded with its license and access path;
anything requiring credentialed access is used only under its own terms.

## License / status

Research artifact. Not a medical device. Not clinical advice.
