from __future__ import annotations

import math

import numpy as np
import pandas as pd


RIDGE_FEATURE_COLUMNS = [
    "current_siri_score",
    "concentration_raw",
    "policy_exposure_raw",
    "alternative_insufficiency_raw",
    "structural_volatility_raw",
    "log_total_import_value",
    "source_count",
    "top1_import_share",
    "usa_import_share",
    "weighted_gdelt_pressure_score",
    "product_group_semiconductor_equipment",
    "product_group_semiconductor_devices",
    "product_group_integrated_circuits",
    "product_group_related_hardware",
]


def _prediction_frame(features: pd.DataFrame, model: str, predicted: np.ndarray) -> pd.DataFrame:
    result = features[
        [
            "sample_id",
            "product_code",
            "product_group",
            "is_core_product",
            "graph_year",
            "target_year",
            "split",
            "target_siri",
        ]
    ].copy()
    result.insert(0, "model", model)
    result = result.rename(columns={"graph_year": "train_year", "target_siri": "actual_siri"})
    result["predicted_siri"] = predicted.astype(float)
    result["error"] = result["predicted_siri"] - result["actual_siri"]
    return result[
        [
            "model",
            "split",
            "sample_id",
            "product_code",
            "product_group",
            "is_core_product",
            "train_year",
            "target_year",
            "actual_siri",
            "predicted_siri",
            "error",
        ]
    ]


def run_naive_baseline(features: pd.DataFrame) -> pd.DataFrame:
    return _prediction_frame(features, "naive", features["current_siri_score"].to_numpy(dtype=float))


def _standardize_train(X: np.ndarray, train_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train = X[train_mask]
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std[std == 0] = 1.0
    return (X - mean) / std, mean, std


def run_ridge_baseline(features: pd.DataFrame, ridge_alpha: float = 1.0) -> pd.DataFrame:
    X = features[RIDGE_FEATURE_COLUMNS].fillna(0.0).to_numpy(dtype=float)
    y = features["target_siri"].to_numpy(dtype=float)
    train_mask = features["split"].eq("train").to_numpy()
    if train_mask.sum() == 0:
        raise ValueError("Ridge baseline requires at least one training sample.")
    X_scaled, _, _ = _standardize_train(X, train_mask)
    X_design = np.column_stack([np.ones(len(X_scaled)), X_scaled])
    X_train = X_design[train_mask]
    y_train = y[train_mask]
    penalty = np.eye(X_train.shape[1]) * ridge_alpha
    penalty[0, 0] = 0.0
    beta = np.linalg.pinv(X_train.T @ X_train + penalty) @ X_train.T @ y_train
    predicted = X_design @ beta
    return _prediction_frame(features, "ridge", predicted)


def _spearman(actual: pd.Series, predicted: pd.Series) -> float:
    if len(actual) < 2:
        return math.nan
    actual_rank = actual.rank(method="average")
    predicted_rank = predicted.rank(method="average")
    corr = actual_rank.corr(predicted_rank)
    return float(corr) if pd.notna(corr) else math.nan


def _metrics_for(group: pd.DataFrame, sample_scope: str, uses_gdelt: bool) -> dict[str, object]:
    errors = group["predicted_siri"] - group["actual_siri"]
    return {
        "model": str(group["model"].iloc[0]) if not group.empty else "",
        "split": str(group["split"].iloc[0]) if not group.empty else "",
        "sample_scope": sample_scope,
        "mae": float(errors.abs().mean()) if not group.empty else math.nan,
        "rmse": float(np.sqrt((errors**2).mean())) if not group.empty else math.nan,
        "spearman_rank_corr": _spearman(group["actual_siri"], group["predicted_siri"]) if len(group) >= 2 else math.nan,
        "n_samples": int(len(group)),
        "n_products": int(group["product_code"].nunique()) if not group.empty else 0,
        "uses_gdelt": bool(uses_gdelt),
    }


def evaluate_predictions(predictions: pd.DataFrame, uses_gdelt: bool) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (model, split), group in predictions.groupby(["model", "split"], sort=True):
        rows.append(_metrics_for(group, "all_model_products", uses_gdelt))
        core = group.loc[group["is_core_product"].astype(bool)]
        if core.empty:
            rows.append(
                {
                    "model": model,
                    "split": split,
                    "sample_scope": "core4_model_products",
                    "mae": math.nan,
                    "rmse": math.nan,
                    "spearman_rank_corr": math.nan,
                    "n_samples": 0,
                    "n_products": 0,
                    "uses_gdelt": bool(uses_gdelt),
                }
            )
        else:
            rows.append(_metrics_for(core, "core4_model_products", uses_gdelt))
    return pd.DataFrame(rows)
