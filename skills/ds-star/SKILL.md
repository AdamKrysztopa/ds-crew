---
name: ds-star
description: "Solve data science tasks over one or many data files (CSV, JSON, Excel/XLSX, Markdown, TXT, SQLite, unstructured text) by writing and executing Python through an iterative plan, implement, execute, verify, refine loop with an LLM-as-judge sufficiency check. Use this skill WHENEVER the user asks a factoid or analytical question answered from data files, wants data wrangling/cleaning, EDA, statistics/hypothesis testing, a chart, or an ML prediction/submission produced FROM their data, especially when the answer requires reconciling MULTIPLE heterogeneous files, when the code runs but might still be wrong, or when a first attempt looks plausible but unverified. Trigger even if the user just drops files and asks what this says or to answer X from it, or uses words like analyze, compute, aggregate, join, merge, clean, summarize, predict, forecast, plot, or delta/total/top-N from the dataset. Do NOT use for prose writing, generic coding unrelated to a dataset, or questions answerable from general knowledge."
---

# DS-STAR: Data Science Agent via Iterative Planning and Verification

A workflow for answering data-science queries by generating Python that you actually run,
then checking — before you commit to an answer — whether the plan was *sufficient* to
answer the question. It is built for heterogeneous data and for tasks where there is no
ground-truth label to check against, so "the script executed" is **not** treated as
"the answer is correct."

This skill implements the method from *DS-STAR* (Nam et al., 2025). The core idea: don't
write one big plan up front. Start with one simple, executable step, look at its real output,
and grow the plan one verified step at a time — exactly how an analyst works incrementally
in a notebook.

## When this applies

Use it for: analytical/factoid questions over data files, multi-file joins, data wrangling,
EDA, statistics, visualization, and ML tasks that produce a file (e.g. `submission.csv`).
It shines when several files in different formats must be reconciled, when domain rules are
encoded in side files (a `tips.md`, a `fees.json`, a README sheet), and when a naive answer
would look fine but be subtly wrong.

## The cardinal rule

**Executable code is not a correct answer.** Most failures come from confidently filtering
on a column that doesn't exist, silently dropping rows, misreading a units/format note, or
answering a different question than was asked. The whole loop exists to catch this before
you report a number.

## Prerequisites

A code-execution environment with Python and pandas (plus numpy; and as needed openpyxl for
xlsx, scipy/scikit-learn/lightgbm for ML, matplotlib for charts, sqlite3 for `.sqlite`).
All input files live under a data directory — confirm the path with the user if unstated.
Read `references/prompts.md` for the exact role prompts to reuse for each step below.

---

## Stage 1 — Analyze every data file first

Before any planning, build a short text **description** of each file. This single step is the
biggest driver of correctness on hard tasks: it is what lets you discover the real column
names, value spellings, sheet names, and encodings instead of guessing.

For each file, write a small self-contained Python script that *loads and prints* the file's
essential structure, then run it and keep the stdout as that file's description:

- **CSV / TSV**: shape, column names, dtypes, missing-value counts, `df.head()`, and for
  low-cardinality object columns their unique values / value counts.
- **JSON**: top-level type (object vs array), keys ("columns"), and a few example records
  (pretty-printed, truncated).
- **Excel / XLSX**: list ALL sheet names first (tasks often hide data in a non-first sheet),
  then describe the relevant sheet(s) as above.
- **Markdown / TXT / unstructured**: metadata, line/section count, and a short head excerpt —
  do not assume a tabular "row" structure exists.
- **SQLite / archives**: list tables (or archive members), then describe the relevant table.

`scripts/analyze_file.py` is a ready-made describer for csv/tsv/json/xlsx/txt/md/sqlite —
run it per file (`python scripts/analyze_file.py <path>`) or use it as a template. Generation
of these scripts is independent per file, so do them all up front.

Guidance baked into the analyzer prompt (see `references/prompts.md`): print real content,
show only a few examples if data is large, and do **not** wrap loads in try/except — let a
real error surface so it can be fixed (see Stage 6).

**Scaling (many files).** If there are more than ~100 candidate files (data lakes), don't
load every description into context. Embed the query and each file description, rank by
cosine similarity, and carry only the top ~100 (or top-K) most relevant descriptions forward.
If the total is under that threshold, just use them all.

---

## Stage 2 — Initialize with ONE simple step

Ask the planner role for the *very first* step only — and make it executable on its own
(typically "load file X and show the relevant slice"). It does **not** need to be sufficient;
it just has to be a correct, runnable starting point. Implement it as a script with the coder
role, run it, and capture the result `r0`. Keep the running plan as `p = [p0]`.

