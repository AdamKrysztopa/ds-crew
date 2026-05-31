# DS-STAR skill suite for Claude Code

> **Two installable Claude Code skills** that implement the DS-STAR data-science agent
> (Nam et al., 2025) — answering analytical questions over data files by writing and
> executing Python through an iterative loop that **never trusts code just because it ran**.

---

## Why DS-STAR?

Most AI data-science workflows stop when the code executes. DS-STAR doesn't.
It grows a plan one verified step at a time and uses an LLM-as-judge to confirm
that the **actual execution output** answers the actual question — catching silent failures
like wrong filters, missing joins, and format mismatches before they reach you.

---

## Installation

### 1. Add the marketplace (one-time per machine)

```bash
claude plugin marketplace add AdamKrysztopa/ds-stats-with-claude
```

### 2. Install the plugin — choose your scope

```bash
# All your projects
claude plugin install ds-star@ds-star --scope user

# This project only (saved to .claude/settings.json)
claude plugin install ds-star@ds-star --scope project

# Local override, not committed
claude plugin install ds-star@ds-star --scope local
```

### 3. Use

Invoke explicitly in any Claude Code session:

```
/ds-star
/ds-star-plus
```

Or just ask an analytical question over a data file — Claude will trigger the skill automatically.

### Updating / uninstalling

```bash
claude plugin update ds-star@ds-star
claude plugin uninstall ds-star@ds-star
```

---

## Which skill to use

| | `ds-star` | `ds-star-plus` |
|---|---|---|
| **Model** | Single model throughout | Haiku / Sonnet / Opus per role |
| **Verifier output** | Yes / No | `{sufficient, reason, missing}` |
| **Backtracking** | Truncate + regenerate | + anti-repeat list, oscillation handling |
| **Token cost** | Full descriptions every round | Schema digests by default |
| **Best for** | Baseline / reproducing the paper | Production, multi-file, cost-sensitive work |

---

## How the loop works

```
ANALYZE every file (real schema, not guesses)
        │
INITIAL simple step (load + peek)
        │
        ▼
   ┌─── IMPLEMENT (Python script)
   │         │
   │      EXECUTE
   │         │
   │      VERIFY ──── sufficient? ──► FINALIZE ──► answer
   │         │ no
   │      ROUTE: add next step  OR  backtrack to wrong step
   └─────────┘
   (max 20 rounds)
```

The verifier is the load-bearing piece: a false "sufficient" ends the run with a wrong
answer that nothing downstream catches, so `ds-star-plus` pins it to Opus and optionally
runs it 3× with majority vote on borderline calls.

---

## Repository layout

```
ds-stats-with-claude/
├── skills/
│   ├── ds-star/                    v1 — faithful paper implementation
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── prompts.md          role prompts for each loop step
│   │   │   └── worked_example.md   annotated 5-round trace
│   │   └── scripts/
│   │       └── analyze_file.py     Stage 1 file describer
│   └── ds-star-plus/               v2 — reliability- and cost-hardened
│       ├── SKILL.md
│       ├── evals/
│       │   └── evals.json          checkable test cases
│       ├── references/
│       │   ├── model_routing.md    Opus/Sonnet/Haiku routing policy
│       │   ├── evidence.md         paper-grounded "why" for every v2 change
│       │   ├── prompts.md          upgraded prompts (structured verifier)
│       │   └── worked_example.md   annotated trace with backtracking
│       └── scripts/
│           ├── analyze_file.py     describer + schema digest emitter
│           └── route_model.py      pick_model() routing helper
├── .claude-plugin/
│   ├── plugin.json                 plugin manifest
│   └── marketplace.json            marketplace manifest
├── ARCHITECTURE.md                 v1 vs v2 side-by-side
├── ROADMAP.md                      planned plus-improvements + new skills
├── papers/
│   └── README.md                   bibliography (PDFs gitignored, re-fetchable)
├── architecture-comparison.svg     mirrored diagram
└── make_diagram.py                 regenerate the SVG
```

---

## Reference

Nam, Yoon, Chen & Pfister (2025). *DS-STAR: Data Science Agent via Iterative Planning and
Verification.* arXiv:2509.21825. Google Cloud / KAIST.

The v2 additions (model routing, structured verifier, oscillation handling, digest caching,
two-stage retrieval) are design extensions: there is no new independent benchmark, but each is
justified against a specific finding in the paper — the 3.5× input-token cost (Table 6), the
analyzer/router ablations (Table 4, e.g. hard accuracy 45.24 → 26.98 without descriptions), the
~8-point retrieval-vs-oracle gap (Table 2), and the round distribution (§4.3). The full evidence
chain is in `skills/ds-star-plus/references/evidence.md`; `skills/ds-star-plus/evals/evals.json`
provides checkable test cases.

## What's next

This repo is growing from "a DS-STAR implementation" into a suite of recent data-science skills.
The planned work — a rubric-guided verifier upgrade (DeepVerifier), an optional MCTS search mode,
and a human-in-the-loop `ds-clarify` skill — is laid out in [`ROADMAP.md`](ROADMAP.md), each item
tied to a paper in the bibliography at [`papers/README.md`](papers/README.md).
