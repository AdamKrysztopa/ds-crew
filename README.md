# Data-science skill suite for Claude Code

> **Six installable Claude Code skills** for end-to-end data science, built on the DS-STAR agent
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
```

Or just ask an analytical question over a data file — Claude will trigger the right skill
automatically.

### Updating / uninstalling

```bash
claude plugin update ds-crew@ds-crew
claude plugin uninstall ds-crew@ds-crew
```

---

## The six skills

| skill | what it does | reach for it when |
|-------|--------------|-------------------|
| **`ds-star`** | Baseline iterative solver — analyze files → grow a verified plan one step at a time | reproducing the paper; a simple, single-model baseline |
| **`ds-star-plus`** | Hardened solver: per-role Haiku/Sonnet/Opus routing, **rubric-graded verifier**, oscillation handling, digest caching, two-stage retrieval, optional MCTS search mode | production, multi-file, cost-sensitive, high-reliability work |
| **`ds-clarify`** | Human-in-the-loop pre-flight — interrogate intent, write `analysis-spec.md` | the question is fuzzy, high-stakes, or contested — run it **before** a solver |
| **`ds-spike`** | Ensemble — N diverse data scientists in parallel, reconciled into consensus + minority report | a number that must be right; two runs disagreed (costs N× — spend for confidence) |
| **`data-profile`** | Standalone data-quality / profiling report (per-column + cross-file join checks) | onboarding a dataset; "is this data clean / what's in it?" |
| **`eda-narrative`** | Exploration → a stakeholder-ready narrative, each finding backed by a number/chart | "what's interesting here?" with no single precise question |

**Typical flow for something important:** `data-profile` → `ds-clarify` → `ds-spike` (which runs
several `ds-star-plus` solvers) → reconciled answer.

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
│   │   │   └── worked_example.md   annotated trace with backtracking
│   │   └── scripts/
│   │       ├── analyze_file.py     describer + schema digest emitter
│   │       ├── route_model.py      pick_model() routing helper
│   │       └── verify_schema.py    verdict validator (+ test_verify_schema.py)
│   ├── ds-clarify/                 human-in-the-loop spec (SKILL + checklist + template)
│   ├── ds-spike/                   ensemble: SKILL + personas + aggregation
│   │   └── scripts/aggregate.py    consensus + minority report (+ test_aggregate.py)
│   ├── data-profile/               standalone data-quality report
│   └── eda-narrative/              exploration → narrative
├── .claude-plugin/                 plugin.json + marketplace.json
├── docs/superpowers/plans/         implementation plans (e.g. rubric-verifier)
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
two-stage retrieval) are design extensions: there is no new independent benchmark, but each is
justified against a specific finding in the paper — the 3.5× input-token cost (Table 6), the
analyzer/router ablations (Table 4, e.g. hard accuracy 45.24 → 26.98 without descriptions), the
~8-point retrieval-vs-oracle gap (Table 2), and the round distribution (§4.3). The full evidence
chain is in `skills/ds-star-plus/references/evidence.md`; `skills/ds-star-plus/evals/evals.json`
provides checkable test cases.

## Status

The full roadmap is implemented: the rubric-graded verifier (DeepVerifier-style), the human-in-the-
loop `ds-clarify`, the capstone `ds-spike` ensemble (blackboard reconciliation), `data-profile`,
`eda-narrative`, and `ds-star-plus`'s optional MCTS search mode + upgraded retrieval. Each change is
tied to a paper in the bibliography at [`papers/README.md`](papers/README.md); the tracks, statuses,
and dependency order live in [`ROADMAP.md`](ROADMAP.md). The two Python helpers ship with unit tests
(`python3 -m unittest` in each `scripts/` dir).
