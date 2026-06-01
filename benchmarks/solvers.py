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

    def solve(self, qid, question, files):
        """Return a canned result for the given question ID.

        Args:
            qid: Question ID (key in the answers dict)
            question: Question text (ignored)
            files: List of files (ignored)

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
    """Drives one ds-crew skill per question via headless `claude -p`.
    Integration-only: requires ANTHROPIC_API_KEY and network. Not unit-tested
    (the plumbing it feeds IS unit-tested via FakeSolver)."""

    def __init__(self, skill_name, model_id, prices):
        self.skill_name = skill_name
        self.model_id = model_id
        self.prices = prices

    def solve(self, qid, question, files):
        t0 = _time.time()
        with _tempfile.TemporaryDirectory() as work_dir:
            manifest = self._invoke(question, files, work_dir)
        u = manifest.get("usage", {})
        return {
            "answer": manifest.get("answer", ""),
            "input_tokens": u.get("input_tokens", 0),
            "output_tokens": u.get("output_tokens", 0),
            "cost_usd": manifest.get("cost_usd"),
            "wall_time_s": manifest.get("latency_s") or (_time.time() - t0),
            "rounds": manifest.get("rounds", 0),
            "model_id": self.model_id,
        }

    def _invoke(self, question, files, work_dir):
        """Invoke the skill via headless claude -p and return parsed run_manifest.json."""
        prompt = f"/{self.skill_name}\n\n{question}"
        result = _subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True, text=True, cwd=work_dir
        )
        # Try to extract a run_manifest from the output if present,
        # otherwise build a minimal manifest from what we can parse
        manifest_path = _json_find_in(result.stdout, "run_manifest") or {}
        if not manifest_path:
            # Fall back: extract answer from stdout text
            answer = result.stdout.strip()
            return {"answer": answer, "usage": {}, "rounds": 1}
        return manifest_path
