import json, os, tempfile, unittest
from runner import run_variant
from solvers import FakeSolver

PRICES = {"claude-sonnet-4-6": {"input": 3.0, "output": 15.0}}

class TestRunner(unittest.TestCase):
    def test_run_variant_writes_one_row_per_question(self):
        questions = [
            {"id": "q1", "question": "...", "files": [], "label": "42",
             "fmt": "answer", "hard": False},
            {"id": "q2", "question": "...", "files": [], "label": "7",
             "fmt": "answer", "hard": True},
        ]
        solver = FakeSolver({
            "q1": {"answer": "@answer[42]", "input_tokens": 100, "output_tokens": 10,
                   "wall_time_s": 1.0, "rounds": 2, "model_id": "claude-sonnet-4-6"},
            "q2": {"answer": "@answer[8]", "input_tokens": 200, "output_tokens": 20,
                   "wall_time_s": 1.5, "rounds": 3, "model_id": "claude-sonnet-4-6"},
        })
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "results.jsonl")
            run_variant("ds-star-plus", questions, solver, PRICES, out)
            rows = [json.loads(l) for l in open(out)]
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["variant"] for r in rows}, {"ds-star-plus"})
        by = {r["question_id"]: r for r in rows}
        self.assertTrue(by["q1"]["correct"])     # @answer[42] extracts "42" == label "42"
        self.assertFalse(by["q2"]["correct"])    # @answer[8] extracts "8" != label "7"
        self.assertIn("cost_usd", by["q1"])
        self.assertIn("input_tokens", by["q1"])

if __name__ == "__main__":
    unittest.main()
