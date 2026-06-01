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
    with open(results_path) as f:
        rows = [json.loads(l) for l in f]
    summary = summarize(rows)
    with open(summary_path, "w") as f:
        f.write(render_summary_md(summary))
    n = max((s["n"] for s in summary.values()), default=0)
    with open(manifest_path, "w") as f:
        json.dump(build_manifest(commit_sha, model_ids, prices, n, seed),
                  f, indent=2, sort_keys=True)
