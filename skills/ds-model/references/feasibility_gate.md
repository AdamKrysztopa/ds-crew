# Feasibility & leakage gate (run BEFORE modeling)

Before building any predictive model, do two things: **(a) estimate the achievable performance
ceiling, and (b) scan for leakage.** Then treat the ceiling as the acceptance bar — *a model that
meaningfully beats the feasibility ceiling is presumed to be leaking until proven otherwise.* This
turns leakage discipline into a **required step**, not a lucky catch by a careful agent.

Cheap, run once, before drafting models. Tool-agnostic — implement in the user's own language /
libraries. The gate has **two faces**; pick by data shape.

---

## A. Cross-sectional (i.i.d. tabular) — the default

1. **Achievable-performance probe (the ceiling).** Fit a trivial baseline (majority class / mean)
   then *one* quick strong model (e.g. gradient boosting) under proper CV. Record the resulting
   metric as the **expected ceiling** — it sets honest expectations and a stop signal (don't grind
   tuning far past it).
2. **Single-feature leakage scan.** For each feature, measure its *solo* association with the target
   (single-feature model score, or "is any category ~100% one class?"). **Flag any feature that
   alone predicts the target near-perfectly** — it is leakage or leakage-adjacent (an ID, a target
   component, a top-code such as `capital-gain=99999`, a post-outcome field). Decide keep / drop /
   flag for each, explicitly.
3. **Adversarial validation (distribution shift).** If a train/test split is given, train a
   classifier to tell train-vs-test rows apart. AUC ≈ 0.5 → same distribution (good); **AUC ≫ 0.5 →
   covariate shift**, so CV will be optimistic — the top discriminating features are the drift
   drivers, handle them before trusting the score.
4. **Duplication / ID check.** Exact and near-duplicate rows leak across the split if not grouped;
   a unique-per-row column (an ID) invites overfitting/leak. Find both, decide dedup/group policy.

## B. Time-series / ordered — when a datetime or row ordering exists

1. **Forecastability gate (the ceiling).** Before forecasting, estimate **how predictable** the
   series is and **at what dependence horizon**. Recommended tool: **`dependence-forecastability`**
   (dependence-structure / forecastability analysis). **Fallback if unavailable:** ACF/PACF for the
   dependence horizon + a predictability proxy (permutation or sample entropy) + a "same period last
   cycle" naive baseline. Record the ceiling.
2. **Temporal split — always.** Split by **time** (train earlier, test later), **never shuffle**;
   use time-respecting CV (rolling / expanding window). A random split on ordered data *is* leakage.
3. **Target-leakage check.** No future information in features (no look-ahead aggregates), no
   target-derived columns (e.g. components that sum to the target), no test-horizon bleed into train.

---

## The cardinal rule of the gate

> **The ceiling is the acceptance bar.** Beating it is an alarm, not a triumph. If a model clears
> the feasibility ceiling by a wide margin, re-run the single-feature / target-leakage scan before
> believing the number.

## Output (record in the spec + the leaderboard/manifest)

- **Expected ceiling** + how it was estimated (probe model / forecastability tool / fallback).
- **Leakage flags**: the features, duplicates, and drift found — with the keep/drop/flag decision.
- **Split policy** chosen (temporal vs stratified) and why.

## See also

- In-pipeline CV / transform discipline (fit-on-train-only, the six-item checklist):
  [`leakage_cv.md`](leakage_cv.md).
- The gate is the *pre-modeling* counterpart of that *in-modeling* discipline — run this first, then
  hold the line with `leakage_cv.md` while you build.
