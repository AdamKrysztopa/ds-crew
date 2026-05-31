# Reference papers

The corpus behind these skills. PDFs live in this folder locally but are **gitignored**
(`papers/*.pdf`) — they are large binaries. This index is the tracked record of what the
skills are built on and what the roadmap draws from. To re-fetch every PDF:

```bash
cd papers
while IFS=' ' read -r f id; do curl -sL -o "$f" "https://arxiv.org/pdf/$id"; done <<'EOF'
ds-star-2509.21825.pdf 2509.21825
da-code-2410.07331.pdf 2410.07331
dabstep-2506.23719.pdf 2506.23719
kramabench-2506.06541.pdf 2506.06541
i-mcts-2502.14693.pdf 2502.14693
deepverifier-2601.15808.pdf 2601.15808
empirical-mcts-2602.04248.pdf 2602.04248
agent-alpha-2602.02995.pdf 2602.02995
swe-search-2410.20285.pdf 2410.20285
blackboard-2510.01285.pdf 2510.01285
awm-2409.07429.pdf 2409.07429
voyager-2305.16291.pdf 2305.16291
expel-2308.10144.pdf 2308.10144
codeact-2402.01030.pdf 2402.01030
data-interpreter-2402.18679.pdf 2402.18679
aide-2502.13138.pdf 2502.13138
autokaggle-2410.20424.pdf 2410.20424
automl-agent-2410.02958.pdf 2410.02958
multiagent-debate-2305.14325.pdf 2305.14325
metagpt-2308.00352.pdf 2308.00352
self-consistency-2203.11171.pdf 2203.11171
EOF
```

---

## Foundation — the method these skills implement

