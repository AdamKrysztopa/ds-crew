# Solver diversity axes

An ensemble only beats a single run if its members are *genuinely different*. Identical agents
with the same seed give correlated errors — you pay N× for no extra signal. Vary along these axes
when dispatching the N solvers. Default N = 3 picks three rows that differ on strategy AND seed;
N = 5 adds model-tier and a second seed.

## Axis 1 — Strategy / persona

| persona | bias it brings | catches |
|---------|----------------|---------|
| **Cautious statistician** | checks distributions, nulls, sample sizes before computing | silent row drops, outliers, degenerate groups |
| **ML-first** | frames as features/targets, leans on libraries | misread task type, leakage, wrong metric |
| **SQL / join-first** | thinks in keys, joins, group-bys | bad joins, duplicate fan-out, wrong grain |
| **Assumption-minimal literalist** | does exactly what the spec says, nothing more | over-engineering, question_substitution |
| **Domain-skeptic** | re-reads side files (tips.md, fees.json) for hidden rules | missed domain rules encoded in docs |

## Axis 2 — Model tier

Mix Opus and Sonnet tier solvers (see `../ds-star-plus/references/model_routing.md` and `config/models.json` for current IDs).
Different tiers fail differently; a tier disagreement is itself informative. Keep at least one Opus
solver so the panel has a strong member.

## Axis 3 — Random seed / sampling

Even same-persona, same-tier solvers should use different sampling seeds so their plans are not
identical. This is the cheapest diversity and the floor for any spike.

## Picking the panel

- **N = 3 (default):** cautious-statistician (Sonnet) · SQL-join-first (Sonnet) · assumption-minimal
  (Opus). Three strategies, mixed tiers, distinct seeds.
- **N = 5 (high stakes):** add ML-first (Sonnet) and domain-skeptic (Opus).

Record each solver's `{persona, model, seed}` alongside its answer so the minority report can say
*which kind* of approach diverged, not just that one did.

## Seeding personas with distilled rules

If a rules store exists (`../ds-memory/SKILL.md` Mode 4 — ExpeL distillation; `rules.jsonl`),
retrieve the rules whose task-signature family overlaps this task and **seed every persona's
assumption list with them** before dispatch. This extends the existing minority-report seeding:
prior runs' hard-won heuristics ("confirm refund handling before summing revenue") become explicit
assumptions each solver must take a position on — so when solvers diverge, they diverge *knowingly*
on a flagged fork rather than re-discovering the same trap independently. Rules are advisory and
shared identically across all N solvers (they are part of the locked spec, not a per-solver variable).
