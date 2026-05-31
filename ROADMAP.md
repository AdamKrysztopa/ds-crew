# Roadmap — toward a suite of recent data-science skills

This repo started as a faithful implementation of DS-STAR (`ds-star`) plus a reliability- and
cost-hardened successor (`ds-star-plus`). This document plans the tracks below:

- **Track A** — concrete improvements to `ds-star-plus`, each pulled from a specific newer paper.
- **Track B** — new data-science skills, led by the human-in-the-loop "grill" skill.
- **Track D** — the `ds-spike` ensemble capstone.
- **Track C** — repo evolution into a data-science skill suite.

Every item is tied to a source in [`papers/`](papers/README.md). Status legend:
🟢 ready to build · 🟡 needs a design decision · ⚪ exploratory · ✅ **implemented**.

> **Implementation status (2026-05-31): all tracks shipped.** A1 ✅ (rubric verifier + tests),
> A2 ✅ (`references/search_mode.md`), A3 ✅ (`references/retrieval.md`), B1 ✅ (`ds-clarify`),
> B2 ✅ (`data-profile`), B3 ✅ (`eda-narrative`), D ✅ (`ds-spike` + tested aggregator),
> C ✅ (suite framing in README + manifests, v1.1.0). The sections below are kept as the design
> rationale and the record of *why* each was built the way it was.

---

## Track A — improving `ds-star-plus`

### A1 🟢 v2.1 — rubric-guided, decomposed verifier (from DeepVerifier)

