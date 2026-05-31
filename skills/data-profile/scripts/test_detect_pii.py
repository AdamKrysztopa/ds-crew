import unittest
from detect_pii import scan_value, scan_column, scan_columns

class TestDetectPII(unittest.TestCase):
    def test_scan_value_email(self):
        self.assertIn("email", scan_value("alice@example.com"))
    def test_scan_value_credit_card_like(self):
        self.assertIn("credit_card", scan_value("4111 1111 1111 1111"))
    def test_scan_value_plain_text_is_clean(self):
        self.assertEqual(scan_value("hello world"), set())
    def test_scan_column_flags_by_name_hint(self):
        kinds = scan_column("ssn", ["123-45-6789", "987-65-4321"])
        self.assertIn("ssn", kinds)
    def test_scan_column_flags_by_value_majority(self):
        kinds = scan_column("contact", ["a@b.com", "c@d.com", "not-an-email"])
        self.assertIn("email", kinds)
    def test_scan_columns_returns_only_flagged(self):
        report = scan_columns({"id": [1, 2, 3], "mail": ["a@b.com", "c@d.com", "e@f.com"]})
        self.assertNotIn("id", report)
        self.assertIn("mail", report)

if __name__ == "__main__":
    unittest.main()
