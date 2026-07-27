# SCI_CRITIC — adversarial review of the science

**Reviewer role:** scientific critic, adversarial by mandate (same-model-family agent).
**Date:** 2026-07-26
**Scope:** `FINDINGS.md` (F1), `PREREGISTRATION.md` (V2), `IDEA_TABLE.md` (V1-V7), `COMPOSITE.md`
(VOICE_AUDIT_COMPOSITE v1.0.0), checked against `CLAUDE.md`, the acquired manifests, and the one
executed run `autoresearch_results/bench_svd_egemaps.json`.
**Method:** every claim below is anchored to a file/line or to a number this audit computed. The
composite fingerprint and the §5 degenerate table were **re-executed**, not read.

> **Internal QA pass — implementer and critic share a model family; independent external review
> pending.**

---

## Summary verdict

This is an unusually disciplined program on paper. Three things are genuinely right and should be
protected: **(i)** every row of `IDEA_TABLE.md` is `UNTESTED`, with the explicit refusal to
call an unexecuted falsifier `SUPPORTED`; **(ii)** V2's falsifier is **two-sided**, so the null is
publishable at equal standing, which removes the incentive that produces most of this field's
literature; **(iii)** the composite fingerprint **reproduces exactly** and the degenerate-row table
**re-executes to 4 dp on all 8 rows** — I checked both, and they are correct.

The problem is not honesty. It is that **the plans have not been reconciled against the data that
was actually acquired**, and that **the two heaviest penalty terms in the composite cannot fire on
the corpora in hand**.

| question the lead asked | verdict |
|---|---|
| Is F1 correctly stated and correctly caveated? | **Arithmetic correct; caveats incomplete.** The 0.871 is measured on a different population (1,853 speakers) than the one it is quoted against (49 speakers, where age-only is **0.741**). No CI. Two numbers in the prose have no artifact. |
| Does `PREREGISTRATION.md` fix everything before a run? | **Metrics/splits/controls/n/tests/abandonment: all fixed — better than most.** But its pinned A2 makes its own §6 instrument gate **unexecutable**, and 7 of its 14 confirmatory cells sit on a corpus with **zero positive labels acquired**. |
| Does `IDEA_TABLE.md` contain a verdict outrunning its evidence? | **No verdict does** — every row is `UNTESTED`. **Several plans do**: V2 claims 2,043 SVD speakers (49 acquired); six of seven rows list COUGHVID under `A3 = speaker_disjoint`, which is impossible there. |
| Is the composite Goodhart-resistant, and does the degenerate demo actually lose? | **The demo reproduces exactly — all 8 rows.** But `lambda_sub` (0.75) is **structurally inert on SVD**, `lambda_ctrl` (3.00) self-weakens with pipeline noise, and the whole formula is **implemented nowhere** — `src/voiceaudit/composite.py` does not exist, so the fingerprint is asserted at no import time. |

---

## 1. F1 — "on SVD, age alone reaches ROC-AUC 0.871"

### What is right

The number is real and reproducible. `scripts/audit_demographic_baseline.py` runs on CPU in
seconds, writes a checksummed artifact (`artifact_md5 2ee9852a...`), and the speaker-disjoint
age+sex figure (0.8768) is computed with `GroupKFold` on `SprecherID`
(`audit_demographic_baseline.py:64-68`) rather than a random split. The "What this does NOT claim"
section is genuinely good: it separates UAR from AUC, refuses to say any published result is wrong,
and states that the claim is about **attribution**, not about whether voice carries pathology
signal. That is the correct framing and it is rare.

### What is wrong or missing

**(a) Population mismatch — the most consequential omission.** 0.871 is computed on the full SVD
session metadata: **2,225 sessions / 1,853 speakers**. The program's actual experimental corpus is
`data/interim/svd/manifest.csv`: **667 recordings / 49 speakers**. On *that* population this audit
measures age-only AUC = **0.7362 (recording) / 0.7414 (speaker)**, and the harness's own fitted
`confound::age_only` lands at **0.7027 / 0.7086**. The gap is ~0.13-0.17 AUC.

