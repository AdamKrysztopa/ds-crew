#!/usr/bin/env python3
"""Persistent IPython-kernel execution for ds-star-plus (Track F, CodeAct 2402.01030).

Opt-in and environment-aware: the kernel runs under THIS interpreter (sys.executable),
so it inherits whatever venv / uv / conda env launched it. Script mode is the default
and needs nothing. See references/execution.md for install guidance per env manager.
    from kernel_runner import KernelSession, check_kernel_available
    ok, hint = check_kernel_available()
    if ok:
        with KernelSession() as k:
            k.run("import pandas as pd; df = pd.read_csv('a.csv')")
            out = k.run("print(len(df))")
"""
import importlib.util, os, shutil, sys

def collect_output(messages):
    stdout, result, error = [], None, None
    for m in messages:
        t, c = m.get("msg_type"), m.get("content", {})
        if t == "stream":
            stdout.append(c.get("text", ""))
        elif t in ("execute_result", "display_data"):
            result = c.get("data", {}).get("text/plain", result)
        elif t == "error":
            error = {"ename": c.get("ename"), "evalue": c.get("evalue"),
                     "traceback": c.get("traceback", [])}
    return {"stdout": "".join(stdout), "result": result, "error": error}

def should_reset(recent_cells, cells_run, max_cells=30):
    """Heuristic: reset a long-lived kernel to bound state drift / leaked memory."""
    return cells_run >= max_cells

def kernel_install_hint(cwd=None, env=None):
    """Env-appropriate install command targeting the ACTIVE interpreter. Never global pip."""
    cwd = cwd if cwd is not None else os.getcwd()
    env = env if env is not None else os.environ
    pkgs = "ipykernel jupyter_client"
    has = lambda f: os.path.exists(os.path.join(cwd, f))
    if shutil.which("uv") and (has("uv.lock") or has("pyproject.toml")):
        return f"uv pip install {pkgs}   # or: uv add {pkgs}"
    if has("poetry.lock"):
        return f"poetry add {pkgs}"
    if env.get("CONDA_PREFIX") and not env.get("VIRTUAL_ENV"):
        return f"conda install -y {pkgs}"
    if env.get("VIRTUAL_ENV"):
        return f"python -m pip install {pkgs}"
    return f'"{sys.executable}" -m pip install {pkgs}'

def check_kernel_available():
    ok = all(importlib.util.find_spec(m) for m in ("jupyter_client", "ipykernel"))
    return ok, "" if ok else kernel_install_hint()

class KernelSession:
    def __init__(self):
        from jupyter_client.manager import KernelManager
        km = KernelManager()
        km.kernel_cmd = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
        km.start_kernel()
        kc = km.client(); kc.start_channels(); kc.wait_for_ready(timeout=60)
        self._km, self._kc, self.cells_run = km, kc, 0
    def run(self, code, timeout=30):
        self._kc.execute(code)
        msgs = []
        while True:
            msg = self._kc.get_iopub_msg(timeout=timeout)
            msgs.append({"msg_type": msg["msg_type"], "content": msg["content"]})
            if msg["msg_type"] == "status" and msg["content"].get("execution_state") == "idle":
                break
        self.cells_run += 1
        return collect_output(msgs)
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self._kc.stop_channels(); self._km.shutdown_kernel(now=True)
