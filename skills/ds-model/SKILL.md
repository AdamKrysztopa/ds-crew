---
name: ds-model
description: "Use when building or improving a predictive model — AIDE-style solution tree with leakage discipline and empirical leaderboard"
---

# ds-model : build, evaluate, and improve models with a solution tree

## When this applies

Use `ds-model` for any task that requires **fitting a predictive or forecasting model**:

- Regression, classification, or ranking on tabular data
- Time-series forecasting
- Kaggle or other ML competition submissions
- Iterative model improvement ("improve accuracy", "reduce RMSE", "beat baseline")
- Hyperparameter tuning or architecture search
- Producing a model artefact or submission file

Do **not** use for pure data aggregation, analytical questions, or EDA — those belong to `ds-star-plus` or `eda-narrative`.

## The cardinal rule

> **The held-out metric is law.**
> Never report training-set performance as the result.
> Every transformer (scaler, encoder, imputer) must be fit on the training split only, then applied to val/test.
> Confirm the full leakage checklist (`references/leakage_cv.md`) before finalising any result.

## How to run it

### Stage 1 — Analyse data and define the objective
- Profile the dataset (shape, dtypes, missing values, target distribution).
- Agree on the **evaluation metric** (e.g. RMSE, AUC, log-loss) and **direction** (`min` or `max`).
- Create a fixed train/val(/test) split with a locked random seed. This split is never changed during the run.

### Stage 2 — Draft the baseline model
- Write the simplest reasonable model (e.g. linear model, decision tree, or gradient-boosted tree with default parameters).
- Wrap transforms and model in a `sklearn.Pipeline` to avoid leakage.
- Register as `lb.add("draft-1", score, parent=None)` using `leaderboard.py`.

### Stage 3 — Evaluate and record
- Compute the held-out val metric on the fixed split.
- Add the result to the leaderboard: `lb.add(node_id, score, parent)`.
- Print the leaderboard summary after each draft.

### Stage 4 — Expand the best node
- Call `lb.node_to_expand()` to identify the current best draft.
- Mutate it: try better features, different algorithm, tuned hyperparameters, or ensembling.
- Fit only on training data; evaluate on the same val split.

### Stage 5 — Repeat until budget or plateau
- Continue Stage 3 → Stage 4 until one stopping condition fires:
  - **Budget**: total drafts reaches N (default 10).
  - **Plateau**: best score unchanged for P consecutive expansions (default 3).
- State which condition stopped the loop.

### Stage 6 — Finalise and deliver
- Select the best node from `lb.best()`.
- Re-fit on full train+val data if a held-out test set exists, then score on test.
- Confirm the leakage checklist (`references/leakage_cv.md`).
- Deliver: best model code, held-out metric, leaderboard summary, leakage checklist confirmation.

## Output

Every `ds-model` run produces:

1. **Best model code** — Python script or notebook cell, self-contained and runnable
2. **Held-out metric** — single number on the fixed val (or test) split, with metric name and direction
3. **Leaderboard summary** — table of all drafts: node id, parent, score, delta vs. previous best
4. **Leakage checklist confirmation** — all six items from `leakage_cv.md` explicitly checked off
5. **Stopping reason** — budget exhausted or plateau (N drafts, P consecutive non-improvements)

## Quick reference

| Resource | What it covers |
|---|---|
| [`references/solution_tree.md`](references/solution_tree.md) | AIDE loop, tree-of-drafts, stopping conditions, fair-comparison guarantee |
| [`references/leakage_cv.md`](references/leakage_cv.md) | Six-item leakage checklist, common pitfalls, Pipeline pattern |
| [`references/evidence.md`](references/evidence.md) | AIDE (2502.13138), AutoKaggle (2410.20424), AutoML-Agent (2410.02958) |
| [`scripts/leaderboard.py`](scripts/leaderboard.py) | `Leaderboard` class — `add`, `best`, `node_to_expand`, `tree` |
