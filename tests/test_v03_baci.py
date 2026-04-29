from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.v03_gcn.baci import (
    build_balanced_panel,
    build_product_coverage,
    build_positive_trade_sample,
    load_country_codes,
    load_product_codes,
    load_yearly_candidate_trades,
)
from scripts.v03_gcn.config import GcnConfig
from scripts.v03_gcn.product_pool import GCN_PRODUCT_CODES


class BaciTests(unittest.TestCase):
    def test_load_yearly_candidate_trades_filters_china_and_product_pool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "BACI_HS07_V202601"
            data_dir.mkdir()
            pd.DataFrame(
                [
                    {"t": 2008, "i": 842, "j": 156, "k": "848620", "v": 10.0, "q": 1.0},
                    {"t": 2008, "i": 392, "j": 156, "k": "999999", "v": 20.0, "q": 2.0},
                    {"t": 2008, "i": 842, "j": 392, "k": "848620", "v": 30.0, "q": 3.0},
                ]
            ).to_csv(data_dir / "BACI_HS07_Y2008_V202601.csv", index=False)
            config = GcnConfig(root=root, years=(2008,))

            result = load_yearly_candidate_trades(2008, GCN_PRODUCT_CODES, config)

            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]["product_code"], "848620")
            self.assertEqual(result.iloc[0]["exporter_code"], 842)

    def test_product_metadata_country_metadata_and_balanced_panel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "BACI_HS07_V202601"
            data_dir.mkdir()
            pd.DataFrame(
                [
                    {"country_code": 842, "country_name": "USA", "country_iso2": "US", "country_iso3": "USA"},
                    {"country_code": 392, "country_name": "Japan", "country_iso2": "JP", "country_iso3": "JPN"},
                ]
            ).to_csv(data_dir / "country_codes_V202601.csv", index=False)
            pd.DataFrame(
                [
                    {"code": "848620", "description": "Semiconductor equipment"},
                    {"code": "854231", "description": "Processors"},
                ]
            ).to_csv(data_dir / "product_codes_HS07_V202601.csv", index=False)
            for year in (2008, 2009):
                pd.DataFrame(
                    [
                        {"t": year, "i": 842, "j": 156, "k": "848620", "v": 10.0 + year - 2008, "q": 1.0},
                        {"t": year, "i": 392, "j": 156, "k": "848620", "v": 20.0, "q": 2.0},
                    ]
                ).to_csv(data_dir / f"BACI_HS07_Y{year}_V202601.csv", index=False)
            config = GcnConfig(root=root, years=(2008, 2009), min_positive_years=1, min_labeled_transitions=1)

            countries = load_country_codes(config)
            products = load_product_codes(config)
            positive, year_checks = build_positive_trade_sample(countries, products, config)
            coverage = build_product_coverage(positive, config)
            panel = build_balanced_panel(positive, ("848620",), config)

            self.assertEqual(len(year_checks), len(GCN_PRODUCT_CODES) * 2)
            self.assertEqual(coverage.set_index("product_code").loc["848620", "positive_years"], 2)
            self.assertEqual(len(panel), 4)
            self.assertIn("import_share", panel.columns)
            self.assertEqual(set(panel["product_group"]), {"semiconductor_equipment"})


if __name__ == "__main__":
    unittest.main()
