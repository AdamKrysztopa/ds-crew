# Quickstart

Get from zero to a verified data-science answer in under 2 minutes.

## 1. Install

```bash
# Add the marketplace (one-time per machine)
claude plugin marketplace add AdamKrysztopa/ds-crew

# Install ds-crew (user scope — available in all your projects)
claude plugin install ds-crew@ds-crew --scope user
```

## 2. Get a sample dataset

Download the OWID CO₂ dataset (~50,000 rows, CC BY 4.0) into a working directory:

```bash
mkdir -p my-analysis && cd my-analysis
curl -L "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv" \
     -o owid-co2-data.csv
```

The file is a country-year panel of CO₂ and greenhouse-gas emissions maintained by
Our World in Data.

> **Failure mode this dataset exercises:** per-capita vs absolute values, and
> World/region aggregate rows mixed with individual countries — two of the six
> DS failure modes the verifier rubric checks.

> **Alternative (if you have the ds-crew repo cloned):** `python3 scripts/fetch_datasets.py owid_co2`

## 3. Ask a question

Open Claude Code in the directory containing `owid-co2-data.csv` and run:

```
/ds-star-plus

Dataset: owid-co2-data.csv
Question: What were global CO2 emissions in billion tonnes in 2022?
          Use the "World" row and the `co2` column (fossil + land-use, MtCO2).
          Report the answer in billion tonnes (Gt CO2).
```

## Expected output

```
Final answer: ~37.1 Gt CO2 (2022, World row, `co2` column)
Verifier score: 4/4 (all checks pass)
```

The `co2` column in the OWID dataset is in million tonnes (Mt); the correct answer
requires dividing by 1,000 to convert to billion tonnes (Gt). A score of 4/4 means
the answer passed all six DS failure-mode checks: wrong column, dropped rows,
units mismatch, scope error, format mismatch, and question substitution.

> **Why ~37.1 Gt?** The OWID `owid-co2-data.csv` records `co2 ≈ 37,123` Mt for
> `iso_code = "OWID_WRL"` (World) in 2022. Divided by 1,000: **37.1 Gt CO2**.
> This figure is consistent with the IEA/GCP 2022 global emissions estimate.

## Next steps

- For fuzzy questions: start with `/ds-conduct` — it inspects your data and builds a plan.
- For high-stakes work: use `/ds-spike` (ensemble of N parallel solvers).
- See [docs/USAGE.md](USAGE.md) for the full routing guide.
- See [docs/datasets.md](datasets.md) for the full catalog of four starter datasets.
