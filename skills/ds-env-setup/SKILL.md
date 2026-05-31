---
name: ds-env-setup
description: "Set up or repair the Python environment for ds-crew analysis skills. Use this skill WHENEVER the user wants to prepare their project's Python environment ('set up env', 'install dependencies', 'prepare environment', 'I can\\'t run the analysis', 'missing pandas', 'env setup'), or when an analysis skill fails with an ImportError. Checks Python availability (stops if absent), detects the project's env manager (uv/venv/conda/poetry/pipenv), installs pandas + openpyxl + matplotlib into that env, and offers a SessionStart hook for proactive future warnings. Do NOT use to install ds-crew itself — see the README Installation section for that."
---

# ds-env-setup : prepare your project's Python environment

## When this applies

Use this skill before running any ds-crew analysis for the first time in a project, when an analysis skill fails with `ModuleNotFoundError`, or when you change env managers and need to reinstall. Also triggered automatically by the optional SessionStart hook (see Stage 5).

## The cardinal rule

Never install into a global Python. Every install command targets the **active environment** detected in Stage 2. If no env exists at all, create one with `uv` before installing.

## How to run it

### Stage 0 — Python check

```bash
python3 --version   # or: python --version
```

If neither command works: **stop here**. Install Python first:
- macOS: `brew install python` or https://www.python.org/downloads/
- Linux: `sudo apt install python3` / `sudo dnf install python3`
- Any platform: https://github.com/pyenv/pyenv

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
- If `uv` present: `uv init && uv add pandas openpyxl matplotlib`
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

- Confirmation of Python version + path
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
