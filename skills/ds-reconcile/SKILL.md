---
name: ds-reconcile
description: "Standalone blackboard reconciliation skill. Use this skill WHENEVER the user already has multiple candidate answers and wants them reconciled ('reconcile these answers', 'which of these results is right?', 'combine these analyses', 'I got different numbers from two runs'). Clusters answers, weights verified ones higher, returns consensus + confidence + minority report. Optionally scores each candidate with ds-verify first. Do NOT use to produce new analyses — use ds-spike for a full parallel run."
---

# ds-reconcile : cluster existing answers into consensus + minority report

## When this applies

Use ds-reconcile when you **already have N candidate answers** (from any source — different
runs, different analysts, different tools) and want them reconciled into a consensus view.

Do NOT use when you need to produce new analyses from scratch; use `ds-spike` for a full
parallel ensemble run that produces and then reconciles answers.

## The cardinal rule

**Always preserve the minority report.** Disagreements between candidates are the insight,
not noise to be suppressed. A unanimous result with high confidence is more trustworthy than
a forced consensus that hides a dissenting answer.

## How to run it

1. Collect candidate records in the standard format:
   ```python
   {"id": "run-1", "answer": 41.7, "sufficient": True, "assumptions": ["refunds excluded"]}
   ```
   The `sufficient` field is optional but important: verified answers are weighted 4× higher
   than unverified ones (`WEIGHT_SUFFICIENT=1.0` vs `WEIGHT_UNVERIFIED=0.25`).
2. Optionally score each candidate with `ds-verify` first to populate `sufficient: True/False`.
   This step is recommended whenever the answer stakes are non-trivial.
3. Call `aggregate(records)` from `../ds-spike/scripts/aggregate.py`.
4. Present the consensus answer + confidence + minority report to the user.

## Output

```json
{
  "answer": "<consensus answer>",
  "confidence": 0.8,
  "support": ["run-1", "run-3"],
  "n_solvers": 3,
  "n_clusters": 2,
  "unanimous": false,
  "minority_report": [
    {
      "answer": "<dissenting answer>",
      "support": ["run-2"],
      "assumptions": ["refunds included"]
    }
  ]
}
```

Report `confidence` as the fraction of total weight (not raw count) behind the consensus,
so that verified answers count more than unverified ones.

## Quick reference

```python
from aggregate import aggregate

result = aggregate(records)
print("consensus:", result["answer"], "confidence:", result["confidence"])
print("minority_report:", result["minority_report"])
```

- Module: `../ds-spike/scripts/aggregate.py`
- Key functions: `aggregate(records)`, `cluster_results(records)`
- Weighting: `sufficient=True` → weight 1.0; `sufficient=False/missing` → weight 0.25
- `aggregate(records)["confidence"]` — fraction of weight behind the consensus
- `aggregate(records)["minority_report"]` — list of dissenting answer clusters
