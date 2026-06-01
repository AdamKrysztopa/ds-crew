# Experiment B — Plugin vs Raw Prompt

**Date:** 2026-06-01
**Model:** claude-sonnet-4-6
**Questions:** 18 (DABench dev subset; 4 hard)

## Purpose

Test whether the ds-crew plugin mechanism adds value beyond injecting the SKILL.md as a
user-message preamble. Both approaches use `claude -p --dangerously-skip-permissions`
(full tool access, real code execution). `num_turns` measures how many internal loop
iterations Claude ran per question.

## Results

| variant | n | strict | field-score | accuracy-hard | avg turns | $/task |
|---|---|---|---|---|---|---|
| ds-star-plugin (`/ds-star`) | 18 | **94.4%** | 97.9% | 100% (4/4) | 4.3 | $0.342 |
| ds-star-prompt (SKILL.md as text) | 18 | **94.4%** | 97.9% | 100% (4/4) | — | $0.310 |

Both miss only **Q8** (see below). All other 17 questions — including all 4 hard ones —
are correct.

## Charts

![Accuracy comparison](img/accuracy_comparison.png)

![Accuracy vs cost](img/accuracy_vs_cost.png)

## Key findings

**Accuracy is identical (94.4%).** Plugin and raw-prompt score the same and miss the same
single question. The plugin runs a slightly deeper loop (and costs a little more) but, on
well-defined closed-form questions, that doesn't change the answer.

**The one miss is a benchmark-label bug, not a skill error.** Q8 asks for the *population*
standard deviation (its constraint says so explicitly); the reference label uses the
*sample* std. Both variants correctly compute population std and are marked wrong. Every
mean and median matches exactly — only the ddof-dependent std-devs differ (5 of 8 fields
correct, hence field-score 97.9% vs strict 94.4%).

**These numbers supersede earlier drafts.** A previous version of this doc reported 73.3%;
that figure was an artifact of a 400-character answer-truncation bug and all-or-nothing
scoring of correct-but-template-echoing answers. See
[Scoring & harness fixes](README.md#scoring--harness-fixes).

## Methodology

- **Plugin variant:** prompt = `/ds-star\n\nDataset: ...\nQuestion: ...`
  → invokes the skill via the plugin mechanism (SKILL.md loaded as system context)
- **Prompt variant:** prompt = `{SKILL.md content}\n\nQuestion: ...`
  → SKILL.md injected as a user-message preamble
- Both run `claude -p --dangerously-skip-permissions` in a temp dir with the data files
- `num_turns` from `--output-format json` counts internal tool-use rounds
- Full answers are retained and scored with both strict and per-field metrics
- **Script:** `benchmarks/experiments/exp_b_plugin_vs_prompt.py`
  (`--qids 7 8 --out file.jsonl` runs a targeted subset without touching the full results)
