from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import GcnConfig


def ensure_output_dirs(config: GcnConfig) -> None:
    for path in (
        config.data_output_dir,
        config.table_output_dir,
        config.figure_output_dir,
        config.model_output_dir,
        config.docs_output_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def save_dataset(df: pd.DataFrame, filename: str, config: GcnConfig) -> Path:
    path = config.data_output_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def save_table(df: pd.DataFrame, filename: str, config: GcnConfig) -> Path:
    path = config.table_output_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path

