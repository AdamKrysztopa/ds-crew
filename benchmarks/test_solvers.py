import unittest
from solvers import FakeSolver, compute_cost, summarize_spike

PRICES = {  # input,output USD per Mtok — mirrors config/models.json
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}

class TestSolvers(unittest.TestCase):
    def test_fake_solver_returns_canned_result(self):
        s = FakeSolver({"q1": {"answer": "@answer[42]", "input_tokens": 1000,
                               "output_tokens": 200, "wall_time_s": 1.0, "rounds": 3}})
        r = s.solve("q1", question="...", files=[])
        self.assertEqual(r["answer"], "@answer[42]")
        self.assertEqual(r["rounds"], 3)

    def test_compute_cost_uses_prices(self):
        c = compute_cost("claude-sonnet-4-6",
                         {"input_tokens": 1_000_000, "output_tokens": 0}, PRICES)
        self.assertAlmostEqual(c, 3.0)

    def test_compute_cost_unknown_model_returns_zero(self):
        c = compute_cost("unknown-model", {"input_tokens": 1_000_000, "output_tokens": 0}, PRICES)
        self.assertEqual(c, 0.0)

    def test_spike_sums_all_subrun_tokens_and_cost(self):
        subruns = [
            {"answer": "@answer[42]", "input_tokens": 1000, "output_tokens": 100,
             "wall_time_s": 2.0, "rounds": 3, "model_id": "claude-sonnet-4-6"},
            {"answer": "@answer[42]", "input_tokens": 2000, "output_tokens": 300,
             "wall_time_s": 3.0, "rounds": 4, "model_id": "claude-sonnet-4-6"},
        ]
        agg = summarize_spike(subruns, consensus="@answer[42]", prices=PRICES)
        self.assertEqual(agg["input_tokens"], 3000)   # SUM, not max/avg
        self.assertEqual(agg["output_tokens"], 400)
        self.assertAlmostEqual(agg["cost_usd"], (3000/1e6)*3.0 + (400/1e6)*15.0)
        self.assertEqual(agg["wall_time_s"], 3.0)      # parallel -> max wall time
        self.assertEqual(agg["rounds"], 4)             # max rounds
        self.assertEqual(agg["answer"], "@answer[42]")
        self.assertEqual(agg["n_subruns"], 2)

if __name__ == "__main__":
    unittest.main()
