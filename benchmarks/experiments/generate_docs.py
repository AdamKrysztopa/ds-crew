#!/usr/bin/env python3
"""Generate docs/experiments/*.md from experiment results.

Run after each experiment completes:
    cd benchmarks
    python3 experiments/generate_docs.py --exp A   # after exp_a
    python3 experiments/generate_docs.py --exp B   # after exp_b
    python3 experiments/generate_docs.py --exp C   # after exp_c
    python3 experiments/generate_docs.py --exp all # regenerate all
"""
import argparse
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_BENCH)
_DOCS = os.path.join(_REPO, "docs", "experiments")
_RESULTS = os.path.join(_HERE, "results")


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _smoke_summary():
    """Load smoke run results into a dict keyed by variant."""
    path = os.path.join(_BENCH, "runs", "smoke", "results.jsonl")
    if not os.path.exists(path):
        return {}
    rows = [json.loads(l) for l in open(path)]
    from collections import defaultdict
    by_v = defaultdict(list)
    for r in rows:
        by_v[r["variant"]].append(r)
    out = {}
    for v, rs in by_v.items():
        hard = [r for r in rs if r["hard"]]
        out[v] = {
            "n": len(rs),
            "accuracy": sum(r["correct"] for r in rs) / len(rs),
            "accuracy_hard": sum(r["correct"] for r in hard) / len(hard) if hard else 0,
            "cost_per_task": sum(r["cost_usd"] for r in rs) / len(rs),
            "tokens_per_task": sum(r["input_tokens"] + r["output_tokens"] for r in rs) / len(rs),
            "wrong_ids": [r["question_id"] for r in rs if not r["correct"]],
        }
    return out


def write_exp_a():
    summary_path = os.path.join(_RESULTS, "exp_a_summary.json")
    if not os.path.exists(summary_path):
        print("exp_a_summary.json not found — run exp_a_no_tools.py first")
        return
    a = _load_json(summary_path)
    smoke = _smoke_summary()

    rows = [
        ("no-tools (Exp A)", a["accuracy"], a["accuracy_hard"],
         a["cost_per_task"], a.get("tokens_per_task", 0)),
    ]
    for v in ["baseline", "ds-star", "ds-star-plus", "ds-spike"]:
        if v in smoke:
            s = smoke[v]
            rows.append((v, s["accuracy"], s["accuracy_hard"],
                         s["cost_per_task"], s["tokens_per_task"]))

    table = "| variant | n | accuracy | accuracy-hard | $/task | tokens/task |\n"
    table += "|---|---|---|---|---|---|\n"
    for label, acc, acc_h, cost, tok in rows:
        n = a["n"] if label == "no-tools (Exp A)" else smoke.get(label, {}).get("n", "—")
        table += f"| {label} | {n} | {acc:.1%} | {acc_h:.1%} | ${cost:.4f} | {tok:.0f} |\n"

    doc = f"""# Experiment A — No-Tools Baseline

**Date:** {__import__('datetime').date.today().isoformat()}
**Model:** {a.get('model', 'claude-sonnet-4-6')}
**Questions:** {a['n']} (same 15 as smoke run)

## Purpose

Establish the floor: how much does code execution actually help?

This experiment calls the Anthropic API directly with **no tools** — no Bash,
no Python execution, no file system access. Claude receives the first 50 rows of
the CSV as plain text and must answer purely by reasoning over those numbers.

Compare to the `baseline` variant (same model, minimal prompt, but full tool access)
to isolate the contribution of code execution vs. raw reasoning.

## Results

{table}

## Charts

![Accuracy comparison](img/accuracy_comparison.png)

![Hard accuracy comparison](img/hard_accuracy_comparison.png)

![Accuracy vs cost](img/accuracy_vs_cost.png)

## Key findings

- **No-tools accuracy:** {a['accuracy']:.1%} vs **tool-using baseline:** {smoke.get('baseline', {}).get('accuracy', 0):.1%}
- Gap of **{abs(a['accuracy'] - smoke.get('baseline', {}).get('accuracy', 0)):.1%}** shows how much code execution adds
- No-tools cost is **${a['cost_per_task']:.4f}/task** — {a['cost_per_task'] / smoke.get('baseline', {}).get('cost_per_task', 0.001):.1f}× {"cheaper" if a["cost_per_task"] < smoke.get("baseline", {}).get("cost_per_task", 999) else "more expensive"} than tool-using baseline
- Wrong IDs (no-tools): {a['wrong_ids']}

## Methodology

- **Model:** `{a.get('model', 'claude-sonnet-4-6')}` via Anthropic SDK, no tools
- **Data:** First 50 rows of each CSV embedded as plain text in the prompt
- **Prompt:** "Answer using only the data shown. Do not write or execute code."
- **Scoring:** Same DABench deterministic scorer as all other experiments
- **Script:** `benchmarks/experiments/exp_a_no_tools.py`

## Interpretation

The no-tools number represents what a user gets when they paste data into a chat
window and ask a question — no agent, no execution, just LLM reasoning over text.

The gap between this and the tool-using baseline is the value of the execution
environment itself, independent of any DS-STAR methodology.
"""

    out = os.path.join(_DOCS, "A-no-tools-baseline.md")
    os.makedirs(_DOCS, exist_ok=True)
    with open(out, "w") as f:
        f.write(doc)
    print(f"Written: {out}")


