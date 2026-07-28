# IMPL_CRITIC — correctness review of the voice-health harness

**Reviewer role:** implementation critic (correctness only; the science is reviewed separately in
`SCI_CRITIC.md`). Same-model-family agent.
**Date:** 2026-07-26
**Scope:** `src/voicehealth/{benchmark,embed,features}.py`, `scripts/run_benchmark.py`,
`scripts/audit_demographic_baseline.py`, `scripts/preprocess_audio.py` (interfaces only).
**Method:** static read plus recomputation of the affected quantities from
`data/interim/*/manifest.csv` and `autoresearch_results/bench_svd_egemaps.json`.
**Test suite:** `tests/` **exists but is empty** — `find tests -type f` returns nothing. There is no
rung-0 UNIT layer in this repository, despite `CLAUDE.md` §5 and `PREREGISTRATION.md` §12 both
requiring one as the gate to every later rung.

> **Internal QA pass — implementer and critic share a model family; independent external review
> pending.**

---

## Summary verdict

The harness is **better than most code of its kind**: the speaker-disjoint assertion is a hard
pre-fit gate with no bypass (`benchmark.py:61-75`, called again inside `_oof_predictions:393` and in
the confound loop at `:484`); the scaler is refitted per fold on train only (`:394`) and again in the
inner loop (`:416`); the ensemble selects its members from **train-only inner OOF AUC** (`:405-425`)
rather than test AUC; the calibrator uses group-aware inner folds (`:162-163`); the paired bootstrap
resamples **speakers**, not recordings (`:216-226`); and the classical-feature backend id is part of
the content hash so an openSMILE run and a librosa-fallback run can never collide
(`features.py:60-61, 214-228`). Those are the right decisions and several of them are unusual.

**One defect can silently invalidate a result** (embedding-cache key omits the labels), **five bias
a reported number**, and the rest are cosmetic. None of them explains away the executed SVD result
(`NOT CLEARED` for all five heads) — that verdict is, if anything, made *more* trustworthy by the
findings below, because two of the biases point in the direction of over-crediting the audio model.

| # | severity | file:line | issue |
|---|---|---|---|
| 1 | **INVALIDATES-RESULTS** | `embed.py:211-234`, `:289-311` | Embedding cache key omits `label`, `speaker_id`, `age`, `sex`; `from_npz` returns them from cache. A relabelled manifest gets a **cache hit and the old labels**. |
| 2 | **BIASES** | `benchmark.py:491-497` (+ `:109-111`) | A skipped fold leaves NaN predictions; `np.nan_to_num(p)` turns them into a **confident 0.0** in the pooled score, while `per_repeat` correctly masks them. Two different NaN policies in adjacent lines. |
| 3 | **BIASES** | `benchmark.py:308-311` | Age mean-imputation (`np.nanmean` over the **whole** bundle) is computed across train and test — a fit-on-all statistic inside the confound baseline the whole program is calibrated against. |
| 4 | **BIASES** | `benchmark.py:480-489` vs `:132-151` | The confound battery gets **one** model class (bare `LogisticRegression`, C=1, no sweep); the audio side gets 4 heads + an ensemble. The bar is handicapped relative to the thing it must bound. |
| 5 | **BIASES** | `benchmark.py:429-430`, `:185-194` | `ens_rank3` scores are within-fold **rank fractions**, not probabilities. `ece`, `accuracy` and `f1` are then computed on them at threshold 0.5 and tabulated next to real probabilities. |
| 6 | **BIASES** | `benchmark.py:173-182` vs `COMPOSITE.md:71-73` | ECE uses **equal-width** bins; the pinned spec says **15 equal-mass bins**. Direct spec/impl divergence on a term that enters the composite. |
| 7 | **BIASES** | `embed.py:202-208` | `_hf_revision` swallows every exception and returns the literal string `"unknown"` — **which is part of the cache key**. Two different model revisions extracted offline collide on one key. |
| 8 | BIASES (science) | `benchmark.py:524-525` | `best_audio_head` and `best_conf` are both selected by **pooled test AUC**. |
| 9 | BIASES | `features.py:103-107`, `:252` | A failed F0 track returns `jitter=shimmer=hnr=0.0`; `np.nan_to_num` then makes any failed feature a legitimate-looking 0.0. Silent failure that is itself potentially class-correlated. |
| 10 | BIASES | `benchmark.py:557-583` | Holm-Bonferroni is **never applied**; the Wilcoxon p is computed, stored, and never used in a verdict; `except Exception` returns a NaN p that passes silently. |
| 11 | COSMETIC | `audit_demographic_baseline.py:43`, `:57` | Missing metadata is silently coerced (`NaN & NaN -> healthy`; any non-`"w"` sex -> male). |
| 12 | COSMETIC | `embed.py:189-199` | `_source_file_hashes` sorts the digest list, so the key is row-order invariant. Self-consistent today (the npz carries its own order) but it means the key does not pin the row order it is paired with. |
| 13 | COSMETIC | `benchmark.py:206`, `:448` | `int(round(mean))` uses banker's rounding, so a 50/50 mixed-label speaker becomes negative. Zero mixed-label speakers exist today (verified), so latent only. |
| 14 | COSMETIC | `embed.py:332-338`, `:504-519` | Clips shorter than `min_seconds` are zero-padded and then `len(w)` (post-pad) is used to build the validity mask, so pad frames count as valid. |
| 15 | COSMETIC | `run_benchmark.py:159` | `RunResult.margins` is serialised under the key `margins_vs_confound`; any consumer reading `["margins"]` gets `None` silently. |

