# Model-tier routing policy (v2)

The principle: **spend reasoning budget on judgment, not on plumbing.** Route each role to the
cheapest tier that reliably does its job, and escalate only on evidence the task is hard.

## Tiers → current models

| Tier | Model id | Use for |
|------|----------|---------|
| Opus | `claude-opus-4-8` | Deepest reasoning: verification, hard re-planning, stuck-state strategy changes |
| Sonnet | `claude-sonnet-4-6` | Strong default for codegen and step-level reasoning |
| Haiku | `claude-haiku-4-5` | High-volume, low-reasoning: file describers, trace trimming, simple formatting |

Always use the latest available snapshot of a tier. If a newer Opus/Sonnet/Haiku ships, prefer
it. Tier *names* are what matter here; the ids above are the current concrete mapping.

## Why these defaults

- **Analyzer → Haiku.** One short describe-the-file script per file, many files, fully
  parallel, almost no cross-file reasoning. This is the single biggest call-count role, so
  cheap-per-call matters most here.
- **Verifier → Opus (always).** This is the asymmetry that defines the method: a false
  "insufficient" just costs another round, but a false "sufficient" ends the run with a wrong
  answer that nothing downstream will catch. Pay for the best judge. Add 3x majority voting on
  borderline/high-stakes verdicts.
- **Planner/Router → Sonnet, escalate to Opus.** Step-level reasoning over real output is
  Sonnet-solid most of the time; reserve Opus for when the task has shown it is hard (no
  progress across rounds, oscillation).
- **Coder → Sonnet, escalate to Opus.** Incremental codegen on top of a working base is
  Sonnet's wheelhouse; escalate only when the same code area keeps failing.
- **Finalizer/Debugger-trim → Haiku.** Reformatting a correct result and trimming a traceback
  are near-mechanical.

## Escalation ladder

Escalate one tier at a time and only on evidence:

1. Role on default tier.
2. After 1 failed attempt at the same sub-goal → next tier up (Haiku→Sonnet, Sonnet→Opus).
3. On oscillation (same step truncated twice) → planner + router to Opus, and switch from a
   single greedy sample to 2-3 candidate steps with verifier pick.
4. Never silently stay escalated longer than needed: once a step succeeds, drop back to the
   default tier for the next, fresh sub-goal.

## Budget intuition

The base method's cost is dominated by re-feeding full descriptions to every role each round.
v2 attacks this from two sides: (a) routing the high-call-volume roles to Haiku, and (b)
passing compact schema digests instead of full descriptions except where a role touches a
specific file. Together these target the input-token bloat that made v1 ~3.5x ReAct's input
tokens, while keeping Opus exactly where correctness depends on it.

## When to ignore routing and just use one strong model

If the whole task is small (a single file, one obvious computation), the orchestration
overhead is not worth it — run it directly on Sonnet end to end and verify once on Opus. The
routing machinery earns its keep on multi-file, multi-round tasks.
