# ds-env-setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `ds-env-setup` skill that detects a project's Python env manager, installs the core ds-crew analysis packages into it, and offers a proactive SessionStart hook.

**Architecture:** stdlib-only `check_env.py` does all detection (pure, testable); `SKILL.md` describes the 5-stage flow Claude follows; an opt-in `SessionStart` hook warns on future env breakage. Follows the repo convention: helper script + sibling test, `python3 -m unittest` runner.

**Tech Stack:** Python stdlib (`os`, `shutil`, `sys`, `subprocess`, `json`, `importlib`); Markdown SKILL.md.

**Spec:** `docs/superpowers/specs/2026-05-31-ds-env-setup-design.md`

---

## Conventions (read once)

- Scripts: stdlib only, module docstring with usage, pure importable functions, `if __name__ == "__main__"` block, sibling `test_*.py`.
- Test runner: `cd skills/ds-env-setup/scripts && python3 -m unittest -v`
- Commits: conventional style + `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `skills/ds-env-setup/scripts/check_env.py` | Create | Detect env manager + `--check` import test |
| `skills/ds-env-setup/scripts/test_check_env.py` | Create | All 6 detection cases + `--check` exit codes |
| `skills/ds-env-setup/SKILL.md` | Create | 5-stage skill flow |
| `README.md` | Modify | Skill table row + command + setup note |

---

## Task 1: `check_env.py` — detection helper + `--check` mode (TDD)

**Files:**
- Create: `skills/ds-env-setup/scripts/check_env.py`
- Create: `skills/ds-env-setup/scripts/test_check_env.py`

- [ ] **Step 1: Create the scripts dir**

```bash
mkdir -p skills/ds-env-setup/scripts
```

- [ ] **Step 2: Write the failing test** — save as `skills/ds-env-setup/scripts/test_check_env.py`:

```python
import os, sys, tempfile, unittest

# detect_env is a pure function — test it without touching the real filesystem
from check_env import detect_env, check_imports

