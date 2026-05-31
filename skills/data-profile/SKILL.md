---
name: data-profile
description: "Produce a thorough data-quality / profiling report for one file or a whole folder (CSV, TSV, JSON, Excel/XLSX, Parquet, SQLite): shape, column types, missingness, cardinality, candidate keys, duplicate rows, value distributions, outliers, encoding/sentinel issues, and cross-file join compatibility. Use this skill WHENEVER the user wants to profile / audit / sanity-check / understand the quality of a dataset before analysis, asks what's in this data or whether it's clean, onboards a new dataset, or needs a data-quality report. This is DS-STAR's analyze-first stage promoted to a standalone deliverable. Pairs naturally before ds-star / ds-star-plus / ds-spike. Do NOT use to answer a specific analytical question (use ds-star-plus) or for prose."
---

# data-profile : know the data before you trust it

DS-STAR's single biggest correctness lever is analyzing every file *before* planning — its
ablation shows hard-task accuracy collapses 45.24 → 26.98 without it (see
`../ds-star-plus/references/evidence.md`). This skill makes that step a first-class output: a
structured data-quality report you can read, share, and act on, independent of any one question.

## When this applies

Onboarding a new dataset; deciding whether data is fit to answer a question; hunting the silent
issues (hidden nulls, sentinels, duplicate fan-out, type surprises, join mismatches) that wreck
analyses later. Run it standalone, or as the pre-step before `ds-clarify` / `ds-star-plus`.

## The cardinal rule

**Print real content; never assume structure.** The same discipline DS-STAR's analyzer uses:
load and *show* — actual column names, actual value spellings, actual dtypes — instead of guessing
from the file name. Surfaced reality is the whole value.

## How to run it

### Stage 1 — Inventory

List every file in scope with size and type. For a folder, group by extension. Do not load
gigabytes blindly — sample large files.

### Stage 2 — Per-file profile

Run `../ds-star-plus/scripts/analyze_file.py <path>` (the ready-made describer) as the base, then
extend it with the data-quality checks in `references/checks.md`. For each file emit:
- shape, columns + dtypes, sheet/table names (Excel/SQLite — list ALL, data often hides off-sheet);
- missingness per column (count + %), and **suspected sentinels** masquerading as values
  (`-`, `?`, `NEW`, `0`, `9999`, empty string);
- cardinality per column; flag **candidate keys** (unique, non-null) and **constant** columns;
- duplicate-row count and the key that would dedup them;
- for numeric columns: min/max/mean/median + simple outlier flags (IQR or z-score);
- for low-cardinality object columns: value counts;
- encoding / parse anomalies (mixed types in a column, stray whitespace, inconsistent casing).

### Stage 3 — Cross-file (folder mode)

For columns that share a name/role across files, check **join compatibility**: dtype match,
value-overlap, and whether a join would fan out (one-to-many) or drop rows (non-overlap). This is
where multi-file analyses silently go wrong; flag it before anyone joins.

### Stage 4 — Report

Emit a single report (markdown by default; the structure is in `references/checks.md`), ending with
a **"Watch-outs" list** — the specific issues that would bite an analysis (e.g. "`amount` has 3%
nulls and a `-` sentinel; `order_id` is NOT unique — fan-out risk on join"). State assumptions you
made (e.g. sampling) plainly.

## Output

A readable data-quality report plus a short watch-outs list. If the user is heading into a specific
analysis, hand the watch-outs to `ds-clarify` so they become spec decisions (null policy, dedup key,
units) rather than silent surprises.

## Quick reference

Data-quality checks + report structure: `references/checks.md`.
Base describer (reused): `../ds-star-plus/scripts/analyze_file.py`.
