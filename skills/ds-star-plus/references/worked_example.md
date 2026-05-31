# Worked example: the loop in action

A condensed trace of the canonical hard DABStep task, to show how routing (especially
backtracking) plays out. Question:

> "In February 2023 what delta would Rafa_AI pay if the relative fee of the fee with ID=17
> changed to 99?"

Files involved: `payments.csv`, `merchant_data.json`, `fees.json`, `acquirer_countries.csv`.
Note the data quirk surfaced in Stage 1: `merchant_data.json` stores `acquirer` as a *list*,
not a scalar — exactly the kind of thing that causes a later crash if you guess.

| Round | Plan state | Verifier | Router | What happened |
|------|------------|----------|--------|----------------|
| 0 | Step 1: filter payments to Rafa_AI, Feb 2023 (day_of_year 32–59) | Insufficient | Add Step | Good runnable start, not an answer |
| 1 | + Step 2: compute the original total fee (enrich, match fee rules, sum) | Insufficient | Add Step | Needs the modified-rate comparison |
| 2 | + Step 3: recompute with rule 17 rate=99 and subtract | Insufficient | **Step 3 wrong** | Recomputed over *all* transactions, not only those rule 17 applies to → truncate Step 3 |
| 3 | regenerated Step 3: filter only rule-17 transactions, apply (99−60)*vol/10000 | Insufficient | **Step 3 wrong** | Hard-coded the rule conditions instead of matching them generally → truncate again |
| 4 | regenerated Step 3: delta = (99 − original_rate)*affected_vol/10000 | Insufficient | Add Step | Closer, but still didn't isolate affected txns by the rule's full conditions |
| 5 | + Step 4: identify txns matching ALL of rule 17's conditions, compute original vs new total, take difference | **Sufficient** | — | Verified → finalize |

Final script printed `2.67727200000000`.

Lessons this trace demonstrates:

- **Backtracking > patching.** Rounds 2–3 each *removed* the bad Step 3 and re-sampled rather
  than editing it. The replacement that finally worked (round 5) reframed the step entirely.
- **The verifier earned its keep.** Every intermediate script *ran without error* and printed
  a confident-looking EUR figure. Only the sufficiency check kept a wrong number from being
  reported.
- **Stage 1 paid off.** Knowing `acquirer` was a list (from the description) is what let the
  coder defensively unwrap it instead of crashing mid-loop.
