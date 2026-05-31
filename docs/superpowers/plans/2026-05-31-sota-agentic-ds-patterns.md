# SOTA Agentic-DS Patterns (v1.2, Tracks E–M) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the ds-crew suite from six skills to the full SOTA agentic-data-science surface — adding cross-session memory, stateful execution, DAG planning, an AutoML modeling skill, multi-agent debate, a sandbox/provenance layer, a data-aware orchestrator, standalone primitive skills, and a usage guide — each grounded in a paper and reflected in the docs/manifests.

**Architecture:** Hybrid delivery (per the design spec): engine upgrades land inside `ds-star-plus`; net-new single-purpose skills are added as their own `skills/<name>/` dirs; one mode is added to `ds-spike`; one cross-cutting reference is shared. Build in dependency order `0 → J → F → G → E → H → I → L → K → M`. Each phase is independently shippable and ends with its own docs delta; Phase M does the holistic sync + version bump.

**Tech Stack:** Markdown SKILL.md + `references/*.md` (progressive disclosure); stdlib-only Python helper scripts with sibling `test_*.py` run via `python3 -m unittest`; `jupyter_client`/`ipykernel` added only for the optional kernel runner; plugin manifests in `.claude-plugin/`.

**Source spec:** `docs/superpowers/specs/2026-05-31-sota-agentic-ds-patterns-design.md`

---

## Conventions every task follows (read once)

These match the existing repo and are NOT repeated per task:

1. **Skill dir layout:** `skills/<name>/SKILL.md` (+ `references/*.md`, `scripts/*.py`, `evals/evals.json` as needed).
2. **SKILL.md shape:** YAML frontmatter (`name`, `description` — the `description` is the trigger surface: pack it with *when to use / when NOT to use* phrases like the existing skills), then `# <name> : <tagline>`, `## When this applies`, `## The cardinal rule`, `## How to run it` (staged), `## Output`, `## Quick reference`.
3. **Helper scripts:** stdlib-only unless a task says otherwise; module docstring with a usage example; pure, importable functions; a `if __name__ == "__main__"` demo; a sibling `test_<name>.py` using `unittest`.
4. **Run tests:** `cd skills/<name>/scripts && python3 -m unittest -v`.
5. **Grounding:** any paper claim cites the arXiv id; new ids must pass Phase 0 verification before being written into `papers/README.md` or a skill's `evidence.md`.
6. **Commits:** one per task (or per coherent task group), conventional-commit style, ending with the repo's `Co-Authored-By` trailer.
7. **Model ids:** reuse the tiers in `skills/ds-star-plus/scripts/route_model.py` (`claude-haiku-4-5` / `claude-sonnet-4-6` / `claude-opus-4-8`).

---

## Phase 0 — Citation verification + bibliography

**Why first:** every later phase cites these; the repo never ships an unverified reference.

### Task 0.1: Verify each new arXiv id

**Files:** none (research task; output recorded in 0.2)

- [ ] **Step 1:** For each id below, fetch the abstract page and confirm the **title + first author** match the claimed paper. Use WebFetch on `https://arxiv.org/abs/<id>` (or `ctx_fetch_and_index`).

| id | claimed paper |
|----|----------------|
| 2409.07429 | Agent Workflow Memory (AWM) |
| 2305.16291 | Voyager |
| 2308.10144 | ExpeL: LLM Agents Are Experiential Learners |
| 2402.01030 | CodeAct — Executable Code Actions Elicit Better LLM Agents |
| 2402.18679 | Data Interpreter (MetaGPT) |
| 2502.13138 | AIDE — AI-Driven Exploration in the space of code |
| 2410.20424 | AutoKaggle |
| 2410.02958 | AutoML-Agent |
| 2305.14325 | Improving Factuality and Reasoning via Multiagent Debate (Du et al.) |
| 2308.00352 | MetaGPT |
| 2203.11171 | Self-Consistency Improves CoT Reasoning (Wang et al.) |

- [ ] **Step 2:** Record the result in a scratch list: `id → CONFIRMED <title>` or `id → MISMATCH, corrected to <id>` or `id → DROP`. Any id that cannot be confirmed is corrected or its citation is dropped (find the right id by `WebSearch`).

- [ ] **Step 3:** No commit (feeds 0.2).

### Task 0.2: Add the v1.2 bibliography block to `papers/README.md`

**Files:** Modify `papers/README.md`

- [ ] **Step 1:** Append a new section `## Patterns added in v1.2 (tracks E–M)` with one table row per **confirmed** id, in the existing table format (`| Paper | arXiv | What we take from it |`), mapping each to its track (E/F/G/H/I/J/K/L).
- [ ] **Step 2:** Append the confirmed ids to the re-fetch `curl` heredoc at the top (same `name id` line format as the existing entries).
- [ ] **Step 3:** Commit: `docs(papers): add v1.2 bibliography (tracks E–M), verified ids`.

---

## Phase J — Sandbox + provenance (cross-cutting)

**Grounding:** DA-Code (2410.07331), DABstep (2506.23719), CodeAct (2402.01030).

### Task J.1: Provenance emitter `run_manifest.py` (test-first)

**Files:**
- Create: `skills/ds-star-plus/scripts/run_manifest.py`
- Test: `skills/ds-star-plus/scripts/test_run_manifest.py`

- [ ] **Step 1: Write the failing test.**

