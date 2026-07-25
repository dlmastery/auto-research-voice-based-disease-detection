# Dataset Acquisition Status

**As of 2026-07-25.** Every "obtained" row below was verified against the bytes
on disk; every URL was fetched live this session. Nothing here is quoted from
memory. Audio lives under `data/raw/` and is **gitignored** (verified with
`git check-ignore`) — no audio or PHI is ever committed.

---

## 1. Status table

| Dataset | Status | On disk | What exists locally | Next action |
|---|---|---|---|---|
| **SVD** (Saarbrücken) | **PILOT OBTAINED** | **152 MB** | full speaker metadata (2,225 sessions) + 20 pathology archives | run `fetch_svd.py --per-class` for the full ~20 GB |
| **COUGHVID** | **FULLY OBTAINED** | **2.30 GB** | `public_dataset_v3.zip`, md5-verified; 34,434 recordings | `--extract`, then decode a sample to fix the sample rate |
| **Coswara** | **METADATA OBTAINED**, audio in flight | ~1.7 GB and climbing (of 13.00 GB) | all labels for 2,746 participants + 43 date manifests | let `fetch_coswara.py --audio` finish; then `--extract` |
| **PROCESS-2** | **SCRIPT-READY, BLOCKED ON GATE** | — | repo id resolved | accept the gate at `huggingface.co/datasets/CognoSpeak/PROCESS-2` |
| **Bridge2AI-Voice v3.1.0** | **BLOCKED ON DUA** (long lead time) | — | access path confirmed | apply for PhysioNet credentialing **now** |
| **Bridge2AI raw audio** | **BLOCKED ON SEPARATE DUA** | — | — | email `DACO@b2ai-voice.org` in parallel |
| NeuroVoz | BLOCKED ON DUA | — | — | Zenodo restricted request (OOD probe only) |
| PC-GITA | BLOCKED — no programmatic path | — | — | email the authors (OOD probe only) |
| VOICED | OPEN, not fetched | — | — | `wget -r -N -c -np https://physionet.org/content/voiced/1.0.0/` |
| PVQD | OPEN, not fetched | — | — | download from Mendeley `9dz247gnyb` v4 |
| DementiaBank / ADReSS | BLOCKED — consortium membership | — | — | membership application |
| DAIC-WOZ | BLOCKED — USC EULA | — | — | not recommended (see §4) |
| SAP | BLOCKED — institutional agreement | — | — | UIUC data agreement |
| mPower | BLOCKED — Synapse registration | — | — | low priority (self-report + repeats) |
| HPP-Voice | BLOCKED — request-based | — | — | low priority (Hebrew, small effects) |

**Nothing was faked.** Where a dataset is blocked, the exact blocker is named.

---

## 2. Obtained — details

### SVD — the primary target. **The survey's access path is obsolete.**
The web-form scraper (`rijulg/svd-downloader`) is not needed. `stimmdb.coli.uni-saarland.de`
is now a Next.js SPA that links its own bulk download to an **open Zenodo record**:

- **<https://zenodo.org/records/16874898>**, DOI `10.5281/zenodo.16874898`,
  concept DOI `10.5281/zenodo.16258834`, **CC-BY-4.0**, `access_right: open`.
- 73 files, **38.06 GB**. This resolves two of the survey's `[UNVERIFIED]` flags
  (the mirror DOI and the archive size).
- The **speaker metadata is NOT on Zenodo**: it is served separately at
  `https://stimmdb.coli.uni-saarland.de/data/voice_data.csv` (167 KB). It is the
  single most important file in the corpus — see `CARD_svd.md` §5.

Pilot proved the path end-to-end: 20 archives, every one md5-verified against
the Zenodo checksum, → **20 sessions / 20 distinct speakers**, all 20 matched
cleanly to `voice_data.csv`. See `data/CARD_svd.md`.

