"""Solver adapters for the benchmark harness.

A Solver maps (question_id, question_text, files) -> result dict with keys:
  answer, input_tokens, output_tokens, wall_time_s, rounds
ds-spike additionally reports `subruns` and SUMS their tokens/cost (see summarize_spike).
"""


def compute_cost(model_id, usage, prices):
    """Compute cost in USD for a given model and token usage.

    Args:
        model_id: Model identifier (e.g., "claude-sonnet-4-6")
        usage: Dict with "input_tokens" and "output_tokens"
        prices: Dict mapping model_id -> {"input": USD/Mtok, "output": USD/Mtok}

    Returns:
        Cost in USD. Returns 0.0 if model_id not found in prices.
    """
    rate = prices.get(model_id, {"input": 0.0, "output": 0.0})
    return (usage.get("input_tokens", 0) / 1_000_000) * rate["input"] + \
           (usage.get("output_tokens", 0) / 1_000_000) * rate["output"]


class FakeSolver:
    """Deterministic solver for unit tests. No LLM, no network."""

    def __init__(self, answers_by_qid):
        """Initialize with canned answers.

        Args:
            answers_by_qid: Dict mapping question_id -> result dict
                           (answer, input_tokens, output_tokens, wall_time_s, rounds)
        """
        self._answers = answers_by_qid

    def solve(self, qid, question, files, format_str="", constraints=""):
        """Return a canned result for the given question ID.

        Args:
            qid: Question ID (key in the answers dict)
            question: Question text (ignored)
            files: List of files (ignored)
            format_str: DABench format spec (ignored)
            constraints: DABench constraints (ignored)

        Returns:
            Dict with answer, input_tokens, output_tokens, wall_time_s, rounds
        """
        return dict(self._answers[qid])


def summarize_spike(subruns, consensus, prices):
    """Aggregate N parallel ds-spike sub-runs.

    Tokens and cost SUM across all sub-runs (the ensemble's true price);
    wall time is the max (they run in parallel); rounds reported as the max observed.

    Args:
        subruns: List of subrun dicts, each with input_tokens, output_tokens,
                 wall_time_s, rounds, model_id, answer
        consensus: The agreed-upon consensus answer
        prices: Dict mapping model_id -> {"input": USD/Mtok, "output": USD/Mtok}

    Returns:
        Dict with aggregated result:
          answer, input_tokens, output_tokens, cost_usd, wall_time_s, rounds, n_subruns
    """
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


import json as _json
import os as _os
import subprocess as _subprocess
import tempfile as _tempfile
import time as _time


def _json_find_in(text, key):
    """Try to parse JSON from text and return value at key. Returns None on failure."""
    try:
        data = _json.loads(text)
        return data.get(key)
    except Exception:
        return None


class ClaudeCliSolver:
    """Drives one variant per question via headless `claude -p`.
    Integration-only: requires ANTHROPIC_API_KEY and network. Not unit-tested
    (the plumbing it feeds IS unit-tested via FakeSolver).

    Args:
        variant_prompt: Preamble injected before the question (variant-specific instructions).
        model_id: Model to report in result rows (cost comes from total_cost_usd).
        prices: Price dict (used only when total_cost_usd is missing from response).
        data_dir: Directory where benchmark data files live; files are copied to work_dir.
    """

    def __init__(self, variant_prompt, model_id, prices, data_dir=None):
        self.variant_prompt = variant_prompt
        self.model_id = model_id
        self.prices = prices
        self.data_dir = data_dir

    def solve(self, qid, question, files, format_str="", constraints=""):
        t0 = _time.time()
        with _tempfile.TemporaryDirectory() as work_dir:
            # Copy data files into work_dir so claude's tools can find them
            if self.data_dir:
                for fname in files:
                    src = _os.path.join(self.data_dir, fname)
                    if _os.path.exists(src):
                        import shutil
                        shutil.copy(src, work_dir)
            result = self._invoke(question, files, work_dir,
                                  format_str=format_str, constraints=constraints)
        wall = _time.time() - t0
        return {
            "answer": result.get("answer", ""),
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "cost_usd": result.get("cost_usd"),
            "wall_time_s": wall,
            "rounds": result.get("rounds", 1),
            "model_id": self.model_id,
        }

    def _invoke(self, question, files, work_dir, format_str="", constraints=""):
        """Call claude -p and parse the --output-format json response."""
        file_list = ", ".join(files) if files else "(none)"
        constraints_line = f"\n\nConstraints: {constraints}" if constraints else ""
        fmt_line = f"\n\nRequired answer format: {format_str}" if format_str else ""
        prompt = (
            f"{self.variant_prompt}\n\n"
            f"Available data file(s) in your working directory: {file_list}\n\n"
            f"Question: {question}{constraints_line}{fmt_line}"
        )
        # --dangerously-skip-permissions is required for headless execution:
        # without it claude -p blocks indefinitely waiting for bash approval.
        proc = _subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json",
             "--dangerously-skip-permissions"],
            capture_output=True, text=True, cwd=work_dir,
        )
        try:
            data = _json.loads(proc.stdout)
        except Exception:
            return {"answer": proc.stdout.strip(), "input_tokens": 0,
                    "output_tokens": 0, "cost_usd": 0.0, "rounds": 1}

        answer = data.get("result", "")
        usage = data.get("usage", {})
        # All token types that count toward billing
        in_tok = (usage.get("input_tokens", 0)
                  + usage.get("cache_creation_input_tokens", 0)
                  + usage.get("cache_read_input_tokens", 0))
        out_tok = usage.get("output_tokens", 0)
        cost = data.get("total_cost_usd") or compute_cost(
            self.model_id,
            {"input_tokens": in_tok, "output_tokens": out_tok},
            self.prices,
        )
        return {
            "answer": answer,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": cost,
            "rounds": 1,  # claude -p is one-shot; skill rounds not observable externally
        }