```python
import json, os, tempfile, unittest
from run_manifest import build_manifest, write_manifest

class TestRunManifest(unittest.TestCase):
    def test_build_manifest_hashes_code_and_lists_inputs(self):
        m = build_manifest(
            question="q1", code="print(1)",
            inputs=["a.csv", "b.json"], answer="42",
            verdict={"score": 4}, model="claude-sonnet-4-6",
        )
        self.assertEqual(m["question"], "q1")
        self.assertEqual(sorted(m["inputs"]), ["a.csv", "b.json"])
        self.assertEqual(len(m["code_sha256"]), 64)          # hex digest
        self.assertEqual(m["answer"], "42")
        self.assertIn("created_utc", m)
    def test_same_code_same_hash(self):
        a = build_manifest("q", "x=1", [], None, {}, "m")
        b = build_manifest("q", "x=1", [], None, {}, "m")
        self.assertEqual(a["code_sha256"], b["code_sha256"])
    def test_write_manifest_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            p = write_manifest(build_manifest("q","c",[],"1",{},"m"), d)
            self.assertTrue(os.path.exists(p))
            self.assertEqual(json.load(open(p))["question"], "q")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails.** `cd skills/ds-star-plus/scripts && python3 -m unittest test_run_manifest -v` → FAIL (no module).

- [ ] **Step 3: Implement `run_manifest.py`** (stdlib only: `hashlib`, `json`, `os`, `datetime`):

```python
#!/usr/bin/env python3
"""Emit a reproducibility manifest for one solver run (Track J).

    from run_manifest import build_manifest, write_manifest
    m = build_manifest(question, code, inputs, answer, verdict, model)
    write_manifest(m, run_dir)          # -> <run_dir>/run_manifest.json
"""
import hashlib, json, os
from datetime import datetime, timezone

def build_manifest(question, code, inputs, answer, verdict, model):
    return {
        "question": question,
        "inputs": list(inputs),
        "code_sha256": hashlib.sha256((code or "").encode("utf-8")).hexdigest(),
        "answer": answer,
        "verdict": verdict,
        "model": model,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }

