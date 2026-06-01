# Architecture: v1 vs v2, back to back

Both versions share one spine — the six-stage loop. They differ in *who* (which model) runs
each stage and in the reliability/cost machinery wrapped around the loop. The diagram
`architecture-comparison.svg` shows this as a mirror: the shared stage spine runs down the
centre, v1 details branch left, v2 details branch right. Read across any row to compare.

## The shared spine (both versions)

```
            ANALYZE FILES
                 |
         INITIAL SIMPLE STEP
                 |
        +------> IMPLEMENT (code) ------+
        |              |                |
        |          EXECUTE              |
        |              |                |
        |          VERIFY  --sufficient--> FINALIZE --> answer
        |              | insufficient
        |           ROUTE
        |        add / backtrack
        +--------------+
        (loop, max 20 rounds)
```

## Row-by-row, back to back

| Stage | v1 (`ds-star`) | v2 (`ds-star-plus`) |
|------|----------------|----------------------|
| Analyze | one model writes a describer per file | **Haiku**, parallel; emits a verbose description **and** a cached schema digest |
| Retrieve (lake) | top-K by embedding | top-150 by embedding **+ Haiku relevance pass** to top-K |
| Initial step | one model | **Haiku** planner -> **Sonnet** coder |
| Implement | one model, full descriptions re-fed each round | **Sonnet** coder; **digests** by default, full desc only for touched files |
| Execute | run script | run script |
| Verify | one model, **Yes/No** | **Opus**, returns graded `{score 1–4, rubric, checks, reason, missing}` (v2.1); sufficient iff `score 4` & no rubric `fail`; **3x vote** on borderline |
| Route | one model: add / Step l | **Sonnet** (Opus if escalated); add / Step l |
| Refine | truncate + regenerate | truncate + regenerate **with anti-repeat list**; oscillation -> Opus + 2-3 candidate branch |
| Finalize | one model | **Haiku** (Sonnet if format complex) |
| Debug | one model, trace + desc | **Haiku** trim -> **Sonnet** fix (Opus after 2 fails) |
| Early exit | implicit | explicit guardrail: easy task + clean verifier reason -> finalize in 1 round |

## The two design asymmetries that drive v2

1. **Verification is asymmetric.** A false "insufficient" costs one more cheap round; a false
   "sufficient" silently ends the run wrong. So the verifier is the *only* role pinned to the
   top tier (Opus) and the only one that votes. Everything else starts cheap and escalates on
   evidence.

2. **Cost lives in repetition, not depth.** v1's token bill is dominated by re-feeding full
   file descriptions to every role every round. v2 keeps the depth where it matters (Opus
   verifier) but kills the repetition (schema digests + caching, Haiku for high-call-volume
   roles). The escalation ladder means most rounds never touch Opus at all.

## Escalation ladder (v2)

```
default tier  --1 failed attempt-->  +1 tier  --still failing-->  Opus
                                                  ^
        oscillation (same step truncated 2x) -----+  (+ branch to 2-3 candidate steps)
```

Drop back to the default tier once a sub-goal succeeds — escalation is per sub-goal, not
sticky for the whole task.

## Why these asymmetries hold (paper evidence)

Both asymmetries above are grounded in the DS-STAR paper (Nam et al., 2025), not asserted: the cost
asymmetry in Table 6 (154,669 input tokens / $0.23 per task, 3.5× ReAct) and the correctness
asymmetry in the Table 4 ablations (removing descriptions: hard 45.24 → 26.98; removing the router:
45.24 → 39.95). The full mapping from each v2 change to its supporting table/number is in
`skills/ds-star-plus/references/evidence.md`.

> **v2 changes are design extensions grounded in the DS-STAR paper, not yet independently
> benchmarked.** See the README Reference section and `skills/ds-star-plus/references/evidence.md`
> for the full evidence chain.

## v1.2 additions (tracks E–M)

The following capabilities extend v2 without changing the shared spine:

| Capability | What was added | Opt-in / Default |
|---|---|---|
| Sandbox + provenance (J) | `run_manifest.py` emits SHA-256 + inputs + verdict per run; `sandbox.md` enforces temp-dir discipline | Default (runs at FINALIZE) |
| Stateful kernel (F) | `kernel_runner.py` — persistent IPython kernel bound to `sys.executable`; mandatory clean re-run before FINALIZE | Opt-in (script mode default) |
| DAG planning (G) | Plan as task graph `{id, goal, deps, status}`; node-level verify; descendant-only replan on failure | Escalated (linear chain default) |
| Cross-session memory (E) | `memory_store.py` — append-only JSONL; seeded at PLAN, recorded at FINALIZE on clean verdict | Opt-in (no-op if store absent) |
| Debate in ds-spike (I) | ≤2 cross-critique rounds before aggregation; `n_revised` field; anti-herding guard | Opt-in (`debate: true`) |
| Standalone primitives (L) | ds-verify, ds-reconcile, ds-vote, ds-search expose the embedded building blocks | Standalone skills |
| ds-model (H) | AIDE solution-tree with leaderboard + leakage/CV discipline | New skill |
| ds-conduct (K) | Data-aware orchestrator: Peek→Grill→Assemble plan→Confirm+Execute | New skill (capstone) |
