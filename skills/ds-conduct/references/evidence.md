# Evidence — Orchestrator Patterns

## Blackboard control-agent

**Source:** Salemi et al., "Agentic Information Retrieval," arXiv 2510.01285 (2025).

The blackboard architecture posts a structured request to a shared workspace; specialist agents
monitor the board and volunteer to handle the sub-tasks that match their capability. Control
returns to the central agent once each specialist completes.

> "The ds-conduct orchestrator plays the role of the blackboard control-agent: it posts a
> request and the specialized sub-skills volunteer by capability."

Applied in `ds-conduct`: Stage 1–2 produce the blackboard entry (peeked schema + resolved
questions); Stages 3–4 dispatch the matching sub-skills (data-profile, ds-clarify, ds-star-plus,
ds-spike) and collect their outputs at each checkpoint.

---

## Supervisor pattern

**Source:** Hong et al., "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework,"
arXiv 2308.00352 (ICLR 2024).

MetaGPT introduces a supervisor (meta-agent) that decomposes a high-level software-engineering
goal into a sequence of standardised operating procedures, assigns each step to a specialist
role (Product Manager, Architect, Engineer, QA), and checkpoints outputs at role boundaries
before the next role begins.

> "Supervisor architecture: a meta-agent decomposes a high-level goal into a workflow, assigns
> sub-tasks to specialist agents, and checkpoints at each handoff."

Applied in `ds-conduct`: `ds-conduct` is the supervisor; data-profile / ds-clarify /
ds-star-plus / ds-spike are the specialist roles. The workflow plan template
(`workflow_plan_template.md`) plays the role of MetaGPT's SOP — it encodes the ordered
handoffs and the checkpoint criteria at each boundary.

---

## Relationship to DS-STAR verification

**Source:** DS-STAR (ds-star-plus SKILL.md and references).

DS-STAR's verifier checks whether a produced answer matches the task specification. `ds-conduct`
ensures a concrete, written specification exists *before* the first analysis skill runs — so the
verifier has a rubric to check against. Without `ds-conduct` (or `ds-clarify`), the verifier
can only confirm internal consistency, not alignment with the user's true intent.

The three-layer chain is:
```
ds-conduct (orchestration) →
  ds-clarify (spec production) →
    ds-star-plus / ds-spike (analysis + verification against spec)
```
