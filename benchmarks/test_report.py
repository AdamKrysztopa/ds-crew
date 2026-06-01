import json, unittest
from report import summarize, render_summary_md, build_manifest

ROWS = [
    {"variant": "ds-star", "question_id": "q1", "hard": False, "correct": True,
     "field_score": 1.0, "fields_matched": 1, "fields_total": 1,
     "input_tokens": 100, "output_tokens": 10, "cost_usd": 0.001, "wall_time_s": 1.0, "rounds": 2},
    {"variant": "ds-star", "question_id": "q2", "hard": True, "correct": False,
     "field_score": 0.625, "fields_matched": 5, "fields_total": 8,
     "input_tokens": 300, "output_tokens": 30, "cost_usd": 0.003, "wall_time_s": 2.0, "rounds": 4},
]

class TestReport(unittest.TestCase):
    def test_summarize_computes_accuracy_and_per_task(self):
        s = summarize(ROWS)["ds-star"]
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["accuracy"], 0.5)        # 1 of 2 strict
        self.assertAlmostEqual(s["accuracy_hard"], 0.0)   # 0 of 1 hard
        self.assertAlmostEqual(s["cost_per_task"], 0.002) # (0.001+0.003)/2
        self.assertAlmostEqual(s["tokens_per_task"], 220) # (110+330)/2
        self.assertEqual(s["median_rounds"], 3)           # median(2,4)

    def test_summarize_computes_mean_field_score(self):
        """Mean per-field credit sits beside strict accuracy as a diagnostic."""
        s = summarize(ROWS)["ds-star"]
        self.assertAlmostEqual(s["mean_field_score"], 0.8125)  # (1.0 + 0.625)/2

    def test_summarize_field_score_defaults_for_legacy_rows(self):
        """Rows from older runs without field_score fall back to strict correctness."""
        legacy = [
            {"variant": "old", "question_id": "q1", "hard": False, "correct": True,
             "input_tokens": 1, "output_tokens": 1, "cost_usd": 0.0, "wall_time_s": 1.0, "rounds": 1},
            {"variant": "old", "question_id": "q2", "hard": False, "correct": False,
             "input_tokens": 1, "output_tokens": 1, "cost_usd": 0.0, "wall_time_s": 1.0, "rounds": 1},
        ]
        self.assertAlmostEqual(summarize(legacy)["old"]["mean_field_score"], 0.5)

    def test_render_summary_md_has_table_header(self):
        md = render_summary_md(summarize(ROWS))
        self.assertIn("| variant | n | accuracy | accuracy-hard | field-score | $/task | tokens/task | median rounds |", md)
        self.assertIn("ds-star", md)

    def test_manifest_has_required_keys(self):
        m = build_manifest(commit_sha="abc123", model_ids={"ds-star": "claude-sonnet-4-6"},
                           prices={"claude-sonnet-4-6": {"input": 3.0, "output": 15.0}},
                           n=2, seed=0)
        for k in ("commit_sha", "model_ids", "prices", "date", "n", "seed"):
            self.assertIn(k, m)

if __name__ == "__main__":
    unittest.main()
