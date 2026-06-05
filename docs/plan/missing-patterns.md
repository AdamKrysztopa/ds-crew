# Implementation plan — the missing literature patterns

**Branch:** `plan/missing-patterns` · **Status:** plan only, nothing implemented yet.

This plans the six pattern gaps surfaced by the citation/pattern audit — techniques that are in
`papers/` and named in the ROADMAP but **not fully built**. Each is judged against the three
standing principles, *not* "build everything":

- **P0 — Claude-native, and language-agnostic at the seam that matters.** No trained models, no
  external agent frameworks. A "value model" or "re-ranker" here means a *Claude call with a focused
  prompt*, never a fine-tuned artifact. **These are Claude *skills* — prose protocols first.** The
  line we draw (decided 2026-06-05): **never make the *user's analysis* depend on our language.** A
  data scientist may work in R, Julia, JS, SQL, or Rust; a helper their *own* code must call would
  impose Python on them — not allowed. But Claude's **internal bookkeeping** (a cross-session store
  the user never sees) may be a **language-neutral data format (JSONL) with an *optional* helper** —
  that imposes nothing on the user's analysis. Two consequences for this plan:
    - **Judgment is always prose.** Column/value matching, ranking, and rule distillation are
      Claude reasoning in a reference doc — never a hand-tuned scoring script with magic weights.
      So Phase 1's column re-rank is prose (no `column_match.py`), full stop.
    - **Internal state is a neutral format, code optional.** Phase 2's rules/search-experience store
      is a documented **JSONL schema**; the existing `memory_store.py` is fine *as-is* (internal
      plumbing, not debt) and need not grow — the new behaviour is prose, and any helper stays an
      optional convenience, never required and never on the user's critical path.
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

### Scientific-grounding audit (completed 2026-06-04 against `papers/`)

A corpus audit initially found three cited papers missing from `papers/`; **all three have since
been fetched from arXiv and content-verified.** Every load-bearing claim now checks out against a
real local PDF:

