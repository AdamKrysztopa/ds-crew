# Debate Protocol Reference

Opt-in multi-agent debate for ds-spike (Stage 3.5). Enable with `debate: true`.

Cite: Du et al., "Improving Factuality and Reasoning in Language Models through Multiagent Debate", arXiv:2305.14325.

## Protocol

After Stage 3 (blackboard collection), run up to 2 debate rounds:

1. Each solver receives all peer answers and rationales (anonymised or attributed — implementer's choice).
2. Each solver may revise its answer; if it does, set `revised: true` on its record.
3. After ≤2 rounds, proceed to Stage 4 (reconciliation) with the final post-debate answers.

## Round cap

Maximum 2 debate rounds. Stop early if no solver revised in the last round (consensus reached).
Cap prevents infinite loops and runaway cost.

## Anti-herding guard

Debate can amplify a confident-wrong majority. ALWAYS preserve the minority report. If a solver
did not revise, its original answer stands in the minority report regardless of peer pressure. The
aggregator uses the FINAL post-debate answers for consensus, but the minority report surfaces any
solvers who disagreed after debate, not just before.

## Cost note

Debate adds ≤2 extra rounds per solver. Opt-in only — default ds-spike is one-shot. Enable with
`debate: true` flag when calling ds-spike.
