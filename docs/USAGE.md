# ds-crew — When to Use Which Skill

This document helps you pick the right skill for your data-science task.  
Three parts: decision table, ASCII flowchart, canonical pipelines.

---

## Core vs Advanced

The fourteen skills split into two tiers:

**Core 5 — everyday entry points** (reach for these first): `ds-conduct`, `ds-star-plus`, `ds-spike`, `data-profile`, `eda-narrative`. These cover the full daily workflow — orchestrate, solve, ensemble, profile, and explore. Most users never need anything else.

**Advanced 9 — power users and specific needs**: `ds-star`, `ds-clarify`, `ds-model`, `ds-memory`, `ds-env-setup`, and the four Track-L standalone primitives (`ds-verify`, `ds-reconcile`, `ds-vote`, `ds-search`). The Track-L primitives are extracted internals of `ds-star-plus`/`ds-spike`, surfaced for users who need fine-grained control over verification, reconciliation, voting, or tree search independently of the main solver loop.

When in doubt, start with `/ds-conduct` — it orchestrates the right Core skills for you automatically.

---

## Start here

Two ways in:

1. **Pick a profile** — [`docs/profiles.md`](profiles.md) bundles skill + model + ensemble into three presets (`quick`, `exploratory`, `production-audit`). Pick the one that matches your use case.
2. **Run `/ds-conduct`** — the recommended front door for any fuzzy request or new dataset. It peeks at your data, asks targeted questions, and routes to the right skills automatically. The default solver behind it is `ds-star-plus`, which falls back to `ds-star`/`ds-search` as needed.

## Config profiles

See [`docs/profiles.md`](profiles.md) for the full reference. Summary:

| profile | when |
|---|---|
| `quick` | Fast factoid over a clean file, low stakes |
| `exploratory` | New/unknown data, want a narrative |
| `production-audit` | High stakes, contested, must defend the number |

---

## Part 1 — Decision Table

| Skill | What it does | Reach for it when | Relative cost |
|---|---|---|---|
| `ds-conduct` | Orchestrates the full crew: peeks at data, grills the user, assembles a skill-and-sequence plan, then runs it with checkpoints | You have data and a fuzzy request with no clear workflow — "where do I start?" or "set up the analysis for me" | `$$` |
| `ds-clarify` | Interrogates every ambiguous analytical choice (metric definitions, scope, time window, nulls, units, output format) and writes a concrete `analysis-spec.md` contract | The question is under-specified, high-stakes, or contested, and you want a locked spec before any computation starts | `$` |
| `data-profile` | Inventories files, computes per-column stats (types, nulls, cardinality, distributions), flags quality issues, and cross-links multiple files | You need to understand data quality and structure before trusting any downstream analysis | `$` |
| `ds-star` | Iterative plan-execute-verify loop (analyze → code → LLM-as-judge → refine) for a single analytical question | You have a clear, moderate-stakes analytical question and want a reliable single-solver answer | `$$` |
| `ds-star-plus` | Reliability- and cost-hardened v2 of ds-star: per-role model-tier routing, graded verifier rubric, oscillation/escalation handling, context caching, smarter retrieval | The primary solver for most analytical questions — prefer over ds-star for anything non-trivial | `$$` |
| `ds-search` | Runs ds-star-plus in MCTS search mode: introspective node expansion and hybrid LLM reward estimation across multiple solution paths | A single analytical task is hard enough that greedy one-shot solving keeps failing or producing suboptimal code | `$$$` |
| `ds-spike` | Dispatches N independent data-scientist agents (diverse models, strategies, seeds) in parallel, collects answers on a blackboard, then reconciles into consensus + confidence + minority report | High-stakes, irreversible, or contested results; two prior runs disagreed; you want ensemble confidence over a single answer | `$$$$` |
| `ds-model` | AutoML solution-tree: baseline → evaluate → expand best node → repeat until metric plateau, with strict leakage/CV discipline | You want to train, tune, or iteratively improve a predictive model (classification, regression, forecasting, Kaggle) | `$$$` |
| `eda-narrative` | Breadth-first survey of the data followed by a verified written narrative — turns exploration into a human-readable story | You want a prose summary of what the data says, not a specific numerical answer | `$$` |
| `ds-verify` | Independently checks any existing answer against the DS failure rubric (scope errors, wrong columns, unit mismatches, leakage, format drift) | You have an answer in hand and want to confirm it is correct before acting on it | `$` |
| `ds-reconcile` | Clusters multiple candidate answers by agreement, weights verified ones higher, returns consensus + confidence + minority report | You already have multiple candidate answers (from different runs, analysts, or tools) and need them merged | `$` |
| `ds-vote` | Runs the same solver N times independently and tallies votes across results | You want a stability or stochasticity check — does the same question reliably produce the same answer? | `$$$` |
| `ds-memory` | Persistent cross-session recipe store: inspect past analyses, prune stale entries, or retrieve prior solutions to seed new planners | You want to reuse a past analysis, check what has been solved before, or recall which approach worked | `$` |