def write_exp_b():
    summary_path = os.path.join(_RESULTS, "exp_b_summary.json")
    if not os.path.exists(summary_path):
        print("exp_b_summary.json not found — run exp_b_multi_round.py first")
        return
    b = _load_json(summary_path)
    smoke = _smoke_summary()

    table = "| variant | n | accuracy | accuracy-hard | $/task | avg rounds |\n"
    table += "|---|---|---|---|---|---|\n"
    for v in ["baseline", "ds-star", "ds-star-plus"]:
        if v in smoke:
            s = smoke[v]
            table += (f"| {v} (single-turn) | {s['n']} | {s['accuracy']:.1%} | "
                      f"{s['accuracy_hard']:.1%} | ${s['cost_per_task']:.4f} | 1 |\n")
    for row in b.get("variants", []):
        avg_rounds = row.get('avg_rounds', '?')
        rounds_str = f"{avg_rounds:.1f}" if isinstance(avg_rounds, (int, float)) else str(avg_rounds)
        table += (f"| {row['variant']} (multi-round) | {row['n']} | {row['accuracy']:.1%} | "
                  f"{row['accuracy_hard']:.1%} | ${row['cost_per_task']:.4f} | "
                  f"{rounds_str} |\n")

    doc = f"""# Experiment B — Multi-Round Execution Harness

**Date:** {__import__('datetime').date.today().isoformat()}
**Model:** {b.get('model', 'claude-sonnet-4-6')}
**Questions:** {b.get('n', '?')}

## Purpose

Test whether the DS-STAR iterative loop — when actually enforced externally —
improves accuracy over single-turn execution.

In Experiment A and the smoke run, `claude -p` is single-turn. The DS-STAR loop
(analyze → code → execute → verify → backtrack) only matters if the code is really
executed and the output is fed back. This experiment does exactly that.

## Results

{table}

## Charts

![Accuracy comparison](img/accuracy_comparison.png)

![Hard accuracy comparison](img/hard_accuracy_comparison.png)

## Key findings

{b.get('findings', '(to be filled after run)')}

## Methodology

- External Python loop using Anthropic SDK tool-use API
- Intercepts `tool_use` blocks, executes Python/Bash locally, returns `tool_result`
- Loop continues until Claude emits a final text answer or round limit hit
- Records rounds, tokens/round, total cost, final answer
- **Script:** `benchmarks/experiments/exp_b_multi_round.py`
"""

    out = os.path.join(_DOCS, "B-multi-round-harness.md")
    os.makedirs(_DOCS, exist_ok=True)
    with open(out, "w") as f:
        f.write(doc)
    print(f"Written: {out}")


