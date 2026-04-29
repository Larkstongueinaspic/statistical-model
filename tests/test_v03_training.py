from __future__ import annotations

import unittest

import numpy as np

from scripts.v03_gcn.trade_graphs import GraphSample
from scripts.v03_gcn.training import TorchDependencyError, prepare_graph_tensors, require_torch, run_numpy_gcn_regressor


class TrainingTests(unittest.TestCase):
    def test_require_torch_raises_clear_error_when_missing(self) -> None:
        try:
            import torch  # noqa: F401
        except ModuleNotFoundError:
            with self.assertRaisesRegex(TorchDependencyError, "pip install"):
                require_torch()
        else:
            self.assertIsNotNone(require_torch())

    def test_prepare_graph_tensors_returns_consistent_arrays(self) -> None:
        sample = GraphSample(
            sample_id="demo-2008",
            product_code="demo",
            product_group="integrated_circuits",
            graph_year=2008,
            target_year=2009,
            node_features=np.array([[1.0, 0.0], [0.0, 1.0]]),
            edge_index=np.array([[0, 1], [1, 0]]),
            edge_weight=np.array([0.5, 0.5]),
            target_siri=42.0,
            split="train",
            edge_count=2,
            source_edge_count=1,
            graph_features={},
        )

        tensors = prepare_graph_tensors([sample])

        self.assertEqual(tensors["node_features"][0].shape, (2, 2))
        self.assertEqual(tensors["edge_index"][0].shape, (2, 2))
        self.assertEqual(tensors["targets"].tolist(), [42.0])
        self.assertEqual(tensors["sample_ids"], ["demo-2008"])

    def test_numpy_gcn_regressor_returns_predictions_for_aligned_samples(self) -> None:
        samples = []
        for idx, split in enumerate(["train", "train", "test"]):
            sample = GraphSample(
                sample_id=f"demo-{idx}",
                product_code="848620",
                product_group="semiconductor_equipment",
                graph_year=2008 + idx,
                target_year=2009 + idx,
                node_features=np.array([[1.0 + idx, 0.0], [0.0, 1.0]]),
                edge_index=np.array([[0, 1], [1, 0]]),
                edge_weight=np.array([1.0, 1.0]),
                target_siri=40.0 + idx,
                split=split,
                edge_count=2,
                source_edge_count=1,
                graph_features={
                    "sample_id": f"demo-{idx}",
                    "product_code": "848620",
                    "product_group": "semiconductor_equipment",
                    "is_core_product": True,
                    "graph_year": 2008 + idx,
                    "target_year": 2009 + idx,
                },
            )
            samples.append(sample)

        predictions = run_numpy_gcn_regressor(samples, ridge_alpha=1.0)

        self.assertEqual(set(predictions["model"]), {"gcn_numpy"})
        self.assertEqual(predictions["sample_id"].tolist(), ["demo-0", "demo-1", "demo-2"])
        self.assertFalse(predictions["predicted_siri"].isna().any())


if __name__ == "__main__":
    unittest.main()
