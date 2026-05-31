# Data-lake retrieval (A3) — two stages plus column-level matching

For data lakes (N > ~100 files; KramaBench's Astronomy domain has 1,556) you cannot load every file
description into context. DS-STAR retrieves top-K by query↔description embedding cosine. That leaves
accuracy on the table — KramaBench Table 2: retrieval 44.69 vs oracle 52.55, a **~8-point gap** the
paper flags as "advanced data discovery... a promising direction." This file is the v2 retrieval
policy and the A3 upgrade that chases that gap.

## Stage 1 — Embedding recall (cheap, high-recall)

Embed the user's query and each file's **schema digest** (not the full description — cheaper, and
column names carry most of the signal). Take the top ~150 by cosine similarity. Goal: recall, not
precision — get the relevant files into the candidate pool even if ranked imperfectly.

## Stage 2 — Haiku relevance pass (cheap, precision)

Run a Haiku pass over the ~150 digests: "which of these files are plausibly needed to answer *this*
query?" Keep only those, down to ~top-K. This recovers files that embed poorly against the query
phrasing but are obviously on-topic by name/columns — the main failure mode of pure cosine.

## Stage 3 (A3) — Column-level / value matching re-rank

The upgrade that targets the oracle gap: for the surviving candidates, score on **structure**, not
just text:
- **column-name match**: does the file expose a column the query needs (an entity id, the metric, a
  join key)? Exact/fuzzy column-name overlap with the query's nouns.
- **value overlap**: if the query names a literal (`NexPay`, a country, a merchant), does any
  low-cardinality column actually *contain* that value? A file that holds the asked value beats one
  that merely mentions it in prose.
- **join reachability**: keep files that share a key with an already-selected file, even if they
  don't match the query directly — they're needed to *complete* the join (the classic multi-file
  miss).

Re-rank by a blend of the embedding score and these structural signals; carry the final top-K
forward. The structural signals are cheap (computed from digests/profiles) and directly attack why
cosine alone under-retrieves.

## Budget & fallback

- If total files < ~100, skip retrieval entirely — use all descriptions (DS-STAR's own rule).
- Cache digests so Stage 1 embeddings are computed once per task.
- If retrieval confidence is low (no candidate clearly matches a needed value/key), say so and ask
  the user to point at the right files rather than guessing — a wrong file set silently dooms the run.

Grounded in KramaBench ([2506.06541](https://arxiv.org/abs/2506.06541)) and the blackboard
discovery work ([2510.01285](https://arxiv.org/abs/2510.01285)); see `evidence.md` §5.
