#!/usr/bin/env python3
"""Generate comparison charts from the *actual* experiment result files.

Honest-comparison rules baked in:
  - Full-set accuracy (18-question DABench dev subset) only compares variants
    that ran the SAME set: no-tools, ds-star (plugin), ds-star (prompt).
  - The contested-question chart (Q7, Q8) compares methodologies
    (ds-star, ds-star-plus, ds-spike) on exactly those two questions — never
    mixed with full-set numbers (mixing hard-only with full-set is what made
    the results look artificially bad in early drafts).
  - Both strict accuracy and per-field score are shown; the gap between them
    is the "nearly right" signal (e.g. Q8's ddof-only divergence).

Usage:
    cd benchmarks && python3 experiments/generate_charts.py

Reads:
    experiments/results/exp_a_summary.json   (no-tools baseline)
    experiments/results/exp_b_results.jsonl   (ds-star plugin + prompt, full set)
    experiments/results/exp_d_methods.jsonl    (ds-star, ds-star-plus on Q7/Q8)
    experiments/results/exp_c_results.jsonl    (ds-spike N=3 on Q7/Q8)

Writes:
    docs/experiments/img/accuracy_comparison.png
    docs/experiments/img/hard_accuracy_comparison.png   (contested Q7/Q8 by method)
    docs/experiments/img/cost_comparison.png
    docs/experiments/img/accuracy_vs_cost.png
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_BENCH)
_RESULTS = os.path.join(_HERE, "results")
_IMG = os.path.join(_REPO, "docs", "experiments", "img")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

COLOR_STRICT = "#1f77b4"
COLOR_FIELD = "#9ecae1"
COLOR_COST = "#ff7f0e"


def _load_jsonl(name):
    path = os.path.join(_RESULTS, name)
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def _load_json(name):
    path = os.path.join(_RESULTS, name)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _agg(rows):
    """Aggregate a list of result rows into strict accuracy, field-score, cost."""
    n = len(rows)
    if not n:
        return None
    field = sum(r.get("field_score", float(r["correct"])) for r in rows) / n
    return {
        "n": n,
        "accuracy": sum(r["correct"] for r in rows) / n,
        "field_score": field,
        "cost_per_task": sum(r["cost_usd"] for r in rows) / n,
    }


def _grouped_accuracy(ax, labels, strict, field, title, subtitle):
    x = np.arange(len(labels))
    w = 0.38
    b1 = ax.bar(x - w / 2, strict, w, label="strict accuracy", color=COLOR_STRICT,
                edgecolor="white", linewidth=1.2)
    b2 = ax.bar(x + w / 2, field, w, label="field-score (partial credit)",
                color=COLOR_FIELD, edgecolor="white", linewidth=1.2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("accuracy", fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=14)
    ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha="center",
            fontsize=8.5, color="#666")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{bar.get_height():.0%}", ha="center", va="bottom",
                    fontsize=8, fontweight="bold")


def make_charts():
    os.makedirs(_IMG, exist_ok=True)

    # ── Data: full 18-question set ──────────────────────────────────────────────
    exp_a = _load_json("exp_a_summary.json")
    exp_b = _load_jsonl("exp_b_results.jsonl")
    from collections import defaultdict
    byv = defaultdict(list)
    for r in exp_b:
        byv[r["variant"]].append(r)

    full = []  # (label, strict, field, cost)
    if exp_a:
        full.append(("No-tools\n(text only)", exp_a.get("accuracy", 0),
                     exp_a.get("accuracy", 0), exp_a.get("cost_per_task", 0)))
    for v, lbl in [("ds-star-plugin", "DS-STAR\n(plugin)"),
                   ("ds-star-prompt", "DS-STAR\n(prompt)")]:
        a = _agg(byv.get(v, []))
        if a:
            full.append((lbl, a["accuracy"], a["field_score"], a["cost_per_task"]))

    # ── Data: contested questions Q7,Q8 by methodology ──────────────────────────
    exp_d = _load_jsonl("exp_d_methods.jsonl")
    exp_c = _load_jsonl("exp_c_results.jsonl")
    md = defaultdict(list)
    for r in exp_d:
        md[r["variant"]].append(r)
    contested = []
    for v, lbl in [("ds-star-plugin", "DS-STAR"),
                   ("ds-star-plus-plugin", "DS-STAR+")]:
        a = _agg(md.get(v, []))
        if a:
            contested.append((lbl, a["accuracy"], a["field_score"], a["cost_per_task"]))
    a = _agg(exp_c)
    if a:
        contested.append(("DS-Spike\n(N=3)", a["accuracy"], a["field_score"],
                          a["cost_per_task"]))

    # ── Chart 1: full-set accuracy (strict + field) ─────────────────────────────
    if full:
        fig, ax = plt.subplots(figsize=(max(6, len(full) * 1.7), 5))
        _grouped_accuracy(
            ax, [f[0] for f in full], [f[1] for f in full], [f[2] for f in full],
            "Accuracy on DABench dev subset",
            "18 questions · claude-sonnet-4-6 · code execution enabled")
        ax.axhline(0.9, color="#bbb", linestyle="--", linewidth=1)
        fig.tight_layout()
        out = os.path.join(_IMG, "accuracy_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # ── Chart 2: contested questions by method ──────────────────────────────────
    if contested:
        fig, ax = plt.subplots(figsize=(max(6, len(contested) * 1.8), 5))
        _grouped_accuracy(
            ax, [c[0] for c in contested], [c[1] for c in contested],
            [c[2] for c in contested],
            "Contested questions (Q7, Q8) by methodology",
            "Q7 passes · Q8 label contradicts its own constraint (ddof) — all methods agree")
        fig.tight_layout()
        out = os.path.join(_IMG, "hard_accuracy_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # ── Chart 3: cost per task ──────────────────────────────────────────────────
    cost_rows = [(f[0], f[3]) for f in full] + \
                ([("DS-Spike\n(N=3, Q7/Q8)", contested[-1][3])]
                 if contested and contested[-1][0].startswith("DS-Spike") else [])
    if cost_rows:
        fig, ax = plt.subplots(figsize=(max(6, len(cost_rows) * 1.6), 5))
        x = np.arange(len(cost_rows))
        bars = ax.bar(x, [c[1] for c in cost_rows], 0.6, color=COLOR_COST,
                      edgecolor="white", linewidth=1.2)
        ax.set_xticks(x)
        ax.set_xticklabels([c[0] for c in cost_rows], fontsize=9)
        ax.set_ylabel("USD / task", fontsize=10)
        ax.set_title("Cost per Task (USD)", fontsize=12, fontweight="bold", pad=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"${bar.get_height():.3f}", ha="center", va="bottom",
                    fontsize=8, fontweight="bold")
        fig.tight_layout()
        out = os.path.join(_IMG, "cost_comparison.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    # ── Chart 4: accuracy vs cost (full set) ────────────────────────────────────
    if full:
        fig, ax = plt.subplots(figsize=(7, 5))
        for lbl, strict, field, cost in full:
            ax.scatter(cost, strict, s=130, zorder=5, color=COLOR_STRICT)
            ax.annotate(lbl.replace("\n", " "), (cost, strict),
                        textcoords="offset points", xytext=(8, 4), fontsize=8)
        ax.set_xlabel("Cost per Task (USD)", fontsize=10)
        ax.set_ylabel("Strict accuracy", fontsize=10)
        ax.set_title("Accuracy vs Cost — DABench dev subset (18 q)",
                     fontsize=12, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0%}"))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        out = os.path.join(_IMG, "accuracy_vs_cost.png")
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")


if __name__ == "__main__":
    make_charts()
