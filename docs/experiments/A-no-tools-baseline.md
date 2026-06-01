# Experiment A — No-Tools Baseline

**Date:** 2026-06-01
**Model:** claude-sonnet-4-6
**Questions:** 15 (same 15 as smoke run)

## Purpose

Establish the floor: how much does code execution actually help?

This experiment calls the Anthropic API directly with **no tools** — no Bash,
no Python execution, no file system access. Claude receives the first 50 rows of
the CSV as plain text and must answer purely by reasoning over those numbers.

Compare to the `baseline` variant (same model, minimal prompt, but full tool access)
to isolate the contribution of code execution vs. raw reasoning.

## Results

This experiment measures only the **no-tools floor**. For the tool-using numbers (which
earlier drafts under-reported due to harness artifacts), see
[Experiment B](B-plugin-vs-prompt.md) — ds-star scores **94.4%** with code execution.

| variant | n | accuracy | accuracy-hard | $/task | tokens/task |
|---|---|---|---|---|---|
| no-tools (Exp A) | 15 | 33.3% | 0.0% | $0.2031 | 46411 |
| ds-star (Exp B, full set) | 18 | **94.4%** | 100% | $0.34 | ~126k |


## Charts

![Accuracy comparison](img/accuracy_comparison.png)

![Hard accuracy comparison](img/hard_accuracy_comparison.png)

![Accuracy vs cost](img/accuracy_vs_cost.png)

## Key findings

- **No-tools accuracy:** 33.3% vs **tool-using ds-star:** 94.4% (Exp B)
- Gap of **~61pp** shows how much code execution adds — the dominant lever in the stack
- No-tools cost is **$0.2031/task** — text-only reasoning burns tokens re-deriving by hand
- Wrong IDs (no-tools): ['0', '5', '6', '7', '8', '9', '14', '18', '23', '26']

## Methodology

- **Model:** `claude-sonnet-4-6` via Anthropic SDK, no tools
- **Data:** First 50 rows of each CSV embedded as plain text in the prompt
- **Prompt:** "Answer using only the data shown. Do not write or execute code."
- **Scoring:** Same DABench deterministic scorer as all other experiments
- **Script:** `benchmarks/experiments/exp_a_no_tools.py`

## Interpretation

The no-tools number represents what a user gets when they paste data into a chat
window and ask a question — no agent, no execution, just LLM reasoning over text.

The gap between this and the tool-using baseline is the value of the execution
environment itself, independent of any DS-STAR methodology.
