# docs/ — the generated dashboard

Everything under `docs/` except this file and `_config.yml` is **generated, never
hand-written**. Four generators produce it, and each fails loudly rather than
emitting a blank or invented cell.

| generator | writes |
|---|---|
| `python scripts/build_dashboard.py` | `docs/index.html` + `docs/assets/*.png` |
| `python scripts/build_datasets_page.py` | `docs/datasets.html` |
| `python scripts/build_hypothesis_pages.py` | `docs/hypotheses/index.html` + `V1..V7.html` |
| `python scripts/build_experiment_pages.py` | `docs/dashboard/experiments/index.html` + one page per run |

`scripts/build_common.py` is the shared spine: the run registry, the tier rule, the
composite fingerprint, the markdown-leak gate and the anchor assertions all live there
exactly once, so the three page tiers cannot disagree about the same artifact.

**Build order** (the hypothesis tier links into the run tier, so build runs first):

```
python scripts/build_experiment_pages.py
python scripts/build_hypothesis_pages.py
python scripts/build_dashboard.py
python scripts/build_datasets_page.py
```

All four are CPU-only, need no network and no model, and take a couple of seconds.
Re-run them after every completed run; do not edit any `.html` by hand, because the
next build overwrites it.

## The guarantees these generators make

1. **Every number is read from an artifact.** Sources include
   `autoresearch_results/F1_demographic_baseline.json`, `bench_svd_egemaps.json`,
   `bench_svd_wavlm_mean_std.json`, `V1_ssl_vs_handcrafted.json`,
   `V2_speaker_subspace.json` (+ its shuffle control), `V6_preprocessing_leakage.json`,
   `V7_silence_shortcut.json`, `data/interim/<corpus>/summary.json` and `manifest.csv`,
   `data/ACQUISITION_STATUS.md`, `data/PREPROCESSING_STATUS.md`,
   `corpus/SURVEY_datasets.md`, `corpus/datasets.json`, `COMPOSITE.md`, `IDEA_TABLE.md`
   and `FINDINGS.md` (CLAUDE.md R1: no orphan numbers; R2: the agent never states a
   metric it did not read from an artifact).
2. **A missing source is fatal.** `FATAL:` and a non-zero exit, never a blank cell.
3. **An undeclared run is fatal.** `build_common.RUN_REGISTRY` names every artifact that
   is a run. An artifact that is renamed or deleted fails the build; so does a *new*
   `*.json` in `autoresearch_results/` that no generator knows about. That second gate is
   the important one — three executed hypotheses once sat on disk for days while every
   published page reported them UNTESTED, because artifact discovery was a hardcoded
   one-entry lookup.
4. **A lookup that matches nothing raises.** `anchor_find` / `anchor_replace` refuse to
   return quietly when the pattern is absent, so a source whose format changed fails the
   build instead of producing a well-formed page with the wrong content.
5. **Plots cannot disagree with their finding.** The age-distribution figure is
   recomputed from the raw metadata and cross-checked against
   `F1_demographic_baseline.json`; a mismatch aborts the build.
6. **Inputs that disagree with each other are rendered, not narrated.** The SVD row of
   `data/PREPROCESSING_STATUS.md` is compared against `data/interim/svd/summary.json` on
   every build; a disagreement produces a visible panel naming both files and both write
   times, and the panel disappears by itself once the markdown is refreshed.
7. **No literal markdown reaches a page.** `leak_gate` scans the emitted HTML for `**`,
   `|---` and line-initial `##` and fails the build on a hit. A check that must be
   remembered will eventually be skipped, so it runs unconditionally in all four
   generators.
8. **Anything unmeasured renders as the literal words _not yet measured_.** The master
   build additionally aborts if that string is absent from the page, which would mean a
   placeholder had been filled with a number.
9. **Statistical tier and scope are separate.** Tier comes from the run's own repeat
   count (n ≥ 8 EVALUATION, otherwise SCREENING); scope is derived by comparing a run's
   speaker count against the widest slice measured on the same corpus. A run can satisfy
   the repeat contract and still be a pilot, and both facts are shown.
10. **No champion row.** `COMPOSITE.md` pins a composite specification and its SHA-256
    fingerprint, which the build recomputes and checks against the pinned value — but
    `src/voiceaudit/composite.py` does not exist, so no composite is computed for any run.
    Nothing is ranked by it and the footer says so.

## Self-containment

Inline CSS, one inline `<script>` per page for sort/filter, PNG plots (no SVG), no CDN,
no JS framework, no webfont, no network request at view time. Opening any page from the
filesystem renders it completely.

## Publishing

Served from the `/docs` folder of `master` at
<https://dlmastery.github.io/auto-research-voice-based-disease-detection/>.
`docs/.nojekyll` disables the Jekyll build; `docs/_config.yml` is the version-controlled
record of the Pages settings rather than an active configuration — see the comment at the
top of that file.
