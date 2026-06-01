# Workflow Plan Template

Fill this template after Stage 2 (Grill) is complete. Present the filled plan to the user
for approval before executing any skill. Do not proceed to Stage 4 until the user explicitly
approves.

---

## TEMPLATE

```
## Conducted Workflow Plan

**Question / goal:** [FILL — one sentence capturing the user's analytical intent]

**Data files:**
- [FILL — filename, row count, key columns]
- [FILL — repeat per file]

**Patterns detected:** [FILL — comma-separated list from trigger_catalog.md that fired]

**Skills to invoke (in order):**
1. [FILL — skill name] — [FILL — reason / what it produces]
2. [FILL — skill name] — [FILL — reason / what it produces]
   ... (repeat as needed)

**ds-spike configuration** (if ensemble selected):
- N personas: [FILL — number, e.g. 3]
- Personas: [FILL — e.g. statistician / SQL-first / ML-first]
- Debate mode: [FILL — yes / no]

**ds-model included:** [FILL — yes / no; if yes, state target column and evaluation metric]

**Analysis spec path:** [FILL — path where ds-clarify will write analysis-spec.md,
                         e.g. data/analysis-spec.md]

**Checkpoints:**
| After step | What to surface | Condition to backtrack |
|---|---|---|
| [FILL — step N] | [FILL — output to show user] | [FILL — condition that triggers a backtrack] |
| [FILL — step N+1] | [FILL — output to show user] | [FILL — condition that triggers a backtrack] |

**Estimated rounds:** [FILL — rough total LLM call count]
```

---

## WORKED EXAMPLE

Scenario: user uploads `payments.csv` and `merchants.json` and asks
"compute monthly churn rate for our merchants."

---

```
## Conducted Workflow Plan

**Question / goal:** Compute the monthly merchant churn rate from payment activity data,
for the trailing 12 months ending last full calendar month.

**Data files:**
- payments.csv — 2,847,312 rows; columns: payment_id, merchant_id, created_at (datetime),
  amount_eur (float), status (enum: success/failed/refunded), card_scheme
- merchants.json — 18,204 records; fields: merchant_id, signup_date, country, tier,
  is_active (bool)

**Patterns detected:**
- Timestamp column (created_at) → time-series / temporal split question
- Shared key column (merchant_id) → join-intent question
- Target-shaped column (is_active / churn) + user mentioned "churn" → predictive-task question
- High-stakes context: user said "our merchants" (internal report likely) → ensemble option offered

**Skills to invoke (in order):**
1. data-profile — peek at payments.csv + merchants.json to confirm row counts, null rates,
   merchant_id join coverage, date range, and churn signal distribution.
2. ds-clarify — pin down: churn definition (0 transactions in trailing N days?), time window
   (calendar month boundaries, which timezone), merchant population in scope (all tiers or
   paying only), null/sentinel handling. Produces data/analysis-spec.md.
3. ds-spike (N=3 personas) — run three independent analysts against the spec; surface consensus
   monthly churn rate series + minority report on any disputed definition.

**ds-spike configuration:**
- N personas: 3
- Personas: statistician (cohort-survival framing) / SQL-first (window-function aggregation) /
  ML-first (feature-engineered churn classifier as a cross-check)
- Debate mode: yes — resolve disagreements on churn window length and treatment of reactivated
  merchants before presenting the final number.

**ds-model included:** no — question is descriptive / diagnostic, not a forward prediction.
(If user later asks "predict which merchants will churn next month," re-run with ds-model.)

**Analysis spec path:** data/analysis-spec.md

**Checkpoints:**
| After step | What to surface | Condition to backtrack |
|---|---|---|
| data-profile | Row counts, null rates table, merchant_id join coverage (% of payment rows matched), date range of payments, churn signal prevalence | If join coverage < 80 % or date range is shorter than 12 months → backtrack to Stage 2 and re-ask scope questions |
| ds-clarify | Full analysis-spec.md — confirm churn definition, time window, population scope, null policy | If user revises churn definition or time window → re-run data-profile to check feasibility, then re-confirm spec |
| ds-spike consensus | Monthly churn rate series (table + chart), confidence band across 3 personas, minority report if any persona diverged by >1 pp | If all three personas disagree substantially → surface each rationale, ask user to adjudicate definition before presenting final answer |

**Estimated rounds:** ~12–18 LLM calls total (3 for profile, 4 for clarify, ~8–12 for spike
across 3 personas + consensus synthesis).
```

---

### Final output format (after checkpoints pass)

Present to the user:

1. **Consensus result** — the monthly churn rate series agreed on by ≥2/3 personas, with the
   exact definition from the spec ("merchant with 0 successful transactions in calendar month,
   timezone Europe/Warsaw, tiers Standard + Premium only").
2. **Minority report** (if any) — which persona diverged, why, and what number they got.
3. **Run manifest** — list of skills invoked, spec path, and any assumptions recorded.

---

**Backtrack rules (general):**

| Situation | Backtrack to |
|---|---|
| Profile reveals a data-quality blocker (e.g. 40 % null on join key) | Stage 2 — re-ask scope / cleaning question, then re-profile |
| User revises a key spec decision mid-run | Stage 3 — rebuild plan section affected by the revision |
| Spike personas all disagree and user cannot adjudicate | Stage 2 — return to ds-clarify with the specific disputed item |
