from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import AnalysisConfig


def ensure_output_dirs(config: AnalysisConfig) -> None:
    for path in [
        config.output_dir,
        config.data_output_dir,
        config.figure_output_dir,
        config.table_output_dir,
        config.docs_output_dir,
        config.mpl_config_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def render_markdown_table(df: pd.DataFrame) -> str:
    table = df.copy()
    table.columns = [str(column) for column in table.columns]
    rows = [table.columns.tolist()] + table.astype(str).values.tolist()
    widths = [max(len(str(row[idx])) for row in rows) for idx in range(len(table.columns))]

    def format_row(row: list[str]) -> str:
        return "| " + " | ".join(str(value).ljust(widths[idx]) for idx, value in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    return "\n".join([format_row(rows[0]), separator] + [format_row(row) for row in rows[1:]])


def save_table(df: pd.DataFrame, stem: str, config: AnalysisConfig) -> None:
    df.to_csv(config.table_output_dir / f"{stem}.csv", index=False)
    (config.table_output_dir / f"{stem}.md").write_text(render_markdown_table(df), encoding="utf-8")


def save_dataset(df: pd.DataFrame, filename: str, config: AnalysisConfig) -> None:
    df.to_csv(config.data_output_dir / filename, index=False)


def save_text_output(text: str, filename: str, output_dir: Path) -> None:
    (output_dir / filename).write_text(text, encoding="utf-8")
