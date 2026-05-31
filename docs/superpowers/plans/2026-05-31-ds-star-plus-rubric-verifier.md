# DS-STAR+ v2.1 Rubric-Guided Verifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the `ds-star-plus` verifier from a binary `{sufficient, reason, missing}` verdict to a graded 1–4 score plus a fixed six-item DS-failure rubric and ≤3 decomposed follow-up checks, with a machine-checkable output contract.

**Architecture:** Add one stdlib-only Python module (`verify_schema.py`) that parses and validates the verifier's JSON verdict and computes sufficiency (`score == 4` AND no rubric item `fail`), tested with stdlib `unittest`. Then update the verifier prompt, the skill docs, the evidence file, the architecture table, and the eval cases to match. This is Track A1 from `ROADMAP.md`, grounded in DeepVerifier (arXiv:2601.15808).

**Tech Stack:** Python 3 standard library only (`json`, `re`, `unittest`) — no pip installs. Markdown skill files. This matches the existing repo convention (see `skills/ds-star-plus/scripts/route_model.py`, which is stdlib-only with an inline self-check).

---

## Conventions for the executor

- All paths are relative to the repo root `/Users/adamkrysztopa/projects/DS-STAR`.
- "Edit" steps give an EXACT find-text and replace-text. Match the find-text verbatim, including indentation and `>` blockquote markers.
- Python is invoked as `python3`. Tests need NO third-party packages.
- Commit after every task. Do not push until Task 8.
- If a find-text does not match exactly, STOP and re-read the file — do not guess.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `skills/ds-star-plus/references/rubric.md` | Create | Canonical six-item DS-failure rubric + verdict schema |
| `skills/ds-star-plus/scripts/verify_schema.py` | Create | Parse/validate verifier JSON; compute sufficiency |
| `skills/ds-star-plus/scripts/test_verify_schema.py` | Create | `unittest` tests for the above |
| `skills/ds-star-plus/references/prompts.md` | Modify | Replace the verifier prompt with the rubric/graded/decomposed version |
| `skills/ds-star-plus/SKILL.md` | Modify | Update change-2 section, loop step 3, quick reference |
| `skills/ds-star-plus/references/evidence.md` | Modify | Extend §2 with the DeepVerifier (2601.15808) grounding |
| `ARCHITECTURE.md` | Modify | Update the Verify row of the comparison table |
| `skills/ds-star-plus/evals/evals.json` | Modify | Add eval case 5 exercising the rubric |

---

## Task 1: Create the rubric reference doc

**Files:**
- Create: `skills/ds-star-plus/references/rubric.md`

- [ ] **Step 1: Write the file**

Create `skills/ds-star-plus/references/rubric.md` with EXACTLY this content:

````markdown
# DS-STAR+ verifier rubric (v2.1)

The verifier scores every candidate answer against these six failure modes before it may
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
    "question_substitution": "pass"
  },
  "checks": ["scope: filtered to Q4 2023 -> yes", "units: EUR as asked -> yes"],
  "reason": "Printed 1234.56 EUR is Rafa_AI's Feb-2023 total fee; matches scope, units, and 2dp format.",
  "missing": []
}
```

`scripts/verify_schema.py` parses and validates this and computes sufficiency; never hand-roll
the parse. `is_sufficient(v)` is the finalize gate: `score == 4` and no rubric item is `fail`.
````

- [ ] **Step 2: Verify the file has all six rubric keys**

Run:
```bash
python3 - <<'PY'
text = open("skills/ds-star-plus/references/rubric.md").read()
keys = ["wrong_column_or_value","dropped_rows","units_mismatch","scope_error","format_mismatch","question_substitution"]
missing = [k for k in keys if k not in text]
print("MISSING:", missing if missing else "none")
assert not missing, missing
print("OK")
PY
```
Expected: `MISSING: none` then `OK`.

- [ ] **Step 3: Commit**

```bash
git add skills/ds-star-plus/references/rubric.md
git commit -m "feat(ds-star-plus): add v2.1 verifier rubric reference"
```

---

## Task 2: Create the verdict-schema module (TDD)

**Files:**
- Create: `skills/ds-star-plus/scripts/test_verify_schema.py`
- Create: `skills/ds-star-plus/scripts/verify_schema.py`

- [ ] **Step 1: Write the failing test**

Create `skills/ds-star-plus/scripts/test_verify_schema.py` with EXACTLY this content:

```python
#!/usr/bin/env python3
"""Tests for verify_schema. Run from this directory:

    python3 -m unittest test_verify_schema -v
"""
import unittest

