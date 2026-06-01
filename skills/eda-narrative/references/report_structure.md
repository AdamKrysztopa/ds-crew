# EDA narrative — report structure

The shape of the report and the exploratory passes behind it. The goal is a story a stakeholder
reads top-to-bottom, where every claim is evidenced and every caveat is stated.

## The exploratory passes (Stage 2)

| pass | compute | report only if |
|------|---------|----------------|
| univariate | distribution / summary stats of key numerics; value counts of key categoricals | a shape is notable (skew, dominance, surprise) |
| trend | main metric over time (if a date exists): level, % growth, seasonality | a direction or pattern is real, not noise |
| segment | main metric by the highest-signal categoricals; top/bottom N groups | a segment clearly over/under-performs |
| relationship | correlations / cross-tabs among key variables | strength is non-trivial (note magnitude) |
| anomaly | outliers, breaks, gaps, suspicious constants | it would mislead if left unflagged |

Breadth first, then depth on whatever surfaced. Don't report a pass that found nothing — absence of
finding is a one-liner in caveats, not a section.

## Report structure

```
# <Dataset> — exploratory findings

## Summary
<2–3 lines: the headline takeaways, each a number>

## Findings
1. **<finding>** — <number/stat>. <chart ref>. So what: <one line>.
2. ...
(3–7 findings, ordered by importance)

## Charts
<chart files with exact titles + axis labels>

## Caveats
- Data quality: <nulls/sentinels/grain from data-profile that limit conclusions>
- Scope: <time range, population covered>
- Not examined: <what this pass did NOT look at>
```

## Discipline

- Each finding = claim + evidence (number or chart) + "so what". No bare adjectives.
- Re-derive every reported number from code you ran (narrated ≠ computed).
- Charts: exact titles and axis labels, like a finalized DS-STAR visualization task.
- If a finding becomes a precise question, route it to `ds-clarify` → `ds-star-plus`.
