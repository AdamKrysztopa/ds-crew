---
name: ds-env-setup
description: "Use when setting up or repairing the Python env for analysis — detects uv/venv/conda/poetry/pipenv, installs core packages"
---

# ds-env-setup : prepare your project's Python environment

## When this applies

Use this skill before running any ds-crew analysis for the first time in a project, when an analysis skill fails with `ModuleNotFoundError`, or when you change env managers and need to reinstall. Also triggered automatically by the optional SessionStart hook (see Stage 5).

## The cardinal rule

Never install into a global Python. Every install command targets the **active environment** detected in Stage 2. If no env exists at all, create one with `uv` before installing.

**Target interpreter: Python 3.11 or 3.12.** This is the band with full DS-stack wheel coverage *and* the only one the feasibility gate's `dependence-forecastability` supports (`requires-python >=3.11,<3.13`). Older (3.9/3.10) risks missing wheels; newer (3.13/3.14) silently disables that tool (gate drops to the fallback). On macOS especially, bare `python3` is often Apple's stock **3.9**, so don't just accept the default — see the Stage 2.5 checkpoint.

## How to run it

### Stage 0 — Python check

```bash
python3 --version   # or: python --version
```

If neither command works: **stop here**. Install Python first:
- macOS: `brew install python` or https://www.python.org/downloads/
- Linux: `sudo apt install python3` / `sudo dnf install python3`
- Any platform: https://github.com/pyenv/pyenv

**Note the version** — you'll need it in Stage 2.5. Classify it:
- **In `[3.11, 3.13)`** (3.11 or 3.12) → ideal, no checkpoint needed.
- **Below 3.11** (e.g. macOS stock 3.9) or **3.13+** → off-target; the Stage 2.5 checkpoint applies.

### Stage 1 — Scope check (informational)

Check whether ds-crew is installed globally or per-project:
```bash
grep -l "ds-env-setup" ~/.claude/settings.json 2>/dev/null && echo "global" || echo "not global"
grep -l "ds-env-setup" .claude/settings.json 2>/dev/null && echo "project" || echo "not project"
```
Print the result for the user's awareness. This does not change the env logic.

### Stage 2 — Detect env manager

Run `check_env.py` (from this skill's `scripts/` dir) to detect the manager:

```bash
python3 <skill_scripts_dir>/check_env.py
```

Reads the returned `manager` field. Priority order: `uv` > `venv` > `conda` > `poetry` > `pipenv` > `none`.

### Stage 2.5 — Interpreter version checkpoint

**Skip this stage if** the Stage 0 version is already in `[3.11, 3.13)` **and** a project env already exists (manager ≠ `none`). Otherwise:

**If `uv` is the manager (or manager is `none` and `uv` is on PATH):**
uv can fetch and pin any interpreter without touching the system Python — so don't silently inherit an off-target default. **Ask the user** (a real checkpoint — do not auto-pick):

> Your default Python is **{version from Stage 0}**. ds-crew targets **3.11–3.12** (full DS-stack
> wheels, and the only band the forecastability gate supports). Since this project uses **uv**, I can
> provision any of these without touching your system Python. Which do you want?
>
> - **3.12 — recommended.** Newest supported; broadest wheel coverage.
> - **3.11.** Slightly more conservative.
> - **Keep default ({version}).** Note: <3.11 may miss wheels; ≥3.13 disables `dependence-forecastability` (gate falls back).

Apply the choice before installing (Stage 3):
```bash
uv python install 3.12      # fetches it if not already present (use 3.11 if chosen)
uv venv --python 3.12       # existing-project path; creates .venv on the chosen interpreter
# — or, on the `none` path —
uv init --python 3.12 && uv venv --python 3.12
```
If the user keeps the default, proceed with no `--python` flag.

**If the manager is `venv` / `conda` / `poetry` / `pipenv` and the default is off-target:** these can't fetch interpreters on their own. Don't block — but surface it:
- Check for a better interpreter already installed: `ls /opt/homebrew/bin/python3.1[12] /usr/local/bin/python3.1[12] 2>/dev/null` (or `pyenv versions`).
- If one exists, tell the user they can recreate the env on it (e.g. `python3.12 -m venv .venv`) or switch to `uv`.
- If none exists, note the limitation (forecastability tool may be unavailable / wheel gaps) and continue with what's there.

### Stage 3 — Install core packages

Run the env-specific command:

| Manager | Command |
|---------|---------|
| `uv` | `uv add pandas openpyxl matplotlib` |
| `venv` | `python -m pip install pandas openpyxl matplotlib` |
| `conda` | `conda install -y pandas openpyxl matplotlib` |
| `poetry` | `poetry add pandas openpyxl matplotlib` |
| `pipenv` | `pipenv install pandas openpyxl matplotlib` |
| `none` | See below |

**If `none` detected:** check for `uv` on PATH first:
```bash
which uv || echo "uv not found"
```
- If `uv` present: run the Stage 2.5 checkpoint first, then `uv init --python <chosen> && uv add pandas openpyxl matplotlib` (omit `--python` only if the user kept the default).
- If `uv` absent: stop and print install instructions:
  ```
  Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh
  Then re-run /ds-env-setup
  ```
  Do NOT fall back to a global `pip install`.

### Stage 4 — Verify

```bash
python3 -c "import pandas; import openpyxl; import matplotlib; print('ready')"
```

If this fails, report which package is missing (the error message names it) and suggest re-running Stage 3. Print the Python path being used:
```bash
python3 -c "import sys; print(sys.executable)"
```

### Stage 5 — Offer SessionStart hook (opt-in)

After a successful verify, ask the user:
> "Want me to add a session-start check so you get a warning if the env breaks in future? I'll add a one-liner to `.claude/settings.json`."

If yes, append to `.claude/settings.json` (create the file + `hooks` key if absent):

```json
"SessionStart": [{
  "hooks": [{
    "type": "command",
    "command": "python3 -c 'import pandas,openpyxl,matplotlib' 2>/dev/null || echo '⚠️  ds-crew: core packages missing — run /ds-env-setup'"
  }]
}]
```

Silent on success. One-liner warning on failure. Non-blocking.

## Output

- Confirmation of Python version + path (and, if Stage 2.5 ran, the interpreter the user chose)
- Detected env manager
- Install command run + its output
- `ready` from the verification step
- (Optional) confirmation that the SessionStart hook was added

## Quick reference

```
check_env.py                # print JSON env info for cwd
check_env.py --check        # exit 0 if packages ok, exit 1 + message if not (for hooks)
```

Packages installed: `pandas`, `openpyxl`, `matplotlib`

For kernel mode (`ds-star-plus`): also install `ipykernel jupyter_client` — see `../ds-star-plus/references/execution.md`