from verify_schema import (
    parse_verdict,
    is_sufficient,
    failed_rubric_items,
    VerdictError,
    RUBRIC_ITEMS,
)

SUFFICIENT = """{
  "score": 4,
  "rubric": {"wrong_column_or_value":"pass","dropped_rows":"pass","units_mismatch":"pass","scope_error":"pass","format_mismatch":"pass","question_substitution":"pass"},
  "checks": ["scope matches Q4 2023", "units are EUR as asked"],
  "reason": "Printed 1234.56 EUR is Rafa_AI Feb-2023 total fee; matches scope/units/2dp.",
  "missing": []
}"""


class ParseTests(unittest.TestCase):
    def test_parses_bare_json(self):
        v = parse_verdict(SUFFICIENT)
        self.assertEqual(v["score"], 4)
        self.assertEqual(set(v["rubric"]), set(RUBRIC_ITEMS))

    def test_parses_fenced_json(self):
        wrapped = "preamble\n```json\n" + SUFFICIENT + "\n```\ntrailing text"
        v = parse_verdict(wrapped)
        self.assertEqual(v["score"], 4)

    def test_empty_response_raises(self):
        with self.assertRaises(VerdictError):
            parse_verdict("")

    def test_no_json_raises(self):
        with self.assertRaises(VerdictError):
            parse_verdict("the answer looks fine to me")

    def test_bad_score_raises(self):
        with self.assertRaises(VerdictError):
            parse_verdict(SUFFICIENT.replace('"score": 4', '"score": 5'))

    def test_bad_rubric_value_raises(self):
        bad = SUFFICIENT.replace('"question_substitution":"pass"', '"question_substitution":"maybe"')
        with self.assertRaises(VerdictError):
            parse_verdict(bad)

    def test_missing_rubric_key_raises(self):
        bad = SUFFICIENT.replace('"format_mismatch":"pass",', "")
        with self.assertRaises(VerdictError):
            parse_verdict(bad)

    def test_too_many_checks_raises(self):
        bad = SUFFICIENT.replace(
            '"checks": ["scope matches Q4 2023", "units are EUR as asked"]',
            '"checks": ["a", "b", "c", "d"]',
        )
        with self.assertRaises(VerdictError):
            parse_verdict(bad)

    def test_empty_reason_raises(self):
        bad = SUFFICIENT.replace(
            '"reason": "Printed 1234.56 EUR is Rafa_AI Feb-2023 total fee; matches scope/units/2dp.",',
            '"reason": "",',
        )
        with self.assertRaises(VerdictError):
            parse_verdict(bad)


class SufficiencyTests(unittest.TestCase):
    def test_score4_no_fail_is_sufficient(self):
        self.assertTrue(is_sufficient(parse_verdict(SUFFICIENT)))

    def test_score4_with_fail_not_sufficient(self):
        v = parse_verdict(SUFFICIENT.replace('"format_mismatch":"pass"', '"format_mismatch":"fail"'))
        self.assertFalse(is_sufficient(v))
        self.assertEqual(failed_rubric_items(v), ["format_mismatch"])

    def test_score3_not_sufficient(self):
        v = parse_verdict(SUFFICIENT.replace('"score": 4', '"score": 3'))
        self.assertFalse(is_sufficient(v))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
cd skills/ds-star-plus/scripts && python3 -m unittest test_verify_schema -v; cd - >/dev/null
```
Expected: FAIL — an `ImportError` / `ModuleNotFoundError: No module named 'verify_schema'` (the module does not exist yet).

- [ ] **Step 3: Write the implementation**

Create `skills/ds-star-plus/scripts/verify_schema.py` with EXACTLY this content:

```python
#!/usr/bin/env python3
"""Validate the DS-STAR+ v2.1 structured verifier verdict.

The verifier (see references/prompts.md and references/rubric.md) must return JSON with a
graded 1-4 score, a fixed six-item rubric of the DS failure modes, up to three decomposed
follow-up checks, a one-line reason, and a list of missing gaps. This module parses that JSON
out of an LLM response and decides sufficiency, so a malformed or over-optimistic verdict
fails loudly instead of silently ending the run with a wrong answer.

    from verify_schema import parse_verdict, is_sufficient
    v = parse_verdict(llm_text)
    if is_sufficient(v):
        finalize()

Stdlib only, matching the repo convention (see route_model.py).
"""
import json
import re

