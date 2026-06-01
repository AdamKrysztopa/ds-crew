#!/usr/bin/env python3
"""Experiment C: SpikeSolver on consistently-failing questions.

Runs the real SpikeSolver (N=3 parallel personas + majority vote) on the
questions that all single-run variants got wrong. Tests whether ensemble
diversity recovers answers that a single solver misses.

The 3 personas (from skills/ds-spike/references/personas.md):
  - cautious-statistician (Sonnet) — checks distributions, nulls, sample sizes
  - sql-join-first (Sonnet)        — thinks in keys, joins, aggregation grain
  - assumption-minimal (Opus)      — does exactly what the spec says, nothing more

Usage:
    cd benchmarks
    python3 experiments/exp_c_spike.py [--question-ids ID [ID ...]]

Output:
    experiments/results/exp_c_results.jsonl
    experiments/results/exp_c_summary.json
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_BENCH)
sys.path.insert(0, _BENCH)

from runner import load_dabench_questions
from score import score_fields, extract_format
from solvers import SpikeSolver

DATA_DIR = os.path.join(_BENCH, "data", "InfiAgent", "examples", "DA-Agent", "data")
TABLES_DIR = os.path.join(DATA_DIR, "da-dev-tables")
OUT_DIR = os.path.join(_HERE, "results")


def _load_skill(name):
    path = os.path.join(_REPO, "skills", name, "SKILL.md")
    content = open(path).read()
    if content.startswith("---"):
        end = content.index("---", 3)
        content = content[end + 3:].lstrip("\n")
    return content


def load_prices():
    import json
    with open(os.path.join(_BENCH, "prices.json")) as f:
        return json.load(f)


def run_exp_c(question_ids=None):
    if question_ids is None:
        question_ids = ["7", "8"]

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "exp_c_results.jsonl")

    prices = load_prices()
    skill_body = _load_skill("ds-star-plus")  # spike uses ds-star-plus per spec
    solver = SpikeSolver(skill_body=skill_body, prices=prices,
                         data_dir=TABLES_DIR, n=3)

    questions = load_dabench_questions(
        os.path.join(DATA_DIR, "da-dev-questions.jsonl"),
        os.path.join(DATA_DIR, "da-dev-labels.jsonl"),
        limit=257,
    )
    targets = [q for q in questions if q["id"] in set(question_ids)]
    print(f"Experiment C — SpikeSolver (N=3) on {len(targets)} hard questions")
    print(f"Personas: cautious-statistician (Sonnet) · sql-join-first (Sonnet) · assumption-minimal (Opus)\n")

    results = []
    with open(out_path, "w") as fh:
        for q in targets:
            print(f"Q{q['id']} [{('hard' if q.get('hard') else 'easy')}]: {q['question'][:65]}...")
            t0 = time.time()
            r = solver.solve(
                q["id"], question=q["question"], files=q["files"],
                format_str=q.get("format_str", ""),
                constraints=q.get("constraints", ""),
            )
            wall = time.time() - t0

            subqs = q.get("subquestions") or [{"fmt": q["fmt"], "label": q["label"]}]
            matched, total = score_fields(r["answer"], subqs)
            correct = (total > 0 and matched == total)
            tokens = extract_format(r["answer"])

            # Per-persona breakdown
            print(f"  Subruns:")
            for sub in r.get("subruns", []):
                sub_tokens = extract_format(sub.get("answer", ""))
                sub_vals = list(zip(sub_tokens[0], sub_tokens[1]))
                print(f"    {sub['persona']:25}: {sub_vals} (${sub.get('cost_usd',0):.3f})")
            print(f"  Consensus: {list(zip(tokens[0], tokens[1]))}")
            print(f"  Expected:  {[(sq['fmt'], sq['label']) for sq in subqs]}")
            print(f"  → {'✓ CORRECT' if correct else '✗ WRONG'}  "
                  f"${r.get('cost_usd',0):.3f} total  {wall:.0f}s\n")

            row = {
                "variant": "ds-spike-n3",
                "question_id": q["id"],
                "hard": q.get("hard", False),
                "correct": correct,
                "field_score": round(matched / total, 4) if total else 0.0,
                "fields_matched": matched,
                "fields_total": total,
                # Full answer retained (truncation chopped the trailing @name[value] tokens)
                "answer": r["answer"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": round(r.get("cost_usd", 0), 6),
                "wall_time_s": round(wall, 2),
                "rounds": r["rounds"],
                "n_subruns": r.get("n_subruns", 3),
                "subruns": r.get("subruns", []),
            }
            results.append(row)
            fh.write(json.dumps(row) + "\n")
            fh.flush()

    correct_count = sum(r["correct"] for r in results)
    total_cost = sum(r["cost_usd"] for r in results)
    summary = {
        "variant": "ds-spike-n3",
        "n": len(results),
        "correct": correct_count,
        "accuracy": round(correct_count / len(results), 3) if results else 0,
        "total_cost_usd": round(total_cost, 4),
        "cost_per_task": round(total_cost / len(results), 4) if results else 0,
        "question_ids": question_ids,
        "wrong_ids": [r["question_id"] for r in results if not r["correct"]],
    }
    summary_path = os.path.join(OUT_DIR, "exp_c_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"=== Experiment C Results ===")
    print(f"SpikeSolver N=3: {correct_count}/{len(results)} correct")
    print(f"Total cost: ${total_cost:.3f}")
    print(f"Results: {out_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question-ids", nargs="+", default=["7", "8"],
                        help="Question IDs to run (default: 7 8)")
    args = parser.parse_args()
    run_exp_c(question_ids=args.question_ids)
