# DS-STAR+ verifier rubric (v2.2)

The verifier scores every candidate answer against these seven failure modes before it may
return a sufficient (score 4) verdict. Each is marked `pass` (clearly clear of this failure),
`fail` (the answer commits it), or `na` (the failure cannot apply to this question). The answer
is sufficient ONLY when the score is 4 AND no item is `fail`.

Adapted from DeepVerifier's failure-taxonomy-to-rubric idea (arXiv:2601.15808) to the data
science domain — see `evidence.md` §2.

| key | failure mode | fail example | pass example |
|-----|--------------|--------------|--------------|
| `wrong_column_or_value` | filters/aggregates on a column or category value that does not exist, or invents one | groups by `payment_gateway` when no such column exists | uses `card_scheme`, confirmed present in the file description |
| `dropped_rows` | silently loses rows (a bad join, a filter returning 0, an unhandled NaN/sentinel) without acknowledging it | inner-join drops unmatched merchants and the count silently halves | join verified to retain the expected row count, or the drop is intended and stated |
| `units_mismatch` | the number is in the wrong unit/scale (cents vs euros, fraction vs percent, basis points) | reports 0.6341 when a percentage was asked (should be 63.41) | reports 63.41% with the unit explicit |
| `scope_error` | wrong slice: wrong time window, entity, category, or timezone | sums all of 2023 when only Q4 was asked | filtered to day_of_year >= 274 for Q4 2023, matching the asked window |
| `format_mismatch` | right value, wrong reported shape: rounding, column order, file name, JSON shape, chart labels | prints 63.4 when two decimals were asked | matches the requested precision / exact column order / required path |
| `question_substitution` | answers a different (often easier) question than the one asked | gives a single global average when a per-country average was asked | returns the per-country top-3 exactly as asked |
| `format_token_missing` | a required `@key[value]` output token is absent, or its bracket contains a placeholder name instead of a computed value | `@mean[mean]` (placeholder literal) or answer is a table with no tokens at all | `@mean[34.65]` present with the actual computed value; all required tokens present |

## Verdict schema

The verifier returns JSON shaped like:

```json
{
  "score": 4,
  "rubric": {
    "wrong_column_or_value": "pass",
    "dropped_rows": "pass",
    "units_mismatch": "pass",
    "scope_error": "pass",
    "format_mismatch": "pass",
    "question_substitution": "pass",
    "format_token_missing": "na"
  },
  "checks": ["scope: filtered to Q4 2023 -> yes", "units: EUR as asked -> yes"],
  "reason": "Printed 1234.56 EUR is Rafa_AI's Feb-2023 total fee; matches scope, units, and 2dp format.",
  "missing": []
}
```

`scripts/verify_schema.py` parses and validates this and computes sufficiency; never hand-roll
the parse. `is_sufficient(v)` is the finalize gate: `score == 4` and no rubric item is `fail`.
