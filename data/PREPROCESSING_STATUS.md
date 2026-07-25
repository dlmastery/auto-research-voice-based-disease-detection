# Audio preprocessing status

Canonical form for every corpus: **16 kHz mono float32 WAV** in
`data/interim/<corpus>/`, with `manifest.csv` as the contract every downstream
stage consumes.

Produced by `scripts/preprocess_audio.py` (decoder for Kay/CSL NSP lives in
`scripts/nsp_reader.py`). Run on CPU only; no GPU, no neural model.

| corpus | found | decoded | failed | speakers | audio | speaker-disjoint split |
|---|---:|---:|---:|---:|---:|---|
| SVD | 667 | **667** | 0 | 49 | 44.8 min | **YES** |
| COUGHVID | 13 535 | _(see below)_ | | 0 real speakers | | **NO — blocker** |
| Coswara | 24 700 est. | _(partial)_ | | 2 746 available | | **YES** |

---

## Manifest contract

`data/interim/<corpus>/manifest.csv`, required columns first:

```
path,corpus,speaker_id,session_id,label,sex,age,duration_s,orig_format,sha256
```

then the extras `pathology,task,speaker_id_provenance,orig_sample_rate,src_sha256`.

- `sha256` digests the **decoded 16 kHz waveform**, so identical audio appearing
  twice under different names or container formats collides. This is the
  leakage check — see the SVD duplicate finding below.
- `src_sha256` digests the source file, for provenance.
- **A row with no `speaker_id` is a fatal error, not a warning.** Such files are
  excluded from the manifest, written to `failures.csv`, and counted under
  `excluded_no_speaker_id` in `summary.json`.
- `speaker_id_provenance` is `participant` (the corpus identifies the human, so
  speaker-disjoint splitting is real) or `recording_proxy` (the corpus only
  identifies the recording — the id **cannot** support a speaker-disjoint
  claim). Every downstream splitter must refuse to make a generalisation claim
  on a `recording_proxy` corpus.

Each corpus also gets `failures.csv` (file, reason) and `summary.json`.

---

## SVD — COMPLETE

### Which decoder worked for `.nsp`: a purpose-written parser

`soundfile` and `librosa` are **not installed** in `C:\Users\evija\anaconda3`,
and **ffmpeg 8.1.1 cannot open the format either** — `.nsp` is a Kay Elemetrics
Computerized Speech Lab container, not RIFF/WAV. The working path is the
pure-Python parser in `scripts/nsp_reader.py`, written from a hexdump of the
actual bytes:

```
offset  bytes  content
0       8      magic b"FORMDS16"
8       4      uint32 LE  size of everything after byte 12  (== filesize - 12)
12      ...    chunk stream: 4-byte ascii id, uint32 LE size, payload (word-aligned)

HEDR  32 bytes   0..19  ascii timestamp, e.g. b"Nov 20 14:49:57 1997"
                 20..23 uint32 LE sample rate   -> 50000 for all 1058 SVD files
                 24..27 uint32 LE sample count
                 28..31 int16 x2 peak amplitude per channel (-1 = channel absent)
SDA_  N bytes    int16 LE PCM, channel A
```

Two departures from canonical IFF/RIFF that break generic readers: the form type
(`DS16`) comes **before** the size field, and all sizes are **little**-endian.

Structure verified across **all 785 files** in `data/raw/svd_pilot/healthy/`:
778 parse cleanly with exactly the chunk set `{HEDR, SDA_}` and sample rate
50 000 Hz; the other 7 are `.txt`/`.json` sidecars, not audio.

Where the `HEDR` sample count and the `SDA_` payload disagree (observed on
`10-iau-egg.egg`: header 1 884 799 samples, payload 1 883 775) the payload wins.

### Evidence the decode is correct, not just non-crashing

Physical plausibility — sustained vowels land where SVD says they should:

| file | duration | RMS | peak |
|---|---:|---:|---:|
| `10-a_h.nsp` | 1.454 s | 0.250 | 0.853 |
| `10-a_n.nsp` | 2.110 s | 0.192 | 0.736 |
| `10-phrase.nsp` | 2.113 s | 0.207 | 1.000 |

