---
name: ds-star-plus
description: "Solve data science tasks over one or many data files (CSV, JSON, Excel/XLSX, Markdown, TXT, SQLite, unstructured text) by writing and executing Python through an iterative plan, implement, execute, verify, refine loop with a rationale-bearing LLM-as-judge and per-role Opus/Sonnet/Haiku routing. Use this skill WHENEVER the user asks a factoid or analytical question answered from data files, wants wrangling/cleaning, EDA, statistics/hypothesis testing, a chart, or an ML prediction/submission produced FROM their data, especially when the answer reconciles MULTIPLE heterogeneous files, when the code runs but might still be wrong, or when an attempt looks plausible but unverified. Trigger even if the user just drops files and asks what this says or to answer X, or uses words like analyze, compute, aggregate, join, merge, clean, summarize, predict, forecast, plot, or delta/total/top-N. This is the cost-aware, reliability-hardened successor to ds-star. Do NOT use for prose writing or generic coding with no file."
---

# DS-STAR+ : reliability- and cost-hardened iterative data science agent

This is **v2** of the DS-STAR workflow. It keeps the proven core — never trust code just
because it ran; grow a plan one *verified* step at a time — and adds four things the base
method left on the table: a verifier that explains itself, model-tier routing so you spend
big-model budget only where it pays, oscillation/escalation handling, and context caching to
cut the ~3.5x token overhead. If you have not seen the base method, the same six stages from
`../ds-star/SKILL.md` apply; this file describes only what changes and why.

Read `references/model_routing.md` for the full routing policy and `references/prompts.md`
for the upgraded role prompts. A worked trace is in `references/worked_example.md`. Every change
below is justified against specific paper findings (tables, numbers) in `references/evidence.md` —
read that for the full "why this and not something else."

## The cardinal rule (unchanged)

Executable code is not a correct answer. The loop exists to catch the plausible-but-wrong
result before it is reported.

---

## What changed in v2

### 1. Per-role model-tier routing (the headline change)

The base method runs every role on one big model. Most roles do not need it. Route by the
cognitive load of the role, then *escalate* only when a task proves hard. Concrete tiers map
to the current models: **Opus** = `claude-opus-4-8` (deepest reasoning), **Sonnet** =
`claude-sonnet-4-6` (strong default for code/reasoning), **Haiku** = `claude-haiku-4-5`
(fast/cheap, high call volume). Always prefer the latest snapshot of each tier.

| Role | Default tier | Why | Escalate to | Escalation trigger |
|------|--------------|-----|-------------|--------------------|
| Analyzer | **Haiku** | Many near-identical describe-the-file scripts, run in parallel; low reasoning | Sonnet | script fails to load a file after 1 debug pass |
| Planner (initial) | **Haiku** | "Load file X and peek" is trivial | Sonnet | — |
| Planner (next step) | **Sonnet** | Must reason about the gap from real output | **Opus** | 2+ rounds with no progress, or oscillation flag |
| Coder | **Sonnet** | Solid incremental codegen | **Opus** | same code area fails 2x after debug |
| **Verifier** | **Opus** | Load-bearing judge; false "sufficient" ends the run with a wrong answer | (stays Opus) | — |
| Router | **Sonnet** | add vs backtrack + pick which step | **Opus** | when planner is escalated |
| Finalizer | **Haiku** | Reformat an already-correct result | Sonnet | guidelines are complex (multi-file, schema match) |
| Debugger (trim trace) | **Haiku** | Pure text reduction | — | — |
| Debugger (fix code) | **Sonnet** | Needs data context + code reasoning | Opus | 2 failed fixes on the same error |

Rule of thumb: **spend on judgment, save on plumbing.** The verifier is the one place a
cheap model is a false economy — a wrong "sufficient" is unrecoverable, so it runs on Opus by
default. Everything that merely transforms text or writes boilerplate starts on Haiku.

