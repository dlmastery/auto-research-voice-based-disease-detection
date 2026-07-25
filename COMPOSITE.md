# COMPOSITE.md — the Goodhart-resistant composite for a claim-audit program

**Instantiation step 2** (`meta-skills/autoresearch-meta/SKILL.md` §4, §11). Written
2026-07-25. Pinned as `VOICE_AUDIT_COMPOSITE v1.0.0`.

> **SHA-256 fingerprint: `37e745ed9b0bb4bd8803b16a2cdb3448611bdbebdebdbcb4dccf1d1f2db7da9a`**
> (short form `37e745ed9b0b`). Reproduce with the exact procedure in §6. This fingerprint must
> appear in every `experiment_log.jsonl` row, every reasoning entry, and every dashboard
> footer. **Editing the formula mid-project is a BLOCKER** — it silently invalidates every
> prior comparison (`meta-skills` §4; `CLAUDE.md` §9 failure 5, where a stale fingerprint that
> no longer matched the code was one of the sibling program's integrity defects).

---

## 1. What the primary quantity actually is

The program's product is **claim survival**, not accuracy. That has a concrete consequence for
the formula: **raw discrimination cannot be the primary efficacy term.**

If `primary_efficacy = AUC`, then the highest-scoring row in this program's table would be the
one that most efficiently exploits a confound — Coppock et al.'s 0.846 cough-COVID classifier
would top the table, and its honest 0.619 would be a footnote (*Nature Machine Intelligence*
2024, arXiv:2212.08570). That is the exact failure the program exists to expose. A composite
that rewards it is worse than no composite.

So the primary term is the **honest margin**: how much discrimination survives *above the
strongest thing a confound alone can achieve*.

```
M = AUC_honest - max(0.5, AUC_conf_max)
```

- `AUC_honest` — ROC-AUC under the honest protocol: `A3 = speaker_disjoint` (at minimum),
  `A4 = fit_per_fold`, `A11 = speaker_level(mean_prob)`. Speaker-level, not recording-level.
- `AUC_conf_max` — the **maximum** AUC achieved by any member of the pinned confound battery
  (§3). Floored at 0.5 so a below-chance confound baseline cannot manufacture margin.

Everything else in the formula is a one-sided penalty, per `meta-skills` §4.

---

## 2. The formula

```
composite = M
          - lambda_disc * max(0, AUC_floor        - AUC_honest)                    # discrimination floor
          - lambda_cal  * max(0, ECE              - ECE_ref)                       # calibration tax
          - lambda_sub  * max(0, AUC_honest - AUC_subgroup_min - delta_sub)        # subgroup worst-case tax
          - lambda_xc   * max(0, AUC_honest - AUC_crosscorpus)                     # cross-corpus retention tax
          - lambda_leak * max(0, AUC_leaky  - AUC_honest)                          # protocol-inflation tax
          - lambda_ctrl * max(0, AUC_negctrl - 0.5 - 2*sigma_null)                 # negative-control leak
```

### Pinned parameters

| parameter | value | rationale |
|---|---|---|
| `lambda_disc` | **1.00** | Without it, a base-rate predictor scores exactly 0 and outranks every genuinely-tested-but-imperfect row. |
| `AUC_floor` | **0.60** | Below this the honest number is not clinically interesting; HPP-Voice's real sleep-apnea effect sits at 0.64 ± 0.03 (arXiv:2505.16490), so the floor is set just under a known-real effect, not above it. |
| `lambda_cal` | **0.50** | A catastrophic ECE of 0.35 costs 0.15 — comparable to a strong margin, so calibration can sink a row but cannot single-handedly dominate it. |
| `ECE_ref` | **0.05** | Standard reliability tolerance; below it, ECE is within typical estimation noise at our n. |
| `lambda_sub` | **0.75** | Subgroup collapse is a *finding, not a footnote* (`CLAUDE.md` §7). Priced heavily enough that a 0.30 pooled-to-worst-group gap (0.225) exceeds most attainable margins. |
| `delta_sub` | **0.05** | Tolerance band: subgroup AUCs on groups of our size have sampling spread of roughly this magnitude. Without it the term fires on noise. |
| `min_subgroup_n` | **30** | Subgroups below this are reported but excluded from `AUC_subgroup_min` — otherwise the term is dominated by whichever cell happens to be smallest. |
| `lambda_xc` | **0.60** | Cross-corpus collapse to 0.43–0.68 is the field's best-documented failure (arXiv:2511.14939); a Coppock-scale 0.30 drop costs 0.18. |
| `lambda_leak` | **1.00** | The program's signature axis. A claim whose number is bought by protocol looseness is worth nothing, so the inflation is subtracted at full weight. |
| `lambda_ctrl` | **3.00** | Near-fatal by design. A shuffled-label AUC of 0.66 costs 0.36 — larger than any margin this domain plausibly produces. A row that fails its negative control must be un-winnable, not merely penalised. |
| `sigma_null` | **measured** | The empirical SD of the negative-control statistic across the same n partitions. Never a rule-of-thumb (`CLAUDE.md` R6/R4 analogue: a delta below the instrument's own noise is not a result). |

### Term definitions (all in AUC units, so the lambdas are AUC-equivalents)

- `ECE` — expected calibration error, 15 equal-mass bins, computed on the same speaker-level
  predictions as `AUC_honest`. Raw and temperature-scaled variants are reported separately
  (arXiv:2601.07969); the **raw** value enters the composite.
- `AUC_subgroup_min` — minimum AUC over the pre-registered subgroup partition (sex; age band;
  where available: site/device, language) among subgroups with n ≥ `min_subgroup_n`.
- `AUC_crosscorpus` — AUC of the *same fitted model* evaluated on the pre-registered partner
  corpus. If no partner corpus exists for the claim, the term is **not zero — it is missing**
  (§4).
- `AUC_leaky` — AUC of the same pipeline under the audited paper's own (looser) protocol,
  typically `A3 = random_recording` and/or `A4 = fit_on_all`. This is the number the paper
  reported; measuring it is what makes the audit an audit.
- `AUC_negctrl` — the **maximum** over the required negative controls that ran for this row:
  label-shuffle, and (where an A9 projection is in play) the variance-matched random
  projection.

---

## 3. The pinned confound battery

`AUC_conf_max = max` over every member of this list that is *computable on the corpus*:

`age_only` · `age_sex_only` · `device_or_site_only` · `duration_only` · `intensity_rms_only` ·
`metadata_only` · `sex_only` · `silence_only` · `snr_only`

Each is a probe of the **same head (A7) and same protocol (A3, A4, A11)** trained on that
feature set alone — i.e. a single-axis perturbation of the champion on A5 (see
`AXIS_TAXONOMY.md` §A5, A12). `silence_only` is the Clever-Hans probe: near-100% Alzheimer's
detection from silent segments alone in the Pitt corpus (arXiv:2406.07410).

**The battery is part of the fingerprint.** Members that are not computable on a given corpus
(e.g. `device_or_site_only` on a single-device corpus) are recorded as
`NOT_APPLICABLE(reason)` in the artifact, never silently dropped. See §5, degenerate row D5:
shrinking the battery is the one way to game this composite, and it is defended by the
fingerprint plus a completeness gate, not by the arithmetic.

---

## 4. The null policy — the anti-inertness rule

> **If any required term was not measured, the composite is `null`. It is never zero, and never
> partial.**

The sibling program shipped a composite with **two of five priced axes inert**
(`CLAUDE.md` §9 failure 5). Treating a missing measurement as a zero penalty is how that
happens: the row scores well *because* it was under-measured. So:

- Every term carries an explicit `measured: true/false` flag and an artifact pointer (R1).
- A row with `composite: null` may appear on the dashboard as an in-progress reproduction. It
  may **never** enter a ranking, a Pareto plot, a promotion decision, or `FINDINGS.md`.
- Which terms are required is **rung-dependent**, and this is the promotion gate itself:

| rung | required terms | composite status |
|---|---|---|
| 0 UNIT | none (plumbing only) | `null` by definition |
| 1 SMOKE | `M`, `AUC_negctrl` | `null` — reported per-axis only |
| 2 DEV | + `ECE` | `null` |
| 3 STANDARD | + `AUC_subgroup_min`, `AUC_leaky` | **defined** |
| 4 FULL | + `AUC_crosscorpus` | **defined**, and this is the only rung whose composite may be quoted externally |

A rung-3 composite omits `AUC_crosscorpus` by *specification*, not by omission; it is recorded
as `composite_r3` with an explicitly different term set, and rung-3 and rung-4 composites are
never compared to each other.

---

## 5. Degenerate rows — the required demonstration

`meta-skills` §4 requires that a degenerate row provably loses. The table below is the verbatim
stdout of a pure-Python evaluation of the §2 formula at the §2 pinned parameters, executed at
specification time — **not** hand-arithmetic (R2). It must be re-derived as a committed rung-0
UNIT test, `scripts/composite_degenerate_check.py`, in instantiation step 6; until that file
exists these numbers carry a provisional artifact pointer only. Two honest rows are included as
the bar the degenerates must fail to clear.

```
row                                      M   disc    cal    sub     xc   leak   ctrl  COMPOSITE
-----------------------------------------------------------------------------------------------
R0  honest reference (SVD repro)    0.2400 0.0000 0.0100 0.0000 0.0900 0.0600 0.0000     0.0800
R1  honest but weak                 0.0800 0.0000 0.0050 0.0000 0.0120 0.0100 0.0000     0.0530
D1  leakage rider                   0.0500 0.0000 0.0200 0.0000 0.0660 0.3200 0.0000    -0.3560
D2  confound rider (Coppock)        0.0100 0.0000 0.0050 0.0000 0.1800 0.0100 0.0000    -0.1850
D3  uncalibrated high-AUC           0.2600 0.0000 0.1450 0.0000 0.1080 0.0200 0.0000    -0.0130
D4  subgroup specialist             0.2700 0.0000 0.0050 0.1950 0.1020 0.0100 0.0000    -0.0420
D6  base-rate null model            0.0000 0.1000 0.0000 0.0000 0.0000 0.0000 0.0000    -0.1000
D7  shuffle-passing artifact        0.1700 0.0000 0.0150 0.0000 0.0720 0.0300 0.3600    -0.3070
```

Inputs (`AUC_honest`, `AUC_conf_max`, `ECE`, `AUC_subgroup_min`, `AUC_crosscorpus`,
`AUC_leaky`, `AUC_negctrl`), with `sigma_null = 0.02` throughout:

| row | what it games | inputs |
|---|---|---|
| **R0** | nothing — a plausible faithful SVD reproduction | 0.86, 0.62, 0.07, 0.81, 0.71, 0.92, 0.51 |
| **R1** | nothing — a weak but genuinely honest effect | 0.66, 0.58, 0.06, 0.63, 0.64, 0.67, 0.51 |
| **D1** | **speaker leakage** — spectacular 0.95 under a random split, 0.63 speaker-disjoint | 0.63, 0.58, 0.09, 0.60, 0.52, 0.95, 0.52 |
| **D2** | **the confound** — AUC 0.85, but a symptom/duration baseline already gets 0.84 | 0.85, 0.84, 0.06, 0.80, 0.55, 0.86, 0.51 |
| **D3** | **discrimination only** — best AUC in the table, ECE 0.34 | 0.88, 0.62, 0.34, 0.84, 0.70, 0.90, 0.51 |
| **D4** | **the pooled average** — 0.89 pooled, 0.58 for the worst sex band | 0.89, 0.62, 0.06, 0.58, 0.72, 0.90, 0.51 |
| **D6** | **the safe null** — predicts the base rate, perfectly calibrated, no leakage anywhere | 0.50, 0.50, 0.01, 0.50, 0.50, 0.50, 0.50 |
| **D7** | **an artifact** — respectable margin, but scores 0.66 on shuffled labels | 0.72, 0.55, 0.08, 0.68, 0.60, 0.75, 0.66 |

**Every degenerate row loses to both honest rows.** The three most instructive:

- **D3 has the highest AUC in the table (0.88 vs R0's 0.86) and the highest raw margin
  (0.2600 vs 0.2400) — and still scores below zero.** That is the Goodhart property working:
  discrimination alone cannot buy the top of the table.
- **D2 sits 0.01 AUC below R0 and loses by 0.265 composite**, entirely because its confound
  baseline is at 0.84. This is the Coppock case, and it is the single row this program most
  needs to rank correctly.
- **D6, the do-nothing null, beats D1, D2 and D7.** It should: a model that claims nothing is
  more honest than one whose number comes from leakage, a confound, or an artifact. It still
  loses to R1, the weak-but-real effect, by 0.153.

### Proven monotonicity

`∂composite / ∂AUC_honest = +1 (from M) + lambda_leak − lambda_sub − lambda_xc = **+0.65 > 0**`
in the worst case where all three of those penalties are simultaneously active. So the
composite **never rewards lowering honest discrimination** — there is no perverse incentive to
under-fit. (`M` and the leak term both rise with `AUC_honest`; only the subgroup and
cross-corpus gaps widen.)

### The one attack the arithmetic does not stop

**D5 — the battery shrinker.** An auditor who wants a large `M` can simply run fewer confound
baselines: `∂composite / ∂AUC_conf_max = −1`, so *every additional confound baseline can only
lower the score*. The formula cannot defend against this, and pretending otherwise would be
dishonest.

It is defended by three non-arithmetic gates instead:
1. The battery is inside the SHA-256 fingerprint (§6) — a shortened battery produces a
   different fingerprint, which fails validation against every prior row.
2. `NOT_APPLICABLE(reason)` is a required, reviewed field; a bare omission makes the composite
   `null` (§4).
3. **The program's deliverable is the verdict, not a high composite.** No incentive in this
   project rewards a high composite — the ledger publishes holds and breaks with equal
   prominence (`CLAUDE.md` R8). This is worth stating plainly, because it is the actual
   structural defence: the composite ranks conditions *within* a claim's audit; it never
   decides whether the program succeeded.

---

## 6. Fingerprint procedure

The fingerprint is taken over the **specification**, not over source code, so a refactor cannot
change it and a parameter edit cannot hide in one.

1. Construct the spec dict with exactly these keys: `name`, `version`, `formula`, `lambdas`,
   `thresholds`, `confound_battery`, `null_policy`.
2. Canonicalise: `json.dumps(SPEC, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.
3. Hash: `hashlib.sha256(canon.encode("utf-8")).hexdigest()`.
4. Assert the result equals the pinned value at import time. A mismatch raises and **halts the
   runner** — it does not warn.

The canonical string for v1.0.0 is, byte for byte:

```
{"confound_battery":["age_only","age_sex_only","device_or_site_only","duration_only","intensity_rms_only","metadata_only","sex_only","silence_only","snr_only"],"formula":"M = AUC_honest - max(0.5, AUC_conf_max); composite = M - l_disc*max(0, AUC_floor - AUC_honest) - l_cal*max(0, ECE - ECE_ref) - l_sub*max(0, AUC_honest - AUC_subgroup_min - delta_sub) - l_xc*max(0, AUC_honest - AUC_crosscorpus) - l_leak*max(0, AUC_leaky - AUC_honest) - l_ctrl*max(0, AUC_negctrl - 0.5 - 2*sigma_null)","lambdas":{"l_cal":0.5,"l_ctrl":3.0,"l_disc":1.0,"l_leak":1.0,"l_sub":0.75,"l_xc":0.6},"name":"VOICE_AUDIT_COMPOSITE","null_policy":"any_missing_term_makes_composite_null","thresholds":{"AUC_floor":0.6,"ECE_ref":0.05,"delta_sub":0.05,"min_subgroup_n":30},"version":"1.0.0"}
```

→ `37e745ed9b0bb4bd8803b16a2cdb3448611bdbebdebdbcb4dccf1d1f2db7da9a`

**Implementation location:** `src/voiceaudit/composite.py`, exporting `SPEC`, `FINGERPRINT`,
`composite(row) -> float | None`, and `fingerprint() -> str`. The degenerate-row table in §5 is
regenerated by `scripts/composite_degenerate_check.py` and is a **rung-0 UNIT test**: if any
degenerate row ever outranks R1, the test fails and the build is red.

---

## 7. The composite is an internal ranking device — the public claim is the Pareto frontier

Per `meta-skills/autoresearch-meta` §4 (L5): *"The Pareto frontier is the primary scientific
object. The scalar composite is a convenience tiebreak."* That applies with extra force here.

- **Externally we publish the raw axes**: `AUC_honest`, `AUC_conf_max` (and every battery
  member individually), `ECE`, per-subgroup AUC, `AUC_crosscorpus`, `AUC_leaky`, and the
  negative controls — each with its n, its tier chip, and its artifact pointer.
- **The accept criterion is Pareto-dominance**, not a composite delta: a condition is better
  only if it is at least as good on every axis and strictly better on at least one.
- **The composite exists to order the rows in a table and to make a degenerate row provably
  un-winnable.** It is never the headline. No sentence in `FINDINGS.md` may state a composite
  without the per-axis breakdown alongside it (`meta-skills` §4).
- **A verdict is never a composite comparison.** `HOLDS` / `ATTENUATED` / `BREAKS` /
  `INCONCLUSIVE` / `NOT_REPRODUCIBLE` are decided against the pre-registered falsifier on the
  pre-registered primary metric — see `PREREGISTRATION.md`. The composite does not appear in
  that decision at all.

**Note for the lead:** `CLAUDE.md` §6's state-file table does not currently list a composite
artifact, and `CLAUDE.md` has no composite section (unlike the sibling constitution's §6). This
file is therefore a **new state file** and should be added to that table, with the fingerprint
requirement folded into the R1/R15 provenance rules.

---

*Internal QA pass — independent external review pending. Every arXiv identifier here is carried
over from `corpus/SURVEY_datasets.md` / `corpus/SURVEY_sota_methods.md` (mechanically verified
2026-07-25); none was introduced from memory (R10). The numeric table in §5 was produced by
executing the reference implementation, not estimated (R2).*
