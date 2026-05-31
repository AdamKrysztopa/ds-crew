#!/usr/bin/env python3
"""Detect the Python env manager used in a project directory (ds-env-setup skill).

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
