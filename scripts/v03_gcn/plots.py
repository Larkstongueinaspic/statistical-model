from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import GcnConfig


def plot_actual_vs_predicted(predictions: pd.DataFrame, config: GcnConfig) -> Path | None:
    if predictions.empty:
        return None
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return None
    path = config.figure_output_dir / "gcn_actual_vs_predicted_siri.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(predictions["actual_siri"], predictions["predicted_siri"], alpha=0.7)
    ax.set_xlabel("Actual SIRI")
    ax.set_ylabel("Predicted SIRI")
    ax.set_title("v0.3 GCN extension predictions")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path

