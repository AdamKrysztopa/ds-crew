import json, subprocess, sys, unittest
from models import load, tier_id, all_prices, price

class TestModels(unittest.TestCase):
    def test_tier_id_resolves(self):
        self.assertEqual(tier_id("opus"), load()["tiers"]["opus"]["id"])

    def test_all_prices_keyed_by_model_id(self):
        p = all_prices()
        self.assertIn(tier_id("haiku"), p)
        self.assertIn("input", p[tier_id("haiku")])

    def test_price_lookup(self):
        self.assertEqual(price(tier_id("sonnet"))["output"],
                         load()["tiers"]["sonnet"]["price_per_mtok"]["output"])

    def test_emit_prices_cli(self):
        out = subprocess.check_output([sys.executable, "models.py", "--emit-prices"])
        data = json.loads(out)
        self.assertIn(tier_id("opus"), data)
        self.assertIn("input", data[tier_id("opus")])

if __name__ == "__main__":
    unittest.main()
