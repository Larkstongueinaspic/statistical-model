from __future__ import annotations

import unittest

import pandas as pd

from scripts.v03_gcn.product_pool import (
    CORE_PRODUCT_CODES,
    build_country_crosswalk,
    build_product_pool,
)


class ProductPoolTests(unittest.TestCase):
    def test_product_pool_marks_model_report_only_and_excluded_products(self) -> None:
        product_codes = pd.DataFrame(
            [
                {"product_code": "848620", "product_description": "Semiconductor manufacturing equipment"},
                {"product_code": "854231", "product_description": "Processors and controllers"},
                {"product_code": "854110", "product_description": "Diodes"},
                {"product_code": "999999", "product_description": "Unrelated"},
            ]
        )
        coverage = pd.DataFrame(
            [
                {
                    "product_code": "848620",
                    "positive_years": 17,
                    "exporter_count": 20,
                    "labeled_transitions": 16,
                    "total_import_value_kusd": 1000.0,
                },
                {
                    "product_code": "854231",
                    "positive_years": 4,
                    "exporter_count": 2,
                    "labeled_transitions": 3,
                    "total_import_value_kusd": 500.0,
                },
                {
                    "product_code": "854110",
                    "positive_years": 15,
                    "exporter_count": 12,
                    "labeled_transitions": 14,
                    "total_import_value_kusd": 750.0,
                },
                {
                    "product_code": "853400",
                    "positive_years": 0,
                    "exporter_count": 0,
                    "labeled_transitions": 0,
                    "total_import_value_kusd": 0.0,
                },
            ]
        )

        result = build_product_pool(product_codes, coverage)
        by_code = result.set_index("product_code")

        self.assertEqual(by_code.loc["848620", "model_status"], "model")
        self.assertTrue(bool(by_code.loc["848620", "is_core_product"]))
        self.assertEqual(by_code.loc["854231", "model_status"], "report_only")
        self.assertTrue(bool(by_code.loc["854231", "is_core_product"]))
        self.assertIn("coverage", by_code.loc["854231", "status_reason"])
        self.assertEqual(by_code.loc["854110", "model_status"], "model")
        self.assertFalse(bool(by_code.loc["854110", "is_core_product"]))
        self.assertEqual(by_code.loc["853400", "model_status"], "excluded")
        self.assertIn("missing_product_metadata", by_code.loc["853400", "status_reason"])

    def test_core_product_codes_include_existing_paper_products(self) -> None:
        self.assertEqual(set(CORE_PRODUCT_CODES), {"848620", "854231", "854232", "854239"})

    def test_country_crosswalk_maps_iso3_and_marks_missing_codes(self) -> None:
        country_codes = pd.DataFrame(
            [
                {"country_code": 842, "country_iso3": "USA", "country_name": "USA"},
                {"country_code": 392, "country_iso3": "JPN", "country_name": "Japan"},
                {"country_code": 490, "country_iso3": pd.NA, "country_name": "Other Asia, nes"},
            ]
        )

        result = build_country_crosswalk(country_codes)
        by_exporter = result.set_index("exporter_code")

        self.assertEqual(by_exporter.loc[842, "gdelt_country_code"], "USA")
        self.assertEqual(by_exporter.loc[842, "mapping_status"], "mapped")
        self.assertEqual(by_exporter.loc[392, "gdelt_country_code"], "JPN")
        self.assertEqual(by_exporter.loc[490, "mapping_status"], "missing_gdelt_code")


if __name__ == "__main__":
    unittest.main()
