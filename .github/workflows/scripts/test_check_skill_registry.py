import os, tempfile, unittest
from check_skill_registry import EXPECTED_SKILLS, _frontmatter_name, registry_errors


def _make_skill(root, name, fm_name="__same__"):
    d = os.path.join(root, name)
    os.makedirs(d)
    nm = name if fm_name == "__same__" else fm_name
    open(os.path.join(d, "SKILL.md"), "w").write(
        f"---\nname: {nm}\ndescription: Use when testing.\n---\n# body\n"
    )


class TestCheckSkillRegistry(unittest.TestCase):
    def test_frontmatter_name_extracted(self):
        with tempfile.TemporaryDirectory() as d:
            _make_skill(d, "ds-foo")
            self.assertEqual(_frontmatter_name(os.path.join(d, "ds-foo", "SKILL.md")), "ds-foo")

    def test_complete_registry_passes(self):
        with tempfile.TemporaryDirectory() as d:
            for name in EXPECTED_SKILLS:
                _make_skill(d, name)
            self.assertEqual(registry_errors(d), [])

    def test_missing_skill_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            for name in list(EXPECTED_SKILLS)[1:]:  # drop one
                _make_skill(d, name)
            errs = " ".join(registry_errors(d))
            self.assertIn("missing from disk", errs)

    def test_undeclared_skill_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            for name in EXPECTED_SKILLS:
                _make_skill(d, name)
            _make_skill(d, "ds-rogue")
            errs = " ".join(registry_errors(d))
            self.assertIn("undeclared skill", errs)

    def test_name_dir_mismatch_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            for name in EXPECTED_SKILLS:
                _make_skill(d, name)
            # corrupt one skill's frontmatter name
            bad = list(EXPECTED_SKILLS)[0]
            open(os.path.join(d, bad, "SKILL.md"), "w").write(
                "---\nname: wrong-name\ndescription: x\n---\n"
            )
            errs = " ".join(registry_errors(d))
            self.assertIn("!=", errs)

    def test_real_repo_registry_is_complete(self):
        root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "skills")
        self.assertEqual(registry_errors(root), [])


if __name__ == "__main__":
    unittest.main()
