from __future__ import annotations

import numpy as np
import pandas as pd

from .gcn_model import TorchDependencyError, import_torch
from .trade_graphs import GraphSample


def require_torch():
    return import_torch()


def prepare_graph_tensors(samples: list[GraphSample]) -> dict[str, object]:
    return {
        "sample_ids": [sample.sample_id for sample in samples],
        "node_features": [sample.node_features.astype(float) for sample in samples],
        "edge_index": [sample.edge_index.astype(np.int64) for sample in samples],
        "edge_weight": [sample.edge_weight.astype(float) for sample in samples],
        "targets": np.array([sample.target_siri for sample in samples], dtype=float),
        "splits": [sample.split for sample in samples],
    }


def adjacency_from_edges(sample: GraphSample) -> np.ndarray:
    node_count = sample.node_features.shape[0]
    adjacency = np.zeros((node_count, node_count), dtype=float)
    for (source, target), weight in zip(sample.edge_index.T, sample.edge_weight, strict=True):
        adjacency[int(source), int(target)] += float(weight)
    degree = adjacency.sum(axis=1)
    degree[degree == 0] = 1.0
    d_inv_sqrt = np.diag(1.0 / np.sqrt(degree))
    return d_inv_sqrt @ adjacency @ d_inv_sqrt


def train_gcn_or_raise(samples: list[GraphSample], hidden_dim: int = 32) -> None:
    require_torch()
    if not samples:
        raise ValueError("GCN training requires at least one graph sample.")
    # Full training is intentionally kept behind the dependency gate for the first implementation pass.
    return None


def _graph_embedding(sample: GraphSample) -> np.ndarray:
    adjacency = adjacency_from_edges(sample)
    propagated = adjacency @ sample.node_features
    return propagated.mean(axis=0)


def run_numpy_gcn_regressor(samples: list[GraphSample], ridge_alpha: float = 1.0) -> pd.DataFrame:
    if not samples:
        return pd.DataFrame()
    X = np.vstack([_graph_embedding(sample) for sample in samples])
    y = np.array([sample.target_siri for sample in samples], dtype=float)
    splits = np.array([sample.split for sample in samples])
    train_mask = splits == "train"
    if train_mask.sum() == 0:
        raise ValueError("numpy GCN regressor requires at least one training sample.")
    train = X[train_mask]
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std == 0] = 1.0
    X_scaled = (X - mean) / std
    X_design = np.column_stack([np.ones(len(X_scaled)), X_scaled])
    X_train = X_design[train_mask]
    y_train = y[train_mask]
    penalty = np.eye(X_train.shape[1]) * ridge_alpha
    penalty[0, 0] = 0.0
    beta = np.linalg.pinv(X_train.T @ X_train + penalty) @ X_train.T @ y_train
    predicted = X_design @ beta
    rows: list[dict[str, object]] = []
    for sample, prediction in zip(samples, predicted, strict=True):
        rows.append(
            {
                "model": "gcn_numpy",
                "split": sample.split,
                "sample_id": sample.sample_id,
                "product_code": sample.product_code,
                "product_group": sample.product_group,
                "is_core_product": bool(sample.graph_features.get("is_core_product", False)),
                "train_year": sample.graph_year,
                "target_year": sample.target_year,
                "actual_siri": sample.target_siri,
                "predicted_siri": float(prediction),
                "error": float(prediction - sample.target_siri),
            }
        )
    return pd.DataFrame(rows)
