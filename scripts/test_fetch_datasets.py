import os, tempfile, unittest
from fetch_datasets import DATASETS, dataset_spec, target_path

class TestFetchDatasets(unittest.TestCase):
    def test_catalog_has_four(self):
        self.assertEqual(set(DATASETS), {"online_retail_ii", "owid_co2", "synthea", "bike_sharing"})
    def test_each_spec_has_url_and_license(self):
        for name in DATASETS:
            spec = dataset_spec(name)
            self.assertTrue(spec["url"].startswith("http"))
            self.assertIn(spec["license"], {"CC BY 4.0", "Apache-2.0"})
    def test_target_path_under_data_dir(self):
        p = target_path("bike_sharing", base="/tmp/data")
        self.assertTrue(p.startswith("/tmp/data"))
        self.assertIn("bike_sharing", p)
    def test_unknown_dataset_raises(self):
        with self.assertRaises(KeyError):
            dataset_spec("nope")

if __name__ == "__main__":
    unittest.main()
