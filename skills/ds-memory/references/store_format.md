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