> **Advanced primitives:** `ds-verify`, `ds-reconcile`, `ds-vote`, `ds-search`, and `ds-memory` are advanced sub-capabilities. Most users start at `ds-conduct` or pick a profile. Reach for these only when you already have an answer to check, results to reconcile, or a specific need not served by the front-door workflow.

---

## Part 2 — Decision Flowchart (ASCII)

```
START: "I have data and a request"
│
├─► Is the request fuzzy / don't know where to start?
│       └─► ds-conduct  (orchestrates the whole crew for you)
│
├─► Want to understand data quality before anything else?
│       └─► data-profile  (stats, nulls, cardinality, cross-file links)
│
├─► Want to lock down intent before analysis runs?
│       └─► ds-clarify  (writes analysis-spec.md contract)
│
├─► Have a precise analytical question?
│   │
│   ├─► High-stakes, irreversible, or contested?
│   │   │
│   │   └─► ds-spike  (N parallel solvers → reconcile)
│   │           │
│   │           └─► Want debate rounds between solvers?
│   │                   └─► ds-spike  with  debate: true
│   │
│   └─► Normal confidence, single-solver?
│       │
│       └─► ds-star-plus  (default analytical workhorse)
│               │
│               └─► Hard task — greedy solving keeps failing?
│                       └─► ds-search  (MCTS tree search)
│
├─► Want to build or improve a predictive model?
│       └─► ds-model  (AutoML solution tree, strict CV)
│
├─► Want a narrative / exploratory story about the data?
│       └─► eda-narrative
│
├─► Want to check an existing answer for errors?
│       └─► ds-verify  (rubric: scope, units, leakage, format)
│               │
│               └─► Answer looks borderline?
│                   │
│                   ├─► ds-vote   (same solver N times — stability check)
│                   └─► ds-spike  (diverse solvers — confidence check)
│
├─► Already have multiple answers to reconcile?
│       └─► ds-reconcile  (cluster → consensus + minority report)
│
└─► Want to reuse or inspect past analyses?
        └─► ds-memory  (inspect / prune / retrieve recipe store)
```

---

## Part 3 — Canonical Pipelines

---

### Pipeline A — Full due-diligence analysis (high stakes)

For decisions where being wrong has real consequences.

```
ds-conduct
  → data-profile        (establish data quality baseline)
  → ds-clarify          (lock the spec; get human sign-off)
  → ds-spike            (N=3, debate:true — diverse parallel solvers)
  → consensus answer + minority report
```

When any spike solver disagrees materially, add `ds-reconcile` to merge the blackboard before drawing conclusions.

---

### Pipeline B — Quick analytical question

For routine, well-scoped questions where speed matters.

```
ds-star-plus
```

If the question turns out to be fuzzy or contested, prepend `ds-clarify` first:

```
ds-clarify → ds-star-plus
```

If ds-star-plus keeps failing on a hard sub-step, escalate:

```
ds-clarify → ds-search   (MCTS on the hard task)
```

---

### Pipeline C — Predictive modelling

For building and iteratively improving a model (Kaggle, forecasting, classification).

```
data-profile              (understand features, nulls, leakage risk)
  → ds-clarify            (pin down target, metric, CV strategy, submission format)
  → ds-model              (AutoML solution tree — baseline → iterate → plateau)
  → ds-verify             (check final metric for leakage and format correctness)
```

---

### Pipeline D — Confidence check on an existing result

For validating a number before reporting or acting on it.

```
ds-verify
  → if PASS:   done
  → if borderline / FAIL:
      ├─► ds-vote   (re-run same solver N times — is the answer stable?)
      └─► ds-spike  (diverse solvers — is there consensus across approaches?)
```

---

### Pipeline E — Exploratory kick-off for a new dataset

For onboarding an unfamiliar dataset and building shared understanding.

```
data-profile              (inventory + quality report)
  → eda-narrative         (breadth-first survey → verified prose story)
  → ds-conduct            (if further analysis is needed, let the conductor plan it)
```

---

## Quick-reference cheat sheet

| You say… | Start with |
|---|---|
| "Where do I even start?" | `ds-conduct` |
| "Profile this data for me" | `data-profile` |
| "Clarify what I mean by X" | `ds-clarify` |
| "What is the average / total / trend of Y?" | `ds-star-plus` |
| "This task is hard, try harder" | `ds-search` |
| "This result is high-stakes — are you sure?" | `ds-spike` |
| "Train a model to predict Z" | `ds-model` |
| "Tell me the story of this data" | `eda-narrative` |
| "Check this answer" | `ds-verify` |
| "I got two different numbers — which is right?" | `ds-reconcile` |
| "Run this 5 times and see if it agrees" | `ds-vote` |
| "Have we solved something like this before?" | `ds-memory` |
