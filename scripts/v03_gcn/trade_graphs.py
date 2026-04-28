from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import GcnConfig
from .product_pool import CORE_PRODUCT_CODES


FEATURE_COLUMNS = (
    "import_share",
    "ln_import_value",
    "is_usa",
    "is_china",
    "source_rank_norm",
    "source_hhi_context",
    "gdelt_pressure_score",
)
PRODUCT_GROUP_COLUMNS = (
    "product_group_semiconductor_equipment",
    "product_group_semiconductor_devices",
    "product_group_integrated_circuits",
    "product_group_related_hardware",
)


@dataclass(frozen=True)
class GraphSample:
    sample_id: str
    product_code: str
    product_group: str
    graph_year: int
    target_year: int
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_weight: np.ndarray
    target_siri: float
    split: str
    edge_count: int
    source_edge_count: int
    graph_features: dict[str, float | int | str | bool]


def _split_for_year(year: int, config: GcnConfig) -> str:
    if year in config.train_years:
        return "train"
    if year in config.validation_years:
        return "validation"
    if year in config.test_years:
        return "test"
    return "unused"


def _target_lookup(targets: pd.DataFrame) -> pd.DataFrame:
    return targets.copy().rename(
        columns={
            "year": "target_year",
            "siri_score": "target_siri",
        }
    )


def _current_siri_lookup(targets: pd.DataFrame) -> pd.DataFrame:
    return targets.copy().rename(
        columns={
            "year": "graph_year",
            "siri_score": "current_siri_score",
        }
    )


def _gdelt_lookup(gdelt_pressure: pd.DataFrame) -> pd.DataFrame:
    if gdelt_pressure.empty:
        return pd.DataFrame(columns=["exporter_code", "year", "gdelt_pressure_score"])
    return gdelt_pressure[["exporter_code", "year", "gdelt_pressure_score"]].copy()


def _product_group_one_hot(product_group: str) -> dict[str, int]:
    mapping = {
        "semiconductor_equipment": "product_group_semiconductor_equipment",
        "semiconductor_devices": "product_group_semiconductor_devices",
        "integrated_circuits": "product_group_integrated_circuits",
        "related_hardware": "product_group_related_hardware",
    }
    return {column: int(column == mapping.get(product_group, "")) for column in PRODUCT_GROUP_COLUMNS}


def _build_edges(source_count: int, config: GcnConfig) -> tuple[np.ndarray, np.ndarray]:
    china_idx = source_count
    edges: list[tuple[int, int]] = []
    weights: list[float] = []
    for idx in range(source_count):
        edges.append((idx, china_idx))
        weights.append(np.nan)
    if config.add_reverse_edges:
        for idx in range(source_count):
            edges.append((china_idx, idx))
            weights.append(np.nan)
    if config.add_self_loops:
        for idx in range(source_count + 1):
            edges.append((idx, idx))
            weights.append(1.0)
    return np.array(edges, dtype=np.int64).T, np.array(weights, dtype=float)


def _source_rows_with_features(group: pd.DataFrame, gdelt: pd.DataFrame) -> pd.DataFrame:
    total = float(group["import_value_kusd"].sum())
    result = group.copy()
    result["import_share"] = result["import_value_kusd"] / total if total > 0 else 0.0
    result = result.sort_values(["import_share", "exporter_code"], ascending=[False, True], ignore_index=True)
    source_count = len(result)
    result["source_rank_norm"] = 0.0
    if source_count > 1:
        result["source_rank_norm"] = result.index / (source_count - 1)
    result = result.merge(gdelt, on=["exporter_code", "year"], how="left")
    result["gdelt_pressure_score"] = result["gdelt_pressure_score"].fillna(0.0)
    return result


