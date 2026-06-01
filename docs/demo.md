# ds-crew demo recording guide

The most persuasive artifact is a short recording showing ds-crew catching a silent data error
before it reaches the analyst. This guide reproduces that recording exactly.

## Scenario

**Dataset:** Online Retail II (UCI id 502, CC BY 4.0) — a real e-commerce transaction log
with a known silent failure: ~25 % of rows are cancellations (InvoiceNo starting with `C`),
negative quantities represent returns, and ~25 % of rows have a null `CustomerID`.

**Question asked:** "What was total revenue in 2010?"

**What ds-crew catches:** without filtering cancellations and returns, a naive sum
over `Quantity * UnitPrice` overstates revenue and the verifier flags it as a scope error.

## Setup (one-time)

```bash
# 1. Fetch the dataset (no data committed to the repo)
python3 scripts/fetch_datasets.py online_retail_ii
# -> data/online_retail_ii/online+retail+ii.zip   (unzip it)
unzip -o "data/online_retail_ii/online+retail+ii.zip" -d data/online_retail_ii/

# 2. Verify your Python env has the analysis packages
# In a new Claude Code session:
/ds-env-setup
```

## Record

```bash
# Install asciinema if needed: brew install asciinema
asciinema rec docs/demo.cast --title "ds-crew: catching a silent revenue error"
```

Inside the recording, open a new Claude Code session and type:

```
/ds-conduct

[when prompted for data] data/online_retail_ii/Year 2010-2011.xlsx
[when prompted for question] What was total revenue in 2010?
```

Watch ds-crew:
1. **Peek** — detect the timestamp column, the cancellation prefix pattern, the null CustomerID rate
2. **Grill** — ask "should we exclude cancellations (C-prefixed invoices)?"
3. **Solve** — filter correctly, compute revenue, verifier confirms
4. **Report** — surface the scope decisions it made

Stop recording: `Ctrl-D` or `exit`.

## Publish

```bash
# Option A: upload to asciinema.org (creates a shareable link)
asciinema upload docs/demo.cast

# Option B: convert to SVG for embedding in README (no external service)
# brew install svg-term-cli
svg-term --cast docs/demo.cast --out docs/demo.svg --window --width 120 --height 35
```

Then embed in README.md (the placeholder `![demo](docs/demo.svg)` is already there).

## Attribution

Online Retail II: Daqing Chen, Sai Liang Sain, and Kun Guo, "Data Mining for the Online Retail
Industry: A Case Study of RFM Model-Based Customer Segmentation Using Data Mining", Journal of
Database Marketing and Customer Strategy Management, 2012. CC BY 4.0. UCI ML Repository id 502.
