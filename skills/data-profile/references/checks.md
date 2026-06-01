# Data-quality checks and report structure

The checklist `data-profile` runs per file, and the shape of the report it emits. Each check names
the downstream failure it prevents (cross-referenced to the `ds-star-plus` rubric where relevant).

## Per-column checks

| check | what to compute | catches |
|-------|-----------------|---------|
| dtype & mixed types | inferred dtype; flag columns with mixed types or numbers-stored-as-text | wrong_column_or_value, parse crashes |
| missingness | null count + %; **suspected sentinels** (`-`, `?`, `NEW`, ``, `0`, `9999`, `N/A`) | dropped_rows, units_mismatch |
| cardinality | n unique; flag **constant** (1 value) and **candidate key** (unique & non-null) | bad joins, fan-out |
| value distribution | for numeric: min/max/mean/median/std; for object (low-card): value counts | scope_error, outliers |
| outliers | IQR rule (outside 1.5×IQR) or |z| > 3; count + a few examples | scope_error |
| whitespace/casing | leading/trailing spaces, inconsistent casing in categorical values | wrong_column_or_value |

## Per-file checks

- shape (rows × cols); for Excel/SQLite list ALL sheets/tables, not just the first;
- duplicate full rows: count + the minimal key that dedups;
- encoding: declared vs detected; any decode errors.

## Cross-file checks (folder mode)

- **Join compatibility** for same-named/role columns: dtype agreement, value overlap %,
  one-to-one vs one-to-many (fan-out), and rows that would be dropped by an inner join.
- **Grain check**: does each file represent the entity it seems to (one row per order? per line
  item? per day?) — mismatched grain is the classic multi-file bug.

## Report structure

```
# Data profile — <folder or file>

## Inventory
<files, sizes, types>

## <file> — <rows × cols>
- columns: <name (dtype, %null, n_unique) ...>
- candidate keys: <...>   constant columns: <...>
- sentinels / hidden nulls: <...>
- duplicates: <n> (dedup on <key>)
- numeric summary: <table>   outliers: <flags>

## Cross-file
- <fileA.col> ↔ <fileB.col>: dtype <ok/mismatch>, overlap <%>, join <1:1 / 1:N / drops N rows>

## Watch-outs (read before analyzing)
- <specific issue that would bite an analysis>
```

Keep the watch-outs concrete and actionable — they are the part a human (or `ds-clarify`) will use.