# The six DS failure modes the verifier scores against (see references/rubric.md).
RUBRIC_ITEMS = (
    "wrong_column_or_value",
    "dropped_rows",
    "units_mismatch",
    "scope_error",
    "format_mismatch",
    "question_substitution",
)
RUBRIC_VALUES = ("pass", "fail", "na")


class VerdictError(ValueError):
    """Raised when a verifier response is missing or malformed."""


def _extract_json(text):
    """Return the JSON object substring from an LLM response.

    Handles a bare object, or one wrapped in a ```json ... ``` (or plain ``` ... ```) fence.
    """
    if not isinstance(text, str) or not text.strip():
        raise VerdictError("empty verifier response")
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise VerdictError("no JSON object found in verifier response")
    return candidate[start : end + 1]


def parse_verdict(text):
    """Parse and validate a verifier response into a normalized verdict dict.

    Raises VerdictError on any structural problem.
    """
    try:
        data = json.loads(_extract_json(text))
    except json.JSONDecodeError as exc:
        raise VerdictError("invalid JSON: %s" % exc) from exc
    if not isinstance(data, dict):
        raise VerdictError("verdict is not a JSON object")

    score = data.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score not in (1, 2, 3, 4):
        raise VerdictError("score must be an int 1-4, got %r" % (score,))

    rubric = data.get("rubric")
    if not isinstance(rubric, dict):
        raise VerdictError("rubric must be an object")
    normalized = {}
    for item in RUBRIC_ITEMS:
        val = rubric.get(item)
        if val not in RUBRIC_VALUES:
            raise VerdictError(
                "rubric['%s'] must be one of %s, got %r" % (item, RUBRIC_VALUES, val)
            )
        normalized[item] = val

    checks = data.get("checks", [])
    if not isinstance(checks, list) or len(checks) > 3:
        raise VerdictError("checks must be a list of at most 3 items")

    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise VerdictError("reason must be a non-empty string")

    missing = data.get("missing", [])
    if not isinstance(missing, list):
        raise VerdictError("missing must be a list")

    return {
        "score": score,
        "rubric": normalized,
        "checks": [str(c) for c in checks],
        "reason": reason.strip(),
        "missing": [str(m) for m in missing],
    }


def failed_rubric_items(verdict):
    """List rubric item names whose value is 'fail'."""
    return [k for k, v in verdict["rubric"].items() if v == "fail"]


def is_sufficient(verdict):
    """Sufficient only when score is a confident 4 AND no rubric item failed.

    This is the early-stop / finalize gate. A high score with any failed rubric item is NOT
    sufficient — the failed item is the gap to fix.
    """
    return verdict["score"] == 4 and not failed_rubric_items(verdict)


