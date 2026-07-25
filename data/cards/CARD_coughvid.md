# Data Card — COUGHVID

**Acquired:** 2026-07-25 · **Tier:** full archive downloaded (2.30 GB), metadata analysed
**Artifact:** `autoresearch_results/acquisition/coughvid_meta_stats.json`
**Producer:** `scripts/analyze_coughvid_meta.py`
**Archive SHA-256:** `37544c58ac5a7d79cb68af56fb3d0a690773b100bef8a03aac96570086fea335`
**Archive bytes:** `2,297,542,075` (matches the Zenodo-declared size exactly)

Every number below was computed from the checksummed archive, not quoted from a paper.

---

## 1. Provenance and licence

| Field | Value |
|---|---|
| Record | `https://zenodo.org/records/7024894` |
| DOI | `10.5281/zenodo.7024894` (concept DOI `10.5281/zenodo.4048312`) |
| Paper | *Nature Scientific Data* 2021, `s41597-021-00937-4` |
| Licence | **CC-BY-4.0** (from the Zenodo API `metadata.license.id = cc-by-4.0`) |
| Access | **Fully open.** No account, no DUA, no gate. Single file. |
| Local path | `data/raw/coughvid/public_dataset_v3.zip` (git-ignored) |
| Download | 207 s, HTTP 200 |

---

## 2. Contents

**68,869 zip members = 34,434 recordings**, each with a paired JSON sidecar:

| extension | count |
|---|---|
| `.json` | 34,434 |
| `.webm` | 29,348 |
| `.wav` | 3,309 |
| `.ogg` | 1,777 |
| `.csv` | 1 |

Audio total = 29,348 + 1,777 + 3,309 = **34,434**, exactly one per JSON.
Compiled metadata: `coughvid_20211012/metadata_compiled.csv` — 34,434 rows, 51 columns
(extracted to `data/raw/coughvid/metadata_compiled.csv`).

Note: the widely-cited "> 25,000 recordings" understates the shipped v3 archive, which
holds **34,434**.

---

## 3. Class balance

`status` is the **self-reported** COVID label. It is present on only **20,664 / 34,434
rows (60.0 %)**.

| `status` | all rows | at `cough_detected ≥ 0.8` |
|---|---|---|
| healthy | 15,476 | 10,132 |
| *missing* | 13,770 | 5,009 |
| symptomatic | 3,873 | 2,683 |
| COVID-19 | 1,315 | **720** |

**≥500/class bar:** met for healthy-vs-COVID both unfiltered (15,476 / 1,315) and under
the conventional `cough_detected ≥ 0.8` filter (10,132 / **720**) — but the positive
class is thin, and 720 is the real working number for any benchmark that applies the
standard filter. `cough_detected` mean = **0.6412**; 18,544 / 34,434 rows clear 0.8.

**Expert-labelled subset (the only clinician-touched labels):**

- rows with ≥1 expert diagnosis: **2,841**
- rows with all 4 experts: **126**
- diagnosis counts: `upper_infection` 883, `healthy_cough` 746, `lower_infection` 732,
  **`COVID-19` 649**, `obstructive_disease` 214

So the clinician-labelled COVID class is **649** — usable, but this is a small-N,
4-rater subset and inter-rater agreement must be reported before it is trusted.

---

## 4. Speaker-disjoint splits — the critical field analysis

| Question | Answer |
|---|---|
| Is there a participant id? | **NO** |
| What ids exist? | `uuid` only — **34,434 rows, 34,434 unique uuids, one per recording** |
| Can repeat submitters be detected? | **No.** No field links two recordings to one person. |

**Verdict: IMPOSSIBLE.** COUGHVID **cannot support a speaker-disjoint split at all.**
This is the single most important fact about this dataset. There is no grouping key,
so every published COUGHVID number — including the frequently-cited **AUC ≈ 0.93** — is
computed on splits that may place the same person's coughs in both train and test, and
is an **upper bound of unknown tightness**.

The only weak proxy is geolocation, and it shows heavy clustering consistent with
repeat local submission:

| lat,long | n |
|---|---|
| 46.5, 6.6 (Lausanne — the collecting institution) | 269 |
| 46.2, 6.1 (Geneva) | 258 |
| 41.0, 29.1 (Istanbul) | 153 |
| 41.4, 2.2 (Barcelona) | 104 |
| 46.2, 6.2 | 104 |

19,431 rows carry a latitude; the coordinates are rounded to 0.1°, so they identify a
city, not a person. **Geolocation is a site confound, not a usable split key.**

**Practical rule for this program:** COUGHVID may be used for pretraining, for
transfer/OOD evaluation, and as a *negative control* demonstrating the leakage
problem — **never** as the source of a headline supervised number.

---

## 5. Confounds measured (not assumed)

**Self-reported respiratory condition — the strongest shortcut found.**

| status | `respiratory_condition = True` | rate |
|---|---|---|
| healthy | 1,985 / 15,476 | **12.8 %** |
| symptomatic | 1,121 / 3,873 | 28.9 % |
| COVID-19 | 451 / 1,315 | **34.3 %** |

A single self-report checkbox separates healthy from COVID-19 by a 21.5-point margin
*before any audio is touched*. Any audio model must be scored against a
metadata-only baseline built from this field.

**Sex.**

| status | male | female | % male |
|---|---|---|---|
| healthy | 9,923 | 5,471 | **64.5 %** |
| COVID-19 | 695 | 586 | **54.3 %** |

A 10.2-point gap.

**Missingness is itself a label.** 13,770 rows (40 %) have no `status`, no `gender`,
no `respiratory_condition` — the missingness pattern is perfectly collinear with the
label being absent, so any imputation leaks.

---

## 6. Audit hooks (what to re-test here)

1. **Metadata-only baseline first.** Fit `respiratory_condition + age + gender` → status.
   Publish that AUC. It is the floor any audio claim must clear.
2. Reproduce the published **AUC ≈ 0.93**, then report that no speaker-disjoint
   variant of it can be constructed, and quantify what a *geolocation*-disjoint split
   does to it (an upper bound on the leakage correction).
3. Report agreement among the 4 expert raters on the 126 fully-rated rows before using
   any expert label.

---

## 7. Reproduce

```bash
curl -sS --ssl-no-revoke -L -o public_dataset_v3.zip \
  "https://zenodo.org/records/7024894/files/public_dataset_v3.zip?download=1"
python scripts/analyze_coughvid_meta.py
```

Metadata is read directly out of the zip — **no audio extraction is required** for the
data card, and none was performed.