*Why this is safe (paper-grounded):* the paper runs every role on one model, but its own ablation
(Table 4) shows the roles are not equally load-bearing — only the **analyzer** (remove it → hard
accuracy 45.24 → 26.98) and **router** (remove it → 45.24 → 39.95) decisively move accuracy, while
the analyzer also has the highest call volume (one parallel call per file, Algorithm 1). Routing by
load attacks the $0.23 / 12.7-call / 154,669-input-token profile in Table 6 without touching what
Table 4 proved is critical. See `references/evidence.md` §1.

`scripts/route_model.py` encodes this table: call
`pick_model(role, attempt=N, oscillating=False, hard=False)` to get the model id to use for a
given role and situation, so routing is consistent rather than ad hoc.

### 2. Verifier returns a graded score, a rubric, a rationale AND what's missing

In v1 the judge says only Yes/No. That makes false "sufficient" both common and silent. v2.1
makes the verdict structured and graded: a `score` (1–4), a fixed six-item `rubric` of the DS
failure modes each marked pass/fail/na (see `references/rubric.md`), up to three decomposed
`checks`, a one-line `reason`, and `missing` (what still needs to happen). The answer is
sufficient ONLY when `score == 4` and no rubric item is `fail`. `scripts/verify_schema.py`
parses and enforces this contract. Three payoffs:

- The router and next planner step now condition on `missing`, so refinement targets the real
  gap instead of guessing.
- On a `sufficient` verdict the `reason` must explicitly tie the printed output to the exact
  question (units, scope, format). If it cannot, that *is* an insufficiency.

For high-stakes or borderline answers, run the verifier **3x and take majority** (self-
consistency). Cheap insurance on the one decision that can silently end the run wrong.

*Why:* the paper's verifier is strictly binary (§3.2: `v ∈ {sufficient, insufficient}`) and the loop
terminates the instant it says "sufficient" (Algorithm 1), so a false "sufficient" is unrecoverable —
this is the exact silent-wrong-answer failure of Figure 3. Self-consistency is the paper's own
recommended hardening for high-stakes multi-step pipelines (cited in the Text-to-SQL related work,
§2); v2 spends it only on the verdict that can end the run wrong. See `references/evidence.md` §2.

### 3. Oscillation and escalation handling

Backtracking can loop: the router removes step 3, the planner proposes a near-identical step
3, it fails again. This is the paper's own diagnosis — in-place revision yields "an overly complex
replacement, therefore frequently flagged again by the router in a next iteration" (§3.2) — except
random resampling with no memory can re-derive the *same* bad step. The paper runs to a 20-round cap
and Fig 4b shows accuracy still rising at the cap, i.e. some tasks burn the whole budget spinning.
v2 tracks, per task, a short **anti-repeat list** of step descriptions that were already flagged
wrong. When the planner is about to regenerate a truncated step:

- Pass the anti-repeat list so it must propose a *materially different* approach.
- If the same step index has been truncated **twice**, set `oscillating=True` → escalate
  planner+router to Opus and ask for a different strategy, not a tweak.
- If two distinct strategies both fail, sample **2-3 candidate next steps** (planner) and let
  the verifier pick the most promising — a light search instead of a single greedy sample.

### 4. Context caching to cut token cost

v1 re-feeds every full file description into every role on every round (the main reason it
uses ~3.5x ReAct's input tokens — Table 6: 154,669 vs 44,691 input tokens, a cost the paper
blames squarely on "comprehensive analytic descriptions of each data file"). v2 keeps a compact
**schema digest** per file (name, column names + dtypes, sheet names, a 1-line summary) and passes
only that by default. Pass the full verbose description only (a) to the coder/debugger when it
touches that specific file, or (b) when a role explicitly asks for it. Cache digests and
descriptions for the task so they are computed once. Expect meaningful token savings on multi-file
tasks with no accuracy loss, because planning rarely needs the full head-dump — it needs the schema.