if __name__ == "__main__":
    _demo = (
        '{"score":4,"rubric":{"wrong_column_or_value":"pass","dropped_rows":"pass",'
        '"units_mismatch":"pass","scope_error":"pass","format_mismatch":"pass",'
        '"question_substitution":"pass"},"checks":["scope ok"],'
        '"reason":"value matches the asked scope/units/format","missing":[]}'
    )
    _v = parse_verdict(_demo)
    print("parsed:", _v)
    print("sufficient:", is_sufficient(_v))
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
cd skills/ds-star-plus/scripts && python3 -m unittest test_verify_schema -v; cd - >/dev/null
```
Expected: PASS — `Ran 11 tests` ending in `OK`.

- [ ] **Step 5: Run the module self-check**

Run:
```bash
python3 skills/ds-star-plus/scripts/verify_schema.py
```
Expected: prints a `parsed: {...}` line and `sufficient: True`.

- [ ] **Step 6: Commit**

```bash
git add skills/ds-star-plus/scripts/verify_schema.py skills/ds-star-plus/scripts/test_verify_schema.py
git commit -m "feat(ds-star-plus): add verdict schema validator with unittest"
```

---

## Task 3: Replace the verifier prompt

**Files:**
- Modify: `skills/ds-star-plus/references/prompts.md`

- [ ] **Step 1: Replace the verifier prompt block**

In `skills/ds-star-plus/references/prompts.md`, find this EXACT text:

````text
## Verifier — Opus (3x majority on borderline/high-stakes)

> You are a strict reviewer. Decide whether the current plan + code + ACTUAL execution result
> answers the question — including correct scope, units, and required format. Code running is
> NOT sufficient.
> Plan: `{steps}`   Code: ```{code}```   Execution result: `{result}`   Question: `{question}`
> Return JSON only:
> `{"sufficient": true|false, "reason": "<one line tying the printed output to the exact question, or why not>", "missing": ["<gap>", ...]}`
> If sufficient, `reason` must name the output value and confirm it matches the question's
> scope/units/format; if you cannot, it is NOT sufficient.
````

Replace it with this EXACT text:

````text
## Verifier — Opus (3x majority on borderline/high-stakes)

> You are a strict reviewer. Decide whether the current plan + code + ACTUAL execution result
> answers the question — including correct scope, units, and required format. Code running is
> NOT sufficient.
> Plan: `{steps}`   Code: ```{code}```   Execution result: `{result}`   Question: `{question}`
>
> 1. Score the answer against the six DS failure modes (see `rubric.md`):
>    wrong_column_or_value, dropped_rows, units_mismatch, scope_error, format_mismatch,
>    question_substitution. Mark each `pass`, `fail`, or `na`.
> 2. Write up to THREE targeted follow-up checks that most threaten THIS answer
>    (e.g. "does the printed scope match the asked time window?") and answer each inline.
> 3. Give a graded score: 1 = clearly wrong, 2 = mostly wrong, 3 = mostly right,
>    4 = clearly sufficient. The answer is sufficient ONLY if score == 4 AND no rubric item
>    is `fail`. Every `fail` item must also appear as a `missing` gap.
> Return JSON only:
> `{"score": 1|2|3|4, "rubric": {"wrong_column_or_value":"pass|fail|na","dropped_rows":"pass|fail|na","units_mismatch":"pass|fail|na","scope_error":"pass|fail|na","format_mismatch":"pass|fail|na","question_substitution":"pass|fail|na"}, "checks": ["<question -> answer>", ...], "reason": "<one line tying the printed output to the exact question, or why not>", "missing": ["<gap>", ...]}`
> If score is 4, `reason` must name the output value and confirm it matches the question's
> scope/units/format; if you cannot, it is NOT sufficient.
> `scripts/verify_schema.py` validates this JSON and computes sufficiency — do not hand-roll it.
````

- [ ] **Step 2: Verify the new schema is present and the old one is gone**

Run:
```bash
python3 - <<'PY'
t = open("skills/ds-star-plus/references/prompts.md").read()
assert '"score": 1|2|3|4' in t, "new graded schema missing"
assert '"sufficient": true|false' not in t, "old binary schema still present"
assert "rubric.md" in t, "rubric reference missing"
print("OK")
PY
```
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add skills/ds-star-plus/references/prompts.md
git commit -m "feat(ds-star-plus): rubric-guided graded verifier prompt"
```

---

## Task 4: Update SKILL.md (verifier section, loop step, quick reference)

**Files:**
- Modify: `skills/ds-star-plus/SKILL.md`

- [ ] **Step 1: Update the verifier change-section**

In `skills/ds-star-plus/SKILL.md`, find this EXACT text:

```text
### 2. Verifier returns a verdict AND a rationale AND what's missing

In v1 the judge says only Yes/No. That makes false "sufficient" both common and silent. In
v2 the verifier must return a small structured verdict: `sufficient` (bool), `reason` (one
line), and `missing` (a list of what still needs to happen if not sufficient). Two payoffs:
```

Replace it with this EXACT text:

```text
### 2. Verifier returns a graded score, a rubric, a rationale AND what's missing

In v1 the judge says only Yes/No. That makes false "sufficient" both common and silent. v2.1
makes the verdict structured and graded: a `score` (1–4), a fixed six-item `rubric` of the DS
failure modes each marked pass/fail/na (see `references/rubric.md`), up to three decomposed
`checks`, a one-line `reason`, and `missing` (what still needs to happen). The answer is
sufficient ONLY when `score == 4` and no rubric item is `fail`. `scripts/verify_schema.py`
parses and enforces this contract. Three payoffs:
```

- [ ] **Step 2: Update the loop step 3**

In `skills/ds-star-plus/SKILL.md`, find this EXACT text:

```text
3. **Verify** (Opus): get `{sufficient, reason, missing}`. Borderline/high-stakes → 3x vote.
   Sufficient → Stage 5.
```

Replace it with this EXACT text:

```text
3. **Verify** (Opus): get `{score, rubric, checks, reason, missing}` (validate with
   `scripts/verify_schema.py`). Borderline/high-stakes → 3x vote. `score == 4` and no rubric
   `fail` → Stage 5.
```

- [ ] **Step 3: Update the quick reference**

In `skills/ds-star-plus/SKILL.md`, find this EXACT text:

