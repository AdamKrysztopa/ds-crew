import unittest
from verify_citations import parse_ids_from_curl_block, abs_url

CURL_SAMPLE = """\
while IFS=' ' read -r f id; do curl -sL -o "$f" "https://arxiv.org/pdf/$id"; done <<'EOF'
ds-star-2509.21825.pdf 2509.21825
awm-2409.07429.pdf 2409.07429
EOF
"""

class TestVerifyCitations(unittest.TestCase):
    def test_parse_ids_extracts_filename_and_id(self):
        ids = parse_ids_from_curl_block(CURL_SAMPLE)
        self.assertIn(("ds-star-2509.21825.pdf", "2509.21825"), ids)
        self.assertIn(("awm-2409.07429.pdf", "2409.07429"), ids)
        self.assertEqual(len(ids), 2)
    def test_abs_url_builds_arxiv_abstract_url(self):
        self.assertEqual(abs_url("2409.07429"), "https://arxiv.org/abs/2409.07429")
    def test_parse_ignores_non_id_lines(self):
        ids = parse_ids_from_curl_block("noise\nfoo-1234.5678.pdf 1234.5678\nmore noise")
        self.assertEqual(ids, [("foo-1234.5678.pdf", "1234.5678")])

if __name__ == "__main__":
    unittest.main()
