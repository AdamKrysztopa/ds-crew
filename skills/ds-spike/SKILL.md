---
name: ds-spike
description: "Use when a number must be right — runs N diverse data scientists in parallel and reconciles into consensus + minority report"
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

**Lock the file-set here too (multi-file / data-lake).** If retrieval is in play, select the relevant
file-set **once** at this stage using the column-level protocol
(`../ds-star-plus/references/retrieval.md` Stage 3) and record it *in the shared spec* — do not let
each solver re-retrieve. Letting N solvers each pick their own files reintroduces the very
divergence the shared spec exists to remove (they'd be solving subtly different problems); a single
locked, recall-biased file-set keeps the ensemble measuring *method* variance, not *input* variance.

### Stage 2 — Dispatch N diverse solvers

**Cost guardrail (default on):** Before launching N agents, estimate N× cost. If the estimate exceeds $1.00 or ~200k tokens, confirm with the user first. After the run, report actual `cost_usd` from each solver manifest. See `references/cost_guardrails.md` for the full pattern.

Launch N parallel `ds-star-plus` runs that differ **deliberately** — diversity is what makes an
ensemble beat one run. Vary along the axes in `references/personas.md`: model tier (Opus vs
Sonnet), strategy/persona (cautious statistician · ML-first · SQL/join-first · assumption-minimal),
and random seed. Each runs in isolation (use the parallel-agent dispatch machinery) against the
same spec and data.

**Memory (opt-in):** If a store exists at `./.ds-crew-memory/recipes.jsonl`, seed each persona's
assumption list with relevant minority-report assumptions from prior runs retrieved via `retrieve()`.
This surfaces historical disagreement points as explicit starting assumptions, sharpening diversity
without biasing solvers toward the same answer.

Execution policy + provenance: see `../ds-star-plus/references/sandbox.md`.

### Stage 3 — Collect on the blackboard

Each solver posts a record: `{id, answer, sufficient, final_code, key_assumptions}`. Keep them
side by side — this shared board is the [2510.01285] post-and-collect pattern.

### Stage 3.5 — Debate (opt-in, flag: `debate: true`)

**Default: disabled. One-shot mode is the default.**

When `debate: true` is passed, run up to 2 structured debate rounds after Stage 3 before
proceeding to Stage 4. Full protocol: `references/debate.md`.

**2-round protocol:**
Each solver receives all peer answers and rationales, then may revise its answer. If it revises,
its record is updated with `revised: true` (tracked by `aggregate()` as `n_revised`). After ≤2
rounds — or as soon as a round produces no revisions — the final post-debate answers proceed to
Stage 4.

**Anti-herding guard:** Debate can amplify a confident-wrong majority. Solvers that did NOT revise
keep their original answer in the minority report regardless of peer pressure. The minority report
always reflects the post-debate dissent, not just pre-debate disagreement.

**Cost:** Adds ≤2 extra LLM rounds per solver (e.g. N=3 → up to 6 extra calls). Reserve for
cases where iterative convergence is worth the cost. See `references/debate.md` for the full
protocol and the Du et al. 2305.14325 citation.

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

## What this cannot guarantee

This skill is markdown driving a model across a long context. No process can enforce
that the verifier, routing, and oscillation-handling steps actually ran as specified.

**Mitigation:** emit a structured `runlog.json` with these fields after each run:
- `rounds` (int): number of loop iterations
- `verifier_verdicts` (list): `[{"round": N, "score": 1-4}, ...]` for each round
- `oscillated` (bool): whether oscillation was detected
- `subrun_cost_usd` (list): cost per sub-run (ds-spike only; empty list for single-solver skills)

Validate it:
```bash
python3 skills/ds-spike/scripts/runlog.py runlog.json
```

If it reports errors, the loop was not followed; do not present the answer as verified.
This makes deviations *detectable after the fact*, not *impossible*.

### Verifier-as-reward circularity (important)

Both ds-spike and ds-search *score* candidate answers with the same A1-rubric verifier
(`../ds-star-plus/scripts/verify_schema.py` + `../ds-star-plus/references/rubric.md`) they use *inside*
each solver. A biased judge is therefore amplified, not caught — the meta-aggregator
inherits the same blind spot as the solvers it is judging.

**Rule:** the meta-aggregator MUST run on a **different model instance** (and preferably
a different tier) than the in-solver verifier. Concretely: if solvers verify with Opus,
the cross-run aggregator must be a separate Opus instance with an independent prompt, or
a different model tier — never reuse the same verifier call or context. This is a
mitigation, not a proof of independence.

## Quick reference

Diversity axes for the solvers: `references/personas.md`.
Clustering + consensus + minority-report rules: `references/aggregation.md`.
Aggregator: `scripts/aggregate.py` (tests: `scripts/test_aggregate.py`).
Why a panel beats one run (blackboard + best-of-N evidence): `references/evidence.md`.
Opt-in debate protocol (Du et al. 2305.14325): `references/debate.md`.