`src/voicehealth/benchmark.py:6` hardcodes the mismatched figure into the module that enforces the
bar: *"F1: on SVD, age alone reaches AUC 0.871."* Any sentence of the form "the audio model must
clear 0.877" is quoting a bar derived from 1,853 speakers and applying it to 49. F1's caveat list
covers UAR-vs-AUC and researcher blame; it does not mention that the two numbers describe different
samples. **Fix: state both, and quote the 49-speaker figure wherever the benchmark is discussed.**

**(b) No uncertainty on the headline number.** F1 reports 0.8709 and 0.8768 to four decimals with
**no CI**, on 2,225 sessions of which 200 speakers contribute up to 24 sessions each
(`F1_demographic_baseline.json`: `speakers_with_multiple_sessions: 200`,
`max_sessions_per_speaker: 24`). A marginal AUC over correlated sessions has an effective n well
below 2,225, and the correct interval is a speaker-cluster bootstrap. `CLAUDE.md` R6 and the
program's own rigor contract require intervals; the program's flagship finding does not have one.

**(c) Two orphan numbers (R1).** F1's table gives `sd 11.6` (healthy) and `sd 15.8` (pathological).
`F1_demographic_baseline.json` contains `mean_age_healthy` and `mean_age_pathological` and **no sd
fields**. Under R1 ("no orphan numbers — artifact provenance") those two values must either be added
to the artifact or removed from the finding.

**(d) A causal word doing unearned work.** "*Underlying cause* — a recruitment asymmetry" is a
causal claim from a cross-sectional association. The evidence supports it and the mechanism is
plausible, but the honest phrasing is "consistent with a recruitment asymmetry".

**(e) Sex is a live confound and is not caveated.** This audit measures sex-only AUC = **0.6308
(recording) / 0.6336 (speaker)** on the interim SVD, driven by pathological 75 % M vs healthy 49 % M.
F1 reports sex-only = 0.5172 on the full metadata and reads it as null. On the corpus the benchmark
runs, it is not null.

**Verdict on F1: `CORRECTLY MEASURED, INCOMPLETELY CAVEATED`.** No retraction is warranted; three
sentences of scope and one CI would fix it.

---

## 2. `PREREGISTRATION.md` — does it fix everything a run needs?

### The checklist, honestly scored

| must be fixed before the run | fixed? | where |
|---|---|---|
| primary metric | YES | §3: `D(k) = AUC_rand(k) - AUC_spk(k)`, headline cell k*=16 / WavLM / SVD declared in advance |
| secondary metrics | YES | §3 table (9 metrics, each with a reason) |
| splits | YES | §4 A3: speaker-disjoint, sex-stratified, 10 partitions, seeds 0-9, assertion before every fit |
| preprocessing scope | YES | §4 A4: `fit_per_fold` for scaler, subspace, PCA, probe, calibrator |
| controls | YES | §5: six, all required, none optional — including a class-direction positive control (C4) and a leaky reference (C6) |
| instrument validation | YES in principle | §6 manipulation check with a numeric gate (>=60 % relative drop in speaker-ID top-1 at k=16) |
| n and multiplicity | YES | §7: n=10, m=14, with the R6 arithmetic shown |
| statistical tests | YES | §8: Wilcoxon + BCa cluster bootstrap + Holm + empirical noise band + an ordinal gate |
| abandonment criterion | YES | §11: five named conditions, each with a logged verdict |
| outcome table fixed in advance | YES | §9 — the interpretation column is written before the data |
| protocol-amendment mechanism | YES | §14 |

**This is a more complete pre-registration than the field norm.** §9 in particular — fixing the
*interpretation* of every possible outcome in advance — closes the HARKing route properly, and §11's
"abandoned, not quietly re-scoped" is the right standard.

### The four defects

**(1) The pinned A2 makes the §6 instrument gate unexecutable — BLOCKER.**

