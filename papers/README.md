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

---

See [`../ROADMAP.md`](../ROADMAP.md) for how each of these maps to a concrete change in the
skills, and [`../skills/ds-star-plus/references/evidence.md`](../skills/ds-star-plus/references/evidence.md)
for how the *current* `plus` design is grounded in the DS-STAR paper.
