#!/usr/bin/env python3
"""Validate the DS-STAR+ v2.2 structured verifier verdict.

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

# The seven DS failure modes the verifier scores against (see references/rubric.md).
RUBRIC_ITEMS = (
    "wrong_column_or_value",
    "dropped_rows",
    "units_mismatch",
    "scope_error",
    "format_mismatch",
    "question_substitution",
    "format_token_missing",  # v2.2: @key[value] token absent or contains placeholder name
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


def check_format_tokens(answer, format_str):
    """Programmatic pre-check for @key[value] token correctness.

    Runs before the LLM verifier as a fast, deterministic gate. Returns a list of
    problem descriptions (empty = all tokens look good).

    Checks:
    - Every key named in format_str appears as @key[...] in answer
    - No bracket contains only word characters (placeholder name, not a number/string)

    Args:
        answer:     The model's final answer text.
        format_str: The required format spec, e.g. '@mean_fare[mean_fare_value] ...'

    Returns:
        List of problem strings. Empty list means no detected token problems.
    """
    if not format_str:
        return []

    # Extract expected keys from the format spec
    expected_keys = re.findall(r"@(\w+)\[", format_str)
    if not expected_keys:
        return []

    # Extract tokens present in the answer
    present = {name: val for name, val in re.findall(r"@(\w+)\[(.*?)\]", answer)}

    # Build set of placeholder names from format spec (e.g. "mean_fare_value" in @mean_fare[mean_fare_value])
    placeholders = set(re.findall(r"@\w+\[(\w+)\]", format_str))

    problems = []
    for key in expected_keys:
        if key not in present:
            problems.append(f"missing token: @{key}[...] not found in answer")
        else:
            val = present[key].strip()
            # Flag only if the value is one of the known placeholder names from the spec
            if val in placeholders:
                problems.append(
                    f"placeholder in token: @{key}[{val}] — "
                    f"'{val}' is the format spec placeholder, not a computed value"
                )

    return problems


if __name__ == "__main__":
    _demo = (
        '{"score":4,"rubric":{"wrong_column_or_value":"pass","dropped_rows":"pass",'
        '"units_mismatch":"pass","scope_error":"pass","format_mismatch":"pass",'
        '"question_substitution":"pass","format_token_missing":"na"},"checks":["scope ok"],'
        '"reason":"value matches the asked scope/units/format","missing":[]}'
    )
    _v = parse_verdict(_demo)
    print("parsed:", _v)
    print("sufficient:", is_sufficient(_v))

    # Demo check_format_tokens
    _fmt = "@mean_fare[mean_fare_value] @count[count_value]"
    print("\nformat token check (good):",
          check_format_tokens("@mean_fare[34.65] @count[715]", _fmt))
    print("format token check (placeholder):",
          check_format_tokens("@mean_fare[mean_fare_value] @count[715]", _fmt))
    print("format token check (missing):",
          check_format_tokens("The mean fare is 34.65", _fmt))
