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
