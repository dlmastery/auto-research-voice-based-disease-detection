# ACQUISITION_STATUS

**Last updated:** 2026-07-25 · **Owner:** data-acquisition (CPU/network, no GPU)
**Scope:** open voice-health corpora for the claim-audit program.

Data cards: [`data/cards/CARD_svd.md`](data/cards/CARD_svd.md) ·
[`data/cards/CARD_coswara.md`](data/cards/CARD_coswara.md) ·
[`data/cards/CARD_coughvid.md`](data/cards/CARD_coughvid.md)

---

> ## ⚠ LIVE DISK ALERT — 2026-07-25, needs a decision
>
> A **parallel agent is actively downloading full Coswara audio** into
> `data/raw/coswara/` (49 date directories, **6.96 GB and growing** at the time of
> writing) plus SVD pathology zips into `data/raw/svd/` (181 MB), using its own
> `scripts/fetch_coswara.py` / `fetch_svd.py` / `fetch_coughvid.py`.
>
> **Free space is down to ~20 GB of 953 GB (98 % full). Coswara audio totals ~16 GB,
> so this run will not fit.** It was left running rather than killed, because it is
> another agent's deliberate work — **the lead should decide.**
>
> This also **duplicates work already complete here**: Coswara metadata is acquired
> and analysed (§2, §3), and the audit questions this task was set do not need Coswara
> audio. Recommend stopping that fetch, or scoping it to one date shard.

## 1. Status board

| Dataset | State | Licence | On disk | Speaker-disjoint split | Audit-ready |
|---|---|---|---|---|---|
| **SVD** | **ACQUIRED** — full 72-archive inventory + 20-speaker audio pilot | CC-BY-4.0 | 245 MB pilot + 2 MB meta | **YES via `SprecherID`** (not the folder name) | **YES — primary target** |
| **Coswara** | **ACQUIRED** — metadata + annotations (no audio) | CC-BY-4.0 | 2 MB | **PARTIAL** — `id` is per-row; ≤63 unlinkable repeats | YES |
| **COUGHVID** | **ACQUIRED** — full 2.30 GB archive | CC-BY-4.0 | 2.30 GB | **IMPOSSIBLE — no participant id exists** | As negative control / OOD only |
| **PROCESS-2** | **BLOCKED — DUA** | DUA ("other") | — | Expected YES (`PROCESS-2_rec__NNN/`) | Pending |
| **Bridge2AI-Voice** | **BLOCKED — credentialing + DUA** | Bridge2AI Registered Access | — | Expected YES | Pending |

**No audio is committed.** `data/raw/` is git-ignored in full; verified with
`git check-ignore` on `.nsp`, `.egg`, and the COUGHVID zip. Only data cards, analysis
scripts, and JSON artifacts enter git.

---

## 2. What was acquired, with provenance

Every headline number is computed by a script and read out of a JSON artifact
(CLAUDE.md R1/R2). No number below is quoted from a paper.

| Artifact | Producer |
|---|---|
| `autoresearch_results/acquisition/svd_inventory_stats.json` | `scripts/svd_fetch_overviews.py` |
| `autoresearch_results/acquisition/svd_inventory_analysis.json` | `scripts/analyze_svd_inventory.py` |
| `autoresearch_results/acquisition/coswara_meta_stats.json` | `scripts/analyze_coswara_meta.py` |
| `autoresearch_results/acquisition/coughvid_meta_stats.json` | `scripts/analyze_coughvid_meta.py` |

Reusable tooling: **`scripts/svd_remote_zip.py`** reads ZIP64 central directories over
HTTP range requests and extracts members without downloading the archive. It works
against any Zenodo deposit, not just SVD.

### Integrity checks performed
- COUGHVID zip: **2,297,542,075 B**, SHA-256
  `37544c58ac5a7d79cb68af56fb3d0a690773b100bef8a03aac96570086fea335` — byte size
  matches the Zenodo-declared size exactly.
- Coswara `combined_data.csv`: 359,150 B — matches the `git ls-tree -l` blob size exactly.
- SVD pilot `.nsp` files: verified `FORMDS16` + `HEDR` magic (genuine Kay Elemetrics NSP).
- SVD inventory: 72/72 archives fetched, **0 failures**.

---

## 3. The three split verdicts (the reason this task existed)

1. **SVD — SUPPORTED, but the obvious key is the wrong one.** `AufnahmeID` (session)
   is the zip folder name and is what a directory-walking loader will group by.
   `SprecherID` (speaker) exists only in `overview.csv`. **378 speakers hold 1,020
   sessions → 40.88 % of rows are at risk if you split on the folder name**; one
   speaker has 24 sessions; 306 speakers span multiple pathology archives; **21
   speakers appear as both healthy and pathological**.
2. **Coswara — PARTIAL.** `id` is unique per row (2,746/2,746), so `GroupKFold` on
   `id` is well-defined, but `rU` marks **63 self-declared returning users** who
   re-submitted under a new `id` with **no linking field** (a further 680 rows leave
   `rU` blank). Residual leakage ≤2.3 % of rows and irreducible from shipped metadata.
3. **COUGHVID — IMPOSSIBLE.** 34,434 rows, 34,434 unique `uuid`s, **no participant
   identifier of any kind**. Every published COUGHVID number is an upper bound of
   unknown tightness. Geolocation clusters heavily (269 recordings at Lausanne) but
   is rounded to 0.1° and identifies a city, not a person.

---

## 4. DUA next-actions

### 4.1 PROCESS-2 — HuggingFace, gated (fast; do this first)