§4 A2 pins SVD to *"sustained vowel /a/ at normal pitch only, one session per speaker."* That is the
manifest's `task == "a_n"`. This audit measures it: **49 rows, 49 speakers, exactly 1 recording per
speaker.**

Consequences, all mechanical:
- §4 A11 `speaker_level(mean_prob)` is a mean over one element — a no-op, and the
  recording/speaker distinction the whole program rests on collapses.
- **§6 cannot run.** It requires closed-set speaker identification *"using a held-out slice of their
  own recordings that is disjoint from the disease-evaluation partition."* With one recording per
  speaker there is no such slice. §6 is the R3 instrument gate; §11 condition 2 abandons V2 if it
  fails at every k. As written it cannot pass or fail — it cannot be attempted.
- §4.1 step 4 builds `S_B = sum_s n_s * nu_s nu_s^T` with `n_s = 1`, i.e. the within-class scatter of
  49 points. Its rank is at most 47, so of the seven pinned ranks **k=64 is unrunnable** and **k=32
  removes 32 of at most 47 available directions** of the entire data manifold. Two of the seven ranks
  are structurally degenerate, and m=14 was declared on the assumption all seven are live.
- §4.1's orthogonality gate (`max_j |cos(U_k[:,j], w)| < 0.10` in 768 dimensions with 49 samples) is
  a demanding requirement in a regime where the empirical within-class scatter spans nearly the whole
  sample space. §11 condition 1 then abandons the hypothesis as `UNFALSIFIABLE on this data` — which
  is a logged verdict, so the machinery is honest; but the pre-registration should say *now* that
  this is the likely outcome at n=49, not discover it after the run.

**Fix:** either widen A2 to all 14 SVD vocalisation tasks (13.6 recordings/speaker, measured) and
re-derive the m/n arithmetic, or enlarge the SVD slice. Both are §14 amendments.

**(2) Seven of the fourteen confirmatory cells sit on a corpus with zero acquired positives —
BLOCKER.** §4 A2 pins Coswara to `covid_positive vs covid_negative`. `data/interim/coswara/manifest.csv`
contains **no `positive_*` label at all** (measured: `healthy 529 / no_resp_illness_exposed 45 /
resp_illness_not_identified 36`). The corpus metadata does hold 681 positives
(`autoresearch_results/acquisition/coswara_meta_stats.json`), so this is a shortfall of the
72-participant slice that was downloaded. **m = 14 is not currently achievable; the runnable family
is m = 7.** See `DATA_SPLIT_AUDIT.md` §3.

