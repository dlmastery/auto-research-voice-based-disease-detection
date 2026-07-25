# Data Card — Coswara

**Status:** METADATA FULLY OBTAINED (all labels, all 43 date manifests).
**Audio NOT yet downloaded — script-ready, 13.00 GB.**
**Verified:** 2026-07-25, against the GitHub tree API and the downloaded files.
**Local path:** `data/raw/coswara/` (gitignored).

---

## 1. Source and licence

| | |
|---|---|
| Repository | <https://github.com/iiscleap/Coswara-Data> (branch `master`) |
| Paper | Nature Scientific Data `s41597-023-02266-0` |
| Licence | `NOASSERTION` per the GitHub API; the repo ships a 13,869-byte `LICENSE.md` — **read it before redistribution** |
| Access | **open** — no gate, no account |

## 2. Size — the survey undercounts this by ~4x

The task brief and `corpus/SURVEY_datasets.md` both describe Coswara as "a few
GB" to be acquired with `git clone`. Measured from the GitHub tree API:

| Measure | Value |
|---|---|
| Working-tree blobs | **13,003,727,715 bytes = 13.00 GB** (336 blobs) |
| Repo size incl. history (API) | **16.75 GB** |

### `git clone` does not work reliably on this host
Two attempts, both lost:

1. Full `git clone` — reaped at ~6 GiB of "Receiving objects", left an empty
   working tree (94 KB `.git`).
2. `git clone --filter=blob:none --depth 1` — died with `fatal: early EOF`
   after 4.4 GB.

**git cannot resume a broken clone**, so every retry restarts from zero. Hence
`scripts/fetch_coswara.py` fetches the same content file-by-file over HTTP from
`raw.githubusercontent.com`, which **is** resumable and restart-safe. Prefer it.

## 3. Repository layout

```
combined_data.csv        359 KB   master participant metadata  (obtained)
csv_labels_legend.json   1.6 KB   decodes every categorical column  (obtained)
extract_data.py                   upstream shard-reassembly script  (obtained)
README.md / LICENSE.md            (obtained)
annotations/             1.1 MB   human annotation files       (not fetched)
technical_validation/    20 MB    validation artefacts          (not fetched)
YYYYMMDD/  x43                    43 date directories, 12.98 GB total
  YYYYMMDD.csv                    that day's metadata          (all 43 obtained)
  YYYYMMDD.tar.gz.{aa,ab,...}     audio, ~500 MB shards        (NOT fetched)
```

Date directories range from **48.3 MB** (`20200911`) to **884.2 MB** (`20200502`).
Audio shards must be concatenated before extraction:
`cat YYYYMMDD.tar.gz.* > YYYYMMDD.tar.gz && tar -xzf YYYYMMDD.tar.gz`
(`fetch_coswara.py --extract` does this automatically).

## 4. Exact contents obtained

- `combined_data.csv` — 2,746 rows × 36 columns. **Complete.**
- `csv_labels_legend.json` — complete column legend. **Complete.**
- All **43** per-date CSVs. **Complete.**
- `github_tree.json` — full file manifest with sizes, kept as provenance.

**Integrity cross-check:** the 43 per-date CSVs sum to exactly 2,746 rows and
2,746 unique ids, and their id set is *identical* to `combined_data.csv` — zero
ids in one and not the other. The metadata is internally consistent and complete.

## 5. n subjects, n recordings, class balance

**n subjects = 2,746** (one row per participant; `id` is unique, 0 duplicates).

> The survey says 2,635 individuals (1,819 negative / 674 positive / 142
> recovered). The released corpus is **larger: 2,746**. Use the measured number.

`covid_status`:

| Label | n |
|---|---|
| healthy | 1,433 |
| positive_mild | 426 |
| no_resp_illness_exposed | 248 |
| positive_moderate | 165 |
| resp_illness_not_identified | 157 |
| recovered_full | 146 |
| positive_asymp | 90 |
| under_validation | 81 |

Collapsed: **positive (mild+moderate+asymp) = 681**, **healthy = 1,433**,
recovered_full = 146.

`test_status`: `p` 681 · `na` 314 · `n` 257 · `ut` 81 · missing 1,413 (51.5%).
`testType`: rtpcr 755 · rat 37 · `False` 13 · missing 1,941 (70.7%).

So **681 positives / 1,433 healthy** — both clear the ≥500/class bar. Note
positives are only 32.2% of that 2,114-subject binary pool; report the base rate.

### n recordings — MEASURED
Verified by extracting date dir `20200430`: **23 participants, every one with
exactly 10 files** — 9 `.wav` + 1 `metadata.json`:

```
breathing-deep.wav   breathing-shallow.wav
cough-heavy.wav      cough-shallow.wav
counting-fast.wav    counting-normal.wav
vowel-a.wav          vowel-e.wav           vowel-o.wav
metadata.json
```

So **n recordings = 2,746 × 9 = 24,714**. The 9-stream structure is exact and
uniform, which makes modality-ablation experiments clean.

### Sample rate — MEASURED, and it is NOT uniform
From 207 WAV headers in `20200430`:

| Property | Value |
|---|---|
| Sample rate | **48,000 Hz (198/207) and 44,100 Hz (9/207)** |
| Channels | mono (207/207) |
| Bit depth | 16-bit PCM (207/207) |
| Duration | min **0.00 s**, median 8.96 s, mean 10.15 s, max 29.95 s |

