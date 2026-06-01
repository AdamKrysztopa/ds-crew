#!/usr/bin/env python3
"""Experiment B: Multi-round execution harness.

Drives ds-star and ds-star-plus skills via the Anthropic SDK tool-use loop:
  1. Send question + skill prompt to Claude
  2. When Claude emits a tool_use (bash/python), execute it locally
  3. Feed tool_result back → Claude verifies, decides to backtrack or continue
  4. Repeat until Claude emits a final text answer (stop_reason=end_turn)

This is the only correct way to measure DS-STAR — the iterative loop only matters
when code actually runs and output comes back.

Usage:
    cd benchmarks
    ANTHROPIC_API_KEY=<key> python3 experiments/exp_b_multi_round.py [--limit N] [--variant VARIANT]

    # Without API key — uses claude -p streaming (slower, same result)
    python3 experiments/exp_b_multi_round.py [--limit N]

Output:
    experiments/results/exp_b_results.jsonl
    experiments/results/exp_b_summary.json
"""
import argparse
import json
import os
import re
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
MODEL = "claude-sonnet-4-6"
MAX_ROUNDS = 20
ROUND_BUDGET_USD = 2.00  # abort if a single question exceeds this


# ── Tool definition ───────────────────────────────────────────────────────────

BASH_TOOL = {
    "name": "bash",
    "description": "Execute a bash command or Python script. Returns stdout+stderr.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string",
                        "description": "Bash command or python3 -c '...' to run"}
        },
        "required": ["command"],
    },
}


