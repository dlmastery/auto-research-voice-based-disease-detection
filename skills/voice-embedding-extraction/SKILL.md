---
name: voice-embedding-extraction
description: >
  Use when extracting frozen SSL / foundation-model embeddings (WavLM, wav2vec2,
  Whisper encoder, HeAR, OPERA) from clinical audio on a 16 GB laptop. Covers the
  SVD .nsp -> WAV conversion blocker, resample/mono/normalise discipline, VAD vs
  fixed windows, pooling choices, content-hash-keyed .npz caching, and the hard
  rule that embeddings are extracted ONCE and never re-extracted per fold. Frozen
  encoders only — fine-tuning large audio encoders is off-thesis for this program.
---

# Skill — voice-embedding-extraction

The whole program runs on **frozen embeddings + a small head**. That is not a
compute compromise, it is the thesis: the field's open questions are about
*protocol* (splits, confounds, calibration), not about representation learning,
so **the compute budget goes to protocol rigor**, not to training encoders
(`corpus/SURVEY_sota_methods.md` (a), (e)).

`audits/NOVELTY_CRITIQUE.md` §d.4 states the boundary: *"if the program finds
itself fine-tuning large audio encoders, it has drifted off-thesis."*

---

## When to use

- First time audio is touched on a corpus.
- Adding a new encoder to axis A5.
- When an experiment is slow — the cause is almost always re-extraction inside a
  loop (§5).
- When a verdict must be checked for representation-specificity (the nuisance
  cube `A5 × A6 × A7 × A8 × seed`, `AXIS_TAXONOMY.md` §3).

---

## 0. The blocker to clear first — SVD ships `.nsp`, not WAV

SVD audio is **Kay Elemetrics NSP** (verified in this repo by the `FORMDS16`
magic + `HEDR` chunk on the 20-speaker pilot). **The `.nsp → WAV` conversion is
not implemented, and it is the next blocking step for the entire SVD audit**
(`ACQUISITION_STATUS.md` §5).

Requirements for whatever converter lands:

- Parse the `HEDR` chunk for sample rate and channel layout rather than assuming
  50 kHz; SVD sessions are not uniform, and a wrong assumed rate silently
  rescales every spectral feature.
- SVD ships a paired `.egg` (electroglottograph) per `.nsp`. **It is a second
  modality, not a second channel** — never mix it into the acoustic stream.
- Write a SHA-256 of each source `.nsp` into the conversion manifest so the
  cache key (§4) is anchored to the original bytes, not to the converted file.
- **Inner-join the manifest to the files on disk before splitting**:
  `overview_healthy.csv` lists 869 sessions but `healthy.zip` ships 687 folders —
  182 rows have no audio.

Until the converter exists, SVD work is metadata-only (which is exactly what
produced finding F1 — `FINDINGS.md`).

---

## 1. Which encoders, and why

| encoder | dim | why it is in the set |
|---|---|---|
| **Whisper-small/medium encoder** | 768 / 1024 | SpeechDx's overall winner across 27 speaker-disjoint tasks (MRR **0.44**), arXiv:2606.17339 |
| **WavLM-base+** | 768 | SpeechDx MRR 0.38; the pre-registered headline representation for V2 (`PREREGISTRATION.md` §A5) |
| **wav2vec2-base** | 768 | the field's default baseline; needed to make our numbers comparable to published ones |
| **HeAR** (`google/hear`) | **512** | health-acoustic prior, ViT-L masked autoencoder over 313 M 2-s clips; arXiv:2403.02522 |
| **OPERA-CT/CE/GT** | — | respiratory foundation models, arXiv:2406.16148 |
| **eGeMAPS / ComParE-2016** (openSMILE) | 88 / 6373 | CPU-only handcrafted baseline; the honest comparator that Gap 1 exists to test |

**Two calibrating facts, both measured by others, both worth stating in any
write-up that ranks encoders:**

- General-purpose encoders currently beat health-specific ones *on average*, and
  SpeechDx's own verdict is quotable: *"No current representation generalizes
  reliably across the clinical speech landscape."*
- Health pretraining appears to buy **sample-efficiency, not ceiling**: HeAR
  reaches near-full performance at ~**50** labelled samples where OPERA needs
  ~**400** (arXiv:2606.15436).

**HeAR imports an undisclosed prior.** Its training corpus is not released, so
using HeAR embeddings imports its (unknown) distribution into your audit. Say so
whenever a HeAR number is reported; it is a limitation, not a footnote.

---

## 2. Preprocessing — pinned, and part of the cache key

Every step below changes the embedding, so every step is part of the content
hash (§4). Changing one silently is how two "identical" experiments stop being
comparable.

1. **Decode → mono.** Average channels only when the channels are genuinely the
   same signal. On SVD, `.egg` is a *separate modality* — never averaged in.
2. **Resample to the encoder's native rate** (16 kHz for WavLM / wav2vec2 /
   Whisper / HeAR). Use one resampler for the whole program and record its name
   and version; different resamplers differ audibly in the top octave.