**The non-negotiable constraint here:** the description is *also* the biggest correctness lever in
the whole method — Table 4 shows removing it collapses hard accuracy 45.24 → 26.98. So the cost
driver and the correctness driver are the same object. v2 therefore *compresses* the description
(digest by default), it never *deletes* it: the full description still reaches the coder/debugger at
the exact point Table 4's signal is consumed. "Send less data context" without this rule would walk
into an 18-point accuracy cliff. See `references/evidence.md` §4.

### 5. Smarter retrieval for data lakes (>100 files)

v1's top-K-by-embedding leaves accuracy on the table — on KramaBench (Table 2) the oracle setting
(relevant files handed in) scores 52.55 vs 44.69 with retrieval, a ~8-point gap the paper itself
flags as "advanced data discovery... a promising direction." v2 uses two cheap stages: (a) embed
query vs file digests, take top ~150; (b) a Haiku relevance pass that keeps only files plausibly
needed for *this* query, down to ~top-K. The relevance pass is cheap and recovers files that embed
poorly but are clearly on-topic by name/columns. See `references/evidence.md` §5.

---

## The loop, with v2 wiring

1. **Analyze** every file (Haiku, parallel) → keep both a verbose description and a schema
   digest. Cache both. Retrieve/trim if it is a data lake.
2. **Initialize** with one simple executable step (Haiku planner → Sonnet coder) and run it.
   For multi-file joins or multiple independent outputs, represent the plan as a DAG (see `references/planning_graph.md`); linear chain is the default for simple tasks.
3. **Verify** (Opus): get `{score, rubric, checks, reason, missing}` (validate with
   `scripts/verify_schema.py`). Borderline/high-stakes → 3x vote. `score == 4` and no rubric
   `fail` → Stage 5.
4. **Route** (Sonnet, Opus if escalated): `Add Step` or `Step l`. On backtrack, truncate and
   regenerate with the anti-repeat list; detect oscillation and escalate/branch as above.
   Re-implement incrementally (Sonnet coder, full description only for touched files),
   execute, return to step 3. Cap at 20 rounds; on cap, finalize best plan and say so.
   On a node failure in a DAG plan, re-wire only the failed node's descendants (see `references/planning_graph.md`); keep oscillation/branch logic unchanged.
5. **Finalize** (Haiku, Sonnet if format is complex) to the exact required output format.
6. **Debug** on any error: trim trace (Haiku) → fix with data context (Sonnet, Opus after 2
   failures).

Execution policy + provenance: see `references/sandbox.md`.
Two execution modes (script default / kernel opt-in): see `references/execution.md`.

## Early-exit guardrail (cost)

Easy tasks often finish in one round; the paper (§4.3, Fig 4) shows easy tasks average 3.0 rounds
with >50% solved by the initial plan p₀ alone, while hard tasks average 5.6 rounds and 98% need at
least one refinement. The distribution is bimodal, so do not burn rounds proving the obvious: if the
initial result already cleanly answers the question and the verifier's `reason` ties output to the
question with no `missing` items, finalize immediately. Reserve the heavy loop for the iterative tail
where the paper shows it pays. See `references/evidence.md` §6.

## Quick reference

Routing policy + model ids: `references/model_routing.md`.
Paper-grounded justification for every v2 change (tables + numbers): `references/evidence.md`.
Upgraded role prompts (structured verifier, anti-repeat planner): `references/prompts.md`.
Verifier rubric (the six DS failure modes): `references/rubric.md`.
Optional MCTS search mode for hard tasks: `references/search_mode.md`.
Data-lake retrieval policy (two-stage + column matching): `references/retrieval.md`.
Worked trace with backtracking: `references/worked_example.md`.
Routing helper: `scripts/route_model.py`. File describer: `scripts/analyze_file.py`.
Verdict validator: `scripts/verify_schema.py`. Test cases: `evals/evals.json`.
