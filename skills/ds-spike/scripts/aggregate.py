#!/usr/bin/env python3
"""Reconcile N data-scientist solver records into a consensus + minority report.

Used by the ds-spike skill (Stage 4). Each solver posts a record to the shared blackboard:

    {"id": "solver-2 (sql-first, sonnet, seed=7)",
     "answer": 41.7,            # number, numeric string, or text
     "sufficient": True,        # did that solver's own verifier pass?
     "assumptions": ["refunds excluded", "EUR"]}

aggregate() clusters matching answers (numeric within rel_tol, or normalized text), weights
verified solvers above unverified ones, and returns the consensus and the dissenting clusters.
See references/aggregation.md. Stdlib only.
"""
import re

WEIGHT_SUFFICIENT = 1.0
WEIGHT_UNVERIFIED = 0.25


def _as_float(x):
    """Return x as a float if it is numeric (ignoring a trailing % and thousands commas), else None."""
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace(",", "")
        if s.endswith("%"):
            s = s[:-1].strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _norm_str(x):
    return re.sub(r"\s+", " ", str(x).strip().lower())


def answers_match(a, b, rel_tol=1e-3, abs_tol=1e-9):
    """True if two answers should be treated as the same result."""
    fa, fb = _as_float(a), _as_float(b)
    if fa is not None and fb is not None:
        return abs(fa - fb) <= max(abs_tol, rel_tol * max(abs(fa), abs(fb)))
    return _norm_str(a) == _norm_str(b)


def _weight(record):
    return WEIGHT_SUFFICIENT if record.get("sufficient") else WEIGHT_UNVERIFIED


def cluster_results(results, rel_tol=1e-3):
    """Greedily group solver records by matching answer. Returns clusters sorted strongest-first."""
    clusters = []
    for r in results:
        for c in clusters:
            if answers_match(c["rep"], r["answer"], rel_tol=rel_tol):
                c["members"].append(r)
                c["weight"] += _weight(r)
                break
        else:
            clusters.append({"rep": r["answer"], "members": [r], "weight": _weight(r)})
    clusters.sort(key=lambda c: (c["weight"], len(c["members"])), reverse=True)
    return clusters


def aggregate(results, rel_tol=1e-3):
    """Return the consensus answer, confidence, and minority report for a list of solver records."""
    if not results:
        raise ValueError("no solver results to aggregate")
    clusters = cluster_results(results, rel_tol=rel_tol)
    total = sum(c["weight"] for c in clusters) or 1.0
    top = clusters[0]
    minority = [
        {
            "answer": c["rep"],
            "support": [m["id"] for m in c["members"]],
            "assumptions": sorted({a for m in c["members"] for a in m.get("assumptions", [])}),
        }
        for c in clusters[1:]
    ]
    return {
        "answer": top["rep"],
        "confidence": round(top["weight"] / total, 4),
        "support": [m["id"] for m in top["members"]],
        "n_solvers": len(results),
        "n_clusters": len(clusters),
        "n_revised": sum(1 for r in results if r.get("revised")),
        "unanimous": len(clusters) == 1,
        "minority_report": minority,
    }


if __name__ == "__main__":
    demo = [
        {"id": "s1 (stat, sonnet)", "answer": "41.7%", "sufficient": True, "assumptions": ["refunds excluded"]},
        {"id": "s2 (sql, opus)", "answer": 41.70001, "sufficient": True, "assumptions": ["refunds excluded"]},
        {"id": "s3 (ml, sonnet)", "answer": 39.4, "sufficient": True, "assumptions": ["refunds included"]},
    ]
    out = aggregate(demo)
    print("consensus:", out["answer"], "confidence:", out["confidence"])
    print("minority:", out["minority_report"])