---

## Stage 3 — Verify sufficiency (LLM-as-judge)

This is the part conventional agents skip. Using the verifier role, judge whether the
*current* plan + its code + its actual execution output is enough to answer the question.
Condition the judgment on all four: the cumulative plan, the user's query, the current code,
and its real output `r_k`. Output is binary: **sufficient** or **insufficient**.

Grounding the judge on the real output (not just the plan text) is what makes it useful — it
can see that a needed column is empty, that a filter returned 0 rows, or that the printed
number doesn't actually answer the question.

If **sufficient** → go to Stage 5 (finalize). Otherwise → Stage 4.

---

## Stage 4 — Route the refinement: add vs. backtrack

When insufficient, decide *how* to fix it using the router role. The decision is one of:

- **Add Step** — the plan so far is correct but incomplete. Keep `p` and generate the next
  step (planner role, conditioned on the latest result so the new step targets the gap).
- **"Step l is wrong"** — a specific earlier step is erroneous. **Truncate** the plan to
  everything before it (`p <- p[0..l-1]`) and regenerate from there.

**Why truncate-and-regenerate instead of editing the bad step in place?** The paper's
empirical finding (and a good default): directly patching a flawed step tends to produce an
over-complicated replacement that the verifier flags again next round. Dropping it and
re-planning via fresh sampling converges faster. Backtracking beats piling correct-looking
steps on top of a broken one, because errors compound downstream.

Then re-implement the updated plan (coder role, building on the prior code as a base so each
round is incremental, not a rewrite), execute, and loop back to Stage 3.

Repeat plan → code → execute → verify → route until the verifier returns **sufficient** or a
maximum iteration budget is reached (default **20**). Expect easy tasks to settle in ~3 rounds
and genuinely hard, multi-file tasks to need ~5–6+; budget accordingly and don't stop at the
first plausible-looking number. If you hit the cap, finalize with the best plan so far and say
so plainly.

A full worked trace (a multi-file fee-delta question that takes 5 routing rounds, including
two backtracks, before passing) is in `references/worked_example.md`.

---

## Stage 5 — Finalize to the required format

Reporting format errors are a common, silent cause of "wrong" answers. Once the plan is
sufficient, produce a final, self-contained script (finalizer role) that prints the answer in
exactly the format requested: rounding/decimal places, a literal string template or JSON
shape, a CSV that matches a provided `sample_result.csv` column order, a file saved to the
required name/path, or a chart with the exact title/labels. If the answer is already in the
last execution result, the finalizer just reprints it in the required shape.

State the final answer to the user and show the final script. Briefly note any consequential
assumption you had to make (e.g. "no payment-gateway column existed, so NexPay was matched via
`card_scheme`").

---

## Stage 6 — Debugging (whenever a script errors)

A traceback alone is often not enough to fix data-centric bugs, because the real cause is
usually in the data (a column is a list not a scalar, a sheet name differs, an encoding,
a stray `?`/`NEW`/`-` sentinel). So when any script raises:

1. Summarize/trim the traceback to the relevant part (keep the failing line).
2. Regenerate the script conditioned on **(a)** the original code, **(b)** the trimmed
   traceback, AND **(c)** the file descriptions from Stage 1 — that data context is what
   resolves most failures.

Apply the same to the Stage-1 analyzer scripts (there, fix using only the trimmed traceback,
since descriptions don't exist yet).

Execution policy + provenance: see `../ds-star-plus/references/sandbox.md`.

---

## Quick reference: the agent roles

| Role | Input | Output |
|------|-------|--------|
| Analyzer | one file path | Python that prints the file's structure → run for its description |
| Planner | query + descriptions (+ plan + last result) | the next single executable step |
| Coder | plan (+ base code) + descriptions | a single Python script implementing the cumulative plan |
| Verifier | plan + query + code + result | `sufficient` / `insufficient` |
| Router | plan + query + result + descriptions | `Add Step` or `Step l` |
| Finalizer | code + result + query + format guidelines | final script in the required output format |
| Debugger | code + trimmed traceback + descriptions | corrected script |

Exact prompt text for each role: `references/prompts.md`.

## Common pitfalls this loop is designed to prevent

- Filtering on a value/column that doesn't exist (caught by Stage 1 + verifier).
- Treating "code ran" as "answer correct" (Stage 3 exists precisely for this).
- Compounding work on top of a wrong early step (Stage 4 backtracking).
- Right computation, wrong reported format (Stage 5).
- Guessing column names/sheet names from memory (Stage 1 + Stage 6 data-aware debug).
