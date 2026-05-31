import os, sys, tempfile, unittest

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
        if shutil.which("uv"):
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
        d, e = self._make(["uv.lock", ".venv/"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "uv")

    def test_venv_beats_conda(self):
        d, e = self._make([".venv/", "environment.yml"])
        result = detect_env(d, e)
        self.assertEqual(result["manager"], "venv")

class TestCheckImports(unittest.TestCase):
    def test_returns_bool(self):
        result = check_imports()
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()
