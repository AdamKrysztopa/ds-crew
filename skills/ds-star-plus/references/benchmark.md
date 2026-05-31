# Benchmark plan (Phase 1) — DABStep, deferred

## Status: DEFERRED

The external DABStep harness was not built in this plan to keep Principle 1 intact
(ds-crew bundles no data stack; DABStep requires pip-installing external packages).

**What ships now (Phase 1):** cost/token/latency instrumentation in `run_manifest.py`
(`usage`, `latency_s`, `cost_usd` fields) — so every run is self-reporting and ready
for benchmark instrumentation when the harness is built.

## Follow-up task (when prioritized)

Install DABStep into a **per-project env via `ds-env-setup`** (uv/venv), never as a
ds-crew dependency. Then:

1. Run `ds-star` vs `ds-star-plus` vs `ds-spike` vs a single-shot baseline on the DABStep subset.
2. Publish a results table with **accuracy + cost + tokens + latency** (all four now emitted by the manifest).
3. DABStep is purpose-built for DS-agent evaluation; prefer it over rolling a custom harness.

## The open question to settle

**Does `ds-spike`'s cross-strategy agreement beat the single-model verifier?**

Measurement: run both on the same DABStep subset, compare accuracy at equal cost.

- If `ds-spike` wins → reframe the docs' verifier-centric trust hierarchy.
- If single-model wins → document the cost-accuracy trade-off and keep current hierarchy.

## Why deferred, not dropped

This is the keystone proof: it converts the suite's reliability claims from assertions to evidence.
It just needs an env + dataset budget the current scope did not spend. The instrumentation is ready.