| Paper | Cited by | Verified claim |
|---|---|---|
| **DS-STAR** ([2509.21825](https://arxiv.org/abs/2509.21825)) | **Phase 1** | Table 2: 44.69 retrieval vs 52.55 oracle; "+8 percentage points" under ideal retrieval; "advanced data discovery is a promising direction" ✅ |
| **KramaBench** ([2506.06541](https://arxiv.org/abs/2506.06541)) | **Phase 1** (scale) | Astronomy = 1,556 files (data-lake scale). Its *own* "oracle" (Table 7) is input-obfuscation — a **different** setting, do not conflate ✅ |
| **ExpeL** ([2308.10144](https://arxiv.org/abs/2308.10144)) | **Phase 2a** | Extracts "natural-language **insights**" from cross-task **success+failure** trajectories, recalled at inference. NB: ExpeL says "insights," not "rules" — our "rule distillation" is a faithful reframing, label it as such ✅ |
| **Empirical-MCTS** ([2602.04248](https://arxiv.org/abs/2602.04248)) | **Phase 2b** | "unifies two distinct types of experience via a dual-loop mechanism" — **short-term (intra-search) / long-term (cross-task)**, not "success/failure" ✅ |
| **AWM** ([2409.07429](https://arxiv.org/abs/2409.07429)) | `ds-memory/scripts/memory_store.py` | "Agent Workflow Memory" — induce/reuse workflows from experience ✅ |
| **I-MCTS** ([2502.14693](https://arxiv.org/abs/2502.14693)) | DEFER #3 | "hybrid reward mechanism" + "LLM-based value model M_value" — confirms DEFER reasoning ✅ |
| **Agent Alpha** ([2602.02995](https://arxiv.org/abs/2602.02995)) | SKIP #6 | "a unified framework that synergizes generation, exploration, and evaluation" ✅ |
| **Voyager** ([2305.16291](https://arxiv.org/abs/2305.16291)) | SKIP #1 | "automatic curriculum that maximizes exploration" + ever-growing "skill library" — the open-ended self-improvement loop the SKIP rejects ✅ |

**Two citation corrections folded into this plan (above):** Phase 1's numbers are **DS-STAR Table 2,
not "KramaBench Table 2"**; Phase 2b's dual experience is **short/long-term, not success/failure**.
**One labelling rule for Phase 2a:** present distilled heuristics as "rules (ExpeL's *natural-language
insights*)" so the protocol never misquotes the paper.

---

## Phase 1 — Column-level retrieval (the one with measured payoff)

**Why first.** This is the only gap with a *quantified* benefit in the literature the repo
already cites. **Citation correctness (verified against `papers/`):** the numbers live in the
**DS-STAR paper ([2509.21825](https://arxiv.org/abs/2509.21825)), Table 2** — DS-STAR scores
**44.69 with retrieval vs 52.55 in the relevant-files oracle setting**, and the paper states
accuracy "increases by **8 percentage points**" under ideal retrieval, a gap caused purely by
retrieval misses. **KramaBench ([2506.06541](https://arxiv.org/abs/2506.06541)) is the benchmark
and the source of the data-lake scale** (Astronomy = **1,556 files**); its *own* "oracle" (Krama
Table 7) is a **different**, input-obfuscation setting and must **not** be conflated with the
retrieval-oracle. The current `ds-star-plus/references/evidence.md §5` and `retrieval.md` say
"KramaBench Table 2" — that mis-attribution is a Phase-1 fix (Task: docs). Pure embedding cosine
misses files that are obviously on-topic by **column name / dtype** but embed poorly against the
query phrasing. Closing this improves correctness on multi-file / data-lake tasks, which is exactly
where the suite claims to help.

**What to build (Claude-native).** A second, cheap re-rank stage layered onto the existing Haiku
relevance pass — *not* a learned re-ranker:
1. From the user's question, extract candidate entities/metrics (Haiku).
2. For each candidate file, score overlap between those terms and the file's **column names +
   dtypes + sheet names** (from the schema digest the file-profiling step already produced, in
   whatever language it ran — already computed, no new I/O).
3. Combine the embedding score, the existing Haiku relevance verdict, and this column-overlap
   score into the final top-K. Keep any file that scores high on *either* signal (recall-biased,
   because a missed file is unrecoverable downstream).

**Files (mechanism — prose, no script).** The mechanism is the **protocol**, not code. The shared
"primitive" the consumers point to is `retrieval.md` itself (the `../` cross-ref pattern, but to a
reference doc rather than a script).
- `skills/ds-star-plus/references/retrieval.md` — sharpen the existing Stage 3 into an *operational*
  protocol: the Haiku pass that already extracts query entities now also emits, per surviving file,
  the three structural judgments (column-name overlap, value containment, join-key reachability) and
  the explicit **recall-biased keep rule** ("keep any file strong on *either* embedding *or*
  structure — a missed file is unrecoverable downstream"). It scores against the **schema digest the
  file-profiling step already produced** (whatever language that step ran in); no new I/O, no Python
  dependency.
- `skills/ds-star-plus/references/evidence.md §5` — fix the mis-citation (DS-STAR Table 2, not
  KramaBench Table 2; Krama's oracle is a *different* setting) and describe the two-pass→three-signal
  design and the oracle-gap target it attacks.
- `skills/ds-star-plus/references/worked_example.md` — add the recovery example (below) inline,
  since there is no unit test to carry it.

**Files (integration — see matrix).** Consumers reference the shared protocol doc, not a script:
- `skills/ds-conduct/SKILL.md` — peek stage applies the Stage 3 judgment per
  `../ds-star-plus/references/retrieval.md` to pick relevant files / route in multi-file cases.
- `skills/ds-clarify/references/clarify_checklist.md` — add "which files are in scope?" surfaced by
  the Stage 3 column/value candidates when files are ambiguous.
- `skills/ds-spike/SKILL.md` — select the retrieved file-set **once** before dispatch (per the same
  protocol); all N solvers inherit the same scoped set (shared-spec rule).

**Effort:** small (prose only). **Cost:** the structural judgments fold into the **existing** Haiku
relevance pass — no new call. **Verification (no script):** a documented worked example where the
embedding pass alone misses a column-obvious file and the Stage 3 rule recovers it; CI path-check
confirms every `../ds-star-plus/references/retrieval.md` cross-ref resolves.

**Done when:** retrieval.md Stage 3 is an operational protocol with the recall-bias keep rule,
evidence.md §5 is correctly attributed and describes the three signals, the worked example shows a
column-obvious recovery, **and** the three consumers reference the shared protocol doc (CI
path-check green; `check_skill_paths.py` confirms the `../` references resolve).

---

## Phase 2 — Memory that learns (ExpeL rules + ds-search experience store)

Two small, composable additions to the **existing** `ds-memory`, no new skill.

### 2a. ExpeL rule distillation (BUILD)

**Gap.** `ds-memory` stores concrete recipes; it never distills them into reusable *heuristics*
(ExpeL's core move: cross-task **success+failure** trajectories → reusable **natural-language
insights**, which we surface as task-level *rules* — "rules" is our label for ExpeL's "insights").

**What to build.** A new `distill` mode in `ds-memory`:
- Reads the recipe store, clusters by task signature, and asks Claude to extract a small set of
  **abstract rules** ("for revenue questions on transaction logs, always confirm cancellation
  handling first") into a separate `rules.jsonl`.
- At plan time, `ds-star-plus`/`ds-spike` retrieve matching *rules* alongside concrete recipes and
  pass them to the planner as guidance.
- Rules are advisory only — the verifier still gates everything (same cardinal rule as recipes).

**Files (mechanism — prose + JSONL, no code).** Per the P0 corollary, both the distillation *and*
the retrieval are **prose protocols**; the only artifact is a language-neutral data file:
- `skills/ds-memory/SKILL.md` — add **Mode 4 (Distill)** as a prose protocol: read the recipe store,
  group by task signature, ask Claude to extract a small set of abstract **rules** (our label for
  ExpeL's "natural-language insights") into `rules.jsonl`. **Retrieval is also prose** ("at plan
  time, read `rules.jsonl`; keep rules whose task signature overlaps the current task; pass as
  advisory guidance"). No clustering algorithm, no `retrieve_rules()` — Claude does both in the
  user's own environment.
- `skills/ds-memory/references/store_format.md` — `rules.jsonl` entry schema (language-neutral JSON).
- `skills/ds-memory/references/evidence.md` — flip the ExpeL "partial" note to "implemented" (PDF now
  in `papers/`, claim verified).
- **No change to `memory_store.py`** — the existing recipe store is grandfathered for the separate
  minimization audit; new work adds none of its own code.

**Files (integration — see matrix).**
- `skills/ds-clarify/references/clarify_checklist.md` — retrieved rules become checklist items
  ("last time a revenue question was ambiguous on cancellations — ask it now").
- `skills/ds-conduct/SKILL.md` — "assemble plan" stage reads the rules store (per `store_format.md`)
  and folds matches into the workflow plan + the questions it raises.
- `skills/ds-spike/references/personas.md` — rules seed each persona's assumption list (extends the
  existing minority-report seeding).
- `skills/ds-star-plus/SKILL.md` — planner retrieves rules alongside recipes at PLAN time.

**Effort:** small. **Cost:** the distill pass is a manual/periodic Claude call, not per-run; rule
retrieval is a cheap local store read shared by all consumers.

### 2b. ds-search dual-experience store (BUILD-small)

**Gap.** Empirical-MCTS ([2602.04248](https://arxiv.org/abs/2602.04248)) "unifies two distinct
types of experience via a dual-loop mechanism" — **short-term (intra-search)** and **long-term
(cross-task)** experience accumulation (verified against `papers/`; note the paper frames it as
short/long-term, *not* literally "success/failure"). `ds-search` today has only the in-run
anti-repeat list — the short-term side, and ephemeral. The missing piece is the **long-term,
cross-run** loop: persist explored-branch outcomes (which approaches scored well / failed and why)
so a later run seeds its tree from prior wins and dead-ends.

**What to build.** Wire `ds-search` to persist its explored-branch outcomes (which approaches
scored well / failed and why) into the **same language-neutral JSONL store**, tagged as search
experience, so a later hard-task run seeds its tree from prior dead-ends and wins. No new store,
no new infra, **no new code** — a new entry type plus prose record/seed protocols.

**Files (mechanism — prose + JSONL, no code).** `skills/ds-search/SKILL.md` (record/seed steps
described as prose: append a search-experience JSON line after each branch verdict; at the start of
a hard run, read prior entries and seed the tree), `skills/ds-search/references/evidence.md` (flip
the dual-experience "partial" note), `skills/ds-memory/references/store_format.md` (search-experience
entry schema). No changes to `memory_store.py`.

**Files (integration — see matrix).**
- `skills/ds-conduct/SKILL.md` — when escalating a hard task to `ds-search`, pass prior
  search experience as seed.
- `skills/ds-spike/references/aggregation.md` — cross-pollinate search-experience with spike
  minority reports (both encode "what diverged and why").
- `skills/ds-star-plus/references/search_mode.md` — on escalation, seed the tree from the
  experience store.

**Effort:** small. **Cost:** negligible (writes only, gated on a search run).

**Phase 2 done when:** Mode 4 (Distill) and the rule/search-experience retrieval are documented as
prose protocols, `store_format.md` specifies the `rules.jsonl` and search-experience schemas, a
worked example shows a distilled rule and a seeded search round-trip, the two `evidence.md`
"partial/deferred" notes match reality, **and** every consumer in the integration matrix is wired
(clarify checklist, conduct plan-assembly, spike personas/aggregation, star-plus planner/search-mode)
with CI path-checks confirming the cross-references resolve. **No new test files** — there is no new
code; correctness is shown by the worked examples and the path-check, not unittest.

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

**Design rule that makes this work:** the mechanism lives in **one** place and is *referenced*,
never copy-pasted — and (P0) judgment is prose while internal state is a neutral format. Concretely:
- **Phase 1 (judgment → prose):** `retrieval.md` Stage 3 is the single shared protocol;
  `ds-conduct`, `ds-clarify`, and `ds-spike` point to it via `../ds-star-plus/references/retrieval.md`
  rather than re-describing the matching rules. No `column_match.py`.
- **Phase 2 (prose + neutral JSONL):** the shared artifacts are the `rules.jsonl` / search-experience
  **schemas** in `store_format.md`; distillation, retrieval, record, and seed are **prose protocols**.
  The existing `memory_store.py` stays as optional internal plumbing — neither extended nor removed
  by this plan — and nothing on the user's analysis path depends on it.

The `../` cross-references all resolve to **reference docs**, so `check_skill_paths.py` still
enforces the integration the same way it would for a script.

## Suggested execution order

1. **Phase 1** (column-level retrieval) — independent, measured payoff, smallest blast radius.
2. **Phase 2a** (ExpeL distillation) — independent of Phase 1.
3. **Phase 2b** (ds-search experience store) — after 2a (reuses the store plumbing it touches).

Each phase is a self-contained PR of **prose + JSONL schema only** — no new code, no new tests;
correctness is shown by worked examples and the CI path-check. None requires the DEFER/SKIP items.
After each phase, update `docs/STATUS.md` and the relevant `evidence.md` so docs keep matching
reality.

## Follow-up (separate): audit the *existing* scripts against the P0 line

Under Philosophy B the test for each existing helper is **not** "is it Python?" but **"does the
*user's analysis* have to call it?"** A separate audit should triage the current scripts
(`memory_store.py`, `verify_schema.py`, `analyze_file.py`, `kernel_runner.py`, `route_model.py`,
`run_manifest.py`, `aggregate.py`, `runlog.py`, …) into:
- **On the user's analysis path → make it prose / language-neutral.** Anything the user's own code
  must invoke, or that does *judgment* (matching, parsing a verdict, ranking) belongs as a protocol,
  not an imported module. Candidate: `analyze_file.py` (profiling the user's data) is better stated
  as "produce this digest, in your project's language."
- **Pure internal plumbing → keep as optional convenience.** A cross-session store the user never
  sees (`memory_store.py`) imposes nothing on their analysis; fine to keep, clearly labelled
  optional, with the JSONL format as the real contract.

**This plan neither extends nor removes those scripts** — it just adds prose + JSONL. The audit is
its own effort with its own CI/test implications, recorded so the line is applied consistently next.
