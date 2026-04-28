from __future__ import annotations

import unittest

import pandas as pd

from scripts.v03_gcn.config import GcnConfig
from scripts.v03_gcn.pipeline import run_baci_only_pipeline


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
        self.assertTrue((outputs.gdelt_pressure["gdelt_pressure_score"] == 0.0).all())


if __name__ == "__main__":
    unittest.main()