def execute_tool(command, work_dir):
    """Run a bash command in work_dir, return (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=work_dir, timeout=60,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return out[:4000], r.returncode  # cap output to avoid context explosion
    except subprocess.TimeoutExpired:
        return "(timeout after 60s)", 1
    except Exception as e:
        return f"(error: {e})", 1


# ── SDK loop ──────────────────────────────────────────────────────────────────

def run_with_sdk(client, skill_prompt, question, files, constraints, format_str, work_dir):
    """Drive the DS-STAR loop via Anthropic SDK tool-use. Returns result dict."""
    import anthropic

    constraints_line = f"\n\nConstraints: {constraints}" if constraints else ""
    fmt_line = f"\n\nRequired answer format: {format_str}" if format_str else ""
    file_list = ", ".join(files) if files else "(none)"

    system = skill_prompt
    user_msg = (
        f"Available data file(s) in your working directory: {file_list}\n\n"
        f"Question: {question}{constraints_line}{fmt_line}"
    )

    messages = [{"role": "user", "content": user_msg}]
    total_in = total_out = 0
    total_cost = 0.0
    rounds = 0
    final_answer = ""

    for _ in range(MAX_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=[BASH_TOOL],
            messages=messages,
        )
        usage = response.usage
        in_tok = usage.input_tokens
        out_tok = usage.output_tokens
        total_in += in_tok
        total_out += out_tok
        cost_this = (in_tok / 1e6 * 3.0) + (out_tok / 1e6 * 15.0)
        total_cost += cost_this

        if total_cost > ROUND_BUDGET_USD:
            final_answer = "(budget exceeded)"
            break

        # Collect text and tool_use blocks
        tool_calls = []
        text_parts = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(block)
            elif block.type == "text":
                text_parts.append(block.text)

        if response.stop_reason == "end_turn" or not tool_calls:
            final_answer = "\n".join(text_parts)
            rounds += 1
            break

        # Execute tool calls and collect results
        rounds += 1
        tool_results = []
        for tc in tool_calls:
            cmd = tc.input.get("command", "")
            output, rc = execute_tool(cmd, work_dir)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": output,
            })

        # Append assistant turn + tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return {
        "answer": final_answer,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cost_usd": total_cost,
        "rounds": rounds,
    }


# ── Fallback: no SDK / no API key ─────────────────────────────────────────────

def run_with_claude_p(skill_prompt, question, files, constraints, format_str, work_dir):
    """Fallback: single claude -p call (same as smoke run — not multi-round)."""
    constraints_line = f"\n\nConstraints: {constraints}" if constraints else ""
    fmt_line = f"\n\nRequired answer format: {format_str}" if format_str else ""
    file_list = ", ".join(files) if files else "(none)"
    prompt = (
        f"{skill_prompt}\n\n"
        f"Available data file(s): {file_list}\n\n"
        f"Question: {question}{constraints_line}{fmt_line}"
    )
    t0 = time.time()
    proc = subprocess.run(
        ["claude", "-p", "--output-format", "json", "--dangerously-skip-permissions"],
        input=prompt, capture_output=True, text=True, cwd=work_dir,
    )
    wall = time.time() - t0
    try:
        data = json.loads(proc.stdout)
    except Exception:
        return {"answer": "", "input_tokens": 0, "output_tokens": 0,
                "cost_usd": 0.0, "wall_time_s": wall, "rounds": 1}
    usage = data.get("usage", {})
    in_tok = (usage.get("input_tokens", 0)
              + usage.get("cache_creation_input_tokens", 0)
              + usage.get("cache_read_input_tokens", 0))
    return {
        "answer": data.get("result", ""),
        "input_tokens": in_tok,
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": data.get("total_cost_usd", 0.0),
        "wall_time_s": wall,
        "rounds": 1,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def _load_skill(skill_name):
    path = os.path.join(_REPO, "skills", skill_name, "SKILL.md")
    with open(path) as f:
        content = f.read()
    if content.startswith("---"):
        end = content.index("---", 3)
        content = content[end + 3:].lstrip("\n")
    return content


VARIANTS = {
    "ds-star":      _load_skill("ds-star"),
    "ds-star-plus": _load_skill("ds-star-plus"),
}


def run_exp_b(limit=15, variants=None, use_sdk=True):
    if variants is None:
        variants = ["ds-star", "ds-star-plus"]

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "exp_b_results.jsonl")

    # Try SDK
    client = None
    if use_sdk:
        try:
            import anthropic
            client = anthropic.Anthropic()
            print(f"Using Anthropic SDK (multi-round loop), model={MODEL}")
        except Exception as e:
            print(f"SDK unavailable ({e}) — falling back to single-turn claude -p")

    questions = load_dabench_questions(
        os.path.join(DATA_DIR, "da-dev-questions.jsonl"),
        os.path.join(DATA_DIR, "da-dev-labels.jsonl"),
        limit=limit,
    )
    print(f"Experiment B: {len(questions)} questions, variants={variants}")

    all_results = []
    with open(out_path, "w") as fh:
        for variant in variants:
            skill_prompt = VARIANTS[variant]
            print(f"\nVariant: {variant}")
            for i, q in enumerate(questions):
                print(f"  [{i+1}/{len(questions)}] Q{q['id']}: {q['question'][:60]}...")
                with tempfile.TemporaryDirectory() as work_dir:
                    # Copy data files
                    for fname in q["files"]:
                        src = os.path.join(TABLES_DIR, fname)
                        if os.path.exists(src):
                            import shutil
                            shutil.copy(src, work_dir)

                    t0 = time.time()
                    if client:
                        r = run_with_sdk(client, skill_prompt,
                                         question=q["question"],
                                         files=q["files"],
                                         constraints=q.get("constraints", ""),
                                         format_str=q.get("format_str", ""),
                                         work_dir=work_dir)
                        r["wall_time_s"] = time.time() - t0
                    else:
                        r = run_with_claude_p(skill_prompt,
                                              question=q["question"],
                                              files=q["files"],
                                              constraints=q.get("constraints", ""),
                                              format_str=q.get("format_str", ""),
                                              work_dir=work_dir)

                subqs = q.get("subquestions") or [{"fmt": q["fmt"], "label": q["label"]}]
                matched, total = score_fields(r["answer"], subqs)
                correct = (total > 0 and matched == total)
                row = {
                    "variant": f"{variant}-multi" if client else variant,
                    "question_id": q["id"],
                    "hard": q.get("hard", False),
                    "level": "hard" if q.get("hard") else "easy",
                    "correct": correct,
                    "field_score": round(matched / total, 4) if total else 0.0,
                    "fields_matched": matched,
                    "fields_total": total,
                    # Full answer retained (truncation chopped the trailing @name[value] tokens)
                    "answer": r["answer"],
                    "input_tokens": r["input_tokens"],
                    "output_tokens": r["output_tokens"],
                    "cost_usd": round(r.get("cost_usd", 0), 6),
                    "wall_time_s": r.get("wall_time_s", 0),
                    "rounds": r["rounds"],
                }
                all_results.append(row)
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"    → {'✓' if correct else '✗'} rounds={r['rounds']} "
                      f"${r.get('cost_usd', 0):.3f}")

    # Summary per variant
    from collections import defaultdict
    by_v = defaultdict(list)
    for r in all_results:
        by_v[r["variant"]].append(r)

    variant_summaries = []
    print("\n=== Experiment B Results ===")
    for v, rs in sorted(by_v.items()):
        hard = [r for r in rs if r["hard"]]
        acc = sum(r["correct"] for r in rs) / len(rs)
        acc_h = sum(r["correct"] for r in hard) / len(hard) if hard else 0
        avg_cost = sum(r["cost_usd"] for r in rs) / len(rs)
        avg_rounds = sum(r["rounds"] for r in rs) / len(rs)
        avg_tok = sum(r["input_tokens"] + r["output_tokens"] for r in rs) / len(rs)
        variant_summaries.append({
            "variant": v, "n": len(rs),
            "accuracy": round(acc, 3), "accuracy_hard": round(acc_h, 3),
            "cost_per_task": round(avg_cost, 4),
            "avg_rounds": round(avg_rounds, 2),
            "tokens_per_task": round(avg_tok),
            "wrong_ids": [r["question_id"] for r in rs if not r["correct"]],
        })
        print(f"  {v}: {acc:.1%} acc ({acc_h:.1%} hard) "
              f"avg {avg_rounds:.1f} rounds ${avg_cost:.3f}/task")

    summary = {
        "model": MODEL,
        "n": limit,
        "multi_round": client is not None,
        "variants": variant_summaries,
    }
    summary_path = os.path.join(OUT_DIR, "exp_b_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults: {out_path}\nSummary: {summary_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--variant", nargs="+",
                        choices=list(VARIANTS.keys()) + ["all"],
                        default=["ds-star", "ds-star-plus"])
    parser.add_argument("--no-sdk", action="store_true",
                        help="Force single-turn fallback even if SDK available")
    args = parser.parse_args()
    variants = list(VARIANTS.keys()) if "all" in args.variant else args.variant
    run_exp_b(limit=args.limit, variants=variants, use_sdk=not args.no_sdk)
