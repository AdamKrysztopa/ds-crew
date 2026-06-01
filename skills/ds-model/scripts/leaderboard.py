#!/usr/bin/env python3
"""Solution-tree leaderboard for ds-model (Track H; AIDE 2502.13138).

Tracks candidate model drafts as a tree; always expands the best-scoring node.
    from leaderboard import Leaderboard
    lb = Leaderboard(metric="rmse", mode="min")
    lb.add("draft-1", 0.82, parent=None)
    lb.add("draft-2", 0.74, parent="draft-1")
    print(lb.node_to_expand())   # -> "draft-2"
"""
import math


class Leaderboard:
    def __init__(self, metric, mode):
        if mode not in ("min", "max"):
            raise ValueError(f"mode must be 'min' or 'max', got {mode!r}")
        self.metric = metric
        self.mode = mode
        self._rows = []  # list of {node, score, parent}

    def add(self, node, score, parent):
        if score is None or (isinstance(score, float) and math.isnan(score)):
            raise ValueError(f"score for node {node!r} is NaN or None")
        self._rows.append({"node": node, "score": float(score), "parent": parent})

    def best(self):
        if not self._rows:
            return None
        return min(self._rows, key=lambda r: r["score"]) if self.mode == "min" \
               else max(self._rows, key=lambda r: r["score"])

    def node_to_expand(self):
        """AIDE strategy: always improve the strongest draft."""
        b = self.best()
        return b["node"] if b else None

    def tree(self):
        """Return parent -> [children] adjacency dict."""
        adj = {}
        for r in self._rows:
            adj.setdefault(r["parent"], []).append(r["node"])
            adj.setdefault(r["node"], [])
        return adj


if __name__ == "__main__":
    lb = Leaderboard("rmse", "min")
    lb.add("draft-1", 0.82, None)
    lb.add("draft-2", 0.74, "draft-1")
    lb.add("draft-3", 0.68, "draft-1")
    print("best:", lb.best())
    print("expand:", lb.node_to_expand())
    print("tree:", lb.tree())
