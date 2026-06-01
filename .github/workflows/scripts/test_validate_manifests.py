import json, os, tempfile, unittest
from validate_manifests import versions_match, load_json_or_error

class TestValidateManifests(unittest.TestCase):
    def test_versions_match_true(self):
        self.assertTrue(versions_match(["1.2.1", "1.2.1", "1.2.1"]))
    def test_versions_match_false(self):
        self.assertFalse(versions_match(["1.2.1", "1.2.0"]))
    def test_load_json_or_error_reports_bad_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            p = f.name
        obj, err = load_json_or_error(p)
        self.assertIsNone(obj)
        self.assertIn("JSON", err)
        os.unlink(p)
    def test_load_json_or_error_ok(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"version": "1.2.1"}, f)
            p = f.name
        obj, err = load_json_or_error(p)
        self.assertEqual(obj["version"], "1.2.1")
        self.assertEqual(err, "")
        os.unlink(p)

if __name__ == "__main__":
    unittest.main()
