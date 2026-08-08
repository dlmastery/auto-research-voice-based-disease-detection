# EXPERIMENT_LEDGER — promotion / demotion log

> **Back-filled on 2026-08-08 from the artifacts in `autoresearch_results/`. It was not written
> contemporaneously**, because this program has no `experiment_log.jsonl` — `CLAUDE.md` §6 names
> one and it does not exist. Every row below therefore points at a file that can be re-read
> today (R1); no row records anything that is not in an artifact, and runs that left no artifact
> are listed separately at the end rather than reconstructed from memory (R2).
>
> Ordering is by each artifact's own recorded timestamp (`generated_utc`) where it has one and
> by file mtime (local clock) otherwise, so the two are not strictly comparable to the minute.
> The **rung** column is an assessment against the gate text in
> `CLAUDE.md` §5; it is **not machine-recorded** anywhere, unlike the tier and the power check.

---

## Executed runs

| # | date | run · artifact | corpus · scale | tier | n × folds · m | rung reached | verdict |
|:--|:--|:--|:--|:--|:--|:--|:--|
| E1 | 2026-07-25 | `audit_demographic_baseline.py` · `F1_demographic_baseline.json` | SVD metadata · 2,225 sessions / 1,853 speakers | `SCREENING` | 1 fit × 5-fold · m — | **1 SMOKE** | **age bar established**: age-only 0.8709, age+sex speaker-disjoint 0.8768 → F1 |
| E2 | 2026-07-25 23:55 | `run_benchmark.py --backbone egemaps --repeats 10` · `bench_svd_egemaps.json` | SVD pilot · 667 rec / **49 spk** | `SCREENING` (capped by the data-split audit, not by power) | 10 × 5 · m=5, `feasible=true` | **2 DEV, blocked** | **NOT CLEARED** — all 5 heads below the age bar (0.7027 rec). Best head `gbt`. |
| E3 | 2026-07-27 | `run_benchmark.py --backbone wavlm --repeats 3` (F2) | SVD pilot · 667 rec / **49 spk** | `SCREENING` · **UNDERPOWERED** | 3 × 5 · m=5, `feasible=false` (min p 0.25 > Holm 0.01) | **1 SMOKE** | **NOT CLEARED \| UNDERPOWERED (R6)** — the power gate refused certification. Artifact **superseded**, see D1 below. |
| E4 | 2026-07-27 | `run_benchmark.py --backbone wavlm --folds 5` (`config_hash f267bc4b705e8645`) | SVD full · 28,509 rec / 1,679 spk | interim | 1 × 5 · m=2 | **2 DEV** | **NOT CLEARED** — age 0.8744 vs WavLM 0.7386. **Superseded** by E6. |
| E5 | 2026-07-28 03:59 | `run_v2_speaker_subspace.py` · `V2_speaker_subspace.json` | SVD full · 28,509 / 1,679 | `EVALUATION` | 10 × 5 · m=14, `min p 0.001953 < Holm 0.003571` | **3 STANDARD** | **CLAIM SUPPORTED, falsifier did NOT fire** → F4. D > 0 with CI excluding zero at all 7 ranks vs **both** controls. |
| E6 | 2026-07-28 04:47 | `run_benchmark.py --backbone wavlm --folds 5 --repeats 8` · `bench_svd_wavlm_mean_std.json` (`815673703168e601`, `git_sha 5cab307`) | SVD full · 28,509 / 1,679 | `CERTIFIED` (EVALUATION) | 8 × 5 · m=2, `min p 0.0078 < Holm 0.025` | **3 STANDARD** | **NOT CLEARED** → F3. Margin **−0.1310** [−0.1471, −0.1149], Wilcoxon p 0.0078. The gap **widened** with 34× the speakers. |
| E7 | 2026-07-28 05:56 | `run_v7_silence_shortcut.py` · `V7_silence_shortcut.json` | SVD · Coswara · COUGHVID | `PARTIAL` — 4 of 6 cells | 10 × 5 · m=6 | **2 DEV** | **shortcut does NOT generalise** → F6. Max 0.5264 across three corpora. `falsifier_fully_evaluable: false`. |
| E8 | 2026-07-28 07:03 | `run_v6_preprocessing_leakage.py` · `V6_preprocessing_leakage.json` | SVD · Coswara | `PARTIAL` — 3 of 6 cells | 10 × 5 · m=6 | **2 DEV** | **near-null reproduced and extended to embeddings** → F5. SVD/WavLM D **+0.00004**. |
| E9 | 2026-07-28 09:05 | `run_v1_ssl_vs_handcrafted.py` · `V1_ssl_vs_handcrafted.json` | SVD age-matched · ~613 spk/seed | `EVALUATION` for the cell that ran | 10 × 5 · m=9 | **3 STANDARD** | **CLAIM SUPPORTED** → F7. eGeMAPS 0.6496 > WavLM 0.6227, CI [−0.0317, −0.0215], **10/10 seeds**. |
| E10 | 2026-07-28 14:11 | `V2_SHUFFLE=1 run_v2_speaker_subspace.py` · `V2_speaker_subspace_SHUFFLE.json` | SVD full | negative control | 3 × 5 · ranks {1,8,16,64} | **control for E5** | **PASSES** — full AUC 0.7382 → **0.5069**; D at k=8 falls 0.0921 → 0.0017 (53×) and **changes sign across ranks**. |

