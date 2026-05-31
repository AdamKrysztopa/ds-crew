# Planning graph: DAG plans and dynamic replan

## Representation

The plan is a DAG where each node is `{id, goal, deps: [ids], status}`. Status values:
`pending | running | done | failed`. The current linear plan is the degenerate case: a chain
where each node has exactly one predecessor — fully back-compatible with the existing loop.

```
Example 3-node DAG for "join payments + merchants, compute fee per category":
  node-1: {id:"load", goal:"load payments.csv and merchants.json", deps:[], status:"pending"}
  node-2: {id:"join", goal:"left-join on merchant_id", deps:["load"], status:"pending"}
  node-3: {id:"agg", goal:"sum fee_eur grouped by category", deps:["join"], status:"pending"}
```

Nodes with no shared deps can run in parallel (e.g., two independent file loads). Execution
order is a topological sort; nodes become `running` only when all their deps are `done`.

---

## Node-level verify

The rubric verifier runs on each terminal (leaf) node and each aggregating node, not only at
the final answer. A node is `done` only when its verifier verdict is `score=4` with no rubric
failures. This catches partial failures early — a bad join or an incorrect load is flagged
before downstream nodes waste effort building on it.

---

## Dynamic replan

On a node failure, re-wire only the failed node's subtree: insert or replace descendant nodes
without touching nodes whose deps are unaffected. This generalises today's
"truncate + regenerate tail" to a graph: only the minimal affected subgraph is re-planned.

- Identify the failed node and all nodes that transitively depend on it.
- Re-plan that subgraph, keeping the anti-repeat list from `SKILL.md §3` in scope so the new
  subgraph proposes a materially different approach.
- Nodes outside the affected subgraph retain their `done` status and outputs — no redundant
  re-execution.

---

## When to escalate to a graph

Escalate from linear chain to DAG when:

- Task involves multiple independent file loads that can run in parallel.
- Task produces multiple independent output artefacts (e.g., two separate tables, two charts).
- Task has explicit "then combine" steps (joins, merges, comparisons between branches).

Simple single-file, single-answer tasks stay linear — preserve the fast path. The overhead of
tracking a DAG is only worth it when there is genuine parallelism or independent failure
isolation to exploit.

---

## Relation to search_mode

The DAG is the structure that `references/search_mode.md` searches over: MCTS explores
alternative sub-graphs rooted at the current best node. When search mode is active, each MCTS
child is a candidate re-wiring of a subtree from the rollout node forward. The DAG and search
mode compose naturally — search navigates the space of DAGs, not just linear sequences.
