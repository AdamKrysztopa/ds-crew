# Solution Tree — AIDE Loop

## The AIDE Loop

The solution tree is the backbone of the ds-model skill. Each iteration of the loop:

1. **Draft** — write or mutate model code starting from `leaderboard.node_to_expand()`
2. **Train** — fit the model on the training split only
3. **Evaluate** — score the model on the held-out validation split using the agreed metric
4. **Record** — call `lb.add(node_id, score, parent=parent_id)` to register the result
5. **Select next base** — call `lb.node_to_expand()` to get the current best node
6. **Mutate / improve** — modify features, hyperparameters, or architecture starting from that node
7. **Repeat** until the stopping condition is met

## Tree-of-Drafts

- Each model draft is a **node** in the solution tree.
- Its **score** is the held-out validation metric (never the training metric).
- The **tree structure** is maintained by `leaderboard.py`: each node records its parent, enabling trace-back to any ancestor.
- The greedy strategy (always expand the current best) is faithful to AIDE (arXiv 2502.13138).

```
root (draft-1, rmse=0.82)
├── draft-2 (rmse=0.74)   ← current best → expand next
└── draft-3 (rmse=0.79)
```

## When to Stop

Stop iterating when **either** condition is met:

- **Budget exhausted** — the number of drafts reaches the pre-agreed maximum N (default: 10).
- **Plateau** — the best score has not improved for P consecutive expansions (default: 3).

Report whichever stopping condition triggered so the user can adjust the budget if needed.

## Fair Comparison Guarantee

All drafts **must** be evaluated on the **same held-out split** throughout the entire run.
- Fix the random seed for the train/val split before the first draft.
- Never re-split mid-run; doing so makes leaderboard scores incomparable.
- The held-out split is not used for any fitting, encoding, scaling, or feature selection.
