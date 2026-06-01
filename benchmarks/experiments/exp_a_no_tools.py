#!/usr/bin/env python3
"""Experiment A: True no-tools baseline.

Calls the Anthropic API directly — no bash, no code execution, no agent loop.
Claude must answer purely from the CSV text embedded in the prompt.

This establishes the floor: how much does code execution help at all?

Usage:
    cd benchmarks
    python3 experiments/exp_a_no_tools.py [--limit N]

Output:
    experiments/results/exp_a_results.jsonl
    experiments/results/exp_a_summary.json
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
sys.path.insert(0, _BENCH)

from runner import load_dabench_questions
from score import score_answer

DATA_DIR = os.path.join(_BENCH, "data", "InfiAgent", "examples", "DA-Agent", "data")
TABLES_DIR = os.path.join(DATA_DIR, "da-dev-tables")
OUT_DIR = os.path.join(_HERE, "results")
MODEL = "claude-sonnet-4-6"
MAX_CSV_ROWS = 50


def embed_csv(file_name):
    """Return the first MAX_CSV_ROWS rows of a CSV as plain text."""
    path = os.path.join(TABLES_DIR, file_name)
    if not os.path.exists(path):
        return f"(file {file_name} not found)"
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        sample = lines[:MAX_CSV_ROWS + 1]
        total_rows = len(lines) - 1
        text = "".join(sample)
        if total_rows > MAX_CSV_ROWS:
            text += f"\n... ({total_rows - MAX_CSV_ROWS} more rows not shown)"
        return text
    except Exception as e:
        return f"(error reading {file_name}: {e})"


def ask_no_tools(question, files, constraints, format_str):
    """Call claude -p with CSV embedded in prompt and tools explicitly blocked."""
    file_sections = ""
    for fname in files:
        csv_text = embed_csv(fname)
        file_sections += f"\n\n### File: {fname}\n```\n{csv_text}\n```"

    constraints_line = f"\n\nConstraints: {constraints}" if constraints else ""
    fmt_line = f"\n\nRequired answer format: {format_str}" if format_str else ""

    # System prompt explicitly blocks tool use — model must reason from text only
    system = (
        "You are a data scientist answering questions from text data. "
        "You MUST NOT use any tools, bash, or code execution. "
        "Reason directly from the numbers in the provided data excerpt. "
        "Do all arithmetic mentally or by inspection."
    )

    prompt = (
        f"{system}\n\nThe data is provided below as plain text. "
        f"Do NOT execute code — answer from the numbers shown.{file_sections}\n\n"
        f"Question: {question}{constraints_line}{fmt_line}"
    )

    t0 = time.time()
    # Pass prompt via stdin to avoid shell escaping issues with large CSVs
    proc = __import__("subprocess").run(
        ["claude", "-p", "--output-format", "json"],
        input=prompt, capture_output=True, text=True,
    )
    wall = time.time() - t0

    try:
        data = __import__("json").loads(proc.stdout)
    except Exception:
        return {"answer": proc.stdout.strip(), "input_tokens": 0,
                "output_tokens": 0, "cost_usd": 0.0, "wall_time_s": wall, "rounds": 1}

    answer = data.get("result", "")
    usage = data.get("usage", {})
    in_tok = (usage.get("input_tokens", 0)
              + usage.get("cache_creation_input_tokens", 0)
              + usage.get("cache_read_input_tokens", 0))
    out_tok = usage.get("output_tokens", 0)
    return {
        "answer": answer,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": data.get("total_cost_usd", 0.0),
        "wall_time_s": wall,
        "rounds": 1,
    }


def run_exp_a(limit=15):
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "exp_a_results.jsonl")

    questions = load_dabench_questions(
        os.path.join(DATA_DIR, "da-dev-questions.jsonl"),
        os.path.join(DATA_DIR, "da-dev-labels.jsonl"),
        limit=limit,
    )
    print(f"Experiment A — no-tools baseline: {len(questions)} questions, model={MODEL}")

    results = []
    with open(out_path, "w") as fh:
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] Q{q['id']}: {q['question'][:65]}...")
            r = ask_no_tools(
                question=q["question"],
                files=q["files"],
                constraints=q.get("constraints", ""),
                format_str=q.get("format_str", ""),
            )
            subqs = q.get("subquestions") or [{"fmt": q["fmt"], "label": q["label"]}]
            correct = all(score_answer(r["answer"], sq["label"], sq["fmt"]) for sq in subqs)
            row = {
                "variant": "no-tools",
                "question_id": q["id"],
                "hard": q.get("hard", False),
                "level": "hard" if q.get("hard") else "easy",
                "correct": correct,
                "answer": r["answer"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": round(r["cost_usd"], 6),
                "wall_time_s": r["wall_time_s"],
                "rounds": 1,
            }
            results.append(row)
            fh.write(json.dumps(row) + "\n")
            fh.flush()

    # Summary
    n = len(results)
    hard = [r for r in results if r["hard"]]
    accuracy = sum(r["correct"] for r in results) / n
    accuracy_hard = sum(r["correct"] for r in hard) / len(hard) if hard else 0.0
    avg_cost = sum(r["cost_usd"] for r in results) / n
    avg_tokens = sum(r["input_tokens"] + r["output_tokens"] for r in results) / n

    summary = {
        "variant": "no-tools",
        "model": MODEL,
        "n": n,
        "accuracy": round(accuracy, 3),
        "accuracy_hard": round(accuracy_hard, 3),
        "cost_per_task": round(avg_cost, 4),
        "tokens_per_task": round(avg_tokens),
        "wrong_ids": [r["question_id"] for r in results if not r["correct"]],
    }
    summary_path = os.path.join(OUT_DIR, "exp_a_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Experiment A Results ===")
    print(f"accuracy:      {accuracy:.1%}  ({sum(r['correct'] for r in results)}/{n})")
    print(f"accuracy-hard: {accuracy_hard:.1%}  ({sum(r['correct'] for r in hard)}/{len(hard)})")
    print(f"cost/task:     ${avg_cost:.4f}")
    print(f"tokens/task:   {avg_tokens:.0f}")
    print(f"wrong IDs:     {summary['wrong_ids']}")
    print(f"\nResults: {out_path}")
    print(f"Summary: {summary_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()
    run_exp_a(limit=args.limit)
