#!/usr/bin/env python3
"""Emit a reproducibility manifest for one solver run (Track J).

    from run_manifest import build_manifest, write_manifest
    m = build_manifest(question, code, inputs, answer, verdict, model)
    write_manifest(m, run_dir)          # -> <run_dir>/run_manifest.json
"""
import hashlib, json, os
from datetime import datetime, timezone

def build_manifest(question, code, inputs, answer, verdict, model):
    return {
        "question": question,
        "inputs": list(inputs),
        "code_sha256": hashlib.sha256((code or "").encode("utf-8")).hexdigest(),
        "answer": answer,
        "verdict": verdict,
        "model": model,
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
