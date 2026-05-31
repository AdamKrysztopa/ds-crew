#!/usr/bin/env python3
"""Tests for aggregate. Run from this directory:

    python3 -m unittest test_aggregate -v
"""
import unittest

from aggregate import aggregate, answers_match, cluster_results


def rec(id, answer, sufficient=True, assumptions=None):
    return {"id": id, "answer": answer, "sufficient": sufficient, "assumptions": assumptions or []}


class MatchTests(unittest.TestCase):
    def test_numeric_tolerance_matches(self):
        self.assertTrue(answers_match(41.7, 41.70001))

    def test_percent_and_number_match(self):
        self.assertTrue(answers_match("41.7%", 41.7))

    def test_distinct_numbers_do_not_match(self):
        self.assertFalse(answers_match(41.7, 39.4))

    def test_text_normalized_match(self):
        self.assertTrue(answers_match("  EUR ", "eur"))

    def test_text_mismatch(self):
        self.assertFalse(answers_match("USD", "EUR"))


class AggregateTests(unittest.TestCase):
    def test_unanimous(self):
        out = aggregate([rec("a", 41.7), rec("b", "41.70%"), rec("c", 41.700001)])
        self.assertTrue(out["unanimous"])
        self.assertEqual(out["confidence"], 1.0)
        self.assertEqual(out["n_clusters"], 1)
        self.assertEqual(out["minority_report"], [])

    def test_majority_with_minority(self):
        out = aggregate([
            rec("a", 41.7, assumptions=["refunds excluded"]),
            rec("b", 41.7, assumptions=["refunds excluded"]),
            rec("c", 39.4, assumptions=["refunds included"]),
        ])
        self.assertTrue(answers_match(out["answer"], 41.7))
        self.assertAlmostEqual(out["confidence"], round(2 / 3, 4))
        self.assertEqual(len(out["minority_report"]), 1)
        self.assertIn("refunds included", out["minority_report"][0]["assumptions"])

    def test_verified_outweighs_unverified(self):
        # two unverified agree on X (0.25 each = 0.5), one verified says Y (1.0) -> Y wins
        out = aggregate([
            rec("a", 10.0, sufficient=False),
            rec("b", 10.0, sufficient=False),
            rec("c", 20.0, sufficient=True),
        ])
        self.assertTrue(answers_match(out["answer"], 20.0))

    def test_count_breaks_weight_tie(self):
        # tie on weight (1.0 vs 1.0) -> more members wins
        out = aggregate([
            rec("a", 5.0, sufficient=False),
            rec("b", 5.0, sufficient=False),
            rec("c", 5.0, sufficient=False),  # cluster weight 0.75, 3 members
            rec("d", 9.0, sufficient=False),  # cluster weight 0.25, 1 member
        ])
        self.assertTrue(answers_match(out["answer"], 5.0))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            aggregate([])

    def test_cluster_count(self):
        clusters = cluster_results([rec("a", 1.0), rec("b", 2.0), rec("c", 1.0)])
        self.assertEqual(len(clusters), 2)

    def test_aggregate_tracks_debate_revisions(self):
        recs = [
            {"id":"s1","answer":41.7,"sufficient":True,"assumptions":[],"revised":False},
            {"id":"s2","answer":41.7,"sufficient":True,"assumptions":[],"revised":True},
            {"id":"s3","answer":39.4,"sufficient":True,"assumptions":[],"revised":False},
        ]
        out = aggregate(recs)
        self.assertEqual(out["answer"], 41.7)
        self.assertEqual(out["n_revised"], 1)

    def test_aggregate_n_revised_defaults_zero_without_debate(self):
        out = aggregate([{"id":"s1","answer":1,"sufficient":True}])
        self.assertEqual(out["n_revised"], 0)


if __name__ == "__main__":
    unittest.main()
