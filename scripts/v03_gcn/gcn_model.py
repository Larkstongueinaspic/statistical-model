from __future__ import annotations


class TorchDependencyError(RuntimeError):
    """Raised when torch-dependent GCN functionality is requested without torch."""


def import_torch():
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise TorchDependencyError(
            "PyTorch is required for GCN training. Install dependencies with `pip install -r requirements.txt`."
        ) from exc
    return torch


def build_simple_gcn_model(input_dim: int, hidden_dim: int):
    torch = import_torch()

    class SimpleGraphRegressor(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = torch.nn.Linear(input_dim, hidden_dim)
            self.head = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, 1),
            )

        def forward(self, node_features, adjacency):
            hidden = torch.relu(adjacency @ self.encoder(node_features))
            pooled = hidden.mean(dim=0)
            return self.head(pooled).squeeze(-1)

    return SimpleGraphRegressor()

