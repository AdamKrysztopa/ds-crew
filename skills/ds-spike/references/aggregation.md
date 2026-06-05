# Aggregation rules

How `scripts/aggregate.py` turns N solver records into a consensus + minority report. Use the
script; do not eyeball it. These are the rules it encodes.

## Input

A list of solver records, one per dispatched agent:

```python
{
  "id": "solver-2 (sql-first, sonnet, seed=7)",
  "answer": 41.7,          # number, numeric string ("41.7", "41.70%"), or text
  "sufficient": true,      # did that solver's own ds-star-plus verifier pass (score 4, no fail)?
  "assumptions": ["refunds excluded", "EUR"]
}
```

## Clustering

- Two answers join the same cluster if they **match**:
  - **numeric** (both parse as a number, ignoring a trailing `%` and thousands commas): equal within
    relative tolerance `rel_tol` (default `1e-3`) — so `41.7` and `41.70001` are the same answer, but
    `41.7` and `39.4` are not.
  - **text**: equal after lowercasing and collapsing whitespace.
- Clustering is greedy against each cluster's first member (its representative).

## Weighting and consensus

- Each solver contributes weight **1.0 if `sufficient`**, else **0.25** (an unverified solver still
  counts a little, but cannot outvote verified ones).
- Clusters are ranked by total weight, then by member count.
- **Consensus** = the top cluster's representative answer. **Confidence** = top cluster weight ÷ total
  weight (so 3 verified agreeing out of 3 → 1.0; 2 of 3 → ~0.8).
- `unanimous` is true iff there is exactly one cluster.

## Minority report

Every non-top cluster is reported with its answer, the solver ids in it, and the **union of those
solvers' assumptions** — because the assumptions are usually *why* they diverged. The lead agent
then narrates the deciding difference and, if `data/analysis-spec.md` does not settle it, escalates
that fork to the user instead of silently adopting the majority.

**Cross-pollinate with the search-experience store.** A spike minority report and a `ds-search`
search-experience entry encode the same thing — *what diverged and why*. When a minority cluster
turns out to be the deciding fork (a winning or losing approach), record it as a search-experience
entry (`../ds-memory/references/store_format.md`: `approach` = the cluster's method, `outcome` =
win/dead-end + the deciding assumption) so a later hard run can seed from it. Conversely, seed spike
personas' assumption lists from matching prior search-experience entries (see
`personas.md`). Both directions are advisory; the verifier and the spec still govern.

## Reading the result

- **High confidence + unanimous** → report the number plainly.
- **High confidence + a minority** → report the number, then the minority and its assumption.
- **Low confidence (no majority / thin top cluster)** → say it is contested, name the deciding
  assumption, and ask the user (or re-spec via `ds-clarify`). A contested number reported as
  contested is a correct, honest output — not a failure.
