#!/usr/bin/env python3
"""Pick the model tier for a DS-STAR+ role, per references/model_routing.md.

Centralizes routing so it is consistent instead of ad hoc. Returns a concrete model id.

    from route_model import pick_model
    pick_model("verifier")                              -> 'claude-opus-4-8'
    pick_model("planner_next", attempt=2)               -> 'claude-opus-4-8'  (escalated)
    pick_model("coder")                                 -> 'claude-sonnet-4-6'
    pick_model("analyzer")                              -> 'claude-haiku-4-5'
    pick_model("router", oscillating=True)              -> 'claude-opus-4-8'

Tier names are the contract; the ids below are the current mapping — bump to the latest
snapshot of each tier when newer models ship.
"""

TIERS = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-8",
}
ORDER = ["haiku", "sonnet", "opus"]

# default tier and an optional hard ceiling per role
DEFAULT = {
    "analyzer": "haiku",
    "planner_init": "haiku",
    "planner_next": "sonnet",
    "coder": "sonnet",
    "verifier": "opus",      # load-bearing judge: never cheap out
    "router": "sonnet",
    "finalizer": "haiku",
    "debug_trim": "haiku",
    "debug_fix": "sonnet",
}


def _bump(tier, steps=1):
    i = min(ORDER.index(tier) + steps, len(ORDER) - 1)
    return ORDER[i]


def pick_model(role, attempt=1, oscillating=False, hard=False):
    """role: key in DEFAULT. attempt: 1-based try count at the same sub-goal.
    oscillating: same step truncated twice. hard: caller already knows it's hard."""
    if role not in DEFAULT:
        raise ValueError(f"unknown role: {role}")
    tier = DEFAULT[role]

    # the verifier stays Opus regardless
    if role == "verifier":
        return TIERS["opus"]

    # escalate one tier per failed attempt beyond the first
    if attempt > 1:
        tier = _bump(tier, attempt - 1)

    # oscillation forces planner/router/coder to the top tier
    if oscillating and role in ("planner_next", "router", "coder", "debug_fix"):
        tier = "opus"

    # caller-known-hard nudges one tier up
    if hard:
        tier = _bump(tier, 1)

    return TIERS[tier]


if __name__ == "__main__":
    checks = [
        ("verifier", dict(), "claude-opus-4-8"),
        ("analyzer", dict(), "claude-haiku-4-5"),
        ("planner_next", dict(), "claude-sonnet-4-6"),
        ("planner_next", dict(attempt=2), "claude-opus-4-8"),
        ("coder", dict(), "claude-sonnet-4-6"),
        ("coder", dict(attempt=2), "claude-opus-4-8"),
        ("router", dict(oscillating=True), "claude-opus-4-8"),
        ("finalizer", dict(), "claude-haiku-4-5"),
        ("finalizer", dict(hard=True), "claude-sonnet-4-6"),
        ("debug_trim", dict(), "claude-haiku-4-5"),
    ]
    ok = True
    for role, kw, expected in checks:
        got = pick_model(role, **kw)
        flag = "ok" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{flag}] pick_model('{role}', {kw}) -> {got}")
    print("ALL PASS" if ok else "SOME FAILED")