---

## Per-finding detail

### 1. INVALIDATES-RESULTS — the embedding cache key does not include the labels

`build_manifest_dict` (`embed.py:211-228`) builds the hashed payload from: `encoder_id`,
`encoder_key`, `encoder_revision`, `corpus_id`, `n_files`, `source_file_hashes`, `sample_rate`,
`pooling`, `PREPROCESS_POLICY`, `lib_versions`. `_source_file_hashes` (`:189-199`) hashes only the
**audio** digests.

`EmbeddingBundle.from_npz` (`:289-311`) then returns `labels`, `speaker_ids`, `sex`, `age`,
`duration_s`, `rms` **out of the cached `.npz`** and never compares them against the `rows` that were
just loaded from the manifest.

So: change a label definition, a speaker-id mapping, or an age column in
`data/interim/<corpus>/manifest.csv`, leave the audio untouched, re-run — you get
`[embed] cache hit` (`:459-462`) and **the run silently uses the previous labels**.

This is not hypothetical for this program. `PREREGISTRATION.md` §4 A2 pins a *label definition*
("pathology subset pinned to the full organic+functional set as distributed"), and
`data/interim/coswara/manifest.csv` carries a label set (`no_resp_illness_exposed`,
`resp_illness_not_identified`) that `DATA_SPLIT_AUDIT.md` §3 shows must be re-fetched. Both are
exactly the kind of edit that would produce a stale-label run with a valid-looking artifact,
a matching `embedding_content_hash`, and no warning.

**Fix (two lines, do both):**
```python
# in build_manifest_dict, alongside source_file_hashes:
"label_speaker_hash": hashlib.sha256(
    "\n".join(f'{r["recording_id"]}\x00{r["speaker_id"]}\x00{r.get("label","")}'
              f'\x00{r.get("age","")}\x00{r.get("sex","")}' for r in rows).encode()
).hexdigest(),
```
and, in `from_npz`'s caller, assert `np.array_equal(bundle.recording_ids, [r["recording_id"] for r in rows])`
before use. The second check alone would have caught it.

### 2. BIASES — two different NaN policies, three lines apart

```python
# benchmark.py:491-497
for name, p in rep_preds.items():
    m = ~np.isnan(p)
    per_repeat[name].append(float(roc_auc_score(y[m], p[m])) ...)   # masks NaN  <-- correct
    pooled.setdefault(name, np.zeros(len(y)))
    pooled[name] += np.nan_to_num(p) / cfg.n_repeats                # NaN -> 0.0 <-- wrong
```

A recording gets `NaN` when its fold was dropped by `stratified_group_folds`:

```python
# benchmark.py:109-111
if test_idx.size == 0 or len(np.unique(y[train_idx])) < 2:
    continue          # those test recordings are never predicted this repeat
```

`np.nan_to_num` then records them as **p = 0.0**, i.e. maximally confident negative, in *every*
downstream number: `score_all`, the pooled AUC, the ECE, the bootstrap CI, the margin, the verdict.
If the dropped speakers are positive the AUC is depressed; if negative it is inflated. Either way
the artifact reports a number that was never predicted.

