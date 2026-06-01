#!/usr/bin/env python3
"""Smoke run: 3 questions × 1 variant to validate the benchmark harness end-to-end.

Usage:
    cd benchmarks
    python3 smoke_run.py [--limit N] [--variant VARIANT]

Writes:
    runs/smoke/results.jsonl
    runs/smoke/summary.md
    runs/smoke/manifest.json

Variant prompts are intentionally minimal — they ask Claude to use Python tools
to analyze the data and produce a DABench-format answer. This measures Claude's
raw data-science ability under different instruction regimes, not interactive skill
execution (which requires a live Claude Code session).
"""
import argparse
import json
import os
import subprocess
import sys

# Run from the benchmarks/ directory
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from runner import load_dabench_questions, run_variant
from report import summarize, render_summary_md, build_manifest
from solvers import ClaudeCliSolver, SpikeSolver

DATA_DIR = os.path.join(_HERE, "data", "InfiAgent", "examples", "DA-Agent", "data")
TABLES_DIR = os.path.join(DATA_DIR, "da-dev-tables")
QUESTIONS_PATH = os.path.join(DATA_DIR, "da-dev-questions.jsonl")
LABELS_PATH = os.path.join(DATA_DIR, "da-dev-labels.jsonl")
REPO_ROOT = os.path.dirname(_HERE)
OUT_DIR = os.path.join(_HERE, "runs", "smoke")


def _load_skill(skill_name):
    """Load a SKILL.md as the variant prompt, stripping YAML frontmatter.

    Frontmatter (--- ... ---) is stripped because claude -p interprets a
    leading '---' as a CLI flag separator, causing a parse error.
    """
    path = os.path.join(REPO_ROOT, "skills", skill_name, "SKILL.md")
    with open(path) as f:
        content = f.read()
    # Strip YAML frontmatter if present
    if content.startswith("---"):
        end = content.index("---", 3)
        content = content[end + 3:].lstrip("\n")
    return content


# Variant prompts — load actual SKILL.md content so the benchmark reflects
# the real skill instructions, not a simplified paraphrase.
VARIANTS = {
    "baseline": (
        "You are a data scientist. Answer the question using the provided data file. "
        "Use Python if needed."
    ),
    "ds-star": _load_skill("ds-star"),
    "ds-star-plus": _load_skill("ds-star-plus"),
    "ds-spike": _load_skill("ds-spike"),
}


def load_prices():
    prices_path = os.path.join(_HERE, "prices.json")
    with open(prices_path) as f:
        return json.load(f)


def get_commit_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, cwd=_HERE
        ).strip()
    except Exception:
        return "unknown"


def failed_question_ids(results_path, variant):
    """Return IDs of questions the given variant got wrong."""
    if not os.path.exists(results_path):
        return []
    with open(results_path) as f:
        rows = [json.loads(l) for l in f if l.strip()]
    return [r["question_id"] for r in rows
            if r["variant"] == variant and not r["correct"]]


