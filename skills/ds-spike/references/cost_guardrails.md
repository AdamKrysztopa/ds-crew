# Ensemble cost guardrails

Running N parallel agents or a search tree multiplies API cost by N (or more).
Before dispatching, estimate and confirm.

## The pattern

1. **Estimate** — before launching, compute projected cost:
   ```python
   from skills.ds_star_plus.scripts.run_manifest import estimate_cost
   projected = estimate_cost(model, {"input_tokens": avg_in, "output_tokens": avg_out}) * N
   ```
   Or use a conservative rough estimate: single-run cost × N.

2. **Default ceiling** — `$1.00` or ~200k total tokens. If the estimate exceeds the
   ceiling, **require explicit user confirmation** before proceeding:
   > "This will run N agents (~$X estimated). Proceed? [y/N]"

3. **User override** — the ceiling is overridable at invocation time. If the user
   sets a higher ceiling or says "go ahead", proceed without re-asking mid-run.

4. **Report actual cost** — at the end of each run, surface the actual `cost_usd`
   from each solver's run manifest (written by `write_manifest`). This closes the
   loop: estimate → confirm → actual.

## Sandbox reminder

Solver code runs with no-network-by-default (Track J sandbox policy).
See `../ds-star-plus/references/sandbox.md` for the full resource/isolation policy.

## When to skip the guardrail

- The user has already confirmed cost at the session level ("run production-audit profile")
- The estimated cost is below the ceiling
- An automated/CI context where a human is not present (document this assumption)
