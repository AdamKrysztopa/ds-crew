import os, tempfile, unittest
from memory_store import record, retrieve, task_signature

class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.p = os.path.join(self.d, "mem.jsonl")
    def test_record_then_retrieve_match(self):
        record(self.p, {"task_signature": "agg|pct", "data_fingerprint": "csv:1",
                        "plan": "load->groupby", "verified_code_snippet": "df.mean()",
                        "verifier_score": 4, "assumptions": ["EUR"], "outcome": "ok"})
        hits = retrieve(self.p, "agg|pct", "csv:1", k=3)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["plan"], "load->groupby")
    def test_retrieve_only_returns_verified_by_default(self):
        record(self.p, {"task_signature":"s","data_fingerprint":"f","verifier_score":2,"plan":"bad"})
        self.assertEqual(retrieve(self.p, "s", "f"), [])
    def test_retrieve_ranks_signature_match_first(self):
        record(self.p, {"task_signature":"agg|pct","data_fingerprint":"csv:1","verifier_score":4,"plan":"A"})
        record(self.p, {"task_signature":"agg|pct","data_fingerprint":"other","verifier_score":4,"plan":"B"})
        hits = retrieve(self.p, "agg|pct", "csv:1", k=2)
        self.assertEqual(hits[0]["plan"], "A")
    def test_task_signature_is_stable_and_order_insensitive(self):
        self.assertEqual(task_signature("Pct of CREDIT  txns?"), task_signature("pct of credit txns"))
    def test_missing_store_returns_empty(self):
        self.assertEqual(retrieve(os.path.join(self.d, "nope.jsonl"), "s", "f"), [])

if __name__ == "__main__":
    unittest.main()
