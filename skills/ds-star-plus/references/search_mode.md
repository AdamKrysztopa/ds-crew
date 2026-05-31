# Optional MCTS search mode (A2) — for the hard tail only

DS-STAR refines **greedily**: one sampled next step per round, execute, re-judge. v2 already
branches to 2–3 candidates on oscillation. Search mode generalizes that into a small Monte Carlo
Tree Search over **plan states** — explore several continuations, score them, expand the most
promising — instead of committing to one greedy path. Grounded in I-MCTS
([2502.14693](https://arxiv.org/abs/2502.14693)), SWE-Search
([2410.20285](https://arxiv.org/abs/2410.20285)), Empirical-MCTS
([2602.04248](https://arxiv.org/abs/2602.04248)), Agent-Alpha
([2602.02995](https://arxiv.org/abs/2602.02995)).

## When to enable (the cost gate)

**Off by default.** MCTS multiplies LLM calls — it fights the cost-hardening that defines
`ds-star-plus`. Enable it only for the hard tail where DS-STAR's own data shows more compute pays
(Fig 4b; hard tasks average 5.6 rounds): a multi-file task that has already **stalled** (2+ rounds
no progress, or oscillation flagged), is **high-stakes**, and where a single greedy plan keeps
getting rejected by the verifier. Otherwise run the normal linear loop.

## The pieces

A **node** is a plan state: the cumulative plan `p`, its code, and its execution result `r`. The
root is the initialized first step.

### 1. Introspective node expansion (I-MCTS)

To expand a node, generate the next candidate step by **reflecting on sibling attempts**, not just
the parent: "here is what the other continuations from this state tried and how they scored — propose
a materially different, better next step." Reuse the anti-repeat list (`SKILL.md` §3) as the sibling
memory. Produce 2–3 children per expansion.

### 2. Hybrid reward (I-MCTS) — score before you pay for execution

Each child gets a value from two sources, blended:
- **LLM value estimate** (cheap): ask the verifier-tier model to *predict* how promising this step is
  toward a sufficient plan, **without executing** — a 1–4 estimate using the same rubric
  (`rubric.md`). This prioritizes branches before spending a code-execution rollout.
- **Actual reward** (real): once a child is executed and verified, replace the estimate with the real
  verdict — `is_sufficient` → terminal win; otherwise the graded `score` (1–4) normalized.

Blend toward the actual score as it becomes available (I-MCTS's Q-value transition), so the search
spends execution budget on the branches the value model likes, and corrects itself with ground truth.

### 3. Selection & termination

Select the highest-value non-terminal leaf to expand next (a UCT-style explore/exploit balance is
optional; greedy-on-value is fine at this scale). Stop when a node verifies **sufficient**
(`score == 4`, no rubric `fail`), or the global 20-round / call budget is hit — then finalize the
best-scoring plan found and say so.

## Wiring into the existing loop

Search mode replaces only Stage 4 (route/refine). Stages 1–2 (analyze, init), 3 (verify), 5
(finalize), 6 (debug) are unchanged. The verifier is still the reward signal — which is why **A1
(the rubric verifier) is a prerequisite**: an unreliable judge makes an unreliable search reward.
Dual success/failure memory (Empirical-MCTS) feeds the anti-repeat list across branches.

## Budget note

Cap children-per-expansion at 3 and total executions at the normal round budget. The value-model
pre-screen is what keeps this affordable: most candidates are pruned on a cheap estimate, and only
the promising few are executed. If even that is too costly for the task, you should not be in search
mode — drop back to the linear loop.