| Paper | arXiv | Why it's here |
|-------|-------|---------------|
| **DS-STAR: Data Science Agent via Iterative Planning and Verification** — Nam, Yoon, Chen, Pfister (Google Cloud / KAIST, 2025) | [2509.21825](https://arxiv.org/abs/2509.21825) | The base method. Analyze-every-file → plan one verified step at a time → LLM-judge sufficiency. Implemented by `ds-star` and `ds-star-plus`. |

## Benchmarks DS-STAR is evaluated on (data-science-agent landscape)

| Paper | arXiv | Why it's here |
|-------|-------|---------------|
| **DABstep: Data Agent Benchmark for Multi-step Reasoning** — Egg et al. (Adyen / Hugging Face, 2025) | [2506.23719](https://arxiv.org/abs/2506.23719) | DS-STAR's headline benchmark (7 heterogeneous files, hidden labels, easy/hard split). Source of our cited cost + round-count numbers. |
| **KramaBench: AI Systems on Data-to-Insight Pipelines over Data Lakes** — Lai et al. (MIT, ICLR 2026) | [2506.06541](https://arxiv.org/abs/2506.06541) | Data-lake / data-discovery benchmark (up to 1,556 files). Motivates `ds-star-plus`'s two-stage retrieval and the ~8-pt oracle gap. |
| **DA-Code: Agent Data Science Code Generation Benchmark** — Huang et al. (2024) | [2410.07331](https://arxiv.org/abs/2410.07331) | Wrangling / ML / EDA generalization benchmark. The third leg of DS-STAR's evaluation. |

## More-advanced techniques — fuel for the roadmap

| Paper | arXiv | What we'd take from it |
|-------|-------|------------------------|
| **DeepVerifier — Inference-Time Scaling of Verification (rubric-guided)** — Wan, Fang et al. (CUHK / Tencent, 2026) | [2601.15808](https://arxiv.org/abs/2601.15808) | **Primary `plus` v2.1 upgrade.** Failure-taxonomy rubrics, verification decomposed into ≤3 targeted checks, graded 1–4 verdict, early-stop. Beats vanilla LLM-judge by 12–48% F1; recall of catching wrong answers 14% → 71%. Cost-aligned. |
| **I-MCTS: Introspective Monte Carlo Tree Search for Agentic AutoML** — Liang et al. (Ant Group / Rutgers, 2025) | [2502.14693](https://arxiv.org/abs/2502.14693) | Tree search over plans vs DS-STAR's greedy single path. Introspective node expansion (parent+sibling reflection) + hybrid reward (LLM value estimate → actual score). Opt-in hard-task escalation. |
| **Empirical-MCTS: Continuous Agent Evolution via Dual-Experience MCTS** — Lu et al. (2026) | [2602.04248](https://arxiv.org/abs/2602.04248) | Dual-experience (success + failure) memory to steer MCTS; informs the anti-repeat / escalation design. |
| **Agent Alpha: Tree Search Unifying Generation, Exploration and Evaluation** — Tang, Chen et al. (GWU, 2026) | [2602.02995](https://arxiv.org/abs/2602.02995) | Unifies generation/exploration/evaluation in one tree-search loop; reference architecture for a search-mode `plus`. |
| **SWE-Search: Enhancing Software Agents with MCTS and Iterative Refinement** — Antoniades, Örwall et al. (ICLR 2025) | [2410.20285](https://arxiv.org/abs/2410.20285) | Proof that MCTS + self-refinement transfers to code-writing agents; closest precedent for adding search to a code-generating DS agent. |
| **LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science** — Salemi, Parmar, Goyal, Song, **Yoon, Zamani, Pfister, Palangi** (Google / UMass, 2025–26) | [2510.01285](https://arxiv.org/abs/2510.01285) | **Substrate for the "Data Science SPIKE" skill (Track D).** By the DS-STAR authors. A central agent posts to a shared blackboard; autonomous sub-agents *volunteer* by capability (no rigid master-slave). +13–57% relative end-to-end success on KramaBench/DSBench/DA-Code. The "post requests, collect from all volunteers" pattern is exactly the multi-agent ensemble substrate. |

---

See [`../ROADMAP.md`](../ROADMAP.md) for how each of these maps to a concrete change in the
skills, and [`../skills/ds-star-plus/references/evidence.md`](../skills/ds-star-plus/references/evidence.md)
for how the *current* `plus` design is grounded in the DS-STAR paper.

---

## Patterns added in v1.2 (tracks E–M)

| Paper | arXiv | What we take from it |
|-------|-------|----------------------|
| **Agent Workflow Memory** — Zora Zhiruo Wang et al. (CMU, 2024) | [2409.07429](https://arxiv.org/abs/2409.07429) | **Track E — workflow memory.** Induces reusable workflow snippets from past episodes and retrieves them at inference time; grounds the skill-memory / retrieval layer that persists hard-won sub-plans across runs. |
| **Voyager: An Open-Ended Embodied Agent with Large Language Models** — Guanzhi Wang et al. (NVIDIA / Caltech, 2023) | [2305.16291](https://arxiv.org/abs/2305.16291) | **Track E — skill library.** Iteratively grows a versioned skill library via self-verification and curriculum; motivates storing and indexing verified code snippets as reusable skills across DS tasks. |
| **ExpeL: LLM Agents Are Experiential Learners** — Andrew Zhao et al. (2023) | [2308.10144](https://arxiv.org/abs/2308.10144) | **Track E — experience distillation.** Collects success/failure trajectories and distills task-level rules; informs the rule-extraction mechanism that turns past DS runs into actionable heuristics. |
| **Executable Code Actions Elicit Better LLM Agents (CodeAct)** — Xingyao Wang et al. (UIUC, 2024) | [2402.01030](https://arxiv.org/abs/2402.01030) | **Track F / J — code-as-action.** Replaces structured tool-calls with executable Python actions in a persistent interpreter; justifies the code-centric action space and stateful execution environment in DS agents. |
| **Data Interpreter: An LLM Agent For Data Science** — Sirui Hong / MetaGPT team (2024) | [2402.18679](https://arxiv.org/abs/2402.18679) | **Track G — dynamic plan rewriting.** Hierarchical DAG plan that rewrites nodes on execution feedback; the key precedent for mid-task plan repair rather than full replanning when a step fails. |
| **AIDE: AI-Driven Exploration in the Space of Code** — Zhengyao Jiang et al. (Weco AI, 2025) | [2502.13138](https://arxiv.org/abs/2502.13138) | **Track H — tree search over code drafts.** Tree search in solution-code space with greedy best-first selection and pruning; the primary reference architecture for the search-mode upgrade in competition settings. |
| **AutoKaggle: A Multi-Agent Framework for Autonomous Data Science Competitions** — Ziming Li et al. (2024) | [2410.20424](https://arxiv.org/abs/2410.20424) | **Track H — competition pipeline.** End-to-end multi-agent loop for Kaggle (feature engineering → model selection → ensemble); blueprints the competition-mode orchestration layer. |
| **AutoML-Agent: A Multi-Agent LLM Framework for Full-Pipeline AutoML** — Patara Trirat et al. (2024) | [2410.02958](https://arxiv.org/abs/2410.02958) | **Track H — full-pipeline AutoML.** Decomposes AutoML into specialized retrieval-augmented agents per stage (preprocessing, HPO, ensembling); informs modular agent hand-off design for end-to-end ML pipelines. |
| **Improving Factuality and Reasoning in Language Models through Multiagent Debate** — Yilun Du et al. (MIT / CMU, 2023) | [2305.14325](https://arxiv.org/abs/2305.14325) | **Track I — debate for correctness.** Multiple LLM agents propose and critique answers across rounds, converging to more factual responses; grounds the debate / cross-checking layer in the ds-spike ensemble. |
| **MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework** — Sirui Hong et al. (2023) | [2308.00352](https://arxiv.org/abs/2308.00352) | **Track K — role-based SOP agents.** Encodes human SOPs as agent roles with structured message passing; reference for assigning distinct analyst roles (data engineer, modeller, critic) within the ds-crew ensemble. |
| **Self-Consistency Improves Chain of Thought Reasoning in Language Models** — Xuezhi Wang et al. (Google Brain, 2022) | [2203.11171](https://arxiv.org/abs/2203.11171) | **Track L — majority-vote sampling.** Samples diverse reasoning paths and marginalises over answers via majority vote; the theoretical basis for the ensemble-voting and answer-aggregation step in ds-spike / ds-star-plus. |
