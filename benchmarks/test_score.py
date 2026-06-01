"""Tests for the vendored DABench deterministic scorer (benchmarks/score.py).

Run:
    cd benchmarks && python3 -m unittest test_score -v
"""
import unittest
from score import score_answer


class TestScore(unittest.TestCase):

    def test_correct_closed_form_matches(self):
        """Exact string match: @answer[42] vs label '42' should be True."""
        self.assertTrue(
            score_answer(
                prediction="@answer[42]",
                label="42",
                fmt="answer",
            )
        )

    def test_wrong_value_is_incorrect(self):
        """Different value: @answer[99] vs label '42' should be False."""
        self.assertFalse(
            score_answer(
                prediction="@answer[99]",
                label="42",
                fmt="answer",
            )
        )

    def test_format_parse_failure_counts_as_wrong(self):
        """Unparseable prediction (no @name[value] token) must return False, never raise."""
        self.assertFalse(
            score_answer(
                prediction="I think it is about forty-two",
                label="42",
                fmt="answer",
            )
        )

    def test_float_comparison_within_tolerance(self):
        """is_equal uses abs(float(a)-float(b)) < 1e-6 for numeric comparison."""
        # Exact float string match
        self.assertTrue(
            score_answer(
                prediction="@mean_fare[42.0]",
                label="42.0",
                fmt="mean_fare",
            )
        )
        # Near-equal within 1e-6 tolerance
        self.assertTrue(
            score_answer(
                prediction="@mean_fare[42.0000005]",
                label="42.0",
                fmt="mean_fare",
            )
        )
        # Outside 1e-6 tolerance must be False
        self.assertFalse(
            score_answer(
                prediction="@mean_fare[42.001]",
                label="42.0",
                fmt="mean_fare",
            )
        )

    def test_wrong_field_name_counts_as_wrong(self):
        """If the fmt key is absent from the prediction, score must be False."""
        self.assertFalse(
            score_answer(
                prediction="@other_field[42]",
                label="42",
                fmt="answer",
            )
        )

    def test_empty_prediction_counts_as_wrong(self):
        """Empty string prediction must return False, never raise."""
        self.assertFalse(
            score_answer(
                prediction="",
                label="42",
                fmt="answer",
            )
        )


if __name__ == "__main__":
    unittest.main()
