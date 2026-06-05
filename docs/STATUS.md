# ds-crew — Implementation & Validation Status

Legend: ✅ done / validated · 🟡 partial (unit/eval tests only) · ⬜ not yet

## Skill status matrix

| skill / track | implemented | validated (ran vs ground truth) | evidence |
|---|---|---|---|
| ds-star (Track A–C) | ✅ | ✅ **94.4% (17/18) DABench**, effectively 18/18 | [`docs/experiments/`](experiments/README.md) |
| ds-star-plus (Tracks A–D) | ✅ | ✅ DABench (same answers as ds-star) + unit tests + evals/ | [`docs/experiments/C-spike-hard-questions.md`](experiments/C-spike-hard-questions.md), `skills/ds-star-plus/scripts/test_*.py` |
| ds-spike (Track I) | ✅ | ✅ DABench contested Qs + unit tests | [`docs/experiments/C-spike-hard-questions.md`](experiments/C-spike-hard-questions.md), `skills/ds-spike/scripts/test_aggregate.py` |
| ds-clarify | ✅ | 🟡 design-validated; not in closed-form benchmark | — |
| ds-model (Track H) | ✅ | 🟡 unit tests + evals/ | `skills/ds-model/scripts/test_leaderboard.py`, `evals/evals.json` |
| ds-conduct (Track K) | ✅ | 🟡 design-validated; orchestration over benchmarked solvers | — |
| ds-memory (Track E) | ✅ | 🟡 unit tests | `skills/ds-memory/scripts/test_memory_store.py` |
| ds-verify (Track L) | ✅ | 🟡 internal of the benchmarked ds-star-plus verifier | [`docs/experiments/`](experiments/README.md) |
| ds-reconcile (Track L) | ✅ | 🟡 internal of the benchmarked ds-spike aggregator | `skills/ds-spike/scripts/test_aggregate.py` |
| ds-vote (Track L) | ✅ | 🟡 unit tests | — |
| ds-search (Track L) | ✅ | 🟡 design-validated; opt-in escalation mode | — |
| data-profile | ✅ | 🟡 PII heuristic unit tests | `skills/data-profile/scripts/test_detect_pii.py` |
| eda-narrative | ✅ | 🟡 design-validated; open-ended (no closed-form ground truth) | — |
| ds-env-setup | ✅ | 🟡 unit tests | `skills/ds-env-setup/scripts/test_check_env.py` |

> The closed-form benchmark validates the **solver core** (ds-star / ds-star-plus and the
> verifier + aggregator they expose as ds-verify / ds-reconcile / ds-spike). The
> human-in-the-loop and exploratory skills (ds-clarify, ds-conduct, eda-narrative) are
> validated by design against the DS-STAR paper rather than by a closed-form score, because
> their value is intent capture and structure, which a single-number benchmark cannot measure.

## Benchmark results (validated)

**DABench dev subset of [InfiAgent-DAEval](https://github.com/InfiAgent/InfiAgent),
`claude-sonnet-4-6`, plugin v1.3.1.** Full study with charts, per-question analysis, and the
three harness fixes: [`docs/experiments/`](experiments/README.md).

| variant | strict accuracy | field-score | $/task |
|---|---|---|---|
| no-tools (text only) | 33% | — | $0.20 |
| **ds-star** (plugin) | **94.4% (17/18)** | 97.9% | $0.34 |
| **ds-star** (prompt) | **94.4% (17/18)** | 97.9% | $0.31 |

Headline: **code execution is the dominant lever (+61pp over text-only).** The single
remaining miss is Q8, a benchmark-label bug (its constraint asks for *population* std; its
label uses *sample* std) — every method computes population std correctly and is marked
wrong. Effectively the skills answer all 18 correctly. The raw pre-fix smoke run
(`benchmarks/runs/smoke/summary.md`, 86.7%/15-q) is retained for provenance but superseded.

## Repo metadata (set on GitHub)
These metadata items require manual action on GitHub:

- **Repository description:** "Fourteen data-science skills for Claude Code — iterative, rubric-verified solving, ensembling, orchestration, and more. Grounded in DS-STAR and follow-on research."
- **Topics:** `claude-code`, `data-science`, `agent`, `ds-star`, `llm-agent`, `automl`

## Final Plan execution summary

- Phase 0 ✅ — credibility foundations complete
- Phase 1 ✅ — instrumentation complete **and** external DABench validation done (94.4%); see `docs/experiments/`
- Phase 2 ✅ — front door + profiles + USAGE.md streamlined
- Phase 3 ✅ — multimodal, export, viz, big-data guidance added
- Phase 4 ⬜ — speculative backlog recorded in ROADMAP.md
- Safety ✅ — PII detection, cost guardrails added

## Missing-literature-patterns initiative (branch `plan/missing-patterns`)

Plan: `docs/plan/missing-patterns.md`. Six literature patterns triaged → 3 BUILD, 1 DEFER, 2 SKIP.
Design principle (P0): Claude skills are **prose protocols**; judgment is prose, internal state is a
language-neutral JSONL format (Philosophy B — never put our language on the *user's* analysis path).

- **Papers corpus completed** — fetched + content-verified ExpeL (2308.10144), Voyager
  (2305.16291), AWM (2409.07429); all 13 cited PDFs now in `papers/`.
- **Citation correction** — the 44.69/52.55/8-pt oracle gap is **DS-STAR Table 2**, not
  "KramaBench Table 2" (fixed in `ds-star-plus/references/retrieval.md` + `evidence.md §5`).
- **Phase 1 (column-level retrieval) ✅** — `retrieval.md` Stage 3 is now an operational protocol
  with the recall-biased keep rule; wired into ds-conduct, ds-clarify, ds-spike, data-profile;
  worked recovery example added. No new code (prose only).
- **Phase 2a (ExpeL rule distillation) ✅** — `ds-memory` Mode 4 (Distill) as a prose protocol;
  `rules.jsonl` schema (language-neutral); ExpeL evidence flipped to implemented; wired into
  ds-star-plus planner, ds-conduct plan-assembly, ds-spike personas, ds-clarify checklist. No new code.
- **Phase 2b (search-experience store) ✅** — `search_experience.jsonl` schema + prose record/seed
  hooks in ds-search; dual-experience evidence flipped (short/long-term framing); wired into
  ds-star-plus search_mode, ds-spike aggregation, ds-conduct escalation. No new code.
- **All green:** CI path-checks, frontmatter, registry, manifests, and all unittest suites pass.
  Three patterns shipped as **prose + JSONL only** (Philosophy B — no language imposed on the user).
