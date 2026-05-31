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
