from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

import pandas as pd

from scripts.v03_gcn.config import GcnConfig
from scripts.v03_gcn.pipeline import run_baci_only_pipeline, run_extended_baci_pipeline, run_panel_pipeline


class PipelineTests(unittest.TestCase):
    def test_baci_only_pipeline_builds_graph_features_predictions_and_metrics(self) -> None:
        rows = []
        for year in range(2008, 2012):
            rows.extend(
                [
                    {
                        "product_code": "848620",
                        "product_group": "semiconductor_equipment",
                        "product_description": "Equipment",
                        "year": year,
                        "exporter_code": 842,
                        "exporter_name": "USA",
                        "exporter_iso3": "USA",
                        "import_value_kusd": 40.0 + year - 2008,
                    },
                    {
                        "product_code": "848620",
                        "product_group": "semiconductor_equipment",
                        "product_description": "Equipment",
                        "year": year,
                        "exporter_code": 392,
                        "exporter_name": "Japan",
                        "exporter_iso3": "JPN",
                        "import_value_kusd": 60.0,
                    },
                ]
            )
        panel = pd.DataFrame(rows)
        config = GcnConfig(
            years=tuple(range(2008, 2012)),
            train_years=(2008, 2009),
            validation_years=(2010,),
            test_years=(),
            min_model_products=1,
            min_labeled_graphs=1,
            disable_gdelt=True,
            allow_baci_only=True,
        )

        outputs = run_baci_only_pipeline(panel, config)

        self.assertFalse(outputs.graph_features.empty)
        self.assertFalse(outputs.predictions.empty)
        self.assertFalse(outputs.metrics.empty)
        self.assertIn("naive", set(outputs.predictions["model"]))
        self.assertIn("ridge", set(outputs.predictions["model"]))
        self.assertIn("gcn_numpy", set(outputs.predictions["model"]))
        self.assertTrue((outputs.gdelt_pressure["gdelt_pressure_score"] == 0.0).all())
        self.assertIn("mapping_status", outputs.country_crosswalk.columns)

    def test_extended_baci_pipeline_reads_raw_baci_when_available(self) -> None:
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
            pd.DataFrame([{"code": "848620", "description": "Equipment"}]).to_csv(
                data_dir / "product_codes_HS07_V202601.csv", index=False
            )
            for year in range(2008, 2012):
                pd.DataFrame(
                    [
                        {"t": year, "i": 842, "j": 156, "k": "848620", "v": 10.0 + year - 2008, "q": 1.0},
                        {"t": year, "i": 392, "j": 156, "k": "848620", "v": 20.0, "q": 2.0},
                    ]
                ).to_csv(data_dir / f"BACI_HS07_Y{year}_V202601.csv", index=False)
            config = GcnConfig(
                root=root,
                years=tuple(range(2008, 2012)),
                train_years=(2008, 2009),
                validation_years=(2010,),
                test_years=(),
                min_positive_years=1,
                min_exporter_count=1,
                min_labeled_transitions=1,
                min_model_products=1,
                min_labeled_graphs=1,
                disable_gdelt=True,
                allow_baci_only=True,
            )

            outputs = run_extended_baci_pipeline(config)

            self.assertFalse(outputs.product_pool.empty)
            self.assertEqual(outputs.product_pool.set_index("product_code").loc["848620", "model_status"], "model")
            self.assertFalse(outputs.graph_features.empty)

    def test_panel_pipeline_uses_real_gdelt_events_when_provided(self) -> None:
        rows = []
        for year in range(2008, 2012):
            rows.extend(
                [
                    {
                        "product_code": "848620",
                        "product_group": "semiconductor_equipment",
                        "product_description": "Equipment",
                        "year": year,
                        "exporter_code": 842,
                        "exporter_name": "USA",
                        "exporter_iso3": "USA",
                        "import_value_kusd": 40.0,
                    },
                    {
                        "product_code": "848620",
                        "product_group": "semiconductor_equipment",
                        "product_description": "Equipment",
                        "year": year,
                        "exporter_code": 392,
                        "exporter_name": "Japan",
                        "exporter_iso3": "JPN",
                        "import_value_kusd": 60.0,
                    },
                ]
            )
        panel = pd.DataFrame(rows)
        gdelt_events = pd.DataFrame(
            [
                {
                    "SQLDATE": 20080101,
                    "Actor1CountryCode": "USA",
                    "Actor2CountryCode": "CHN",
                    "GoldsteinScale": -5.0,
                    "NumMentions": 2,
                    "AvgTone": -1.0,
                    "SOURCEURL": "https://example.test/chip",
                }
            ]
        )
        config = GcnConfig(
            years=tuple(range(2008, 2012)),
            train_years=(2008, 2009),
            validation_years=(2010,),
            test_years=(),
            min_model_products=1,
            min_labeled_graphs=1,
            disable_gdelt=False,
            allow_baci_only=False,
        )

        outputs = run_panel_pipeline(panel, config, gdelt_events=gdelt_events)

        self.assertGreater(outputs.gdelt_pressure["gdelt_event_count"].sum(), 0)
        self.assertTrue(outputs.metrics["uses_gdelt"].all())
        self.assertEqual(
            set(outputs.country_crosswalk["gdelt_country_code"]),
            {"USA", "JPN"},
        )


if __name__ == "__main__":
    unittest.main()
