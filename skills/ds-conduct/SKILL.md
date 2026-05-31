---
name: ds-conduct
description: "Use when starting fresh with data and unsure which skills to use — peeks at data, asks targeted questions, assembles a crew plan"
---

# ds-conduct : the crew's conductor

## When this applies

Starting fresh: user has data and a fuzzy request but no clear workflow yet. The conductor
figures out the right crew and sequence before any analysis runs.

**Typical triggers:**
- "Where do I start with this data?"
- "Orchestrate the analysis."
- "Look at my data and tell me what to do."
- "Set up the analysis for me."
- "I have a CSV — what should I do?"
- User uploads files but has not named a specific skill or method.

**Skip this skill** when the user already knows what they want (e.g. "run ds-spike on
payments.csv to compute churn"). Call the named skill directly.

## The cardinal rule

`ds-conduct` is a conductor, not an analyst. It never re-implements the skills it
orchestrates. If it needs to know something from the data, it calls `data-profile`. If it
needs intent clarified, it calls `ds-clarify`. If it needs analysis, it dispatches
`ds-star-plus` or `ds-spike`. All substance lives in the specialist skills.

---

## How to run it

### Stage 1 — Peek (fast, read-only)

Inspect every data file structurally **without running analysis**: row count, column names +
dtypes, null rates, unique counts for key columns, timestamp detection, candidate keys, file
relationships (shared columns across files). Reuse the fast analyzer from
`../data-profile/SKILL.md` (description-only mode, not a full profile). Goal: learn enough
to ask informed questions.

Produce a compact internal summary:
```
payments.csv: 2.8M rows | columns: payment_id (uuid, unique), merchant_id (int, 97% coverage),
created_at (datetime, range 2023-01–2024-12), amount_eur (float, 2% null), status (3 values)
merchants.json: 18K records | merchant_id (int, key), signup_date, country, tier, is_active (bool)
Shared key: merchant_id (both files)
Triggered patterns: timestamp, shared key, target-shaped column (is_active), internal report language
```

### Stage 2 — Grill (data-aware)

Using the trigger catalog (`references/trigger_catalog.md`), identify every pattern that fired
in Stage 1. Formulate one targeted question per detected pattern, **grounded in what was
actually seen** ("I see a `created_at` column — is this a time-series problem?" not "do you
have time data?"). Extend with the clarification checklist from
`../ds-clarify/references/clarify_checklist.md` for any additional ambiguities.

**Ask all triggered questions in a single batched message.** Do not trickle questions one
per round. Record every answer — unanswered items block plan assembly.

### Stage 3 — Assemble plan

Fill in the workflow plan template (`references/workflow_plan_template.md`) with the answers
from Stage 2. Determine:

- Which skills, in what order
- `ds-spike` N + personas, if ensemble selected
- Whether `ds-model` is needed (prediction task)
- The `analysis-spec.md` path that `ds-clarify` will write
- Explicit checkpoint points and backtrack conditions at each handoff

Present the filled plan to the user in plain language. Do not begin execution until the user
approves.

### Stage 4 — Confirm → Execute with checkpoints

Show the assembled plan. **Wait for explicit user approval.** On approval, execute skill by
skill, pausing at each checkpoint to surface the output before proceeding.

At each checkpoint:
1. Show the output from the completed skill (profile summary, spec contents, or analysis result).
2. Ask "Continue to [next step]?" or surface any anomaly that warrants re-asking.
3. If a checkpoint output reveals a problem — bad data quality, wrong join, ambiguous spec —
   **backtrack** to the appropriate stage (see backtrack table in the workflow template) rather
   than pressing forward with a flawed foundation.

---

## Output

A conducted analysis: profile → spec → analysis result (consensus + minority report if spike
was used), plus a **run manifest** listing:
- Each skill invoked (in order)
- The `analysis-spec.md` path
- Any assumptions recorded during clarification
- Checkpoint decisions and any backtrack events

---

## Quick reference

| Resource | Path |
|---|---|
| Trigger catalog | `references/trigger_catalog.md` |
| Workflow plan template | `references/workflow_plan_template.md` |
| Evidence / theory | `references/evidence.md` |
| Clarification checklist | `../ds-clarify/references/clarify_checklist.md` |
| Spec template | `../ds-clarify/references/spec_template.md` |

**Pairs with:** data-profile · ds-clarify · ds-star-plus · ds-spike · ds-model
