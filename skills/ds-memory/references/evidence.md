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
ExpeL collects cross-task **success *and* failure** trajectories and distills natural-language
**insights** (abstract heuristics), not just concrete examples; at inference it recalls those
insights alongside its successful exemplars. (Verified against `papers/expel-2308.10144.pdf`: the
paper's term is "insights", which we surface as "rules"; it derives them from both successes and
failures.)

> **Implemented — Mode 4 (Distill).** The cross-task *rule distillation* half of ExpeL is built:
> `ds-memory` Mode 4 clusters recipes by task signature and distills a small set of abstract
> **rules** (our label for ExpeL's "insights") into `rules.jsonl`, retrieved as advisory guidance
> alongside concrete recipes. It is **prose, not an algorithm** — Claude does the clustering and
> extraction; the JSONL schema (`references/store_format.md`) is the only artifact, so it imposes no
> language on the user. Rules are advisory; the verifier still gates every step. (Distillation is a
> *judgment* task — deliberately not a scoring function.)

## The honest caveat

Memory that is trusted blindly is worse than no memory: a stale or near-miss recipe seeds a
plausible-but-wrong plan. Hence the two hard rules in `SKILL.md` — **store only verified
recipes**, and **retrieval is a suggestion the verifier still gates**.