**No row has ever reached rung 4 (FULL).** Rung 4 requires cross-corpus transfer, calibration,
subgroup robustness and an independent re-run; every evaluation-tier result above is SVD-only,
reports ECE without a reliability curve, and has not been independently re-run.

---

## Demotions, supersessions and deliberate exclusions

| id | what happened | consequence |
|:--|:--|:--|
| **D1** | E3's artifact was **overwritten in place** by E4/E6 at the same path. `FINDINGS.md` F2 cites `config_hash d8ab0b7584b7fdb7`; the file now holds `815673703168e601`. | F2's numbers survive **only in prose** and are the one row in the README's four-number table without a CI. Re-running the pilot config is the only way to restore it. |
| **D2** | E2's `bench_svd_egemaps.json` passes the R6 power check at n=10 but sits on **49 speakers**, which `audits/DATA_SPLIT_AUDIT.md` rates **CONDITIONAL PASS — screening only**. | **Power feasibility does not promote a run.** The tier is set by the weaker of the two gates, and it is `SCREENING`. |
| **D3** | COUGHVID cells of V6 **deliberately excluded**, citing F2/`acquisition/coughvid_meta_stats.json`: 34,434 unique uuids for 34,434 recordings, `speaker_id_field_present: false`, so `GroupKFold` degenerates to plain `KFold`. | Recorded as a judgement with its reasoning, **not a silent omission**. A pre-registered cell that becomes *known-uninformative* is different from one that is merely inconvenient. |
| **D4** | E9's **first** artifact claimed eGeMAPS had run: `encoders_run` was populated from *the cache file existing* rather than from *the arm producing a number*. | A silently-skipped arm was reported as executed. Fixed in both script and artifact, with the reason recorded rather than quietly overwritten (`FINDINGS.md` F7). |
| **D5** | `audits/IMPL_CRITIC.md` finding 1 (**INVALIDATES-RESULTS**): the embedding cache key omitted `label`/`speaker_id`/`age`/`sex`, so a relabelled manifest got a cache hit with the **old** labels. | **Fixed** — `src/voicehealth/embed.py:_label_hashes` now puts labels inside the cache identity, and the docstring records the defect. Findings 2–6 and 8–10 remain **open**. |
| **D6** | `autoresearch_results/_quarantined/` (R11d) holds **zero retractions**. | Machinery installed and not yet needed. No result in this ledger has been withdrawn. |

---

## Runs that produced no artifact, and are therefore not rows

Listed so the ledger's silence is not mistaken for absence of work:

- Corpus acquisition (SVD 38.1 GB) and audio decode of 28,509 files — status tracked in
  `data/ACQUISITION_STATUS.md` and `data/PREPROCESSING_STATUS.md`, **not timed**.
- WavLM and eGeMAPS full-corpus extraction passes — the caches are `.gitignore`d and regenerable,
  and no wall-clock was recorded. Two **non-resumable** eGeMAPS extractions were killed at 74 %
  and 8.5 % and discarded everything, which is why `extract_egemaps_resumable.py` exists.
- COUGHVID embedding extraction — abandoned at ~8.5 %, deliberately, per D3.
- Every dashboard build (`scripts/build_*.py`) — writes `docs/`, not `autoresearch_results/`.

---

*Internal QA pass — independent external review pending (R16). Total recorded wall-clock across
E1–E10 is **25,880 s ≈ 7.19 h**, itemised per finding in `README.md` → Cost accounting.*
