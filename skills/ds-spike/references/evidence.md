# Why a reconciled panel beats one run — evidence

`ds-spike` is not a vibe; it is two well-supported ideas composed.

## 1. Aggregating diverse rollouts is a known win (best-of-N / self-consistency)

`ds-star-plus` already uses self-consistency at the verifier — **3× majority vote** on borderline
verdicts — for exactly the reason a spike scales up: the asymmetry of a silent wrong answer. A
spike lifts the same principle from the single judge call to the **whole solver pipeline**. Diverse
independent attempts decorrelate errors; agreement across *different strategies* (see
`personas.md`) is far stronger evidence than one agent agreeing with itself. The DS-STAR paper's
own related work cites self-consistency among the techniques that harden multi-step pipelines.

## 2. The blackboard architecture is the right collection substrate

**LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science** — Salemi,
Parmar, Goyal, Song, **Yoon, Zamani, Pfister, Palangi** (arXiv:2510.01285) — is by the DS-STAR
authors. A central agent posts a request to a shared blackboard; autonomous sub-agents **volunteer**
based on their capabilities, with no rigid master-slave controller that must know each agent's
expertise in advance. Reported gains: **+13–57% relative** end-to-end success and up to **+9%**
data-discovery F1 over strong baselines on KramaBench, DSBench, and DA-Code — the same benchmark
family DS-STAR uses. `ds-spike` adopts the post-and-collect pattern: each solver posts its
`{answer, code, assumptions, sufficiency}` to the board; the lead reconciles from the board.

## 3. Tree-search work supports "explore then evaluate, don't commit greedily"

I-MCTS (2502.14693), SWE-Search (2410.20285), Agent-Alpha (2602.02995) and Empirical-MCTS
(2602.04248) all show that exploring multiple candidate solutions and scoring them beats a single
greedy path. `ds-spike` is the *inter-agent* form of that idea (many whole solvers), complementary
to `ds-star-plus`'s optional *intra-agent* MCTS search mode (`../ds-star-plus/references/search_mode.md`).

## The honest caveat

These gains come at **N× cost**. The same literature that justifies the method also bounds its use:
spend it where a wrong number is expensive, not on routine questions. That gate is the skill's
"when this applies" section.
