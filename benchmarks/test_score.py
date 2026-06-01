"""Tests for the vendored DABench deterministic scorer (benchmarks/score.py).

Run:
    cd benchmarks && python3 -m unittest test_score -v
"""
import unittest
from score import score_answer, score_fields


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

    def test_echoed_template_does_not_mask_real_answer(self):
        """Real Q0 failure: the model answers @mean_fare[34.65] but also pastes its
        script containing the literal template @mean_fare[{mean_fare}]. The unfilled
        {placeholder} token must be ignored so the real value still scores correct."""
        prediction = (
            "The mean fare is @mean_fare[34.65].\n\n"
            "```python\nprint(f\"@mean_fare[{mean_fare}]\")\n```"
        )
        self.assertTrue(score_answer(prediction, label="34.65", fmt="mean_fare"))

    def test_only_template_token_still_counts_as_wrong(self):
        """If the ONLY token is an unfilled template, there is no real answer -> wrong."""
        self.assertFalse(
            score_answer(
                prediction="print(f'@mean_fare[{mean_fare}]')",
                label="34.65",
                fmt="mean_fare",
            )
        )


class TestScoreFields(unittest.TestCase):
    """Per-field partial-credit scoring (diagnostic; strict scoring is unchanged)."""

    def test_all_fields_match_returns_full(self):
        """Every sub-field matching returns (n_total, n_total)."""
        prediction = "@stat[3.5] @pval[0.01]"
        subquestions = [{"fmt": "stat", "label": "3.5"}, {"fmt": "pval", "label": "0.01"}]
        self.assertEqual(score_fields(prediction, subquestions), (2, 2))

    def test_partial_match_returns_fraction(self):
        """Mirrors the real Q8 failure: 5 of 8 fields match exactly, 3 std-devs diverge."""
        prediction = (
            "@mean_fare_class1[87.96] @median_fare_class1[69.30] @std_dev_fare_class1[80.64] "
            "@mean_fare_class2[21.47] @median_fare_class2[15.05] @std_dev_fare_class2[13.15] "
            "@mean_fare_class3[13.23] @median_fare_class3[8.05] @std_dev_fare_class3[10.03]"
        )
        subquestions = [
            {"fmt": "mean_fare_class1", "label": "87.96"},
            {"fmt": "median_fare_class1", "label": "69.30"},
            {"fmt": "std_dev_fare_class1", "label": "80.86"},   # population vs sample std -> miss
            {"fmt": "mean_fare_class2", "label": "21.47"},
            {"fmt": "median_fare_class2", "label": "15.05"},
            {"fmt": "std_dev_fare_class2", "label": "13.19"},   # miss
            {"fmt": "mean_fare_class3", "label": "13.23"},
            {"fmt": "std_dev_fare_class3", "label": "10.04"},   # miss
        ]
        self.assertEqual(score_fields(prediction, subquestions), (5, 8))

    def test_no_fields_match_returns_zero(self):
        """No matching sub-field returns (0, n_total)."""
        prediction = "@stat[99] @pval[99]"
        subquestions = [{"fmt": "stat", "label": "3.5"}, {"fmt": "pval", "label": "0.01"}]
        self.assertEqual(score_fields(prediction, subquestions), (0, 2))

    def test_unparseable_prediction_returns_zero_matched(self):
        """Prediction with no tokens never raises; matches nothing."""
        subquestions = [{"fmt": "stat", "label": "3.5"}, {"fmt": "pval", "label": "0.01"}]
        self.assertEqual(score_fields("no tokens here", subquestions), (0, 2))


if __name__ == "__main__":
    unittest.main()
