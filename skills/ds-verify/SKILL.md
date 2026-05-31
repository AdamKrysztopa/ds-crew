---
name: ds-verify
description: "Standalone rubric-decomposed verifier. Use this skill WHENEVER the user wants to check, verify, sanity-check, or audit an answer or number that came from anywhere ('is this result right?', 'check this answer', 'audit this number', 'verify this analysis'). Applies the DeepVerifier-style 6-item DS failure rubric (wrong column, dropped rows, units mismatch, scope error, format mismatch, question substitution) and returns a graded score 1–4 with targeted follow-up checks. Do NOT use to produce a new analysis — use ds-star-plus for that."
---

# ds-verify : independently check any answer against the DS failure rubric

## When this applies

Use ds-verify when you have an answer from **any source** (a colleague, a notebook, a prior
ds-star-plus run, a BI dashboard, a one-off query) and want it independently scored against the
six DS failure modes. The answer is already in hand — you are not producing one.

Do NOT use to produce a new analysis from scratch; use `ds-star-plus` for that.

## The cardinal rule

A **score of 4 with no rubric item marked `fail`** is the only passing grade. This is identical
to the internal gate used by `ds-star-plus`. A score of 3 with all items `pass` is NOT
sufficient — `is_sufficient()` will return `False`.

## How to run it

1. Provide the **original question** (as plain text, or point to `analysis-spec.md` if
   `ds-clarify` was used to produce one).
2. Provide the **candidate answer** plus any supporting code or data that is available.
3. Build the verifier prompt per `../ds-star-plus/references/prompts.md` (the same prompt
   template used by ds-star-plus's internal verifier role).
4. Parse the LLM response with `parse_verdict()` from
   `../ds-star-plus/scripts/verify_schema.py`.
5. Gate with `is_sufficient()` from the same module. If it returns `False`, surface the
   `checks` list (up to 3 targeted follow-up checks) and the `missing` list to the user.

## Output

A graded verdict dict:

```json
{
  "score": 1,
  "rubric": {
    "wrong_column_or_value": "pass | fail | na",
    "dropped_rows": "pass | fail | na",
    "units_mismatch": "pass | fail | na",
    "scope_error": "pass | fail | na",
    "format_mismatch": "pass | fail | na",
    "question_substitution": "pass | fail | na"
  },
  "checks": ["≤3 targeted follow-up checks"],
  "reason": "one-line explanation",
  "missing": ["gaps that would be needed to fully verify"]
}
```

Report the score, any `fail` items, the `reason`, and the `checks` to the user so they know
exactly what to fix.

## Quick reference

```python
from verify_schema import parse_verdict, is_sufficient

v = parse_verdict(llm_response_text)
if is_sufficient(v):
    print("PASS — answer is verified")
else:
    print("FAIL — score:", v["score"], "| failed items:", [k for k, val in v["rubric"].items() if val == "fail"])
    print("follow-up checks:", v["checks"])
```

- Module: `../ds-star-plus/scripts/verify_schema.py`
- Rubric reference: `../ds-star-plus/references/rubric.md`
- Verifier prompt template: `../ds-star-plus/references/prompts.md`
- Rubric items: `wrong_column_or_value`, `dropped_rows`, `units_mismatch`, `scope_error`,
  `format_mismatch`, `question_substitution`
