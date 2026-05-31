# Roadmap — toward a suite of recent data-science skills

This repo started as a faithful implementation of DS-STAR (`ds-star`) plus a reliability- and
cost-hardened successor (`ds-star-plus`). This document plans the next two tracks:

- **Track A** — concrete improvements to `ds-star-plus`, each pulled from a specific newer paper.
- **Track B** — new data-science skills, led by the human-in-the-loop "grill" skill.

Every item is tied to a source in [`papers/`](papers/README.md). Status legend:
🟢 ready to build · 🟡 needs a design decision · ⚪ exploratory.

---

## Track A — improving `ds-star-plus`

### A1 🟢 v2.1 — rubric-guided, decomposed verifier (from DeepVerifier)

**Source:** DeepVerifier, [2601.15808](https://arxiv.org/abs/2601.15808).

**Why.** The verifier is the one unrecoverable decision in the loop (a false "sufficient" ends the
run wrong, silently). v2 already hardened it (rationale + `missing` + 3× vote + Opus). DeepVerifier
is the next rung on the *same* ladder and is cost-aligned: it beats a vanilla LLM-judge by **12–48%
F1**, lifting *recall of catching wrong answers from 14% → 71%* (their GAIA-Web ablation), with no
training. This directly attacks DS-STAR's core failure mode.

**What changes.** Replace the current `{sufficient: bool, reason, missing}` verifier with a
rubric-scored, decomposed one:

1. **Fixed DS-failure rubric.** Turn our "common pitfalls" list into an explicit checklist the
   verifier scores against every time: wrong column/value · silently dropped rows · units mismatch ·
   scope error (wrong filter/time window/entity) · format mismatch · question-substitution (answered
   a different question). This is DeepVerifier's "failure taxonomy → rubric" applied to data science.
2. **Decomposition over holistic judgement.** Instead of one all-or-nothing verdict, emit ≤3
   targeted follow-up checks (e.g. "does the printed scope match the asked scope?", "are the units
   the asked units?") and answer each — cheaper than re-judging the whole task.
3. **Graded 1–4 verdict** (1 = clearly wrong … 4 = clearly sufficient) instead of a bool, with
   early-stop when the verdict is confidently 4 and no rubric item fails. Maps cleanly onto the
   existing early-exit guardrail.

**Files:** `skills/ds-star-plus/references/prompts.md` (verifier prompt), `SKILL.md` (verify stage),
new `references/evidence.md` entry citing 2601.15808, `evals/evals.json` (cases that exercise each
rubric item). **Effort:** small–medium, no new scripts. **Risk:** low; it's a strict superset of the
current verifier.

### A2 🟡 v2.2 — optional MCTS "search mode" for hard tasks (from I-MCTS / SWE-Search)

**Sources:** I-MCTS [2502.14693](https://arxiv.org/abs/2502.14693), SWE-Search
[2410.20285](https://arxiv.org/abs/2410.20285), Empirical-MCTS
[2602.04248](https://arxiv.org/abs/2602.04248), Agent Alpha
[2602.02995](https://arxiv.org/abs/2602.02995).

**Why.** DS-STAR refines greedily — one sampled next step per round. v2 already branches to 2–3
candidates on oscillation; MCTS is the principled generalization. Two transferable ideas:
- **Introspective node expansion** (I-MCTS): generate the next candidate by reflecting on the
  solutions+results of *sibling* attempts, not just the parent — "here's what the neighbours tried
  and scored, do better."
- **Hybrid reward** (I-MCTS): an LLM value-model *estimates* a branch's promise before paying for a
  full execution rollout, then blends toward the real execution score — so search prioritizes without
  running every candidate. SWE-Search shows this whole pattern transfers to code-writing agents.

**The tension (why 🟡).** MCTS multiplies LLM calls — it fights the cost-hardening thesis that
*defines* `ds-star-plus`. **Decision needed:** ship this as an explicit opt-in `search_mode` reserved
for the hard tail (the ~5.6-round, multi-file tasks where DS-STAR's Fig 4 shows more compute pays),
**not** as a default. Empirical-MCTS's dual success/failure memory would feed our anti-repeat list.

**Files:** new `references/search_mode.md`, `scripts/` helper for the value-model scoring, `SKILL.md`
escalation section. **Effort:** large. **Gate:** only after A1 lands and we can measure whether the
verifier is reliable enough to be the MCTS reward signal.

### A3 ⚪ Retrieval upgrade for data lakes

**Source:** KramaBench [2506.06541](https://arxiv.org/abs/2506.06541) (the ~8-pt oracle gap).
v2 already added a Haiku relevance pass; a learned re-ranker or column-level matching could close
more of the gap. Low priority until A1/A2.

---

## Track B — new data-science skills

### B1 🟢 `ds-clarify` — human-in-the-loop pre-flight (the flagship new skill)

**Inspiration:** the superpowers `grill-with-docs` / `grill-me` pattern (relentless decision-tree
interrogation that updates docs inline). **Grounding:** DS-STAR's own paper names this as *the* future
direction — §5: *"extend this framework to a human-in-the-loop setting... combine the automated
capabilities of DS-STAR with the intuition and domain knowledge of a human expert."*

**The gap it fills.** DS-STAR's verifier can confirm the output answers *the question as the agent
understood it* — it cannot know the user's *true* intent. The classic silent failure (the paper's
own NexPay case, Fig 3) is partly intent ambiguity: what counts as "active"? which timezone? how are
nulls/dupes handled? what are the units? Tie-breaks? Output format? No amount of verification fixes a
precisely-answered *wrong question*.

**Shape.** A skill that, before (and optionally during) a `ds-star`/`ds-star-plus` run:
1. **Grills the user** through the ambiguity decision tree — metric definitions, scope/filters, time
   windows + timezone, null/dedup/outlier handling, units, rounding, tie-breaking, exact output
   format — resolving each branch like `grill-with-docs` does for plans.
2. **Emits a written `analysis-spec.md`** (the agreed contract) that the DS-STAR verifier then checks
   the output against — turning fuzzy intent into a checkable rubric (dovetails with A1).
3. **Optional mid-run checkpoints** at router backtracks: surface the consequential assumption and
   confirm before spending more rounds.

**Files:** new `skills/ds-clarify/SKILL.md` + `references/clarify_checklist.md` (the decision tree) +
`references/spec_template.md`. **Effort:** medium. **Note:** complements rather than replaces the
autonomous skills — invoke it when stakes are high or the query is under-specified.

### B2 ⚪ `data-profile` — standalone deep data-quality report

Promote DS-STAR's Stage-1 analyzer into a first-class skill: a thorough profiling / data-quality
report (types, missingness, cardinality, candidate keys, anomalies, encoding issues) for any file or
folder, usable on its own. Reuses `analyze_file.py`. Low effort, high standalone utility.

### B3 ⚪ `eda-narrative` — guided EDA to a written narrative

A skill that runs an exploratory pass and produces a narrative report (findings + charts), distinct
from DS-STAR's question-answering loop. Exploratory.

---

## Track C — repo evolution

Once Track A1 + B1 land, the repo is no longer "just DS-STAR" — it's a **suite of recent
data-science skills** (autonomous solving, human-in-the-loop clarification, profiling). Plan:

- Rename the repo / marketplace to reflect the suite (e.g. *data-science-skills* or *ds-skills*),
  update `.claude-plugin/marketplace.json`, `plugin.json`, and install docs.
- Keep `papers/README.md` as the living bibliography so the repo visibly tracks the current literature.
- Each skill stays independently installable; `ds-clarify` is the connective tissue between them.

---

## Suggested order

1. **A1** (rubric verifier) — biggest reliability win, smallest blast radius, cost-aligned.
2. **B1** (`ds-clarify`) — the human-in-the-loop skill you asked for; pairs naturally with A1's rubric.
3. **C** (repo rename) — once two new things exist to justify the broader name.
4. **A2** (search mode) — only after A1 makes the verifier a trustworthy reward signal.
5. **B2 / B3 / A3** — opportunistic.

Open decisions before building: (1) A2 default-off vs cut entirely; (2) final skill names; (3) whether
`ds-clarify` writes its spec into the same data dir the DS-STAR skills read from.