def write_manifest(manifest, run_dir):
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "run_manifest.json")
    with open(path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return path

if __name__ == "__main__":
    print(build_manifest("demo", "print(1)", ["a.csv"], "1", {"score": 4}, "claude-sonnet-4-6"))
```

- [ ] **Step 4: Run tests.** Same command → PASS (3 tests).
- [ ] **Step 5: Commit.** `git add skills/ds-star-plus/scripts/run_manifest.py skills/ds-star-plus/scripts/test_run_manifest.py && git commit` → `feat(ds-star-plus): run-manifest provenance emitter (track J)`.

### Task J.2: Shared `references/sandbox.md`

**Files:** Create `skills/ds-star-plus/references/sandbox.md`

- [ ] **Step 1:** Write the reference. Required sections: **Resource policy** (wall-clock timeout per cell, memory ceiling, no-network default for solver code), **Working directory discipline** (each run in its own temp dir; never write outside it; read inputs read-only), **Provenance** (call `run_manifest.write_manifest` at FINALIZE; point to `scripts/run_manifest.py`), **What to surface to the user** (manifest path + code hash). Acceptance: the doc names the timeout knob, the temp-dir rule, and links the emitter.
- [ ] **Step 2:** Add a one-line pointer from `skills/ds-star-plus/SKILL.md` EXECUTE stage: "Execution policy + provenance: see `references/sandbox.md`."
- [ ] **Step 3:** Commit: `docs(ds-star-plus): shared sandbox/provenance reference (track J)`.

### Task J.3: Cross-link sandbox from the other solvers

**Files:** Modify `skills/ds-star/SKILL.md`, `skills/ds-spike/SKILL.md`

- [ ] **Step 1:** Add the same one-line pointer to `../ds-star-plus/references/sandbox.md` in each skill's execution stage (DRY — single source).
- [ ] **Step 2:** Commit: `docs: cross-link sandbox reference from ds-star and ds-spike (track J)`.

---

## Phase F — Stateful kernel execution (`ds-star-plus` upgrade)

**Grounding:** CodeAct (2402.01030).

### Task F.1: Environment-aware dependency policy (no global pip assumption)

**The problem this avoids:** the kernel deps must live in **the same interpreter that runs the analysis** — which may be a `venv`, a `uv`-managed env, `poetry`, or `conda`, not a global Python. A bare `pip install` can install into the wrong interpreter, and Jupyter's default kernelspec may launch a *different* Python than the one with the user's `pandas`. Two rules follow, implemented in F.2/F.3:

1. **The kernel always launches under `sys.executable`** (the active interpreter), not a registered kernelspec — so it inherits the venv/uv/conda env automatically.
2. **Install guidance is env-detected**, and always targets the active env:

| Detected env | Install command |
|---|---|
| `uv` (`uv.lock`/`pyproject.toml` + `uv` on PATH) | `uv pip install ipykernel jupyter_client` (or `uv add …` to persist as a dep) |
| active `venv` (`$VIRTUAL_ENV` set) | `python -m pip install ipykernel jupyter_client` |
| `poetry` (`poetry.lock`) | `poetry add ipykernel jupyter_client` |
| `conda` (`$CONDA_PREFIX`, no venv) | `conda install -y ipykernel jupyter_client` |
| plain / unknown | `"{sys.executable}" -m pip install ipykernel jupyter_client` |

- [ ] **Step 1:** No code here — this policy is realized by `check_kernel_available()` / `kernel_install_hint()` (F.2) and documented in `execution.md` (F.3).
- [ ] **Step 2:** No standalone commit (folded into F.2/F.3).

### Task F.2: `kernel_runner.py` — pure helpers test-first, live kernel guarded

**Files:**
- Create: `skills/ds-star-plus/scripts/kernel_runner.py`
- Test: `skills/ds-star-plus/scripts/test_kernel_runner.py`

- [ ] **Step 1: Write the failing test** (unit-tests the pure helpers with fixture messages; the live-kernel test self-skips if `ipykernel` is absent):

```python
import importlib.util, sys, unittest
from kernel_runner import (collect_output, should_reset,
                           check_kernel_available, kernel_install_hint, KernelSession)

def _has_kernel():
    return all(importlib.util.find_spec(m) for m in ("jupyter_client", "ipykernel"))

class TestPureHelpers(unittest.TestCase):
    def test_collect_output_joins_stream_and_result(self):
        msgs = [
            {"msg_type": "stream", "content": {"text": "hello\n"}},
            {"msg_type": "execute_result", "content": {"data": {"text/plain": "42"}}},
        ]
        out = collect_output(msgs)
        self.assertEqual(out["stdout"], "hello\n")
        self.assertEqual(out["result"], "42")
        self.assertIsNone(out["error"])
    def test_collect_output_captures_error(self):
        msgs = [{"msg_type": "error", "content": {"ename": "ValueError", "evalue": "bad", "traceback": ["t"]}}]
        out = collect_output(msgs)
        self.assertEqual(out["error"]["ename"], "ValueError")
    def test_should_reset_on_long_session(self):
        self.assertTrue(should_reset(["import pandas as pd"], cells_run=40))   # long session
        self.assertFalse(should_reset(["df.head()"], cells_run=2))

class TestEnvAwareInstall(unittest.TestCase):
    def test_hint_names_both_packages(self):
        hint = kernel_install_hint()
        self.assertIn("ipykernel", hint)
        self.assertIn("jupyter_client", hint)
    def test_hint_targets_active_interpreter_in_plain_env(self):
        # in a plain env (no uv/poetry/conda markers) the hint must use *this* interpreter,
        # never a bare global `pip` — guards the venv/uv concern.
        hint = kernel_install_hint(cwd="/tmp/__nonexistent_no_markers__", env={})
        self.assertIn(sys.executable, hint)
    def test_check_returns_tuple_with_hint_when_missing(self):
        ok, hint = check_kernel_available()
        self.assertIsInstance(ok, bool)
        if not ok:
            self.assertIn("ipykernel", hint)

@unittest.skipUnless(_has_kernel(), "jupyter_client/ipykernel not installed")
class TestLiveKernel(unittest.TestCase):
    def test_state_persists_and_uses_active_interpreter(self):
        with KernelSession() as k:
            k.run("x = 21")
            out = k.run("print(x * 2)")
            self.assertEqual(out["stdout"].strip(), "42")
            # the kernel must be the SAME interpreter that launched it (venv/uv safety)
            out2 = k.run("import sys; print(sys.executable)")
            self.assertEqual(out2["stdout"].strip(), sys.executable)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails.** `python3 -m unittest test_kernel_runner -v` → FAIL (no module).

- [ ] **Step 3: Implement `kernel_runner.py`.** `collect_output` / `should_reset` are pure stdlib. `kernel_install_hint(cwd, env)` detects the env manager and **always targets the active interpreter** (never a bare global `pip`). `check_kernel_available()` reports importability + the hint. `KernelSession` binds the kernel to `sys.executable` via an explicit launch command (so it inherits the venv/uv/conda env regardless of registered kernelspecs); `jupyter_client` is imported lazily inside `__init__` so the module imports without it.

```python
#!/usr/bin/env python3
"""Persistent IPython-kernel execution for ds-star-plus (Track F, CodeAct 2402.01030).

Opt-in and environment-aware: the kernel runs under THIS interpreter (sys.executable),
so it inherits whatever venv / uv / conda env launched it. Script mode is the default
and needs nothing. See references/execution.md for install guidance per env manager.
    from kernel_runner import KernelSession, check_kernel_available
    ok, hint = check_kernel_available()       # hint tells the user how to install, in THEIR env
    if ok:
        with KernelSession() as k:
            k.run("import pandas as pd; df = pd.read_csv('a.csv')")
            out = k.run("print(len(df))")      # state persists across cells
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
    """Env-appropriate install command for ipykernel+jupyter_client, targeting the ACTIVE env.

    Never emits a bare global `pip`: falls back to `"{sys.executable}" -m pip` so the install
    lands in the interpreter actually running the analysis (venv/uv-safe).
    """
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
        return f"python -m pip install {pkgs}"          # active venv on PATH
    return f'"{sys.executable}" -m pip install {pkgs}'  # plain/unknown: bind to this interpreter

def check_kernel_available():
    ok = all(importlib.util.find_spec(m) for m in ("jupyter_client", "ipykernel"))
    return ok, "" if ok else kernel_install_hint()

class KernelSession:
    def __init__(self):
        from jupyter_client.manager import KernelManager
        km = KernelManager()
        # bind the kernel to the CURRENT interpreter, not a registered kernelspec:
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
```

> Note: `km.kernel_cmd` may emit a DeprecationWarning on newer `jupyter_client`; it is still honored and is the simplest interpreter-pinning approach. If it is ever removed, register a transient kernelspec for `sys.executable` instead — same intent.

- [ ] **Step 4: Run tests.** `python3 -m unittest test_kernel_runner -v` → PASS (pure + env-hint tests always pass; live test passes if the deps are in the active env, else skipped).
- [ ] **Step 5: Commit.** `feat(ds-star-plus): optional stateful kernel runner (track F)`.

### Task F.3: `references/execution.md` + SKILL.md EXECUTE stage

**Files:** Create `skills/ds-star-plus/references/execution.md`; Modify `skills/ds-star-plus/SKILL.md` (EXECUTE stage)

- [ ] **Step 1:** Write `execution.md`. Required sections: **Two modes** (script default = paper-faithful + fully reproducible + zero extra deps; kernel opt-in = incremental state, cheaper re-runs), **When to use the kernel** (long multi-step exploratory tasks; NOT when reproducibility/auditability is paramount), **State hygiene** (`should_reset` heuristic; re-import at reset), **Mandatory clean re-run before FINALIZE** (re-execute the full accumulated script once from a fresh kernel/process to guarantee the final answer is reproducible — closes the stateful-execution risk in spec §3 F), and **Install — environment-aware** (this is the critical section): state that the kernel runs under the **active interpreter** (`sys.executable`), so deps must be installed into *that* env, never a global `pip`; reproduce the env-detection table from Task F.1 (uv / venv / poetry / conda / plain); and instruct callers to obtain the exact command at runtime from `check_kernel_available()` rather than hard-coding one. Add a one-liner that the agent should invoke our scripts through the project's runner (e.g. `uv run python …` under uv, or the activated venv's `python`) so `sys.executable` is already correct.
- [ ] **Step 2:** Update SKILL.md EXECUTE stage to mention both modes and link `references/execution.md`; default stays script.
- [ ] **Step 3:** Commit: `docs(ds-star-plus): kernel-vs-script execution reference (track F)`.

