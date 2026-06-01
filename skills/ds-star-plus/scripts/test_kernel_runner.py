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
        self.assertTrue(should_reset(["import pandas as pd"], cells_run=40))
        self.assertFalse(should_reset(["df.head()"], cells_run=2))

class TestEnvAwareInstall(unittest.TestCase):
    def test_hint_names_both_packages(self):
        hint = kernel_install_hint()
        self.assertIn("ipykernel", hint)
        self.assertIn("jupyter_client", hint)
    def test_hint_targets_active_interpreter_in_plain_env(self):
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
            out2 = k.run("import sys; print(sys.executable)")
            self.assertEqual(out2["stdout"].strip(), sys.executable)

if __name__ == "__main__":
    unittest.main()
