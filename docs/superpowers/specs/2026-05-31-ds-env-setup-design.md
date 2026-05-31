# Design — `ds-env-setup` skill

**Date:** 2026-05-31
**Status:** design approved, pending implementation plan
**Branch:** sota-agentic-ds-patterns

---

## Purpose

A skill that prepares a user's project Python environment to run ds-crew analysis
scripts. Triggered manually (`/ds-env-setup`) or recommended when an analysis
fails due to missing packages. An optional `SessionStart` hook provides proactive
warnings at the start of each session.

---

## Files

```
skills/ds-env-setup/
  SKILL.md                  ← skill (5-stage flow)
  scripts/
    check_env.py            ← detection + --check mode (stdlib only)
    test_check_env.py       ← tests for all 6 detection cases + --check mode
```

Plus: `README.md` updated (skill table + `/`-command list + setup note in
"Getting started").

---

## Skill flow (5 stages)

### Stage 0 — Python check
Run `python3 --version` (fallback `python --version`).
**Hard stop** if neither is on PATH: print instructions pointing to python.org,
pyenv, Homebrew. Nothing else runs.

### Stage 1 — Scope check (informational)
Check whether ds-crew is installed globally (`~/.claude/settings.json`) or
per-project (`.claude/settings.json`). Print for the user's awareness only —
does not change the env logic.

### Stage 2 — Env detection (via `check_env.py`)
`check_env.py` checks in priority order and returns a structured dict:

| Priority | Detected when | Manager |
|---|---|---|
| 1 | `uv.lock` present, OR (`pyproject.toml` + `uv` on PATH) | `uv` |
| 2 | `.venv/` or `venv/` directory present | `venv` |
| 3 | `environment.yml` present, OR `$CONDA_PREFIX` set | `conda` |
| 4 | `poetry.lock` present | `poetry` |
| 5 | `Pipfile` present | `pipenv` |
| 6 | None of the above | `none` |

Returns: `{manager, python_path, project_root, active_venv}`.

### Stage 3 — Install core packages
Packages: `pandas openpyxl matplotlib`

| Manager | Command |
|---|---|
| `uv` | `uv add pandas openpyxl matplotlib` |
| `venv` | `python -m pip install pandas openpyxl matplotlib` |
| `conda` | `conda install -y pandas openpyxl matplotlib` |
| `poetry` | `poetry add pandas openpyxl matplotlib` |
| `pipenv` | `pipenv install pandas openpyxl matplotlib` |
| `none` | `uv init` → add deps to `pyproject.toml` → `uv sync` |

For the `none` case: requires `uv` on PATH. If `uv` is also absent, print
install instructions (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and
stop — do not fall back to a global `pip install` (that would install into the
wrong interpreter).

### Stage 4 — Verify
Run `python -c "import pandas; import openpyxl; import matplotlib; print('ready')"` in
the correct interpreter context (active venv / `uv run python` / etc.).
Print the resolved Python path. If the import fails, report which package is
missing and suggest re-running Stage 3.

### Stage 5 — Offer SessionStart hook (opt-in)
After a successful verify, ask:
> "Want me to add a session-start check so you get a warning if the env breaks
> in future?"

If yes, append to the project's `.claude/settings.json` (creating it if absent):

```json
"SessionStart": [{
  "hooks": [{
    "type": "command",
    "command": "python3 -c 'import pandas,openpyxl,matplotlib' 2>/dev/null || echo '⚠️  ds-crew: core packages missing — run /ds-env-setup'"
  }]
}]
```

Silent on success (no noise every session). One-liner warning on failure.
Non-blocking.

---

## `check_env.py` contract

```
check_env.py                  → prints JSON detection result
check_env.py --check          → exit 0 if pandas+openpyxl+matplotlib importable,
                                 exit 1 + one-line message if not
```

Pure functions `detect_env(cwd, environ) -> dict` and `check_imports() -> bool`.
Stdlib only. Sibling `test_check_env.py` covers all 6 detection cases and both
modes.

---

## SKILL.md description (trigger surface)

```
"Set up or repair the Python environment for ds-crew analysis skills. Use this
skill WHENEVER the user wants to prepare their project's Python environment
('set up env', 'install dependencies', 'prepare environment', 'I can't run the
analysis', 'missing pandas', 'env setup'), or when an analysis skill fails with
an ImportError. Checks Python availability (stops if absent), detects the
project's env manager (uv/venv/conda/poetry/pipenv), installs pandas +
openpyxl + matplotlib into that env, and offers a SessionStart hook for
proactive future warnings. Do NOT use to install ds-crew itself — see the
README Installation section for that."
```

---

## README update

- Add `ds-env-setup` row to the skill table: "Set up / verify the Python env
  for analysis" | "Before first analysis; after changing env; ImportError during
  a run" | `$`
- Add `/ds-env-setup` to the `/`-command list
- Add a "Before your first analysis" note near the top pointing at `/ds-env-setup`

---

## Out of scope

- Installing ds-crew itself (covered in README Installation section)
- Setting up `jupyter_client`/`ipykernel` for kernel mode (covered in
  `ds-star-plus/references/execution.md`)
- Windows path handling (noted as a known limitation; the skill targets
  macOS/Linux)
