import unittest
from runlog import validate_runlog, REQUIRED_FIELDS

class TestRunlog(unittest.TestCase):
    def test_valid_log_passes(self):
        log = {"rounds": 3, "verifier_verdicts": [{"round": 1, "score": 2},
                                                   {"round": 2, "score": 3},
                                                   {"round": 3, "score": 4}],
               "oscillated": False, "subrun_cost_usd": [0.10, 0.12]}
        errs = validate_runlog(log)
        self.assertEqual(errs, [])

    def test_missing_field_is_reported(self):
        errs = validate_runlog({"rounds": 3})
        self.assertTrue(any("verifier_verdicts" in e for e in errs))

    def test_verdicts_must_cover_each_round(self):
        log = {"rounds": 3, "verifier_verdicts": [{"round": 1, "score": 4}],
               "oscillated": False, "subrun_cost_usd": []}
        errs = validate_runlog(log)
        self.assertTrue(any("verdict" in e.lower() for e in errs))

if __name__ == "__main__":
    unittest.main()
