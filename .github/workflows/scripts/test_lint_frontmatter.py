import os, tempfile, unittest
from lint_frontmatter import parse_frontmatter, lint_skill

GOOD = "---\nname: ds-foo\ndescription: Use when you need foo. Not for bar.\n---\n# body\n"
NO_FM = "# just a heading\n"
MISSING_DESC = "---\nname: ds-foo\n---\n# body\n"

class TestLintFrontmatter(unittest.TestCase):
    def test_parse_good_frontmatter(self):
        fm = parse_frontmatter(GOOD)
        self.assertEqual(fm["name"], "ds-foo")
        self.assertIn("Use when", fm["description"])
    def test_lint_passes_good(self):
        self.assertEqual(lint_skill(GOOD), [])
    def test_lint_flags_missing_block(self):
        self.assertIn("no frontmatter block", " ".join(lint_skill(NO_FM)))
    def test_lint_flags_missing_description(self):
        self.assertIn("description", " ".join(lint_skill(MISSING_DESC)))

if __name__ == "__main__":
    unittest.main()
