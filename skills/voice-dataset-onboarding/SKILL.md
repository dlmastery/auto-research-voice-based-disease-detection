---
name: voice-dataset-onboarding
description: >
  Use when adding ANY new voice corpus to the program, before a single feature is
  extracted. The eight-gate checklist: licence + DUA status, access path, speaker-
  id availability (a corpus with no speaker id cannot support an evaluation-tier
  claim — say so in the card), class balance and natural base rate, per-class n
  against the >=500 bar, the confound audit, the data card, and the ethics/PHI
  gate. Includes the measured SVD / Coswara / COUGHVID / PROCESS-2 / Bridge2AI
  status table and the host constraints (disk, TLS proxy, cp1252 console) that
  shaped every acquisition decision here.
---

# Skill — voice-dataset-onboarding

**Dataset access is the binding constraint on this program, not compute.** Start
every DUA application before writing code; never let the program stall waiting on
paperwork (`CLAUDE.md` §4.1).

Onboarding ends when a **data card** exists in `data/cards/` and the status board
in `ACQUISITION_STATUS.md` has a row. Not before.

---

## When to use

- Adding a corpus to `AXIS_TAXONOMY.md` A1's admissible values.
- Starting a DUA / credentialing application.
- Deciding whether a corpus can carry an **evaluation-tier** claim or only a
  screening / OOD / negative-control role.
- Re-verifying a corpus after an upstream re-deposit (SVD moved hosts and DOIs;
  see §3).

---

## 1. The eight gates

Each gate produces a **recorded value**, not a judgement. A gate that cannot be
answered is answered `UNKNOWN(reason)` — never left blank.

### G1 — Licence and DUA status
Record: licence id, whether a DUA exists, what it *binds* (non-commercial only?
no redistribution? no re-hosting? no biometric/speaker-verification training? no
re-identification? deletion on completion?), and whether access is revocable.

The binding terms change what may be built, not just what may be downloaded.
PROCESS-2's DUA prohibits public re-hosting, so **no PROCESS-2 audio or derived
excerpt may enter the dashboard or the repo — plan for metrics-only**. Discover
that at onboarding, not when the dashboard is being written.

### G2 — Access path, verified by execution
Record the exact URL/command, the byte size, and a checksum you computed
yourself. Verified examples from this repo:

- COUGHVID zip: **2,297,542,075 B**, SHA-256
  `37544c58ac5a7d79cb68af56fb3d0a690773b100bef8a03aac96570086fea335` — matches
  the Zenodo-declared size exactly.
- Coswara `combined_data.csv`: 359,150 B — matches the `git ls-tree -l` blob size.
- SVD Zenodo record `10.5281/zenodo.16874898`, **38.06 GB across 73 files**,
  inventory SHA-256 `476378e2c4f38ec7d10d50ed10e011bf31ec03a7c24ea1ab1c0f121000bab33b`.

### G3 — Speaker-id availability — **the gate that decides the corpus's tier**

> A corpus without a usable speaker identifier **cannot support an evaluation-tier
> claim**. Write that sentence into its data card at onboarding time.

Three verdict levels, all measured (never assumed from a paper):

| verdict | meaning | tier it permits |
|---|---|---|
| SUPPORTED | a speaker id exists and links every row | evaluation-tier |
| PARTIAL | an id exists but a bounded fraction of rows is unlinkable | evaluation-tier **with the bound stated in every row** |
| IMPOSSIBLE | no participant identifier of any kind | OOD probe / negative control only |

**Measure it, and beware the obvious key.** On SVD the natural key
(`AufnahmeID`, the zip folder name) is the *session*, not the speaker: grouping
on it leaves **40.88 %** of rows at risk. Details and the assertion code:
[voice-speaker-disjoint-splits](../voice-speaker-disjoint-splits/SKILL.md).

### G4 — Class balance and the natural base rate
Record every label value's n, the binary collapse you intend to use, **and the
natural base rate** — the prevalence in the wild, which is what a clinical PPV
would be computed against. Report the base rate even when you balance; balancing
is a modelling choice that hides the deployment prior.

