---
name: ds-spike
description: "Run a SPIKE on a high-stakes data-science problem: dispatch several independent data-scientist agents (diverse models, strategies, and seeds) to solve the SAME specified question in parallel, collect their answers + code + assumptions on a shared blackboard, then reconcile them into one consensus answer with a confidence and a minority report of where (and why) they disagreed. Use this skill WHENEVER a data result is high-stakes, irreversible, contested, or when two earlier single runs disagreed, or when the user asks for an ensemble / second opinion / spike / panel of data scientists / best-of-N on a data question, or wants to know how confident to be in a number. Agreement across diverse independent solvers is a far stronger correctness signal than one agent's self-check. This is the expensive, spend-for-confidence mode (N full runs) — reserve it for decisions that justify the cost. Pairs with ds-clarify (shared spec) and ds-star-plus (the solver). Do NOT use for routine, low-stakes, or already-settled questions."
---

# ds-spike : a panel of data scientists, reconciled

For a number that actually matters, one agent's self-verification is not enough — even a good
verifier can be confidently wrong in a way nothing downstream catches. A **spike** runs the
problem several times *independently and diversely*, then treats **agreement across different
approaches** as the real confidence signal and **disagreement as the insight** (where solvers
diverge usually reveals the one assumption the answer hinges on).

This is inference-time scaling by **parallel rollouts + aggregation** — the verifier's 3× vote
(in `ds-star-plus`) lifted from the judge to the whole pipeline (best-of-N / self-consistency).
The collaboration substrate is the **blackboard architecture** of Salemi, Yoon, Pfister et al.
(arXiv:2510.01285) — by the DS-STAR authors — where agents post to and volunteer from a shared
workspace rather than obeying a rigid central controller. See `references/evidence.md`.

## When this applies (and the cost honesty)

Use it for **high-stakes / irreversible / contested** results, or when two single runs already
disagreed. It costs ≈ **N× a single run** — the most expensive mode in this suite, in deliberate
tension with `ds-star-plus`'s cost-hardening. Default **N = 3**. This is the mirror image of
"save on plumbing": here you *spend for confidence*. Do not spike routine questions.

## The cardinal rule

**Concordance, not a single confident answer, is the signal.** Five agents agreeing via five
different routes is strong evidence. Five agents agreeing because they made the *same* unstated
assumption is not — which is why every solver must report its assumptions, and why divergence is
reported, never hidden.

## How to run the spike

### Stage 1 — Lock the question (use `ds-clarify`)

Run `../ds-clarify` first and write `data/analysis-spec.md`. Without a shared spec the agents
diverge on *intent* rather than *method*, and the ensemble is noise instead of signal. Every
solver gets the identical spec.

### Stage 2 — Dispatch N diverse solvers

Launch N parallel `ds-star-plus` runs that differ **deliberately** — diversity is what makes an
ensemble beat one run. Vary along the axes in `references/personas.md`: model tier (Opus vs
Sonnet), strategy/persona (cautious statistician · ML-first · SQL/join-first · assumption-minimal),
and random seed. Each runs in isolation (use the parallel-agent dispatch machinery) against the
same spec and data.

### Stage 3 — Collect on the blackboard

Each solver posts a record: `{id, answer, sufficient, final_code, key_assumptions}`. Keep them
side by side — this shared board is the [2510.01285] post-and-collect pattern.

### Stage 4 — Reconcile (Opus lead)

Feed the records to `scripts/aggregate.py` (`aggregate(results)`), which clusters answers (numeric
tolerance or normalized strings), weights *verified* solvers above unverified ones, and returns a
**consensus answer + confidence** plus a **minority report**. Then the lead agent (Opus) reads the
minority report and explains *why* clusters diverged (e.g. "3 of 5 excluded refunds, 2 included
them → the figure hinges on that choice") and, if the spec is silent on that fork, escalates it back
to the user rather than silently picking. Rules: `references/aggregation.md`.

### Stage 5 — Report

State the consensus answer, the confidence (share of weighted support), and the minority report.
If confidence is low (no majority, or the top cluster is thin), say so plainly and surface the
deciding assumption — a contested number reported as contested is the correct output, not a failure.

## Output

```
Consensus: 41.7%   confidence 0.83 (5 solvers, 2 clusters)
Minority: 1 solver got 39.4% — included refunds (negative amounts); spec said exclude.
Deciding assumption: refund handling.
```

## Quick reference

Diversity axes for the solvers: `references/personas.md`.
Clustering + consensus + minority-report rules: `references/aggregation.md`.
Aggregator: `scripts/aggregate.py` (tests: `scripts/test_aggregate.py`).
Why a panel beats one run (blackboard + best-of-N evidence): `references/evidence.md`.
