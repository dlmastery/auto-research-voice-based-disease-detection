# Data Card — COUGHVID

**Status:** FULLY OBTAINED (2.30 GB archive, md5-verified).
**Verified:** 2026-07-25, against the live Zenodo API and the archive itself.
**Local path:** `data/raw/coughvid/` (gitignored).

---

## 1. Source and licence

| | |
|---|---|
| Record | <https://zenodo.org/records/7024894> |
| Record DOI | `10.5281/zenodo.7024894` |
| Concept DOI | `10.5281/zenodo.4048311` (always resolves to latest) |
| Version | 3.0, published 2021-02-03 |
| Licence | **CC-BY-4.0** |
| Access | `open` — no gate, no account |
| Paper | Nature Scientific Data `s41597-021-00937-4` |

## 2. Exact contents obtained

| File | Bytes | Verified |
|---|---|---|
| `public_dataset_v3.zip` | **2,297,542,075** (2.30 GB) | md5 `7c6cdf184748a2600538c331ba0ba718` — matches Zenodo |

Everything lives under one directory, `coughvid_20211012/`, with **68,869 entries**:

| Kind | Count |
|---|---|
| Audio — `.webm` | 29,348 |
| Audio — `.wav` | 3,309 |
| Audio — `.ogg` | 1,777 |
| **Audio total** | **34,434** |
| Per-recording `.json` sidecars | 34,434 |
| `metadata_compiled.csv` | 1 (5,463,841 bytes) |

Files are named `<uuid>.{webm,wav,ogg}` with a matching `<uuid>.json`.

> The survey says ">25,000 recordings"; the released v3 archive actually holds
> **34,434**. Use the measured number.

## 3. n subjects, n recordings, class balance

**n recordings = 34,434. n subjects = UNKNOWN — see §5.**

`status` (self-reported):

| Label | n | % |
|---|---|---|
| healthy | 15,476 | 44.9% |
| *(missing)* | 13,770 | 40.0% |
| symptomatic | 3,873 | 11.2% |
| **COVID-19** | **1,315** | 3.8% |

With labels present (20,664 recordings): healthy 74.9%, symptomatic 18.7%,
COVID-19 6.4%. Both COVID-19 (1,315) and healthy (15,476) clear the program's
≥500/class bar, but at a **natural base rate of 6.4% positive** among labelled
recordings — report it, and do not silently rebalance without saying so.

`status_SSL` (a semi-supervised-learning label column) is **75.8% missing**.

### The expert-labelled subset is tiny
Four expert annotators contribute `quality_k`, `cough_type_k`, `dyspnea_k`,
`wheezing_k`, `stridor_k`, `choking_k`, `congestion_k`, `nothing_k`,
`diagnosis_k`, `severity_k` for k = 1..4. Every one of those 40 columns is
**~97.6% missing** — only **~820 recordings (2.4%)** carry any expert label
(`quality_1`: 614 ok / 156 poor / 32 good / 18 no_cough). Any claim resting on
expert labels is a ≤820-recording claim, not a 34k one.

## 4. Sample rate and audio format

**Sample rate: `[UNVERIFIED]` — not decoded in this pass.** The archive ships
compressed `.webm`/`.ogg` (Opus/Vorbis from browser capture) plus some `.wav`;
these are crowd-recorded on arbitrary consumer hardware, so a single nominal
rate should not be assumed. Decode a sample and measure before fixing a
preprocessing config.

`cough_detected` is a per-recording cough-classifier confidence in [0,1]
(7,958 distinct values, no missing). The published convention is to keep
`cough_detected > 0.8`, which the survey puts at ~35 h of audio.

## 5. Metadata fields — and the fatal gap for this program

`metadata_compiled.csv`, 34,434 rows × 52 columns.

| Field | Missing | Notes |
|---|---|---|
| `uuid` | 0% | **per-RECORDING id — 34,434 rows, 34,434 unique, 0 duplicates** |
| `datetime` | 0% | 34,434 distinct — every recording is its own timestamp |
| `cough_detected` | 0% | cough-classifier confidence |
| `age` | **43.7%** | |
| `gender` | **40.0%** | male 12,850 / female 7,682 / other 132 |
| `latitude`, `longitude` | 43.6% | coarse geography (~1 dp) |
| `respiratory_condition` | 40.0% | self-reported |
| `fever_muscle_pain` | 40.0% | self-reported |
| `status` | 40.0% | the label |
| `status_SSL` | 75.8% | |
| `quality_*`…`severity_*` (40 cols) | ~97.6% | expert subset only |

### >>> NO SPEAKER ID. SPEAKER-DISJOINT SPLITTING IS IMPOSSIBLE. <<<

This is the loud warning the program's #1 requirement demands.

- `uuid` is **one per recording**, not one per person: 34,434 rows → 34,434
  unique uuids, zero duplicates. It cannot group recordings by contributor.
- There is **no** participant id, session id, device id, or account id anywhere
  in the CSV or in the filenames.
- COUGHVID is an anonymous web-form submission corpus. **Nothing in the release
  reveals whether the same person submitted twice**, and with 34k crowd
  submissions some certainly did.

**Consequences that must be honoured:**

1. COUGHVID **cannot** produce a speaker-disjoint split, and therefore cannot
   support an evaluation-tier claim under this program's rigor contract.
2. Use it as the survey intends: **self-supervised pretraining** and an
   **out-of-distribution transfer target** for a model trained elsewhere.
   Both uses are unharmed by the missing speaker id, because neither requires a
   within-COUGHVID train/test split.
3. If a within-COUGHVID number is ever reported, it must be labelled
   **"recording-level split, speaker identity unknown, leakage not excludable"**
   — never called speaker-independent.
4. No device or hardware field either, so the §3.3 device-confound check
   ("a device-only classifier must be near chance") **cannot be run** on COUGHVID.

There is also no PCR reference: `status` is entirely self-report. The published
intra-set AUC ~0.93 should be treated as an upper bound inflated by label noise
and demographics.

## 6. Reproduce

```bash
python scripts/fetch_coughvid.py --info      # record metadata, no download
python scripts/fetch_coughvid.py             # 2.30 GB, md5-verified, resumable
python scripts/fetch_coughvid.py --extract   # + unzip
```