def build_graph_samples(
    panel: pd.DataFrame,
    targets: pd.DataFrame,
    gdelt_pressure: pd.DataFrame,
    config: GcnConfig,
) -> tuple[list[GraphSample], pd.DataFrame]:
    positive = panel.loc[panel["import_value_kusd"] > 0].copy()
    target = _target_lookup(targets)
    current = _current_siri_lookup(targets)
    gdelt = _gdelt_lookup(gdelt_pressure)
    samples: list[GraphSample] = []
    index_rows: list[dict[str, object]] = []

    for (product_code, year), group in positive.groupby(["product_code", "year"], sort=True):
        year = int(year)
        if year >= max(config.years):
            continue
        sample_id = f"{product_code}-{year}"
        target_year = year + 1
        product_group = str(group["product_group"].iloc[0]) if "product_group" in group.columns else ""
        target_row = target.loc[(target["product_code"] == product_code) & (target["target_year"] == target_year)]
        current_row = current.loc[(current["product_code"] == product_code) & (current["graph_year"] == year)]
        if target_row.empty or current_row.empty:
            index_rows.append(
                {
                    "sample_id": sample_id,
                    "product_code": product_code,
                    "graph_year": year,
                    "target_year": target_year,
                    "node_count": 0,
                    "edge_count": 0,
                    "source_edge_count": 0,
                    "target_siri": np.nan,
                    "split": _split_for_year(year, config),
                    "status": "skipped",
                    "skip_reason": "missing_target" if target_row.empty else "missing_current_siri",
                }
            )
            continue
        source_rows = _source_rows_with_features(group, gdelt)
        source_count = len(source_rows)
        total = float(source_rows["import_value_kusd"].sum())
        hhi = float((source_rows["import_share"] ** 2).sum()) if total > 0 else 0.0
        weighted_gdelt = float((source_rows["import_share"] * source_rows["gdelt_pressure_score"]).sum())
        source_features = np.column_stack(
            [
                source_rows["import_share"].to_numpy(dtype=float),
                np.log(source_rows["import_value_kusd"].to_numpy(dtype=float) + 1.0),
                (source_rows["exporter_code"].astype(int).to_numpy() == 842).astype(float),
                np.zeros(source_count, dtype=float),
                source_rows["source_rank_norm"].to_numpy(dtype=float),
                np.full(source_count, hhi, dtype=float),
                source_rows["gdelt_pressure_score"].to_numpy(dtype=float),
            ]
        )
        china_features = np.array([[1.0, np.log(total + 1.0), 0.0, 1.0, 0.0, hhi, weighted_gdelt]], dtype=float)
        node_features = np.vstack([source_features, china_features])
        edge_index, edge_weight = _build_edges(source_count, config)
        source_weights = source_rows["import_share"].to_numpy(dtype=float)
        edge_weight[:source_count] = source_weights
        if config.add_reverse_edges:
            edge_weight[source_count : source_count * 2] = source_weights
        target_siri = float(target_row["target_siri"].iloc[0])
        current_siri = float(current_row["current_siri_score"].iloc[0])
        split = _split_for_year(year, config)
        graph_features = {
            "sample_id": sample_id,
            "product_code": str(product_code),
            "product_group": product_group,
            "is_core_product": str(product_code) in CORE_PRODUCT_CODES,
            "graph_year": year,
            "target_year": target_year,
            "split": split,
            "current_siri_score": current_siri,
            "target_siri": target_siri,
            "concentration_raw": float(current_row["concentration_raw"].iloc[0]),
            "policy_exposure_raw": float(current_row["policy_exposure_raw"].iloc[0]),
            "alternative_insufficiency_raw": float(current_row["alternative_insufficiency_raw"].iloc[0]),
            "structural_volatility_raw": float(current_row["structural_volatility_raw"].iloc[0]),
            "log_total_import_value": float(np.log(total + 1.0)),
            "source_count": int(source_count),
            "top1_import_share": float(source_rows["import_share"].max()),
            "usa_import_share": float(
                source_rows.loc[source_rows["exporter_code"].astype(int) == 842, "import_share"].sum()
            ),
            "weighted_gdelt_pressure_score": weighted_gdelt,
            **_product_group_one_hot(product_group),
        }
        sample = GraphSample(
            sample_id=sample_id,
            product_code=str(product_code),
            product_group=product_group,
            graph_year=year,
            target_year=target_year,
            node_features=node_features,
            edge_index=edge_index,
            edge_weight=edge_weight,
            target_siri=target_siri,
            split=split,
            edge_count=int(edge_index.shape[1]),
            source_edge_count=source_count,
            graph_features=graph_features,
        )
        samples.append(sample)
        index_rows.append(
            {
                "sample_id": sample_id,
                "product_code": str(product_code),
                "graph_year": year,
                "target_year": target_year,
                "node_count": int(node_features.shape[0]),
                "edge_count": sample.edge_count,
                "source_edge_count": source_count,
                "target_siri": target_siri,
                "split": split,
                "status": "usable",
                "skip_reason": "",
            }
        )
    return samples, pd.DataFrame(index_rows)


def build_graph_level_features(samples: list[GraphSample]) -> pd.DataFrame:
    rows = [sample.graph_features for sample in samples]
    columns = [
        "sample_id",
        "product_code",
        "product_group",
        "is_core_product",
        "graph_year",
        "target_year",
        "split",
        "current_siri_score",
        "target_siri",
        "concentration_raw",
        "policy_exposure_raw",
        "alternative_insufficiency_raw",
        "structural_volatility_raw",
        "log_total_import_value",
        "source_count",
        "top1_import_share",
        "usa_import_share",
        "weighted_gdelt_pressure_score",
        *PRODUCT_GROUP_COLUMNS,
    ]
    return pd.DataFrame(rows, columns=columns)
