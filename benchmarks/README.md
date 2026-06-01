# ds-crew benchmark harness (dev-only)

Not shipped with the plugin. Measures ds-star / ds-star-plus / ds-spike on the
InfiAgent-DAEval (DABench) closed-form benchmark to convert reliability claims
into evidence (review item #1).

> **Status:** plumbing fully built and unit-tested. The full 257×3 run requires a
> real API budget — see "Full run" below. Until an operator runs it and commits the
> results, the README claim stays "not yet independently benchmarked."

## Layout

```
benchmarks/
  data/InfiAgent/      cloned upstream benchmark (gitignored; run fetch_data.py)
  score.py             vendored upstream deterministic scorer
  solvers.py           FakeSolver + ClaudeCliSolver + cost helpers
  runner.py            run_variant() → results.jsonl; load_dabench_questions()
  report.py            results.jsonl → summary.md + manifest.json
  fetch_data.py        clones InfiAgent-DAEval into data/
  prices.json          model pricing (generated from config/models.json)
  runs/smoke/          committed 2–3 question smoke run
  runs/<run-id>/       full runs (gitignored)
```

## Setup

```bash
# Clone benchmark data (one-time)
python3 benchmarks/fetch_data.py

# Run unit tests (no API key needed)
cd benchmarks && python3 -m unittest -v
```

## Smoke run (2–3 questions, dev validation)

A pre-committed smoke run lives in `benchmarks/runs/smoke/`. It validates the
pipeline end-to-end without a full paid run. To reproduce it:

```bash
# Requires ANTHROPIC_API_KEY
python3 - <<'PY'
import json, os, sys
sys.path.insert(0, "benchmarks")
from runner import run_variant, load_dabench_questions
from solvers import ClaudeCliSolver
from report import summarize, render_summary_md, build_manifest, main as report_main
import subprocess

QUESTIONS_PATH = "benchmarks/data/InfiAgent/examples/DA-Agent/da-dev-questions.jsonl"
LABELS_PATH    = "benchmarks/data/InfiAgent/examples/DA-Agent/da-dev-labels.jsonl"
PRICES_PATH    = "benchmarks/prices.json"
OUT_DIR        = "benchmarks/runs/smoke"
os.makedirs(OUT_DIR, exist_ok=True)

import json as _json
prices = _json.load(open(PRICES_PATH))
questions = load_dabench_questions(QUESTIONS_PATH, LABELS_PATH, limit=3)

for variant, skill, model_id in [
    ("ds-star",      "ds-star",      "claude-sonnet-4-6"),
    ("ds-star-plus", "ds-star-plus", "claude-sonnet-4-6"),
    ("ds-spike",     "ds-spike",     "claude-sonnet-4-6"),
]:
    solver = ClaudeCliSolver(skill, model_id, prices)
    run_variant(variant, questions, solver, prices, f"{OUT_DIR}/results.jsonl")

sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
report_main(
    f"{OUT_DIR}/results.jsonl",
    f"{OUT_DIR}/summary.md",
    f"{OUT_DIR}/manifest.json",
    commit_sha=sha,
    model_ids={"ds-star": "claude-sonnet-4-6", "ds-star-plus": "claude-sonnet-4-6", "ds-spike": "claude-sonnet-4-6"},
    prices=prices,
    seed=0,
)
print("Smoke run complete. See benchmarks/runs/smoke/summary.md")
PY
```

## Full run (operator step — real API budget)

> **Cost warning:** Running all 257 questions × 3 variants drives ~771 headless skill
> invocations. ds-spike multiplies further by its N sub-run count. Estimated cost:
> **$30–$150** at current prices (see `prices.json`). Confirm budget before running.

```bash
# Set ANTHROPIC_API_KEY, then:
python3 - <<'PY'
# Same as smoke run above, but remove limit=3
# Replace OUT_DIR with "benchmarks/runs/<date>"
PY
```

Until an operator runs this and commits the results under `benchmarks/runs/`,
the repo's credibility claim remains "not yet independently benchmarked."

## Updating prices

```bash
python3 config/models.py --emit-prices > benchmarks/prices.json
```
