from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .baselines import evaluate_predictions, run_naive_baseline, run_ridge_baseline
from .baci import (
    build_balanced_panel,
    build_positive_trade_sample,
    build_product_coverage,
    load_country_codes,
    load_product_codes,
)
from .config import GcnConfig
from .gdelt import aggregate_gdelt_pressure
from .product_pool import build_country_crosswalk, build_product_pool
from .siri_targets import build_siri_targets
from .training import run_numpy_gcn_regressor
from .trade_graphs import build_graph_level_features, build_graph_samples


@dataclass(frozen=True)
class PipelineOutputs:
    product_pool: pd.DataFrame
    positive_trades: pd.DataFrame
    balanced_panel: pd.DataFrame
    country_crosswalk: pd.DataFrame
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


def _panel_country_crosswalk(panel: pd.DataFrame) -> pd.DataFrame:
    exporters = panel[["exporter_code", "exporter_iso3"]].drop_duplicates().copy()
    if "exporter_name" in panel.columns:
        names = panel[["exporter_code", "exporter_name"]].drop_duplicates("exporter_code")
        exporters = exporters.merge(names, on="exporter_code", how="left")
    else:
        exporters["exporter_name"] = ""
    return build_country_crosswalk(exporters)


def _score_samples(samples, graph_features: pd.DataFrame, uses_gdelt: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    if graph_features.empty:
        return pd.DataFrame(), pd.DataFrame()
    naive = run_naive_baseline(graph_features)
    ridge = run_ridge_baseline(graph_features)
    gcn_numpy = run_numpy_gcn_regressor(samples)
    predictions = pd.concat([naive, ridge, gcn_numpy], ignore_index=True)
    metrics = evaluate_predictions(predictions, uses_gdelt=uses_gdelt)
    return predictions, metrics


def run_panel_pipeline(
    panel: pd.DataFrame,
    config: GcnConfig,
    gdelt_events: pd.DataFrame | None = None,
) -> PipelineOutputs:
    uses_gdelt = gdelt_events is not None and not config.disable_gdelt
    country_crosswalk = _panel_country_crosswalk(panel)
    if gdelt_events is None:
        if not (config.disable_gdelt and config.allow_baci_only):
            raise ValueError("Pass GDELT events or set disable_gdelt=True and allow_baci_only=True.")
        gdelt_pressure = build_zero_gdelt_pressure(panel, config)
    elif config.disable_gdelt:
        raise ValueError("GDELT events were provided while disable_gdelt=True.")
    else:
        gdelt_pressure = aggregate_gdelt_pressure(gdelt_events, country_crosswalk, config.years, config)
    siri_targets = build_siri_targets(panel)
    samples, graph_index = build_graph_samples(panel, siri_targets, gdelt_pressure, config)
    graph_features = build_graph_level_features(samples)
    predictions, metrics = _score_samples(samples, graph_features, uses_gdelt=uses_gdelt)
    return PipelineOutputs(
        product_pool=pd.DataFrame(),
        positive_trades=pd.DataFrame(),
        balanced_panel=panel,
        country_crosswalk=country_crosswalk,
        siri_targets=siri_targets,
        gdelt_pressure=gdelt_pressure,
        graph_index=graph_index,
        graph_features=graph_features,
        predictions=predictions,
        metrics=metrics,
    )


def run_baci_only_pipeline(panel: pd.DataFrame, config: GcnConfig) -> PipelineOutputs:
    return run_panel_pipeline(panel, config, gdelt_events=None)


def run_extended_baci_pipeline(config: GcnConfig, gdelt_events: pd.DataFrame | None = None) -> PipelineOutputs:
    if not config.baci_dir.exists():
        raise FileNotFoundError(f"Missing BACI directory: {config.baci_dir}")
    country_codes = load_country_codes(config)
    product_codes = load_product_codes(config)
    positive, _ = build_positive_trade_sample(country_codes, product_codes, config)
    coverage = build_product_coverage(positive, config)
    product_pool = build_product_pool(product_codes, coverage, config)
    selected_products = tuple(
        product_pool.loc[product_pool["model_status"].isin(["model", "report_only"]), "product_code"].astype(str)
    )
    panel = build_balanced_panel(positive, selected_products, config)
    outputs = run_panel_pipeline(panel, config, gdelt_events=gdelt_events)
    return PipelineOutputs(
        product_pool=product_pool,
        positive_trades=positive,
        balanced_panel=panel,
        country_crosswalk=outputs.country_crosswalk,
        siri_targets=outputs.siri_targets,
        gdelt_pressure=outputs.gdelt_pressure,
        graph_index=outputs.graph_index,
        graph_features=outputs.graph_features,
        predictions=outputs.predictions,
        metrics=outputs.metrics,
    )
