# Data Card — Saarbrücken Voice Database (SVD)

**Acquired:** 2026-07-25 · **Tier:** full metadata inventory + 20-speaker audio pilot
**Artifacts:**
`autoresearch_results/acquisition/svd_inventory_stats.json` (per-archive structure)
`autoresearch_results/acquisition/svd_inventory_analysis.json` (balance + leakage)
**Producers:** `scripts/svd_remote_zip.py`, `scripts/svd_fetch_overviews.py`,
`scripts/analyze_svd_inventory.py`
**Inventory SHA-256:** `476378e2c4f38ec7d10d50ed10e011bf31ec03a7c24ea1ab1c0f121000bab33b`

---

## 1. Provenance and licence — *the survey's `[UNVERIFIED]` DOI is now resolved*

The old PHP export interface at `stimmdb.coli.uni-saarland.de` is **gone** (the help
page 404s; the site is now a static page). The database has been re-deposited:

| Field | Value |
|---|---|
| Zenodo record | `https://zenodo.org/records/16874898` |
| **DOI** | **`10.5281/zenodo.16874898`** |
| **Licence** | **CC-BY-4.0** (from the Zenodo API) |
| Access | **Fully open.** No account, no DUA, no gate. |
| Total deposit | **38.06 GB** across 73 files |
| Publication date field | 2008 |
| Maintainer contacts | `ahoy.ship@uk-essen.de` (technical), `manfred.puetzer@gmail.com` (data) |

The deposit is **one zip per pathology** plus `healthy.zip` (6.02 GB) and a
`data.zip` (17.88 GB) that mirrors everything else.

---

## 2. Acquisition method — no 38 GB download was needed

Zenodo serves `Accept-Ranges: bytes`. `scripts/svd_remote_zip.py` reads the ZIP64
central directory from the tail of each archive and extracts individual members by
byte range. The complete 72-archive inventory cost **~4 HTTP requests per archive**
and a few MB, instead of 38 GB.

`scripts/svd_fetch_overviews.py` ran over all 72 archives (`data.zip` skipped as a
duplicate) with **0 failures**.

**Pilot:** 20 healthy speakers, **558 files (278 `.nsp` + 278 `.egg` + 2 `.txt`),
245.2 MB, in 4 min 20 s**, at `data/raw/svd_pilot/healthy/` (git-ignored).
Files verified as genuine Kay Elemetrics NSP (`FORMDS16` magic + `HEDR` chunk).

> Performance note worth keeping: the naive per-member implementation needed
> ~2 requests per file and would have taken ~2 hours for the same pilot. Because zip
> members are stored contiguously, fetching the union byte-range **once** and slicing
> locally reduced it to a single request. `extract_many()` is the function to reuse.

---

## 3. Structure

Inside each archive: `<AufnahmeID>/{vowels,sentences,remarks}/` plus a root
`overview.csv`.

- `vowels/` — `/a/ /i/ /u/` at normal / high / low / low-high-low pitch
- `sentences/` — the German phrase *"Guten Morgen, wie geht es Ihnen?"*
- paired `-egg.egg` electroglottograph signal for every `.nsp`
- audio is **`.nsp` (Kay Elemetrics), not WAV** — a conversion step is required

Registry columns (`overview.csv`): `AufnahmeID`, `AufnahmeTyp` (`n`/`p`),
`AufnahmeDatum`, `Diagnose`, **`SprecherID`**, `Geburtsdatum`, `Geschlecht` (`m`/`w`),
`Pathologien`.

---

## 4. Class balance (measured)

**Shipped audio (speaker folders in the zips):**

| | folders |
|---|---|
| healthy | **687** |
| pathological (71 archives) | **1,625** |
| **total** | **2,312** |

**Registry (`overview.csv` rows, 72 archives concatenated):** 2,495 sessions ·
**2,225 unique `AufnahmeID`** · **1,853 unique `SprecherID`** ·
`AufnahmeTyp`: `p` = 1,626, `n` = 869.

By speaker: **854 healthy**, **1,020 pathological** (21 appear as both — see §5).
**≥500/class bar: met on either counting.**

### Two discrepancies to carry honestly

