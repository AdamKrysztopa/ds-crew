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

---

# Worked example: column-level retrieval recovers a file embedding missed

A data-lake task (N ≈ 1,400 files) to show the Stage-3 keep rule (`retrieval.md`) doing its job.
Question:

> "What was the average **claim amount** per **policy** in 2023?"

Two files matter; one is recovered only by structure:

| File | Stage 1 embedding (query↔description cosine) | Stage 3 structural judgment | Kept? |
|------|----------------------------------------------|------------------------------|-------|
| `motor_claims_2023.csv` | **0.71** — description says "claims dataset" | column-name match: `claim_amount`, `policy_id` | ✅ both signals |
| `pol_master.parquet` | **0.18** — description reads "master reference extract, internal", never says "policy" | join-key reachability: shares `policy_id` with the selected claims file; needed to scope "per policy" / 2023 effective policies | ✅ **structure only** |
| `weather_stations.csv` | 0.22 | no column/value/key overlap | ❌ neither |

**What would have happened embedding-only (Stage 1–2):** `pol_master.parquet` ranks **below**
`weather_stations.csv` on cosine — its description is bureaucratic boilerplate that never mentions
"policy". A top-K cut drops it. The run then computes "average claim amount" with no way to resolve
each claim to its policy's 2023 validity → a confident, **wrong** number, and nothing downstream can
recover the never-loaded file. This is precisely the 44.69→52.55 oracle gap (DS-STAR Table 2) in
miniature.

**What the keep rule does:** `pol_master.parquet` is weak on embedding but strong on **join-key
reachability** (it shares `policy_id` with the already-selected claims file). The recall-biased rule
— *keep a file strong on either signal* — carries it forward. The join becomes possible; the answer
is computable.

Lessons:

- **Structure beats prose for discovery.** A file's *columns and keys* say what it can answer; its
  *description* often does not. Stage 3 scores the former.
- **Recall-bias is the whole point.** When embedding and structure disagree, keep the file — a
  missed file is unrecoverable, an extra file is merely pruned by execution. Asymmetric cost,
  asymmetric rule.
- **No new tooling.** All three judgments (column-name, value, join-key) are read off the digests
  the profiling step already produced, inside the Stage-2 Haiku pass — no extra call, no script.
