# Data Card — Coswara

**Acquired:** 2026-07-25 · **Tier:** metadata + annotations only (no audio pulled)
**Artifact:** `autoresearch_results/acquisition/coswara_meta_stats.json`
**Producer:** `scripts/analyze_coswara_meta.py`
**Source SHA-256 (`combined_data.csv`):** `e462c503bee3408214195855975b0eda08dd1188c0d521b494d93d388d60a72d`

Every number below was computed by the script above from the checksummed file and
read out of the JSON artifact — none is quoted from a paper (CLAUDE.md R1/R2).

---

## 1. Provenance and licence

| Field | Value |
|---|---|
| Upstream | `https://github.com/iiscleap/Coswara-Data` |
| Paper | Coswara, *Nature Scientific Data* 2023, `s41597-023-02266-0` |
| Licence | **CC-BY-4.0** (`LICENSE.md`, "Copyright (c) 2021 LEAP Lab, Indian Institute of Science, Bangalore") |
| Access | **Fully open.** No account, no DUA, no gate. |
| Local path | `data/raw/coswara_meta/` (git-ignored) |
| Audio pulled | **None.** Audio lives in per-date `*.tar.gz.a[a-d]` shards, ~16 GB total. |

### Acquisition note — a disk hazard, recorded so it is not repeated
`git clone` of this repo pulls **16.75 GB** (`gh api repos/iiscleap/Coswara-Data
--jq .size` → `16753933` KB) and the checkout roughly doubles it. Two naive clones
were killed mid-flight on this host (24 GB free, 98%-full system drive). Worse,
`--filter=blob:none` *without* `--no-checkout` is a trap: the automatic checkout
lazily re-fetches every blob in HEAD, so it downloads the full ~13 GB anyway.
**Metadata was instead fetched file-by-file over `raw.githubusercontent.com` — 15
files, 2 MB, seconds.** Sizes were verified against `git ls-tree -l` blob sizes
(`combined_data.csv` = 359,150 B, exact match).

---

## 2. Contents

`combined_data.csv` — **2,746 rows**, 36 columns, one row per participant submission.
Field dictionary in `csv_labels_legend.json`.

`annotations/*.csv` — 9 files, per-modality human quality ratings:
`breathing-deep`, `breathing-shallow`, `cough-heavy`, `cough-shallow`,
`counting-fast`, `counting-normal`, `vowel-a`, `vowel-e`, `vowel-o`.

Nine audio streams per participant (two breathing, two cough, three sustained
vowels, two counting/speech styles).

---

## 3. Class balance

| `covid_status` | n |
|---|---|
| healthy | 1,433 |
| positive_mild | 426 |
| no_resp_illness_exposed | 248 |
| positive_moderate | 165 |
| resp_illness_not_identified | 157 |
| recovered_full | 146 |
| positive_asymp | 90 |
| under_validation | 81 |
| **total** | **2,746** |

**Binary task** (positive = mild+moderate+asymp; negative = healthy):

- **positive n = 681**
- **negative n = 1,433**
- **Meets the ≥500/class bar: YES** (both classes clear 500).

> Note a discrepancy to state honestly: the *Scientific Data* paper reports 2,635
> individuals (1,819 negative / 674 positive / 142 recovered). The shipped CSV has
> **2,746** rows and a different split. Do not quote the paper's n for this file;
> quote the artifact.

---

## 4. Speaker-disjoint splits — the critical field analysis

| Question | Answer |
|---|---|
| Is there a participant id? | **Yes — `id`** ("User ID") |
| Is `id` unique per row? | **Yes.** 2,746 rows, 2,746 unique ids, `max_rows_per_id = 1` |
| Any id spanning multiple `record_date`s? | **No** (0) |
| Returning-user flag? | **Yes — `rU`**: `n` = 2,003, **`y` = 63**, blank = 680 |

**Verdict: PARTIAL.** `id`-level `GroupKFold` is the correct split and is
well-defined — but it is **not a guarantee of speaker disjointness**. 63 rows are
self-declared returning users who submitted again under a *new* `id`, and **no field
links a returning user to their earlier submission**. A further 680 rows leave `rU`
blank, so the true repeat count is bounded below by 63 and unknown above.

**Practical rule for this program:** split on `id`; report that ≤63/2,746 (≤2.3%)
of rows may share a speaker with another row across the split boundary, and that
this residual is *irreducible from the shipped metadata*. Any claim whose margin is
smaller than that residual is not safe.

---

## 5. Confounds measured (not assumed)

**Sex.** The classes are differently balanced, so a sex-only classifier has signal:

| class | male | female | % male |
|---|---|---|---|
| positive | 413 | 267 | **60.7 %** |
| negative | 1,068 | 364 | **74.6 %** |

A 13.9-point gap.

**Age.** positive mean **39.34** (median 35) vs negative mean **33.29** (median 30) —
a ~6-year gap in the same direction as COVID severity.

**Geography / site.** positive is **667/681 = 98.0 % India**; negative is
**1,266/1,433 = 88.3 % India** with 63 United States. Country is not balanced across
the label, so an accent/handset/site cue is available to the model.

**Label provenance.** `covid_status` is **self-reported**; `testType` (RAT/RT-PCR)
and `test_status` exist but are sparsely populated. This is a self-report corpus,
not a PCR-referenced one.

---

## 6. Audit hooks (what to re-test here)

1. Reproduce the published intra-dataset **AUC ≈ 0.92**, then re-run under
   `id`-level `GroupKFold`, and report the delta.
2. Fit a **demographics-only baseline** (age + sex + country). Given the gaps above,
   claim only the margin *above* that baseline.
3. Cross-corpus transfer to COUGHVID — the collapse is the expected result and is
   the point.

---

## 7. Reproduce

```bash
python scripts/analyze_coswara_meta.py     # rewrites the JSON artifact
```

Re-fetch metadata (2 MB, no clone):

```bash
B=https://raw.githubusercontent.com/iiscleap/Coswara-Data/master
for f in combined_data.csv csv_labels_legend.json extract_data.py README.md LICENSE.md; do
  curl -sS --ssl-no-revoke -L -o "$f" "$B/$f"
done
```

**Do not** `git clone` this repository.
