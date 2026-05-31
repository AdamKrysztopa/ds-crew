# Publication-quality plotting guidance (Phase 3)

The solver's code uses whatever plotting library is in the project env — ds-crew
bundles nothing (Principle 1). This guide helps produce clear, defensible charts.

## Library selection (in the solver's code)

```python
# Prefer what's available — check in this order:
try:
    import plotly.express as px          # interactive, great for notebooks
except ImportError:
    try:
        import seaborn as sns            # statistical, matplotlib-based
        import matplotlib.pyplot as plt
    except ImportError:
        import matplotlib.pyplot as plt  # always available if matplotlib is
```

## Chart selection by question type

| Question type | Preferred chart |
|---|---|
| Distribution of one variable | Histogram or KDE |
| Comparison across categories | Bar chart (sorted) |
| Relationship between two numerics | Scatter plot |
| Trend over time | Line chart (time on x-axis) |
| Composition / parts of a whole | Stacked bar or pie (only if ≤5 slices) |
| Correlation matrix | Heatmap |

## Quality checklist

- [ ] **Label axes** — include units (e.g., "Revenue (USD)", "Temperature (°C)")
- [ ] **Title** — states the finding, not just "Chart of X" (e.g., "Revenue peaks in Q4 every year")
- [ ] **No chartjunk** — remove unnecessary gridlines, 3D effects, decorations
- [ ] **Accessible colors** — avoid red/green only; use colorblind-friendly palettes (`viridis`, `tab10`)
- [ ] **Save to run dir** — `plt.savefig(run_dir / "chart_name.png", dpi=150, bbox_inches="tight")`
- [ ] **Reference in report** — include the image path in the Markdown report

## When to produce charts

Produce a chart only when it reveals something the numbers alone don't.
"This number went up" does not need a chart. "Revenue dipped every January" does.