### COUGHVID — complete
2,297,542,075 bytes, md5 `7c6cdf184748a2600538c331ba0ba718`, matching Zenodo
exactly. **34,434 recordings** (the survey's ">25,000" undercounts).
Note: the archive was already on disk from a parallel process when my fetcher
ran; I verified the md5 independently rather than trusting the size match.
See `data/CARD_coughvid.md`.

### Coswara — metadata complete, audio downloading
All 2,746 participant labels and all 43 date manifests are on disk and
internally consistent (the 43 per-date CSVs sum to exactly the 2,746 ids in
`combined_data.csv`, with zero set difference).

---

## 3. Corrections to `corpus/SURVEY_datasets.md`

Measured, not quoted. Each of these changes a planning assumption.

| Dataset | Survey | Measured 2026-07-25 |
|---|---|---|
| SVD access | web-form scrape via `rijulg/svd-downloader` | **open Zenodo record, plain HTTP** |
| SVD Zenodo DOI | `[UNVERIFIED]` | **`10.5281/zenodo.16874898`** |
| SVD archive size | `[UNVERIFIED]` | **38.06 GB / 73 files** |
| SVD speakers | 2,043 | **1,853** unique `SprecherID` |
| SVD healthy | 687 | **869** healthy sessions / 833 pure-healthy speakers |
| SVD format | "WAV + EGG" | **`.nsp` + `.egg`** — needs conversion |
| Coswara size | "a few GB" | **13.00 GB** (16.75 GB with history) |
| Coswara subjects | 2,635 | **2,746** |
| COUGHVID size | "~1 GB" | **2.30 GB** |
| COUGHVID recordings | ">25,000" | **34,434** |
| COUGHVID concept DOI | `10.5281/zenodo.4048312` | **`10.5281/zenodo.4048311`** |
| PROCESS-2 HF repo | `[UNVERIFIED]` | **`CognoSpeak/PROCESS-2`** |

---

## 4. Speaker-disjoint splitting — the program's #1 requirement

Read this before designing any split.

| Dataset | Speaker id? | Verdict |
|---|---|---|
| **SVD** | **YES — `SprecherID`, 0 missing** | Fully supported. **But the archives are laid out by *session* (`AufnahmeID`), not speaker.** 200 of 1,853 speakers have >1 session (max 24), holding **25.7% of all sessions**. Grouping by directory name still leaks. Join on `AufnahmeID` → group by `SprecherID`. 21 speakers appear as *both* healthy and pathological and need a pre-registered rule. |
| **Coswara** | **YES — `id`, unique per row** | Groups a participant's 9 streams correctly. **Caveat:** `rU` ("returning user") is `y` for 63 and *missing for 680*; a repeat contributor gets a new `id` with nothing linking them. So `id` gives **submission-disjoint, not person-disjoint** splits. Say so in any claim. |
| **COUGHVID** | **>>> NO. NONE AT ALL. <<<** | `uuid` is per-**recording**: 34,434 rows, 34,434 unique, 0 duplicates. No participant/session/device/account id anywhere. **A speaker-disjoint split is impossible**, so COUGHVID cannot support an evaluation-tier claim. Use it only for self-supervised pretraining and OOD transfer — neither needs a within-corpus split. |

### Device fields — mostly missing, but Coswara is better than it first appears
Neither corpus records handset or microphone. But the §3.3 device check is
**partially executable on Coswara** and **not at all on COUGHVID**:

- **Coswara.** `combined_data.csv` has no device column, *but* the
  per-participant `metadata.json` inside the audio tarballs carries `dT`, a
  capture-platform flag (`web` 126 / `android` 1, **61% coverage** over 208
  participants sampled). Combine it with **sample rate** (measured: 48 kHz for
  198/207 files, 44.1 kHz for 9/207 — a real hardware signal at 100% coverage)
  plus `l_c`/`l_s` and `record_date`. That composite is a usable device proxy.
  You must extract the tarballs to get `dT` — a metadata-only workflow misses it.
- **COUGHVID.** Nothing at all. Only coarse `latitude`/`longitude` (43.6%
  missing) and `datetime`.

Report the specific handset/microphone as *unobserved* in both cases rather than
implying device was controlled.

### Other confounds already visible in the metadata
- **SVD age gap:** healthy median 22.8 y vs pathological median **52.9 y** — a
  30-year gap. Age alone is a strong classifier. A demographics-only baseline is
  mandatory; claim only the margin above it.
- **Coswara sex skew:** 69.2% male. **COUGHVID sex skew:** 62.6% male among
  those who reported (40% did not).
- **Coswara geography:** 91.6% India, 41% Karnataka — effectively single-site.
- **COUGHVID expert labels:** only ~820 of 34,434 recordings (2.4%) carry any
  expert annotation. Any expert-label claim is a ≤820-recording claim.

---

## 5. Blocked datasets — exact application paths

### PROCESS-2 — fastest unblock, highest headroom
- **Repo (resolved this session): <https://huggingface.co/datasets/CognoSpeak/PROCESS-2>**
  — `gated: manual`, public, 4,306 downloads, 13 likes, last modified 2026-06-29,
  audio + text, `size_categories: 1K<n<10K`. Owner `CognoSpeak` is the University
  of Sheffield group behind arXiv:2605.14888.
  *(A second repo, `Madhurananda/PROCESS-2`, is a tabular-only subset — `n<1K`,
  CSV, 2 downloads. Use `CognoSpeak/PROCESS-2`.)*
- **What the human must do:** sign in to HuggingFace → open the repo → complete
  the "provide your professional details to request access" form (all fields
  required, gate is **manually** reviewed by the owners) → wait for approval →
  `huggingface-cli login`, then `load_dataset("CognoSpeak/PROCESS-2")`.
- **Caveat:** 400 participants (200 HC / 150 MCI / 50 dementia) **fails the
  ≥500/class bar** — screening-tier only. Published macro-F1 0.59 (3-way) is
  essentially unsaturated, so it is still the best headroom per GPU-hour.

### Bridge2AI-Voice v3.1.0 — start the paperwork today (weeks of lead time)
- **URL: <https://physionet.org/content/b2ai-voice/3.1.0/>**
- Access level: **credentialed**. Verified verbatim from the page: *"Only
  credentialed users who sign the DUA can access the files."*
- **No training course required** (unlike MIMIC — confirmed on the page).
- DUA name: **"Bridge2AI Voice Registered Access Agreement"**.
- **What the human must do:** (i) create a PhysioNet account; (ii) apply for
  credentialed status — needs identity verification **plus a supervisor /
  institutional reference**, which is the slow step; (iii) sign the Registered
  Access Agreement on the project page.
- **Critical limitation, confirmed on the page:** *"The published Bridge2AI-Voice
  Adult Dataset contains derived features from the audio waveforms. This
  PhysioNet project does not contain raw audios."* End-to-end audio work is
  **not** possible from this tier.
- **Raw audio is a separate application**, in parallel: email
  **`DACO@b2ai-voice.org`** for the Synapse data-access committee; requires
  institutional sign-off.
- Download size: still not published — `[UNVERIFIED]`.

### Lower-priority gated corpora (OOD probes only; all fail the ≥500/class bar)
| Dataset | Path | What the human must do |
|---|---|---|
| NeuroVoz | Zenodo restricted record via Sci Data `s41597-024-04186-z` | paste the full DUA text + institutional details into the request box; tooling at `github.com/BYO-UPM/Neurovoz_Dababase` |
| PC-GITA | no programmatic path | email the authors directly |
| ADReSS / ADReSSo / ADReSS-M | <https://dementia.talkbank.org/> | DementiaBank consortium membership + T&C |
| DAIC-WOZ | USC ICT | sign the EULA. **Not recommended** — the interviewer-prompt shortcut (arXiv:2404.14463) makes it a trap unless all interviewer audio is stripped |
| SAP | UIUC | institutional data agreement |
| mPower | <https://www.synapse.org/mpower> (`syn4993293`) | Synapse account + qualified-researcher terms |
| HPP-Voice | Human Phenotype Project site | request as a qualified researcher |

### Open but not yet fetched (small, cheap, useful as OOD probes)
- **VOICED** — <https://physionet.org/content/voiced/1.0.0/>, fully open,
  `wget -r -N -c -np`. 208 voices.
- **PVQD** — <https://data.mendeley.com/datasets/9dz247gnyb/4>, direct download.
  296 recordings.

---

## 6. Host-specific gotchas (they will bite the next agent)

1. **Norton Antivirus MITM-intercepts all TLS on this machine** (issuer
   `CN=Norton Web/Mail Shield Root`). `certifi` fails every HTTPS handshake with
   `CERTIFICATE_VERIFY_FAILED`, and `curl` fails with `CRYPT_E_NO_REVOCATION_CHECK`.
   **Fix:** `import truststore; truststore.inject_into_ssl()` — reads the Windows
   trust store, which carries the Norton root. Already built into
   `scripts/_download.py`, so it is handled for every fetcher.
2. **`git clone` is unreliable here for large repos.** Coswara (13 GB) was lost
   twice — reaped at ~6 GiB, then `fatal: early EOF` at 4.4 GB. git cannot resume
   a broken clone. `fetch_coswara.py` uses resumable HTTP instead.
3. **Background jobs get reaped under memory pressure.** Every fetcher streams to
   a `.part` file and resumes via HTTP `Range`, so a reap costs time, not bytes.
4. **Windows console is cp1252** — printing `ä`/`ö` from the German pathology
   names crashes with `UnicodeEncodeError`. Run fetchers with
   `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`.
5. **GitHub's unauthenticated API is rate-limited per IP** and was already
   exhausted on this host. `fetch_coswara.py` picks up `GITHUB_TOKEN`/`GH_TOKEN`
   or falls back to `gh auth token`.
6. **A size match is not an integrity check.** `_download.py` re-verifies md5 on
   files that already exist when the host publishes a checksum — this caught a
   COUGHVID archive placed by a parallel process.

---

## 7. Duplicate directories — a second agent worked this task in parallel

A second agent acquired the same datasets concurrently into **different paths**.
Nothing is corrupted and the two efforts are complementary, but `data/raw/` now
holds two parallel sets. Decide which is canonical before building loaders.

| Mine (this card set) | Parallel agent's |
|---|---|
| `data/raw/svd/` — 20 pathology archives + `voice_data.csv` | `data/raw/svd_meta/` (all 71 per-pathology `overview_*.csv`), `data/raw/svd_pilot/` (incl. `healthy`) |
| `data/raw/coswara/` — metadata + audio shards | `data/raw/coswara_meta/` — metadata + `annotations/` |
| `data/raw/coughvid/` | *(shared — same directory)* |

Their `scripts/svd_remote_zip.py` reads individual members out of the Zenodo
archives over HTTP **without downloading the whole zip** — genuinely useful and
worth keeping alongside `fetch_svd.py`. Their `svd_fetch_overviews.py` harvested
all 71 zip-local `overview.csv` files, which is a good cross-check on the master
`voice_data.csv`.

**COUGHVID note:** the archive was already on disk from that agent when
`fetch_coughvid.py` ran. Rather than trusting the size match, its md5 was
recomputed independently and **matches Zenodo exactly**, so the file is genuine.
`_download.py` was then hardened to always re-verify a checksum on pre-existing
files instead of skipping on size alone.

## 8. Scripts

| Script | Purpose |
|---|---|
| `scripts/_download.py` | shared resumable/polite downloader; truststore injection; md5 verification |
| `scripts/fetch_svd.py` | SVD via Zenodo + the SPA metadata CSV (`--list/--metadata-only/--pilot/--per-class/--all/--files`) |
| `scripts/fetch_coswara.py` | Coswara via resumable HTTP (`--list/--metadata-only/--pilot/--dates/--audio/--extract`) |
| `scripts/fetch_coughvid.py` | COUGHVID via Zenodo (`--info/--extract`) |

All are idempotent — re-running skips completed files (re-verifying checksums
where available), so an interrupted fetch is resumed by simply running it again.
