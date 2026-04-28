from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from scripts.v03_gcn.config import GcnConfig
from scripts.v03_gcn.trade_graphs import build_graph_level_features, build_graph_samples


class TradeGraphTests(unittest.TestCase):
    def test_build_graph_samples_creates_source_china_graph_with_expected_features(self) -> None:
        panel = pd.DataFrame(
            [
                {
                    "product_code": "848620",
                    "product_group": "semiconductor_equipment",
                    "product_description": "Equipment",
                    "year": 2008,
                    "exporter_code": 842,
                    "exporter_iso3": "USA",
                    "exporter_name": "USA",
                    "import_value_kusd": 40.0,
                },
                {
                    "product_code": "848620",
                    "product_group": "semiconductor_equipment",
                    "product_description": "Equipment",
                    "year": 2008,
                    "exporter_code": 392,
                    "exporter_iso3": "JPN",
                    "exporter_name": "Japan",
                    "import_value_kusd": 60.0,
                },
            ]
        )
        targets = pd.DataFrame(
            [
                {
                    "product_code": "848620",
                    "year": 2008,
                    "siri_score": 20.0,
                    "concentration_raw": 0.52,
                    "policy_exposure_raw": 0.4,
                    "alternative_insufficiency_raw": 1.0,
                    "structural_volatility_raw": 0.0,
                    "total_import_value_kusd": 100.0,
                },
                {
                    "product_code": "848620",
                    "year": 2009,
                    "siri_score": 30.0,
                    "concentration_raw": 0.38,
                    "policy_exposure_raw": 0.2,
                    "alternative_insufficiency_raw": 0.5,
                    "structural_volatility_raw": 0.5,
                    "total_import_value_kusd": 100.0,
                },
            ]
        )
        gdelt = pd.DataFrame(
            [
                {"exporter_code": 842, "year": 2008, "gdelt_pressure_score": 0.8},
                {"exporter_code": 392, "year": 2008, "gdelt_pressure_score": 0.2},
            ]
        )

        samples, index = build_graph_samples(panel, targets, gdelt, GcnConfig())

        self.assertEqual(len(samples), 1)
        sample = samples[0]
        self.assertEqual(sample.sample_id, "848620-2008")
        self.assertEqual(sample.node_features.shape, (3, 7))
        self.assertEqual(sample.edge_index.shape[0], 2)
        self.assertEqual(sample.edge_count, 7)
        self.assertEqual(sample.source_edge_count, 2)
        self.assertAlmostEqual(sample.target_siri, 30.0)
        self.assertEqual(index.iloc[0]["status"], "usable")

        usa_features = sample.node_features[sample.node_features[:, 2] == 1.0][0]
        china_features = sample.node_features[2]
        self.assertAlmostEqual(usa_features[0], 0.4)
        self.assertAlmostEqual(usa_features[2], 1.0)
        self.assertAlmostEqual(china_features[0], 1.0)
        self.assertAlmostEqual(china_features[3], 1.0)
        self.assertAlmostEqual(china_features[6], 0.44)

    def test_graph_level_features_align_with_samples(self) -> None:
        panel = pd.DataFrame(
            [
                {"product_code": "854231", "product_group": "integrated_circuits", "year": 2008, "exporter_code": 842, "import_value_kusd": 20.0},
                {"product_code": "854231", "product_group": "integrated_circuits", "year": 2008, "exporter_code": 392, "import_value_kusd": 80.0},
            ]
        )
        targets = pd.DataFrame(
            [
                {
                    "product_code": "854231",
                    "year": 2008,
                    "siri_score": 10.0,
                    "concentration_raw": 0.68,
                    "policy_exposure_raw": 0.2,
                    "alternative_insufficiency_raw": 1.0,
                    "structural_volatility_raw": 0.0,
                    "total_import_value_kusd": 100.0,
                },
                {
                    "product_code": "854231",
                    "year": 2009,
                    "siri_score": 11.0,
                    "concentration_raw": 0.50,
                    "policy_exposure_raw": 0.1,
                    "alternative_insufficiency_raw": 0.8,
                    "structural_volatility_raw": 0.1,
                    "total_import_value_kusd": 200.0,
                },
            ]
        )
        gdelt = pd.DataFrame(
            [
                {"exporter_code": 842, "year": 2008, "gdelt_pressure_score": 1.0},
                {"exporter_code": 392, "year": 2008, "gdelt_pressure_score": 0.0},
            ]
        )
        samples, _ = build_graph_samples(panel, targets, gdelt, GcnConfig())

        features = build_graph_level_features(samples)
        row = features.iloc[0]

        self.assertEqual(row["sample_id"], "854231-2008")
        self.assertTrue(bool(row["is_core_product"]))
        self.assertAlmostEqual(row["current_siri_score"], 10.0)
        self.assertAlmostEqual(row["target_siri"], 11.0)
        self.assertAlmostEqual(row["usa_import_share"], 0.2)
        self.assertAlmostEqual(row["weighted_gdelt_pressure_score"], 0.2)
        self.assertEqual(row["product_group_integrated_circuits"], 1)
        self.assertTrue(np.isclose(row["log_total_import_value"], np.log(101.0)))


if __name__ == "__main__":
    unittest.main()
