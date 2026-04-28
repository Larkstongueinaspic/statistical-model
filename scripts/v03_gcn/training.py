from __future__ import annotations

import numpy as np

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
