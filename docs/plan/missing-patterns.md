# Implementation plan — the missing literature patterns

**Branch:** `plan/missing-patterns` · **Status:** plan only, nothing implemented yet.

This plans the six pattern gaps surfaced by the citation/pattern audit — techniques that are in
`papers/` and named in the ROADMAP but **not fully built**. Each is judged against the three
standing principles, *not* "build everything":

- **P0 — Claude-native only.** No trained models, no external agent frameworks. A "value model"
  or "re-ranker" here means a *Claude call with a focused prompt*, never a fine-tuned artifact.
- **Cost thesis.** `ds-star-plus` exists to be cheap. Anything that multiplies LLM calls must be
  opt-in and reserved for a hard tail with a measured payoff.
- **Streamline beats add.** No new top-level skill unless a benchmark or a real user pull demands
  it. Prefer deepening an existing skill.
- **Integrated, not just standalone.** Every pattern below must serve the orchestration fabric —
  `ds-conduct`, `ds-clarify`, `ds-spike`, `ds-star-plus` — wherever it makes sense, not only as a
  leaf capability. A retrieval improvement only the solver can reach, or a memory rule only
  `ds-star-plus` sees, is **half-built**. Each mechanism ships as a reusable script/reference that
  the meta-skills *call*, mirroring the Track-L "primitive used everywhere" design (`ds-verify` /
  `ds-reconcile` are internals of the solvers *and* standalone). The integration matrix below is
  part of the definition of done — a phase is not complete until its consumers are wired.

## Verdict at a glance

| # | Pattern (paper) | Where | Gap | Verdict |
|---|---|---|---|---|
| 5 | Column-level retrieval (KramaBench 2506.06541) | `ds-star-plus` | only Haiku relevance pass; ~8pt oracle gap unaddressed | **BUILD — Phase 1** |
| 2 | Rule distillation (ExpeL 2308.10144) | `ds-memory` | stores concrete recipes, no abstract heuristics | **BUILD — Phase 2** |
| 4 | Dual-experience memory (Empirical-MCTS 2602.04248) | `ds-search` | failure side only (anti-repeat); no success store | **BUILD-small — Phase 2** (reuse ds-memory) |
| 3 | Hybrid-reward value model (I-MCTS 2502.14693) | `ds-search` | prompt-level estimate, not engineered | **DEFER** — keep prompt-level |
| 1 | Automatic curriculum (Voyager 2305.16291) | `ds-memory` | not built | **SKIP** — contradicts kickoff thesis |
| 6 | Unified gen/explore/eval (Agent Alpha 2602.02995) | `ds-search` | referenced, not a distinct loop | **SKIP** — already covered; cite as influence |

The two SKIPs and one DEFER are deliberate: they are the expensive, open-ended self-improvement
techniques that fight the cost thesis and serve no current user. Recording them here so they are
not silently re-added later.

---

## Phase 1 — Column-level retrieval (the one with measured payoff)

**Why first.** This is the only gap with a *quantified* benefit in the literature the repo
already cites: KramaBench Table 2 shows DS-STAR at **44.69 with retrieval vs 52.55 oracle** — a
~8pt gap caused purely by retrieval misses (`ds-star-plus/references/evidence.md §5`). Pure
embedding cosine misses files that are obviously on-topic by **column name / dtype** but embed
poorly against the query phrasing. Closing this improves correctness on multi-file / data-lake
tasks, which is exactly where the suite claims to help.