1. **Registry ⊃ shipped audio.** `overview_healthy.csv` lists **869** sessions but
   `healthy.zip` ships **687** folders — **182 registry rows have no audio**. Only 2
   of 72 archives mismatch at all (`healthy` by 182, one other by 1); all 71
   pathology archives match exactly. A loader that trusts `overview.csv` will
   silently mis-align the healthy class.
2. **The commonly cited "687 healthy / 1,356 pathological" is only half-confirmed.**
   687 matches the shipped healthy folders exactly. 1,356 matches neither the 1,625
   shipped pathological folders nor the 1,020 unique pathological speakers measured
   here. Do not quote 1,356 without reconciling it.

---

## 5. Speaker-disjoint splits — the headline finding

**SVD ships two different identifiers, and the wrong one is the obvious one.**

- `AufnahmeID` — the **session/recording** id. **This is also the folder name inside
  every zip**, so it is what any directory-walking loader will naturally group by.
- `SprecherID` — the **speaker** id. Not present in any file path.

Measured consequences:

| Measure | Value |
|---|---|
| Unique sessions (`AufnahmeID`) | 2,225 |
| Unique speakers (`SprecherID`) | **1,853** |
| Speakers with >1 session | **378** |
| Sessions belonging to those speakers | **1,020** |
| **Rows at risk if split on session id** | **40.88 %** |
| Max sessions by one speaker | **24** |
| Speakers appearing in >1 pathology archive | **306** |
| **Speakers appearing as both healthy and pathological** | **21** |

Examples of one speaker spanning several pathology archives:

- `1636` → Carcinoma in situ, Chordektomie, Dysphonie, Laryngitis, Taschenfaltenstimme
- `1887` → Dysphonie, Morbus Parkinson
- `1720` → Chondrom, Vox senilis

**Verdict: SUPPORTED, but only via `SprecherID`, which must be joined in from
`overview.csv`.** Splitting on the folder name — the path of least resistance — puts
the same speaker on both sides of the split for **up to 40.9 % of rows**. The 21
speakers recorded as both healthy *and* pathological are a second, independent
problem: they make the binary label itself speaker-ambiguous.

**Practical rule:** build the split on `SprecherID`; drop or explicitly assign the 21
cross-label speakers before any healthy-vs-pathological experiment; never rely on the
directory structure alone.

---

## 6. Confounds measured

**Sex** is recorded as `Geschlecht` (`m`/`w`); the corpus overall is female-skewed
(1,307 `w` of 2,495 rows). Per-class breakdown is in the artifact JSON under
`confounds.sex_healthy` / `confounds.sex_pathological` and must be reported per-class
in any result, per the reference benchmark's own practice of reporting UAR separately
for male and female.

**Pathology-subset selection** is the documented gaming surface for this corpus:
reported accuracy moves with which of the 71 pathologies are included and which audio
material is used. The subset must be pre-registered in git before any sweep.

**Age** is derivable from `Geburtsdatum` and `AufnahmeDatum`; not yet computed.

---

## 7. Audit hooks (what to re-test here)

1. **The primary audit target.** Reproduce the published reference result
   (UAR 85.61 female / 84.69 male / 85.22 combined, arXiv:2410.10537, public code)
   under its own protocol, then re-run under `SprecherID`-grouped CV and report the
   delta. The 40.9 %-at-risk figure above makes this a well-posed, pre-registerable
   audit with a real external number to hill-climb against.
2. Quantify what excluding the 21 cross-label speakers does to the same number.
3. Report per-sex UAR, never pooled only.

---

## 8. Reproduce

```bash
python scripts/svd_fetch_overviews.py        # full inventory, ~4 requests/archive
python scripts/analyze_svd_inventory.py      # balance + leakage artifact
python scripts/svd_remote_zip.py list  "healthy.zip"
python scripts/svd_remote_zip.py pilot "healthy.zip" --speakers 20 \
       --outdir data/raw/svd_pilot/healthy
```

`.nsp` → WAV conversion is still required before feature extraction (the Zenodo
description links a conversion tool). **Not yet done — flagged in
`ACQUISITION_STATUS.md`.**
