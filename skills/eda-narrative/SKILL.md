---
name: eda-narrative
description: "Use when exploring data without a fixed question — produces a stakeholder-ready narrative backed by numbers and charts"
---

# eda-narrative : exploration into a story

Question-answering (`ds-star-plus`) and *exploration* are different jobs. Exploration has no single
right answer — it surveys the data and reports what's worth knowing. This skill does that and writes
it up as a narrative a stakeholder can read: each claim grounded in a computed number or a chart,
each caveat stated.

## When this applies

A first look at a new dataset; a stakeholder asking "what's interesting here?"; finding trends,
correlations, segments, anomalies, or a summary deck's worth of findings. Run **after**
`data-profile` (don't narrate dirty data as if clean) and instead of `ds-star-plus` when there is no
single precise question.

## The cardinal rule

**Every finding carries its evidence.** No "sales are strong" — instead "Q4 revenue €1.2M, +18% vs
Q3 (chart)". An unsupported narrative is a guess dressed as insight. If the data can't support a
claim, say what it *can* support.

## How to run it

### Stage 1 — Ground in quality

Read the `data-profile` watch-outs first (or run it). Know the nulls, sentinels, and grain before
you compute a single statistic, so findings aren't artifacts of dirty data.

### Stage 2 — Survey (breadth before depth)

Compute the standard exploratory passes, each grounded:
- **Univariate**: distributions of key numerics and categoricals (with the actual numbers).
- **Trends**: time series of the main metric(s) if a date column exists — level, growth, seasonality.
- **Segments**: the main metric broken down by the highest-signal categoricals (top/bottom groups).
- **Relationships**: correlations / cross-tabs among key variables; note strength, not just sign.
- **Anomalies**: outliers, sudden changes, suspicious gaps — flagged, not hidden.

### Stage 3 — Verify before narrating

Each finding you intend to report must be re-derived by code you actually ran (the DS-STAR rule:
executable ≠ correct, and *narrated ≠ computed*). Drop any "finding" you can't reproduce from a real
number or chart.

### Stage 4 — Write the narrative

Use `references/report_structure.md`: a 2–3 line executive summary, then 3–7 findings each with its
number/chart and a one-line "so what", then caveats (data quality, scope, what was NOT examined).
Generate charts with exact titles and axis labels. Order findings by importance, not by computation
order.

## Output

A readable narrative report (markdown + chart files) where every claim is backed by evidence and the
caveats are explicit. If a finding raises a precise question worth nailing down, hand it to
`ds-clarify` → `ds-star-plus`.

## Quick reference

Report structure + the exploratory passes: `references/report_structure.md`.
Profile the data first: `../data-profile/SKILL.md`.
