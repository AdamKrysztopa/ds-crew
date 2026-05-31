---
name: ds-search
description: "Standalone MCTS search-mode solver for a single hard data-science task. Use this skill WHENEVER a single task is hard enough to warrant tree search ('this task is hard, search harder', 'try multiple solution paths', 'tree search this', 'explore alternatives for this specific step'). Runs ds-star-plus in its optional MCTS search mode: introspective node expansion + hybrid LLM reward estimation. More expensive than a plain ds-star-plus run but finds better solutions on hard multi-step tasks. Composes with DAG planning (references/planning_graph.md). Do NOT use for routine single-answer questions — use ds-star-plus; do NOT use for ensemble confidence — use ds-spike."
---

# ds-search : tree-search a single hard task with MCTS

## When this applies

Use ds-search when **one task is hard enough** that greedy refinement keeps oscillating or
failing — the linear ds-star-plus loop has tried multiple rounds without reaching a sufficient
answer and you want to explore alternative solution paths before committing to one.

Good signals:
- The planner keeps returning to the same failing approach
- Multiple different implementations all fail the verifier on the same rubric item
- The task has genuinely branching solution paths (e.g., SQL vs. pandas vs. join strategy)

Do NOT use for:
- Routine questions — the LLM call budget multiplies; use `ds-star-plus`.
- Ensemble confidence — use `ds-spike` (persona diversity + debate).

## The cardinal rule

**Search multiplies LLM calls** (budget ≈ branching_factor × depth). Use it deliberately,
not by default. The value-model pre-screen keeps it affordable — most candidate branches are
pruned on a cheap estimate before execution — but even so, this is the most expensive mode
in the suite. Apply it to the hard tail only.

## How to run it

1. **Formulate the single hard task clearly** — one well-scoped question, with all relevant
   data files and the desired output format specified.
2. **Activate search mode** per `../ds-star-plus/references/search_mode.md`. Set:
   - `branching_factor` — number of alternative continuations to generate per expansion
     (cap at 3 per the budget note in search_mode.md)
   - `max_depth` — maximum plan steps to explore before forcing termination
3. **Run.** The search expands a tree of candidate solution steps. Each node is scored by
   the hybrid reward: cheap LLM value estimate first, then replaced by the real verifier
   verdict once executed.
4. **Take the highest-scoring leaf** as the answer. If no leaf reached `score == 4` with
   no rubric failures, report the best found and state that it did not fully pass.

Selection strategy: pick the highest-value non-terminal leaf to expand next (greedy-on-value;
UCT-style explore/exploit balance is optional at this scale). Stop on first sufficient node
or when the global call budget is exhausted.

## Output

- **Best solution found** — the answer from the highest-scoring leaf in the search tree
- **Verifier score** — the score (1–4) and rubric verdict for that leaf
- **Paths explored** — a brief summary of how many branches were explored and which were
  pruned early by the value estimate

If the search terminates without a `score == 4` / no-fail result, say so explicitly and
surface the best partial solution with its rubric failures.

## Quick reference

- Full MCTS protocol: `../ds-star-plus/references/search_mode.md`
- DAG planning integration: `../ds-star-plus/references/planning_graph.md`
- Verifier scoring: `../ds-star-plus/scripts/verify_schema.py` (`parse_verdict`,
  `is_sufficient`)
- Rubric reference: `../ds-star-plus/references/rubric.md`
- Budget cap: branching_factor ≤ 3, total executions ≤ normal round budget (see
  search_mode.md Budget note)
