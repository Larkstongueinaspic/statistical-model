from __future__ import annotations

import unittest

import pandas as pd

from scripts.v03_gcn.baselines import evaluate_predictions, run_naive_baseline, run_ridge_baseline


def feature_table() -> pd.DataFrame:
    rows = []
    for idx, (year, current, target, core) in enumerate(
        [
            (2008, 10.0, 11.0, True),
            (2009, 11.0, 13.0, True),
            (2010, 12.0, 12.0, False),
            (2022, 20.0, 21.0, True),
            (2023, 22.0, 23.0, False),
        ]
    ):
        rows.append(
            {
                "sample_id": f"sample-{idx}",
                "product_code": "848620" if core else "854110",
                "product_group": "semiconductor_equipment" if core else "semiconductor_devices",
                "is_core_product": core,
                "graph_year": year,
                "target_year": year + 1,
                "split": "train" if year <= 2010 else "test",
                "current_siri_score": current,
                "target_siri": target,
                "concentration_raw": current / 100,
                "policy_exposure_raw": 0.2,
                "alternative_insufficiency_raw": 0.3,
                "structural_volatility_raw": 0.1,
                "log_total_import_value": 5.0,
                "source_count": 2,
                "top1_import_share": 0.8,
                "usa_import_share": 0.2,
                "weighted_gdelt_pressure_score": 0.4,
                "product_group_semiconductor_equipment": int(core),
                "product_group_semiconductor_devices": int(not core),
                "product_group_integrated_circuits": 0,
                "product_group_related_hardware": 0,
            }
        )
    return pd.DataFrame(rows)


class BaselineTests(unittest.TestCase):
    def test_naive_baseline_uses_current_siri_as_prediction(self) -> None:
        predictions = run_naive_baseline(feature_table())
        row = predictions.loc[predictions["sample_id"] == "sample-0"].iloc[0]

        self.assertEqual(row["model"], "naive")
        self.assertEqual(row["predicted_siri"], 10.0)
        self.assertEqual(row["actual_siri"], 11.0)
        self.assertEqual(row["error"], -1.0)

    def test_evaluate_predictions_outputs_all_and_core_scopes(self) -> None:
        predictions = run_naive_baseline(feature_table())
        metrics = evaluate_predictions(predictions, uses_gdelt=True)

        scopes = set(metrics["sample_scope"])
        self.assertIn("all_model_products", scopes)
        self.assertIn("core4_model_products", scopes)
        test_all = metrics.loc[(metrics["split"] == "test") & (metrics["sample_scope"] == "all_model_products")].iloc[0]
        self.assertEqual(test_all["n_samples"], 2)
        self.assertTrue(bool(test_all["uses_gdelt"]))

    def test_ridge_baseline_returns_aligned_predictions(self) -> None:
        predictions = run_ridge_baseline(feature_table(), ridge_alpha=1.0)

        self.assertEqual(set(predictions["model"]), {"ridge"})
        self.assertEqual(set(predictions["sample_id"]), set(feature_table()["sample_id"]))
        self.assertFalse(predictions["predicted_siri"].isna().any())


if __name__ == "__main__":
    unittest.main()
