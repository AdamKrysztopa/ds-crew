#!/usr/bin/env python3
"""Experiment B: Plugin-loaded skill vs raw SKILL.md prompt.

Compares two ways of invoking DS-STAR:

  plugin   — /ds-star invoked properly via the ds-crew Claude Code plugin.
             The skill is loaded as system context through the plugin mechanism,
             exactly as a user would experience it.

  prompt   — SKILL.md injected as a user-message preamble (what our smoke run
             did). No plugin, skill instructions are just another blob of text.

Both use `claude -p --dangerously-skip-permissions` (full tool access, multi-round).
The --output-format json `num_turns` field tells us how many internal turns Claude used.

This answers: does the plugin mechanism itself add value beyond the raw text?

Usage:
    cd benchmarks
    python3 experiments/exp_b_plugin_vs_prompt.py [--limit N]

Output:
    experiments/results/exp_b_results.jsonl
    experiments/results/exp_b_summary.json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_BENCH)
sys.path.insert(0, _BENCH)

from runner import load_dabench_questions
from score import score_fields

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


def run_variant(variant_name, prompt_builder, q, work_dir):
    """Run one question with one variant. Returns result dict."""
    for fname in q["files"]:
        src = os.path.join(TABLES_DIR, fname)
        if os.path.exists(src):
            shutil.copy(src, work_dir)

    prompt = prompt_builder(q)
    t0 = time.time()
    proc = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json",
         "--dangerously-skip-permissions"],
        capture_output=True, text=True, cwd=work_dir,
    )
    wall = time.time() - t0

    try:
        data = json.loads(proc.stdout)
    except Exception:
        return {"answer": "", "input_tokens": 0, "output_tokens": 0,
                "cost_usd": 0.0, "wall_time_s": wall, "turns": 0}

    answer = data.get("result", "")
    usage = data.get("usage", {})
    in_tok = (usage.get("input_tokens", 0)
              + usage.get("cache_creation_input_tokens", 0)
              + usage.get("cache_read_input_tokens", 0))
    return {
        "answer": answer,
        "input_tokens": in_tok,
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": data.get("total_cost_usd", 0.0),
        "wall_time_s": wall,
        "turns": data.get("num_turns", 1),
    }


# ── Prompt builders ───────────────────────────────────────────────────────────

def plugin_prompt(skill_name):
    """Use the actual plugin slash command."""
    def build(q):
        file_list = ", ".join(q["files"]) if q["files"] else "(none)"
        constraints_line = f"\nConstraints: {q.get('constraints','')}" if q.get("constraints") else ""
        fmt_line = f"\nRequired answer format: {q.get('format_str','')}" if q.get("format_str") else ""
        return (
            f"/{skill_name}\n\n"
            f"Dataset: {file_list}\n"
            f"Question: {q['question']}{constraints_line}{fmt_line}"
        )
    return build


def raw_prompt(skill_name):
    """Inject SKILL.md as a user-message preamble (smoke run approach)."""
    skill_body = _load_skill(skill_name)
    def build(q):
        file_list = ", ".join(q["files"]) if q["files"] else "(none)"
        constraints_line = f"\n\nConstraints: {q.get('constraints','')}" if q.get("constraints") else ""
        fmt_line = f"\n\nRequired answer format: {q.get('format_str','')}" if q.get("format_str") else ""
        return (
            f"{skill_body}\n\n"
            f"Available data file(s) in your working directory: {file_list}\n\n"
            f"Question: {q['question']}{constraints_line}{fmt_line}"
        )
    return build


VARIANTS = {
    "ds-star-plugin":      plugin_prompt("ds-star"),
    "ds-star-prompt":      raw_prompt("ds-star"),
    "ds-star-plus-plugin": plugin_prompt("ds-star-plus"),
    "ds-star-plus-prompt": raw_prompt("ds-star-plus"),
}


# ── Runner ────────────────────────────────────────────────────────────────────

def run_exp_b(limit=15, variants=None, qids=None, out_name="exp_b_results.jsonl"):
    if variants is None:
        variants = list(VARIANTS.keys())

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, out_name)

    questions = load_dabench_questions(
        os.path.join(DATA_DIR, "da-dev-questions.jsonl"),
        os.path.join(DATA_DIR, "da-dev-labels.jsonl"),
        limit=257 if qids else limit,
    )
    if qids:
        wanted = set(str(x) for x in qids)
        questions = [q for q in questions if q["id"] in wanted]
    print(f"Experiment B — plugin vs prompt: {len(questions)} questions")
    print(f"Variants: {variants}\n")

    all_rows = []
    with open(out_path, "w") as fh:
        for variant in variants:
            prompt_builder = VARIANTS[variant]
            print(f"--- {variant} ---")
            variant_rows = []
            for i, q in enumerate(questions):
                print(f"  [{i+1}/{len(questions)}] Q{q['id']}: {q['question'][:60]}...")
                with tempfile.TemporaryDirectory() as work_dir:
                    r = run_variant(variant, prompt_builder, q, work_dir)

                subqs = q.get("subquestions") or [{"fmt": q["fmt"], "label": q["label"]}]
                matched, total = score_fields(r["answer"], subqs)
                correct = (total > 0 and matched == total)
                row = {
                    "variant": variant,
                    "question_id": q["id"],
                    "hard": q.get("hard", False),
                    "level": "hard" if q.get("hard") else "easy",
                    "correct": correct,
                    "field_score": round(matched / total, 4) if total else 0.0,
                    "fields_matched": matched,
                    "fields_total": total,
                    # Full answer retained: the @name[value] tokens the scorer needs
                    # appear at the END of the response, so truncation destroyed them
                    # and made saved results impossible to re-score/audit.
                    "answer": r["answer"],
                    "input_tokens": r["input_tokens"],
                    "output_tokens": r["output_tokens"],
                    "cost_usd": round(r["cost_usd"], 6),
                    "wall_time_s": round(r["wall_time_s"], 2),
                    "turns": r["turns"],
                }
                variant_rows.append(row)
                all_rows.append(row)
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"    → {'✓' if correct else '✗'}  turns={r['turns']}  "
                      f"${r['cost_usd']:.3f}  {r['wall_time_s']:.1f}s")

            # Per-variant summary
            n = len(variant_rows)
            hard = [r for r in variant_rows if r["hard"]]
            acc = sum(r["correct"] for r in variant_rows) / n
            acc_h = sum(r["correct"] for r in hard) / len(hard) if hard else 0
            avg_turns = sum(r["turns"] for r in variant_rows) / n
            avg_cost = sum(r["cost_usd"] for r in variant_rows) / n
            print(f"  → {acc:.1%} acc ({acc_h:.1%} hard)  "
                  f"avg {avg_turns:.1f} turns  ${avg_cost:.3f}/task\n")

    # Full summary
    from collections import defaultdict
    by_v = defaultdict(list)
    for r in all_rows:
        by_v[r["variant"]].append(r)

    print("=== Experiment B Results ===")
    print(f"{'variant':22} {'acc':>6} {'hard':>6} {'field':>6} {'turns':>7} {'$/task':>8}")
    print("-" * 62)
    variant_summaries = []
    for v in variants:
        rs = by_v[v]
        if not rs:
            continue
        hard = [r for r in rs if r["hard"]]
        acc = sum(r["correct"] for r in rs) / len(rs)
        acc_h = sum(r["correct"] for r in hard) / len(hard) if hard else 0
        field = sum(r["field_score"] for r in rs) / len(rs)
        avg_turns = sum(r["turns"] for r in rs) / len(rs)
        avg_cost = sum(r["cost_usd"] for r in rs) / len(rs)
        avg_tok = sum(r["input_tokens"] + r["output_tokens"] for r in rs) / len(rs)
        print(f"{v:22} {acc:>6.1%} {acc_h:>6.1%} {field:>6.1%} {avg_turns:>7.1f} ${avg_cost:>7.3f}")
        variant_summaries.append({
            "variant": v, "n": len(rs),
            "accuracy": round(acc, 3),
            "accuracy_hard": round(acc_h, 3),
            "mean_field_score": round(field, 3),
            "avg_turns": round(avg_turns, 2),
            "cost_per_task": round(avg_cost, 4),
            "tokens_per_task": round(avg_tok),
            "wrong_ids": [r["question_id"] for r in rs if not r["correct"]],
        })

    summary = {"n": limit, "variants": variant_summaries}
    summary_path = os.path.join(OUT_DIR, "exp_b_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults: {out_path}")
    print(f"Summary: {summary_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--variant", nargs="+",
                        choices=list(VARIANTS.keys()) + ["all"],
                        default=["ds-star-plugin", "ds-star-prompt"])
    parser.add_argument("--qids", nargs="+", default=None,
                        help="Run only these question IDs (default: first --limit questions)")
    parser.add_argument("--out", default="exp_b_results.jsonl",
                        help="Output filename under results/ (use a separate file for targeted runs)")
    args = parser.parse_args()
    variants = list(VARIANTS.keys()) if "all" in args.variant else args.variant
    run_exp_b(limit=args.limit, variants=variants, qids=args.qids, out_name=args.out)
