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

if __name__ == "__main__":
    unittest.main()
