from __future__ import annotations

import pandas as pd

from .config import GcnConfig


def build_validation_results(
    product_pool: pd.DataFrame,
    graph_index: pd.DataFrame,
    metrics: pd.DataFrame,
    config: GcnConfig,
    uses_gdelt: bool,
) -> pd.DataFrame:
    rows = []

    if "model_status" in product_pool.columns:
        model_products = product_pool.loc[product_pool["model_status"] == "model"]
    else:
        model_products = pd.DataFrame()
    rows.append(
        {
            "category": "product_pool",
            "check": "model product count meets threshold",
            "passed": int(len(model_products) >= config.min_model_products),
            "details": f"model_products={len(model_products)}, threshold={config.min_model_products}",
        }
    )

    usable_graphs = graph_index.loc[graph_index["status"] == "usable"] if not graph_index.empty else graph_index
    rows.append(
        {
            "category": "graphs",
            "check": "labeled graph count meets threshold",
            "passed": int(len(usable_graphs) >= config.min_labeled_graphs),
            "details": f"usable_graphs={len(usable_graphs)}, threshold={config.min_labeled_graphs}",
        }
    )

    rows.append(
        {
            "category": "gdelt",
            "check": "GDELT status is explicit",
            "passed": 1,
            "details": "enabled" if uses_gdelt else "disabled_baci_only",
        }
    )

    rows.append(
        {
            "category": "metrics",
            "check": "metrics table has rows",
            "passed": int(not metrics.empty),
            "details": f"metric_rows={len(metrics)}",
        }
    )
    return pd.DataFrame(rows)
