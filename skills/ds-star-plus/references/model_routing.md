> **Single source of truth:** Concrete model IDs and prices are defined in
> `config/models.json` (review item #6). The tier table below mirrors it;
> if they diverge, config wins — update config, not this table.

## Reusable helper

Any skill or caller can import `pick_model` from `scripts/route_model.py` to apply consistent
cost-tiered routing without duplicating the logic:

```python
from route_model import pick_model

pick_model(role, attempt=1, oscillating=False, hard=False)
```

**Arguments:**

| Argument | Type | Default | Semantics |
|----------|------|---------|-----------|
| `role` | `str` | required | One of the keys in the DEFAULT table below (`"analyzer"`, `"planner_init"`, `"planner_next"`, `"coder"`, `"verifier"`, `"router"`, `"finalizer"`, `"debug_trim"`, `"debug_fix"`) |
| `attempt` | `int` | `1` | 1-based try count at the same sub-goal. Each failed attempt beyond the first bumps one tier (Haiku→Sonnet, Sonnet→Opus). |
| `oscillating` | `bool` | `False` | True when the same step has been truncated twice. Forces `planner_next`, `router`, `coder`, and `debug_fix` to Opus. |
| `hard` | `bool` | `False` | True when the caller already knows the task is hard. Nudges one tier up regardless of attempt count. |

**Tier table (current model ids):**

| Tier | Model id | Default roles |
|------|----------|---------------|
| Haiku | `claude-haiku-4-5` | `analyzer`, `planner_init`, `finalizer`, `debug_trim` |
| Sonnet | `claude-sonnet-4-6` | `planner_next`, `coder`, `router`, `debug_fix` |
| Opus | `claude-opus-4-8` | `verifier` (always) |

**Escalation ladder:**

1. Role starts on its default tier.
2. `attempt > 1` → bump one tier per failed attempt beyond the first.
3. `oscillating=True` → force `planner_next`, `router`, `coder`, `debug_fix` to Opus.
4. `hard=True` → nudge one tier up (applied after attempt escalation).
5. `verifier` is always Opus regardless of any argument.

**Examples:**

```python
pick_model("verifier")                       # -> 'claude-opus-4-8'  (always)
pick_model("coder")                          # -> 'claude-sonnet-4-6'
pick_model("coder", attempt=2)               # -> 'claude-opus-4-8'  (escalated)
pick_model("analyzer")                       # -> 'claude-haiku-4-5'
pick_model("planner_next", attempt=2)        # -> 'claude-opus-4-8'  (escalated)
pick_model("router", oscillating=True)       # -> 'claude-opus-4-8'  (oscillation)
pick_model("finalizer", hard=True)           # -> 'claude-sonnet-4-6' (nudged)
```

---

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

The base method's cost is dominated by re-feeding full descriptions to every role each round
(Table 6: 154,669 input tokens, 12.7 LLM calls, $0.23/task on DABStep — 3.5x ReAct's 44,691
input tokens, a bill the paper attributes to "comprehensive analytic descriptions of each data
file"). v2 attacks this from two sides: (a) routing the high-call-volume roles to Haiku, and (b)
passing compact schema digests instead of full descriptions except where a role touches a
specific file. Together these target that input-token bloat while keeping Opus exactly where
correctness depends on it. Critically, the descriptions are also the #1 correctness lever
(Table 4 ablation: removing them drops hard accuracy 45.24 → 26.98), so v2 compresses them into
digests rather than dropping them — the full description still reaches any role that touches the
file. Full evidence chain: `evidence.md`.

## When to ignore routing and just use one strong model

If the whole task is small (a single file, one obvious computation), the orchestration
overhead is not worth it — run it directly on Sonnet end to end and verify once on Opus. The
routing machinery earns its keep on multi-file, multi-round tasks.
