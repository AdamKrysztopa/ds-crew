import os, tempfile, unittest
from check_skill_paths import referenced_paths, unresolved_paths

class TestCheckSkillPaths(unittest.TestCase):
    def test_extracts_reference_and_script_paths(self):
        text = "see `references/rubric.md` and `../ds-star-plus/scripts/route_model.py`"
        got = referenced_paths(text)
        self.assertIn("references/rubric.md", got)
        self.assertIn("../ds-star-plus/scripts/route_model.py", got)

    def test_unresolved_detected_for_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            skill = os.path.join(d, "SKILL.md")
            open(skill, "w").write("ref `references/nope.md`")
            missing = unresolved_paths(skill)
            self.assertEqual(missing, ["references/nope.md"])

    def test_real_repo_skills_all_resolve(self):
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        import glob
        bad = {}
        for sk in glob.glob(os.path.join(root, "skills", "*", "SKILL.md")):
            u = unresolved_paths(sk)
            if u:
                bad[sk] = u
        self.assertEqual(bad, {}, f"unresolved skill references: {bad}")

if __name__ == "__main__":
    unittest.main()
