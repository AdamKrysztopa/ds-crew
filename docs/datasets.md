# Starter-four demo datasets

Four confirmed open-data datasets chosen for distinct domains, built-in silent failures to catch,
and clean licensing. Data is **never committed** to the repo — fetch on demand:

```bash
python3 scripts/fetch_datasets.py online_retail_ii   # one
python3 scripts/fetch_datasets.py --all              # all four
```

## The catalog

| # | Dataset | Domain | License | Failure mode it exercises | Skills it showcases |
|---|---------|--------|---------|---------------------------|---------------------|
| 1 | **Online Retail II** (UCI id 502) | Retail / e-commerce | CC BY 4.0 | Cancellations (C-prefixed invoices), negative quantities = returns, null CustomerID, mixed countries → revenue scope error | `ds-conduct`, `ds-clarify`, `data-profile` |
| 2 | **OWID CO₂ data** (`owid/co2-data`) | Climate / energy, multi-country panel | CC BY 4.0 | Per-capita vs absolute, CO₂ vs CO₂-per-GDP, World/region aggregate rows mixed with countries → unit-mismatch + scope traps | `ds-star-plus`, `eda-narrative` |
| 3 | **Synthea synthetic EHR** (synthetichealth) | Healthcare, multi-table | Apache-2.0 | Multi-file joins (patients ↔ encounters ↔ conditions ↔ meds) + safe PII-detection demo (synthetic, no real PHI) | `data-profile`, multi-file `ds-star-plus`, PII guardrail |
| 4 | **UCI Bike Sharing** (UCI id 275) | Urban mobility / transport | CC BY 4.0 | `casual + registered = cnt` → target leakage; hourly time-series → temporal CV | `ds-model` |

## Why these four

- **Distinct domains:** retail, climate, healthcare, transport
- **Distinct failure modes:** scope/dropped-rows, units, joins/PII, leakage/CV — covering four of the six DS failure modes in the verifier rubric
- **No credentialing required:** Synthea is synthetic (no MIMIC sign-up)
- **Clean licensing:** all CC BY 4.0 or Apache-2.0

## Attribution

- Online Retail II: D. Chen, S.L. Sain, K. Guo (2012). CC BY 4.0. [UCI id 502](https://archive.ics.uci.edu/dataset/502)
- OWID CO₂: Our World in Data. CC BY 4.0. [github.com/owid/co2-data](https://github.com/owid/co2-data)
- Synthea: The MITRE Corporation. Apache-2.0. [synthea.mitre.org](https://synthea.mitre.org)
- Bike Sharing: H. Fanaee-T, J. Gama (2013). CC BY 4.0. [UCI id 275](https://archive.ics.uci.edu/dataset/275)