---

## Phase G — DAG planning + dynamic replan (`ds-star-plus` upgrade)

**Grounding:** Data Interpreter / MetaGPT (2402.18679).

### Task G.1: `references/planning_graph.md`

**Files:** Create `skills/ds-star-plus/references/planning_graph.md`

- [ ] **Step 1:** Write the reference. Required sections: **Representation** (plan = DAG; node `{id, goal, deps:[ids], status}`; the current linear plan is the degenerate single chain — back-compatible), **Node-level verify** (the rubric verifier runs per terminal/aggregating node, not only at the end), **Dynamic replan** (on a node failure, re-wire/insert nodes affecting only the failed node's descendants instead of truncating the whole tail — generalizes today's truncate+backtrack), **When to escalate to a graph** (multi-file joins, multiple independent outputs; simple single-output tasks stay linear — preserve the easy-task fast path), **Relation to search_mode** (the DAG is the structure `references/search_mode.md` searches over). Acceptance: doc shows the node schema and a worked 3-node example.
- [ ] **Step 2:** Commit: `docs(ds-star-plus): DAG planning + dynamic replan reference (track G)`.

### Task G.2: SKILL.md PLAN/ROUTE stages reference the graph

**Files:** Modify `skills/ds-star-plus/SKILL.md`

- [ ] **Step 1:** In the PLAN and ROUTE stages add: linear chain is the default; on multi-output/multi-file tasks, represent the plan as a DAG per `references/planning_graph.md`; node-level verify + descendant-only replan. Keep oscillation/branch text intact (it composes with the graph).
- [ ] **Step 2:** Commit: `docs(ds-star-plus): wire PLAN/ROUTE to DAG planning (track G)`.

---

## Phase E — `ds-memory` (persistent skill/workflow library)

**Grounding:** AWM (2409.07429), Voyager (2305.16291), ExpeL (2308.10144); extends Empirical-MCTS (2602.04248).

### Task E.1: `memory_store.py` (test-first)

**Files:**
- Create: `skills/ds-memory/scripts/memory_store.py`
- Test: `skills/ds-memory/scripts/test_memory_store.py`

- [ ] **Step 1: Write the failing test:**

```python
import os, tempfile, unittest
from memory_store import record, retrieve, task_signature

class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.p = os.path.join(self.d, "mem.jsonl")
    def test_record_then_retrieve_match(self):
        record(self.p, {"task_signature": "agg|pct", "data_fingerprint": "csv:1",
                        "plan": "load->groupby", "verified_code_snippet": "df.mean()",
                        "verifier_score": 4, "assumptions": ["EUR"], "outcome": "ok"})
        hits = retrieve(self.p, "agg|pct", "csv:1", k=3)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["plan"], "load->groupby")
    def test_retrieve_only_returns_verified_by_default(self):
        record(self.p, {"task_signature":"s","data_fingerprint":"f","verifier_score":2,"plan":"bad"})
        self.assertEqual(retrieve(self.p, "s", "f"), [])          # score<4 filtered out
    def test_retrieve_ranks_signature_match_first(self):
        record(self.p, {"task_signature":"agg|pct","data_fingerprint":"csv:1","verifier_score":4,"plan":"A"})
        record(self.p, {"task_signature":"agg|pct","data_fingerprint":"other","verifier_score":4,"plan":"B"})
        hits = retrieve(self.p, "agg|pct", "csv:1", k=2)
        self.assertEqual(hits[0]["plan"], "A")                     # exact fingerprint wins
    def test_task_signature_is_stable_and_order_insensitive(self):
        self.assertEqual(task_signature("Pct of CREDIT  txns?"), task_signature("pct of credit txns"))
    def test_missing_store_returns_empty(self):
        self.assertEqual(retrieve(os.path.join(self.d, "nope.jsonl"), "s", "f"), [])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails.** FAIL (no module).

- [ ] **Step 3: Implement `memory_store.py`** (stdlib: `json`, `os`, `re`):

```python
#!/usr/bin/env python3
"""Persistent cross-session recipe store for ds-crew (Track E; AWM 2409.07429).

Append-only JSONL of verified analysis recipes; retrieved by task signature + data
fingerprint similarity. Stdlib only.
    from memory_store import record, retrieve, task_signature
    record(path, {...}); hits = retrieve(path, sig, fingerprint, k=3)
"""
import json, os, re