**Repo id resolved (was `[UNVERIFIED]` in the survey):
[`CognoSpeak/PROCESS-2`](https://huggingface.co/datasets/CognoSpeak/PROCESS-2)** —
`gated: manual`, public, 4,306 downloads, 13 likes, last modified 2026-06-29.
A second copy exists at `Madhurananda/PROCESS-2` (first author's account, `gated:
manual`, holds `meta-info.csv`); **treat `CognoSpeak/PROCESS-2` as canonical.**

Contents confirmed from the file listing: `PROCESS-2_rec__NNN/` directories, each with
`__CTD`, `__PFT`, `__SFT` as paired `.wav` + `.txt`. **The participant id is the
directory name**, so speaker-disjoint splitting should be straightforward — to be
confirmed on receipt.

**Next actions**
1. Log in to HuggingFace and open the dataset page; complete the access form
   ("provide your professional details… all fields are required").
2. Accept the DUA. Binding terms: non-commercial academic research only; **no
   re-identification, no redistribution, no public re-hosting, no biometric/
   speaker-verification training, no surveillance use**; institutional storage with
   restricted access; delete on project completion; cite the dataset and avoid
   quoting identifiable speech excerpts in publications.
3. On approval: `huggingface-cli login`, then `load_dataset("CognoSpeak/PROCESS-2")`.
4. **Blocker to flag:** the DUA prohibits public re-hosting — no PROCESS-2 audio or
   derived excerpts may go into the dashboard or the repo. Plan for metrics-only.

*Turnaround and approver are not stated on the page.* Access is revocable.

### 4.2 Bridge2AI-Voice v3.1.0 — PhysioNet credentialed + DUA (slow; start now)

Confirmed from `https://physionet.org/content/b2ai-voice/3.1.0/`:
- Access: *"Only credentialed users who sign the DUA can access the files."*
- Licence: **Bridge2AI Voice Registered Access License**
- **No CITI training course is required** for this dataset (unlike MIMIC).
- **The PhysioNet release contains derived features only — no raw audio.** Parquet
  feature files + TSV phenotype/metadata folders. Total size is not published.

**Next actions**
1. Create a PhysioNet account and apply for **credentialed** status (institutional
   details + a reference). *Exact field list and turnaround are not documented on the
   public pages —* `[UNVERIFIED]`; expect weeks, so start immediately.
2. Sign the Bridge2AI Voice Registered Access DUA on the project page.
3. **Raw audio is a separate application**: email `DACO@b2ai-voice.org` for
   institutional approval; audio is delivered via Synapse at
   **`https://www.synapse.org/Synapse:syn72370534/`**. Start this in parallel — it
   gates any end-to-end audio work.
4. **Design implication:** if only the feature tier lands, Bridge2AI supports
   *feature-space* audits only, not waveform-level reproduction. Do not plan a
   raw-audio experiment against it until DACO approves.

---

## 5. Known gaps / not yet done

- **SVD `.nsp` → WAV conversion is not implemented.** Audio is Kay Elemetrics NSP;
  a converter is required before feature extraction. **This is the next blocking
  step for the SVD audit.**
- SVD **age** is derivable from `Geburtsdatum` + `AufnahmeDatum` but is not yet computed.
- SVD registry/audio mismatch: `overview_healthy.csv` lists 869 sessions, `healthy.zip`
  ships 687 folders — **182 rows have no audio**. Any loader must inner-join, not trust
  the CSV.
- The widely cited SVD split "687 healthy / 1,356 pathological" is only half-confirmed:
  687 matches shipped healthy folders; **1,356 matches neither** the 1,625 shipped
  pathological folders nor the 1,020 unique pathological speakers measured here.
  Needs reconciliation before it is quoted.
- COUGHVID audio has not been extracted from the zip (not needed for the card).
- Coswara audio (~16 GB of tar shards) has not been fetched; only a per-date pilot
  would be needed, and only if a Coswara audio experiment is scheduled.

---

## 6. Host constraint that shaped every decision

The system drive is **98 % full (~25 GB free of 953 GB)**. This is a hard ceiling on
acquisition and it forced the range-request approach throughout.

**Two naive `git clone`s of `iiscleap/Coswara-Data` were started and stopped**: the
repo is **16.75 GB** (`gh api repos/iiscleap/Coswara-Data --jq .size` → `16753933` KB)
and a full clone plus checkout is ≈30 GB — it would have exhausted the disk.

> **The trap worth remembering:** `git clone --filter=blob:none` *without*
> `--no-checkout` is **not** safe. The automatic checkout lazily re-fetches every blob
> in HEAD, so it downloads the full archive anyway — observed here as a 4.4 GB
> `tmp_pack` growing after a 13 KB "blobless" pack had already landed.
> Use `--filter=blob:none --no-checkout` **plus** `git sparse-checkout set …` before
> any checkout — or, better for a handful of files, skip git and fetch over
> `raw.githubusercontent.com`.

**Network note:** this host's proxy breaks TLS for Python's `ssl` module
(`CERTIFICATE_VERIFY_FAILED`) and for default `curl` (`CRYPT_E_NO_REVOCATION_CHECK`).
**All fetching uses `curl --ssl-no-revoke`**, invoked via `subprocess` from Python.

**Console note:** printing German pathology names (umlauts) to the cp1252 Windows
console raised `UnicodeEncodeError` and killed a run mid-fetch — exactly the failure
mode the constitution warns about. `svd_fetch_overviews.py` now sanitises console
output and checkpoints its JSON after every archive.