```text
Upgraded role prompts (structured verifier, anti-repeat planner): `references/prompts.md`.
Worked trace with backtracking: `references/worked_example.md`.
Routing helper: `scripts/route_model.py`. File describer: `scripts/analyze_file.py`.
Test cases: `evals/evals.json`.
```

Replace it with this EXACT text:

```text
Upgraded role prompts (structured verifier, anti-repeat planner): `references/prompts.md`.
Verifier rubric (the six DS failure modes): `references/rubric.md`.
Worked trace with backtracking: `references/worked_example.md`.
Routing helper: `scripts/route_model.py`. File describer: `scripts/analyze_file.py`.
Verdict validator: `scripts/verify_schema.py`. Test cases: `evals/evals.json`.
```

- [ ] **Step 4: Verify all three edits landed**

Run:
```bash
python3 - <<'PY'
t = open("skills/ds-star-plus/SKILL.md").read()
assert "graded score, a rubric" in t, "section 2 heading not updated"
assert "{score, rubric, checks, reason, missing}" in t, "loop step 3 not updated"
assert "references/rubric.md" in t, "rubric not in quick reference"
assert "scripts/verify_schema.py" in t, "validator not in quick reference"
print("OK")
PY
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/ds-star-plus/SKILL.md
git commit -m "docs(ds-star-plus): describe graded rubric verifier in SKILL.md"
```

---

## Task 5: Extend evidence.md §2 with the DeepVerifier grounding

**Files:**
- Modify: `skills/ds-star-plus/references/evidence.md`

- [ ] **Step 1: Append the v2.1 grounding paragraph to §2**

In `skills/ds-star-plus/references/evidence.md`, find this EXACT text:

```text
self-consistency as the tool for high-stakes judgements — it lists *"self-consistency"* among the
techniques that harden multi-step pipelines in the Text-to-SQL related work (§2). v2 applies it
to the one decision that can silently end the run: **3× majority vote on borderline verdicts.**
```

Replace it with this EXACT text:

```text
self-consistency as the tool for high-stakes judgements — it lists *"self-consistency"* among the
techniques that harden multi-step pipelines in the Text-to-SQL related work (§2). v2 applies it
to the one decision that can silently end the run: **3× majority vote on borderline verdicts.**

**v2.1 extension (DeepVerifier, [2601.15808](https://arxiv.org/abs/2601.15808)).** DeepVerifier
shows the binary judge is the weak link and replaces it with a rubric-guided, *decomposed*
verifier: failures are pre-classified into a fixed taxonomy, verification is split into a few
targeted follow-up checks rather than one holistic call, and the verdict is graded. It beats a
vanilla LLM-judge by **12–48% F1**, lifting recall of catching wrong answers from **14% → 71%**
(their GAIA-Web ablation) — with no training and at modest cost (decomposition stays to ≤3 checks).
v2.1 ports this: a six-item DS-failure rubric (`references/rubric.md`), ≤3 decomposed `checks`, and
a graded 1–4 `score` where sufficiency requires `score == 4` with no rubric `fail`. The contract is
enforced by `scripts/verify_schema.py` so a malformed or over-optimistic verdict fails loudly.
```

- [ ] **Step 2: Verify the addition**

Run:
```bash
python3 - <<'PY'
t = open("skills/ds-star-plus/references/evidence.md").read()
assert "2601.15808" in t, "DeepVerifier citation missing"
assert "14% → 71%" in t, "recall figure missing"
print("OK")
PY
```
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add skills/ds-star-plus/references/evidence.md
git commit -m "docs(ds-star-plus): ground v2.1 verifier in DeepVerifier evidence"
```

---

## Task 6: Update the ARCHITECTURE.md comparison table

**Files:**
- Modify: `ARCHITECTURE.md`

- [ ] **Step 1: Update the Verify row**

In `ARCHITECTURE.md`, find this EXACT text:

```text
| Verify | one model, **Yes/No** | **Opus**, returns `{sufficient, reason, missing}`; **3x vote** on borderline |
```

Replace it with this EXACT text:

```text
| Verify | one model, **Yes/No** | **Opus**, returns graded `{score 1–4, rubric, checks, reason, missing}` (v2.1); sufficient iff `score 4` & no rubric `fail`; **3x vote** on borderline |
```

- [ ] **Step 2: Verify the edit**

Run:
```bash
python3 - <<'PY'
t = open("ARCHITECTURE.md").read()
assert "score 1–4, rubric, checks" in t, "verify row not updated"
print("OK")
PY
```
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add ARCHITECTURE.md
git commit -m "docs: update architecture table for graded rubric verifier"
```