def task_signature(text):
    """Normalized, order-insensitive bag-of-words signature for a task prompt."""
    words = sorted(set(re.findall(r"[a-z0-9]+", str(text).lower())))
    return "|".join(words)

def record(path, entry):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")

def _load(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out

def retrieve(path, signature, fingerprint, k=3, min_score=4):
    """Return up to k verified recipes, exact-fingerprint matches ranked first."""
    rows = [r for r in _load(path) if r.get("verifier_score", 0) >= min_score]
    sig_words = set(signature.split("|"))
    def score(r):
        rs = set(str(r.get("task_signature", "")).split("|"))
        overlap = len(sig_words & rs) / (len(sig_words | rs) or 1)
        fp = 1 if r.get("data_fingerprint") == fingerprint else 0
        return (fp, overlap)
    ranked = sorted(rows, key=score, reverse=True)
    return [r for r in ranked if score(r) > (0, 0)][:k]

if __name__ == "__main__":
    print(task_signature("Pct of CREDIT txns?"))
```

- [ ] **Step 4: Run tests.** PASS (5 tests).
- [ ] **Step 5: Commit.** `feat(ds-memory): persistent recipe store + retrieval (track E)`.

### Task E.2: `ds-memory` SKILL.md + store-format reference

**Files:** Create `skills/ds-memory/SKILL.md`, `skills/ds-memory/references/store_format.md`

- [ ] **Step 1:** Write `store_format.md`: the entry schema (the keys in E.1's test), where the store lives (default `./.ds-crew-memory/recipes.jsonl` in the data dir; document overriding), retrieval semantics (verified-only, fingerprint-first), and pruning guidance.
- [ ] **Step 2:** Write `SKILL.md`. `description` triggers: "inspect / prune / reuse past analyses", "have we solved this before", "remember this analysis". Sections per convention; `## How to run it` covers: inspect the store, prune stale/low-score entries, and how solvers call `record`/`retrieve`. State clearly it is **both** a thin user-invocable inspector and the substrate other skills use.
- [ ] **Step 3:** Commit: `feat(ds-memory): skill doc + store-format reference (track E)`.

### Task E.3: Wire opt-in memory hooks into `ds-star-plus` and `ds-spike`

**Files:** Modify `skills/ds-star-plus/SKILL.md` (PLAN + FINALIZE stages), `skills/ds-spike/SKILL.md` (dispatch stage)

- [ ] **Step 1:** ds-star-plus PLAN: "If a memory store exists, call `retrieve(store, task_signature(question), data_fingerprint)` and seed the planner with any hit (as a *suggestion*, never blindly trusted — the verifier still gates)." FINALIZE: "On a clean verdict (`is_sufficient`), `record(...)` the `{plan, code, score, assumptions}`." Mark the whole hook **flag-gated / optional** so an absent store is a no-op.
- [ ] **Step 2:** ds-spike dispatch: optionally seed persona assumptions from prior minority reports in the store.
- [ ] **Step 3:** Commit: `feat(ds-star-plus,ds-spike): opt-in ds-memory hooks (track E)`.

---

## Phase H — `ds-model` (AutoML solution-tree skill)

**Grounding:** AIDE (2502.13138), AutoKaggle (2410.20424), AutoML-Agent (2410.02958).

### Task H.1: `leaderboard.py` (test-first)

**Files:**
- Create: `skills/ds-model/scripts/leaderboard.py`
- Test: `skills/ds-model/scripts/test_leaderboard.py`

- [ ] **Step 1: Write the failing test:**

```python
import unittest
from leaderboard import Leaderboard

class TestLeaderboard(unittest.TestCase):
    def test_best_respects_direction_minimize(self):
        lb = Leaderboard(metric="rmse", mode="min")
        lb.add("n1", 0.9, parent=None); lb.add("n2", 0.4, parent="n1"); lb.add("n3", 0.6, parent="n1")
        self.assertEqual(lb.best()["node"], "n2")
    def test_best_respects_direction_maximize(self):
        lb = Leaderboard(metric="auc", mode="max")
        lb.add("n1", 0.7, parent=None); lb.add("n2", 0.85, parent="n1")
        self.assertEqual(lb.best()["node"], "n2")
    def test_node_to_expand_is_current_best(self):
        lb = Leaderboard(metric="rmse", mode="min")
        lb.add("n1", 0.9, parent=None); lb.add("n2", 0.5, parent="n1")
        self.assertEqual(lb.node_to_expand(), "n2")    # AIDE: improve the best draft
    def test_rejects_nan_or_missing_metric(self):
        lb = Leaderboard(metric="rmse", mode="min")
        with self.assertRaises(ValueError):
            lb.add("bad", float("nan"), parent=None)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails.** FAIL.
- [ ] **Step 3: Implement `leaderboard.py`** (stdlib: `math`): a `Leaderboard` tracking `{node, score, parent}` rows; `add` rejects NaN/None; `best()` picks min/max by `mode`; `node_to_expand()` returns the best node id (AIDE: greedily improve the strongest draft); a `tree()` helper returning parent→children.
- [ ] **Step 4: Run tests.** PASS (4 tests).
- [ ] **Step 5: Commit.** `feat(ds-model): solution-tree leaderboard (track H)`.

### Task H.2: `ds-model` SKILL.md + references

**Files:** Create `skills/ds-model/SKILL.md`, `skills/ds-model/references/solution_tree.md`, `skills/ds-model/references/leakage_cv.md`, `skills/ds-model/references/evidence.md`

- [ ] **Step 1:** `solution_tree.md`: the AIDE loop (draft → train → eval on held-out metric → improve the best node via `leaderboard.node_to_expand`), tree-of-drafts, when to stop (budget / plateau).
- [ ] **Step 2:** `leakage_cv.md`: the discipline that is the skill's core value — proper train/valid/test split, cross-validation, target leakage checklist (no future info, no target-derived features, group-aware splits for panels/time), honest metric reporting. Acceptance: a concrete leakage checklist (≥5 items).
- [ ] **Step 3:** `evidence.md`: cite 2502.13138 / 2410.20424 / 2410.02958 with one line each on what is borrowed.
- [ ] **Step 4:** `SKILL.md`: `description` triggers — "train/build a model", "predict/forecast", "Kaggle/submission", "improve model accuracy", and a NOT-for line (use `ds-star-plus` for factoid/aggregation). Sections per convention; reuse `ds-star-plus` execution (kernel) + verifier; objective is a held-out metric, not factoid sufficiency. Link the three references.
- [ ] **Step 5:** Commit: `feat(ds-model): AutoML solution-tree skill docs (track H)`.

### Task H.3: `ds-model` evals

**Files:** Create `skills/ds-model/evals/evals.json`

- [ ] **Step 1:** Mirror the `ds-star-plus/evals/evals.json` shape (`skill_name`, `note`, `evals[]`). Add ≥3 cases: a regression task (assert held-out RMSE reported + CV used), a classification task (assert AUC/accuracy on a held-out split + no leakage), a "submission format" task (assert output columns match a sample). Each with `assertions` and `files`.
- [ ] **Step 2:** Commit: `test(ds-model): checkable eval cases (track H)`.

---

## Phase I — Debate mode in `ds-spike`

**Grounding:** Multiagent debate, Du et al. (2305.14325).

### Task I.1: Extend `aggregate.py` to consume post-debate states (test-first)

**Files:**
- Modify: `skills/ds-spike/scripts/aggregate.py`
- Modify: `skills/ds-spike/scripts/test_aggregate.py`

- [ ] **Step 1: Add failing tests** to `test_aggregate.py`:

```python
def test_aggregate_uses_post_debate_answer_when_present(self):
    # a solver that revised during debate: its 'answer' is its final post-debate answer,
    # and 'revised' marks that it moved — aggregation must use the final answer.
    from aggregate import aggregate
    recs = [
        {"id":"s1","answer":41.7,"sufficient":True,"assumptions":[],"revised":False},
        {"id":"s2","answer":41.7,"sufficient":True,"assumptions":[],"revised":True},
        {"id":"s3","answer":39.4,"sufficient":True,"assumptions":[],"revised":False},
    ]
    out = aggregate(recs)
    self.assertEqual(out["answer"], 41.7)
    self.assertEqual(out["n_revised"], 1)          # new field: how many moved in debate

def test_aggregate_n_revised_defaults_zero_without_debate(self):
    from aggregate import aggregate
    out = aggregate([{"id":"s1","answer":1,"sufficient":True}])
    self.assertEqual(out["n_revised"], 0)
```

- [ ] **Step 2: Run to verify it fails.** `cd skills/ds-spike/scripts && python3 -m unittest test_aggregate -v` → FAIL (no `n_revised`).
- [ ] **Step 3: Implement.** In `aggregate()`'s returned dict add `"n_revised": sum(1 for r in results if r.get("revised"))`. (Answers already reflect final post-debate values by contract; no clustering change needed — keep the minority report.)
- [ ] **Step 4: Run tests.** PASS (existing + 2 new).
- [ ] **Step 5: Commit.** `feat(ds-spike): track debate revisions in aggregation (track I)`.

### Task I.2: `references/debate.md` + SKILL.md debate stage

**Files:** Create `skills/ds-spike/references/debate.md`; Modify `skills/ds-spike/SKILL.md`

- [ ] **Step 1:** Write `debate.md`: the protocol (after Stage 3 blackboard collection, run ≤2 debate rounds where each solver sees peers' answers+rationales and may revise, setting `revised: true` if it moves), the **round cap**, and the **anti-herding guard** (debate can amplify a confident-wrong majority — always preserve the minority report; do not let debate collapse genuine diversity). Cite 2305.14325.
- [ ] **Step 2:** In SKILL.md insert an **optional Stage 3.5 — Debate (opt-in)** between Collect and Reconcile; default `ds-spike` stays one-shot. Note the cost (extra rounds).
- [ ] **Step 3:** Commit: `docs(ds-spike): opt-in multi-agent debate stage (track I)`.

---

## Phase L — Standalone primitives

**Grounding:** DeepVerifier (2601.15808), self-consistency (2203.11171), I-MCTS/SWE-Search (2502.14693/2410.20285), blackboard (2510.01285). Each reuses an existing script — minimal new code.

### Task L.1: `ds-verify` skill

**Files:** Create `skills/ds-verify/SKILL.md`

- [ ] **Step 1:** Write SKILL.md. Reuses `../ds-star-plus/scripts/verify_schema.py` + `../ds-star-plus/references/{rubric,prompts}.md` (link, do not copy). Input: a question or `analysis-spec.md` + a candidate answer (+ optional code/data); output: the graded `{score,rubric,checks,reason,missing}` verdict. `description` triggers: "check / verify / sanity-check this answer", "is this result right", "audit this number". `## How to run it`: build the verifier prompt from `prompts.md`, parse with `parse_verdict`, gate with `is_sufficient`.
- [ ] **Step 2:** Commit: `feat(ds-verify): standalone rubric verifier skill (track L)`.

### Task L.2: `ds-reconcile` skill

**Files:** Create `skills/ds-reconcile/SKILL.md`

- [ ] **Step 1:** Write SKILL.md. Reuses `../ds-spike/scripts/aggregate.py`. Input: a list of candidate answers (+ optional code/assumptions/`sufficient` flags) the user already has; output: consensus + confidence + minority report via `aggregate()`. Optionally score each candidate with `ds-verify` first. `description` triggers: "reconcile these answers", "which of these results is right", "combine these analyses".
- [ ] **Step 2:** Commit: `feat(ds-reconcile): standalone blackboard reconciliation skill (track L)`.

### Task L.3: `ds-vote` skill

**Files:** Create `skills/ds-vote/SKILL.md`

- [ ] **Step 1:** Write SKILL.md. Self-consistency over a single solver: run `ds-star-plus` N times (varied seed, same model/persona — *no* persona diversity, unlike `ds-spike`), then `aggregate()` for a majority answer + agreement rate. Position it explicitly as the cheap cousin of `ds-spike` (cite 2203.11171). `description` triggers: "quick confidence check", "run it a few times and see if it agrees", "how stable is this number".
- [ ] **Step 2:** Commit: `feat(ds-vote): standalone self-consistency skill (track L)`.

### Task L.4: `ds-search` skill

**Files:** Create `skills/ds-search/SKILL.md`

- [ ] **Step 1:** Write SKILL.md. Standalone front-door to the MCTS search mode: link `../ds-star-plus/references/search_mode.md` and run a single hard task under search. `description` triggers: "this task is hard, search harder", "tree search this", "try multiple solution paths". Note the cost (search multiplies calls) and that it composes with the DAG (Phase G).
- [ ] **Step 2:** Commit: `feat(ds-search): standalone MCTS search-mode skill (track L)`.

### Task L.5: `ds-route` as a documented shared utility

**Files:** Create `skills/ds-star-plus/references/routing.md` (promote the existing policy to a citable reference)

- [ ] **Step 1:** Per spec §8 decision-4, `ds-route` is a **utility/reference, not a slash command**. Write `routing.md` documenting `pick_model(role, attempt, oscillating, hard)` from `scripts/route_model.py` as the reusable cost-tiering helper any skill/user can import, with the tier table and the escalation ladder. (If `model_routing.md` already covers this, instead add a top "Reusable helper" section pointing at `route_model.py` and skip a new file.)
- [ ] **Step 2:** Commit: `docs(ds-star-plus): document routing as a reusable utility (track L)`.

---

## Phase K — `ds-conduct` (data-aware orchestrator, capstone)

**Grounding:** blackboard control-agent (2510.01285), MetaGPT supervisor (2308.00352).

### Task K.1: `references/trigger_catalog.md`

**Files:** Create `skills/ds-conduct/references/trigger_catalog.md`

- [ ] **Step 1:** Write the catalog as a table: **data pattern → question to ask → candidate skill/route**. Required rows at minimum: timestamp column → "time-series? panel? horizon/frequency?" → time-aware split / `ds-model`; two files share a key → "join intended? join type?" → multi-file `ds-star-plus`; target-shaped column + predictive ask → "predict it? metric?" → `ds-model`; many files / data lake → retrieval route; high cardinality id → "entity-level aggregation?"; heavy missingness/dirty → `data-profile` first; high-stakes/contested → `ds-spike`. Acceptance: ≥7 rows, each with all three columns.
- [ ] **Step 2:** Commit: `docs(ds-conduct): data-pattern trigger catalog (track K)`.

### Task K.2: `references/workflow_plan_template.md`

**Files:** Create `skills/ds-conduct/references/workflow_plan_template.md`

- [ ] **Step 1:** A fill-in template for the conducted plan the user approves: ordered skill steps, `ds-spike` N + chosen personas, whether `ds-model` runs, the `analysis-spec.md` reference (delegated to `ds-clarify`), and explicit **checkpoint points** between handoffs. Acceptance: a worked example plan instance.
- [ ] **Step 2:** Commit: `docs(ds-conduct): workflow-plan template (track K)`.

### Task K.3: `ds-conduct` SKILL.md + evidence

**Files:** Create `skills/ds-conduct/SKILL.md`, `skills/ds-conduct/references/evidence.md`

- [ ] **Step 1:** `evidence.md`: cite 2510.01285 (control-agent/blackboard) and 2308.00352 (supervisor) — one line each.
- [ ] **Step 2:** `SKILL.md` implementing the four-stage flow from spec §3 K: **Peek** (reuse `../data-profile` analyzer in a fast read-only mode — shapes/dtypes/timestamp/geo/id detection/keys), **Grill data-aware** (extend `../ds-clarify/references/clarify_checklist.md` with the trigger catalog), **Assemble plan** (use the workflow-plan template), **Confirm → execute with checkpoints** (spec §8 decision-3: checkpoint at each handoff, not full auto-run). `description` triggers: "where do I start with this data", "orchestrate the analysis", "look at my data and tell me what to do", "set up the analysis for me". Make explicit it is a **conductor** — it invokes other skills, it does not re-implement them.
- [ ] **Step 3:** Commit: `feat(ds-conduct): data-aware orchestrator skill (track K)`.

---

## Phase M — Usage guide, manifests, and holistic docs sync

### Task M.1: `docs/USAGE.md` chooser

**Files:** Create `docs/USAGE.md`

- [ ] **Step 1:** Write the chooser with three parts: (1) **decision table** — every skill → what it does → when to reach for it → relative cost; (2) **decision flowchart** (ASCII): fuzzy request/new data → `ds-conduct`; precise question → `ds-star-plus`; high-stakes/contested → `ds-spike`; predictive task → `ds-model`; just check an answer → `ds-verify`; reconcile existing answers → `ds-reconcile`; stability check → `ds-vote`; hard single task → `ds-search`; onboard data → `data-profile`; explore → `eda-narrative`; lock intent → `ds-clarify`; reuse past work → `ds-memory`; (3) **canonical pipelines** (`ds-conduct → data-profile → ds-clarify → ds-spike`, etc.). Acceptance: every skill in the repo appears exactly once in the decision table.
- [ ] **Step 2:** Commit: `docs: add USAGE.md suite chooser (track M)`.

### Task M.2: README sync

**Files:** Modify `README.md`

- [ ] **Step 1:** Update the header count ("Six installable skills" → the new total), the skill table (add `ds-model`, `ds-conduct`, `ds-verify`, `ds-reconcile`, `ds-vote`, `ds-search`, `ds-memory`), the `/`-command list, the "typical flow" (lead with `ds-conduct`), the repo-layout tree (new skill dirs + new references/scripts), and add a prominent link to `docs/USAGE.md` near the top. Update the Status section to note tracks E–M.
- [ ] **Step 2:** Commit: `docs(readme): reflect v1.2 suite (tracks E–M)`.

### Task M.3: ROADMAP sync

**Files:** Modify `ROADMAP.md`

- [ ] **Step 1:** Add Tracks E–M with one paragraph each (pattern, paper, status ✅), update the implementation-status banner and the dependency graph/suggested-order to include the new chain `J→F→G→E→H→I→L→K→M`.
- [ ] **Step 2:** Commit: `docs(roadmap): add tracks E–M`.

### Task M.4: ARCHITECTURE sync + diagram

**Files:** Modify `ARCHITECTURE.md`, `make_diagram.py`, regenerate `architecture-comparison.svg`

- [ ] **Step 1:** Add rows for the new engine stages (kernel execution, DAG plan/replan, node-level verify, debate, memory read/write hooks). If `make_diagram.py` drives the SVG, update it and regenerate: `python3 make_diagram.py`; otherwise hand-edit the SVG minimally or note it as out of date.
- [ ] **Step 2:** Commit: `docs(architecture): v1.2 stages + regenerated diagram`.

### Task M.5: Manifest + version bump to v1.2.0

**Files:** Modify `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `package.json`

- [ ] **Step 1:** Bump all three `version` fields `1.1.0` → `1.2.0`. Update the `description` strings to list the new skills. In `marketplace.json` add keywords (`automl`, `orchestration`, `memory`, `debate`, `provenance`).
- [ ] **Step 2:** Verify JSON parses: `python3 -c "import json; [json.load(open(p)) for p in ['.claude-plugin/plugin.json','.claude-plugin/marketplace.json','package.json']]; print('ok')"`.
- [ ] **Step 3:** Commit: `chore: bump ds-crew to v1.2.0 (tracks E–M)`.

### Task M.6: Full test sweep

**Files:** none

- [ ] **Step 1:** Run every script test suite:
```bash
for d in skills/*/scripts; do (cd "$d" && python3 -m unittest -v 2>&1 | tail -3); done
```
Expected: all suites OK (run_manifest, kernel_runner, memory_store, leaderboard, aggregate, verify_schema).
- [ ] **Step 2:** Spot-check each new SKILL.md has valid frontmatter (`name` + `description`).
- [ ] **Step 3:** No commit (verification only). If anything fails, fix in its phase before declaring done.

---

## Self-review (completed by author)

- **Spec coverage:** E→Phase E; F→Phase F; G→Phase G; H→Phase H; I→Phase I; J→Phase J; K→Phase K; L→Phase L (ds-verify/reconcile/vote/search + ds-route utility); M→Phase M (USAGE.md). Citation gate→Phase 0. Docs/manifest deltas→Phase M (+ per-phase docs tasks). All spec §3 tracks mapped.
- **Open-decision resolution:** ds-memory = both inspector + substrate (E.2); kernel default = script, kernel opt-in (F.3); ds-conduct = checkpoint per handoff (K.3); ds-route = utility not command (L.5); ds-vote = thin standalone skill (L.3); /ds-help = not shipped, USAGE.md only (M.1).
- **Type consistency:** `build_manifest/write_manifest` (J), `collect_output/should_reset/check_kernel_available/kernel_install_hint/KernelSession.run` (F, kernel pinned to `sys.executable`; install hints env-aware, never global pip), `record/retrieve/task_signature` (E), `Leaderboard.add/best/node_to_expand/tree` (H), `aggregate(...)["n_revised"]` (I) used consistently across their tasks and references. Reused existing `parse_verdict/is_sufficient` (verify_schema) and `aggregate` (aggregate.py) by their real signatures.
- **Placeholder scan:** no TBD/TODO; markdown tasks carry explicit required-section lists + acceptance criteria; code tasks carry real test + impl.