**Did it fire on the executed SVD run?** No — 49 speakers over 5 folds always leaves both classes in
train; `per_repeat_auc` in `bench_svd_egemaps.json` contains no NaN. **It is primed to fire on
Coswara**, where `DATA_SPLIT_AUDIT.md` §3 measures 9 positive speakers of 72: a 5-fold partition
regularly produces a fold whose train side is single-class.

**Fix:** accumulate a per-index count of non-NaN contributions and divide by it, or raise if any
fold is dropped. Silently dropping a fold is the more serious half of this bug.

### 3. BIASES — the confound baseline imputes age using test-fold data

```python
# benchmark.py:310
age = np.nan_to_num(bundle.age.astype(np.float64), nan=float(np.nanmean(bundle.age)))
```

`confound_matrix` is called **once per repeat, outside the fold loop** (`:481`), so the imputation
constant is the grand mean over train **and** test. The module docstring at `:12-16` states the
opposite guarantee — *"Every fitted object is fit per fold on TRAIN ONLY -- scaler, head,
calibrator..."* — and cites the Applied Soft Computing leakage measurement to argue that "it's only
a small effect" is not defensible. An imputation constant is a fitted object.

Impact today is small: age missingness is **0.0 % on SVD and Coswara** and 4.8 % on COUGHVID
(measured). But V6 (`IDEA_TABLE.md`) is a hypothesis *about exactly this class of leakage*, so
running it with a fit-on-all imputation inside the comparator is self-defeating. Also note
`np.nanmean` on an all-NaN age column emits a RuntimeWarning and returns NaN, which then propagates
into the design matrix as NaN and makes `LogisticRegression.fit` raise — a loud failure, which is
the correct behaviour, but it is unguarded.

### 4. BIASES — asymmetric model capacity between the audio arm and the bar

The audio arm gets `logreg`, `linsvm` (Platt-calibrated), `mlp(256)`, `gbt` (200 boosting rounds),
plus a rank-average ensemble (`benchmark.py:132-151`, `:466`). The confound arm gets one bare
`LogisticRegression(max_iter=5000)` (`:486`) on 1-4 raw columns.

Logistic regression on age is **monotone in age**. The SVD age-pathology relationship is not
monotone (measured: pathological ages span 6-89 with sd 22.3 and a bimodal young/old structure;
healthy span 19-68 with sd 16.0). A `HistGradientBoostingClassifier` on the same age column would
almost certainly exceed the 0.7027 the logistic bar achieves, which would shrink every reported
margin. The comparison as built systematically **over-credits the audio model**.

Note this cuts the same way as finding 8 and against the current SVD verdict: the harness reported
`NOT CLEARED` for all five heads **despite** both biases favouring the audio arm. That strengthens
the negative result rather than weakening it.

**Fix:** run the confound battery through the identical `heads` tuple and take the max, exactly as
the audio arm does.

### 5. BIASES — the ensemble's calibration metrics are meaningless

```python
# benchmark.py:429-430
ranks = [stats.rankdata(fold_test[h]) / len(test_idx) for h in members]
preds[ENSEMBLE_NAME][test_idx] = np.mean(ranks, axis=0)
```

These are within-fold rank fractions in (0, 1]. They are a valid **ranking** (AUC is fine) and an
invalid **probability**. `score_all` (`:185-194`) then computes `accuracy`, `f1` at threshold 0.5 and
`ece` on them, and `run_benchmark.py:187-194` prints the ECE column with no distinction. In
`bench_svd_egemaps.json` `ens_rank3` carries `ece = 0.1242` (recording) / `0.1860` (speaker) — those
numbers should not exist. There is a second-order issue too: ranks are normalised **within a fold**,
so pooling them across folds with different positive rates mixes incommensurate scales.

**Fix:** emit `ece: null` for rank-based scores, or convert with an in-fold isotonic/Platt map fitted
on train only.

### 6. BIASES — ECE binning contradicts the pinned specification

`benchmark.py:174` `edges = np.linspace(0.0, 1.0, n_bins + 1)` — **equal-width**.
`COMPOSITE.md` §2 term definitions: *"`ECE` — expected calibration error, **15 equal-mass bins**"*.

Equal-width binning on a skewed score distribution concentrates most samples in one or two bins and
systematically **under-reports** ECE. Since `lambda_cal = 0.5` prices ECE directly into the
composite, the implementation and the fingerprinted specification disagree on a priced term. The
fingerprint `37e745ed9b0b` covers the *specification*, so this divergence is invisible to the
fingerprint check — and the fingerprint check does not exist yet either (see `SCI_CRITIC.md` §4).

