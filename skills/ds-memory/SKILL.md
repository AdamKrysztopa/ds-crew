---
name: ds-memory
description: "Persistent cross-session recipe store for ds-crew analyses. Use this skill WHENEVER the user asks to inspect, prune, or reuse past analyses ('have we solved this before?', 'remember this analysis', 'reuse past work', 'what analyses have we run?'). Also the substrate other skills (ds-star-plus, ds-spike) call to seed planners and record verified outcomes. Do NOT use for new analysis — use ds-star-plus or ds-spike for that."
---

# ds-memory : remember and reuse what worked

A lightweight, append-only JSONL store that persists verified analysis recipes across
sessions. When a `ds-star-plus` or `ds-spike` run reaches a clean `verifier_score == 4`
verdict, the recipe — plan, code, assumptions, outcome — is banked here. Future runs on
similar tasks can seed their planner with matching recipes instead of starting cold.

The store is built on the Agentic Workflow Memory (AWM) principle (arXiv:2409.07429): save
what worked, retrieve by similarity, let the downstream verifier still gate every reuse. This
skill is the persistent-memory substrate of the ds-crew suite.

## When this applies

Use **ds-memory** directly when the user wants to:
- **Inspect** the store — "what analyses have we run?", "show me past results", "have we solved this before?"
- **Prune** the store — "remove stale entries", "clean up old analyses", "prune recipes older than 2024"
- **Retrieve** a past recipe explicitly — "reuse the analysis we ran on the sales data last month"

Use it **indirectly** (called by other skills) when:
- `ds-star-plus` reaches a clean verdict and wants to bank the recipe
- `ds-star-plus` starts a new plan and a store exists at the default path
- `ds-spike` wants to seed each solver's assumption list with minority-report assumptions from prior runs

Do **not** use this skill to run new analysis — that is `ds-star-plus` or `ds-spike`.

## The cardinal rule

**Only record entries with `verifier_score == 4`.** A recipe that slipped past the verifier
is worse than no recipe at all — it seeds future plans with a plausible-but-wrong approach.

**Retrieval is never blindly trusted.** Retrieved recipes are *suggestions* to the planner,
not answers. The downstream verifier still gates every step. A past plan that worked on
slightly different data may not work here.

## How to run it

### Mode 1 — Inspect

List recent entries from the store. Report: task signature, data fingerprint, outcome, score,
and timestamp (if present). Group by task signature to surface repeated patterns.

```python
from memory_store import _load
entries = _load(".ds-crew-memory/recipes.jsonl")
for e in sorted(entries, key=lambda x: x.get("timestamp",""), reverse=True)[:20]:
    print(e.get("task_signature"), "|", e.get("outcome"), "|", e.get("verifier_score"))
```

### Mode 2 — Prune

Remove entries that are low-score or stale. The store is append-only at write time, so
pruning means rewriting it without the unwanted entries. See the pruning example in
`references/store_format.md`. Always confirm the count before and after.

### Mode 3 — Retrieve (called by ds-star-plus / ds-spike at plan time)

```python
from memory_store import retrieve, task_signature
store = ".ds-crew-memory/recipes.jsonl"
sig = task_signature(question)          # normalize the question
hits = retrieve(store, sig, data_fingerprint, k=3)
# hits: list of recipe dicts, ranked by (exact fp match, word-overlap), score >= 4 only
```

Pass `hits` to the planner as *suggestions*. Mark them explicitly as prior recipes, not
ground truth. The verifier still runs on every step.

## Output

**Inspect / Prune:** a summary of store state — total entries, entries by score, entries by
task-signature cluster, date range (if timestamps present). After pruning: count removed and
count retained.

**Retrieve:** a list of matching recipe entries (up to k=3), each showing task signature,
data fingerprint, plan summary, outcome, score, and assumptions.

## Quick reference

```python
from memory_store import record, retrieve, task_signature

store = "./.ds-crew-memory/recipes.jsonl"   # default path (relative to data dir)

# Bank a verified recipe
record(store, {
    "task_signature": task_signature(question),
    "data_fingerprint": fingerprint,
    "plan": plan_text,
    "verified_code_snippet": code,
    "verifier_score": 4,
    "assumptions": assumptions_list,
    "outcome": "ok",
})

# Retrieve matching recipes
hits = retrieve(store, task_signature(question), fingerprint, k=3)
```

Store format + pruning guidance: `references/store_format.md`.
Script: `scripts/memory_store.py`. Tests: `scripts/test_memory_store.py`.
