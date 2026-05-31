#!/usr/bin/env python3
"""Describe a data file's structure for DS-STAR Stage 1.

Usage: python analyze_file.py <path> [path2 ...]

Prints essential structure (no try/except suppression by design — let errors surface so the
debugging step can use them). Supports csv/tsv, json, xlsx/xls, txt/md, sqlite. For anything
else it prints a short head excerpt. This is a sensible default; for a specific file you can
always generate a bespoke describer instead.
"""
import json
import os
import sys


def describe_tabular(df, name):
    print(f"--- {name}: {df.shape[0]} rows x {df.shape[1]} cols ---")
    print("Columns & dtypes:")
    for c in df.columns:
        print(f"  - {c}: {df[c].dtype}")
    miss = df.isnull().sum()
    miss = miss[miss > 0]
    if len(miss):
        print("Missing values:")
        print(miss.to_string())
    print("Head (up to 5 rows):")
    print(df.head().to_string())
    obj_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) in ("string", "str")]
    for c in obj_cols:
        n = df[c].nunique(dropna=True)
        if 1 <= n <= 15:
            print(f"Unique values of '{c}' ({n}):")
            print(df[c].value_counts(dropna=False).to_string())


def describe_csv(path, sep):
    import pandas as pd
    describe_tabular(pd.read_csv(path, sep=sep), os.path.basename(path))


def describe_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"--- {os.path.basename(path)} ---")
    print(f"Top-level type: {type(data).__name__}")
    if isinstance(data, dict):
        keys = list(data.keys())
        print(f"Keys ({len(keys)}): {keys}")
        for k, v in list(data.items())[:5]:
            s = str(v)
            print(f"  {k}: {s[:70] + '...' if len(s) > 70 else s}")
    elif isinstance(data, list):
        print(f"Array with {len(data)} items")
        if data and isinstance(data[0], dict):
            print(f"Element keys: {list(data[0].keys())}")
        print("First items:")
        print(json.dumps(data[:3], indent=2, ensure_ascii=False)[:1500])


def describe_excel(path):
    import pandas as pd
    xls = pd.ExcelFile(path)
    print(f"--- {os.path.basename(path)} ---")
    print(f"Sheets ({len(xls.sheet_names)}): {xls.sheet_names}")
    for sheet in xls.sheet_names:
        print(f"\n[Sheet: {sheet}]")
        describe_tabular(pd.read_excel(xls, sheet_name=sheet), sheet)


def describe_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    print(f"--- {os.path.basename(path)}: {len(lines)} lines ---")
    print("Head (up to 40 lines):")
    print("".join(lines[:40]))


def describe_sqlite(path):
    import sqlite3
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"--- {os.path.basename(path)} --- tables: {tables}")
    import pandas as pd
    for t in tables:
        df = pd.read_sql_query(f"SELECT * FROM '{t}' LIMIT 5", conn)
        print(f"\n[Table: {t}] columns: {list(df.columns)}")
        print(df.to_string())
    conn.close()


def describe(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".csv",):
        describe_csv(path, ",")
    elif ext in (".tsv",):
        describe_csv(path, "\t")
    elif ext in (".json",):
        describe_json(path)
    elif ext in (".xlsx", ".xls"):
        describe_excel(path)
    elif ext in (".sqlite", ".db"):
        describe_sqlite(path)
    elif ext in (".txt", ".md"):
        describe_text(path)
    else:
        describe_text(path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_file.py <path> [path2 ...]")
        sys.exit(1)
    for p in sys.argv[1:]:
        print("=" * 60)
        describe(p)
        print()
