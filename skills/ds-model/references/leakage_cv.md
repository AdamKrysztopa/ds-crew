# Leakage & CV Discipline

Data leakage silently inflates held-out scores and invalidates the solution tree.
Before reporting any result, confirm every item on this checklist.

## Leakage Checklist

- [ ] **No future data in features** — all feature values must be knowable at prediction time; no lag-0 targets, no post-event flags, no timestamps from the future.
- [ ] **No target-derived features** — features must not be computed from the label column (e.g. target-encoding must be computed inside the CV fold, not on the full dataset).
- [ ] **Fit transformers on train split only** — scalers, encoders, imputers must be fit on train, then applied to val/test; never fit on the combined dataset.
- [ ] **Group-aware splits for panel/time data** — if rows share an entity (user, store) or time, ensure groups don't leak across splits (use GroupKFold or time-ordered splits).
- [ ] **No post-hoc feature selection on full data** — feature selection must happen inside the cross-validation loop; selecting features on the full dataset before splitting leaks val/test signal.
- [ ] **Report held-out metric, not training metric** — the final reported score is on the held-out test/val set, never on the data the model was trained on.

## Common Pitfalls

| Pattern | Safe version |
|---|---|
| `scaler.fit_transform(X)` on full data | `scaler.fit(X_train).transform(X_val)` |
| Target-encoding with full `y` | Target-encoding inside `KFold` loop |
| `train_test_split` after feature engineering | Feature engineering inside the split |
| Reporting train RMSE | Reporting val/test RMSE |
| Sorting by date, then splitting row-by-row | `TimeSeriesSplit` or explicit cutoff |

## Pipeline Pattern (scikit-learn)

Use `sklearn.pipeline.Pipeline` to bundle transformers + estimator so that `.fit()` on the training fold automatically applies all transformations correctly — eliminating the most common leakage mistakes.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

pipe = Pipeline([("scale", StandardScaler()), ("model", Ridge())])
pipe.fit(X_train, y_train)
score = pipe.score(X_val, y_val)   # transformer never saw val data
```
