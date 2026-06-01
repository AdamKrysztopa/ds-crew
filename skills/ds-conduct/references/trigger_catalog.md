# Data-Pattern Trigger Catalog

When `ds-conduct` peeks at the data (Stage 1), match detected patterns against this table.
For every matching row, ask the corresponding question before assembling the workflow plan.
Questions should be grounded in what was actually seen ("I see a `created_at` column —
is this a time-series problem?"), not asked in the abstract.

| Data pattern detected | Question to ask | Candidate skill / route |
|---|---|---|
| Timestamp / datetime column detected | "Is this a time-series or panel problem? What prediction horizon or aggregation window? Should we respect temporal order in splits?" | Time-aware ds-star-plus or ds-model |
| Two or more files share a candidate key column | "Is a join intended? What join type (inner / left / outer)? Which file is the left table?" | Multi-file ds-star-plus |
| Target-shaped column (binary, bounded 0–1, or named label / target / y / churn) + user mentions prediction | "Is this a predictive task? What is the evaluation metric? What is the prediction horizon?" | ds-model |
| Many files (>10) / data-lake structure | "Do you want to search all files or a specific subset? Is there a schema registry or a master index file?" | ds-star-plus with two-stage retrieval |
| High-cardinality ID column (unique count ≈ row count) | "Is this an entity identifier? Should the analysis be per-entity or aggregated across all entities?" | Groupby-first ds-star-plus |
| Heavy missingness (>20 % null in key columns) or dirty indicators (sentinel values, inconsistent types) | "Should we profile the data first? Are nulls meaningful (e.g. 'no event occurred') or are they data-quality issues that need cleaning?" | data-profile first, then ds-star-plus |
| High-stakes context: user mentions 'important', 'board', 'irreversible', 'report', 'decision' | "This sounds high-stakes — should we run an ensemble of data-scientist personas for higher confidence? (adds ~3× time)" | ds-spike (with optional debate) |
| Wide table (>50 columns) with no clear target | "With this many columns, should we first identify which features are relevant to your question, or do you already have a column list in mind?" | data-profile feature-importance pre-pass, then ds-clarify |
| Multiple currency / unit columns, or mixed locale number formats | "I see amounts in what may be different currencies or units — should we normalise to a single unit before analysis? Which reference rate / date?" | ds-clarify (units & scale item) → ds-star-plus |
| Nested or semi-structured column (JSON strings, list-like values, pipe-delimited) | "Some columns appear to contain nested data. Should we flatten them, or treat them as opaque strings?" | ds-star-plus with pre-processing note in spec |

---

**Usage note:** Multiple patterns may fire on the same dataset. Ask all triggered questions in a
single batched message (Stage 2 of `ds-conduct`) rather than one round-trip per pattern.
Unanswered items block plan assembly — record every answer in the workflow plan before proceeding.
