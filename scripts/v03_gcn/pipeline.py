from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .baselines import evaluate_predictions, run_naive_baseline, run_ridge_baseline
from .config import GcnConfig
from .siri_targets import build_siri_targets
from .trade_graphs import build_graph_level_features, build_graph_samples


@dataclass(frozen=True)
class PipelineOutputs:
    siri_targets: pd.DataFrame
    gdelt_pressure: pd.DataFrame
    graph_index: pd.DataFrame
    graph_features: pd.DataFrame
    predictions: pd.DataFrame
    metrics: pd.DataFrame


def build_zero_gdelt_pressure(panel: pd.DataFrame, config: GcnConfig) -> pd.DataFrame:
    exporters = (
        panel[["exporter_code", "exporter_iso3"]]
        .drop_duplicates()
        .assign(gdelt_country_code=lambda df: df["exporter_iso3"].fillna(""))
    )
    years = pd.DataFrame({"year": list(config.years)})
    result = exporters.merge(years, how="cross")
    result["gdelt_event_count"] = 0
    result["gdelt_avg_goldstein"] = 0.0
    result["gdelt_negative_goldstein_sum"] = 0.0
    result["gdelt_mentions"] = 0
    result["gdelt_avg_tone"] = 0.0
    result["gdelt_pressure_score"] = 0.0
    result["gdelt_filter_mode"] = "disabled_gdelt"
    return result


def run_baci_only_pipeline(panel: pd.DataFrame, config: GcnConfig) -> PipelineOutputs:
    if not (config.disable_gdelt and config.allow_baci_only):
        raise ValueError("BACI-only pipeline requires disable_gdelt=True and allow_baci_only=True.")
    siri_targets = build_siri_targets(panel)
    gdelt_pressure = build_zero_gdelt_pressure(panel, config)
    samples, graph_index = build_graph_samples(panel, siri_targets, gdelt_pressure, config)
    graph_features = build_graph_level_features(samples)
    if graph_features.empty:
        predictions = pd.DataFrame()
        metrics = pd.DataFrame()
    else:
        naive = run_naive_baseline(graph_features)
        ridge = run_ridge_baseline(graph_features)
        predictions = pd.concat([naive, ridge], ignore_index=True)
        metrics = evaluate_predictions(predictions, uses_gdelt=False)
    return PipelineOutputs(
        siri_targets=siri_targets,
        gdelt_pressure=gdelt_pressure,
        graph_index=graph_index,
        graph_features=graph_features,
        predictions=predictions,
        metrics=metrics,
    )
