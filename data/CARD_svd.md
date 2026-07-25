# Data Card — Saarbrücken Voice Database (SVD)

**Status:** PILOT OBTAINED (metadata complete, 20 pathology archives fetched).
**Verified:** 2026-07-25, against the live Zenodo API and the downloaded files themselves.
**Local path:** `data/raw/svd/` (gitignored — audio is never committed).

---

## 1. The headline finding: SVD needs no scraping

`corpus/SURVEY_datasets.md` describes SVD as served from a web export form at
`stimmdb.coli.uni-saarland.de` with bulk access via the third-party scraper
`github.com/rijulg/svd-downloader`, and marks the Zenodo mirror DOI `[UNVERIFIED]`.

**That path is obsolete.** The site is now a Next.js SPA whose own *"The complete
dataset is available for download here"* link points at an **open Zenodo record**:

| | |
|---|---|
| Record | <https://zenodo.org/records/16874898> |
| Record DOI | `10.5281/zenodo.16874898` |
| Concept DOI | `10.5281/zenodo.16258834` (always resolves to latest) |
| Licence | **CC-BY-4.0** |
| Access | `open` — no login, no DUA, no click-through |
| Files | 73 |
| Total | **38,059,544,640 bytes = 38.06 GB** |
| Creators | Pützer, Manfred; Barry, William J. |
| Hosted by | Essen University Hospital (formerly Institute of Phonetics, Saarland University) |

So acquisition is a plain HTTP fetch. `scripts/fetch_svd.py` does it directly
against the Zenodo API — resumable, md5-verified, politely rate-limited. The
scraper is not needed.

## 2. Source URLs

| Item | URL |
|---|---|
| Audio archives | `https://zenodo.org/api/records/16874898` → per-file `links.self` |
| **Speaker metadata table** | `https://stimmdb.coli.uni-saarland.de/data/voice_data.csv` |
| `.nsp` → WAV converter | `https://github.com/UMEssen/stimmdatenbank-converter` |
| Landing page | `https://stimmdb.coli.uni-saarland.de/` |
| Technical contact | `ahoy.ship@uk-essen.de` |
| Data contact | `manfred.puetzer@gmail.com` |

**The metadata CSV is NOT in the Zenodo record.** It is served separately by the
SPA and is the single most important file in the dataset for this program (see §5).
`fetch_svd.py` always fetches it.

## 3. Exact contents obtained

### Always fetched
- `voice_data.csv` — 167,457 bytes, 2,225 session rows + header. **Complete.**
- `zenodo_record.json` — full API response, kept as provenance.

### Audio pilot (20 smallest pathology archives, ~120 MB of the 38 GB)
Fetched to prove the path end-to-end; every file md5-verified against the Zenodo
checksum. Includes `Morbus Parkinson.zip`, `Chondrom.zip`, `Valleculacyste.zip`,
`Mediale Halscyste.zip`, `Carcinoma in situ.zip`, `Papillom.zip`, and 14 more.

### The record's two redundant encodings — do not download both
| Archive | Size | Note |
|---|---|---|
| `data.zip` | 17.88 GB | the complete corpus in one file |
| `healthy.zip` | 6.02 GB | the control speakers |
| 71 × `<Pathology>.zip` | 5.5 MB – 1.93 GB | one per pathology, German label |

`data.zip` and {`healthy.zip` + the 71 pathology zips} are **the same corpus twice**.
Take one or the other. The per-class zips (~20 GB) are the better choice: they
allow class-balanced partial downloads and make a pilot possible.
`fetch_svd.py --per-class` selects them and skips `data.zip`.

## 4. Corpus statistics (computed from `voice_data.csv`, not quoted)

| Quantity | Value |
|---|---|
| Sessions (recording IDs) | **2,225** |
| Unique speakers (`SprecherID`) | **1,853** |
| Pathological sessions (`AufnahmeTyp = p`) | **1,356** |
| Healthy sessions (`AufnahmeTyp = n`) | **869** |
| Pure-pathological speakers | **999** |
| Pure-healthy speakers | **833** |
| Speakers with *both* n and p sessions | **21** |
| Distinct pathology labels | **71** (15 with ≥30 sessions) |
| Recording date range | 1997-11-20 → 2004-06-16 |
| Language | German |

### Class balance
- **Session level:** 1,356 pathological / 869 healthy (60.9% / 39.1%).
- **Speaker level:** 999 pathological / 833 healthy, ignoring the 21 mixed.
- **Balanced speaker-disjoint pool: 833 per class** — comfortably clears the
  program's ≥500/class bar without touching the mixed speakers.

### Sex (complete — 0 missing)
| Class | Female (`w`) | Male (`m`) |
|---|---|---|
| Pathological speakers | 546 | 453 |
| Healthy speakers | 413 | 420 |

### Age at recording (derived from `Geburtsdatum` + `AufnahmeDatum`, 0 missing)
| Class | n | min | median | mean | max |
|---|---|---|---|---|---|
| Healthy (`n`) | 869 | 9.6 | 22.8 | 28.3 | 84.4 |
| Pathological (`p`) | 1,356 | 6.1 | **52.9** | 51.0 | 94.7 |

> **A 30-year median age gap between the classes.** Age alone is a very strong
> classifier here. A demographics-only baseline is mandatory for any SVD claim,
> and the reported margin must be the margin *above* it.

