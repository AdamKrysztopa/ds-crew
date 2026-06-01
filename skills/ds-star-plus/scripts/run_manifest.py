#!/usr/bin/env python3
"""Emit a reproducibility manifest for one solver run (Track J).

    from run_manifest import build_manifest, write_manifest
    m = build_manifest(question, code, inputs, answer, verdict, model)
    write_manifest(m, run_dir)          # -> <run_dir>/run_manifest.json
"""
import hashlib, json, os
from datetime import datetime, timezone

def _models_config():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        p = os.path.join(d, "config", "models.json")
        if os.path.exists(p):
            with open(p) as fh:
                return json.load(fh)
        d = os.path.dirname(d)
    raise FileNotFoundError("config/models.json not found")

_RATES_PER_MTOK = {
    spec["id"]: (spec["price_per_mtok"]["input"], spec["price_per_mtok"]["output"])
    for spec in _models_config()["tiers"].values()
}

def estimate_cost(model, usage):
    rate_in, rate_out = _RATES_PER_MTOK.get(model, (0.0, 0.0))
    return (usage.get("input_tokens", 0) / 1_000_000) * rate_in + \
           (usage.get("output_tokens", 0) / 1_000_000) * rate_out

def build_manifest(question, code, inputs, answer, verdict, model,
                   usage=None, latency_s=None):
    usage = usage or {}
    return {
        "question": question,
        "inputs": list(inputs),
        "code_sha256": hashlib.sha256((code or "").encode("utf-8")).hexdigest(),
        "answer": answer,
        "verdict": verdict,
        "model": model,
        "usage": usage,
        "latency_s": latency_s,
        "cost_usd": round(estimate_cost(model, usage), 6),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }

def write_manifest(manifest, run_dir):
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "run_manifest.json")
    with open(path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return path

if __name__ == "__main__":
    model = next(iter(_RATES_PER_MTOK))
    print(build_manifest("demo", "print(1)", ["a.csv"], "1", {"score": 4}, model))
