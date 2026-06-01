"""Drive one solver variant over the benchmark questions -> results.jsonl.

Each row: variant, question_id, hard, correct, input_tokens, output_tokens,
cost_usd, wall_time_s, rounds.
"""
import json
import os
from score import score_answer
from solvers import compute_cost

def run_variant(variant, questions, solver, prices, out_path):
    """Run a solver variant over questions, appending rows to out_path (JSONL).

    Appending is intentional for running multiple variants into the same file.
    HOWEVER: if this variant already has rows in the file, this will RAISE to
    prevent silent duplication. Delete or move the file before re-running.
    """
    # Check for existing rows for this variant to prevent silent duplication
    if os.path.exists(out_path):
        with open(out_path) as f:
            existing_variants = {json.loads(l)["variant"] for l in f if l.strip()}
        if variant in existing_variants:
            raise ValueError(
                f"results.jsonl already contains rows for variant '{variant}'. "
                f"Delete or move {out_path} before re-running."
            )

    with open(out_path, "a") as fh:
        for q in questions:
            r = solver.solve(q["id"], question=q["question"], files=q["files"])
            usage = {"input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"]}
            cost = r.get("cost_usd")
            if cost is None:
                cost = compute_cost(r.get("model_id", ""), usage, prices)
            subqs = q.get("subquestions") or [{"fmt": q["fmt"], "label": q["label"]}]
            row = {
                "variant": variant,
                "question_id": q["id"],
                "hard": q.get("hard", False),
                "correct": all(score_answer(r["answer"], sq["label"], sq["fmt"]) for sq in subqs),
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
            # common_answers is [[name, value], ...] — store ALL sub-answers
            if rec.get("common_answers"):
                labels[rec["id"]] = [[str(x[0]), str(x[1])] for x in rec["common_answers"]]
            else:
                labels[rec["id"]] = []

    questions = []
    with open(questions_path) as f:
        for line in f:
            if limit and len(questions) >= limit:
                break
            q = json.loads(line)
            qid = q["id"]
            if qid not in labels:
                continue
            sub_answers = labels[qid]
            questions.append({
                "id": str(qid),
                "question": q["question"],
                "files": [q["file_name"]] if q.get("file_name") else [],
                # Keep label + fmt for backward compat (use first sub-answer)
                "label": sub_answers[0][1] if sub_answers else "",
                "fmt": _extract_fmt_key(q.get("format", "")),
                "hard": q.get("level") == "hard",
                # All sub-answers for multi-part scoring
                "subquestions": [
                    {"fmt": str(rec[0]), "label": str(rec[1])}
                    for rec in sub_answers
                ],
            })
    return questions


def _extract_fmt_key(fmt_string):
    """Extract the key name from a format string like '@mean_fare[mean_fare_value]' -> 'mean_fare'."""
    import re
    m = re.match(r"@(\w+)\[", fmt_string)
    return m.group(1) if m else ""
