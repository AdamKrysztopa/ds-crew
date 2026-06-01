"""Vendored DABench deterministic scorer.

Original source:
  benchmarks/data/InfiAgent/examples/DA-Agent/eval_closed_form.py
  Copyright (c) InfiAgent (https://github.com/InfiAgent/InfiAgent)
  Licensed under Apache 2.0

Only the two scoring primitives (`extract_format` and `is_equal`) are
vendored here; the CLI / JSONL evaluation harness is intentionally omitted.
See UPSTREAM_NOTES.md for format details.
"""
import re


# ── Vendored from InfiAgent eval_closed_form.py ──────────────────────────────

def extract_format(input_string):
    """Extract all @name[value] tokens from *input_string*.

    Returns:
        answer_names : list[str]   -- the ``name`` parts
        answers      : list[str]   -- the ``value`` parts
    """
    pattern = r"@(\w+)\[(.*?)\]"
    matches = re.findall(pattern, input_string)
    answer_names = [match[0] for match in matches]
    answers = [match[1] for match in matches]
    return answer_names, answers


def is_equal(response, label):
    """Return True iff *response* equals *label* (exact or float within 1e-6)."""
    if response == label:
        return True
    else:
        try:
            return abs(float(response) - float(label)) < 1e-6
        except Exception:
            return False


# ── Public wrapper ────────────────────────────────────────────────────────────

def score_answer(prediction: str, label: str, fmt: str) -> bool:
    """Return True iff *prediction* matches *label* under the DABench scorer.

    Args:
        prediction : Raw model output text (may contain @name[value] tokens).
        label      : Ground-truth answer string (e.g. "42" or "42.0").
        fmt        : The expected answer-name key (e.g. "answer", "mean_fare").

    Returns:
        True if the ``@fmt[...]`` token is present and its value matches
        *label* via ``is_equal``; False in ALL other cases, including when
        the token is absent or the text cannot be parsed.

    Any exception is caught and converted to False — this function never raises.

    Vendored from InfiAgent/InfiAgent (eval_closed_form.py); see UPSTREAM_NOTES.md.
    """
    try:
        answer_names, answers = extract_format(prediction)
        extracted = dict(zip(answer_names, answers))
        predicted_value = extracted.get(fmt)
        if predicted_value is None:
            return False
        return bool(is_equal(predicted_value, label))
    except Exception:
        return False