### 7. BIASES — a swallowed exception becomes part of the cache key

```python
# embed.py:202-208
def _hf_revision(hf_id):
    try:
        return str(model_info(hf_id).sha)
    except Exception:
        return "unknown"          # <-- lands inside content_hash()
```

Two failure modes, both silent:
- **Online vs offline produce different keys** for byte-identical embeddings (revision SHA vs
  `"unknown"`), causing a spurious re-extraction and two `.npz` files that provenance treats as
  distinct artifacts.
- **Worse:** two *genuinely different* model revisions both extracted offline hash to
  `"unknown"` and **collide**. The second run gets a cache hit and silently uses the first
  revision's embeddings, while `R15` (determinism envelope) reports a clean provenance record.

The `bench_svd_egemaps.json` run used `--backbone egemaps`, whose revision is
`opensmile-python 2.6.0` and is resolved locally, so the executed result is unaffected. Every
`wavlm`/`whisper`/`hear` run will be exposed.

**Fix:** fall back to the locally resolved snapshot commit (`huggingface_hub.snapshot_download`'s
returned path / `refs/main`), and if genuinely unresolvable, **raise** rather than hash a placeholder.

### 8. BIASES — best head and best bar are chosen on test AUC

```python
# benchmark.py:524-525
best_conf  = max(confound_names, key=lambda n: rec[n]["roc_auc"])
best_audio = max(audio_names,    key=lambda n: rec[n]["roc_auc"])
```

Both maxima are taken over the pooled **test** predictions.

- `best_audio` is a winner's-curse selection. It only affects the `margins.best_audio_head` label
  (verdicts are emitted per head at `:572-583`), so the damage is presentational — but the field
  that a reader's eye lands on is the peeked one.
- `best_conf` is selection-over-6 on the same data, and the paired bootstrap CI at `:536-553` does
  **not** account for that selection. Here the direction is *conservative*: choosing the maximum
  confound shrinks every delta, making `cleared_confound_bar` harder to earn. That is the right way
  to be wrong, and it should be said out loud in the artifact rather than left implicit.

### 9. BIASES — silent zeros in the classical feature backend

`features.py:103-107`: if fewer than 3 voiced frames are found, `_jitter_shimmer_hnr` returns
`{"jitter_local": 0.0, "shimmer_local": 0.0, "hnr_db": 0.0}`. `features.py:252`:
`X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)`.

A recording on which pYIN fails completely therefore produces a feature vector that is
indistinguishable from a genuine measurement of zero jitter, zero shimmer and 0 dB HNR. If F0
tracking fails more often on pathological (breathy, aperiodic, diplophonic) voices than on healthy
ones — which is the clinically expected direction — **the failure indicator itself becomes the
discriminative feature**, and the model learns "pYIN could not track this" rather than any voice
property.

The executed `bench_svd_egemaps.json` used the **openSMILE** backend
(`"is_real_egemaps": true`, `opensmile-python 2.6.0`), so this path did not run. It will run on any
host without `opensmile` installed, and `backend_id()` switches **silently** on import availability
(`features.py:60-61`) — correctly recorded in the artifact, but not surfaced to the operator.

**Fix:** carry an explicit `n_features_imputed` / `f0_track_failed` column into the bundle, report it
by class, and treat a class-imbalanced failure rate as a blocking data-quality finding.

### 10. BIASES — the statistical contract is computed but not enforced

