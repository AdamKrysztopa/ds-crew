---
name: ds-memory
description: "Use when browsing, pruning, or seeding a run from past analyses stored across sessions"
---

# ds-memory : remember and reuse what worked

A lightweight, append-only JSONL store that persists verified analysis recipes across
sessions. When a `ds-star-plus` or `ds-spike` run reaches a clean `verifier_score == 4`
verdict, the recipe — plan, code, assumptions, outcome — is banked here. Future runs on
similar tasks can seed their planner with matching recipes instead of starting cold.

The store is built on three lines of agent-memory work: **Agentic Workflow Memory** (AWM,
arXiv:2409.07429) — save what worked, retrieve by similarity; **Voyager** (arXiv:2305.16291) —
a versioned library of self-verified skills; and **ExpeL** (arXiv:2308.10144) — distilling
experience into reusable guidance. ExpeL's distillation is implemented as **Mode 4 (Distill)**
below: concrete recipes → abstract **rules** (our label for ExpeL's "natural-language insights",
extracted from cross-task success *and* failure). The downstream verifier still gates every reuse.
This skill is the persistent-memory substrate of the ds-crew suite. Grounding, and the one
deliberately-skipped half (Voyager's automatic curriculum — open-ended self-improvement, no current
user): `references/evidence.md`.

## When this applies

Use **ds-memory** directly when the user wants to:
- **Inspect** the store — "what analyses have we run?", "show me past results", "have we solved this before?"
- **Prune** the store — "remove stale entries", "clean up old analyses", "prune recipes older than 2024"
- **Retrieve** a past recipe explicitly — "reuse the analysis we ran on the sales data last month"
- **Distill** rules from the store — "extract reusable heuristics from past runs", "what general lessons have we learned?" (Mode 4)

Use it **indirectly** (called by other skills) when:
- `ds-star-plus` reaches a clean verdict and wants to bank the recipe
- `ds-star-plus` starts a new plan and a store exists at the default path — retrieves matching *recipes and rules*
- `ds-conduct` assembles a plan and folds matching rules into the workflow + the questions it raises
- `ds-clarify` turns a matching rule into a checklist item ("last time this task-kind was ambiguous here — ask now")
- `ds-spike` wants to seed each solver's assumption list with minority-report assumptions and matching rules from prior runs

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

### Mode 4 — Distill (ExpeL rules; prose protocol, run periodically)

Concrete recipes answer "what worked on *this* data"; **rules** answer "what tends to be true for
*this kind of task*" — the ExpeL move of turning a pile of trajectories into reusable
natural-language insights. This mode is **judgment, so it is prose, not an algorithm** — Claude does
the clustering and extraction; the only artifact is a second JSONL file, `rules.jsonl`, in the same
store. No new code: read with the existing generic `_load`, append with the existing generic
`record` (or any JSONL reader/writer in your language — the format is the contract).

**Distill (periodic, not per-run):**
1. Read the recipe store. Group entries by `task_signature` similarity (the same word-overlap notion
   `retrieve` uses) — and, where present, by `data_fingerprint` family.
2. For each cluster with enough evidence (≥3 recipes, and ideally a mix of clean and corrected
   outcomes), ask: *what reusable heuristic explains the wins and would have prevented the misses?*
   Extract a **small** set of abstract rules — e.g. *"for revenue questions on transaction logs,
   confirm cancellation/refund handling before summing"*. Keep them general (task-kind level), not
   data-specific (that is what recipes are for). Prefer few, high-signal rules over many.
3. Append each as one line to `rules.jsonl` (schema in `references/store_format.md`): the rule text,
   the `task_signature` family it applies to, supporting recipe count, and a confidence note.
4. Rules are **advisory only** — same cardinal rule as recipes; the verifier still gates everything.
   A rule never asserts an answer, only a thing-to-check.

**Retrieve rules (at plan time, alongside recipe retrieval — also prose):** read `rules.jsonl`, keep
rules whose `task_signature` family overlaps the current question, and pass them to the planner as
guidance ("prior runs of this task-kind suggest: …"). No scoring function — overlap judgment is
Claude's, in the user's own environment.

## Output

**Inspect / Prune:** a summary of store state — total entries, entries by score, entries by
task-signature cluster, date range (if timestamps present). After pruning: count removed and
count retained.

**Retrieve:** a list of matching recipe entries (up to k=3), each showing task signature,
data fingerprint, plan summary, outcome, score, and assumptions.

**Distill:** the small set of rules written to `rules.jsonl` — each with its rule text, the
task-signature family it covers, supporting recipe count, and confidence. Report how many clusters
were examined and how many rules were added vs. already present.

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