Also record label **provenance**: self-report vs clinician-confirmed vs
PCR-referenced. These are not interchangeable, and a high AUC on a self-report
corpus may be measuring self-report behaviour (`SURVEY_datasets.md` §3.9).

### G5 — The ≥500/class bar
`>= 500` positives **and** `>= 500` negatives for an evaluation-tier claim. Below
that the corpus is **screening-tier only** and every number from it must be
labelled as such. PROCESS-2 (400 participants) fails the bar and is listed anyway
because its baselines are unsaturated (macro-F1 **0.59** 3-way, arXiv:2605.14888)
— but its rows carry the screening chip.

Pool-limited corpora are onboarded honestly: maximise within the pool and **say
so explicitly**, rather than quietly reporting a small slice as if it were the
whole.

### G6 — The confound audit
Run the pinned battery before any audio work:
[voice-confound-baseline](../voice-confound-baseline/SKILL.md). The corpus is not
onboarded until `AUC_conf_max` is in an artifact. On SVD this gate produced
finding F1 (age alone AUC **0.8709**) — i.e. the gate is not a formality; it can
be the most important number the corpus ever yields.

### G7 — The data card
`data/cards/CARD_<corpus>.md`, with: provenance + licence table, acquisition
method and cost, contents inventory, class balance, the G3 split verdict, the
confound-battery result, known gaps, and **every number carrying its producing
script and JSON artifact**. Existing cards are the template:
`data/cards/CARD_svd.md`, `CARD_coswara.md`, `CARD_coughvid.md`.

### G8 — Ethics, PHI and disk
No PHI is ever committed. No restricted corpus is redistributed. `data/raw/` is
git-ignored **in full** — verify with `git check-ignore` on the actual extensions
(`.nsp`, `.egg`, the zip) rather than trusting the pattern. Only cards, scripts,
split manifests (speaker ids hashed), and metric JSON enter git. **Voice is a
biometric.**

---

## 2. Discrepancies are findings, not nuisances

Every corpus onboarded here disagreed with its own paper. Record the delta; quote
the artifact, never the paper (R2).

- **Coswara**: the *Scientific Data* paper reports 2,635 individuals
  (1,819 neg / 674 pos / 142 recovered). The shipped CSV has **2,746 rows** and a
  different split. Quote the file.
- **COUGHVID**: widely cited as "> 25,000 recordings"; the shipped v3 archive
  holds **34,434**. Also: `status` is present on only **20,664 / 34,434 rows
  (60.0 %)**.
- **SVD**: `overview_healthy.csv` lists 869 sessions but `healthy.zip` ships
  **687 folders — 182 rows have no audio**. Any loader must **inner-join**. And
  the canonical "687 healthy / 1,356 pathological" split is only half-confirmed:
  687 matches the shipped healthy folders; **1,356 matches neither** the 1,625
  shipped pathological folders nor the 1,020 unique pathological speakers
  measured here. Needs reconciliation before it is quoted.

---

## 3. Status board (measured 2026-07-25)

