# ds-crew — data science skills for Claude Code

[![CI](https://github.com/AdamKrysztopa/ds-crew/actions/workflows/ci.yml/badge.svg)](https://github.com/AdamKrysztopa/ds-crew/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2)
![version](https://img.shields.io/badge/version-1.3.1-informational)

> **See the whole arc:** [**Walkthrough — from a raw file to a reviewed answer**](docs/walkthrough.md) — a messy real dataset, a vague goal, and the plugin catching a silent revenue error on the way to a defensible number. *(To record your own terminal cast, see [`docs/demo.md`](docs/demo.md).)*

14 slash commands that give Claude Code structured workflows for data science work — profiling, exploration, analysis, and model-building. The goal is a good kickoff: get from zero to a structured, executable, reviewed starting point in minutes rather than hours.

> **The contract.** This is a *kickoff* tool, not an oracle.
> - **What it does:** the mechanical work — profile the data, pin down the question, write and run the code, and check the result against common silent-failure modes.
> - **What it hands back to you:** the judgment — the right question, the right data, the right interpretation — with the consequential scope decisions surfaced, not buried.
> - **When it stops and asks:** ambiguous scope, contradictory requirements, or a domain judgment call. The cases it gets wrong are exactly the ones that warrant human or multi-agent review anyway — so it routes them to you instead of guessing.

**→ [Quickstart — one dataset, one command, expected output](docs/quickstart.md)**

---

## What it does

Drop a data file in your project and use a slash command to kick off whatever you need:

- **Start an analysis** — `/ds-conduct` peeks at your data, asks a few questions, and assembles the right workflow automatically
- **Profile a new dataset** — `/data-profile` gives you column stats, null rates, and join diagnostics before you write a single line
- **Explore without a question** — `/eda-narrative` surfaces what's interesting and writes it up
- **Get a verified answer** — `/ds-star-plus` writes and runs Python iteratively, checks the result against 7 common failure modes (wrong column, dropped rows, unit mismatch, scope error, format mismatch, question substitution, missing output token), and backtracks if something's off
- **Run multiple approaches** — `/ds-spike` runs 3 diverse solvers in parallel and reconciles them; useful when you need confidence or when two single runs disagreed
- **Build a model** — `/ds-model` runs an AIDE-style solution tree with leakage and CV discipline

The skills are prompts — structured workflows that guide Claude through a task. They don't replace your judgment; they give you a faster, more consistent starting point than writing the prompt from scratch each time.

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

```
/ds-conduct       # start here if you're not sure — inspects data, asks, routes
/ds-star-plus     # iterative solver with rubric-graded verification
/ds-spike         # 3 parallel solvers → consensus + minority report
/data-profile     # data quality / profiling report
/eda-narrative    # exploration → stakeholder narrative
/ds-star          # baseline solver (paper-faithful, single model)
/ds-clarify       # pin down intent before solving — writes analysis-spec.md
/ds-model         # AutoML solution-tree with leakage/CV discipline
/ds-verify        # grade any answer against the 7 DS failure modes
/ds-reconcile     # reconcile multiple existing answers into consensus
/ds-vote          # run same solver N times, take majority
/ds-search        # MCTS tree-search for a task that keeps failing greedy
/ds-memory        # remember and reuse recipes across sessions
/ds-env-setup     # verify Python env, install packages, offer SessionStart hook
```

> **First time?** Run `/ds-env-setup` to verify your Python environment has the packages these skills need.

### Updating / uninstalling

```bash
claude plugin update ds-crew@ds-crew
claude plugin uninstall ds-crew@ds-crew
```

> **After installing or updating:** start a new Claude Code session (or `/restart`) — the plugin cache loads at session start.

---

## The fourteen skills

**Not sure where to start?** Run `/ds-conduct` or see [docs/USAGE.md](docs/USAGE.md) for a decision table.

### Core 5 — reach for these first

| skill | what it does | reach for it when |
|-------|--------------|-------------------|
| **`ds-conduct`** | Peeks at your data, asks clarifying questions, assembles and runs the right workflow | Starting fresh; fuzzy request; don't know which skill fits |
| **`ds-star-plus`** | Iterative solver: write code → execute → verify against 7 failure modes → backtrack if wrong; Haiku/Sonnet/Opus routing | You need an answer and want it checked, not just executed |
| **`ds-spike`** | 3 diverse solvers in parallel, reconciled into consensus + minority report | A number that must be right; two runs disagreed; high-stakes |
| **`data-profile`** | Per-column stats, null rates, cross-file join checks | Onboarding a new dataset; "is this data clean?" |
| **`eda-narrative`** | Open-ended exploration → written narrative with numbers | No specific question yet; "what's interesting here?" |

### Advanced 9 — specific needs

> The four Track-L primitives (`ds-verify`, `ds-reconcile`, `ds-vote`, `ds-search`) are internals of `ds-star-plus`/`ds-spike` exposed standalone for when you need fine-grained control.

| skill | what it does | reach for it when |
|-------|--------------|-------------------|
| **`ds-star`** | Baseline iterative solver, single model, paper-faithful | Reproducing the paper; simple single-model baseline |
| **`ds-clarify`** | Interrogates intent, writes `analysis-spec.md` | Question is fuzzy, high-stakes, or contested — run before a solver |
| **`ds-model`** | AutoML: draft → train → eval → improve loop with leakage/CV discipline | Predict/forecast; Kaggle; improve model accuracy |
| **`ds-memory`** | Stores and retrieves what worked across sessions | Reuse past analyses; seed new runs from history |
| **`ds-env-setup`** | Detects uv/venv/conda/poetry/pipenv, installs core packages | Before first analysis; after env change; `ImportError` |
| **`ds-verify`** | Grades any answer against 7 DS failure modes | Audit a result from any source |
| **`ds-reconcile`** | Clusters multiple answers into consensus + minority report | Already have N answers and want them reconciled |
| **`ds-vote`** | Same solver N times, majority answer + stability score | Quick stability check on a moderate-stakes question |
| **`ds-search`** | MCTS tree-search over solution space | One task keeps failing greedy; want alternative solution paths |

> **→ [Which skill? See docs/USAGE.md](docs/USAGE.md)** · [Config profiles](docs/profiles.md) · [Demo datasets](docs/datasets.md)

### `ds-star` vs `ds-star-plus` at a glance

| | `ds-star` | `ds-star-plus` |
|---|---|---|
| **Model** | Single model throughout | Haiku / Sonnet / Opus per role |
| **Verifier** | Yes / No | Score 1–4 with rubric, checks, reason |
| **Backtracking** | Truncate + regenerate | + anti-repeat list, oscillation handling |
| **Context** | Full descriptions every round | Schema digests by default |
| **Use when** | Simple baseline; reproducing the paper | Production, multi-file, cost-sensitive |

---

## How the verification loop works

The solver skills (ds-star, ds-star-plus) run this loop rather than executing one big script:

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

The verifier checks 7 failure modes before accepting an answer: wrong column or value,
dropped rows, units mismatch, scope error, format mismatch, question substitution, and
missing output token. It's useful for catching the kind of error that looks fine until
you check it — a filter that silently drops half the rows, a units conversion that was
skipped, a summary over the wrong time window.

It doesn't catch everything, and it's not a replacement for reviewing the code yourself
on anything important.

---

## Repository layout

```
ds-crew/
├── skills/
│   ├── ds-star/                    baseline — faithful paper implementation
│   ├── ds-star-plus/               hardened solver (routing, rubric verifier, retrieval)
│   │   ├── references/             routing policy, evidence, rubric, search, retrieval
│   │   └── scripts/                analyze_file, route_model, verify_schema, run_manifest
│   ├── ds-clarify/                 pre-flight spec (SKILL + checklist + template)
│   ├── ds-spike/                   ensemble (SKILL + personas + aggregation)
│   ├── data-profile/               standalone data-quality report
│   ├── eda-narrative/              exploration → narrative
│   ├── ds-conduct/                 data-aware orchestrator
│   ├── ds-model/                   AutoML solution-tree
│   ├── ds-memory/                  persistent recipe store
│   └── ds-verify · ds-reconcile · ds-vote · ds-search/   standalone primitives
├── benchmarks/                     DABench harness (dev tool, not shipped with plugin)
│   ├── runner.py · score.py · report.py · solvers.py
│   ├── runs/smoke/                 15-question benchmark results
│   └── experiments/                Exp A/B/C study — see docs/experiments/
├── config/models.json              single source of truth for model IDs and prices
├── .claude-plugin/                 plugin.json + marketplace.json
└── docs/
    ├── USAGE.md                    skill chooser + decision table
    ├── experiments/                benchmark study results and charts
    └── quickstart.md
```

---

## Benchmark results

18-question DABench dev subset of [InfiAgent-DAEval](https://github.com/InfiAgent/InfiAgent),
`claude-sonnet-4-6`. Full study: [`docs/experiments/`](docs/experiments/).

| variant | strict accuracy | field-score | $/task | notes |
|---|---|---|---|---|
| no-tools (text only) | 33% | — | $0.20 | floor — no code execution |
| **ds-star** (plugin) | **94.4%** (17/18) | 97.9% | $0.34 | code execution + iterative loop |
| **ds-star** (prompt) | **94.4%** (17/18) | 97.9% | $0.31 | SKILL.md as prompt — same result |
| ds-spike (N=3, contested Qs) | — | — | $0.90 | ensemble adds cost, not correctness, when methods already agree |

Code execution is the dominant lever (+61pp over text-only). The single remaining "miss" is
**Q8, a benchmark-label bug** — its constraint demands the *population* std, its label uses the
*sample* std; every method (ds-star, ds-star-plus, all three ds-spike personas) correctly computes
population std and is marked wrong. Effectively the skills answer all 18 correctly. Earlier drafts'
lower numbers were harness artifacts (answer truncation, last-token-wins on echoed code templates,
all-or-nothing scoring) — see [`docs/experiments/`](docs/experiments/README.md#scoring--harness-fixes).

---

## References

The suite is grounded in resent literature. The foundation is DS-STAR; the other skills
each implement a specific pattern from the recent data-science-agent literature. Full annotated
bibliography with re-fetch script: [**`papers/README.md`**](papers/README.md).

**Foundation**

Nam, Yoon, Chen & Pfister (2025). *DS-STAR: Data Science Agent via Iterative Planning and
Verification.* arXiv:[2509.21825](https://arxiv.org/abs/2509.21825). Google Cloud / KAIST.
Implemented by `ds-star` and `ds-star-plus`.

**What grounds each skill**

| skill | primary papers | pattern taken |
|-------|----------------|---------------|
| `ds-star-plus` | DS-STAR · DeepVerifier ([2601.15808](https://arxiv.org/abs/2601.15808)) · CodeAct ([2402.01030](https://arxiv.org/abs/2402.01030)) · Data Interpreter ([2402.18679](https://arxiv.org/abs/2402.18679)) · KramaBench ([2506.06541](https://arxiv.org/abs/2506.06541)) | rubric-graded decomposed verifier, code-as-action, DAG replan, two-stage retrieval |
| `ds-spike` / `ds-reconcile` | Blackboard ([2510.01285](https://arxiv.org/abs/2510.01285)) · Multi-agent debate ([2305.14325](https://arxiv.org/abs/2305.14325)) | post-and-volunteer ensemble, cross-critique |
| `ds-search` | I-MCTS ([2502.14693](https://arxiv.org/abs/2502.14693)) · SWE-Search ([2410.20285](https://arxiv.org/abs/2410.20285)) · Agent Alpha ([2602.02995](https://arxiv.org/abs/2602.02995)) · Empirical-MCTS ([2602.04248](https://arxiv.org/abs/2602.04248)) | introspective tree search, hybrid reward |
| `ds-model` | AIDE ([2502.13138](https://arxiv.org/abs/2502.13138)) · AutoKaggle ([2410.20424](https://arxiv.org/abs/2410.20424)) · AutoML-Agent ([2410.02958](https://arxiv.org/abs/2410.02958)) | solution-tree search over code drafts |
| `ds-memory` | AWM ([2409.07429](https://arxiv.org/abs/2409.07429)) · Voyager ([2305.16291](https://arxiv.org/abs/2305.16291)) · ExpeL ([2308.10144](https://arxiv.org/abs/2308.10144)) | workflow memory, skill library, experience distillation |
| `ds-conduct` | Blackboard ([2510.01285](https://arxiv.org/abs/2510.01285)) · MetaGPT ([2308.00352](https://arxiv.org/abs/2308.00352)) | data-aware orchestration, role-based SOPs |
| `ds-vote` | Self-consistency ([2203.11171](https://arxiv.org/abs/2203.11171)) | majority-vote sampling |

The v2 extensions (model routing, structured verifier, oscillation handling, digest caching) are
design choices justified against specific paper findings — see
`skills/ds-star-plus/references/evidence.md`. They are not independently benchmarked as
improvements over the baseline. **Implementation depth varies by pattern** — the expensive
inference-scaling techniques (deep MCTS value models, learned re-rankers, automatic curricula)
are documented as guidance, not fully engineered; see [`ROADMAP.md`](ROADMAP.md) for what is
built vs. deferred.

## Status

All 14 skills implemented; the solver core is **validated on DABench at 94.4% (17/18,
effectively 18/18)** — see [`docs/STATUS.md`](docs/STATUS.md) for the per-skill matrix and
[`docs/experiments/`](docs/experiments/README.md) for the full study. Unit tests live in each
`scripts/` directory (`python3 -m unittest`), and CI guards the skill registry, frontmatter,
referenced paths, and manifests. Tracks and dependency order: [`ROADMAP.md`](ROADMAP.md).
Open questions and the spike-vs-verifier circularity note:
[`skills/ds-star-plus/references/benchmark.md`](skills/ds-star-plus/references/benchmark.md).