**What to build (Claude-native).** A second, cheap re-rank stage layered onto the existing Haiku
relevance pass — *not* a learned re-ranker:
1. From the user's question, extract candidate entities/metrics (Haiku).
2. For each candidate file, score overlap between those terms and the file's **column names +
   dtypes + sheet names** (from the analyzer's schema digest — already computed, no new I/O).
3. Combine the embedding score, the existing Haiku relevance verdict, and this column-overlap
   score into the final top-K. Keep any file that scores high on *either* signal (recall-biased,
   because a missed file is unrecoverable downstream).

**Files (mechanism).**
- `skills/ds-star-plus/scripts/column_match.py` — pure-stdlib term/column overlap scorer, callable
  with just a question + schema digests (no solver state), so other skills can use it directly +
  `test_column_match.py`.
- `skills/ds-star-plus/references/retrieval.md` — add the column-level re-rank stage to the
  protocol.
- `skills/ds-star-plus/references/evidence.md §5` — update to describe the two-pass→three-signal
  design and the oracle-gap target it attacks.

**Files (integration — see matrix).**
- `skills/ds-conduct/SKILL.md` — peek stage calls `../ds-star-plus/scripts/column_match.py` to pick
  relevant files / route in multi-file cases (the `../` cross-ref pattern `ds-search` already uses).
- `skills/ds-clarify/references/clarify_checklist.md` — add "which files are in scope?" prompted by
  column-match candidates when files are ambiguous.
- `skills/ds-spike/SKILL.md` — select the retrieved file-set **once** before dispatch; all N solvers
  inherit the same scoped set (shared-spec rule).

**Effort:** small–medium. **Cost:** one extra Haiku call per retrieval (only fires when N>100
files). **Test:** unit-test the overlap scorer on synthetic schema digests; add a DABench/Krama-
style eval case where the embedding pass alone misses a column-obvious file.

**Done when:** `column_match.py` + tests pass in CI, retrieval.md documents the three-signal merge,
an eval case demonstrates a file recovered that embedding-only would miss, **and** the three
consumers above call the shared scorer (CI path-check confirms the `../` references resolve).

---

## Phase 2 — Memory that learns (ExpeL rules + ds-search experience store)

Two small, composable additions to the **existing** `ds-memory`, no new skill.

### 2a. ExpeL rule distillation (BUILD)

**Gap.** `ds-memory` stores concrete recipes; it never distills them into reusable *heuristics*
(ExpeL's core move: success/failure trajectories → task-level rules).

**What to build.** A new `distill` mode in `ds-memory`:
- Reads the recipe store, clusters by task signature, and asks Claude to extract a small set of
  **abstract rules** ("for revenue questions on transaction logs, always confirm cancellation
  handling first") into a separate `rules.jsonl`.
- At plan time, `ds-star-plus`/`ds-spike` retrieve matching *rules* alongside concrete recipes and
  pass them to the planner as guidance.
- Rules are advisory only — the verifier still gates everything (same cardinal rule as recipes).

**Files (mechanism).** `skills/ds-memory/SKILL.md` (add Mode 4 — Distill), `scripts/memory_store.py`
(`distill_rules()` + `retrieve_rules()`), `scripts/test_memory_store.py`,
`references/store_format.md` (rules schema), `references/evidence.md` (flip the ExpeL "partial"
note to "implemented").

**Files (integration — see matrix).**
- `skills/ds-clarify/references/clarify_checklist.md` — retrieved rules become checklist items
  ("last time a revenue question was ambiguous on cancellations — ask it now").
- `skills/ds-conduct/SKILL.md` — "assemble plan" stage calls `retrieve_rules()` and folds matches
  into the workflow plan + the questions it raises.
- `skills/ds-spike/references/personas.md` — rules seed each persona's assumption list (extends the
  existing minority-report seeding).
- `skills/ds-star-plus/SKILL.md` — planner retrieves rules alongside recipes at PLAN time.

**Effort:** small. **Cost:** the distill pass is a manual/periodic Claude call, not per-run; rule
retrieval is a cheap local store read shared by all consumers.

### 2b. ds-search dual-experience store (BUILD-small)

**Gap.** Empirical-MCTS keeps *both* success and failure memory to steer search; `ds-search` only
has the in-run anti-repeat list (failure side, ephemeral).

**What to build.** Wire `ds-search` to persist its explored-branch outcomes (which approaches
scored well / failed and why) into the **existing** `ds-memory` store, tagged as search
experience, so a later hard-task run seeds its tree from prior dead-ends and wins. No new store,
no new infra — reuse `memory_store.py`.

**Files (mechanism).** `skills/ds-search/SKILL.md` (record/seed hooks), `skills/ds-search/references/
evidence.md` (flip the dual-experience "partial" note), `skills/ds-memory/references/
store_format.md` (search-experience entry type).

**Files (integration — see matrix).**
- `skills/ds-conduct/SKILL.md` — when escalating a hard task to `ds-search`, pass prior
  search experience as seed.
- `skills/ds-spike/references/aggregation.md` — cross-pollinate search-experience with spike
  minority reports (both encode "what diverged and why").
- `skills/ds-star-plus/references/search_mode.md` — on escalation, seed the tree from the
  experience store.

**Effort:** small. **Cost:** negligible (writes only, gated on a search run).

**Phase 2 done when:** distill + rule-retrieval + search-experience round-trip are unit-tested,
CI green, the two `evidence.md` "partial/deferred" notes match reality, **and** every consumer in
the integration matrix is wired (clarify checklist, conduct plan-assembly, spike personas/
aggregation, star-plus planner/search-mode) with CI path-checks confirming the cross-references
resolve.

---

## Deferred — engineered hybrid-reward value model (I-MCTS, #3)

**Decision: keep prompt-level; do not engineer.** `ds-search` already instructs Claude to do a
cheap value estimate before paying for execution. A genuinely engineered value model (trained or
even a dedicated scoring sub-loop) multiplies calls and fights the cost thesis for a payoff only
realized on a hard tail we have not yet observed in practice.

**Gate to revisit:** a real workload where the hard tail is large enough that prompt-level search
demonstrably wastes budget. At that point, the cheapest Claude-native step is a dedicated Haiku
"branch promise" scorer with a calibration eval — still no trained model. Until then, the
`ds-search/references/evidence.md` honesty table is the correct representation.

## Skipped (recorded so they are not re-added)

- **#1 Voyager automatic curriculum.** Proposing progressively harder self-directed tasks is an
  open-ended self-improvement loop. A *kickoff* tool grows its library as a byproduct of
  user-driven runs; a curriculum serves no current user and re-bloats `ds-memory`. Permanent skip
  absent a concrete demand.
- **#6 Agent Alpha unified loop.** The generation/exploration/evaluation unification is an
  architecture framing already realized by `ds-search`'s loop + the rubric verifier. Keep it as a
  cited influence in `ds-search/references/evidence.md`; do not build a separate mechanism.

---

## Cross-skill integration matrix (part of "done")

Each BUILD mechanism is a shared utility. This is where it must plug in — ✅ wire it, — = not
applicable:

| consumer | Column retrieval (P1) | Rule distillation (P2a) | Search-experience (P2b) |
|---|---|---|---|
| **`ds-conduct`** (orchestrator) | ✅ peek stage uses column-match to pick relevant files in multi-file/data-lake cases and route accordingly | ✅ "assemble plan" stage retrieves matching rules → folds them into the workflow plan and the questions it raises | ✅ when it escalates a hard task to `ds-search`, passes prior search experience |
| **`ds-clarify`** (spec) | ✅ when files are ambiguous, surfaces column-match candidates as "which files are in scope?" | ✅ distilled rules become *clarify checklist items* — "last time this was ambiguous, ask it now" | — |
| **`ds-spike`** (ensemble) | ✅ select the retrieved file-set **once** before dispatch so all N solvers solve the *same* scoped problem (ties to the shared-spec rule) | ✅ rules seed each persona's assumption list (extends the existing minority-report seeding) | ✅ search-experience ↔ spike minority reports cross-pollinate (both encode "what diverged") |
| **`ds-star-plus`** (solver) | ✅ native home (Phase 1) | ✅ planner retrieves rules alongside recipes | ✅ on escalation to search mode, seed the tree from experience |
| **`data-profile`** | ✅ reuses/produces the schema digests column-match scores against | — | — |

**Design rule that makes this work:** the mechanism lives in **one** place and is *called*, never
copy-pasted. Concretely:
- `column_match.py` is a standalone scorer (stdlib, no solver state) so `ds-conduct`, `ds-clarify`,
  and `ds-spike` can all call it directly — not only through a full `ds-star-plus` run.
- `memory_store.py` gains `distill_rules()` / `retrieve_rules()` and a search-experience entry
  type, so every consumer reads the same store with the same gating rule.

## Suggested execution order

1. **Phase 1** (column-level retrieval) — independent, measured payoff, smallest blast radius.
2. **Phase 2a** (ExpeL distillation) — independent of Phase 1.
3. **Phase 2b** (ds-search experience store) — after 2a (reuses the store plumbing it touches).

Each phase is a self-contained PR with its own tests; none requires the DEFER/SKIP items. After
each phase, update `docs/STATUS.md` and the relevant `evidence.md` so docs keep matching reality.
