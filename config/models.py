"""Canonical model alias/price registry (review item #6). Single source of truth.
Stdlib only. Consumers read tiers/ids/prices from here instead of hardcoding."""
import json, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "models.json")

def load():
    with open(_PATH) as fh:
        return json.load(fh)

def tier_id(tier):
    return load()["tiers"][tier]["id"]

def all_prices():
    return {t["id"]: t["price_per_mtok"] for t in load()["tiers"].values()}

def price(model_id):
    return all_prices()[model_id]

if __name__ == "__main__":
    if "--emit-prices" in sys.argv:
        json.dump(all_prices(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
