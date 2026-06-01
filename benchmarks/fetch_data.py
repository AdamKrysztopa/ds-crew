#!/usr/bin/env python3
"""Clone InfiAgent-DAEval benchmark data into benchmarks/data/.

Usage: python3 benchmarks/fetch_data.py
Requires: git on PATH
"""
import os, subprocess, sys

REPO_URL = "https://github.com/InfiAgent/InfiAgent"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "InfiAgent")

def fetch():
    if os.path.exists(DATA_DIR):
        print(f"Already cloned at {DATA_DIR}. Pulling...")
        subprocess.run(["git", "-C", DATA_DIR, "pull", "--ff-only"], check=True)
    else:
        os.makedirs(os.path.dirname(DATA_DIR), exist_ok=True)
        print(f"Cloning {REPO_URL} -> {DATA_DIR} (depth=1)...")
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, DATA_DIR], check=True)
    print("Done.")

if __name__ == "__main__":
    fetch()
