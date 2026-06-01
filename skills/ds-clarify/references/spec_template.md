# Analysis spec — <one-line question restated>

> Written by `ds-clarify`. The downstream `ds-star` / `ds-star-plus` run reads this and the
> verifier checks the final answer against the **Acceptance** and **Output format** sections.
> Fill every field. Mark anything the user left to agent judgement as `(assumed)`.

## Question (verbatim)
<paste the user's exact request>

## Data files in scope
- `data/<file>` — <one-line role>

## Resolved decisions
| dimension | decision | source |
|-----------|----------|--------|
| Metric definition | <e.g. revenue = net of discount, excl. refunds> | user / (assumed) |
| Population / scope | <e.g. all merchants in region EU> | user / (assumed) |
| Time window + timezone | <e.g. 2023-10-01 .. 2023-12-31 inclusive, Europe/Warsaw> | user / (assumed) |
| Filters & category values | <e.g. card_scheme == 'NexPay'> | user / (assumed) |
| Null / sentinel handling | <e.g. drop rows with null amount (~3%)> | user / (assumed) |
| Duplicates / dedup key | <e.g. order_id unique; no dedup> | user / (assumed) |
| Outlier policy | <e.g. keep all> | user / (assumed) |
| Units & scale | <e.g. EUR; answer as percentage 0–100> | user / (assumed) |
| Rounding / precision | <e.g. 1 decimal place, round half-up> | user / (assumed) |
| Tie-breaking / ordering | <e.g. ties broken alphabetically by name> | user / (assumed) |

## Output format
<exact shape: a bare number / a string template / JSON shape / CSV with columns [a,b,c] in this
order matching sample_result.csv / file saved to data/result.csv / chart titled "..." with axes ...>

## Acceptance
- Sanity range / known reference: <e.g. expect 30–50%>
- The answer is correct iff: <the concrete success condition>

## Stated assumptions (agent judgement)
- <anything not explicitly decided by the user, recorded so it is never silent>
