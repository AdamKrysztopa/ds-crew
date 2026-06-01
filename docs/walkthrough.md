# Walkthrough — from a raw file to a reviewed answer

This is the whole arc the plugin is *for*: you have a messy dataset and a vague goal, and
you want a structured, executable, **reviewed** starting point — not a black-box number you
have to take on faith. It uses a real dataset with a known trap, so you can see the skills
catch a silent error rather than sail past it.

> This walkthrough shows representative output (abridged for length). The exact prose Claude
> produces varies run to run; the *structure* — peek → clarify → solve → verify → handback —
> is what's stable. To record your own terminal cast of this run, see [`demo.md`](demo.md).

---

## The setup

**Dataset:** [Online Retail II](https://archive.ics.uci.edu/dataset/502) (UCI id 502, CC BY 4.0) —
a real e-commerce transaction log. It has three traps that quietly corrupt a naive answer:

- ~25% of rows are **cancellations** (`InvoiceNo` starting with `C`)
- negative `Quantity` rows are **returns**
- ~25% of rows have a **null `CustomerID`**

**Your goal (deliberately vague):** *"What was total revenue in 2010?"*

A one-line `df.eval("Quantity * UnitPrice").sum()` answers this — and is **wrong**, because it
counts cancellations and returns as positive revenue. Nothing in the data tells you it's wrong.
That's the failure class this plugin exists to surface.

```bash
python3 scripts/fetch_datasets.py online_retail_ii
unzip -o "data/online_retail_ii/online+retail+ii.zip" -d data/online_retail_ii/
```

---

## Step 1 — `/ds-conduct`: peek before committing

You don't know which skill you need, so you start at the front door.

```
/ds-conduct   data/online_retail_ii/Year 2010-2011.xlsx
```

`ds-conduct` profiles the file *before* asking you anything, and reports what it sees:

```
541,910 rows × 8 cols. Detected:
  • InvoiceNo (object) — 9,288 values start with "C"  → looks like cancellations (~25%)
  • Quantity (int)     — 10,624 negative values        → returns / adjustments
  • CustomerID (float) — 135,080 nulls (24.9%)
  • InvoiceDate (datetime) — spans 2009-12 … 2011-12   → "2010" is ambiguous: calendar 2010?
  • UnitPrice (float)  — 2 negative, 40 zero           → bad rows or freebies?

Before I compute "total revenue in 2010" I need three decisions from you ↓
```

It then **routes**: because the question is under-specified *and* the data has scope traps,
it pulls in `ds-clarify` rather than guessing.

---

## Step 2 — `/ds-clarify`: turn fuzzy intent into a checkable contract

`ds-clarify` interrogates exactly the ambiguities that would otherwise become silent errors,
and writes the answers to `analysis-spec.md` — the contract the verifier will later check against.

```
Q1. "Revenue" — include or exclude cancellations (C-prefixed invoices)?
    → [exclude]  (standard: cancellations reverse a sale)
Q2. Returns (negative Quantity) — net them against revenue, or drop them?
    → [net]      (revenue should reflect refunds)
Q3. "2010" — calendar year 2010, or your fiscal year?
    → [calendar 2010, i.e. 2010-01-01 … 2010-12-31]
Q4. Rows with null CustomerID — keep? (they have valid InvoiceDate + amount)
    → [keep]     (revenue isn't conditional on knowing the customer)
Q5. Zero / negative UnitPrice rows — keep or drop?
    → [drop]     (not real sales)
```

Output — `analysis-spec.md`:

```markdown
# Analysis spec: total revenue, calendar 2010
- Metric: sum(Quantity * UnitPrice)
- Scope: InvoiceDate in [2010-01-01, 2010-12-31]
- Exclude: InvoiceNo starting with "C" (cancellations)
- Include: negative Quantity (returns net against revenue)
- Include: null CustomerID rows
- Exclude: UnitPrice <= 0
- Output token: @total_revenue_2010[<value>]
```

This is the step that changes a *precisely-answered wrong question* into a precisely-answered
**right** one. No amount of downstream verification can fix an intent you never pinned down.

---

## Step 3 — `/ds-star-plus`: solve against the spec, with the loop

```
/ds-star-plus   (reads analysis-spec.md + the data file)
```

It writes and runs Python iteratively — load → filter to the agreed scope → compute → and on
each round the verifier checks the result against 7 failure modes (wrong column/value, dropped
rows, units, scope, format, question-substitution, missing output token):

```
round 1  load + peek                          verdict 2/4  "no scope filter applied yet"
round 2  filter cancellations + date + price  verdict 3/4  "returns not yet handled per spec"
round 3  net returns, keep null CustomerID    verdict 4/4  "matches spec; scope printed"
FINALIZE  @total_revenue_2010[748957.02]
```

Crucially, the **naive** answer (no filtering) would have been ≈ $823k. The verified answer is
≈ $749k. The ~$74k difference *is* the silent error — and the run shows you exactly which scope
decisions produced it.

---

## Step 4 — `/ds-verify`: an independent grade

You can audit the result from any source against the same rubric:

```
/ds-verify   answer=748957.02  spec=analysis-spec.md  code=<the final script>

score 4/4 — sufficient
  ✓ scope matches spec (2010 calendar, cancellations excluded, returns netted)
  ✓ units consistent (currency, no conversion)
  ✓ output token present and well-formed
  ✓ no silently dropped rows beyond the spec's explicit exclusions
```

---

## Step 5 — the handback (this is the point)

The run ends with what stays *yours*, surfaced explicitly rather than buried:

```
Answer: total 2010 revenue = £748,957.02

Decisions baked into this number (review these — they are judgment calls, not facts):
  • cancellations excluded, returns netted   → if your finance team books gross, this changes
  • null-CustomerID rows kept                 → if "revenue" means attributable revenue, drop them
  • UnitPrice<=0 dropped (42 rows)            → confirm none were legitimate promotions

This is a defensible kickoff figure, not an audited financial statement.
```

That's the whole thesis in one screen: the plugin did the mechanical work fast and correctly,
showed its scope decisions, and handed the *interpretation* back to you. The 5 minutes it took
replaced an hour of plumbing — and it caught the cancellation trap that a one-liner would have
shipped silently.

---

## What each skill contributed

| step | skill | what it added |
|------|-------|---------------|
| 1 | `ds-conduct` | saw the traps in the data *before* asking, routed to clarification |
| 2 | `ds-clarify` | turned "revenue in 2010" into a checkable `analysis-spec.md` |
| 3 | `ds-star-plus` | solved against the spec; verifier caught the missing scope filter |
| 4 | `ds-verify` | independent grade against the 7 failure modes |
| 5 | — | surfaced the judgment calls instead of hiding them |

For the closed-form accuracy numbers behind step 3's verifier, see
[`docs/experiments/`](experiments/README.md) (DABench: 94.4%, effectively 18/18).
