from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import GcnConfig


def write_summary(metrics: pd.DataFrame, validation: pd.DataFrame, config: GcnConfig, uses_gdelt: bool) -> Path:
    path = config.docs_output_dir / "summary_v0.3_gcn.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 阶段总结-v0.3-gcn",
        "",
        f"- GDELT enabled: {uses_gdelt}",
        f"- Metric rows: {len(metrics)}",
        f"- Validation checks: {len(validation)}",
        "",
        "本阶段输出年度动态图 GCN 扩展所需的数据结构、基线和验证结果。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
