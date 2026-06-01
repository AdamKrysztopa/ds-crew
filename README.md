# Data-science skill suite for Claude Code

[![CI](https://github.com/AdamKrysztopa/ds-crew/actions/workflows/ci.yml/badge.svg)](https://github.com/AdamKrysztopa/ds-crew/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)
![version](https://img.shields.io/badge/version-1.3.0-informational)

> **Demo:** ![demo recording](docs/demo.svg) *(record once with `docs/demo.md`; SVG not yet generated — see [`docs/STATUS.md`](docs/STATUS.md))*

> **Fourteen installable Claude Code skills** for end-to-end data science, built on the DS-STAR agent
> (Nam et al., 2025) and follow-on research — answering analytical questions over data files by
> writing and executing Python through an iterative loop that **never trusts code just because it
> ran**, plus clarification, ensembling, profiling, and exploration skills around it.

---

## Why DS-STAR?

Most AI data-science workflows stop when the code executes. DS-STAR doesn't.
It grows a plan one verified step at a time and uses an LLM-as-judge to confirm
that the **actual execution output** answers the actual question — catching silent failures
like wrong filters, missing joins, and format mismatches before they reach you.

---

## Installation

### 1. Add the marketplace (one-time per machine)

```bash
claude plugin marketplace add AdamKrysztopa/ds-crew
```

### 2. Install the plugin — choose your scope

```bash
# All your projects
claude plugin install ds-crew@ds-crew --scope user

# This project only (saved to .claude/settings.json)
claude plugin install ds-crew@ds-crew --scope project

# Local override, not committed
claude plugin install ds-crew@ds-crew --scope local
```

### 3. Use

Invoke explicitly in any Claude Code session:

```
/ds-star          # baseline iterative solver (paper-faithful)
/ds-star-plus     # reliability- & cost-hardened solver (rubric verifier, routing)
/ds-clarify       # human-in-the-loop: pin down intent → analysis-spec.md
/ds-spike         # ensemble: N data scientists in parallel → consensus + minority report
/data-profile     # standalone data-quality / profiling report
/eda-narrative    # exploration → stakeholder-ready narrative
/ds-conduct       # data-aware orchestrator: peeks at data, grills, assembles + executes crew workflow
/ds-model         # AutoML solution-tree: AIDE-style draft→train→eval→improve loop
/ds-verify        # standalone rubric verifier: grades any answer against the 6 DS failure modes
/ds-reconcile     # blackboard reconciliation: clusters answers into consensus + minority report
/ds-vote          # self-consistency N-vote: majority answer + stability score
/ds-search        # standalone MCTS search: tree-search a single hard task
/ds-memory        # persistent recipe store: remember and reuse what worked across sessions
/ds-env-setup     # set up / verify the Python env: detects uv/venv/conda/poetry/pipenv, installs core packages
```

Or just ask an analytical question over a data file — Claude will trigger the right skill
automatically.

> **First time?** Run `/ds-env-setup` to verify your project's Python environment has the packages the analysis skills need.

### Updating / uninstalling

```bash
claude plugin update ds-crew@ds-crew
claude plugin uninstall ds-crew@ds-crew
```

> **After installing or updating:** Start a new Claude Code session (or `/restart`) before using the skills — the plugin cache is loaded at session start, so new skills and skill updates are not available until the next session.

---

## The fourteen skills

**New here?** Start with a [config profile](docs/profiles.md) or run `/ds-conduct` — it inspects your data and routes automatically. See [docs/USAGE.md](docs/USAGE.md) for the full chooser.

| skill | what it does | reach for it when |
|-------|--------------|-------------------|
| **`ds-star`** | Baseline iterative solver — analyze files → grow a verified plan one step at a time | reproducing the paper; a simple, single-model baseline |
| **`ds-star-plus`** | Hardened solver: per-role Haiku/Sonnet/Opus routing, **rubric-graded verifier**, oscillation handling, digest caching, two-stage retrieval, optional MCTS search mode | production, multi-file, cost-sensitive, high-reliability work |
| **`ds-clarify`** | Human-in-the-loop pre-flight — interrogate intent, write `analysis-spec.md` | the question is fuzzy, high-stakes, or contested — run it **before** a solver |
| **`ds-spike`** | Ensemble — N diverse data scientists in parallel, reconciled into consensus + minority report | a number that must be right; two runs disagreed (costs N× — spend for confidence) |
| **`data-profile`** | Standalone data-quality / profiling report (per-column + cross-file join checks) | onboarding a dataset; "is this data clean / what's in it?" |
| **`eda-narrative`** | Exploration → a stakeholder-ready narrative, each finding backed by a number/chart | "what's interesting here?" with no single precise question |
| **`ds-conduct`** | Data-aware orchestrator — peeks at data, grills, assembles + executes a crew workflow | Starting fresh with data; fuzzy request; don't know which skills to use |
| **`ds-model`** | AutoML solution-tree — AIDE-style draft→train→eval→improve loop with leakage/CV discipline | Predict/forecast; Kaggle; improve model accuracy |
| **`ds-verify`** | Standalone rubric verifier — grades any answer against the 6 DS failure modes | Check/audit any result from any source |
| **`ds-reconcile`** | Blackboard reconciliation — clusters existing answers into consensus + minority report | Already have multiple answers; want them reconciled |
| **`ds-vote`** | Self-consistency N-vote — same solver N times, majority answer + stability | Quick stability check; moderate-stakes question |
| **`ds-search`** | Standalone MCTS search — tree-search a single hard task | One task keeps failing greedy; want alternative solution paths |
| **`ds-memory`** | Persistent recipe store — remember and reuse what worked across sessions | Inspect/prune past analyses; seed new runs from history |
| **`ds-env-setup`** | Set up / verify the Python env — detects uv/venv/conda/poetry/pipenv, installs core packages, offers a SessionStart hook | Before first analysis; after changing env; `ImportError` during a run |

> **Advanced primitives** (`ds-verify`, `ds-reconcile`, `ds-vote`, `ds-search`, `ds-memory`): invoke directly only when you have a specific need — checking an answer, reconciling existing results, or inspecting the memory store. Most users start at `/ds-conduct`.

> **→ [Which skill should I use? See docs/USAGE.md](docs/USAGE.md)** · [Config profiles](docs/profiles.md) · [Demo datasets](docs/datasets.md)

**Typical flow for something important:** `ds-conduct` (orchestrates the whole crew) → `data-profile` → `ds-clarify` → `ds-spike` (ensemble) → reconciled answer. See [docs/USAGE.md](docs/USAGE.md) for all routing options.

### `ds-star` vs `ds-star-plus` at a glance

| | `ds-star` | `ds-star-plus` |
|---|---|---|
| **Model** | Single model throughout | Haiku / Sonnet / Opus per role |
| **Verifier output** | Yes / No | graded `{score 1–4, rubric, checks, reason, missing}` |
| **Backtracking** | Truncate + regenerate | + anti-repeat list, oscillation handling |
| **Token cost** | Full descriptions every round | Schema digests by default |
| **Best for** | Baseline / reproducing the paper | Production, multi-file, cost-sensitive work |

---

## How the loop works

```
ANALYZE every file (real schema, not guesses)
        │
INITIAL simple step (load + peek)
        │
        ▼
   ┌─── IMPLEMENT (Python script)
   │         │
   │      EXECUTE
   │         │
   │      VERIFY ──── sufficient? ──► FINALIZE ──► answer
   │         │ no
   │      ROUTE: add next step  OR  backtrack to wrong step
   └─────────┘
   (max 20 rounds)
```

The verifier is the load-bearing piece: a false "sufficient" ends the run with a wrong
answer that nothing downstream catches, so `ds-star-plus` pins it to Opus and optionally
runs it 3× with majority vote on borderline calls.

---

## Repository layout

```
ds-crew/
├── skills/
│   ├── ds-star/                    baseline — faithful paper implementation
│   │   ├── SKILL.md · references/{prompts,worked_example}.md · scripts/analyze_file.py
│   ├── ds-star-plus/               hardened solver (routing, rubric verifier, retrieval)
│   │   ├── SKILL.md
│   │   ├── evals/evals.json        checkable test cases
│   │   ├── references/
│   │   │   ├── model_routing.md    Opus/Sonnet/Haiku routing policy
│   │   │   ├── evidence.md         paper-grounded "why" for every change
│   │   │   ├── rubric.md           the six DS failure modes (v2.1 verifier)
│   │   │   ├── search_mode.md      optional MCTS search mode (A2)
│   │   │   ├── retrieval.md        two-stage + column-match retrieval (A3)
│   │   │   ├── prompts.md          upgraded prompts (rubric-graded verifier)
│   │   │   ├── worked_example.md   annotated trace with backtracking
│   │   │   ├── execution.md        persistent IPython kernel (opt-in, Track F)
│   │   │   ├── planning_graph.md   DAG planning + dynamic replan (Track G)
│   │   │   └── sandbox.md          working-dir discipline + no-network default (Track J)
│   │   └── scripts/
│   │       ├── analyze_file.py     describer + schema digest emitter
│   │       ├── route_model.py      pick_model() routing helper
│   │       ├── verify_schema.py    verdict validator (+ test_verify_schema.py)
│   │       ├── run_manifest.py     reproducibility manifest emitter (Track J)
│   │       └── kernel_runner.py    persistent kernel driver (Track F)
│   ├── ds-clarify/                 human-in-the-loop spec (SKILL + checklist + template)
│   ├── ds-spike/                   ensemble: SKILL + personas + aggregation
│   │   ├── references/debate.md    optional cross-critique mode (Track I)
│   │   └── scripts/aggregate.py    consensus + minority report (+ test_aggregate.py)
│   ├── data-profile/               standalone data-quality report
│   ├── eda-narrative/              exploration → narrative
│   ├── ds-conduct/                 data-aware orchestrator (Track K)
│   │   └── SKILL.md · references/{trigger_catalog,workflow_plan_template,evidence}.md
│   ├── ds-model/                   AutoML solution-tree (Track H)
│   │   ├── SKILL.md · evals/evals.json
│   │   ├── references/{solution_tree,leakage_cv,evidence}.md
│   │   └── scripts/leaderboard.py
│   ├── ds-memory/                  persistent recipe store (Track E)
│   │   ├── SKILL.md · references/store_format.md
│   │   └── scripts/memory_store.py
│   ├── ds-verify/                  standalone rubric verifier (Track L)
│   │   └── SKILL.md
│   ├── ds-reconcile/               blackboard reconciliation (Track L)
│   │   └── SKILL.md
│   ├── ds-vote/                    self-consistency N-vote (Track L)
│   │   └── SKILL.md
│   └── ds-search/                  standalone MCTS search (Track L)
│       └── SKILL.md
├── .claude-plugin/                 plugin.json + marketplace.json
├── docs/
│   ├── USAGE.md                    decision table, flowchart, canonical pipelines
│   └── superpowers/plans/          implementation plans (e.g. rubric-verifier)
├── ARCHITECTURE.md                 v1 vs v2 side-by-side
├── ROADMAP.md                      tracks, statuses, dependency order
├── papers/README.md               bibliography (PDFs gitignored, re-fetchable)
├── architecture-comparison.svg · make_diagram.py
```

---

## Reference

Nam, Yoon, Chen & Pfister (2025). *DS-STAR: Data Science Agent via Iterative Planning and
Verification.* arXiv:2509.21825. Google Cloud / KAIST.

The v2 additions (model routing, structured verifier, oscillation handling, digest caching,
two-stage retrieval) are design extensions grounded in the DS-STAR paper, not yet independently
benchmarked. Each change is justified against a specific finding in the paper — the 3.5×
input-token cost (Table 6: 154,669 vs 44,691 tokens vs ReAct), the analyzer/router ablations
(Table 4, e.g. hard accuracy 45.24 → 26.98 without descriptions), the ~8-point
retrieval-vs-oracle gap (Table 2), and the round distribution (§4.3). The full evidence chain is
in `skills/ds-star-plus/references/evidence.md`; `skills/ds-star-plus/evals/evals.json` provides
checkable test cases.

## Status

All tracks A–M are **implemented**; **validation against external benchmarks is pending** (see [`docs/STATUS.md`](docs/STATUS.md)). Skills with passing unit/eval test suites are marked 🟡; the rest await the Phase 1 external benchmark. Benchmark plan and the open ds-spike-vs-verifier question: [`skills/ds-star-plus/references/benchmark.md`](skills/ds-star-plus/references/benchmark.md).

Tracks A–D delivered the rubric-graded verifier (DeepVerifier-style),
the human-in-the-loop `ds-clarify`, the capstone `ds-spike` ensemble (blackboard reconciliation),
`data-profile`, `eda-narrative`, and `ds-star-plus`'s optional MCTS search mode + upgraded retrieval.
Tracks E–M (v1.2) add persistent memory (`ds-memory`), stateful kernel execution, DAG planning,
AutoML solution-tree (`ds-model`), debate mode in `ds-spike`, sandbox + provenance, the data-aware
orchestrator (`ds-conduct`), five standalone primitive skills, and the `docs/USAGE.md` routing guide.
Each change is tied to a paper in the bibliography at [`papers/README.md`](papers/README.md); the
tracks, statuses, and dependency order live in [`ROADMAP.md`](ROADMAP.md). The Python helpers ship
with unit tests (`python3 -m unittest` in each `scripts/` dir).