Median duration over all 778 pilot files is **1.38 s** (range 0.53–77.7 s; the
long tail is the `iau` continuous pitch-glide task). No silence, no clipping-noise.

The decisive check is that the waveform is *voice* with the pitch the metadata
predicts. Autocorrelation F0 on the steady portion of sustained vowels:

| file | F0 | periodicity | sex in `voice_data.csv` |
|---|---:|---:|---|
| `10-a_n.nsp` | 200.8 Hz | 0.977 | w (female) |
| `10-i_n.nsp` | 203.3 Hz | 0.976 | w |
| `10-u_n.nsp` | 204.9 Hz | 0.847 | w |
| `12-a_n.nsp` | 221.2 Hz | 0.974 | w |
| `1852-a_n.nsp` | 233.6 Hz | 0.968 | w |

Three different vowels from session 10 give 200.8 / 203.3 / 204.9 Hz — the same
speaker's pitch recovered independently three times — and every value sits in
the female modal range (165–255 Hz), matching the metadata sex. A byte-order or
offset error could not produce that.

Resampling 50 kHz → 16 kHz uses `scipy.signal.resample_poly` at the exact
rational ratio 8/25 (polyphase FIR, proper anti-aliasing, no drift).

### Metadata join

Filenames are `<AufnahmeID>-<task>.nsp` (`10-a_h.nsp` → session 10, task `a_h`).
The numeric prefix joins to `svd_meta/svd_inventory.csv` (= `voice_data.csv`
plus an `_archive` column naming the pathology), which carries `SprecherID`,
`Geschlecht`, `Geburtsdatum` and `Pathologien`. Age is computed from birth date
minus recording date. All 49 sessions resolved; **0 files dropped for a missing
speaker id**.

### Result

667 `.nsp` decoded, **0 failures**: 387 healthy (29 speakers, from
`svd_pilot/`) + 280 pathological (20 speakers, from the 20 zips extracted to
`data/raw/svd_extracted/`). 44.8 min of audio, 14 tasks per speaker
(`a_/i_/u_` × `n/h/l/lhl`, plus `iau` and `phrase`).

The `.egg` files decode with the same parser but are **excluded from the audio
manifest**: electroglottography is a contact-sensor signal, not a microphone
recording, and feeding it to an audio embedding model would be a category error.
Add `--include-egg` support if a downstream stage ever wants them.

### Three findings the modelling stage must not ignore

**1. Only 49 speakers are on disk, and pathology is perfectly confounded with
speaker.** Each of the 20 pathology zips contains exactly **one** session, so
every pathology is represented by exactly one person (14 files each). A
multi-class pathology classifier trained on this cannot distinguish "pathology"
from "speaker identity" — the two are the same variable. Only the binary
healthy-vs-pathological task is meaningful, and at 49 speakers a
speaker-disjoint test fold holds ~10 people, so the 95% CI on any accuracy is
roughly ±15 pp. **This is screening-tier data, not evaluation-tier.**

**2. The acquisition is 20 of 72 archives, and it got the 20 smallest.** SVD
metadata describes 2 225 sessions from 1 853 speakers. The downloaded archives
are the single-session rarities; the 52 missing archives hold **1 344
pathological sessions from 1 010 speakers**:

| missing archive | sessions | | missing archive | sessions |
|---|---:|---|---|---:|
| Hyperfunktionelle Dysphonie | 213 | | Psychogene Dysphonie | 91 |
| Rekurrensparese | 213 | | Kontaktpachydermie | 71 |
| Laryngitis | 140 | | Reinke Ödem | 68 |
| Funktionelle Dysphonie | 112 | | Spasmodische Dysphonie | 64 |
| Dysphonie | 101 | | Chordektomie | 59 |

Fetching these is the highest-value action available to the program — it is
worth roughly 20× the current pathological speaker count, and it is what turns
SVD from screening-tier into evaluation-tier. The healthy side needs the same
treatment: 854 healthy speakers exist, 29 are on disk.

**3. Age is a strong confounder; duration is not.** Per-speaker age alone
separates the classes at **AUC 0.741** (healthy mean 30.3 y, pathological mean
48.9 y — an 18.6-year gap). Any SVD classifier must be reported against an
age-only baseline, or it is measuring voice ageing. Duration is comparatively
clean (AUC 0.563), and the per-task duration distributions match across classes
except `phrase` (1.85 s healthy vs 2.22 s pathological). Sex is also skewed on
the pathological side (5 F / 15 M vs 15 F / 14 M healthy).