**Source:** DeepVerifier, [2601.15808](https://arxiv.org/abs/2601.15808).

**Why.** The verifier is the one unrecoverable decision in the loop (a false "sufficient" ends the
run wrong, silently). v2 already hardened it (rationale + `missing` + 3× vote + Opus). DeepVerifier
is the next rung on the *same* ladder and is cost-aligned: it beats a vanilla LLM-judge by **12–48%
F1**, lifting *recall of catching wrong answers from 14% → 71%* (their GAIA-Web ablation), with no
training. This directly attacks DS-STAR's core failure mode.

**What changes.** Replace the current `{sufficient: bool, reason, missing}` verifier with a
rubric-scored, decomposed one:

1. **Fixed DS-failure rubric.** Turn our "common pitfalls" list into an explicit checklist the
   verifier scores against every time: wrong column/value · silently dropped rows · units mismatch ·
   scope error (wrong filter/time window/entity) · format mismatch · question-substitution (answered
   a different question). This is DeepVerifier's "failure taxonomy → rubric" applied to data science.
2. **Decomposition over holistic judgement.** Instead of one all-or-nothing verdict, emit ≤3
   targeted follow-up checks (e.g. "does the printed scope match the asked scope?", "are the units
   the asked units?") and answer each — cheaper than re-judging the whole task.
3. **Graded 1–4 verdict** (1 = clearly wrong … 4 = clearly sufficient) instead of a bool, with
   early-stop when the verdict is confidently 4 and no rubric item fails. Maps cleanly onto the
   existing early-exit guardrail.

**Files:** `skills/ds-star-plus/references/prompts.md` (verifier prompt), `SKILL.md` (verify stage),
new `references/evidence.md` entry citing 2601.15808, `evals/evals.json` (cases that exercise each
rubric item). **Effort:** small–medium, no new scripts. **Risk:** low; it's a strict superset of the
current verifier.

### A2 🟡 v2.2 — optional MCTS "search mode" for hard tasks (from I-MCTS / SWE-Search)

**Sources:** I-MCTS [2502.14693](https://arxiv.org/abs/2502.14693), SWE-Search
[2410.20285](https://arxiv.org/abs/2410.20285), Empirical-MCTS
[2602.04248](https://arxiv.org/abs/2602.04248), Agent Alpha
[2602.02995](https://arxiv.org/abs/2602.02995).

**Why.** DS-STAR refines greedily — one sampled next step per round. v2 already branches to 2–3
candidates on oscillation; MCTS is the principled generalization. Two transferable ideas:
- **Introspective node expansion** (I-MCTS): generate the next candidate by reflecting on the
  solutions+results of *sibling* attempts, not just the parent — "here's what the neighbours tried
  and scored, do better."
- **Hybrid reward** (I-MCTS): an LLM value-model *estimates* a branch's promise before paying for a
  full execution rollout, then blends toward the real execution score — so search prioritizes without
  running every candidate. SWE-Search shows this whole pattern transfers to code-writing agents.

**The tension (why 🟡).** MCTS multiplies LLM calls — it fights the cost-hardening thesis that
*defines* `ds-star-plus`. **Decision needed:** ship this as an explicit opt-in `search_mode` reserved
for the hard tail (the ~5.6-round, multi-file tasks where DS-STAR's Fig 4 shows more compute pays),
**not** as a default. Empirical-MCTS's dual success/failure memory would feed our anti-repeat list.

**Files:** new `references/search_mode.md`, `scripts/` helper for the value-model scoring, `SKILL.md`
escalation section. **Effort:** large. **Gate:** only after A1 lands and we can measure whether the
verifier is reliable enough to be the MCTS reward signal.

### A3 ⚪ Retrieval upgrade for data lakes

**Source:** KramaBench [2506.06541](https://arxiv.org/abs/2506.06541) (the ~8-pt oracle gap).
v2 already added a Haiku relevance pass; a learned re-ranker or column-level matching could close
more of the gap. Low priority until A1/A2.

---

## Track B — new data-science skills

### B1 🟢 `ds-clarify` — human-in-the-loop pre-flight (the flagship new skill)

**Inspiration:** the superpowers `grill-with-docs` / `grill-me` pattern (relentless decision-tree
interrogation that updates docs inline). **Grounding:** DS-STAR's own paper names this as *the* future
direction — §5: *"extend this framework to a human-in-the-loop setting... combine the automated
capabilities of DS-STAR with the intuition and domain knowledge of a human expert."*

**The gap it fills.** DS-STAR's verifier can confirm the output answers *the question as the agent
understood it* — it cannot know the user's *true* intent. The classic silent failure (the paper's
own NexPay case, Fig 3) is partly intent ambiguity: what counts as "active"? which timezone? how are
nulls/dupes handled? what are the units? Tie-breaks? Output format? No amount of verification fixes a
precisely-answered *wrong question*.

**Shape.** A skill that, before (and optionally during) a `ds-star`/`ds-star-plus` run:
1. **Grills the user** through the ambiguity decision tree — metric definitions, scope/filters, time
   windows + timezone, null/dedup/outlier handling, units, rounding, tie-breaking, exact output
   format — resolving each branch like `grill-with-docs` does for plans.
2. **Emits a written `analysis-spec.md`** (the agreed contract) that the DS-STAR verifier then checks
   the output against — turning fuzzy intent into a checkable rubric (dovetails with A1).
3. **Optional mid-run checkpoints** at router backtracks: surface the consequential assumption and
   confirm before spending more rounds.

**Files:** new `skills/ds-clarify/SKILL.md` + `references/clarify_checklist.md` (the decision tree) +
`references/spec_template.md`. **Effort:** medium. **Note:** complements rather than replaces the
autonomous skills — invoke it when stakes are high or the query is under-specified.

### B2 ⚪ `data-profile` — standalone deep data-quality report

Promote DS-STAR's Stage-1 analyzer into a first-class skill: a thorough profiling / data-quality
report (types, missingness, cardinality, candidate keys, anomalies, encoding issues) for any file or
folder, usable on its own. Reuses `analyze_file.py`. Low effort, high standalone utility.

### B3 ⚪ `eda-narrative` — guided EDA to a written narrative

A skill that runs an exploratory pass and produces a narrative report (findings + charts), distinct
from DS-STAR's question-answering loop. Exploratory.

---

## Track D — `ds-spike`: the multi-data-scientist ensemble (capstone)

> **The idea (user's):** for a specific data-science problem, run a *spike* — several independent
> "data scientists" working the same problem in parallel — then collect and reconcile findings from
> all of them into one answer plus the disagreements.

**Status:** 🟡 capstone — buildable as soon as A1 + B1 land (see "When can we start", below).

**Why this is principled, not crazy.** This is **inference-time scaling by parallel rollouts +
aggregation** — best-of-N / self-consistency lifted from the verifier (where v2 already uses 3× vote)
to the *whole pipeline*. The collaboration substrate already exists in the literature, by the DS-STAR
authors themselves: the **blackboard architecture** ([2510.01285](https://arxiv.org/abs/2510.01285)) —
a central agent posts a request to a shared blackboard and autonomous sub-agents *volunteer* by
capability, no rigid master-slave coordinator. It reports **+13–57% relative** end-to-end success on
the same benchmarks DS-STAR uses. Agent-Alpha ([2602.02995](https://arxiv.org/abs/2602.02995)) and
Empirical-MCTS ([2602.04248](https://arxiv.org/abs/2602.04248)) supply the generation/evaluation and
dual-experience-memory pieces.

**Shape.**
1. **Spec once (B1).** Run `ds-clarify` first so every scientist solves the *same* question — without
   a shared spec, parallel agents diverge on intent, not method, and the ensemble is noise.
2. **Dispatch N diverse solvers.** N parallel `ds-star-plus` runs that differ deliberately — model
   tier (Opus vs Sonnet), strategy/persona (cautious statistician · ML-first · SQL/join-first ·
   assumption-minimal), and seed. Diversity is what makes an ensemble beat a single run. Uses the
   superpowers `dispatching-parallel-agents` machinery; each agent runs in isolation.
3. **Blackboard collection.** Each scientist posts to a shared workspace: `{answer, final code, plan,
   verifier verdict + rationale, key assumptions}` — the [2510.01285] post-and-volunteer pattern.
4. **Lead/aggregator reconciles (Opus).** A meta-agent clusters answers, runs the **A1 rubric
   verifier** on each, and produces: a **consensus answer + confidence**, *and* a **minority report**
   — where solvers disagreed and *why* (divergent assumptions are themselves the insight: "3 of 5
   excluded refunds; 2 included them → the number hinges on that choice"). Agreement across diverse
   strategies is a far stronger correctness signal than one agent's self-verification.

**Cost (the honest caveat).** N full runs ≈ N× the cost — the most expensive thing in the repo, and
in direct tension with the cost-hardening that defines `plus`. So `ds-spike` is **explicitly
high-stakes-only**: irreversible decisions, board-level numbers, contested results, or a task where
two earlier single runs disagreed. Default N = 3. It is a deliberate "spend for confidence" mode, the
mirror image of v2's "save on plumbing."

**Dependencies:** **A1** (the verifier is the aggregator's scoring function) and **B1** (the shared
spec). Reuses the blackboard pattern; independent of A2 (A2 is *intra*-agent search, `ds-spike` is
*inter*-agent search — orthogonal, composable later).

**Files:** new `skills/ds-spike/SKILL.md` + `references/aggregation.md` (clustering + minority-report
rules) + `references/personas.md` (the diversity axes) + `references/evidence.md` (cite 2510.01285).
**Effort:** medium–large, mostly orchestration over existing skills.

---

## Track C — repo evolution

Once Track A1 + B1 land, the repo is no longer "just DS-STAR" — it's a **suite of recent
data-science skills** (autonomous solving, human-in-the-loop clarification, profiling). Plan:

- Rename the repo / marketplace to reflect the suite (e.g. *data-science-skills* or *ds-skills*),
  update `.claude-plugin/marketplace.json`, `plugin.json`, and install docs.
- Keep `papers/README.md` as the living bibliography so the repo visibly tracks the current literature.
- Each skill stays independently installable; `ds-clarify` is the connective tissue between them.

---

## Suggested order

1. **A1** (rubric verifier) — biggest reliability win, smallest blast radius, cost-aligned. *No blockers.*
2. **B1** (`ds-clarify`) — the human-in-the-loop skill; pairs naturally with A1's rubric. *No blockers.*
3. **D** (`ds-spike`) — the multi-data-scientist ensemble. **Unlocked the moment A1 + B1 exist** (it
   uses A1 as its judge and B1 as its shared spec). The capstone — build it third.
4. **C** (repo rename) — once A1 + B1 (+ D) exist, the "suite of data-science skills" name is earned.
5. **A2** (search mode) — only after A1 makes the verifier a trustworthy reward signal.
6. **B2 / B3 / A3** — opportunistic.

```
A1 (rubric verifier) ─┐
                      ├─► D (ds-spike ensemble) ─► C (repo rename)
B1 (ds-clarify) ──────┘
A2 (MCTS) ── independent, opt-in, later
```

## When can we start to implement "all"?

**Now — nothing is blocked at the front of the chain.** The critical path is **A1 → B1 → D**, and
A1 has zero dependencies. So:

- **Start today:** A1 (rubric-guided verifier). Pure upgrade to one prompt + SKILL.md + evals; low risk.
- **Then:** B1 (`ds-clarify`), planned through the brainstorming + write-a-skill skills first.
- **Then `ds-spike` becomes buildable** — it is *only* gated on A1 + B1, both of which are small/medium.
  Nothing in the SPIKE idea needs the expensive A2 (MCTS) first.

In short: we can begin the whole sequence immediately; `ds-spike` is reachable right after the two
foundational pieces, not after the entire backlog.

Open decisions before building: (1) A2 default-off vs cut entirely; (2) final skill names
(`ds-clarify`, `ds-spike`?); (3) whether `ds-clarify` writes its spec into the same data dir the
DS-STAR skills read from; (4) `ds-spike` default N and its diversity axes (model × persona × seed).
