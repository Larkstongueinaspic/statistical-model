from __future__ import annotations

import unittest

import pandas as pd

from scripts.v03_gcn.siri_targets import build_siri_targets, attach_next_year_targets


def sample_panel() -> pd.DataFrame:
    rows = []
    for year, values in {
        2008: {842: 40.0, 392: 60.0},
        2009: {842: 20.0, 392: 30.0, 410: 50.0},
        2010: {842: 10.0, 392: 90.0},
    }.items():
        for exporter_code, import_value in values.items():
            rows.append(
                {
                    "product_code": "000001",
                    "product_description": "Demo product",
                    "year": year,
                    "exporter_code": exporter_code,
                    "import_value_kusd": import_value,
                }
            )
    return pd.DataFrame(rows)


class SiriTargetTests(unittest.TestCase):
    def test_build_siri_targets_returns_product_year_scores(self) -> None:
        result = build_siri_targets(sample_panel())

        self.assertEqual(result["product_code"].unique().tolist(), ["000001"])
        self.assertEqual(result["year"].tolist(), [2008, 2009, 2010])
        self.assertIn("siri_score", result.columns)
        self.assertIn("siri_score_policy_weighted", result.columns)

    def test_attach_next_year_targets_aligns_graph_year_to_future_siri(self) -> None:
        graph_index = pd.DataFrame(
            [
                {"sample_id": "000001-2008", "product_code": "000001", "graph_year": 2008},
                {"sample_id": "000001-2009", "product_code": "000001", "graph_year": 2009},
                {"sample_id": "000001-2010", "product_code": "000001", "graph_year": 2010},
            ]
        )
        targets = build_siri_targets(sample_panel())

        result = attach_next_year_targets(graph_index, targets)
        by_sample = result.set_index("sample_id")

        expected_2009 = targets.loc[targets["year"] == 2009, "siri_score"].iloc[0]
        expected_2010 = targets.loc[targets["year"] == 2010, "siri_score"].iloc[0]
        self.assertAlmostEqual(by_sample.loc["000001-2008", "target_siri"], expected_2009)
        self.assertAlmostEqual(by_sample.loc["000001-2009", "target_siri"], expected_2010)
        self.assertEqual(by_sample.loc["000001-2010", "status"], "skipped")
        self.assertEqual(by_sample.loc["000001-2010", "skip_reason"], "missing_target")


if __name__ == "__main__":
    unittest.main()