**Duplicate audio (benign, but dedupe before counting).** 30 files share 13
distinct waveform hashes. Every collision is **within a single speaker** —
never across speakers — so there is no train/test leakage under a
speaker-disjoint split. It is SVD storing one take under several pitch-condition
names (e.g. `1338-a_n`, `1338-a_l`, `1338-a_lhl` are byte-identical). 17 rows
are redundant; drop them before quoting a per-file `n`.

---

## COUGHVID

### Speaker id: NOT AVAILABLE — this corpus cannot support a speaker-disjoint claim

`metadata_compiled.csv` has 34 434 rows and 34 434 distinct `uuid`s. There is
**no participant, user, or subject column** — the only identifier is the
per-recording uuid. Nothing links two recordings to the same person, and the
dataset was collected via an anonymous web form that people could submit
repeatedly.

The manifest therefore sets `speaker_id = coughvid_<uuid>` with
`speaker_id_provenance = recording_proxy`, and `summary.json` reports
`speaker_disjoint_split_possible: false`.

**Consequence: COUGHVID is usable for pretraining, augmentation and as an
out-of-distribution probe. It must not carry a generalisation claim** — a
"speaker-disjoint" split over uuids is not speaker-disjoint, because one person
may appear in both halves and there is no way to detect it.

### Selection and decoding

Media in the zip: 29 348 `.webm`, 3 309 `.wav`, 1 777 `.ogg` (2.9 GB
uncompressed). Decoded with **ffmpeg 8.1.1** (`-f f32le -ar 16000 -ac 1`),
streaming one member at a time out of the 2.2 GB archive — full extraction does
not fit the free disk on this host.

Applied the standard CoughVID quality protocol: `cough_detected >= 0.8` **and** a
non-null `status`, giving **13 535** recordings — healthy 10 132, symptomatic
2 683, COVID-19 720. Both filters are flags (`--cough-threshold`,
`--include-unlabeled`) if a later stage wants the full 34 434.

<!--COUGHVID_RESULT-->

---

## Coswara

### Speaker id: available and real

Each date archive expands to `<participant_id>/<recording>.wav`, and the
participant directory name joins to `combined_data.csv` `id` (2 746
participants, all distinct). `speaker_id_provenance = participant`, so
**speaker-disjoint splitting is possible**. Nine recordings per participant:
`breathing-{deep,shallow}`, `cough-{heavy,shallow}`, `counting-{fast,normal}`,
`vowel-{a,e,o}`.

Labels: healthy 1 433, positive_mild 426, no_resp_illness_exposed 248,
positive_moderate 165, resp_illness_not_identified 157, recovered_full 146,
positive_asymp 90, under_validation 81.

### Extraction

Each `<date>/` holds a single tarball split across parts
(`<date>.tar.gz.aa`, `.ab`, …). Parts are concatenated in sorted order, untarred
to a temp dir, decoded, and the temp dir removed — the source is 13 GB
compressed and cannot be expanded in place.

<!--COSWARA_RESULT-->

---

## Environment notes

- Interpreter `C:\Users\evija\anaconda3\python.exe` (numpy 1.26.4, pandas 2.1.4,
  scipy 1.11.4). **`soundfile`, `librosa`, `torchaudio`, `audioread` are all
  absent** — nothing in this pipeline needs them.
- `ffmpeg` 8.1.1 on PATH, used for every container except `.nsp`.
- Decoding parallelises with `--workers` (one ffmpeg subprocess per file, so it
  is spawn-bound); 12 workers gave a ~5× speedup over serial.
- Set `PYTHONIOENCODING=utf-8`: the Windows console is cp1252 and German
  pathology names (`Internusschwäche`, `Reinke Ödem`) crash an unset one.
- **Disk is the binding constraint on this host: ~15 GB free of 953 GB.**
  Coswara at full size would need ~16 GB decoded, so the runner takes
  `--max-output-gb` / `--min-free-gb` and stops cleanly between date archives
  rather than filling the volume; `summary.json` then records
  `complete: false` with the reason.