---

## Task 7: Add an eval case that exercises the rubric

**Files:**
- Modify: `skills/ds-star-plus/evals/evals.json`

- [ ] **Step 1: Add eval case 5**

In `skills/ds-star-plus/evals/evals.json`, find this EXACT text:

```text
      "files": ["sales.csv"]
    }
  ]
}
```

Replace it with this EXACT text:

```text
      "files": ["sales.csv"]
    },
    {
      "id": 5,
      "name": "rubric-units-and-format",
      "prompt": "From transactions.csv, what fraction of total revenue came from credit cards? Report as a percentage rounded to one decimal place.",
      "expected_output": "A percentage (not a 0-1 fraction) rounded to exactly one decimal, e.g. 41.7, derived only from transactions.csv.",
      "assertions": [
        "Verifier marks units_mismatch=pass only if the answer is a percentage, not a 0-1 fraction",
        "Verifier marks format_mismatch=pass only if the value has exactly one decimal place",
        "Final score is 4 with no rubric item failing before the answer is reported",
        "Computation uses only transactions.csv (no fabricated columns)"
      ],
      "files": ["transactions.csv"]
    }
  ]
}
```

- [ ] **Step 2: Verify the JSON still parses and has 5 cases**

Run:
```bash
python3 - <<'PY'
import json
d = json.load(open("skills/ds-star-plus/evals/evals.json"))
assert len(d["evals"]) == 5, len(d["evals"])
assert d["evals"][-1]["id"] == 5
print("OK", len(d["evals"]), "cases")
PY
```
Expected: `OK 5 cases`.

- [ ] **Step 3: Commit**

```bash
git add skills/ds-star-plus/evals/evals.json
git commit -m "test(ds-star-plus): add eval case exercising verifier rubric"
```

---

## Task 8: Full validation and push

**Files:** none (verification only)

- [ ] **Step 1: Re-run the unit tests**

Run:
```bash
cd skills/ds-star-plus/scripts && python3 -m unittest test_verify_schema -v; cd - >/dev/null
```
Expected: `Ran 11 tests` … `OK`.

- [ ] **Step 2: Re-run both script self-checks**

Run:
```bash
python3 skills/ds-star-plus/scripts/verify_schema.py && python3 skills/ds-star-plus/scripts/route_model.py
```
Expected: the verify_schema demo line + `sufficient: True`, then `route_model` prints `ALL PASS`.

- [ ] **Step 3: Validate every JSON file in the skill**

Run:
```bash
python3 - <<'PY'
import json, glob
for f in glob.glob("skills/ds-star-plus/**/*.json", recursive=True) + glob.glob(".claude-plugin/*.json"):
    json.load(open(f)); print("ok", f)
PY
```
Expected: an `ok <path>` line for each JSON file, no traceback.

- [ ] **Step 4: Confirm a clean tree and push**

Run:
```bash
git status --short
git push origin main
```
Expected: `git status --short` prints nothing (all committed); push succeeds.

---

## Self-Review (completed during planning)

**Spec coverage (ROADMAP A1):**
- "Fixed DS-failure rubric (6 items)" → Task 1 (rubric.md) + Task 2 (`RUBRIC_ITEMS`).
- "Decomposition into ≤3 targeted checks" → Task 3 prompt + Task 2 (`checks` length ≤ 3 enforced).
- "Graded 1–4 verdict with early-stop" → Task 2 (`is_sufficient` = score 4 & no fail) + Task 4 loop step.
- "Files: prompts.md, SKILL.md, evidence.md entry citing 2601.15808, evals.json" → Tasks 3, 4, 5, 7. (Plus ARCHITECTURE.md, Task 6, for doc consistency.)

**Placeholder scan:** No TBD/TODO; every code and edit step shows full content. Tests contain real assertions.

**Type/name consistency:** `RUBRIC_ITEMS`, `parse_verdict`, `is_sufficient`, `failed_rubric_items`, `VerdictError` are defined in Task 2's `verify_schema.py` and imported with those exact names in Task 2's test. The verdict keys `score`/`rubric`/`checks`/`reason`/`missing` are identical across rubric.md (Task 1), the prompt (Task 3), SKILL.md (Task 4), and the validator (Task 2). The six rubric keys are byte-identical in rubric.md, the prompt, and `RUBRIC_ITEMS`.

**Out of scope (own plans later):** B1 `ds-clarify`, D `ds-spike`, C repo rename, A2 MCTS search mode.
