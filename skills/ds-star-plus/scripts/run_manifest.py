#!/usr/bin/env python3
"""Emit a reproducibility manifest for one solver run (Track J).

    from run_manifest import build_manifest, write_manifest
    m = build_manifest(question, code, inputs, answer, verdict, model)
    write_manifest(m, run_dir)          # -> <run_dir>/run_manifest.json
"""
import hashlib, json, os
from datetime import datetime, timezone

_RATES_PER_MTOK = {  # USD per 1M tokens (input, output); update as pricing changes
    "claude-haiku-4-5":  (1.0,  5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8":  (15.0, 75.0),
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
    print(build_manifest("demo", "print(1)", ["a.csv"], "1", {"score": 4}, "claude-sonnet-4-6"))
