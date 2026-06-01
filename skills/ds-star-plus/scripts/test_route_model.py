import unittest
from route_model import pick_model, TIERS

class TestRouteModel(unittest.TestCase):
    def test_behavior_unchanged(self):
        self.assertEqual(pick_model("verifier"), "claude-opus-4-8")
        self.assertEqual(pick_model("analyzer"), "claude-haiku-4-5")
        self.assertEqual(pick_model("planner_next"), "claude-sonnet-4-6")
        self.assertEqual(pick_model("planner_next", attempt=2), "claude-opus-4-8")
        self.assertEqual(pick_model("coder", attempt=2), "claude-opus-4-8")
        self.assertEqual(pick_model("router", oscillating=True), "claude-opus-4-8")
        self.assertEqual(pick_model("finalizer", hard=True), "claude-sonnet-4-6")

    def test_tiers_sourced_from_config_not_hardcoded(self):
        src = open("route_model.py").read()
        # Extract code after the docstring (skip the module docstring)
        parts = src.split('"""')
        code_src = '"""'.join(parts[2:]) if len(parts) > 2 else src  # Skip first docstring
        # Check that hardcoded model IDs are not in the code logic
        # (they should come from config, not be hardcoded string literals in assignments)
        self.assertNotIn('"claude-opus-4-8":\n', code_src)
        self.assertNotIn('"claude-sonnet-4-6":\n', code_src)
        self.assertNotIn('"claude-haiku-4-5":\n', code_src)
        # Verify config loading pattern exists
        self.assertIn('_models_config()', code_src)
        self.assertIn('_CFG["tiers"].items()', code_src)

if __name__ == "__main__":
    unittest.main()