`power_check` (`:285-300`) computes Holm's tightest threshold `0.05/m` and reports `feasible`.
`stats.wilcoxon` runs at `:558`. **Neither is used in any verdict.** The verdict at `:572-583` is
decided solely by `rec_delta["lo"] > 0 and spk_delta["lo"] > 0`. Holm-Bonferroni is applied
**nowhere in the repository** (grep: no `holm` outside `power_check`'s label string).

`PREREGISTRATION.md` §7 and `IDEA_TABLE.md` both pre-register the rule *"the Wilcoxon p and a
speaker-level cluster-bootstrap interval, and the more conservative binds the verdict."* The code
implements only one of the two and lets the other bind nothing.

The `except Exception` at `:560` compounds this: a degenerate Wilcoxon returns
`{"p_value": nan, "error": ...}` and no code path notices. In the executed run this masked an
interesting fact — `gbt`'s Wilcoxon is `statistic = 0.0, p = 0.001953`, the **minimum attainable**
p, because `gbt` lost to the age bar in **all 10 of 10** repeats. A two-sided p of 0.002 stored
next to `"cleared_confound_bar": false` is a significant result **in the wrong direction**, and the
artifact does not say so.

### 11-15. Cosmetic

- **11.** `audit_demographic_baseline.py:43` `df["healthy"] = df["Pathologien"].isna() & df["Diagnose"].isna()`
  labels a session with *missing* pathology metadata as healthy. `:57`
  `sex = (d["Geschlecht"] == "w")` maps NaN and any unexpected coding to male. Both silently absorb
  data-quality problems into the labels of the program's headline F1 number. Neither is
  count-checked in the artifact.
- **12.** `_source_file_hashes` (`embed.py:198`) hashes `"\n".join(sorted(digests))`, so the key is
  invariant to row order. `from_npz` returns the full bundle from cache so there is no live
  misalignment, but the key does not pin the ordering it was created with, which is the kind of
  invariant a `data-contract-validator` gate exists to hold.
- **13.** `aggregate_to_speaker` (`:206`) and the dataset census (`:448`) use `int(round(...))`;
  Python's round-half-to-even sends a 50/50 speaker to class 0. Verified: **0 mixed-label speakers
  in all three corpora**, so latent.
- **14.** `load_audio` (`:332-338`) crops to 30 s then zero-pads to 0.5 s minimum, and the caller
  (`:509-519`) builds the frame mask from the **post-pad** length, so padded silence is pooled as
  valid signal. Only affects clips under 0.5 s (SVD minimum measured: 0.32 s — so this **does** fire
  on SVD).
- **15.** `run_benchmark.py:159` writes `result.margins` under the key `margins_vs_confound`. Any
  reader doing `payload["margins"]` gets `None` with no error. Confirmed against the shipped
  artifact.

---

## Does any of this invalidate the one executed result?

`autoresearch_results/bench_svd_egemaps.json` — SVD, openSMILE eGeMAPSv02, 5 folds x 10 repeats,
667 recordings / 49 speakers, verdict **`NOT CLEARED` for all of logreg, linsvm, mlp, gbt,
ens_rank3**.

**No.** Findings 1, 2, 7 and 9 did not fire on this run (openSMILE backend, locally resolved
revision, no dropped folds, no relabelling). Findings 3 and 4 and 8 all bias in favour of the audio
arm, and the audio arm still lost: best speaker-level audio AUC 0.7983 (`gbt`) against an age-only
bar of 0.7086, with a paired speaker-level delta CI of **[-0.076, +0.264]** that includes zero, and a
recording-level delta of **-0.012**, CI [-0.159, +0.151]. Finding 6 (ECE binning) affects only the
ECE column, which is reported and not yet composited.

The result that **is** compromised is the *reporting* around it: the ECE column for `ens_rank3` is
not a calibration measurement (5), the confound bar is handicapped (4), the Wilcoxon result pointing
the other way is not surfaced (10), and the "0.871 age bar" quoted in the module docstring
(`benchmark.py:6`) is measured on a different population than the run
(`DATA_SPLIT_AUDIT.md` §4).

---

## Prioritized fix list

1. **[BLOCKER]** Add the label/speaker/demographic digest to the embedding cache key and assert
   `recording_ids` alignment on every cache hit (finding 1).
2. **[BLOCKER]** Create `tests/` content. There is no rung-0 UNIT layer at all, so
   `CLAUDE.md` §5's "never spend rung k+1 compute before rung k's gate is cleared" is currently
   unenforceable — and the one rung-3-shaped run in the repo was executed with zero passing rung-0
   gates beneath it, which is verbatim the sibling-program failure `CLAUDE.md` §9 exists to prevent.
3. **[MAJOR]** Fix the NaN pooling policy and make a dropped fold raise, not `continue` (2).
4. **[MAJOR]** Move age imputation inside the fold and fit it on train only (3).
5. **[MAJOR]** Run the confound battery through the same head family as the audio arm (4).
6. **[MAJOR]** Implement Holm across the declared family and let the more conservative of
   {Wilcoxon, cluster bootstrap} bind the verdict, as pre-registered (10).
7. **[MINOR]** Equal-mass ECE bins to match `COMPOSITE.md` (6); `ece: null` for rank scores (5);
   raise instead of `"unknown"` in `_hf_revision` (7); surface the selection-on-test caveat (8);
   count and report feature-imputation failures by class (9).

---

*Internal QA pass — implementer and critic share a model family; independent external review
pending. Line references are to the files as of 2026-07-26; every measured number was recomputed
from the manifests or read out of `autoresearch_results/bench_svd_egemaps.json`.*

---

> **Internal QA pass — implementer and critic share a model family; independent external review pending.**

---

# Addendum 2026-07-28 — `run_v2_speaker_subspace.py`

The program's first experiment against a registered hypothesis. Audited **during**
implementation rather than after, which is why three defects were caught before any
result was reported. All three were mine.

## D1 — the control was not variance-matched (CORRECTNESS, would have inflated the finding)

`variance_matched_random()` drew 400 uniformly-random k-subsets of the principal
directions and kept the closest match to the speaker subspace's captured variance.
That cannot work: a random 16-of-1536 draw essentially never includes the top
directions, so the best draw reached **0.350** of the variance against the speaker
subspace's **0.818**.

The comparison was therefore between two *different-sized* interventions — remove 82%
of the variance one way, 35% the other — and could not separate "identity was removed"
from "more signal was removed". Measured cost of the defect: `D(16)` read **+0.132**
with the broken control and **+0.070 / +0.075** with correct ones, an inflation of
~1.8×. Had this shipped, the headline would have been nearly double its true size.

**Fixed** with two controls built from the data's own principal axes: `pca_topk` (the
variance-*maximising* rank-k subspace — 0.879 at k=16, i.e. strictly *more* than the
speaker subspace, so a positive D cannot be a variance artifact) and `var_matched`
(top-k with the lowest member walked down the spectrum onto the target). Both are
reported so the claim survives whichever control a reader trusts.

