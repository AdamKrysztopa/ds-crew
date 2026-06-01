#!/usr/bin/env python3
"""Validate ds-crew manifests parse and agree on version (Phase 0 CI).

Checks: plugin.json, marketplace.json (nested version), package.json all parse
and carry the SAME version string.

    python3 validate_manifests.py     # from repo root
"""
import json, sys

def load_json_or_error(path):
    try:
        return json.load(open(path)), ""
    except FileNotFoundError:
        return None, f"missing file: {path}"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON in {path}: {e}"

def versions_match(versions):
    return len(set(versions)) == 1

def _collect_versions():
    plugin, e1 = load_json_or_error(".claude-plugin/plugin.json")
    market, e2 = load_json_or_error(".claude-plugin/marketplace.json")
    pkg, e3 = load_json_or_error("package.json")
    errs = [e for e in (e1, e2, e3) if e]
    if errs:
        return None, errs
    versions = [
        plugin["version"],
        market["metadata"]["version"],
        market["plugins"][0]["version"],
        pkg["version"],
    ]
    return versions, []

if __name__ == "__main__":
    versions, errs = _collect_versions()
    if errs:
        for e in errs:
            print(e)
        sys.exit(1)
    ok = versions_match(versions)
    print(f"manifest versions {versions}: " + ("OK" if ok else "MISMATCH"))
    sys.exit(0 if ok else 1)
