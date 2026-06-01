"""Run-log schema + validator for the ds-spike / ds-conduct loops (review item #3).

IMPORTANT — what this does and does NOT do: a Python validator cannot force the
model to actually run the verifier/routing/oscillation loop. It only checks that a
structured log claiming the loop ran is well-formed, so deviations are *detectable
after the fact*, not *impossible*. This is the honest boundary; see the SKILL.md
"What this cannot guarantee" notes.
"""
REQUIRED_FIELDS = ("rounds", "verifier_verdicts", "oscillated", "subrun_cost_usd")

def validate_runlog(log):
    errs = []
    for f in REQUIRED_FIELDS:
        if f not in log:
            errs.append(f"missing required field: {f}")
    if errs:
        return errs
    rounds = log["rounds"]
    seen = {v.get("round") for v in log["verifier_verdicts"]}
    for r in range(1, rounds + 1):
        if r not in seen:
            errs.append(f"no verifier verdict recorded for round {r}")
    return errs

if __name__ == "__main__":
    import json, sys
    errs = validate_runlog(json.load(open(sys.argv[1])))
    print("\n".join(errs) if errs else "OK")
    sys.exit(1 if errs else 0)
