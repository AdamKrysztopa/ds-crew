# Smoke Run — DABench (subset)

> **⚠️ Superseded — pre-harness-fix numbers.** This raw smoke run predates the three
> scoring/harness fixes (answer truncation, last-token-wins on echoed templates,
> all-or-nothing scoring) documented in
> [`docs/experiments/README.md`](../../../docs/experiments/README.md#scoring--harness-fixes).
> The numbers below (15-q, 86.7%) are kept verbatim as the original run record for
> provenance. **The corrected, canonical result is the 18-question study: ds-star
> 17/18 (94.4%), effectively 18/18 once the Q8 benchmark-label bug is accounted for.**
> See [`docs/experiments/`](../../../docs/experiments/).

**Questions:** 15 (13 easy/medium, 2 hard)
**Variants:** baseline, ds-star, ds-star-plus, ds-spike

| variant | n | accuracy | accuracy-hard | $/task | tokens/task | median rounds |
|---|---|---|---|---|---|---|
| baseline | 15 | 0.867 | 0.500 | 0.0912 | 101541 | 1 |
| ds-spike | 15 | 0.800 | 0.500 | 0.2583 | 258525 | 1 |
| ds-star | 15 | 0.867 | 0.500 | 0.0951 | 94344 | 1 |
| ds-star-plus | 15 | 0.867 | 0.500 | 0.1033 | 103126 | 1 |