3. **Do NOT peak-normalise by default.** RMS intensity is a *confound-battery
   member* (`COMPOSITE.md` §3) and a documented recording-protocol shortcut
   (*PLOS Digital Health* `10.1371/journal.pdig.0000516`). If you normalise, the
   `intensity_rms_only` baseline is no longer measuring what the audio model
   sees. Pin the choice, run the battery under the same choice, and say which.
4. **Duration.** Record raw duration per file **before** any cropping — it is
   the `duration_only` baseline. Then either fixed-length windows or VAD (§3).
5. **Strip interviewer audio** on any interview-based corpus, without exception.
   The interviewer's side is consistently *more* discriminative than the
   participant's: I-Longformer 0.73 vs P-Longformer 0.71, I-GCN 0.88 vs P-GCN
   0.85 on DAIC-WOZ (Burdisso et al., ClinicalNLP @ NAACL 2024, arXiv:2404.14463).

---

## 3. VAD vs fixed windows

| | fixed windows | VAD-gated |
|---|---|---|
| what it is | contiguous N-second windows (HeAR's native unit is **2 s**) | keep only detected speech regions |
| pro | deterministic, trivially reproducible, no extra model in the pipeline | removes silence/room tone |
| con | includes silence, which is itself predictive | **the VAD is an unvalidated instrument** — it has its own error rate, and it can differ systematically between classes |

**Default: fixed windows, and keep the silence.** Reason: `silence_only` is a
required member of the confound battery — near-100 % Alzheimer's detection from
silent segments alone in the Pitt corpus (arXiv:2406.07410). You cannot run that
probe if the pipeline has already discarded silence, and you cannot interpret a
VAD-gated result without first showing what the silence alone achieves.

If VAD is used, it is an **instrument** under `CLAUDE.md` R3 and must be
characterised before its output is trusted: report its per-class speech-fraction
distribution, and check that a probe on *speech fraction alone* is near chance.
A VAD whose gating differs by class has manufactured a confound.

---

## 4. Caching — content-hash keyed, extracted once

```
cache/embeddings/
  <encoder_id>/
    <corpus_id>/
      <content_hash>.npz        # X (n, d) float32, ids, speaker_ids, meta
      manifest.json             # everything that went into content_hash
```

`content_hash` = SHA-256 over the canonical JSON of:

```json
{
  "encoder_id": "microsoft/wavlm-base-plus",
  "encoder_revision": "<hf commit sha>",
  "corpus_id": "svd",
  "source_file_hashes": "<sha256 of the sorted per-file sha256 list>",
  "sample_rate": 16000, "mono": true, "peak_normalise": false,
  "windowing": {"mode": "fixed", "seconds": 2.0, "hop": 2.0},
  "vad": null,
  "pooling": "mean",
  "layer": "last",
  "dtype": "float32",
  "lib_versions": {"torch": "...", "transformers": "...", "soundfile": "..."}
}
```

Stored in the `.npz` alongside `X`: `recording_id`, **`speaker_id`**, `sex`,
`age`, `duration_s`, `rms`, and the source file's SHA-256.

**`speaker_id` travels with the embeddings.** If it is not in the `.npz`, a
downstream fold loop will silently fall back to a recording-level split — which
is the failure mode
[voice-speaker-disjoint-splits](../voice-speaker-disjoint-splits/SKILL.md)
exists to prevent. Non-negotiable.

**Invalidation:** if the manifest's hash does not match the current config,
re-extract. Never silently use a stale cache; `CLAUDE.md` R15 invalidates results
by staleness when a dependency changes, and `lib_versions` is inside the hash
precisely so that happens loudly.

---

## 5. The hard rule

> **Extract once. Never re-extract inside a fold loop, a rank sweep, a seed
> sweep, or a hyperparameter search.**

Extraction is the only expensive step in this program; everything downstream is
linear algebra on cached matrices. The V2 pre-registration is explicit that its
whole cost is "one extraction pass" (`PREREGISTRATION.md` §Why V2 is first). A
sweep that re-extracts is not slow — it is *wrong*, because it makes the seed
sweep measure extraction nondeterminism instead of partition variance.

The corollary that matters for correctness: **caching embeddings is not
preprocessing leakage, but fitting anything on them is.** The scaler, PCA basis,
LDA/subspace, resampler and calibrator are all fitted **per fold** on cached
features (`A4 = fit_per_fold`). Scaling fitted before splitting moves SVD by
−0.14 to +0.14 pp but VOICED by **−8.3 to +7.8 pp** over 1,000 repetitions per
configuration (*Applied Soft Computing* `S1568494626007970`).

---

## 6. Pooling (axis A6) — conditional on A5

`mean` · `mean+std` · `max` · `attention` · `first/last frame` · per-layer
selection · clip-level mean over 2-s windows (HeAR's native unit).

- **A6 is undefined for HeAR** (one vector per 2-s clip; you aggregate clips, not
  frames) and for the handcrafted sets (functionals are already applied). A5×A6
  is a **ragged grid** — enumerate valid pairs, do not multiply cardinalities.
- `mean+std` and `max` expose more duration/intensity information than `mean`,
  and duration and intensity are exactly the documented recording-protocol
  shortcuts. Moving A6 can therefore *increase* the confound share; when it does,
  the confound battery must be re-read alongside, not just the AUC.
- Default: `mean` over frames (WavLM/wav2vec2/Whisper), clip-mean for HeAR — the
  values pinned in `PREREGISTRATION.md` §A6.

---

## 7. Laptop budget (16 GB VRAM, and RAM is the real ceiling)

- **Host RAM, not VRAM, is usually the binding constraint.** Check free RAM
  before a run; a browser holding tens of GB will page an extraction to disk and
  turn a 2-second forward pass into 30. Run model jobs in the **foreground** when
  RAM is tight — background jobs get reaped under memory pressure.
- Batch by **total audio seconds**, not by file count; clinical corpora have a
  long duration tail and a file-count batch will OOM on the tail.
- Cast embeddings to `float32` on write (`float16` in the cache costs precision
  in the subspace estimation for no meaningful disk saving at these sizes).
- Extract with `torch.inference_mode()`, encoder in eval mode, on GPU; move each
  batch's output to CPU immediately.
- Order of preference when time-boxed: **openSMILE (CPU, free) → WavLM-base+ →
  Whisper-small-enc → HeAR**. The CPU baseline is not a consolation prize; Gap 1
  asks whether "SSL beats handcrafted" survives an honest protocol at all.
- **Never print unicode to the console** in an extraction script on this host
  (`α`, `Δ`, `‖`, umlauts) — cp1252 raises `UnicodeEncodeError` and kills the
  run. Write the `.npz` and manifest **before** any summary print.

---

## 8. Anti-patterns

| anti-pattern | consequence | do instead |
|---|---|---|
| Re-extracting per fold / per k / per seed | 10–100× slowdown; the seed sweep measures extraction noise | extract once into `cache/embeddings/`, keyed by content hash |
| `speaker_id` not stored in the `.npz` | downstream silently splits on recordings | store it; assert its presence at load |
| Assuming a 50 kHz sample rate for `.nsp` | every spectral feature silently rescaled | parse the `HEDR` chunk |
| Averaging the `.egg` channel into the acoustic stream | a different modality contaminates the representation | keep EGG as a separate, explicitly-labelled stream |
| Peak-normalising by default | breaks the `intensity_rms_only` baseline's interpretation | pin the choice; run the battery under the same choice |
| VAD-gating before running `silence_only` | the Clever-Hans probe becomes impossible | keep silence; characterise the VAD as an instrument if used |
| Keeping interviewer audio | I-GCN 0.88 vs P-GCN 0.85 — you measure the interviewer (arXiv:2404.14463) | strip it, always |
| Fine-tuning the encoder to lift the number | off-thesis (`audits/NOVELTY_CRITIQUE.md` §d.4) | frozen encoders + small head; spend the budget on protocol |
| Reporting a HeAR result without noting the undisclosed training corpus | imports an unknown distribution into the audit | state it every time |
| Cache without `lib_versions` in the key | R15 staleness goes undetected | put versions inside the content hash |

---

## Definition of done

- [ ] Every embedding matrix has a `manifest.json` whose `content_hash` matches
      the config that produced it.
- [ ] `speaker_id`, `sex`, `age`, `duration_s`, `rms` and the source file SHA-256
      travel inside the `.npz`.
- [ ] Extraction ran **once**; the sweep loads, never extracts.
- [ ] Every fitted object downstream is `fit_per_fold`.
- [ ] Sample rate, mono policy, normalisation policy, windowing and pooling are
      pinned and recorded — not defaults inherited from a library.
- [ ] Interviewer audio stripped (interview corpora); EGG kept separate (SVD).
- [ ] If VAD was used, its per-class speech-fraction distribution is reported and
      a speech-fraction-only probe is near chance.
- [ ] The encoder's revision/commit is recorded, not just its name.

---

## Cross-references

- Split discipline that the cached `speaker_id` enables: [`../voice-speaker-disjoint-splits/SKILL.md`](../voice-speaker-disjoint-splits/SKILL.md)
- The baselines these features must beat: [`../voice-confound-baseline/SKILL.md`](../voice-confound-baseline/SKILL.md)
- Corpus onboarding, incl. the `.nsp` blocker's status: [`../voice-dataset-onboarding/SKILL.md`](../voice-dataset-onboarding/SKILL.md)
- A5 / A6 axis definitions and the ragged A5×A6 grid: `../../AXIS_TAXONOMY.md`
- Pinned representation for V2: `../../PREREGISTRATION.md` §4
- Encoder evidence: `corpus/SURVEY_sota_methods.md` (a) — SpeechDx arXiv:2606.17339,
  HeAR arXiv:2403.02522, OPERA arXiv:2406.16148, sample-efficiency arXiv:2606.15436
- Acquisition tooling and host constraints: `../../ACQUISITION_STATUS.md` §5–§6
