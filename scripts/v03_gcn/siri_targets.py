from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from scripts.v02_analysis.risk_index import build_siri_outputs
except ModuleNotFoundError:
    from v02_analysis.risk_index import build_siri_outputs


def build_siri_targets(panel: pd.DataFrame) -> pd.DataFrame:
    siri_index, _, _ = build_siri_outputs(panel)
    result = siri_index.copy()
    return result[
        [
            "product_code",
            "product_name",
            "year",
            "total_import_value_kusd",
            "concentration_raw",
            "policy_exposure_raw",
            "alternative_insufficiency_raw",
            "structural_volatility_raw",
            "siri_score",
            "siri_score_policy_weighted",
        ]
    ].sort_values(["product_code", "year"], ignore_index=True)


def attach_next_year_targets(graph_index: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    result = graph_index.copy()
    result["target_year"] = result["graph_year"].astype(int) + 1
    lookup = targets[["product_code", "year", "siri_score"]].rename(
        columns={"year": "target_year", "siri_score": "target_siri"}
    )
    result = result.merge(lookup, on=["product_code", "target_year"], how="left")
    if "status" not in result.columns:
        result["status"] = "usable"
    if "skip_reason" not in result.columns:
        result["skip_reason"] = ""
    missing = result["target_siri"].isna()
    result.loc[missing, "status"] = "skipped"
    result.loc[missing, "skip_reason"] = "missing_target"
    result["target_siri"] = result["target_siri"].astype(float)
    result.loc[missing, "target_siri"] = np.nan
    return result
