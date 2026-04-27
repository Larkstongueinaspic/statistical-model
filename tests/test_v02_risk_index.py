from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from scripts.v02_analysis.risk_index import (
    BASELINE_WEIGHTS,
    POLICY_WEIGHTED_WEIGHTS,
    build_siri_panel,
    build_siri_ranking,
    build_siri_weight_sensitivity,
    compute_siri_scores,
    normalize_siri_components,
    validate_weights,
)


def sample_panel() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2008,
                "exporter_code": 842,
                "exporter_name": "USA",
                "import_value_kusd": 40.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2008,
                "exporter_code": 392,
                "exporter_name": "Japan",
                "import_value_kusd": 60.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2009,
                "exporter_code": 842,
                "exporter_name": "USA",
                "import_value_kusd": 20.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2009,
                "exporter_code": 392,
                "exporter_name": "Japan",
                "import_value_kusd": 30.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2009,
                "exporter_code": 410,
                "exporter_name": "Rep. of Korea",
                "import_value_kusd": 50.0,
            },
        ]
    )


class RiskIndexTests(unittest.TestCase):
    def test_build_siri_panel_computes_raw_components(self) -> None:
        result = build_siri_panel(sample_panel())
        row_2008 = result.loc[result["year"] == 2008].iloc[0]
        row_2009 = result.loc[result["year"] == 2009].iloc[0]

        self.assertAlmostEqual(row_2008["total_import_value_kusd"], 100.0)
        self.assertAlmostEqual(row_2008["concentration_raw"], 0.52)
        self.assertAlmostEqual(row_2008["policy_exposure_raw"], 0.4)
        self.assertAlmostEqual(row_2008["alternative_insufficiency_raw"], 1.0)
        self.assertAlmostEqual(row_2008["structural_volatility_raw"], 0.0)

        self.assertAlmostEqual(row_2009["concentration_raw"], 0.38)
        self.assertAlmostEqual(row_2009["policy_exposure_raw"], 0.2)
        self.assertAlmostEqual(row_2009["alternative_insufficiency_raw"], 0.53125)
        self.assertAlmostEqual(row_2009["structural_volatility_raw"], 0.5)

    def test_normalize_and_score_bounds(self) -> None:
        raw = build_siri_panel(sample_panel())
        normalized = normalize_siri_components(raw)
        scored = compute_siri_scores(normalized, BASELINE_WEIGHTS, score_column="siri_score")

        self.assertTrue(((scored["siri_score"] >= 0) & (scored["siri_score"] <= 100)).all())
        for column in [
            "concentration_norm",
            "policy_exposure_norm",
            "alternative_insufficiency_norm",
            "structural_volatility_norm",
        ]:
            self.assertTrue(((scored[column] >= 0) & (scored[column] <= 1)).all())

    def test_missing_us_and_zero_total_are_handled(self) -> None:
        panel = pd.DataFrame(
            [
                {
                    "product_code": "000002",
                    "product_description": "No US product",
                    "year": 2008,
                    "exporter_code": 392,
                    "exporter_name": "Japan",
                    "import_value_kusd": 0.0,
                }
            ]
        )
        result = build_siri_panel(panel)
        row = result.iloc[0]
        self.assertEqual(row["total_import_value_kusd"], 0.0)
        self.assertEqual(row["policy_exposure_raw"], 0.0)
        self.assertEqual(row["concentration_raw"], 0.0)
        self.assertEqual(row["structural_volatility_raw"], 0.0)

    def test_min_equals_max_normalizes_to_zero(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "product_code": "000001",
                    "product_name": "Demo",
                    "year": 2008,
                    "total_import_value_kusd": 100.0,
                    "concentration_raw": 1.0,
                    "policy_exposure_raw": 0.0,
                    "alternative_insufficiency_raw": 1.0,
                    "structural_volatility_raw": 0.0,
                },
                {
                    "product_code": "000002",
                    "product_name": "Demo 2",
                    "year": 2008,
                    "total_import_value_kusd": 100.0,
                    "concentration_raw": 1.0,
                    "policy_exposure_raw": 0.0,
                    "alternative_insufficiency_raw": 1.0,
                    "structural_volatility_raw": 0.0,
                },
            ]
        )
        normalized = normalize_siri_components(raw)
        self.assertTrue(np.isclose(normalized["concentration_norm"], 0.0).all())
        self.assertTrue(np.isclose(normalized["policy_exposure_norm"], 0.0).all())

    def test_invalid_weights_raise_clear_error(self) -> None:
        with self.assertRaises(ValueError):
            validate_weights({"concentration": 1.0})
        with self.assertRaises(ValueError):
            validate_weights(
                {
                    "concentration": 0.25,
                    "policy_exposure": 0.25,
                    "alternative_insufficiency": 0.25,
                    "structural_volatility": -0.25,
                }
            )

    def test_ranking_and_sensitivity_are_deterministic(self) -> None:
        raw = build_siri_panel(sample_panel())
        normalized = normalize_siri_components(raw)
        scored = compute_siri_scores(normalized, BASELINE_WEIGHTS, score_column="siri_score")
        scored = compute_siri_scores(scored, POLICY_WEIGHTED_WEIGHTS, score_column="siri_score_policy_weighted")

        ranking = build_siri_ranking(scored, target_year=2009)
        sensitivity = build_siri_weight_sensitivity(scored, target_year=2009)

        self.assertEqual(ranking.iloc[0]["rank"], 1)
        self.assertIn("rank_policy_weighted", ranking.columns)
        self.assertIn("rank_change", ranking.columns)
        self.assertIn("policy_weighted_rank", sensitivity.columns)

    def test_ranking_tie_breaks_by_recent_average_then_product_code(self) -> None:
        scored = pd.DataFrame(
            [
                {"product_code": "A", "product_name": "A product", "year": 2022, "siri_score": 20.0, "siri_score_policy_weighted": 20.0},
                {"product_code": "A", "product_name": "A product", "year": 2023, "siri_score": 40.0, "siri_score_policy_weighted": 40.0},
                {"product_code": "A", "product_name": "A product", "year": 2024, "siri_score": 80.0, "siri_score_policy_weighted": 80.0},
                {"product_code": "B", "product_name": "B product", "year": 2022, "siri_score": 40.0, "siri_score_policy_weighted": 40.0},
                {"product_code": "B", "product_name": "B product", "year": 2023, "siri_score": 60.0, "siri_score_policy_weighted": 60.0},
                {"product_code": "B", "product_name": "B product", "year": 2024, "siri_score": 80.0, "siri_score_policy_weighted": 80.0},
                {"product_code": "D", "product_name": "D product", "year": 2022, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "D", "product_name": "D product", "year": 2023, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "D", "product_name": "D product", "year": 2024, "siri_score": 50.0, "siri_score_policy_weighted": 50.0},
                {"product_code": "C", "product_name": "C product", "year": 2022, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "C", "product_name": "C product", "year": 2023, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "C", "product_name": "C product", "year": 2024, "siri_score": 50.0, "siri_score_policy_weighted": 50.0},
            ]
        )
        ranking = build_siri_ranking(scored, target_year=2024)
        self.assertEqual(ranking["product_code"].tolist(), ["B", "A", "C", "D"])
        self.assertEqual(ranking.set_index("product_code").loc["B", "rank"], 1)
        self.assertEqual(ranking.set_index("product_code").loc["A", "rank"], 2)
        self.assertEqual(ranking.set_index("product_code").loc["C", "rank"], 3)
        self.assertEqual(ranking.set_index("product_code").loc["D", "rank"], 4)


if __name__ == "__main__":
    unittest.main()