class TestDetectEnv(unittest.TestCase):

    def _make(self, files=(), env=None):
        """Create a temp dir with the given filenames present."""
        d = tempfile.mkdtemp()
        for f in files:
            if f.endswith("/"):
                os.makedirs(os.path.join(d, f.rstrip("/")), exist_ok=True)
            else:
                open(os.path.join(d, f), "w").close()
        return d, (env or {})

    def test_uv_lock_wins(self):
        d, e = self._make(["uv.lock", "poetry.lock"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "uv")

    def test_pyproject_plus_uv_on_path(self):
        import shutil
        d, e = self._make(["pyproject.toml"])
        if shutil.which("uv"):          # only run where uv is installed
            result = detect_env(d, e)
            self.assertEqual(result["manager"], "uv")

    def test_venv_dir_detected(self):
        d, e = self._make([".venv/"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "venv")

    def test_venv_dir_alt_name(self):
        d, e = self._make(["venv/"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "venv")

    def test_conda_env_yml(self):
        d, e = self._make(["environment.yml"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "conda")

    def test_conda_prefix_env_var(self):
        d, e = self._make([], env={"CONDA_PREFIX": "/opt/conda/envs/myenv"})
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "conda")

    def test_poetry_lock(self):
        d, e = self._make(["poetry.lock"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "poetry")

    def test_pipfile(self):
        d, e = self._make(["Pipfile"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "pipenv")

    def test_none_detected(self):
        d, e = self._make([])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "none")

    def test_result_has_required_keys(self):
        d, e = self._make([])
        result = detect_env(d, e)
        for key in ("manager", "python_path", "project_root", "active_venv"):
            self.assertIn(key, result)

    def test_uv_beats_venv(self):
        """Priority: uv > venv."""
        d, e = self._make(["uv.lock", ".venv/"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "uv")

    def test_venv_beats_conda(self):
        """Priority: venv > conda."""
        d, e = self._make([".venv/", "environment.yml"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "venv")

class TestCheckImports(unittest.TestCase):
    def test_returns_bool(self):
        result = check_imports()
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify it fails**

```bash
cd skills/ds-env-setup/scripts && python3 -m unittest test_check_env -v 2>&1 | head -5
```

Expected: `ModuleNotFoundError: No module named 'check_env'`

- [ ] **Step 4: Write `check_env.py`** — save as `skills/ds-env-setup/scripts/check_env.py`:

```python
#!/usr/bin/env python3
"""Detect the Python env manager used in a project directory (Track ds-env-setup).

    from check_env import detect_env, check_imports
    result = detect_env(".", os.environ)   # -> {manager, python_path, project_root, active_venv}
    ok = check_imports()                   # -> True if pandas+openpyxl+matplotlib importable

CLI:
    python3 check_env.py              # print JSON detection result for cwd
    python3 check_env.py --check      # exit 0 if imports ok, exit 1 + message if not
"""
import importlib.util, json, os, shutil, sys


def detect_env(cwd, environ):
    """Return env manager info for the given directory.

    Priority: uv > venv > conda > poetry > pipenv > none.
    Pure function — no side effects, no filesystem writes.
    """
    has = lambda f: os.path.exists(os.path.join(cwd, f))
    has_dir = lambda d: os.path.isdir(os.path.join(cwd, d))

    if has("uv.lock") or (has("pyproject.toml") and shutil.which("uv")):
        manager = "uv"
    elif has_dir(".venv") or has_dir("venv"):
        manager = "venv"
    elif has("environment.yml") or environ.get("CONDA_PREFIX"):
        manager = "conda"
    elif has("poetry.lock"):
        manager = "poetry"
    elif has("Pipfile"):
        manager = "pipenv"
    else:
        manager = "none"

    venv_path = (
        os.path.join(cwd, ".venv") if has_dir(".venv")
        else os.path.join(cwd, "venv") if has_dir("venv")
        else environ.get("VIRTUAL_ENV", "")
    )

    return {
        "manager": manager,
        "python_path": sys.executable,
        "project_root": cwd,
        "active_venv": venv_path,
    }


def check_imports():
    """Return True if pandas, openpyxl, and matplotlib are all importable."""
    packages = ("pandas", "openpyxl", "matplotlib")
    return all(importlib.util.find_spec(p) is not None for p in packages)


if __name__ == "__main__":
    if "--check" in sys.argv:
        if check_imports():
            sys.exit(0)
        missing = [
            p for p in ("pandas", "openpyxl", "matplotlib")
            if importlib.util.find_spec(p) is None
        ]
        print(f"ds-crew: missing packages: {', '.join(missing)} — run /ds-env-setup")
        sys.exit(1)
    else:
        print(json.dumps(detect_env(os.getcwd(), dict(os.environ)), indent=2))
```

- [ ] **Step 5: Run tests — all must pass**

```bash
cd skills/ds-env-setup/scripts && python3 -m unittest -v
```

Expected: 12–13 tests, all OK (the `test_pyproject_plus_uv_on_path` test is conditional on `uv` being installed — passes or is effectively skipped if uv absent).

- [ ] **Step 6: Commit**

```bash
git add skills/ds-env-setup/scripts/check_env.py skills/ds-env-setup/scripts/test_check_env.py
git commit -m "$(cat <<'EOF'
feat(ds-env-setup): env detection helper + --check mode (TDD)

detect_env() covers uv/venv/conda/poetry/pipenv/none in priority order.
check_imports() tests pandas+openpyxl+matplotlib importability.
CLI: no-arg prints JSON; --check exits 0/1 for SessionStart hook use.
12 unit tests, stdlib only.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `ds-env-setup/SKILL.md`

**Files:**
- Create: `skills/ds-env-setup/SKILL.md`

- [ ] **Step 1: Write `SKILL.md`** — exact content:

```markdown
---
name: ds-env-setup
description: "Set up or repair the Python environment for ds-crew analysis skills. Use this skill WHENEVER the user wants to prepare their project's Python environment ('set up env', 'install dependencies', 'prepare environment', 'I can’t run the analysis', 'missing pandas', 'env setup'), or when an analysis skill fails with an ImportError. Checks Python availability (stops if absent), detects the project's env manager (uv/venv/conda/poetry/pipenv), installs pandas + openpyxl + matplotlib into that env, and offers a SessionStart hook for proactive future warnings. Do NOT use to install ds-crew itself — see the README Installation section for that."
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

If this fails, report which package is missing (the error message names it) and suggest re-running Stage 3. Print the Python path being used: `import sys; print(sys.executable)`.

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
```

- [ ] **Step 2: Commit**

```bash
git add skills/ds-env-setup/SKILL.md
git commit -m "$(cat <<'EOF'
feat(ds-env-setup): 5-stage env setup skill (track ds-env-setup)

Checks Python, detects uv/venv/conda/poetry/pipenv/none, installs
pandas+openpyxl+matplotlib, verifies imports, offers SessionStart hook.
Stops hard if Python absent or if no env manager and uv also absent.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: README.md update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read README.md** to find the exact skill count, skill table, command list, and opening section.

- [ ] **Step 2: Make three targeted edits:**

**Edit A** — Update skill count in the header from "Thirteen installable Claude Code skills" → "Fourteen installable Claude Code skills".

**Edit B** — Add one row to the skill table (after the `ds-memory` row):

```markdown
| **`ds-env-setup`** | Set up / verify the Python env — detects uv/venv/conda/poetry/pipenv, installs core packages, offers a SessionStart hook | Before first analysis; after changing env; ImportError during a run |
```

**Edit C** — Add `/ds-env-setup` to the `/`-command list.

**Edit D** — Add a "Before your first analysis" callout near the top of the README, just before or after the Installation section:

```markdown
> **First time?** Run `/ds-env-setup` to verify your project's Python environment has the packages the analysis skills need.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): add ds-env-setup to skill table and command list

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Push

- [ ] **Step 1: Verify all tests still pass**

```bash
for d in skills/ds-star-plus/scripts skills/ds-spike/scripts skills/ds-memory/scripts skills/ds-model/scripts skills/ds-env-setup/scripts; do
  echo "=== $d ===" && (cd "$d" && python3 -m unittest -v 2>&1 | tail -3)
done
```

Expected: all suites OK.

- [ ] **Step 2: Push the branch**

```bash
git push -u origin sota-agentic-ds-patterns
```

Expected: branch pushed to remote, tracking set.

---

## Self-review

- **Spec coverage:** Stage 0 (Python check) → Task 2 Step 1 Stage 0; Stage 1 (scope check) → Task 2 Stage 1; Stage 2 (detection) → Task 1 + Task 2 Stage 2; Stage 3 (install) → Task 2 Stage 3 (all 6 managers + uv-absent stop); Stage 4 (verify) → Task 2 Stage 4; Stage 5 (hook) → Task 2 Stage 5; README → Task 3. All spec sections covered.
- **Placeholder scan:** None. All code blocks complete, all commands exact.
- **Type consistency:** `detect_env(cwd: str, environ: dict) -> dict` and `check_imports() -> bool` used consistently in tests and implementation. `manager` key used in both test assertions and SKILL.md stage 2.
