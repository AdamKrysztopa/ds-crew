# Design — SOTA agentic data-science patterns (v1.2 tracks E–K)

**Date:** 2026-05-31
**Status:** design approved (brainstorming), pending implementation plan
**Scope:** close the gap between the current six-skill suite and the broader SOTA
landscape of agentic data-science patterns, on the **hybrid** delivery shape
(engine upgrades to `ds-star-plus` where natural + a small number of net-new
single-purpose skills).

> Continues the repo discipline: **every track is tied to a paper** and ships its
> **README / ROADMAP / ARCHITECTURE / bibliography** updates. PDFs stay gitignored
> and re-fetchable; only verified arXiv IDs may be written into `papers/README.md`.

---

## 1. Gap analysis (why these tracks)

The suite already covers: the iterative plan→implement→execute→verify→refine loop
(`ds-star`/`ds-star-plus`), rubric-decomposed LLM-as-judge verification
(DeepVerifier), cost-tiered model routing, self-consistency N-vote, intra-agent
MCTS search mode, multi-agent ensemble + blackboard reconciliation (`ds-spike`),
human-in-the-loop intent clarification (`ds-clarify`), two-stage data-lake
retrieval, and analyze-first profiling / EDA narrative (`data-profile`,
`eda-narrative`).

Patterns that are **missing or only partial**, each promoted to a track:

| Track | Missing pattern | Current state |
|------|------------------|---------------|
| **E** | Persistent **cross-session memory / skill library** | only *within-run* dual-experience (anti-repeat); nothing persists across tasks |
| **F** | **Stateful / notebook-native execution** | every round re-runs a whole script from scratch |
| **G** | **DAG planning + dynamic replan** | plan is linear and greedy (one step at a time) |
| **H** | Dedicated **AutoML / ML-modeling solution-tree** agent | ML answered ad-hoc inside the generic loop; no leaderboard / CV discipline |
| **I** | **Multi-agent debate / iterative critique** | `ds-spike` reconciliation is one-shot aggregation |
| **J** | **Safe sandboxed execution + provenance/lineage** | implicit; no run-manifest or isolation guarantees |
| **K** | **Data-aware orchestrator** (supervisor over the crew) | no entry-point that looks at data, grills, then conducts the right skills |

---

## 2. Delivery shape (hybrid — approved)

- **Engine upgrades to `ds-star-plus`** (benefit every downstream skill): **F**
  stateful kernel, **G** DAG planning, and **E**'s read/write hooks.
- **New single-purpose skills:** **H** `ds-model`, **K** `ds-conduct`, and the
  **E** `ds-memory` substrate (installable, but primarily a shared store).
- **Mode added to an existing skill:** **I** debate inside `ds-spike`.
- **Cross-cutting reference:** **J** sandbox/provenance, shared by all solvers.

---

## 3. Per-track design

### Track E — `ds-memory` (persistent skill/workflow library)

**Pattern.** Bank *verified* analysis recipes and workflows; retrieve them on new
tasks by data-shape / task signature. The cross-task analogue of the repo's
existing within-run dual-experience memory.

**Grounding.** Agent Workflow Memory `⚠2409.07429`, Voyager `⚠2305.16291`,
ExpeL `⚠2308.10144`; extends Empirical-MCTS (`2602.04248`, already in repo).

**Delivery.**
- New skill dir `skills/ds-memory/` — `SKILL.md`, `references/store_format.md`,
  `scripts/memory_store.py` (+ `test_memory_store.py`).
- **Store format:** append-only JSONL of entries
  `{task_signature, data_fingerprint, plan, verified_code_snippet, verifier_score,
  assumptions, outcome, timestamp}`. Keyed/retrieved by `(task_signature,
  data_fingerprint)` similarity.
- **Hooks (non-invasive, opt-in):** `ds-star-plus` reads matching recipes at plan
  time (seed the planner) and writes back on a clean verifier verdict; `ds-spike`
  may seed personas from past minority reports. Hooks are guarded by a flag so the
  solvers still run with an empty/absent store.

**Interface.** `memory_store.py` exposes `retrieve(signature, fingerprint, k)` and
`record(entry)`; pure functions over a file path, unit-testable with a temp store.

**Effort.** Medium. **Deps.** none (foundational). **Risk.** low — additive, flag-gated.

### Track F — stateful kernel execution (`ds-star-plus` engine upgrade)

**Pattern.** Maintain a persistent IPython/Jupyter kernel; each step executes
incrementally against retained variables instead of re-running a full script.
Cheaper, fewer reload bugs, closer to how a human notebook works.

**Grounding.** CodeAct — *Executable Code Actions Elicit Better LLM Agents*
`⚠2402.01030`.

**Delivery.**
- `skills/ds-star-plus/references/execution.md` — kernel-vs-script policy, state
  hygiene, when to reset.
