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


def load_dabench_questions(questions_path, labels_path, limit=None):
    """Load and join DABench questions + labels into normalized dicts.

    Normalized format: {id (str), question, files (list), label (str), fmt (str), hard (bool)}
    Uses real field names from UPSTREAM_NOTES.md.
    """
    import json
    # Load labels by id
    labels = {}
    with open(labels_path) as f:
        for line in f:
            rec = json.loads(line)
            # common_answers is [[name, value], ...] — take first value
            if rec.get("common_answers"):
                labels[rec["id"]] = str(rec["common_answers"][0][1])
            else:
                labels[rec["id"]] = ""

    questions = []
    with open(questions_path) as f:
        for line in f:
            if limit and len(questions) >= limit:
                break
            q = json.loads(line)
            qid = q["id"]
            if qid not in labels:
                continue
            questions.append({
                "id": str(qid),
                "question": q["question"],
                "files": [q["file_name"]] if q.get("file_name") else [],
                "label": labels[qid],
                "fmt": _extract_fmt_key(q.get("format", "")),
                "hard": q.get("level") == "hard",
            })
    return questions


def _extract_fmt_key(fmt_string):
    """Extract the key name from a format string like '@mean_fare[mean_fare_value]' -> 'mean_fare'."""
    import re
    m = re.match(r"@(\w+)\[", fmt_string)
    return m.group(1) if m else ""