Two consequences:

1. **Resample explicitly.** A mixed 48 kHz / 44.1 kHz corpus silently breaks any
   pipeline that assumes one rate.
2. **Sample rate is itself a device proxy** — the 44.1 kHz minority almost
   certainly reflects different capture hardware. Check that a
   sample-rate-only classifier is near chance.
3. **Zero-length recordings exist** (min duration 0.00 s). Filter on duration
   before training and report how many were dropped.

## 6. Metadata fields — speaker-disjoint splitting

36 columns; `csv_labels_legend.json` decodes all of them.

| Field | Meaning | Missing | Role |
|---|---|---|---|
| `id` | User ID (Firebase-style UID) | 0% | **the grouping key** |
| `covid_status` | health status | 0% | the label |
| `record_date` | submission date | 0% | temporal splits / drift |
| `a` | age | 0% | confound control |
| `g` | gender | 0% | male 1,900 / female 844 / other 2 |
| `l_c`, `l_s`, `l_l` | country / state / locality | 0 / 0 / 11.7% | site confound proxy |
| `rU` | **returning user (y/n)** | 24.8% | **identity-leakage flag — see below** |
| `ep` | proficient in English | 0% | |
| `test_status`, `testType`, `test_date` | COVID test | 51.5 / 70.7 / 70.7% | label provenance |
| `vacc` | vaccination status | 64.9% | |
| `smoker`, `cold`, `cough`, `fever`, `st`, `ftg`, `mp`, `loss_of_smell`, `bd`, `diarrhoea` | symptoms | 60–98% | **confounder matching (§3.2)** |
| `asthma`, `cld`, `pneumonia`, `ht`, `diabetes`, `ihd`, `others_resp`, `others_preexist` | comorbidities | 88–97% | |
| `ctScan`, `ctDate`, `ctScore` | CT scan | 64.9 / 94.4 / 94.4% | |

### Speaker id: PRESENT — but with a real caveat

`id` is unique per row (2,746/2,746), so it groups a participant's 9 audio
streams correctly. **`GroupKFold(groups=id)` is required** — a recording-level
split would put a participant's cough in train and their breathing in test.

**The caveat, and it matters:** `rU` ("returning user") is **`y` for 63
participants and missing for 680 (24.8%)**. A returning user submits again and
receives a *new* `id`, so the same human can appear under multiple ids. There is
no field linking them.

> **Therefore `id` guarantees *submission*-disjoint, not *person*-disjoint splits.**
> At least 63 known repeat contributors, and up to 680 more unknown, may straddle
> a fold boundary. State this explicitly with any Coswara result; do not claim
> strict speaker-independence.

### Device info: absent from the CSV, but PARTIALLY present in the tarballs

`combined_data.csv` has **no** device, microphone, OS or browser column. But the
per-participant `metadata.json` shipped *inside the audio tarballs* carries
fields that never made it into the master CSV. Measured over 208 participants
across 5 date directories:

| Field | Coverage | Values |
|---|---|---|
| `dT` | **127/208 (61%)** | `web` 126, `android` 1 |
| `fV` | 51/208 (25%) | `2` |
| `iF` | 76/208 (37%) | — |
| `id`, `date` | 157 / 81 | mirror the CSV |

`dT` is a **capture-platform** flag (web form vs Android app), not a phone model
or microphone. It is coarse and 39% missing, but it is *not nothing*.

> **Correction to the obvious reading:** the survey's §3.3 device check is not
> flatly impossible on Coswara, it is *partially* possible. Build the device
> proxy from three measured signals — `dT` (platform, 61% coverage),
> **sample rate** (48 kHz vs 44.1 kHz, 100% coverage, measurable from every WAV),
> and `l_c`/`l_s` + `record_date` (geography and collection wave). Run the
> device-only classifier on that composite and report it.
>
> What remains genuinely unobserved is the **specific handset and microphone**.
> Say that plainly rather than claiming device was controlled.

To use `dT` you must extract the tarballs — it is not in the CSV, so a
metadata-only workflow will miss it entirely.

### Other confounds visible in the metadata
- **Sex skew:** 69.2% male (1,900 / 844 / 2). Report per-sex metrics.
- **Geographic concentration:** India 2,515 (91.6%); Karnataka alone 1,127 (41%).
  This is effectively a single-site corpus with a long tail.
- **Label provenance is mixed:** only 792 participants have any test type
  recorded (755 RT-PCR). The remainder is self-report. Per survey §3.9 these are
  not interchangeable — consider a PCR-only sensitivity analysis.
- **Temporal drift:** submissions span 2020-04-13 → 2022-02-24 across 398
  distinct dates, crossing multiple variant waves and the vaccine rollout.

## 7. Reproduce

```bash
python scripts/fetch_coswara.py --list           # the 43 date dirs by size
python scripts/fetch_coswara.py --metadata-only  # ~4 MB — what is obtained now
python scripts/fetch_coswara.py --pilot          # + smallest date dir (48 MB)
python scripts/fetch_coswara.py --audio          # all 43 dirs, 13 GB, resumable
python scripts/fetch_coswara.py --audio --extract
```