- `skills/ds-star-plus/scripts/kernel_runner.py` (+ test) — start kernel, exec a
  cell, capture stdout/err/result, timeout, kill. **Script-mode fallback** preserved
  (kernel optional; default can stay script for paper-faithfulness, kernel opt-in).
- `SKILL.md` EXECUTE stage updated to describe both modes.

**Effort.** Medium. **Deps.** J (run inside the sandbox). **Risk.** medium — stateful
execution can mask non-reproducibility; mitigated by a "final clean re-run" guard
before FINALIZE and by provenance (J).

### Track G — DAG planning + dynamic replan (`ds-star-plus` engine upgrade)

**Pattern.** Represent the plan as a task **graph** (nodes = sub-tasks, edges =
data deps) with node-level verification and dynamic re-wiring on failure, rather
than a strictly linear append/backtrack.

**Grounding.** MetaGPT **Data Interpreter** `⚠2402.18679`.

**Delivery.**
- `skills/ds-star-plus/references/planning_graph.md` — graph representation,
  node-level verify, replan rules, how it generalizes the current linear plan
  (linear plan = degenerate chain).
- `SKILL.md` PLAN/ROUTE stages updated; ties into the existing oscillation/branch
  logic and the search_mode (DAG is the substrate MCTS searches over).

**Effort.** Medium–large. **Deps.** benefits from F. **Risk.** medium — must not
regress the simple-task fast path; keep linear chain as default, escalate to graph
on multi-file / multi-output tasks.

### Track H — `ds-model` (AutoML solution-tree skill)

**Pattern.** Dedicated modeling loop: draft → train → evaluate on a held-out
metric → improve, as a **solution tree** with empirical leaderboard feedback, plus
explicit CV / leakage / target-definition discipline.

**Grounding.** AIDE `⚠2502.13138`, AutoKaggle `⚠2410.20424`,
AutoML-Agent `⚠2410.02958`.

**Delivery.**
- New skill dir `skills/ds-model/` — `SKILL.md`,
  `references/{solution_tree,leakage_cv,evidence}.md`,
  `scripts/leaderboard.py` (+ test) tracking candidate metrics, `evals/evals.json`.
- Reuses `ds-star-plus` execution (kernel) + verifier; differs in objective
  (predictive metric, not factoid sufficiency) and in tree-of-drafts search.

**Effort.** Large. **Deps.** F (execution), optionally E (recall good model
families), G (pipeline as DAG). **Risk.** medium — must enforce leakage/CV checks
or it produces optimistic garbage; that discipline is the skill's core value.

### Track I — debate mode in `ds-spike`

**Pattern.** Optional cross-critique: after the parallel solvers post to the
blackboard, run ≤2 debate rounds where each solver sees peers' answers+rationales
and may revise, *before* the aggregator reconciles. Sharpens disagreement into
either consensus or a crisp minority report.

**Grounding.** Multi-agent debate, Du et al. `⚠2305.14325`.

**Delivery.**
- `skills/ds-spike/references/debate.md` — debate protocol, round cap, anti-herding
  guard (debate can amplify a confident-wrong majority — keep the minority report).
- `skills/ds-spike/scripts/aggregate.py` extended (+ tests) to consume post-debate
  states. **Opt-in flag**; default `ds-spike` stays one-shot.

**Effort.** Medium. **Deps.** none (sits on existing `ds-spike`). **Risk.** medium —
debate can reduce diversity; mitigated by cap + preserved minority report.

### Track J — sandbox + provenance (cross-cutting reference)

**Pattern.** Every solver runs code in a constrained sandbox and emits a
**run manifest** (inputs, code hash, env, outputs, verifier verdict) for
reproducibility and audit.

**Grounding.** Execution-environment practice from DA-Code (`2410.07331`) and
DABstep (`2506.23719`, both in repo) + CodeAct `⚠2402.01030`.

**Delivery.**
- Shared `references/sandbox.md` (authored once, referenced by `ds-star`,
  `ds-star-plus`, `ds-model`, `ds-spike`) — resource/timeout/network policy, temp
  workdir discipline.
- Lightweight provenance emitter (a `run_manifest.json` written per run); a helper
  in `ds-star-plus/scripts/` (+ test).

**Effort.** Small–medium. **Deps.** none (foundational). **Risk.** low.

### Track K — `ds-conduct` (data-aware orchestrator) — capstone

**Pattern.** Supervisor / control-agent that turns one fuzzy request + a dataset
into a conducted crew workflow.

**Grounding.** Blackboard control-agent (`2510.01285`, in repo) + supervisor
pattern, MetaGPT `⚠2308.00352`.

**Flow.**
1. **Peek** — fast, read-only structural scan (reuses `data-profile`'s analyzer in
   a quick mode: shapes, dtypes, timestamp/geo/id detection, candidate keys,
   file relationships). Cheap.
