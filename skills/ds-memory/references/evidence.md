# Why a persistent recipe store — evidence

`ds-memory` composes three lines of work on agent memory. The store itself is deliberately
simple (append-only JSONL, similarity retrieval, verifier-gated reuse); the papers justify
*why* that shape is the right floor and mark where it stops.

## 1. Workflow memory — induce reusable workflows from past episodes

**Agent Workflow Memory (AWM)** — Wang et al. (CMU, 2024), arXiv:[2409.07429](https://arxiv.org/abs/2409.07429).
AWM induces reusable *workflow* snippets from past trajectories and retrieves them at inference
time, improving success and efficiency on web tasks. This is the core `ds-memory` pattern: a
verified `ds-star-plus` run is banked as a recipe (plan + code + assumptions + outcome) and
retrieved by task signature on a similar future task. Retrieval seeds the planner; it never
bypasses the verifier.

## 2. Skill library — grow a versioned library via self-verification

**Voyager** — Wang et al. (NVIDIA / Caltech, 2023), arXiv:[2305.16291](https://arxiv.org/abs/2305.16291).
Voyager grows an ever-expanding, *versioned* library of verified skills, indexed for retrieval
and reused as building blocks. `ds-memory` adopts the library-of-verified-artifacts idea — only
`verifier_score == 4` recipes are stored, so the library stays trustworthy.

> **Not yet implemented (deliberate):** Voyager's *automatic curriculum* — proposing
> progressively harder tasks to drive library growth — is out of scope. `ds-memory` grows its
> library as a byproduct of user-driven runs, not via a self-directed curriculum. See ROADMAP.

## 3. Experience distillation — turn trajectories into rules

**ExpeL** — Zhao et al. (2023), arXiv:[2308.10144](https://arxiv.org/abs/2308.10144).
ExpeL collects success/failure trajectories and distills task-level *rules* (abstract heuristics),
not just concrete examples. `ds-memory` currently stores concrete recipes and the minority-report
assumptions that seed `ds-spike`.

> **Partial (deliberate):** the abstract cross-task *rule distillation* half of ExpeL — turning
> many recipes into a small set of reusable heuristics — is not built. Recipes are concrete, not
> distilled. Recorded as a ROADMAP item.

## The honest caveat

Memory that is trusted blindly is worse than no memory: a stale or near-miss recipe seeds a
plausible-but-wrong plan. Hence the two hard rules in `SKILL.md` — **store only verified
recipes**, and **retrieval is a suggestion the verifier still gates**.
