#!/usr/bin/env python3
"""Persistent cross-session recipe store for ds-crew (Track E; AWM 2409.07429).

Append-only JSONL of verified analysis recipes; retrieved by task signature + data
fingerprint similarity. Stdlib only.
    from memory_store import record, retrieve, task_signature
    record(path, {...}); hits = retrieve(path, sig, fingerprint, k=3)
"""
import json, os, re

def task_signature(text):
    """Normalized, order-insensitive bag-of-words signature for a task prompt."""
    words = sorted(set(re.findall(r"[a-z0-9]+", str(text).lower())))
    return "|".join(words)

def record(path, entry):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")

def _load(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def retrieve(path, signature, fingerprint, k=3, min_score=4):
    """Return up to k verified recipes, exact-fingerprint matches ranked first."""
    rows = [r for r in _load(path) if r.get("verifier_score", 0) >= min_score]
    sig_words = set(signature.split("|"))
    def score(r):
        rs = set(str(r.get("task_signature", "")).split("|"))
        overlap = len(sig_words & rs) / (len(sig_words | rs) or 1)
        fp = 1 if r.get("data_fingerprint") == fingerprint else 0
        return (fp, overlap)
    ranked = sorted(rows, key=score, reverse=True)
    return [r for r in ranked if score(r) > (0, 0)][:k]

if __name__ == "__main__":
    print(task_signature("Pct of CREDIT txns?"))
