# `audits/` — the audit ledger

Every artifact here is adversarial by construction. An audit that finds nothing is a failed audit,
so each document below leads with what is broken, not with what works.

**Circularity disclosure, applying to every file in this directory:**
*Internal QA pass — implementer and critic share a model family; independent external review
pending.* A same-family audit is a useful filter, not an external seal
(`CLAUDE.md` R5, R16).

---

## Index

| audit | date | scope | one-line verdict |
|---|---|---|---|
| [**DATA_SPLIT_AUDIT.md**](DATA_SPLIT_AUDIT.md) | 2026-07-26 | `data/interim/{svd,coswara,coughvid}/manifest.csv` — speaker ids, sessions/speaker, class balance, age/sex confounds, recording-level leakage simulation | **SVD CONDITIONAL PASS (screening only, 49 speakers) · Coswara FAIL (0 acquired positives under the pre-registered label; 9 positive speakers under any substitute) · COUGHVID HARD FAIL (`speaker_id` is the recording UUID — a speaker-disjoint claim there would be false as stated).** A recording-level split would leak 100 % of SVD speakers and 99.4 % of Coswara test recordings. |
| [**IMPL_CRITIC.md**](IMPL_CRITIC.md) | 2026-07-26 | `src/voicehealth/{benchmark,embed,features}.py`, `scripts/run_benchmark.py`, `scripts/audit_demographic_baseline.py` | **One INVALIDATES-RESULTS defect** (the embedding cache key omits labels/speaker-ids, so a relabelled manifest gets a cache hit and the *old* labels), **five BIASES**, nine cosmetic. `tests/` is **empty** — there is no rung-0 UNIT layer. The one executed SVD run is **not** invalidated; its `NOT CLEARED` verdict survives, and two of the biases favoured the audio arm that still lost. |
| [**SCI_CRITIC.md**](SCI_CRITIC.md) | 2026-07-26 | `FINDINGS.md` F1, `PREREGISTRATION.md` V2, `IDEA_TABLE.md` V1–V7, `COMPOSITE.md` | **The composite fingerprint and all 8 degenerate rows were re-executed and reproduce exactly** — that demonstration is real. But `lambda_sub` (0.75) **cannot fire on SVD** (both sex subgroups fall under `min_subgroup_n = 30`), `lambda_ctrl` (3.00) self-weakens as pipeline noise grows, and the formula is **implemented nowhere** (`src/voiceaudit/composite.py` does not exist). No `IDEA_TABLE.md` verdict outruns its evidence — every row is `UNTESTED`, which is right — but five *plans* outrun the acquired data. `PREREGISTRATION.md` §4 A2 makes its own §6 instrument gate unexecutable. F1's 0.871 is measured on 1,853 speakers and quoted against 49, where the real figure is **0.741**. |
| [**NOVELTY_CRITIQUE.md**](NOVELTY_CRITIQUE.md) | 2026-07-25 | prior art for the program's framing and target selection | The autoresearch *loop* is not novel (arXiv:2606.20394 published it in June 2026) and the accuracy frontier is closed to a laptop; **the domain survives under exactly one framing — an audit engine, not a detector factory.** |
| [**PRIOR_AUTORESEARCH_REPOS.md**](PRIOR_AUTORESEARCH_REPOS.md) | 2026-07-25 | archaeology of seven prior `dlmastery/*` autoresearch programs, replayed from their own `experiment_log.jsonl` | Two programs landed real externally-benchmarked results; one ran **0 experiments** across 324 scaffolded tasks; one shipped a paper abstract still containing a different project's numbers. The failure modes `CLAUDE.md` encodes are measured, not assumed. |

---

## The single most serious defect across all audits

**`src/voicehealth/embed.py:211-234` + `:289-311` — the embedding cache key is built from the audio
digests, the encoder id and the preprocessing policy, and omits `label`, `speaker_id`, `age` and
`sex`; `EmbeddingBundle.from_npz` then returns all four out of the cached `.npz` without comparing
them to the manifest that was just loaded.** Edit a label definition, leave the audio untouched,
re-run: you get `[embed] cache hit` and a silently stale-labelled result with a matching
`embedding_content_hash` and a clean provenance record. `PREREGISTRATION.md` §4 A2 pins a label
*definition*, and `DATA_SPLIT_AUDIT.md` §3 shows the Coswara manifest must be re-fetched — so this is
primed to fire on the next two things the program is scheduled to do.

---

## Missing state files (blocking, found by `SCI_CRITIC.md` §2)

`CLAUDE.md` §6 mandates these; none exists as of 2026-07-26:

- `autoresearch_results/experiment_log.jsonl`
- `autoresearch_results/best_config.json`
- `autoresearch_results/JUDGE_CARD.md`
- `EXPERIMENT_LEDGER.md`
- `src/voiceaudit/composite.py` and `scripts/composite_degenerate_check.py` (`COMPOSITE.md` §6)
- `tests/` is present but empty — no rung-0 UNIT gate exists

Consequence: the one executed run (`autoresearch_results/bench_svd_egemaps.json`) has no ledger row,
no rung classification, and no recorded deviation from `PREREGISTRATION.md` §4 A2.

---

## Audits still missing from this directory

Named in `CLAUDE.md` §6 / the meta-process but not yet written:
**META_PROCESS_AUDIT** (skill-pack fidelity), **SHUFFLE_TEST** (the label-shuffle negative control as
a standing artifact, `PREREGISTRATION.md` C3), **LINK_DISCIPLINE / DASHBOARD_COMPREHENSION** (the
`docs/dashboard/` surfaces), and a **CODE_REVIEW** pass on `scripts/preprocess_audio.py` and the
fetchers, which `IMPL_CRITIC.md` covered only at the interface level.
