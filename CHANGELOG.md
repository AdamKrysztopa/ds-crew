# Changelog

All notable changes to ds-crew are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses semver.

## [1.5.1] — 2026-06-05 — Make the forecastability tool actually usable

### Fixed
- `ds-model/references/feasibility_gate.md`: the time-series gate now gives a **concrete, usable
  recipe** for `dependence-forecastability` instead of just naming it — `pip install
  dependence-forecastability`, the **distribution-name ≠ import-name** gotcha (`import forecastability`),
  the **Python 3.11–3.12** constraint (with venv/fallback guidance for 3.13+ envs), the
  `run_triage(TriageRequest(...))` entry point and the `forecastability` CLI, and the repo link.
  Without this, an agent would recognize the tool but fumble the install/import.

## [1.5.0] — 2026-06-05 — Feasibility & leakage gate (pre-modeling)

### Added
- **Feasibility & leakage gate** — a pre-modeling protocol that runs *before* any model:
  estimate the achievable performance **ceiling** and **scan for leakage**, then treat the ceiling
  as the acceptance bar (a model that beats it is a leakage alarm, not a win). New shared reference
  `ds-model/references/feasibility_gate.md`, with two faces:
  - **Tabular (i.i.d.):** probe-model ceiling · single-feature leakage scan · adversarial validation
    (train/test drift) · duplication / ID check.
  - **Time-series / ordered:** **forecastability ceiling** (recommended tool: `dependence-forecastability`;
    fallback ACF/PACF + entropy) · temporal split, never shuffle · target-leakage check.
  Tool-agnostic (prose protocol, runs in the user's own language) — fills the suite's previously
  implicit time-series path.
- Wired into the affected skills: `ds-model` (new **Stage 0**, cardinal rule, quick reference),
  `ds-conduct` (trigger catalog routes predictive/time-series patterns through the gate; plan
  assembly notes it), `ds-clarify` (the spec's **Acceptance** now records the feasibility ceiling).

## [1.4.0] — 2026-06-05 — Three literature patterns (prose protocols)

### Added
- **Column-level retrieval (Phase 1)** — `ds-star-plus/references/retrieval.md` Stage 3 is now an
  operational protocol with an explicit recall-biased keep rule (keep a file strong on *either*
  embedding *or* structure: column-name overlap, value containment, join-key reachability). Folds
  into the existing Haiku relevance pass — no new call. Wired into `ds-conduct`, `ds-clarify`,
  `ds-spike`, `data-profile`; worked recovery example added.
- **ExpeL rule distillation (Phase 2a)** — `ds-memory` **Mode 4 (Distill)**: concrete recipes →
  abstract `rules.jsonl` (our label for ExpeL's "natural-language insights"), retrieved as advisory
  guidance. Wired into `ds-star-plus` planner, `ds-conduct` plan-assembly, `ds-spike` personas,
  `ds-clarify` checklist.
- **Search-experience store (Phase 2b)** — `search_experience.jsonl` (Empirical-MCTS long-term, dual
  experience) with prose record/seed hooks in `ds-search`. Wired into `ds-star-plus` `search_mode`,
  `ds-spike` `aggregation`, `ds-conduct` escalation.

All three ship as **language-agnostic prose + JSONL schemas — zero new code** (judgment is prose;
internal state is a neutral format that imposes no language on the user's analysis).

### Fixed
- Citation corrections (verified against `papers/`): the 44.69/52.55/8-pt oracle gap is **DS-STAR
  Table 2**, not "KramaBench Table 2"; Empirical-MCTS dual experience is **short/long-term**, not
  "success/failure"; ExpeL's term is "insights". Completed the papers corpus (ExpeL, Voyager, AWM)
  and flipped the corresponding `evidence.md` notes to implemented.

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