### Top pathologies (session level)
Rekurrensparese 197 · Hyperfunktionelle Dysphonie 143 · Laryngitis 82 ·
Funktionelle Dysphonie 75 · Dysphonie 70 · Spasmodische Dysphonie 62 ·
Psychogene Dysphonie 51 · Chordektomie 40 · Reinke Ödem 34 · Kontaktpachydermie 32

## 5. Metadata fields — speaker-disjoint splitting

`voice_data.csv` columns (all German-named):

| Column | Meaning | Missing | Role |
|---|---|---|---|
| `SprecherID` | **speaker id** | 0 | **the grouping key — `GroupKFold(groups=SprecherID)`** |
| `AufnahmeID` | recording/session id | 0 | session key; = the directory name inside each zip |
| `AufnahmeTyp` | `n` = normal, `p` = pathological | 0 | the label |
| `AufnahmeDatum` | recording date | 0 | session effects |
| `Geburtsdatum` | date of birth | 0 | → age at recording |
| `Geschlecht` | `w` = female, `m` = male | 0 | stratification (SOTA is reported per sex) |
| `Pathologien` | pathology label(s), comma-separated | 1,029 blank (= the healthy rows) | subset definition |
| `Diagnose` | free-text clinical note | 1,029 blank | qualitative only |

**Speaker id: PRESENT and complete.** Speaker-disjoint splitting is fully supported.

### The trap that will bite a careless split

The archives are laid out by **session**, not by speaker:

```
Morbus Parkinson.zip
├── overview.csv                       <- AufnahmeID -> SprecherID mapping
└── 1580/                              <- this is AufnahmeID (SESSION), NOT SprecherID
    ├── remarks/1580-remarks.txt
    ├── sentences/1580-phrase.nsp  +  1580-phrase-egg.egg
    └── vowels/  1580-{a,i,u}_{n,h,l,lhl}.nsp  + matching -egg.egg   (+ 1580-iau.nsp)
```

Every filename carries the **session** id. Grouping by directory name therefore
still leaks, because:

- **200 of 1,853 speakers have more than one session** (max **24** sessions for
  one speaker), and those speakers hold **572 of 2,225 sessions = 25.7% of the corpus**.
- **21 speakers appear as both healthy and pathological** (plausibly pre/post
  treatment). These carry contradictory labels at speaker level and need an
  explicit, pre-registered rule — drop them, or use only their first session.

> **Rule for this program:** join every recording to `voice_data.csv` on
> `AufnahmeID`, then group by `SprecherID`. Never group by the directory name.
> Report speaker-level n alongside recording-level n.

Note: each zip also carries its own `overview.csv` with the same schema, so the
mapping travels with the audio. The zip-local `Pathologien` is sometimes a
*single* label where the master `voice_data.csv` carries the full multi-label
string (e.g. session 1580 is `Morbus Parkinson` in the zip but
`Morbus Parkinson, Dysphonie` in the master). **Prefer the master CSV.**

## 6. Recordings per session, sample rate, format

Each session directory holds **14 recordings**, each as an `.nsp` + `.egg` pair
(28 files):

- **12 sustained vowels** — {`a`, `i`, `u`} × {`_n` normal, `_h` high, `_l` low,
  `_lhl` rising-falling} pitch.
- **1 vowel sequence** — `iau`.
- **1 German sentence** — `phrase`: *"Guten Morgen, wie geht es Ihnen?"*

So the corpus is ~2,225 × 14 ≈ **31,150 recordings** (plus the paired EGG channel).

**Format:** Kay/CSL `.nsp` (sound-pressure signal) with a parallel `.egg`
electroglottographic signal — **not WAV**, despite the landing page's
"High-Quality WAV Recordings" copy. Convert with
`github.com/UMEssen/stimmdatenbank-converter`.

**Sample rate: `[UNVERIFIED]` — not yet read from an `.nsp` header.** SVD is
widely documented at 50 kHz, but this card does not assert a number it has not
measured. Confirm from a header before it enters any preprocessing config.

## 7. Discrepancies vs `corpus/SURVEY_datasets.md`

| Survey claim | Measured | Note |
|---|---|---|
| "2,043 speakers" | **1,853** unique `SprecherID` | survey figure not reproducible from the released CSV |
| "687 healthy / 1,356 pathological" | 869 healthy / **1,356** pathological sessions | pathological count matches exactly; healthy does not |
| Zenodo DOI `[UNVERIFIED]` | `10.5281/zenodo.16874898` | **resolved** |
| "Archive size `[UNVERIFIED]`" | **38.06 GB** (73 files) | **resolved** |
| "WAV + EGG per session" | `.nsp` + `.egg` | WAV requires conversion |
| Bulk access via `rijulg/svd-downloader` | direct Zenodo HTTP | scraper obsolete |

The widely-cited "687 healthy" is likely a *subset* convention from the older web
interface rather than the full release. **Pre-register which convention this
program uses before the first sweep** — §2 of the survey already warns that the
pathology subset and audio material materially move the score.

## 8. Benchmark to hill-climb

Published SOTA: **UAR 85.61 (female) / 84.69 (male) / 85.22 (combined)** —
arXiv:2410.10537, with public code (Zenodo `10.5281/zenodo.13771573`) and a
REFORMS checklist. Reported per sex, so reproduce it per sex.
`[NEEDS VERIFICATION]` until reproduced on our own ladder.

## 9. Reproduce

```bash
python scripts/fetch_svd.py --list            # the 73-file table
python scripts/fetch_svd.py --metadata-only   # 167 KB — do this first
python scripts/fetch_svd.py --pilot --pilot-n 20
python scripts/fetch_svd.py --per-class       # ~20 GB, the real corpus
```
