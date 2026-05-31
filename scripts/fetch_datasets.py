#!/usr/bin/env python3
"""Fetch the starter-four demo datasets on demand (Principle: data is not committed).

Stdlib downloader. Files land under <base>/<name>/ and are gitignored.

    python3 fetch_datasets.py online_retail_ii         # one
    python3 fetch_datasets.py --all                    # all four
"""
import os, sys, urllib.request

DATASETS = {
    "online_retail_ii": {
        "url": "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
        "license": "CC BY 4.0", "domain": "retail",
        "failure_mode": "cancellations / negative qty / null CustomerID -> revenue scope error",
    },
    "owid_co2": {
        "url": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
        "license": "CC BY 4.0", "domain": "climate/energy panel",
        "failure_mode": "per-capita vs absolute; World/region rows mixed with countries",
    },
    "synthea": {
        "url": "https://synthea.mitre.org/downloads/synthea_sample_data_csv_latest.zip",
        "license": "Apache-2.0", "domain": "healthcare multi-table",
        "failure_mode": "multi-file joins + safe (synthetic) PII demo",
    },
    "bike_sharing": {
        "url": "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip",
        "license": "CC BY 4.0", "domain": "urban mobility",
        "failure_mode": "casual+registered=cnt target leakage; hourly -> temporal CV",
    },
}

def dataset_spec(name):
    return DATASETS[name]

def target_path(name, base="data"):
    return os.path.join(base, name, os.path.basename(dataset_spec(name)["url"]))

def fetch(name, base="data"):
    spec = dataset_spec(name)
    dest = target_path(name, base)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"fetching {name} ({spec['license']}) -> {dest}")
    urllib.request.urlretrieve(spec["url"], dest)
    return dest

if __name__ == "__main__":
    args = sys.argv[1:]
    names = list(DATASETS) if "--all" in args else args
    if not names:
        print("usage: fetch_datasets.py <name>... | --all"); sys.exit(2)
    for n in names:
        fetch(n)
