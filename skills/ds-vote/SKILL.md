---
name: ds-vote
description: "Self-consistency N-vote for data science answers. Use this skill WHENEVER the user wants a quick confidence check ('run it a few times and see if it agrees', 'how stable is this number?', 'is this answer robust?'). Runs ds-star-plus N times with varied seeds (same model, same persona — no diversity), then aggregates for majority answer + agreement rate. This is the cheap cousin of ds-spike: no persona diversity, no debate, just vote count. Cite Wang et al. 2203.11171. Do NOT use for high-stakes contested results — use ds-spike with debate for that."
---

# ds-vote : run the same solver N times and count votes

## When this applies

Use ds-vote when you want a **fast stability check** on a moderately important question.
You want to know: if I run this again, would I get the same answer?

Do NOT use when:
- The stakes are high and you need independent confirmation — use `ds-spike` (different
  personas, potential debate round).
- You already have multiple candidate answers in hand — use `ds-reconcile`.

## The cardinal rule

**This is NOT an ensemble.** Solvers use the same model and persona across all N runs, so
agreement indicates *stability*, not *independent confirmation*. Consistent agreement means
the answer is stable; disagreement means the question is sensitive to code or interpretation
choices. For true independence (diversity of approach), use `ds-spike`.

Based on self-consistency sampling: Wang et al. 2022 (arXiv:2203.11171).

## How to run it

1. Run `ds-star-plus` **N times** (default N=3) with varied random seeds but identical
   model and persona settings.
2. Collect the result of each run as a record:
   ```python
   {"id": f"vote-{i}", "answer": answer_i, "sufficient": sufficient_i}
   ```
3. Call `aggregate()` from `../ds-spike/scripts/aggregate.py` on all N records.
4. Report the majority answer + confidence (fraction of runs agreeing) + any minority answers.

## Output

- **Majority answer** — the answer returned by the plurality of runs (weighted by sufficiency)
- **Confidence** — fraction of total weight behind the majority answer (0.0–1.0)
- **Minority answers** — any answers returned by fewer runs (surface these; they indicate
  instability)

Example:

```
Majority answer: 41.7   confidence: 0.83   (2/3 runs)
Minority answer: 39.1   (1 run — different handling of NaN rows)
```

## Quick reference

```python
from aggregate import aggregate   # ../ds-spike/scripts/aggregate.py

records = [
    {"id": "vote-1", "answer": answer_1, "sufficient": sufficient_1},
    {"id": "vote-2", "answer": answer_2, "sufficient": sufficient_2},
    {"id": "vote-3", "answer": answer_3, "sufficient": sufficient_3},
]
result = aggregate(records)
print("majority:", result["answer"], "confidence:", result["confidence"])
```

- Default N = 3 (add runs for higher confidence at higher cost)
- Same model and persona across all runs (only seed varies)
- `aggregate()` for majority vote and confidence: `../ds-spike/scripts/aggregate.py`
- Reference: Wang et al. 2022, arXiv:2203.11171 ("Self-Consistency Improves Chain of Thought
  Reasoning in Language Models")