def run_smoke(limit=3, variants=None, rerun_failures_of=None):
    """Run variants over questions.

    Args:
        limit: Max questions to load.
        variants: List of variant names to run.
        rerun_failures_of: If set, only run questions that FAILED for this
            variant (reads existing results.jsonl). Useful for: run baseline
            cheap on all N, then pass failed IDs to expensive variants.
    """
    if variants is None:
        variants = ["ds-star"]

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "results.jsonl")

    if rerun_failures_of is None and os.path.exists(out_path):
        # Only wipe if any requested variant already has rows — safe to append new variants
        with open(out_path) as _f:
            existing = {json.loads(l)["variant"] for l in _f if l.strip()}
        if any(v in existing for v in variants):
            print(f"Removing existing {out_path} (variant overlap detected)")
            os.remove(out_path)

    prices = load_prices()
    questions = load_dabench_questions(QUESTIONS_PATH, LABELS_PATH, limit=limit)

    if rerun_failures_of:
        fail_ids = set(failed_question_ids(out_path, rerun_failures_of))
        questions = [q for q in questions if q["id"] in fail_ids]
        print(f"Rerunning {len(questions)} questions that failed for '{rerun_failures_of}'")
    else:
        print(f"Loaded {len(questions)} questions")

    model_ids_used = []
    for variant in variants:
        prompt = VARIANTS.get(variant, VARIANTS["ds-star"])
        model_id = "claude-sonnet-4-6"
        model_ids_used.append(model_id)

        if variant == "ds-spike":
            # True spike: N=3 independent parallel solvers + majority vote
            solver = SpikeSolver(
                skill_body=prompt,
                prices=prices,
                data_dir=TABLES_DIR,
                n=3,
            )
        else:
            solver = ClaudeCliSolver(
                variant_prompt=prompt,
                model_id=model_id,
                prices=prices,
                data_dir=TABLES_DIR,
            )
        print(f"\nRunning variant '{variant}' over {len(questions)} questions...")
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] Q{q['id']}: {q['question'][:60]}...")
        run_variant(variant, questions, solver, prices, out_path)

        # Sanity-check this variant before continuing to the next
        with open(out_path) as f:
            all_rows = [json.loads(l) for l in f]
        variant_rows = [r for r in all_rows if r["variant"] == variant]
        zero_tok = [r for r in variant_rows if r["input_tokens"] == 0]
        if zero_tok:
            print(f"\n⚠️  ABORT: {len(zero_tok)} zero-token rows in '{variant}' — likely a prompt/parse failure.")
            print("   Affected question IDs:", [r["question_id"] for r in zero_tok])
            print("   Fix the issue and re-run. Remaining variants skipped.")
            break
        n_correct = sum(r["correct"] for r in variant_rows)
        print(f"  ✓ '{variant}' done: {n_correct}/{len(variant_rows)} correct, "
              f"avg ${sum(r['cost_usd'] for r in variant_rows)/len(variant_rows):.3f}/task")

    # Report
    with open(out_path) as f:
        rows = [json.loads(l) for l in f]

    summary = summarize(rows)
    print("\n=== Smoke Run Results ===")
    print(render_summary_md(summary))

    summary_path = os.path.join(OUT_DIR, "summary.md")
    with open(summary_path, "w") as f:
        from collections import Counter
        level_counts = Counter(q.get("hard", False) for q in questions)
        n_hard = level_counts[True]; n_easy = level_counts[False]
        f.write("# Smoke Run — DABench (subset)\n\n")
        f.write(f"**Questions:** {limit} ({n_easy} easy/medium, {n_hard} hard)\n")
        f.write(f"**Variants:** {', '.join(variants)}\n\n")
        f.write(render_summary_md(summary))

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(
            build_manifest(
                commit_sha=get_commit_sha(),
                model_ids=list(set(model_ids_used)),
                prices=prices,
                n=limit,
                seed=0,
            ),
            f, indent=2, sort_keys=True,
        )

    print(f"\nResults: {out_path}")
    print(f"Summary: {summary_path}")
    print(f"Manifest: {manifest_path}")


def diagnose(results_path=None):
    """Print a failure breakdown from an existing results.jsonl."""
    if results_path is None:
        results_path = os.path.join(OUT_DIR, "results.jsonl")
    qs_map = {}
    DATA = os.path.join(_HERE, "data", "InfiAgent", "examples", "DA-Agent", "data")
    for line in open(os.path.join(DATA, "da-dev-questions.jsonl")):
        q = json.loads(line)
        qs_map[str(q["id"])] = q

    rows = [json.loads(l) for l in open(results_path)]
    variants = sorted(set(r["variant"] for r in rows))

    # Per-question, which variants got it wrong?
    qids = sorted(set(r["question_id"] for r in rows))
    print(f"{'Q':>4} {'level':6} {'file':30} {'correct by variant'}")
    print("-" * 80)
    for qid in qids:
        q = qs_map.get(qid, {})
        level = q.get("level", "?")
        fname = q.get("file_name", "?")[:28]
        scores = {r["variant"]: ("✓" if r["correct"] else "✗")
                  for r in rows if r["question_id"] == qid}
        row_str = "  ".join(f"{v[:10]}:{scores.get(v,'?')}" for v in variants)
        print(f"Q{qid:>3} {level:6} {fname:30} {row_str}")

    # Show answer snippet for failures
    print("\n--- Failure details (answer snippets) ---")
    for qid in qids:
        q = qs_map.get(qid, {})
        wrong_rows = [r for r in rows if r["question_id"] == qid and not r["correct"]]
        if not wrong_rows:
            continue
        print(f"\nQ{qid} [{q.get('level','?')}]: {q.get('question','')[:70]}")
        print(f"  Expected: {q.get('constraints','(no constraints)')[:80]}")
        for r in wrong_rows[:2]:  # show first 2 variants
            ans = r.get("answer", "")
            snippet = ans[:120].replace("\n", " ") if ans else "(empty)"
            print(f"  {r['variant']:12}: {snippet}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3,
                        help="Number of questions (default: 3)")
    parser.add_argument("--variant", nargs="+", default=["ds-star"],
                        choices=list(VARIANTS.keys()) + ["all"],
                        help="Variant(s) to run (or 'all')")
    parser.add_argument("--diagnose", action="store_true",
                        help="Print failure breakdown from existing results.jsonl")
    parser.add_argument("--rerun-failures-of", metavar="VARIANT",
                        help="Only run questions that FAILED for VARIANT in existing results")
    args = parser.parse_args()
    if args.diagnose:
        diagnose()
    else:
        variants = list(VARIANTS.keys()) if "all" in args.variant else args.variant
        run_smoke(limit=args.limit, variants=variants,
                  rerun_failures_of=args.rerun_failures_of)