| corpus | state | licence | on disk | speaker-disjoint split | tier it can carry |
|---|---|---|---|---|---|
| **SVD** | **ACQUIRED** — full 72-archive inventory + 20-speaker audio pilot | CC-BY-4.0 (Zenodo `10.5281/zenodo.16874898`, 38.06 GB / 73 files) | 245 MB pilot + 2 MB meta | **YES via `SprecherID`** (not the folder name) | **evaluation — primary target** |
| **Coswara** | **ACQUIRED** — metadata + 9 annotation files, no audio | CC-BY-4.0 | 2 MB | **PARTIAL** — `id` unique per row; 63 `rU` returning users unlinkable, ≤ 2.3 % residual | evaluation, bound stated (pos 681 / neg 1,433 binary) |
| **COUGHVID** | **ACQUIRED** — full 2.30 GB archive | CC-BY-4.0 | 2.30 GB | **IMPOSSIBLE** — 34,434 rows, 34,434 uuids, no participant id | **OOD probe / negative control only** |
| **PROCESS-2** | **BLOCKED — DUA.** Repo id resolved: [`CognoSpeak/PROCESS-2`](https://huggingface.co/datasets/CognoSpeak/PROCESS-2) (`gated: manual`) | DUA — non-commercial, **no public re-hosting** | — | expected YES (`PROCESS-2_rec__NNN/`), confirm on receipt | screening only (400 participants < 500/class) |
| **Bridge2AI-Voice v3.1.0** | **BLOCKED — credentialing + DUA** | Bridge2AI Registered Access (no CITI course) | — | expected YES | feature-tier only; **PhysioNet ships derived features, no raw audio** — raw audio is a separate Synapse/DACO application (`syn72370534`) |

**The next blocking step for the SVD audit is not a model — it is a codec.** SVD
audio is Kay Elemetrics `.nsp` (verified `FORMDS16` magic + `HEDR` chunk) and the
`.nsp → WAV` conversion **is not implemented**. See
[voice-embedding-extraction](../voice-embedding-extraction/SKILL.md) §2.

---

## 4. Host constraints that shape acquisition here

Recorded so they are not rediscovered the hard way.

1. **Disk is the ceiling.** The system drive was at **98 % full (~20–25 GB free
   of 953 GB)**. Two naive `git clone`s of `iiscleap/Coswara-Data` (**16.75 GB**;
   ≈ 30 GB with checkout) were started and killed.
2. **`git clone --filter=blob:none` without `--no-checkout` is a trap.** The
   automatic checkout lazily re-fetches every blob in HEAD, so it downloads the
   full archive anyway — observed as a 4.4 GB `tmp_pack` growing *after* a 13 KB
   "blobless" pack had landed. Use `--filter=blob:none --no-checkout` **plus**
   `git sparse-checkout set …`, or skip git entirely and fetch over
   `raw.githubusercontent.com` (15 files, 2 MB, seconds).
3. **Range requests beat downloads.** Zenodo serves `Accept-Ranges: bytes`.
   `scripts/svd_remote_zip.py` reads the ZIP64 central directory from an
   archive's tail and extracts members by byte range: the complete 72-archive SVD
   inventory cost ~4 HTTP requests per archive and a few MB instead of 38 GB. It
   works against any Zenodo deposit. Fetch the **union byte range once** and
   slice locally (`extract_many()`); the naive per-member version needed ~2
   requests per file and would have taken ~2 hours for the 20-speaker pilot
   instead of 4 min 20 s.
4. **This host's proxy breaks TLS** for Python's `ssl` module
   (`CERTIFICATE_VERIFY_FAILED`) and for default `curl`
   (`CRYPT_E_NO_REVOCATION_CHECK`). All fetching uses
   `curl --ssl-no-revoke` invoked via `subprocess`.
5. **The Windows cp1252 console kills unicode.** Printing German pathology names
   (umlauts) raised `UnicodeEncodeError` and killed a fetch mid-run. Sanitise
   console output, and **checkpoint the JSON artifact after every unit of work**
   so a late crash still leaves the data.

---

## 5. Worked example — onboarding COUGHVID, and why it got demoted

1. **G1** CC-BY-4.0 from the Zenodo API (`metadata.license.id = cc-by-4.0`); no
   account, no DUA, no gate.
2. **G2** one file, 2,297,542,075 B, SHA-256 `37544c58…`, 207 s, HTTP 200 —
   size matches Zenodo's declared value exactly.
3. **G3** 34,434 rows, **34,434 unique `uuid`s, no participant identifier of any
   kind → IMPOSSIBLE.** Geolocation clusters (269 recordings at Lausanne) but is
   rounded to 0.1° and identifies a city, not a person.
4. **G4/G5** `status` present on 60.0 % of rows; healthy 15,476 / COVID-19 1,315
   (10,132 / 720 at `cough_detected ≥ 0.8`). Both classes clear 500 unfiltered.
5. **Verdict** — the ≥500/class bar passes and the corpus is the largest open one
   available, **and it still cannot carry an evaluation-tier claim**, because G3
   failed. Its card says so, and it says the consequence plainly: *every published
   COUGHVID number is an upper bound of unknown tightness.* COUGHVID's role in
   this program is OOD transfer and negative control.

That is the shape of a correct onboarding: the size gate and the id gate are
independent, and the id gate wins.

---

## 6. Anti-patterns

| anti-pattern | consequence | do instead |
|---|---|---|
| Extracting features before the card exists | numbers with no provenance; R1 deletes them | card first, then features |
| Quoting the paper's n | Coswara's paper says 2,635; the file has 2,746 | compute from the checksummed file; quote the artifact |
| "We'll find the speaker id later" | the corpus silently carries an evaluation claim it cannot support | G3 is a blocking gate; record IMPOSSIBLE and demote |
| Grouping by the directory name | 40.88 % of SVD rows leak, and it *looks* like a group split | identify the true speaker key and name it in the config |
| Trusting the registry CSV over the files on disk | 182 SVD rows have no audio | inner-join manifest to disk before splitting |
| Starting the DUA after the code is written | weeks of stall; Bridge2AI credentialing is slow | start every application on day one, in parallel |
| Downloading the whole deposit to read a manifest | 38 GB on a 98 %-full disk | HTTP range reads (`scripts/svd_remote_zip.py`) |
| Planning a dashboard around DUA'd audio | PROCESS-2's DUA forbids public re-hosting | discover binding terms at G1; plan metrics-only |
| Reporting a balanced set without the natural base rate | hides the deployment prior | report both |

---

## Definition of done

- [ ] `data/cards/CARD_<corpus>.md` exists, every number traced to a script + JSON.
- [ ] `ACQUISITION_STATUS.md` has a status-board row and a DUA next-action list.
- [ ] G3 verdict recorded as SUPPORTED / PARTIAL(bound) / IMPOSSIBLE, **measured**.
- [ ] Per-class n vs the ≥500 bar recorded; tier (evaluation / screening / OOD)
      stated explicitly, with the pool cap named if pool-limited.
- [ ] `AUC_conf_max` from the pinned battery is in an artifact.
- [ ] Licence + binding DUA terms recorded, including what they forbid building.
- [ ] `git check-ignore` verified on the real extensions; no audio, no PHI in git.
- [ ] Discrepancies against the corpus's own paper written down, not smoothed over.
- [ ] The corpus is added to `AXIS_TAXONOMY.md` A1 with its tier restriction.

---

## Cross-references

- Status board and DUA next-actions: `../../ACQUISITION_STATUS.md`
- Card templates: `../../data/cards/CARD_svd.md`, `CARD_coswara.md`, `CARD_coughvid.md`
- Dataset survey + the 8 documented traps: `../../corpus/SURVEY_datasets.md` §3
- Split gate (G3's machinery): [`../voice-speaker-disjoint-splits/SKILL.md`](../voice-speaker-disjoint-splits/SKILL.md)
- Confound gate (G6): [`../voice-confound-baseline/SKILL.md`](../voice-confound-baseline/SKILL.md)
- Extraction, incl. the `.nsp` blocker: [`../voice-embedding-extraction/SKILL.md`](../voice-embedding-extraction/SKILL.md)
- Meta-process split audit: [`../../meta-skills/autoresearch-data-split-audit/SKILL.md`](../../meta-skills/autoresearch-data-split-audit/SKILL.md)
- Acquisition tooling: `scripts/svd_remote_zip.py`, `scripts/svd_fetch_overviews.py`,
  `scripts/analyze_svd_inventory.py`, `scripts/analyze_coswara_meta.py`,
  `scripts/analyze_coughvid_meta.py`
