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

    def test_multi_answer_requires_all_correct(self):
        """A question with two sub-answers is only CORRECT if both match."""
        questions = [
            {"id": "q1", "question": "...", "files": [], "label": "3.5", "fmt": "stat",
             "hard": False,
             "subquestions": [{"fmt": "stat", "label": "3.5"}, {"fmt": "pval", "label": "0.01"}]},
        ]
        # solver gets both right
        solver_both = FakeSolver({"q1": {"answer": "@stat[3.5] @pval[0.01]",
                                          "input_tokens": 100, "output_tokens": 10,
                                          "wall_time_s": 1.0, "rounds": 2,
                                          "model_id": "claude-sonnet-4-6"}})
        # solver only gets first right
        solver_one = FakeSolver({"q1": {"answer": "@stat[3.5] @pval[99.0]",
                                         "input_tokens": 100, "output_tokens": 10,
                                         "wall_time_s": 1.0, "rounds": 2,
                                         "model_id": "claude-sonnet-4-6"}})
        with tempfile.TemporaryDirectory() as d:
            out1 = os.path.join(d, "r1.jsonl")
            run_variant("v", questions, solver_both, PRICES, out1)
            row_both = json.loads(open(out1).read())
            self.assertTrue(row_both["correct"])   # both sub-answers match -> CORRECT

            out2 = os.path.join(d, "r2.jsonl")
            run_variant("v", questions, solver_one, PRICES, out2)
            row_one = json.loads(open(out2).read())
            self.assertFalse(row_one["correct"])   # second sub-answer wrong -> WRONG

    def test_run_variant_raises_on_duplicate_variant(self):
        questions = [{"id": "q1", "question": "...", "files": [], "label": "42",
                      "fmt": "answer", "hard": False}]
        solver = FakeSolver({"q1": {"answer": "@answer[42]", "input_tokens": 10,
                                    "output_tokens": 5, "wall_time_s": 0.5,
                                    "rounds": 1, "model_id": "claude-sonnet-4-6"}})
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "results.jsonl")
            run_variant("ds-star", questions, solver, PRICES, out)   # first run: OK
            with self.assertRaises(ValueError):
                run_variant("ds-star", questions, solver, PRICES, out)  # second run: raises

if __name__ == "__main__":
    unittest.main()