**(3) The R6 power check cannot fail, so it is decorative.** §7's arithmetic
(`2/2^n <= 0.05/m`) treats `n` as the number of *re-partitions of the same 49 speakers*. `n` is a
free parameter of the resampling loop — raise `--repeats` and R6 passes. The binding quantity is the
speaker pool, which R6 never touches. §7 pre-registers the correlation caveat honestly ("Wilcoxon
over them is anti-conservative... the more conservative binds the verdict"), which is the right
instinct; but the check that the runner *enforces* is the one that cannot fail. Meanwhile
`benchmark.py:572-583` implements neither the Wilcoxon binding nor Holm at all
(`IMPL_CRITIC.md` finding 10) — so the conservative-binds rule exists only in prose.

**(4) §11 condition 5 compares incommensurable units, and §11 condition 3 is near-certain to fire.**
Condition 5 abandons V2 as `NOT_REPRODUCIBLE` if *"`AUC_full` cannot be brought within 0.05 AUC of
SVD's published reference"* — the published reference is **UAR 85.22**, and `FINDINGS.md` itself
states that UAR and AUC "are different metrics and are not directly comparable." An abandonment
criterion stated in the wrong unit is not a criterion. Condition 3 abandons if the 2-sigma seed band
on `D(k)` exceeds 0.10 AUC; the executed run's speaker-level bootstrap CIs on this corpus are
**0.26 AUC wide** (e.g. `gbt` [0.663, 0.925]), so the abandonment condition should be expected to
fire, and the pre-registration should say so.

**(5) Freeze-rule accountability gap.** The header declares *"FROZEN-PENDING-COMMIT — no data has
been touched."* `bench_svd_egemaps.json` (generated `2026-07-25T23:55:48Z`) ran the SVD corpus
through a 5-fold x 10-repeat pipeline using **all 14 tasks**, not `a_n` only. The defensible reading
is that the benchmark-harness run is not the V2 experiment — but nothing in the repository says
which, because **`autoresearch_results/experiment_log.jsonl`, `best_config.json`, `JUDGE_CARD.md`
and `EXPERIMENT_LEDGER.md` are all MISSING** (verified), and `PREREGISTRATION.md` §13's mandated
`autoresearch_results/runs/V2-<rung>-<config_hash>/` directory does not exist. `CLAUDE.md` §6 lists
all four as state files. The one executed run therefore has **no ledger row, no reasoning entry and
no rung classification** — which is the precise accounting failure R1/R2 exist to prevent.

---

## 3. `IDEA_TABLE.md` — does any verdict outrun its evidence?

**No verdict does, and that is a real achievement.** Every row is `UNTESTED`; the header states the
rule explicitly and names the sibling program's six unexecuted-falsifier `SUPPORTED` verdicts as the
thing being avoided. The "Predicted Δ" column is labelled as pre-registration, not measurement, in
the footer. Do not weaken this.

**But five plan-level claims outrun the acquired data**, and the summary table's `satisfiable ✓`
column presents them as sound:

| # | claim in `IDEA_TABLE.md` | measured reality |
|---|---|---|
| 1 | V2 "Datasets: SVD (>=2 vocalisations/speaker, **2,043 speakers**)" | **49 speakers** acquired |
| 2 | V2 "Coswara (9 streams/participant)" for 7 of 14 cells | 72 participants, **9 positive speakers**, and **0** under the pre-registered label |
| 3 | V1, V3, V4, V5, V6, V7 all list **COUGHVID** under `A3 = speaker_disjoint` | COUGHVID `speaker_id` is a **recording UUID** (`recording_proxy`, 13,535/13,535); a speaker-disjoint split is unverifiable there. `PREREGISTRATION.md` §4 already excludes it for V2 — the registry was never updated to match |
| 4 | V1 falsifier requires `A3 = speaker_disjoint + demographically_matched` on >=2 of 3 corpora | On SVD only **9** healthy/pathological speaker pairs match within ±5 y (18 of 49 speakers). The falsifier is not executable as written |
| 5 | Summary table: "**Every plan in this table is arithmetically satisfiable under R6**" | True of the `(m, n)` arithmetic, and uninformative — see §2(3). No row checks `n` against the acquired **speaker** counts, which is the quantity that binds |

The registry's own remedy is already written into it — *"the runner must recompute `2/2^n <= 0.05/m`
at launch... a rule that is checked only in a markdown table is the 'decorative rigor' failure
mode."* The same sentence should be applied to the dataset column: **a dataset claimed only in a
markdown table is decorative provenance.** Add a launch-time assertion that the acquired manifest
contains the pinned labels and at least the declared speaker counts.

---

## 4. `COMPOSITE.md` — is it Goodhart-resistant, and does the degenerate row actually lose?

### What I verified by re-execution

**Fingerprint: PASS.** I canonicalised the §6 spec dict verbatim and hashed it:
`37e745ed9b0bb4bd8803b16a2cdb3448611bdbebdebdbcb4dccf1d1f2db7da9a` — **exact match** to the pinned
value. The canonical string in §6 is byte-accurate.

**Degenerate table: PASS.** I re-executed the §2 formula at the §2 pinned lambdas on the §5 inputs.
**All 8 rows reproduce to 4 decimal places**, term by term (M, disc, cal, sub, xc, leak, ctrl,
composite). Every degenerate does lose to both honest rows. The three headline observations in the
prose (D3 has the highest AUC and the highest raw margin and still scores negative; D6 the do-nothing
null beats D1/D2/D7; D6 still loses to R1) are all true as computed.

**Monotonicity proof: PASS.** `d(composite)/d(AUC_honest) = +1 (M) + l_leak - l_sub - l_xc = +0.65`
is correct in the stated worst case where all three penalties are simultaneously active, and the
omitted `disc` term only adds. There is no perverse incentive to under-fit.

### Where the composite is not as strong as the document claims

**(a) `lambda_sub` — the second-heaviest weight — is structurally inert on the primary corpus.**
`min_subgroup_n = 30`; subgroups below it are excluded from `AUC_subgroup_min`. §1 mandates
speaker-level as the honest unit. Measured speaker-level sex counts:

| corpus | M speakers | F speakers | eligible at n>=30 |
|---|---|---|---|
| **SVD** | **29** | **20** | **neither** |
| Coswara | 57 | 15 | male only |

On SVD, **no sex subgroup qualifies**, so the subgroup tax has nothing to minimise over. On Coswara
the only eligible subgroup is the *majority* group, so `AUC_subgroup_min` measures the best case, not
the worst — the term inverts its own purpose. `CLAUDE.md` §7 calls subgroup collapse "a finding, not
a footnote"; at λ_sub = 0.75 it is priced accordingly and then cannot fire.

Under §4's null policy the honest consequence is sharper than inertness: at rung 3
`AUC_subgroup_min` is a **required** term, so **no rung-3 composite is computable on SVD as
acquired** — the composite is `null`, and a `null` composite "may never enter a ranking, a Pareto
plot, a promotion decision, or FINDINGS.md." That is the null policy working as designed, and it
means the program cannot currently produce a composited row at all. This should be stated in
`COMPOSITE.md` rather than discovered at rung 3.

**(b) `lambda_ctrl` self-weakens exactly when it is most needed.** The negative-control term is
`l_ctrl * max(0, AUC_negctrl - 0.5 - 2*sigma_null)` with `sigma_null` **measured by the same
pipeline**. A noisier pipeline earns a wider free band. On 49 speakers the measured speaker-level
bootstrap half-widths are ~0.13 AUC, so a shuffled-label AUC of up to roughly **0.63 would incur no
penalty at all**. The term the document calls "near-fatal by design" is, on the corpora in hand,
close to unreachable. **Fix:** floor `sigma_null` (e.g. `max(sigma_null, 0.02)`), or make the band a
fixed constant and report the measured noise separately as its own axis. As written, the incentive
gradient points toward a noisier estimator.

**(c) The §5 attribution for D2 is imprecise on the row the document says matters most.** The prose
says D2 *"loses by 0.265 composite, **entirely** because its confound baseline is at 0.84."*
Decomposing R0 − D2 = 0.265 (computed): the margin term contributes **0.230**, the cross-corpus term
**+0.090**, the leak term **−0.050**, calibration **−0.005**. The confound is 87 % of the gap, not
all of it. Replace "entirely" with the decomposition.

**(d) The demonstration is a hand-chosen set, not a search.** Six degenerates losing shows that six
specific attacks fail. It does not show that no degenerate wins. The stated rung-0 test
(`scripts/composite_degenerate_check.py`) should be extended to a bounded **maximisation**: search
the input box for the highest-composite row subject to `M <= 0.02` (no honest margin), and report the
worst case found. That is the falsifiable version of "Goodhart-resistant".

**(e) The whole formula is implemented nowhere.** §6 specifies
`src/voiceaudit/composite.py` exporting `SPEC`, `FINGERPRINT`, `composite(row)`, `fingerprint()`,
and says *"Assert the result equals the pinned value at import time. A mismatch raises and **halts
the runner** — it does not warn."* Verified: **`src/voiceaudit/` does not exist**, and neither does
`scripts/composite_degenerate_check.py`. `src/` contains only `voicehealth/{benchmark,embed,features}.py`.
So:
- the fingerprint is asserted at **no** import time;
- the composite has **never been computed on a real row** — `bench_svd_egemaps.json` has no
  composite field;
- the D5 defence ("the battery is inside the fingerprint, a shortened battery fails validation
  against every prior row") is **not operative**, because nothing validates. D5 is currently
  undefended in practice, not merely undefended in arithmetic.

The document is honest about this — §5 says "until that file exists these numbers carry a provisional
artifact pointer only." This audit upgrades that: the numbers are now **independently re-derived and
correct**; the *enforcement* is still absent.

**(f) `AUC_conf_max` is inflated by the implementation, independently of the formula.** The confound
battery is fit with a single bare logistic regression while the audio arm gets four heads plus an
ensemble (`IMPL_CRITIC.md` finding 4). Since `M = AUC_honest - max(0.5, AUC_conf_max)` and
`d(composite)/d(AUC_conf_max) = -1`, a handicapped bar inflates every margin by construction. The
formula's central quantity is only as honest as the weakest model in the battery.

**(g) The `AUC_floor = 0.60` justification is thinner than stated.** §2 argues the floor "is set just
under a known-real effect, not above it," citing HPP-Voice's sleep-apnea effect at 0.64 ± 0.03. That
effect's lower 1-sigma bound is 0.61 — **0.01 above the floor**. A real effect one standard deviation
below its point estimate would sit essentially on the cliff, and `lambda_disc = 1.00` makes the
penalty steep there. The floor is defensible but it is not "just under" by a comfortable margin.

---

## 5. Prioritized scientific findings

1. **[BLOCKER]** Reconcile `IDEA_TABLE.md` and `PREREGISTRATION.md` against the acquired manifests
   before any further compute: SVD is 49 speakers not 2,043; Coswara has 0 acquired positives under
   the pinned label; COUGHVID cannot support `A3 = speaker_disjoint` in six of seven rows.
2. **[BLOCKER]** `PREREGISTRATION.md` §4 A2 (`a_n` only) makes §6's instrument gate unexecutable and
   two of seven ranks degenerate. Amend under §14 before the freeze commit is cited by any run.
3. **[BLOCKER]** Create the four missing state files (`experiment_log.jsonl`, `best_config.json`,
   `EXPERIMENT_LEDGER.md`, `JUDGE_CARD.md`) and back-fill a row for `bench_svd_egemaps.json`, with
   its rung and its deviation from A2 stated. One executed run with no ledger entry is how the
   accounting failure starts.
4. **[MAJOR]** Implement `src/voiceaudit/composite.py` with the import-time fingerprint assertion and
   the degenerate check as a rung-0 test. Until then D5 is undefended and the composite is prose.
5. **[MAJOR]** Fix `min_subgroup_n` against the actual speaker counts (or declare the subgroup term
   `NOT_APPLICABLE(n<30)` and accept `composite: null` on SVD, per §4). Floor `sigma_null` so the
   negative-control gate does not weaken with noise.
6. **[MAJOR]** Add the population scope and a speaker-cluster CI to F1, and correct
   `benchmark.py:6`; move the two orphan sd values into the artifact or out of the finding.
7. **[MINOR]** Restate §11 condition 5 in a single metric; replace "entirely" in `COMPOSITE.md` §5
   with the measured decomposition; add the searched-degenerate test.

---

## 6. What this audit does not claim

It does not claim any published voice-health result is wrong; it does not claim the program's
hypotheses are false; and it makes no clinical or diagnostic statement. It claims that several
pre-registered plans are, as written, not executable on the data that has been acquired, and that
two priced terms of the composite cannot currently fire.

---

*Internal QA pass — implementer and critic share a model family; independent external review
pending. The fingerprint and the degenerate table were re-executed by this audit and both are
confirmed correct; every other number is either a file/line reference or a quantity computed from
`data/interim/*/manifest.csv` or `autoresearch_results/*.json`.*

---

> **Internal QA pass — implementer and critic share a model family; independent external review pending.**
