import json, os, tempfile, unittest
from run_manifest import build_manifest, write_manifest

class TestRunManifest(unittest.TestCase):
    def test_build_manifest_hashes_code_and_lists_inputs(self):
        m = build_manifest(
            question="q1", code="print(1)",
            inputs=["a.csv", "b.json"], answer="42",
            verdict={"score": 4}, model="claude-sonnet-4-6",
        )
        self.assertEqual(m["question"], "q1")
        self.assertEqual(sorted(m["inputs"]), ["a.csv", "b.json"])
        self.assertEqual(len(m["code_sha256"]), 64)
        self.assertEqual(m["answer"], "42")
        self.assertIn("created_utc", m)
    def test_same_code_same_hash(self):
        a = build_manifest("q", "x=1", [], None, {}, "m")
        b = build_manifest("q", "x=1", [], None, {}, "m")
        self.assertEqual(a["code_sha256"], b["code_sha256"])
    def test_write_manifest_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            p = write_manifest(build_manifest("q","c",[],"1",{},"m"), d)
            self.assertTrue(os.path.exists(p))
            self.assertEqual(json.load(open(p))["question"], "q")

    def test_build_manifest_records_usage_fields(self):
        m = build_manifest(
            question="q", code="print(1)", inputs=[], answer="1",
            verdict={"score": 4}, model="claude-sonnet-4-6",
            usage={"input_tokens": 1000, "output_tokens": 200},
            latency_s=3.5,
        )
        self.assertEqual(m["usage"]["input_tokens"], 1000)
        self.assertEqual(m["usage"]["output_tokens"], 200)
        self.assertAlmostEqual(m["latency_s"], 3.5)
        self.assertIn("cost_usd", m)
        self.assertGreater(m["cost_usd"], 0)

    def test_usage_optional_back_compat(self):
        m = build_manifest("q", "c", [], "1", {}, "m")   # old 6-arg signature
        self.assertEqual(m["usage"], {})
        self.assertIsNone(m["latency_s"])
        self.assertEqual(m["cost_usd"], 0.0)

    def test_cost_uses_model_tier_rates(self):
        from run_manifest import estimate_cost
        c = estimate_cost("claude-haiku-4-5", {"input_tokens": 1_000_000, "output_tokens": 0})
        self.assertGreater(c, 0)
        c_opus = estimate_cost("claude-opus-4-8", {"input_tokens": 1_000_000, "output_tokens": 0})
        self.assertGreater(c_opus, c)

if __name__ == "__main__":
    unittest.main()
