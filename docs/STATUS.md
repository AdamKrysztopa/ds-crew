# ds-crew — Implementation & Validation Status

Legend: ✅ done · 🟡 partial (unit/eval tests only, no external benchmark) · ⬜ not yet

## Skill status matrix

| skill / track | implemented | validated (ran vs ground truth) | evidence |
|---|---|---|---|
| ds-star (Track A–C) | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-star-plus (Tracks A–D) | ✅ | 🟡 unit tests + evals/ | `skills/ds-star-plus/scripts/test_*.py`, `evals/evals.json` |
| ds-clarify | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-spike (Track I) | ✅ | 🟡 unit tests | `skills/ds-spike/scripts/test_aggregate.py` |
| ds-model (Track H) | ✅ | 🟡 unit tests + evals/ | `skills/ds-model/scripts/test_leaderboard.py`, `evals/evals.json` |
| ds-conduct (Track K) | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-memory (Track E) | ✅ | 🟡 unit tests | `skills/ds-memory/scripts/test_memory_store.py` |
| ds-verify (Track L) | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-reconcile (Track L) | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-vote (Track L) | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-search (Track L) | ✅ | ⬜ pending Phase 1 benchmark | — |
| data-profile | ✅ | 🟡 PII heuristic unit tests | `skills/data-profile/scripts/test_detect_pii.py` |
| eda-narrative | ✅ | ⬜ pending Phase 1 benchmark | — |
| ds-env-setup | ✅ | 🟡 unit tests | `skills/ds-env-setup/scripts/test_check_env.py` |

## Benchmark plan
An external benchmark (DABStep) is planned for Phase 1. See `skills/ds-star-plus/references/benchmark.md` for the follow-up specification.

## Repo metadata (set on GitHub)
These metadata items require manual action on GitHub:

- **Repository description:** "Fourteen data-science skills for Claude Code — iterative, rubric-verified solving, ensembling, orchestration, and more. Grounded in DS-STAR and follow-on research."
- **Topics:** `claude-code`, `data-science`, `agent`, `ds-star`, `llm-agent`, `automl`

## Final Plan execution summary (2026-05-31)

- Phase 0 ✅ — credibility foundations complete
- Phase 1 🟡 — instrumentation complete; external benchmark deferred
- Phase 2 ✅ — front door + profiles + USAGE.md streamlined
- Phase 3 ✅ — multimodal, export, viz, big-data guidance added
- Phase 4 ⬜ — speculative backlog recorded in ROADMAP.md
- Safety ✅ — PII detection, cost guardrails added