def write_exp_c():
    summary_path = os.path.join(_RESULTS, "exp_c_summary.json")
    if not os.path.exists(summary_path):
        print("exp_c_summary.json not found — run exp_c_spike.py first")
        return
    c = _load_json(summary_path)

    doc = f"""# Experiment C — Spike on Hard Questions

**Date:** {__import__('datetime').date.today().isoformat()}
**Questions:** Hard failures from previous experiments

## Purpose

Test whether N=3 ensemble voting (SpikeSolver) recovers questions that
all single-run variants got wrong. Spike's value is variance reduction:
if different approaches make different errors, majority vote wins.

## Results

![Hard accuracy comparison](img/hard_accuracy_comparison.png)

| variant | questions | correct | accuracy |
|---|---|---|---|
{chr(10).join(f"| {r['variant']} | {r['n']} | {r['correct']} | {r['accuracy']:.1%} |" for r in c.get('variants', []))}

## Sub-run breakdown (per question)

{c.get('subrun_table', '(generated after run)')}

## Key findings

{c.get('findings', '(to be filled after run)')}

## Methodology

- `SpikeSolver`: 3 parallel `claude -p` calls with diverse personas
  - cautious-statistician (Sonnet)
  - sql-join-first (Sonnet)
  - assumption-minimal (Opus)
- Majority vote on `@key[value]` tokens across 3 sub-runs
- Run only on questions that all single-turn variants got wrong
- **Script:** `benchmarks/experiments/exp_c_spike.py`
"""

    out = os.path.join(_DOCS, "C-spike-hard-questions.md")
    os.makedirs(_DOCS, exist_ok=True)
    with open(out, "w") as f:
        f.write(doc)
    print(f"Written: {out}")


def write_index(smoke):
    """Write docs/experiments/README.md index."""
    doc = """# ds-crew Benchmark Experiments

Three experiments measuring what actually makes the DS-STAR methodology valuable.

## The question

All tool-using variants (baseline, ds-star, ds-star-plus, ds-spike) scored
identically on a 15-question single-turn benchmark. Why? Because `claude -p`
is one-shot — the iterative loop never fires. These experiments isolate each
variable.

## Experiments

| # | Name | What it measures | Status |
|---|------|-----------------|--------|
| [A](A-no-tools-baseline.md) | No-tools baseline | Value of code execution itself | ✅ |
| [B](B-multi-round-harness.md) | Multi-round harness | Value of iterative DS-STAR loop | 🔄 |
| [C](C-spike-hard-questions.md) | Spike on hard Qs | Value of N=3 ensemble voting | 🔄 |

## Summary table (all experiments)

| variant | accuracy | accuracy-hard | $/task | notes |
|---|---|---|---|---|
| no-tools | — | — | — | Exp A |
| baseline (agent) | — | — | — | smoke run |
| ds-star (single-turn) | — | — | — | smoke run |
| ds-star-plus (single-turn) | — | — | — | smoke run |
| ds-star (multi-round) | — | — | — | Exp B |
| ds-star-plus (multi-round) | — | — | — | Exp B |
| ds-spike (N=3) | — | — | — | Exp C |

*(Updated after each experiment runs)*

## Charts

![Accuracy comparison](img/accuracy_comparison.png)
![Accuracy vs cost](img/accuracy_vs_cost.png)
"""
    out = os.path.join(_DOCS, "README.md")
    os.makedirs(_DOCS, exist_ok=True)
    with open(out, "w") as f:
        f.write(doc)
    print(f"Written: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", default="all",
                        choices=["A", "B", "C", "all"])
    args = parser.parse_args()

    smoke = _smoke_summary()
    write_index(smoke)

    if args.exp in ("A", "all"):
        write_exp_a()
    if args.exp in ("B", "all"):
        write_exp_b()
    if args.exp in ("C", "all"):
        write_exp_c()