2. **Grill, data-aware** — asks questions *triggered by what it saw*, extending the
   `ds-clarify` checklist with **data-pattern triggers** (e.g. timestamp →
   "time-series? panel? horizon?"; shared key across files → "join intended?";
   target-shaped column → "predictive task → route to `ds-model`?").
3. **Assemble plan** — converts answers into a concrete crew workflow + spike plan:
   which skills in what order, `ds-spike` N and personas, whether `ds-model` runs,
   and the `analysis-spec.md` contract (delegates to `ds-clarify`'s template).
4. **Confirm → execute with checkpoints** — shows the plan; on approval runs it,
   surfacing each handoff (the blackboard control-agent role).

**Delivery.**
- New skill dir `skills/ds-conduct/` — `SKILL.md`,
  `references/{trigger_catalog,workflow_plan_template,evidence}.md`. Trigger catalog
  = data-pattern → question → candidate skill mapping. No heavy new scripts; it
  orchestrates existing skills via the dispatching-parallel-agents machinery.

**Effort.** Medium–large (mostly orchestration + the trigger catalog). **Deps.**
`data-profile`, `ds-clarify`, `ds-spike` (+I), benefits from E. **Risk.** medium —
scope creep; keep it a *conductor*, not a re-implementation of the skills it calls.

---

## 4. Sequencing (dependency-ordered)

```
J (sandbox)──┐
F (kernel)───┼─► G (DAG) ──► H (ds-model) ─┐
E (memory)───┘                              ├─► K (ds-conduct)  ← capstone
I (debate, independent) ────────────────────┘
```

Recommended build order: **J → F → G → E → H → I → K**.
- J first: safety/provenance underpins everything, lowest risk.
- F before G: the graph executes against kernel state.
- E lands as soon as a clean verdict exists to record (after F/G stabilize).
- H needs F (and ideally G/E).
- I is independent — can slot anytime.
- K is last: it conducts all the above.

Each track is **its own commit/checkpoint** with its own docs delta, so the suite
is shippable after any track.

---

## 5. Cross-cutting docs & manifest updates (every track contributes)

- **README.md** — "six skills" → eight user-facing (+`ds-model`, `ds-conduct`;
  `ds-memory` as substrate). Update skill table, `/`-command list, "typical flow"
  now led by `ds-conduct`, and the repo-layout tree.
- **ROADMAP.md** — add Tracks E–K with rationale + status legend; update the
  "suggested order" and dependency graph.
- **ARCHITECTURE.md** — new rows (kernel execution, DAG plan, debate); regenerate
  `architecture-comparison.svg` via `make_diagram.py`.
- **papers/README.md** — new **"Patterns added in v1.2"** bibliography block + the
  re-fetch `curl` list, **only with verified arXiv IDs**.
- **`.claude-plugin/plugin.json` + `marketplace.json`** — register new skills, bump
  to **v1.2.0**; sync `package.json` version.
- **Evals/tests** — each new script ships a `unittest` per repo convention
  (`python3 -m unittest` in its `scripts/` dir).

---

## 6. Citation verification gate (hard requirement)

Before any `⚠to-verify` arXiv ID is written into `papers/README.md`, the
implementation plan MUST include a step that fetches each ID and confirms title +
authors match the claimed paper. Any ID that cannot be confirmed is either
corrected or the citation is dropped — the repo never ships an unverified
reference.

`⚠to-verify` IDs: 2409.07429 (AWM), 2305.16291 (Voyager), 2308.10144 (ExpeL),
2402.01030 (CodeAct), 2402.18679 (Data Interpreter), 2502.13138 (AIDE),
2410.20424 (AutoKaggle), 2410.02958 (AutoML-Agent), 2305.14325 (multi-agent
debate), 2308.00352 (MetaGPT).

---

## 7. Out of scope (YAGNI)

- BI/dashboard generation, agentic SQL warehouse connectors, active-learning data
  acquisition — noted but not planned here.
- Retraining / fine-tuning any model (all patterns are inference-time).
- Replacing the linear plan or script execution as *defaults* — F and G are
  opt-in/escalation paths so the paper-faithful baseline is preserved.

---

## 8. Open decisions for the plan phase

1. Is `ds-memory` user-invocable (`/ds-memory` to inspect/prune the store) or
   purely a substrate other skills call? (Leaning: both — a thin inspect command.)
2. Default kernel vs script in `ds-star-plus` (leaning: script default, kernel
   opt-in, to keep paper-faithfulness and reproducibility guarantees).
3. `ds-conduct` autonomy after approval: full auto-run vs checkpoint at each
   handoff (leaning: checkpoint at each handoff, matching the human-in-the-loop
   ethos).
