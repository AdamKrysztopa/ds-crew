---
name: ds-clarify
description: "Human-in-the-loop pre-flight for data-science questions: BEFORE running an analysis, interrogate the user to pin down every ambiguous choice (metric definitions, scope/filters, time window + timezone, null/duplicate/outlier handling, units, rounding, tie-breaking, exact output format), then write a concrete analysis-spec.md contract. Use this skill WHENEVER a data question is under-specified, high-stakes, or contested, or when the user asks to clarify/scope/spec out an analysis before computing, or says grill me on this analysis, or when two prior runs disagreed. The spec it produces becomes the rubric the ds-star / ds-star-plus verifier checks the answer against — so it prevents the most common silent failure: precisely answering a subtly different question than the user meant. Trigger before ds-star/ds-star-plus on important or fuzzy requests. Do NOT use for already-precise one-liners, prose writing, or generic coding."
---

# ds-clarify : resolve analytical intent before you compute

A verifier can confirm an answer matches *the question as the agent understood it*. It cannot
know your **true** intent. The classic data-science failure — the kind DS-STAR's own paper shows
(the NexPay case, Fig 3) — is a *precisely computed answer to the wrong question*: a different
metric definition, a different time window, a different null policy than you had in mind. No
amount of downstream verification fixes that. `ds-clarify` closes the gap up front.

This is the human-in-the-loop direction DS-STAR names as future work (paper §5: *"combine the
automated capabilities of DS-STAR with the intuition and domain knowledge of a human expert"*).
It is modelled on the relentless decision-tree interrogation of grilling skills, specialized to
the ambiguities that actually move data-science numbers.

## When this applies

Use it **before** `ds-star` / `ds-star-plus` when the request is high-stakes (a reported figure,
a board number, an irreversible decision), under-specified (vague metric, no format given), or
contested (a previous answer was disputed, or two runs disagreed). Skip it for already-precise,
low-stakes one-liners — clarification has a time cost; spend it where ambiguity is real.

## The cardinal rule

**A confidently wrong question is worse than an honest "which did you mean?"** Every ambiguous
choice you silently resolve is a coin flip on correctness. Surface them, get a decision, write it
down. The written spec is the deliverable — not just the conversation.

## How to run it

### Stage 1 — Skim the data, then the question

Run the analyzer (`../ds-star/scripts/analyze_file.py` or `../ds-star-plus/scripts/analyze_file.py`)
on the referenced files first, so your questions are grounded in the **real** schema, not guesses.
Knowing the columns/values lets you ask "is `card_scheme = NexPay` the intended filter?" instead of
"what is NexPay?". An informed question is answerable in one reply; an uninformed one wastes a round.

### Stage 2 — Walk the ambiguity checklist

Work through `references/clarify_checklist.md`. For each item that is genuinely ambiguous **for this
question**, ask the user — batching related questions. Do not ask about items the question already
pins down, and do not invent ambiguity that isn't there. Prefer concrete either/or choices grounded
in the data ("include refunds (negative amounts) or exclude them? I see 1,204 negative rows") over
open prompts. One pass is usually enough; a second only if answers open new forks.

### Stage 3 — Write the spec

Fill `references/spec_template.md` into a file the analysis run will read — default
`data/analysis-spec.md` (confirm the path). Every resolved choice becomes a line. Anything the user
explicitly left to your judgement is recorded as a stated assumption, not a silent one.

### Stage 4 — Hand off

State: "Spec written to `<path>`. Running `ds-star-plus` against it." The downstream verifier now
checks the answer against the spec's concrete criteria (units, scope, format) — i.e. the spec
*is* the per-task rubric for the six failure modes in `../ds-star-plus/references/rubric.md`. For a
long run, optionally re-surface any consequential new assumption at a router backtrack before
spending more rounds.

## What the checklist covers (summary)

Metric definition · population/scope · time window + timezone · filters & category values ·
null / missing / sentinel handling · duplicate & dedup keys · outlier policy · units & scale ·
rounding/precision · tie-breaking & ordering · exact output format (string template, JSON shape,
CSV column order, file name/path, chart title/labels) · acceptance check. Full tree with prompts:
`references/clarify_checklist.md`.

## Output

A written `analysis-spec.md` (template: `references/spec_template.md`) plus a one-line summary of
the consequential decisions, e.g. *"active = ≥1 login in trailing 28 days (Europe/Warsaw); refunds
excluded; revenue net of discount; answer as a 1-dp percentage."* That sentence is the contract the
rest of the pipeline — and the user — can hold you to.
