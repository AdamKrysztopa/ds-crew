# ds-crew config profiles

Profiles bundle skill + model tier + ensemble settings so you can pick a mode
instead of navigating 14 skills individually.

## The three profiles

| profile | front-door skill | model tier | ensemble N | when to use |
|---|---|---|---|---|
| `quick` | `ds-star-plus` | planner: `claude-haiku-4-5`, verifier: `claude-sonnet-4-6` | 1 (no spike) | Fast factoid / aggregation over a clean file; low stakes |
| `exploratory` | `ds-conduct` → `eda-narrative` | `claude-sonnet-4-6` throughout | 1, debate off | New or unknown data; you want a narrative, not just a number |
| `production-audit` | `ds-conduct` → `ds-spike` | `claude-opus-4-8` for verify + reconcile | 3, debate on, cost guardrail on | High-stakes or contested results; you must defend the number |

## Profile details

### `quick`
**Skills invoked (in order):** `ds-star-plus`
**Model:** planner = `claude-haiku-4-5`, verifier = `claude-sonnet-4-6`
**When:** single-table CSV, clear question, low stakes, fast iteration needed
**Not for:** contested results, unknown data shape, predictive tasks

### `exploratory`
**Skills invoked (in order):** `ds-conduct` → `data-profile` → `eda-narrative`
**Model:** `claude-sonnet-4-6` throughout
**When:** first look at a new dataset, stakeholder presentation, discovering patterns
**Not for:** high-stakes decisions, predictive ML

### `production-audit`
**Skills invoked (in order):** `ds-conduct` → `data-profile` → `ds-clarify` → `ds-spike` (N=3, debate on)
**Model:** `claude-opus-4-8` for verifier and reconciler; `claude-sonnet-4-6` for solvers
**Cost guardrail:** on (confirm before spending N× ensemble cost)
**When:** regulated environments, contested numbers, CFO-level reporting, audit trails
**Not for:** quick exploration (use `exploratory` instead)

## How to invoke a profile

Profiles are documentation-level presets — tell ds-conduct which profile you want:

```
/ds-conduct production-audit
```

Or just describe what you need and let ds-conduct route:
```
/ds-conduct   [ds-conduct will ask what you're trying to do and suggest the right profile]
```
