import unittest
from leaderboard import Leaderboard

class TestLeaderboard(unittest.TestCase):
    def test_best_respects_direction_minimize(self):
        lb = Leaderboard(metric="rmse", mode="min")
        lb.add("n1", 0.9, parent=None); lb.add("n2", 0.4, parent="n1"); lb.add("n3", 0.6, parent="n1")
        self.assertEqual(lb.best()["node"], "n2")
    def test_best_respects_direction_maximize(self):
        lb = Leaderboard(metric="auc", mode="max")
        lb.add("n1", 0.7, parent=None); lb.add("n2", 0.85, parent="n1")
        self.assertEqual(lb.best()["node"], "n2")
    def test_node_to_expand_is_current_best(self):
        lb = Leaderboard(metric="rmse", mode="min")
        lb.add("n1", 0.9, parent=None); lb.add("n2", 0.5, parent="n1")
        self.assertEqual(lb.node_to_expand(), "n2")
    def test_rejects_nan_or_missing_metric(self):
        lb = Leaderboard(metric="rmse", mode="min")
        with self.assertRaises(ValueError):
            lb.add("bad", float("nan"), parent=None)

if __name__ == "__main__":
    unittest.main()
