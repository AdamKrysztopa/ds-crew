# Why tree-search the hard tail — evidence

`ds-search` is the *intra-agent* search escalation: when greedy refinement (the default
`ds-star-plus` loop) keeps failing on one hard task, explore a tree of alternative solution
paths instead of one path. Four papers ground the design; the full operational protocol lives in
`../ds-star-plus/references/search_mode.md`.

## 1. Tree search beats greedy on hard agentic tasks

**SWE-Search** — Antoniades, Örwall et al. (ICLR 2025), arXiv:[2410.20285](https://arxiv.org/abs/2410.20285).
Shows MCTS + iterative self-refinement transfers to *code-writing* agents — the closest precedent
for adding search to a code-generating data-science agent. Establishes that the explore-then-
evaluate pattern, not just chat-style reflection, is what moves the needle on hard tasks.

## 2. Introspective expansion + hybrid reward

**I-MCTS** — Liang et al. (Ant Group / Rutgers, 2025), arXiv:[2502.14693](https://arxiv.org/abs/2502.14693).
Two ideas `ds-search` adopts:
- **Introspective node expansion** — generate the next candidate by reflecting on the
  solutions+scores of *sibling* attempts, not just the parent ("here's what the neighbours tried;
  do better").
- **Hybrid reward** — an LLM value-model *estimates* a branch's promise before paying for a full
  execution rollout, then blends toward the real verifier score. This is what keeps search
  affordable: most candidate branches are pruned on a cheap estimate before execution.

## 3. Unified generation / exploration / evaluation

**Agent Alpha** — Tang, Chen et al. (GWU, 2026), arXiv:[2602.02995](https://arxiv.org/abs/2602.02995).
Unifies generation, exploration, and evaluation in one tree-search loop — the reference
architecture for a single search-mode pass that proposes, explores, and scores without separate
orchestration stages.

## 4. Dual-experience memory to steer search

**Empirical-MCTS** — Lu et al. (2026), arXiv:[2602.04248](https://arxiv.org/abs/2602.04248).
"Unifies two distinct types of experience via a dual-loop mechanism" — **short-term (intra-search)**
and **long-term (cross-task)** experience accumulation (verified against
`papers/empirical-mcts-2602.04248.pdf`; the paper frames it as short/long-term, *not* literally
"success/failure"). `ds-search` now implements **both** halves: the in-run **anti-repeat list** is
the short-term side (`SKILL.md §3`), and a persistent **search-experience store**
(`search_experience.jsonl`, schema in `../ds-memory/references/store_format.md`) is the long-term
side — recorded at end-of-search, read to seed the tree of a later hard-task run toward prior wins
and away from dead-ends.

## Implementation depth — read this honestly

`ds-search` is **prompt-level guidance, not engineered search infrastructure.** It directs Claude
to run the I-MCTS/SWE-Search pattern within a single skill invocation; it does **not** ship a
trained value-model or a UCT scheduler as code. The dual-experience memory, however, *is* now
realized — as a language-neutral JSONL store plus prose record/seed protocols, not bundled code.
Specifically:

| paper mechanism | in ds-search | gap |
|---|---|---|
| introspective expansion (I-MCTS) | ✅ prompt instruction | — |
| hybrid reward: value estimate → real verifier (I-MCTS) | 🟡 described | no trained value-model; the "estimate" is an LLM judgement (DEFER — see plan) |
| dual short/long-term experience (Empirical-MCTS) | ✅ implemented | short-term = anti-repeat list; long-term = `search_experience.jsonl` store (prose + JSONL, no engine) |
| unified gen/explore/eval loop (Agent Alpha) | 🟡 referenced | architecture, not a distinct engineered loop (SKIP — already covered) |

The remaining 🟡 rows are deliberate and consistent with the suite's cost thesis (search multiplies
LLM calls); the hybrid-reward value-model is a DEFER and the unified loop a SKIP in
`docs/plan/missing-patterns.md`. The long-term experience store closes the one row that was a real
gap, without shipping a search *engine*.

## The verifier-as-reward caveat

`ds-search` scores candidate branches with the same rubric verifier the solvers use internally,
so a biased judge is amplified. The mitigation (run the scoring on a separate model instance /
tier) is in `SKILL.md` under "Verifier-as-reward circularity".
