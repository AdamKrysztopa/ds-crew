# Reviewer Credibility Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every unverified claim in ds-crew falsifiable (build a real DABench harness) and stop the repo asserting anything it has not measured, plus tidy structure and hygiene — addressing all 12 external-review items.

**Architecture:** One branch (`fix/reviewer-credibility-pass`), five phases in deliverable order A→B→C→D→E, each phase independently committable. The benchmark harness separates *plumbing* (scoring, cost-summing, reporting — fully unit-tested with deterministic fake solvers) from *LLM driving* (a `claude -p` adapter behind a `Solver` interface, smoke-validated only). Model IDs collapse to one canonical `config/models.json`. Where a "fix" would be theater (the loop driver, #3), we ship an after-the-fact run-log validator + a written statement of the limitation instead.

**Tech Stack:** Python 3.12 stdlib only (no PyYAML, no pip deps in shipped code), `unittest`, GitHub Actions, markdown. Benchmark harness may vendor InfiAgent-DAEval's scorer (dev-only, not shipped with the plugin).

**Conventions (match existing repo):**
- Test files are `test_*.py` living *next to* the module they test; they import flat (`from foo import bar`).
- CI (`.github/workflows/ci.yml`) auto-discovers `test_*.py` under `skills/*/scripts`, `scripts`, `.github/workflows/scripts`. New test dirs must be added to that loop (Task E2).
- Stdlib only. No network at import time.

---

## File Structure

**Created:**
- `config/models.json` — canonical alias→model-id→price map (single source of truth, #6).
- `config/models.py` — stdlib loader for the above (`load`, `tier_id`, `all_prices`, `price`, `--emit-prices` CLI).
- `config/test_models.py` — loader tests.
- `benchmarks/UPSTREAM_NOTES.md` — recorded DABench field names + vendored-scorer provenance (discovery output, #1).
- `benchmarks/score.py` — vendored upstream deterministic scorer + thin wrapper (#1).
- `benchmarks/test_score.py` — scorer wrapper tests (format-parse-fail = WRONG).
- `benchmarks/solvers.py` — `Solver` interface, `FakeSolver`, `ClaudeCliSolver`, cost helper, ds-spike sub-run summation (#1).
- `benchmarks/test_solvers.py` — solver plumbing + spike cost-sum tests.
- `benchmarks/runner.py` — drives variants per question → `results.jsonl` (#1).
- `benchmarks/test_runner.py` — runner tests with `FakeSolver`.
- `benchmarks/report.py` — `results.jsonl` → `summary.md` + `manifest.json` (#1).
- `benchmarks/test_report.py` — report/aggregation tests.
- `benchmarks/fetch_data.py` — clone/download DABench into `benchmarks/data/` (#1).
- `benchmarks/prices.json` — generated snapshot from `config/models.json` (#1/#6).
- `benchmarks/runs/smoke/` — committed 2–3 question smoke run (#1).
- `benchmarks/README.md` — how to run, budget warning, full-run operator command (#1).
- `skills/ds-spike/scripts/runlog.py` — run-log schema + validator (#3).
- `skills/ds-spike/scripts/test_runlog.py` — validator tests.
- `.github/workflows/scripts/check_skill_paths.py` — referenced-path resolver (#8).
- `.github/workflows/scripts/test_check_skill_paths.py` — path-resolver tests.
- `CHANGELOG.md` — Keep-a-Changelog history (#11).
- `docs/quickstart.md` — one dataset, one command, expected output (#12).

**Modified:**
- `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `docs/STATUS.md`, `skills/ds-star-plus/SKILL.md` — de-hype sweep (#2, #5).
- `skills/ds-star-plus/scripts/route_model.py` — source IDs from `config/models.json` (#6).
- `skills/ds-star-plus/scripts/run_manifest.py` — source rates from `config/models.json` (#6).
- `skills/ds-star-plus/references/model_routing.md`, `references/prompts.md`, `skills/ds-spike/references/personas.md` — reference config instead of re-listing IDs (#6).
- `skills/ds-spike/SKILL.md`, `skills/ds-search/SKILL.md` — verifier-as-reward circularity + different-instance rule (#4).
- `skills/ds-spike/SKILL.md`, `skills/ds-conduct/SKILL.md` — run-log emission + honest-limitation note (#3).
- `README.md`, `docs/USAGE.md` — Core 5 / Advanced 9 surface (#7).
- `.github/workflows/ci.yml` — add `benchmarks`, `config` test dirs + path smoke (#10, #8).
- `.gitignore` — ignore `benchmarks/runs/*` except the committed smoke run; ignore `benchmarks/data/` raw downloads.

---

## Phase A — Kill the contradiction (#2)

### Task A1: De-hype the docs

**Files:**
- Modify: `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `docs/STATUS.md`, `skills/ds-star-plus/SKILL.md`

- [ ] **Step 1: Enumerate every comparative-superiority claim**

Run and read the full output:
```bash
grep -rni -E 'cheaper|faster|better than|outperform|superior|more reliable|reduces? (cost|tokens)|cuts? .*overhead' \
  README.md ARCHITECTURE.md ROADMAP.md docs/STATUS.md skills/ds-star-plus/SKILL.md
```
Expected: a list including `skills/ds-star-plus/SKILL.md:12` ("cut the ~3.5x token overhead") and `:106`, plus README/ARCHITECTURE paper-figure references.

- [ ] **Step 2: Classify each hit**

For each line decide: (a) **paper figure** (3.5×, Table 4/6/2 numbers) → keep but ensure it is explicitly attributed to the DS-STAR paper, never to ds-crew; (b) **ds-crew measured claim** (none should exist) → none expected; (c) **implied-superiority framing** ("cut the overhead", "more reliable") → rewrite.

- [ ] **Step 3: Apply the canonical disclaimer**

Wherever v2's design is described as an improvement, ensure the text reads (or links to) the canonical line:
> v2 changes are design extensions grounded in the DS-STAR paper, not yet independently benchmarked.

In `README.md` "Status" / "Reference" sections this line already partly exists — make it the single authority and cross-link it from `ARCHITECTURE.md` and `skills/ds-star-plus/SKILL.md`. Reword `ds-star-plus/SKILL.md:12` from "cut the ~3.5x token overhead" to e.g. "aim to reduce the input-token overhead the paper reports (Table 6: 154,669 vs 44,691 tokens vs ReAct) — a design goal, not yet independently benchmarked."

- [ ] **Step 4: Verify no unattributed comparative claim remains**

Run:
```bash
grep -rni -E 'cheaper|faster|outperform|superior|more reliable' \
  README.md ARCHITECTURE.md ROADMAP.md docs/STATUS.md skills/ds-star-plus/SKILL.md \
  | grep -viE 'paper|table|arxiv|ds-star paper|not yet|design (goal|extension)'
```
Expected: **no output** (every remaining hit is paper-attributed or a disclaimed design goal).

- [ ] **Step 5: Commit**

```bash
git add README.md ARCHITECTURE.md ROADMAP.md docs/STATUS.md skills/ds-star-plus/SKILL.md
git commit -m "docs(#2): remove implied measured v2 superiority; attribute paper figures"
```

---

## Phase B — Benchmark harness (#1)

### Task B1: Scaffold `benchmarks/` and gitignore policy

**Files:**
- Create: `benchmarks/README.md` (stub), `benchmarks/runs/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Create the directory skeleton**

```bash
mkdir -p benchmarks/data benchmarks/runs
touch benchmarks/runs/.gitkeep
```

- [ ] **Step 2: Add gitignore rules**

Append to `.gitignore`:
```
# Benchmark harness: ignore raw data + run outputs, but keep the committed smoke run
benchmarks/data/*
!benchmarks/data/.gitkeep
benchmarks/runs/*
!benchmarks/runs/.gitkeep
!benchmarks/runs/smoke/
```
Then `touch benchmarks/data/.gitkeep`.

- [ ] **Step 3: Write the README stub**

`benchmarks/README.md`:
```markdown
# ds-crew benchmark harness (dev-only)

Not shipped with the plugin. Measures ds-star / ds-star-plus / ds-spike on the
InfiAgent-DAEval (DABench) closed-form benchmark to convert reliability claims
into evidence (review item #1).

> **Status:** plumbing built + smoke-validated on a 2–3 question subset. The full
> 257×3 run is an operator step (real API budget) — see "Full run" below.

Layout, usage, and the full-run command are filled in by Tasks B2–B8.
```

- [ ] **Step 4: Commit**

```bash
git add benchmarks/.gitkeep benchmarks/README.md benchmarks/runs/.gitkeep benchmarks/data/.gitkeep .gitignore
git commit -m "chore(#1): scaffold benchmarks/ dir + gitignore policy"
```

### Task B2: DISCOVERY — record real DABench field names + scorer provenance

> This task resolves the spec's "known unknowns." Do NOT assume field names — read them.

**Files:**
- Create: `benchmarks/UPSTREAM_NOTES.md`
- Modify: `benchmarks/fetch_data.py` (create)

- [ ] **Step 1: Fetch the upstream data**

Write `benchmarks/fetch_data.py` to clone InfiAgent-DAEval into `benchmarks/data/` (stdlib `subprocess` + `git clone --depth 1 https://github.com/InfiAgent/InfiAgent`, or the dataset's documented location). Run it.

- [ ] **Step 2: Inspect actual files and record fields**

Open the actual question file(s) (e.g. the DA-Eval JSONL) and the answer/label file. Record in `benchmarks/UPSTREAM_NOTES.md`:
  - exact path(s) of the questions file and the labels file,
  - the **exact JSON keys** for: question id, question text, attached file name(s), the closed-form label/answer, the answer-format spec, and any difficulty/hard flag,
  - the exact module path + function name of the upstream deterministic scorer,
  - the upstream license + commit SHA (for attribution).

- [ ] **Step 3: Sanity-print 2 records**

In `UPSTREAM_NOTES.md`, paste two real (redacted if needed) records so later tasks code against reality.

- [ ] **Step 4: Commit**

```bash
git add benchmarks/fetch_data.py benchmarks/UPSTREAM_NOTES.md
git commit -m "chore(#1): record DABench field names + upstream scorer provenance"
```

### Task B3: Vendor the deterministic scorer (TDD)

**Files:**
- Create: `benchmarks/score.py`, `benchmarks/test_score.py`

- [ ] **Step 1: Write the failing test**

`benchmarks/test_score.py` (adjust the label/format keys to the names recorded in UPSTREAM_NOTES.md):
```python
import unittest
from score import score_answer

class TestScore(unittest.TestCase):
    def test_correct_closed_form_matches(self):
        # format spec + label taken from a real record in UPSTREAM_NOTES.md
        self.assertTrue(score_answer(prediction="@answer[42]", label="42",
                                     fmt="@answer[<number>]"))
    def test_wrong_value_is_incorrect(self):
        self.assertFalse(score_answer(prediction="@answer[41]", label="42",
                                      fmt="@answer[<number>]"))
    def test_format_parse_failure_counts_as_wrong(self):
        # unparseable prediction must score WRONG, never raise / never be excluded
        self.assertFalse(score_answer(prediction="I think it is about forty-two",
                                      label="42", fmt="@answer[<number>]"))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd benchmarks && python3 -m unittest test_score -v`
Expected: FAIL (`No module named 'score'`).

- [ ] **Step 3: Vendor the scorer + wrap it**

Copy the upstream scorer module into `benchmarks/score.py` verbatim under its license header (attribution per UPSTREAM_NOTES.md). Add a thin wrapper:
```python
def score_answer(prediction, label, fmt):
    """Return True iff `prediction` matches `label` under the upstream scorer.
    Any parse/format failure returns False (WRONG) — never raises, never excludes.
    Delegates the actual comparison to the vendored upstream scorer; this wrapper
    only guarantees the parse-failure-as-wrong contract."""
    try:
        return bool(_upstream_is_correct(prediction, label, fmt))  # name per UPSTREAM_NOTES
    except Exception:
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd benchmarks && python3 -m unittest test_score -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add benchmarks/score.py benchmarks/test_score.py
git commit -m "feat(#1): vendor DABench deterministic scorer; parse-failure = WRONG"
```

### Task B4: `Solver` interface + `FakeSolver` + cost helper (TDD)

**Files:**
- Create: `benchmarks/solvers.py`, `benchmarks/test_solvers.py`

- [ ] **Step 1: Write the failing test**

`benchmarks/test_solvers.py`:
```python
import unittest
from solvers import FakeSolver, compute_cost

PRICES = {  # input,output USD per Mtok — mirrors config/models.json
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}

class TestSolvers(unittest.TestCase):
    def test_fake_solver_returns_canned_result(self):
        s = FakeSolver({"q1": {"answer": "42", "input_tokens": 1000,
                               "output_tokens": 200, "wall_time_s": 1.0, "rounds": 3}})
        r = s.solve("q1", question="...", files=[])
        self.assertEqual(r["answer"], "42")
        self.assertEqual(r["rounds"], 3)

    def test_compute_cost_uses_prices(self):
        c = compute_cost("claude-sonnet-4-6",
                         {"input_tokens": 1_000_000, "output_tokens": 0}, PRICES)
        self.assertAlmostEqual(c, 3.0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd benchmarks && python3 -m unittest test_solvers -v`
Expected: FAIL (`No module named 'solvers'`).

- [ ] **Step 3: Implement the interface + fake + cost helper**

`benchmarks/solvers.py`:
```python
"""Solver adapters for the benchmark harness.

A Solver maps (question_id, question_text, files) -> result dict with keys:
  answer, input_tokens, output_tokens, wall_time_s, rounds
ds-spike additionally reports `subruns` and SUMS their tokens/cost (see SpikeCliSolver).
"""

def compute_cost(model_id, usage, prices):
    rate = prices.get(model_id, {"input": 0.0, "output": 0.0})
    return (usage.get("input_tokens", 0) / 1_000_000) * rate["input"] + \
           (usage.get("output_tokens", 0) / 1_000_000) * rate["output"]

class FakeSolver:
    """Deterministic solver for unit tests. No LLM, no network."""
    def __init__(self, answers_by_qid):
        self._answers = answers_by_qid
    def solve(self, qid, question, files):
        return dict(self._answers[qid])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd benchmarks && python3 -m unittest test_solvers -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add benchmarks/solvers.py benchmarks/test_solvers.py
git commit -m "feat(#1): Solver interface, FakeSolver, price-based cost helper"
```

### Task B5: ds-spike sub-run cost summation (TDD)

**Files:**
- Modify: `benchmarks/solvers.py`, `benchmarks/test_solvers.py`

- [ ] **Step 1: Write the failing test**

Append to `benchmarks/test_solvers.py`:
```python
    def test_spike_sums_all_subrun_tokens_and_cost(self):
        from solvers import summarize_spike
        subruns = [
            {"answer": "42", "input_tokens": 1000, "output_tokens": 100,
             "wall_time_s": 2.0, "rounds": 3, "model_id": "claude-sonnet-4-6"},
            {"answer": "42", "input_tokens": 2000, "output_tokens": 300,
             "wall_time_s": 3.0, "rounds": 4, "model_id": "claude-sonnet-4-6"},
        ]
        agg = summarize_spike(subruns, consensus="42", prices=PRICES)
        self.assertEqual(agg["input_tokens"], 3000)   # SUM, not max/avg
        self.assertEqual(agg["output_tokens"], 400)
        self.assertAlmostEqual(agg["cost_usd"], (3000/1e6)*3.0 + (400/1e6)*15.0)
        self.assertEqual(agg["wall_time_s"], 3.0)      # parallel -> max wall time
        self.assertEqual(agg["rounds"], 4)             # report the max rounds
        self.assertEqual(agg["answer"], "42")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd benchmarks && python3 -m unittest test_solvers -v`
Expected: FAIL (`cannot import name 'summarize_spike'`).

- [ ] **Step 3: Implement `summarize_spike`**

Append to `benchmarks/solvers.py`:
```python
def summarize_spike(subruns, consensus, prices):
    """Aggregate N parallel ds-spike sub-runs. Tokens and cost SUM across all
    sub-runs (the ensemble's true price); wall time is the max (they run in
    parallel); rounds reported as the max observed."""
    total_in = sum(s["input_tokens"] for s in subruns)
    total_out = sum(s["output_tokens"] for s in subruns)
    cost = sum(compute_cost(s["model_id"],
                            {"input_tokens": s["input_tokens"],
                             "output_tokens": s["output_tokens"]}, prices)
               for s in subruns)
    return {
        "answer": consensus,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cost_usd": cost,
        "wall_time_s": max(s["wall_time_s"] for s in subruns),
        "rounds": max(s["rounds"] for s in subruns),
        "n_subruns": len(subruns),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd benchmarks && python3 -m unittest test_solvers -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add benchmarks/solvers.py benchmarks/test_solvers.py
git commit -m "feat(#1): ds-spike cost SUMS all N parallel sub-runs"
```

### Task B6: `runner.py` → `results.jsonl` (TDD)

**Files:**
- Create: `benchmarks/runner.py`, `benchmarks/test_runner.py`

- [ ] **Step 1: Write the failing test**

`benchmarks/test_runner.py`:
```python
import json, os, tempfile, unittest
from runner import run_variant
from solvers import FakeSolver

PRICES = {"claude-sonnet-4-6": {"input": 3.0, "output": 15.0}}

class TestRunner(unittest.TestCase):
    def test_run_variant_writes_one_row_per_question(self):
        questions = [
            {"id": "q1", "question": "...", "files": [], "label": "42",
             "fmt": "@answer[<number>]", "hard": False},
            {"id": "q2", "question": "...", "files": [], "label": "7",
             "fmt": "@answer[<number>]", "hard": True},
        ]
        solver = FakeSolver({
            "q1": {"answer": "@answer[42]", "input_tokens": 100, "output_tokens": 10,
                   "wall_time_s": 1.0, "rounds": 2, "model_id": "claude-sonnet-4-6"},
            "q2": {"answer": "@answer[8]", "input_tokens": 200, "output_tokens": 20,
                   "wall_time_s": 1.5, "rounds": 3, "model_id": "claude-sonnet-4-6"},
        })
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "results.jsonl")
            run_variant("ds-star-plus", questions, solver, PRICES, out)
            rows = [json.loads(l) for l in open(out)]
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["variant"] for r in rows}, {"ds-star-plus"})
        by = {r["question_id"]: r for r in rows}
        self.assertTrue(by["q1"]["correct"])     # 42 == 42
        self.assertFalse(by["q2"]["correct"])    # 8 != 7
        self.assertIn("cost_usd", by["q1"])
        self.assertIn("input_tokens", by["q1"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd benchmarks && python3 -m unittest test_runner -v`
Expected: FAIL (`No module named 'runner'`).

- [ ] **Step 3: Implement `run_variant`**

`benchmarks/runner.py`:
```python
"""Drive one solver variant over the benchmark questions -> results.jsonl.

Each row: variant, question_id, hard, correct, input_tokens, output_tokens,
cost_usd, wall_time_s, rounds.
"""
import json
from score import score_answer
from solvers import compute_cost

def run_variant(variant, questions, solver, prices, out_path):
    with open(out_path, "a") as fh:
        for q in questions:
            r = solver.solve(q["id"], question=q["question"], files=q["files"])
            usage = {"input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"]}
            cost = r.get("cost_usd")
            if cost is None:
                cost = compute_cost(r.get("model_id", ""), usage, prices)
            row = {
                "variant": variant,
                "question_id": q["id"],
                "hard": q.get("hard", False),
                "correct": bool(score_answer(r["answer"], q["label"], q["fmt"])),
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": round(cost, 6),
                "wall_time_s": r["wall_time_s"],
                "rounds": r["rounds"],
            }
            fh.write(json.dumps(row) + "\n")
    return out_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd benchmarks && python3 -m unittest test_runner -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add benchmarks/runner.py benchmarks/test_runner.py
git commit -m "feat(#1): runner emits per-question×variant results.jsonl"
```

### Task B7: `report.py` → `summary.md` + `manifest.json` (TDD)

**Files:**
- Create: `benchmarks/report.py`, `benchmarks/test_report.py`

- [ ] **Step 1: Write the failing test**

`benchmarks/test_report.py`:
```python
import json, unittest
from report import summarize, render_summary_md, build_manifest

ROWS = [
    {"variant": "ds-star", "question_id": "q1", "hard": False, "correct": True,
     "input_tokens": 100, "output_tokens": 10, "cost_usd": 0.001, "wall_time_s": 1.0, "rounds": 2},
    {"variant": "ds-star", "question_id": "q2", "hard": True, "correct": False,
     "input_tokens": 300, "output_tokens": 30, "cost_usd": 0.003, "wall_time_s": 2.0, "rounds": 4},
]

class TestReport(unittest.TestCase):
    def test_summarize_computes_accuracy_and_per_task(self):
        s = summarize(ROWS)["ds-star"]
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["accuracy"], 0.5)        # 1 of 2
        self.assertAlmostEqual(s["accuracy_hard"], 0.0)   # 0 of 1 hard
        self.assertAlmostEqual(s["cost_per_task"], 0.002) # (0.001+0.003)/2
        self.assertAlmostEqual(s["tokens_per_task"], 220) # (110+330)/2
        self.assertEqual(s["median_rounds"], 3)           # median(2,4)

    def test_render_summary_md_has_table_header(self):
        md = render_summary_md(summarize(ROWS))
        self.assertIn("| variant | n | accuracy | accuracy-hard | $/task | tokens/task | median rounds |", md)
        self.assertIn("ds-star", md)

    def test_manifest_has_required_keys(self):
        m = build_manifest(commit_sha="abc123", model_ids={"ds-star": "claude-sonnet-4-6"},
                           prices={"claude-sonnet-4-6": {"input": 3.0, "output": 15.0}},
                           n=2, seed=0)
        for k in ("commit_sha", "model_ids", "prices", "date", "n", "seed"):
            self.assertIn(k, m)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd benchmarks && python3 -m unittest test_report -v`
Expected: FAIL (`No module named 'report'`).

- [ ] **Step 3: Implement report**

`benchmarks/report.py`:
```python
"""Aggregate results.jsonl into summary.md + manifest.json."""
import json, statistics
from datetime import date

def summarize(rows):
    out = {}
    variants = sorted({r["variant"] for r in rows})
    for v in variants:
        rs = [r for r in rows if r["variant"] == v]
        hard = [r for r in rs if r["hard"]]
        out[v] = {
            "n": len(rs),
            "accuracy": sum(r["correct"] for r in rs) / len(rs) if rs else 0.0,
            "accuracy_hard": (sum(r["correct"] for r in hard) / len(hard)) if hard else 0.0,
            "cost_per_task": sum(r["cost_usd"] for r in rs) / len(rs) if rs else 0.0,
            "tokens_per_task": sum(r["input_tokens"] + r["output_tokens"] for r in rs) / len(rs) if rs else 0.0,
            "median_rounds": statistics.median(r["rounds"] for r in rs) if rs else 0,
        }
    return out

def render_summary_md(summary):
    head = "| variant | n | accuracy | accuracy-hard | $/task | tokens/task | median rounds |"
    sep = "|---|---|---|---|---|---|---|"
    lines = [head, sep]
    for v, s in summary.items():
        lines.append(f"| {v} | {s['n']} | {s['accuracy']:.3f} | {s['accuracy_hard']:.3f} "
                     f"| {s['cost_per_task']:.4f} | {s['tokens_per_task']:.0f} | {s['median_rounds']} |")
    return "\n".join(lines) + "\n"

def build_manifest(commit_sha, model_ids, prices, n, seed):
    return {"commit_sha": commit_sha, "model_ids": model_ids, "prices": prices,
            "date": date.today().isoformat(), "n": n, "seed": seed}

def main(results_path, summary_path, manifest_path, commit_sha, model_ids, prices, seed):
    rows = [json.loads(l) for l in open(results_path)]
    summary = summarize(rows)
    open(summary_path, "w").write(render_summary_md(summary))
    n = max((s["n"] for s in summary.values()), default=0)
    json.dump(build_manifest(commit_sha, model_ids, prices, n, seed),
              open(manifest_path, "w"), indent=2, sort_keys=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd benchmarks && python3 -m unittest test_report -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add benchmarks/report.py benchmarks/test_report.py
git commit -m "feat(#1): report.py -> summary.md table + manifest.json"
```

### Task B8: Real `ClaudeCliSolver` + smoke run + operator docs

> The fake solvers proved the plumbing. This task adds the real LLM adapter and validates the pipeline end-to-end on 2–3 questions. The full 257×3 run stays an operator step.

**Files:**
- Modify: `benchmarks/solvers.py`, `benchmarks/README.md`
- Create: `benchmarks/runs/smoke/results.jsonl`, `benchmarks/runs/smoke/summary.md`, `benchmarks/runs/smoke/manifest.json`, `benchmarks/prices.json`

- [ ] **Step 1: Implement the headless adapter**

Append `ClaudeCliSolver` (and `SpikeCliSolver`) to `benchmarks/solvers.py`. It shells out to `claude -p` in headless mode, invoking the named skill against the question + data files, parses the answer and the usage/`cost_usd` from the run manifest (`run_manifest.py` already emits `usage`, `latency_s`, `cost_usd`), and returns the result dict. `SpikeCliSolver` launches N sub-runs and calls `summarize_spike(...)`. Mark this module section clearly as integration-only (network + API key).

```python
import json, subprocess, time

class ClaudeCliSolver:
    """Drives one ds-crew skill per question via headless `claude -p`.
    Integration-only: requires ANTHROPIC_API_KEY and network. Not unit-tested
    (the plumbing it feeds IS unit-tested via FakeSolver)."""
    def __init__(self, skill, model_id, prices):
        self.skill, self.model_id, self.prices = skill, model_id, prices
    def solve(self, qid, question, files):
        t0 = time.time()
        manifest = self._invoke(question, files)   # parses run_manifest.json
        u = manifest.get("usage", {})
        return {
            "answer": manifest["answer"],
            "input_tokens": u.get("input_tokens", 0),
            "output_tokens": u.get("output_tokens", 0),
            "cost_usd": manifest.get("cost_usd"),
            "wall_time_s": manifest.get("latency_s") or (time.time() - t0),
            "rounds": manifest.get("rounds", 0),
            "model_id": self.model_id,
        }
    # _invoke(...) builds the `claude -p` command for self.skill and returns the
    # parsed run_manifest.json — implement against the headless CLI contract.
```

- [ ] **Step 2: Generate `benchmarks/prices.json` from the canonical config**

> Depends on Phase D Task D1 (`config/models.py`). If executing strictly in order, defer this sub-step until D1 lands, or temporarily hand-write `prices.json` and regenerate after D1.

Run: `python3 config/models.py --emit-prices > benchmarks/prices.json`
Expected: a JSON map of `model_id -> {input, output}` identical to `config/models.json` prices.

- [ ] **Step 3: Run the smoke subset (2–3 questions, all three variants)**

Pick 2–3 DABench questions (include ≥1 hard). Run each variant via the CLI solver, writing into `benchmarks/runs/smoke/`. Then build the report:
```bash
python3 - <<'PY'
# orchestration: load smoke questions, run ds-star / ds-star-plus / ds-spike,
# append to runs/smoke/results.jsonl, then report.main(...) for summary+manifest
PY
```
Expected artifacts: `runs/smoke/results.jsonl` (rows = questions×3 variants), `runs/smoke/summary.md` (the table), `runs/smoke/manifest.json` (commit SHA, model IDs, prices, date, N, seed).

- [ ] **Step 4: Verify the smoke artifacts**

Run:
```bash
test -s benchmarks/runs/smoke/results.jsonl && \
grep -q "median rounds" benchmarks/runs/smoke/summary.md && \
python3 -c "import json;m=json.load(open('benchmarks/runs/smoke/manifest.json'));assert all(k in m for k in ('commit_sha','model_ids','prices','date','n','seed'))" && \
echo OK
```
Expected: `OK`.

- [ ] **Step 5: Fill in `benchmarks/README.md` operator section**

Document the layout, the exact full-run command, and a budget warning:
> **Full run (operator step):** `python3 benchmarks/runner.py --all --n 257` over all 3 variants drives ~771 headless skill runs (ds-spike multiplies by its sub-run count). Estimated cost: **\$X–\$Y** at current prices — confirm budget before running. Until an operator runs this and commits the results, the README claim stays "not yet independently benchmarked."

- [ ] **Step 6: Commit**

```bash
git add benchmarks/solvers.py benchmarks/README.md benchmarks/prices.json benchmarks/runs/smoke/
git commit -m "feat(#1): headless claude -p adapter + committed smoke run + operator docs"
```

---

## Phase C — Reliability honesty (#3, #4, #5)

### Task C1: Run-log schema + validator (TDD) — the honest #3

**Files:**
- Create: `skills/ds-spike/scripts/runlog.py`, `skills/ds-spike/scripts/test_runlog.py`

- [ ] **Step 1: Write the failing test**

`skills/ds-spike/scripts/test_runlog.py`:
```python
import unittest
from runlog import validate_runlog, REQUIRED_FIELDS

class TestRunlog(unittest.TestCase):
    def test_valid_log_passes(self):
        log = {"rounds": 3, "verifier_verdicts": [{"round": 1, "score": 2},
                                                   {"round": 2, "score": 3},
                                                   {"round": 3, "score": 4}],
               "oscillated": False, "subrun_cost_usd": [0.10, 0.12]}
        errs = validate_runlog(log)
        self.assertEqual(errs, [])
    def test_missing_field_is_reported(self):
        errs = validate_runlog({"rounds": 3})
        self.assertTrue(any("verifier_verdicts" in e for e in errs))
    def test_verdicts_must_cover_each_round(self):
        log = {"rounds": 3, "verifier_verdicts": [{"round": 1, "score": 4}],
               "oscillated": False, "subrun_cost_usd": []}
        errs = validate_runlog(log)
        self.assertTrue(any("verdict" in e.lower() for e in errs))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd skills/ds-spike/scripts && python3 -m unittest test_runlog -v`
Expected: FAIL (`No module named 'runlog'`).

- [ ] **Step 3: Implement the validator**

`skills/ds-spike/scripts/runlog.py`:
```python
"""Run-log schema + validator for the ds-spike / ds-conduct loops (review item #3).

IMPORTANT — what this does and does NOT do: a Python validator cannot force the
model to actually run the verifier/routing/oscillation loop. It only checks that a
structured log claiming the loop ran is well-formed, so deviations are *detectable
after the fact*, not *impossible*. This is the honest boundary; see the SKILL.md
"What this cannot guarantee" notes.
"""
REQUIRED_FIELDS = ("rounds", "verifier_verdicts", "oscillated", "subrun_cost_usd")

def validate_runlog(log):
    errs = []
    for f in REQUIRED_FIELDS:
        if f not in log:
            errs.append(f"missing required field: {f}")
    if errs:
        return errs
    rounds = log["rounds"]
    seen = {v.get("round") for v in log["verifier_verdicts"]}
    for r in range(1, rounds + 1):
        if r not in seen:
            errs.append(f"no verifier verdict recorded for round {r}")
    return errs

if __name__ == "__main__":
    import json, sys
    errs = validate_runlog(json.load(open(sys.argv[1])))
    print("\n".join(errs) if errs else "OK")
    sys.exit(1 if errs else 0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd skills/ds-spike/scripts && python3 -m unittest test_runlog -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/ds-spike/scripts/runlog.py skills/ds-spike/scripts/test_runlog.py
git commit -m "feat(#3): run-log schema + validator (honest after-the-fact check)"
```

### Task C2: Document the #3 limitation + wire run-log into the prose

**Files:**
- Modify: `skills/ds-spike/SKILL.md`, `skills/ds-conduct/SKILL.md`

- [ ] **Step 1: Add the honesty note to both SKILLs**

In each, add a short subsection titled **"What this cannot guarantee"** stating: the loop is markdown driving a model across long context; no process enforces that the verifier/routing/oscillation steps actually ran. Mitigation: the skill MUST emit a structured run-log (fields: `rounds`, `verifier_verdicts`, `oscillated`, `subrun_cost_usd`) validated by `skills/ds-spike/scripts/runlog.py`, which makes deviations detectable, not impossible.

- [ ] **Step 2: Instruct the skill to emit + validate the log**

Add a final step to each skill's "How to run it": *Emit `runlog.json` with the required fields and validate it: `python3 .../runlog.py runlog.json` — if it reports errors, the loop was not followed; do not present the answer as verified.*

- [ ] **Step 3: Verify references resolve**

Run: `grep -n "runlog.py" skills/ds-spike/SKILL.md skills/ds-conduct/SKILL.md`
Expected: a relative path from each SKILL to `skills/ds-spike/scripts/runlog.py` that exists on disk (ds-conduct references `../ds-spike/scripts/runlog.py`).

- [ ] **Step 4: Commit**

```bash
git add skills/ds-spike/SKILL.md skills/ds-conduct/SKILL.md
git commit -m "docs(#3): state what prose loops cannot guarantee; wire run-log validator"
```

### Task C3: Verifier-as-reward circularity note + different-instance rule (#4)

**Files:**
- Modify: `skills/ds-spike/SKILL.md`, `skills/ds-search/SKILL.md`

- [ ] **Step 1: Add the circularity subsection to both SKILLs**

Add **"Verifier-as-reward circularity (important)"**: ds-spike and ds-search both *score* candidate answers with the same A1-rubric verifier (`../ds-star-plus/scripts/verify_schema.py` + `references/rubric.md`) they use *inside* each solver. A biased judge is therefore amplified, not caught — the meta-aggregator inherits the same blind spot.

- [ ] **Step 2: State the enforcement rule**

Add: **the meta-aggregator MUST run on a different model instance (and preferably a different tier) than the in-solver verifier.** Concretely: if solvers verify with Opus, the cross-run aggregator must be a separate Opus instance with an independent prompt, or a different tier — never reuse the same verifier call/context. Note this is a mitigation, not a proof of independence.

- [ ] **Step 3: Verify**

Run: `grep -ni "circularity\|different (model )*instance\|meta-aggregator" skills/ds-spike/SKILL.md skills/ds-search/SKILL.md`
Expected: matches in both files.

- [ ] **Step 4: Commit**

```bash
git add skills/ds-spike/SKILL.md skills/ds-search/SKILL.md
git commit -m "docs(#4): document verifier-as-reward circularity; require distinct aggregator instance"
```

### Task C4: Back or remove the 3.5× reduction claim (#5)

**Files:**
- Modify: `skills/ds-star-plus/SKILL.md` (and any line found in Step 1)

- [ ] **Step 1: Find the reduction claim**

Run: `grep -rn "3.5" skills/ README.md ARCHITECTURE.md`
Expected: `ds-star-plus/SKILL.md:12` and `:106`, plus paper-attributed mentions.

- [ ] **Step 2: Distinguish and rewrite**

The paper's 3.5× (DS-STAR's input tokens vs ReAct, Table 6) stays, attributed. Any claim that ds-star-plus *itself* achieves a measured token reduction must be removed or reframed as an unverified design goal pending the benchmark (#1). Reword `:106` and `:12` so no number is presented as a ds-crew measurement. If Phase B's smoke run produced a real tokens/task figure, you may cite it explicitly as "smoke run, N=3, see benchmarks/runs/smoke/summary.md" — never extrapolated to a headline claim.

- [ ] **Step 3: Verify**

Run: `grep -rn "3.5" skills/ds-star-plus/SKILL.md | grep -viE "table|paper|design goal|not yet|smoke run"`
Expected: **no output**.

- [ ] **Step 4: Commit**

```bash
git add skills/ds-star-plus/SKILL.md
git commit -m "docs(#5): remove unmeasured token-reduction claim; keep paper figure attributed"
```

---

## Phase D — Structure (#6, #7, #8)

### Task D1: Canonical `config/models.json` + loader (TDD)

**Files:**
- Create: `config/models.json`, `config/models.py`, `config/test_models.py`

- [ ] **Step 1: Write the failing test**

`config/test_models.py`:
```python
import json, subprocess, sys, unittest
from models import load, tier_id, all_prices, price

class TestModels(unittest.TestCase):
    def test_tier_id_resolves(self):
        self.assertEqual(tier_id("opus"), load()["tiers"]["opus"]["id"])
    def test_all_prices_keyed_by_model_id(self):
        p = all_prices()
        self.assertIn(tier_id("haiku"), p)
        self.assertIn("input", p[tier_id("haiku")])
    def test_price_lookup(self):
        self.assertEqual(price(tier_id("sonnet"))["output"],
                         load()["tiers"]["sonnet"]["price_per_mtok"]["output"])
    def test_emit_prices_cli(self):
        out = subprocess.check_output([sys.executable, "models.py", "--emit-prices"])
        self.assertIn(tier_id("opus"), json.loads(out))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd config && python3 -m unittest test_models -v`
Expected: FAIL (`No module named 'models'`).

- [ ] **Step 3: Create the canonical data + loader**

`config/models.json` (prices mirror current `run_manifest.py` rates):
```json
{
  "tiers": {
    "haiku":  {"id": "claude-haiku-4-5",  "roles": ["analyzer", "planner_init", "finalizer", "debug_trim"], "price_per_mtok": {"input": 1.0,  "output": 5.0}},
    "sonnet": {"id": "claude-sonnet-4-6", "roles": ["planner_next", "coder", "router", "debug_fix"],        "price_per_mtok": {"input": 3.0,  "output": 15.0}},
    "opus":   {"id": "claude-opus-4-8",   "roles": ["verifier"],                                            "price_per_mtok": {"input": 15.0, "output": 75.0}}
  },
  "order": ["haiku", "sonnet", "opus"]
}
```

`config/models.py`:
```python
"""Canonical model alias/price registry (review item #6). Single source of truth.
Stdlib only. Consumers read tiers/ids/prices from here instead of hardcoding."""
import json, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "models.json")

def load():
    with open(_PATH) as fh:
        return json.load(fh)

def tier_id(tier):
    return load()["tiers"][tier]["id"]

def all_prices():
    return {t["id"]: t["price_per_mtok"] for t in load()["tiers"].values()}

def price(model_id):
    return all_prices()[model_id]

if __name__ == "__main__":
    if "--emit-prices" in sys.argv:
        json.dump(all_prices(), sys.stdout, indent=2, sort_keys=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd config && python3 -m unittest test_models -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add config/models.json config/models.py config/test_models.py
git commit -m "feat(#6): canonical config/models.json + stdlib loader"
```

### Task D2: Source `route_model.py` IDs from config (TDD, behavior unchanged)

**Files:**
- Modify: `skills/ds-star-plus/scripts/route_model.py`
- Create: `skills/ds-star-plus/scripts/test_route_model.py`

- [ ] **Step 1: Write the failing test (no hardcoded IDs + unchanged behavior)**

`skills/ds-star-plus/scripts/test_route_model.py`:
```python
import re, unittest
from route_model import pick_model, TIERS

class TestRouteModel(unittest.TestCase):
    def test_behavior_unchanged(self):
        self.assertEqual(pick_model("verifier"), "claude-opus-4-8")
        self.assertEqual(pick_model("analyzer"), "claude-haiku-4-5")
        self.assertEqual(pick_model("planner_next"), "claude-sonnet-4-6")
        self.assertEqual(pick_model("planner_next", attempt=2), "claude-opus-4-8")
        self.assertEqual(pick_model("router", oscillating=True), "claude-opus-4-8")
        self.assertEqual(pick_model("finalizer", hard=True), "claude-sonnet-4-6")
    def test_tiers_sourced_from_config_not_hardcoded(self):
        src = open("route_model.py").read()
        # the literal model-id strings must not appear in routing source
        self.assertNotIn("claude-opus-4-8", src)
        self.assertNotIn("claude-sonnet-4-6", src)
        self.assertNotIn("claude-haiku-4-5", src)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd skills/ds-star-plus/scripts && python3 -m unittest test_route_model -v`
Expected: FAIL (`test_tiers_sourced_from_config_not_hardcoded` — IDs still hardcoded; the `__main__` block also has them).

- [ ] **Step 3: Replace the hardcoded `TIERS`/`ORDER` with a config read**

In `route_model.py`, replace the `TIERS = {...}` / `ORDER = [...]` literals with a walk-up loader (keeps the module flat-importable; deliberate ~6-line duplication avoids sys.path coupling in the flat-test layout):
```python
import json, os

def _models_config():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        p = os.path.join(d, "config", "models.json")
        if os.path.exists(p):
            with open(p) as fh:
                return json.load(fh)
        d = os.path.dirname(d)
    raise FileNotFoundError("config/models.json not found")

_CFG = _models_config()
TIERS = {tier: spec["id"] for tier, spec in _CFG["tiers"].items()}
ORDER = _CFG["order"]
```
Also update the `__main__` self-check `checks` list: keep the expected values (they are assertions about behavior, and `test_route_model.py` now covers them) OR delete the redundant `__main__` block in favor of the new test. **Delete the `__main__` checks block** so no literal IDs remain in the source.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd skills/ds-star-plus/scripts && python3 -m unittest test_route_model -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/ds-star-plus/scripts/route_model.py skills/ds-star-plus/scripts/test_route_model.py
git commit -m "refactor(#6): route_model sources IDs from config/models.json"
```

### Task D3: Source `run_manifest.py` rates from config (TDD)

**Files:**
- Modify: `skills/ds-star-plus/scripts/run_manifest.py`, `skills/ds-star-plus/scripts/test_run_manifest.py`

- [ ] **Step 1: Add a failing test for config-sourced rates**

Append to `skills/ds-star-plus/scripts/test_run_manifest.py`:
```python
    def test_rates_sourced_from_config_not_hardcoded(self):
        src = open("run_manifest.py").read()
        self.assertNotIn("claude-opus-4-8", src)
        self.assertNotIn("claude-sonnet-4-6", src)
        self.assertNotIn("claude-haiku-4-5", src)

    def test_cost_matches_config_prices(self):
        from run_manifest import estimate_cost
        # sonnet input price is 3.0/Mtok in config/models.json
        c = estimate_cost("claude-sonnet-4-6", {"input_tokens": 1_000_000, "output_tokens": 0})
        self.assertAlmostEqual(c, 3.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd skills/ds-star-plus/scripts && python3 -m unittest test_run_manifest -v`
Expected: FAIL (`test_rates_sourced_from_config_not_hardcoded` — `_RATES_PER_MTOK` still hardcodes IDs; the `__main__` demo also has one).

- [ ] **Step 3: Replace `_RATES_PER_MTOK` with a config read**

In `run_manifest.py`, replace the literal `_RATES_PER_MTOK = {...}` with the same walk-up loader pattern, building rates from config prices:
```python
import json, os

def _models_config():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        p = os.path.join(d, "config", "models.json")
        if os.path.exists(p):
            with open(p) as fh:
                return json.load(fh)
        d = os.path.dirname(d)
    raise FileNotFoundError("config/models.json not found")

_RATES_PER_MTOK = {
    spec["id"]: (spec["price_per_mtok"]["input"], spec["price_per_mtok"]["output"])
    for spec in _models_config()["tiers"].values()
}
```
Change the `__main__` demo line that hardcodes `"claude-sonnet-4-6"` to derive it from config, e.g. `next(iter(_RATES_PER_MTOK))`, so no literal ID remains.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd skills/ds-star-plus/scripts && python3 -m unittest test_run_manifest -v`
Expected: PASS (all prior tests + 2 new).

- [ ] **Step 5: Commit**

```bash
git add skills/ds-star-plus/scripts/run_manifest.py skills/ds-star-plus/scripts/test_run_manifest.py
git commit -m "refactor(#6): run_manifest sources rates from config/models.json"
```

### Task D4: Point the doc tables at the canonical config (#6)

**Files:**
- Modify: `skills/ds-star-plus/references/model_routing.md`, `skills/ds-star-plus/references/prompts.md`, `skills/ds-spike/references/personas.md`

- [ ] **Step 1: Add a canonical-source banner to `model_routing.md`**

At the top of the tier table add: *"Concrete model IDs are defined in `config/models.json` (the single source of truth, review item #6). The table below mirrors it; if they diverge, config wins — update config, not this table."*

- [ ] **Step 2: Replace inline IDs in `prompts.md` and `personas.md` with tier names + pointer**

In `prompts.md` lines 5–6 and `personas.md` line 20, replace the literal `claude-…` IDs with tier names (Haiku/Sonnet/Opus) and a pointer to `config/models.json` / `model_routing.md`. Keep the prose meaning intact.

- [ ] **Step 3: Verify only `model_routing.md` still lists concrete IDs (intentionally, as a mirror)**

Run:
```bash
grep -rln -E 'claude-(opus|sonnet|haiku)-' skills/*/references/
```
Expected: only `skills/ds-star-plus/references/model_routing.md` (the labeled mirror). `prompts.md` and `personas.md` no longer match.

- [ ] **Step 4: Commit**

```bash
git add skills/ds-star-plus/references/model_routing.md skills/ds-star-plus/references/prompts.md skills/ds-spike/references/personas.md
git commit -m "docs(#6): reference config/models.json instead of re-listing model IDs"
```

### Task D5: Core 5 / Advanced 9 README surface (#7)

**Files:**
- Modify: `README.md`, `docs/USAGE.md`

- [ ] **Step 1: Regroup the skills table in README**

Split the existing "The fourteen skills" table into two labelled tables:
  - **Core 5** — `ds-conduct`, `ds-star-plus`, `ds-spike`, `data-profile`, `eda-narrative` (the everyday entry points).
  - **Advanced 9** — `ds-star`, `ds-clarify`, `ds-model`, `ds-memory`, `ds-env-setup`, and the four Track-L primitives `ds-verify`, `ds-reconcile`, `ds-vote`, `ds-search`.
  Add one sentence per group explaining when to reach past Core into Advanced. Note explicitly that the four primitives (`ds-verify`/`ds-reconcile`/`ds-vote`/`ds-search`) are extracted internals of `ds-star-plus`/`ds-spike`, surfaced standalone for power users.

- [ ] **Step 2: Mirror the split in `docs/USAGE.md`**

Add a short "Core vs Advanced" preface to the chooser so the two surfaces stay consistent. Do **not** change any skill's behavior, frontmatter, or references — docs only.

- [ ] **Step 3: Verify no skill files changed**

Run: `git status --porcelain skills/`
Expected: **no output** (Task D5 touches only README.md and docs/USAGE.md).

- [ ] **Step 4: Commit**

```bash
git add README.md docs/USAGE.md
git commit -m "docs(#7): split skill surface into Core 5 / Advanced 9"
```

### Task D6: SKILL.md path-resolution smoke test (#8, TDD)

**Files:**
- Create: `.github/workflows/scripts/check_skill_paths.py`, `.github/workflows/scripts/test_check_skill_paths.py`

- [ ] **Step 1: Write the failing test**

`.github/workflows/scripts/test_check_skill_paths.py`:
```python
import os, tempfile, unittest
from check_skill_paths import referenced_paths, unresolved_paths

class TestCheckSkillPaths(unittest.TestCase):
    def test_extracts_reference_and_script_paths(self):
        text = "see `references/rubric.md` and `../ds-star-plus/scripts/route_model.py`"
        got = referenced_paths(text)
        self.assertIn("references/rubric.md", got)
        self.assertIn("../ds-star-plus/scripts/route_model.py", got)

    def test_unresolved_detected_for_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            skill = os.path.join(d, "SKILL.md")
            open(skill, "w").write("ref `references/nope.md`")
            missing = unresolved_paths(skill)
            self.assertEqual(missing, ["references/nope.md"])

    def test_real_repo_skills_all_resolve(self):
        # the actual repo must have zero unresolved references
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        import glob
        bad = {}
        for sk in glob.glob(os.path.join(root, "skills", "*", "SKILL.md")):
            u = unresolved_paths(sk)
            if u:
                bad[sk] = u
        self.assertEqual(bad, {}, f"unresolved skill references: {bad}")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd .github/workflows/scripts && python3 -m unittest test_check_skill_paths -v`
Expected: FAIL (`No module named 'check_skill_paths'`).

- [ ] **Step 3: Implement the resolver**

`.github/workflows/scripts/check_skill_paths.py`:
```python
#!/usr/bin/env python3
"""Assert every references/ and scripts/ path named in a SKILL.md resolves on disk
(review item #8). Stdlib only; run from repo root or via CI.

    python3 check_skill_paths.py                 # check all skills/*/SKILL.md
    python3 check_skill_paths.py path/to/SKILL.md
"""
import glob, os, re, sys

# matches optional ../ hops then references/<...>.<ext> or scripts/<...>.<ext>
_PAT = re.compile(r"(?:\.\./)*(?:references|scripts)/[\w./-]+\.(?:md|py|json|txt)")

def referenced_paths(text):
    # de-dup, preserve order
    seen, out = set(), []
    for m in _PAT.findall(text):
        if m not in seen:
            seen.add(m); out.append(m)
    return out

def unresolved_paths(skill_path):
    base = os.path.dirname(os.path.abspath(skill_path))
    text = open(skill_path).read()
    missing = []
    for rel in referenced_paths(text):
        if not os.path.exists(os.path.normpath(os.path.join(base, rel))):
            missing.append(rel)
    return missing

if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob("skills/*/SKILL.md"))
    failed = False
    for p in paths:
        for rel in unresolved_paths(p):
            print(f"[MISSING] {p}: {rel}")
            failed = True
    print("ALL RESOLVE" if not failed else "UNRESOLVED REFERENCES FOUND")
    sys.exit(1 if failed else 0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd .github/workflows/scripts && python3 -m unittest test_check_skill_paths -v`
Expected: PASS (3 tests). If `test_real_repo_skills_all_resolve` fails, a SKILL.md names a path that does not exist — fix the reference (a real bug this test exists to catch) before proceeding.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/scripts/check_skill_paths.py .github/workflows/scripts/test_check_skill_paths.py
git commit -m "test(#8): SKILL.md references/ and scripts/ paths must resolve on disk"
```

---

## Phase E — Hygiene (#9–#12)

### Task E1: Verify LICENSE (#9)

**Files:**
- Inspect: `LICENSE`

- [ ] **Step 1: Confirm LICENSE exists and is non-trivial**

Run: `test -s LICENSE && head -1 LICENSE`
Expected: prints `MIT License`. (Already present — no new file. If absent, add an MIT LICENSE for "Adam Krysztopa, 2026".)

- [ ] **Step 2: No commit needed** unless a file was added.

### Task E2: Extend CI to run the new suites + path smoke (#10, #8)

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add new test dirs to the unittest loop**

In `ci.yml`, extend the `for d in ...` list to include `benchmarks` and `config`:
```yaml
          for d in skills/*/scripts scripts .github/workflows/scripts benchmarks config; do
```
(`benchmarks` tests use only stdlib + the vendored scorer, which is committed — no pip install needed. If the vendored scorer imports a third-party package, add a `pip install` step guarded to the benchmarks job only.)

- [ ] **Step 2: Add an explicit path-resolution step**

After the frontmatter lint step, add:
```yaml
      - name: Check SKILL.md referenced paths resolve
        run: python3 .github/workflows/scripts/check_skill_paths.py
```

- [ ] **Step 3: Verify the loop locally (mimic CI)**

Run:
```bash
fail=0
for d in skills/*/scripts scripts .github/workflows/scripts benchmarks config; do
  if ls "$d"/test_*.py >/dev/null 2>&1; then (cd "$d" && python3 -m unittest) || fail=1; fi
done
python3 .github/workflows/scripts/check_skill_paths.py || fail=1
echo "exit=$fail"
```
Expected: `exit=0`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(#10,#8): run benchmarks/config suites + SKILL.md path smoke"
```

### Task E3: Add CHANGELOG.md (#11)

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Write a Keep-a-Changelog file**

`CHANGELOG.md`:
```markdown
# Changelog

All notable changes to ds-crew are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses semver.

## [Unreleased] — Reviewer Credibility Pass
### Added
- `benchmarks/` harness: vendored DABench scorer, runner, report, smoke run (#1).
- `config/models.json` single source of truth for model IDs + prices (#6).
- SKILL.md reference-path resolution smoke test in CI (#8, #10).
- Run-log schema + validator for ds-spike/ds-conduct loops (#3).
- `docs/quickstart.md` (#12); `CHANGELOG.md` (#11).
### Changed
- README/docs no longer imply measured v2 superiority; paper figures attributed (#2, #5).
- README skill surface split into Core 5 / Advanced 9 (#7).
- `route_model.py` / `run_manifest.py` source IDs + rates from `config/models.json` (#6).
### Documented
- Verifier-as-reward circularity + distinct-aggregator-instance rule in ds-spike/ds-search (#4).
- The honest limits of prose-driven loops (#3).

## [1.3.0] — 2026-05-31
- Final Plan phases 0–4 (see ROADMAP.md / git history).
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(#11): add CHANGELOG.md"
```

### Task E4: Quickstart with a real dataset + command + expected output (#12)

**Files:**
- Create: `docs/quickstart.md`
- Modify: `README.md` (link the quickstart near the top)

- [ ] **Step 1: Pick the bundled sample**

Use one small dataset already referenced by `docs/datasets.md` / `scripts/fetch_datasets.py` (or bundle a tiny CSV under `docs/` if none is committed). Confirm it loads with stdlib `csv`.

- [ ] **Step 2: Write the quickstart**

`docs/quickstart.md`: one dataset, one command (e.g. running `ds-star-plus` against the sample with a single concrete question), and the **expected output** (the final answer + a line from the run manifest). Keep it copy-pasteable and deterministic enough to recognize success.

- [ ] **Step 3: Link from README**

Add a "Quickstart" link directly under the title/intro of `README.md`.

- [ ] **Step 4: Verify the command runs**

Execute the quickstart command exactly as written; confirm the output matches what the doc claims (adjust the doc to reality if not — never the reverse).

- [ ] **Step 5: Commit**

```bash
git add docs/quickstart.md README.md
git commit -m "docs(#12): quickstart — one dataset, one command, expected output"
```

---

## Final verification (run before opening the PR)

- [ ] **All tests pass (mimic CI):**
```bash
fail=0
for d in skills/*/scripts scripts .github/workflows/scripts benchmarks config; do
  if ls "$d"/test_*.py >/dev/null 2>&1; then echo "== $d =="; (cd "$d" && python3 -m unittest) || fail=1; fi
done
python3 .github/workflows/scripts/lint_frontmatter.py || fail=1
python3 .github/workflows/scripts/validate_manifests.py || fail=1
python3 .github/workflows/scripts/check_skill_paths.py || fail=1
echo "OVERALL exit=$fail"
```
Expected: `OVERALL exit=0`.

- [ ] **No hardcoded model IDs remain in routing/manifest source:**
```bash
grep -rn -E 'claude-(opus|sonnet|haiku)-' skills/ds-star-plus/scripts/route_model.py skills/ds-star-plus/scripts/run_manifest.py
```
Expected: **no output**.

- [ ] **No unattributed superiority claims remain:**
```bash
grep -rni -E 'cheaper|outperform|superior|more reliable' README.md ARCHITECTURE.md skills/ds-star-plus/SKILL.md \
  | grep -viE 'paper|table|not yet|design (goal|extension)|smoke run'
```
Expected: **no output**.

- [ ] **Smoke benchmark artifacts present:** `benchmarks/runs/smoke/{results.jsonl,summary.md,manifest.json}` exist and `summary.md` contains the table header.

- [ ] **Spec coverage:** items #1–#12 each map to a task (A1=#2; B1–B8=#1; C1–C2=#3; C3=#4; C4=#5; D1–D4=#6; D5=#7; D6=#8; E1=#9; E2=#10; E3=#11; E4=#12). ✅

---

## Notes for the implementer

- **Discovery gates code (Task B2).** Do not write `score.py` / `runner.py` field access until `UPSTREAM_NOTES.md` records the *real* DABench keys. The test stubs in B3/B6 use placeholder key names (`label`, `fmt`, `hard`) — rename them to the actual keys you recorded.
- **The 6-line `_models_config()` walk-loader is duplicated** in `route_model.py` and `run_manifest.py` on purpose: it keeps both modules flat-importable by their existing `test_*.py` without sys.path manipulation. Do not "DRY" it into a shared module that breaks the flat-import test convention.
- **Phase ordering caveat:** Task B8 Step 2 generates `benchmarks/prices.json` from `config/models.py`, which lands in Phase D. If you execute strictly A→B→C→D→E, hand-write `prices.json` in B8 and regenerate it after D1, or pull Task D1 forward to before B8. Either is fine; note it in the commit.
- **TDD discipline:** every code task is red→green→commit. Do not implement before the test fails for the right reason.
