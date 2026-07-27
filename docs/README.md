# docs/ — the generated dashboard

`docs/index.html` and everything in `docs/assets/` are **generated, not hand-written**. They are
produced by `python scripts/build_dashboard.py`, which reads every number it renders out of a
source artifact in this repository — `autoresearch_results/F1_demographic_baseline.json`,
`autoresearch_results/bench_svd_egemaps.json`, `data/interim/<corpus>/summary.json` and
`manifest.csv`, `data/ACQUISITION_STATUS.md`, `data/PREPROCESSING_STATUS.md`,
`corpus/SURVEY_datasets.md`, `IDEA_TABLE.md` and `FINDINGS.md` — and writes a single
self-contained page with inline CSS, one inline `<script>` for table sort/filter, and PNG plots.
There is no CDN, no JS framework and no network request: opening the file offline renders the
complete dashboard. Do not edit `index.html` by hand — the next build overwrites it. If a source
file is missing the generator exits with a `FATAL:` message rather than emitting a blank or
invented cell (CLAUDE.md R1: no orphan numbers; R2: the agent never states a metric it did not
read from an artifact), and the age-distribution figure is additionally cross-checked against the
F1 JSON so a plot can never disagree with the finding it illustrates. Anything not yet measured
renders as the literal words *not yet measured*. To refresh the dashboard after a new run
completes, re-run the generator; it is CPU-only and takes a couple of seconds.
