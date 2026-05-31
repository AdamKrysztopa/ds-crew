# Ambiguity checklist (the decision tree)

Walk these for any non-trivial data question. For each, decide: is it **already pinned** by the
question, **ambiguous** (ask the user), or **not applicable**? Only ask about the ambiguous ones,
and batch related questions into one message. Each item lists the failure it prevents (mapped to
the `ds-star-plus` rubric in `../ds-star-plus/references/rubric.md`).

## 1. Metric definition — *prevents question_substitution*
What exactly is being measured? "Revenue" = gross or net of discount/refunds/tax? "Active user" =
logged in, transacted, or opened the app? "Average" = mean or median? Ask for the formula if the
term is even slightly fuzzy.
> Prompt: *"By <metric> do you mean <A> or <B>? e.g. revenue net of discount, or gross?"*

## 2. Population / scope — *prevents scope_error*
Which rows are in scope? All customers, or only paying ones? Which segment, region, product line?
Is there an implied entity ("our merchants") that needs a filter?
> Prompt: *"Should this cover <all X> or only <subset>?"*

## 3. Time window + timezone — *prevents scope_error*
Exact start/end? Inclusive or exclusive of the boundary? "Last quarter" = calendar Q or trailing 90
days? Which timezone defines the day boundary (UTC vs local)? Fiscal vs calendar year?
> Prompt: *"Q4 2023 = Oct 1–Dec 31 inclusive, in which timezone? UTC or <local>?"*

## 4. Filters & category values — *prevents wrong_column_or_value*
Confirm the literal column/value against the **real schema** (from Stage 1). Does the asked filter
("NexPay", "credit card") map to an actual value, and in which column? Case sensitivity, spelling
variants, synonyms?
> Prompt: *"I see no payment-gateway column; the closest is `card_scheme` with value `NexPay`. Use that?"*

## 5. Null / missing / sentinel handling — *prevents dropped_rows*
Drop, zero-fill, or impute nulls? Are there sentinels (`-`, `?`, `NEW`, `0`, `9999`) that secretly
mean missing? Should rows with a missing key be excluded or kept?
> Prompt: *"~3% of `amount` is null — drop those rows, treat as 0, or stop and report?"*

## 6. Duplicates & dedup keys — *prevents dropped_rows*
Are duplicate rows expected? What key identifies a unique record? Dedup before or after aggregation?
> Prompt: *"Is `order_id` unique, or can it repeat (e.g. line items)? Dedup on what?"*

## 7. Outlier policy — *prevents scope_error / question_substitution*
Cap, winsorize, exclude, or keep extreme values? Is there a known bad-data range?
> Prompt: *"Keep the 5 transactions over €1M, or treat them as data errors and exclude?"*

## 8. Units & scale — *prevents units_mismatch*
Cents vs main currency unit? Fraction (0–1) vs percent (0–100)? Basis points? Per-row vs aggregate?
Currency conversion needed, at what rate/date?
> Prompt: *"Answer as a percentage (e.g. 41.7) or a 0–1 fraction (0.417)? Amounts in EUR or cents?"*

## 9. Rounding / precision — *prevents format_mismatch*
How many decimals? Round half-up or banker's? Truncate or round? Significant figures?
> Prompt: *"Round to how many decimal places?"*

## 10. Tie-breaking & ordering — *prevents format_mismatch / question_substitution*
For "top N", how are ties broken? Sort ascending or descending? Stable order by a secondary key?
> Prompt: *"For top-3 by value, if two tie, break ties by <name alphabetical> or <most recent>?"*

## 11. Exact output format — *prevents format_mismatch*
A bare number, a literal string template, a JSON shape, a CSV (which exact column order — match a
`sample_result.csv`?), a saved file (which name/path), or a chart (exact title/axis labels)?
> Prompt: *"Output as a single number, a sentence, or a `result.csv` matching `sample_result.csv` columns?"*

## 12. Acceptance check — *defines the rubric*
What would make the answer obviously right or wrong to you? Capture a sanity figure or a known
reference value if one exists.
> Prompt: *"Roughly what range do you expect — so we both catch a wildly wrong number?"*

---

**Discipline:** ask only what's genuinely ambiguous, ground every question in the real data, prefer
concrete either/or choices, batch them, and record every answer in the spec. Silence on an item is a
decision too — if you must assume, write the assumption down as an assumption.
