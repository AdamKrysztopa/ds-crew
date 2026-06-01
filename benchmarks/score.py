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
        # Drop unfilled template placeholders, e.g. an echoed code line
        # `print(f"@mean_fare[{mean_fare}]")` emits @mean_fare[{mean_fare}].
        # A value containing braces is never a real DABench answer; ignoring it
        # stops the echoed template from masking the model's actual answer.
        pairs = [(n, v) for n, v in zip(answer_names, answers)
                 if "{" not in v and "}" not in v]
        extracted = dict(pairs)
        predicted_value = extracted.get(fmt)
        if predicted_value is None:
            return False
        return bool(is_equal(predicted_value, label))
    except Exception:
        return False


def score_fields(prediction: str, subquestions) -> tuple:
    """Per-field partial credit: how many sub-fields match, out of how many.

    DIAGNOSTIC ONLY — this does not change the strict, DABench-faithful
    ``score_answer`` metric (exact 1e-6 match, all-or-nothing per question).
    It exists to distinguish "nearly right" answers (e.g. 5/8 fields exact,
    3 std-devs off only by a population-vs-sample ddof convention) from answers
    that are genuinely wrong.

    Args:
        prediction   : Raw model output text (may contain @name[value] tokens).
        subquestions : Iterable of {"fmt": name, "label": value} dicts.

    Returns:
        (n_matched, n_total). Never raises; an unparseable prediction yields
        (0, n_total).
    """
    subs = list(subquestions)
    matched = sum(1 for sq in subs if score_answer(prediction, sq["label"], sq["fmt"]))
    return matched, len(subs)
