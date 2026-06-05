# Data-lake retrieval (A3) — two stages plus column-level matching

For data lakes (N > ~100 files; KramaBench's Astronomy domain has 1,556 files) you cannot load every
file description into context. DS-STAR retrieves top-K by query↔description embedding cosine. That
leaves accuracy on the table — **the DS-STAR paper's own Table 2** (2509.21825, evaluated on
KramaBench): retrieval **44.69** vs relevant-files oracle **52.55**, an **8-percentage-point gap**
the paper flags as "advanced data discovery... a promising direction." (KramaBench (2506.06541) is
the benchmark and the source of the data-lake scale; its *own* "oracle" is a different,
input-obfuscation setting — don't conflate.) This file is the v2 retrieval policy and the A3 upgrade
that chases that gap.

## Stage 1 — Embedding recall (cheap, high-recall)

Embed the user's query and each file's **schema digest** (not the full description — cheaper, and
column names carry most of the signal). Take the top ~150 by cosine similarity. Goal: recall, not
precision — get the relevant files into the candidate pool even if ranked imperfectly.

## Stage 2 — Haiku relevance pass (cheap, precision)

Run a Haiku pass over the ~150 digests: "which of these files are plausibly needed to answer *this*
query?" Keep only those, down to ~top-K. This recovers files that embed poorly against the query
phrasing but are obviously on-topic by name/columns — the main failure mode of pure cosine.

## Stage 3 (A3) — Column-level / value matching re-rank

The upgrade that targets the oracle gap. **No new tooling — this folds into the Stage 2 Haiku
pass.** That pass already has the query and each surviving file's schema digest in context; have it
additionally emit, **per file**, the three structural judgments below. Everything scores against the
schema digest the file-profiling step already produced (column names, dtypes, sheet names, and the
low-cardinality value lists) — whatever language that step ran in. No extra I/O, no extra call.

For each surviving candidate, judge:

1. **column-name match** — does the file expose a column the query needs (an entity id, the metric,
   a join key)? Exact or fuzzy overlap between the query's nouns and the column names (treat
   `customer_id` ≈ "customer", `claim_amount` ≈ "claim"/"amount").
2. **value overlap** — if the query names a literal (`NexPay`, a country, a merchant), does any
   **low-cardinality** column actually *contain* that value? A file that holds the asked value beats
   one that merely mentions it in prose.
3. **join reachability** — keep files that share a key column with an **already-selected** file,
   even if they don't match the query directly — they're needed to *complete* the join (the classic
   multi-file miss).

**The keep rule (recall-biased — this is the point).** Carry a file forward into the final top-K if
it is strong on **either** the embedding/Haiku-relevance signal **or** any structural signal above.
Do **not** require both. A missed file is unrecoverable downstream — the whole run silently fails on
a file that was never loaded — so when the two signals disagree, keep the file. Bias toward recall
and let execution prune what is genuinely irrelevant later.

This directly attacks why cosine alone under-retrieves (it ranks by query↔description prose
similarity and misses files that are obviously on-topic by column/value structure), which is the
documented source of the oracle gap below.

## Budget & fallback

- If total files < ~100, skip retrieval entirely — use all descriptions (DS-STAR's own rule).
- Cache digests so Stage 1 embeddings are computed once per task.
- If retrieval confidence is low (no candidate clearly matches a needed value/key), say so and ask
  the user to point at the right files rather than guessing — a wrong file set silently dooms the run.

Grounded in KramaBench ([2506.06541](https://arxiv.org/abs/2506.06541)) and the blackboard
discovery work ([2510.01285](https://arxiv.org/abs/2510.01285)); see `evidence.md` §5.
