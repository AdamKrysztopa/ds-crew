# Changelog

All notable changes to ds-crew are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses semver.

## [1.3.1] — 2026-06-01 — Format token fix + benchmark study

### Fixed
- `ds-star/SKILL.md` + `ds-star-plus/SKILL.md`: Stage 5 format token checklist —
  explicit 3-rule checklist prevents model from copying placeholder names into
  `@key[value]` tokens or omitting tokens entirely (root cause of Q8/Q14 failures
  in DABench benchmark runs).
- `ds-star-plus/references/rubric.md` v2.1 → v2.2: added `format_token_missing`
  as 7th verifier rubric item.
- `ds-star-plus/scripts/verify_schema.py`: added `check_format_tokens()` programmatic
  pre-check; 18/18 tests pass.

### Added
- `benchmarks/experiments/` study framework: Exp A (no-tools baseline), Exp B
  (plugin vs raw prompt), with chart generator and doc generator.
- `benchmarks/experiments/exp_a_no_tools.py`: 33% accuracy / $0.20/task — confirms
  code execution adds +47pp accuracy while cutting cost.
- `benchmarks/experiments/exp_b_plugin_vs_prompt.py`: plugin (4.3 turns avg) vs
  raw prompt (3.8 turns) — both 73.3% on 15-question DABench subset.
- `benchmarks/solvers.py`: real `SpikeSolver` — N=3 parallel personas (cautious-
  statistician/Sonnet, sql-join-first/Sonnet, assumption-minimal/Opus) + majority vote.
- `benchmarks/smoke_run.py`: `--rerun-failures-of` for tiered cheap-first strategy;
  per-variant sanity check aborts on zero-token rows; `--diagnose` flag.

## [Unreleased] — Reviewer Credibility Pass

### Added
- `benchmarks/` harness: vendored DABench scorer, FakeSolver/ClaudeCliSolver runners,
  results.jsonl pipeline, report table + manifest, operator smoke-run docs (review #1).
- `config/models.json` — single source of truth for model IDs and prices (review #6).
- `skills/ds-spike/scripts/runlog.py` — run-log schema + after-the-fact validator (review #3).
- `.github/workflows/scripts/check_skill_paths.py` — SKILL.md path-resolution smoke test (review #8).
- `CHANGELOG.md` (review #11).
- `docs/quickstart.md` (review #12).

### Changed
- README, ARCHITECTURE.md, ROADMAP.md, docs/STATUS.md, skills/ds-star-plus/SKILL.md:
  removed implied measured v2 superiority; paper figures now explicitly attributed (review #2, #5).
- README skill surface split into Core 5 / Advanced 9 (review #7).
- `route_model.py` and `run_manifest.py` now source model IDs and rates from
  `config/models.json` (review #6).
- `skills/ds-star-plus/references/prompts.md` and `skills/ds-spike/references/personas.md`
  reference tier names + `config/models.json` instead of re-listing literal model IDs (review #6).
- `ds-search/SKILL.md` and `ds-spike/SKILL.md`: fixed broken `references/rubric.md` path
  references to correct cross-skill path `../ds-star-plus/references/rubric.md` (detected by #8 smoke test).

### Documented
- Verifier-as-reward circularity + distinct-aggregator-instance rule in
  `ds-spike/SKILL.md` and `ds-search/SKILL.md` (review #4).
- Honest limits of prose-driven loops ("What this cannot guarantee") in
  `ds-spike/SKILL.md` and `ds-conduct/SKILL.md` (review #3).

## [1.3.0] — 2026-05-31

Final Plan phases 0–4 (see ROADMAP.md for full track listing):
- Phase 0: credibility (LICENSE, citation audit, STATUS matrix, SKILL linter, CI badges, demo recipe)
- Phase 1: instrumentation (`run_manifest.py` with cost/token/latency fields)
- Phase 2: usability (config profiles, `ds-conduct` front door)
- Safety: heuristic PII detection in `data-profile`, cost guardrails in `ds-spike` + `ds-search`
- Datasets: stdlib fetcher, catalog of four starter datasets
- Phase 3: multimodal input, report export, visualization guidance (folded into existing skills)
- Phase 4: speculative backlog + permanent architectural boundaries documented
