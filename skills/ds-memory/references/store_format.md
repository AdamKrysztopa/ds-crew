# Store format reference

## Entry schema

Each line in the JSONL store is one recipe object:

| Field | Type | Notes |
|---|---|---|
| `task_signature` | string | Pipe-joined sorted bag-of-words from the task prompt (use `task_signature()` to produce). |
| `data_fingerprint` | string | Lightweight fingerprint of the dataset (e.g. `csv:<sha8>`, `sqlite:<name>:<row_count>`). Caller constructs this. |
| `plan` | string | The sequence of steps that solved the task. |
| `verified_code_snippet` | string | The final, verified code block that produced the answer. |
| `verifier_score` | int (1–4) | Score from the ds-star-plus structured verifier. Only entries with score ≥ 4 are returned by `retrieve()`. |
| `assumptions` | list[str] | Explicit assumptions the analysis relied on (currency, date range, inclusion/exclusion rules, etc.). |
| `outcome` | string | Summary of what the answer was (e.g. `"ok"`, or a short phrase like `"41.7% of transactions"`). |
| `timestamp` | string (ISO 8601) | Optional. When the entry was recorded. Useful for pruning stale recipes. |

## Default store path

`./.ds-crew-memory/recipes.jsonl` — relative to the working data directory.

Override by passing an explicit path to `record()` / `retrieve()`:
```python
from memory_store import record, retrieve
store = "/path/to/project/.ds-crew-memory/recipes.jsonl"
record(store, entry)
hits = retrieve(store, sig, fingerprint)
```

## Retrieval semantics

- Only entries with `verifier_score >= 4` are eligible.
- Results are ranked by `(exact fingerprint match, then word-overlap of task_signature)`.
- `retrieve()` returns up to `k=3` entries by default.
- A score of `(0, 0)` — no fingerprint match and zero signature word-overlap — is excluded entirely.

## Rules store (`rules.jsonl`) — Mode 4 (ExpeL distillation)

A **second** JSONL file alongside `recipes.jsonl`, in the same `.ds-crew-memory/` directory:
`./.ds-crew-memory/rules.jsonl`. Where a recipe is a concrete solved instance, a **rule** is an
abstract, task-kind-level heuristic distilled from a *cluster* of recipes (ExpeL's "natural-language
insight"). This file is the **contract**; it is plain JSON, readable/writable in any language —
Mode 4 produces it by Claude's judgment, not by a scoring function.

Each line is one rule object:

| Field | Type | Notes |
|---|---|---|
| `rule` | string | The heuristic, in natural language. A thing to *check*, never an answer. E.g. `"for revenue questions on transaction logs, confirm cancellation/refund handling before summing"`. |
| `task_signature_family` | string | Pipe-joined representative words of the task-kind this rule covers (same word-overlap notion as recipe `task_signature`). Used to match a rule to an incoming question. |
| `support` | int | How many recipes in the cluster the rule was distilled from (evidence weight). |
| `derived_from` | list[str] | Optional. `data_fingerprint`s or signatures of the supporting recipes, for traceability back to evidence. |
| `confidence` | string | `"high"` / `"medium"` / `"low"` — Claude's calibration on how reliably the rule generalizes. |
| `timestamp` | string (ISO 8601) | Optional. When the rule was distilled (lets a later re-distill supersede it). |

**Retrieval (advisory):** at plan time, read `rules.jsonl`, keep rules whose `task_signature_family`
overlaps the current question, and pass them to the planner/checklist as guidance — never as
ground truth. The verifier still gates every step, exactly as for recipes.

## Search-experience store (`search_experience.jsonl`) — ds-search dual memory

A **third** JSONL file in the same `.ds-crew-memory/` directory:
`./.ds-crew-memory/search_experience.jsonl`. This is the **long-term (cross-run)** half of
Empirical-MCTS's dual experience (the in-run anti-repeat list is the short-term half). `ds-search`
appends one entry per materially distinct explored branch at end-of-search; a later hard-task run
reads matching entries to seed its tree toward prior wins and away from dead-ends. Plain JSON,
language-neutral — `ds-search` writes it in whatever language the run used.

Each line is one search-experience object:

| Field | Type | Notes |
|---|---|---|
| `task_signature_family` | string | Task-kind key (same word-overlap notion as recipes/rules), for matching to a future task. |
| `approach` | string | The branch's strategy in one phrase — e.g. `"join claims→policy on policy_id, then group by year"`. |
| `verifier_score` | int (1–4) | The score the branch reached when executed (or its best partial). |
| `outcome` | string | `"win"` or `"dead-end"`, with a one-line *why* — e.g. `"dead-end: double-counted refunds"`. |
| `data_fingerprint` | string | Optional. Dataset fingerprint, for tighter matching. |
| `timestamp` | string (ISO 8601) | Optional. When the branch was recorded. |

**Seeding (advisory):** at the start of a hard `ds-search` run, read entries whose
`task_signature_family` overlaps the task; bias expansion toward `win` approaches and away from
`dead-end` ones *before* spending execution budget. Advisory only — the verifier still scores every
executed node. This store also cross-pollinates with `ds-spike` minority reports (see
`../ds-spike/references/aggregation.md`): both encode *what diverged and why*.

## Pruning guidance

The store is **append-only** at write time. To prune:

1. Load all entries with `json.loads()`.
2. Filter out entries where `verifier_score < 4` or `timestamp < cutoff`.
3. Rewrite the file with the surviving entries (one JSON object per line).

Example:
```python
import json, pathlib
from datetime import datetime, timezone

cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)
path = ".ds-crew-memory/recipes.jsonl"
lines = pathlib.Path(path).read_text().splitlines()
kept = []
for line in lines:
    if not line.strip():
        continue
    e = json.loads(line)
    if e.get("verifier_score", 0) < 4:
        continue
    ts = e.get("timestamp")
    if ts and datetime.fromisoformat(ts) < cutoff:
        continue
    kept.append(line)
pathlib.Path(path).write_text("\n".join(kept) + "\n")
```