## D2 — the manipulation check could not check anything (VALIDITY, unresolved)

The pre-registered check was "speaker-ID accuracy falls from ~0.90 to < 0.30". Measured
on unprojected embeddings it was **0.204** — a number with no room to fall, so its drop
demonstrated nothing.

Cause: a 150-way task over speakers with ≥4 recordings starves the probe. Narrowing to
60-way over speakers with ≥12 recordings raised it to **0.278** (chance 0.0167).

**This remains a genuine weakness, not a closed issue.** 0.278 is 16.7× chance, so
identity *is* linearly present, but it is nowhere near the predicted 0.90. The
prediction assumed mean-pooled WavLM-base+ separates speakers like an x-vector; it does
not. Consequence for the finding: the projection demonstrably removes *some* identity,
but the claim "the subspace removed is the identity subspace" is supported only weakly,
and any write-up must say so in the body rather than a footnote.

## D3 — the speaker basis was recomputed per rank (PERFORMANCE, no correctness impact)

The speaker-mean matrix and its SVD are rank-independent; only the `Vt[:k]` slice
varies. `speaker_subspace()` rebuilt both on every call, once per rank. Measured at
1.2 s + 10.7 s ≈ 12 s per call, so ~6 redundant calls × 10 repeats ≈ 13 minutes wasted.
Now cached per (matrix, split). The dominant cost — 21 `auc_cv` calls per repeat — is
inherent to the design and unchanged.

## What is verified

- **Leakage.** Every subspace, speaker and control alike, is estimated on *training
  speakers only*, inside the repeat's 80% speaker split. Estimating on all data would
  leak test speakers into the projection meant to remove them. Scalers are fit per fold
  on train only. Splits are `GroupKFold` on `speaker_id` throughout.
- **Family size.** `FAMILY_M = 14` is the pre-registered value and is used even though
  only SVD runs (a post-hoc m=7 would be easier to clear). Shrinking m after the fact is
  the move the contract forbids.
- **Judge-free.** The objective is ROC-AUC against ground-truth clinical labels; no
  model grades any output, so the failed judge calibration is irrelevant here.

## What is NOT verified

- **No shuffle test.** The pipeline has not been run with permuted labels to confirm it
  returns AUC ≈ 0.5. Until it is, a systematic bug that inflates every arm equally would
  be invisible — `D` is a *difference*, so it would survive such a bug unnoticed. This is
  the highest-value missing control and should precede any external claim.
- **SVD only.** The pre-registration names SVD *and* Coswara. Coswara has not been run,
  so half the registered family is unexecuted.
- **Single backbone, single head.** WavLM mean+std pooling with logistic regression. The
  result may not transfer to other representations, which is exactly what
  arXiv:2604.14354 claims is a property of representations in general.

---

> **Internal QA pass — implementer and critic share a model family; independent external
> review pending.** This addendum audits code the same author wrote, in the same session.