import concurrent.futures as _futures
import sys as _sys


# Persona prefixes injected before the ds-star-plus skill body (N=3 default panel)
_SPIKE_PERSONAS = [
    ("cautious-statistician", "claude-sonnet-4-6",
     "You are a cautious statistician. Before computing anything, check distributions, "
     "null counts, sample sizes, and outliers. Flag every silent row drop.\n\n"),
    ("sql-join-first", "claude-sonnet-4-6",
     "You are a SQL/join-first analyst. Think in keys, joins, and group-bys. "
     "Check for duplicate fan-out and wrong aggregation grain.\n\n"),
    ("assumption-minimal", "claude-opus-4-8",
     "You are an assumption-minimal literalist. Do exactly what the question specifies "
     "— nothing more, nothing less. Surface every implicit assumption.\n\n"),
]


class SpikeSolver:
    """True ds-spike: N independent ClaudeCliSolver runs with diverse personas,
    reconciled by majority vote on extracted @key[value] tokens.

    Costs SUM across all N sub-runs (per spec). Wall time is MAX (parallel semantics).
    """

    def __init__(self, skill_body, prices, data_dir=None, n=3):
        """
        Args:
            skill_body: ds-star-plus SKILL.md content (frontmatter already stripped).
            prices: Price dict for cost computation.
            data_dir: Directory where benchmark data files live.
            n: Number of parallel solvers (default 3).
        """
        self.skill_body = skill_body
        self.prices = prices
        self.data_dir = data_dir
        self.n = n

    def solve(self, qid, question, files, format_str="", constraints=""):
        personas = _SPIKE_PERSONAS[:self.n]
        t0 = _time.time()

        def run_persona(persona_name, model_id, persona_prefix):
            prompt = persona_prefix + self.skill_body
            solver = ClaudeCliSolver(
                variant_prompt=prompt,
                model_id=model_id,
                prices=self.prices,
                data_dir=self.data_dir,
            )
            result = solver.solve(qid, question=question, files=files,
                                  format_str=format_str, constraints=constraints)
            result["persona"] = persona_name
            return result

        # Run personas in parallel threads (each spawns its own claude -p subprocess)
        with _futures.ThreadPoolExecutor(max_workers=self.n) as pool:
            futs = [pool.submit(run_persona, name, mid, prefix)
                    for name, mid, prefix in personas]
            sub_results = [f.result() for f in _futures.as_completed(futs)]

        # Aggregate: majority vote on each @key[value] token across sub-runs
        consensus = self._vote(sub_results, format_str)

        return {
            "answer": consensus,
            "input_tokens": sum(r["input_tokens"] for r in sub_results),
            "output_tokens": sum(r["output_tokens"] for r in sub_results),
            "cost_usd": sum(r.get("cost_usd") or 0 for r in sub_results),
            "wall_time_s": max(r["wall_time_s"] for r in sub_results),
            "rounds": max(r["rounds"] for r in sub_results),
            "n_subruns": len(sub_results),
            "subruns": [{"persona": r["persona"], "answer": r["answer"],
                         "cost_usd": r.get("cost_usd")} for r in sub_results],
        }

    @staticmethod
    def _vote(sub_results, format_str):
        """Majority vote on @key[value] tokens across sub-run answers.

        For each expected key in format_str, collect the value each sub-run
        produced, return the majority value (ties → first seen).
        """
        import re
        token_pat = re.compile(r"@(\w+)\[(.*?)\]")

        # Collect per-key votes from each sub-run
        votes = {}  # key -> list of values
        for r in sub_results:
            for name, val in token_pat.findall(r.get("answer", "")):
                votes.setdefault(name, []).append(val)

        if not votes:
            # No tokens found in any sub-run — return the first non-empty answer
            for r in sub_results:
                if r.get("answer"):
                    return r["answer"]
            return ""

        # Build consensus answer with majority value per key
        parts = []
        for key, vals in votes.items():
            majority = max(set(vals), key=vals.count)
            parts.append(f"@{key}[{majority}]")
        return " ".join(parts)
