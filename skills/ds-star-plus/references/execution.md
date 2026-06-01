# Execution modes: script vs kernel

## Two modes

### Script mode (default)

Each step writes a complete Python script and re-runs it from scratch. The script imports
everything it needs, loads data, does its work, and prints results. Paper-faithful, fully
reproducible, zero extra dependencies. Always works — no kernel to manage, no state to
corrupt. Use this unless you have a specific reason to switch.

### Kernel mode (opt-in)

A persistent IPython kernel runs cells incrementally; state (DataFrames, variables, fitted
models) persists across steps. Only the new cell is sent and executed each round — earlier
outputs are already in memory. Cheaper re-runs on long tasks because large file loads happen
once. Requires `ipykernel` + `jupyter_client`.

---

## When to use the kernel

Use kernel mode for: long multi-step exploratory tasks where intermediate DataFrames are
expensive to reload each round (large CSVs, slow DB queries, heavy feature engineering that
feeds multiple later steps).

Do **NOT** use kernel mode when:

- Reproducibility or auditability is paramount (e.g., final production runs, audit trails).
- The task is short enough that re-running from scratch is cheap.
- You need a clean slate between experiments.

---

## State hygiene

Long kernel sessions accumulate stale variables and shadow definitions. To detect and recover:

- Call `should_reset(recent_cells, cells_run)` from `scripts/kernel_runner.py` to detect long
  sessions. It returns `True` when the session has grown risky (many cells, large state).
- On reset: restart the kernel and re-run all accumulated imports before continuing. The
  kernel runner handles this automatically when the flag fires.
- Import statements at the top of each cell (idempotent) make resets safe — re-running them
  does not change state, so you never have to remember what was imported.

---

## Mandatory clean re-run before FINALIZE

Before calling FINALIZE, re-execute the full accumulated script **once in a fresh process
(script mode)** to guarantee the final answer is reproducible. Paste all cells into a single
script, run it with no existing kernel, and verify the output matches. This closes the
stateful-execution reproducibility risk: a kernel session may rely on variables set in a
cell that was since overwritten, so the final answer can be un-reproducible even if it looked
correct in the kernel.

---

## Install — environment-aware

The kernel runs under `sys.executable` (the active interpreter), so `ipykernel` and
`jupyter_client` must be installed into **that** environment. Never use a bare global `pip`
(it may install into a different Python than the one running your code).

Get the correct install command at runtime:

```python
from kernel_runner import check_kernel_available
ok, hint = check_kernel_available()  # hint is env-detected, always targets active interpreter
if not ok:
    print(f"Install with: {hint}")
```

`check_kernel_available` inspects the environment and returns the right command:

| Environment | Install command |
|---|---|
| uv (`uv.lock` or `pyproject.toml` + `uv` on PATH) | `uv pip install ipykernel jupyter_client` |
| active venv (`$VIRTUAL_ENV` set) | `python -m pip install ipykernel jupyter_client` |
| poetry (`poetry.lock` present) | `poetry add ipykernel jupyter_client` |
| conda (`$CONDA_PREFIX` set, no venv) | `conda install -y ipykernel jupyter_client` |
| plain/unknown | `"<sys.executable>" -m pip install ipykernel jupyter_client` |

Always invoke scripts through the project runner (`uv run python script.py` under uv, or
with the activated venv) so `sys.executable` resolves correctly to the environment where
your packages live.

---

## Large inputs — recommend, don't depend

When a file is large (rule of thumb: > 1 GB or > available RAM), ds-star-plus *recommends
in its planning prompt* that the solver's code use a memory-efficient tool — **if that
tool is available in the project env**. ds-crew installs nothing.

Recommendations by situation:

| Situation | Recommended tool (if available) |
|---|---|
| Large CSV/Parquet, SQL-style aggregation | DuckDB (`import duckdb`) — columnar, in-process, no server |
| Wide DataFrames, slow pandas ops | Polars (`import polars as pl`) — lazy evaluation, streaming |
| Chunked iteration | pandas `chunksize=` parameter — always available |

**How to surface this in the plan:** "The input file is large. If `duckdb` is importable,
use it for the join/aggregation — it handles out-of-core data and is much faster than
pandas for this operation."

**The line:** tools the solver's code invokes = fine; anything ds-crew itself must install
to function = out (Principle 1).
