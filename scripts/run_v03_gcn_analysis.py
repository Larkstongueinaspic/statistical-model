from __future__ import annotations

import argparse

import pandas as pd

from v03_gcn.baselines import evaluate_predictions, run_naive_baseline, run_ridge_baseline
from v03_gcn.config import GcnConfig
from v03_gcn.pipeline import run_baci_only_pipeline, run_extended_baci_pipeline, run_panel_pipeline
from v03_gcn.plots import plot_actual_vs_predicted
from v03_gcn.reports import write_summary
from v03_gcn.storage import ensure_output_dirs, save_dataset, save_table
from v03_gcn.validation import build_validation_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v0.3 dynamic GCN/GDELT extension outputs.")
    parser.add_argument("--graph-features", type=str, default="", help="Existing graph_level_features_v03.csv to score.")
    parser.add_argument("--baci-only", action="store_true", help="Run without GDELT features and mark outputs explicitly.")
    parser.add_argument("--gdelt-events", type=str, default="", help="GDELT event CSV to aggregate into country-year pressure.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = GcnConfig(disable_gdelt=args.baci_only, allow_baci_only=args.baci_only)
    uses_gdelt = bool(args.gdelt_events) and not args.baci_only
    ensure_output_dirs(config)
    if args.graph_features:
        features = pd.read_csv(args.graph_features)
        naive = run_naive_baseline(features)
        ridge = run_ridge_baseline(features)
        predictions = pd.concat([naive, ridge], ignore_index=True)
        metrics = evaluate_predictions(predictions, uses_gdelt=uses_gdelt)
        product_pool = pd.DataFrame()
        graph_index = pd.DataFrame()
    else:
        if not args.baci_only and not args.gdelt_events:
            raise SystemExit("Pass --baci-only for BACI-only fallback or --gdelt-events PATH for GDELT-enabled output.")
        gdelt_events = pd.read_csv(args.gdelt_events) if uses_gdelt else None
        if config.baci_dir.exists():
            outputs = run_extended_baci_pipeline(config, gdelt_events=gdelt_events)
        else:
            panel_path = config.root / "results" / "v02" / "data" / "balanced_panel_multi_product_china_2008_2024.csv"
            if not panel_path.exists():
                raise SystemExit(f"Missing BACI directory and existing panel: {panel_path}")
            panel = pd.read_csv(panel_path)
            if args.baci_only:
                outputs = run_baci_only_pipeline(panel, config)
            else:
                outputs = run_panel_pipeline(panel, config, gdelt_events=gdelt_events)
        if not outputs.product_pool.empty:
            save_dataset(outputs.product_pool, "gcn_product_pool_v03.csv", config)
        if not outputs.positive_trades.empty:
            save_dataset(outputs.positive_trades, "positive_trades_v03_gcn.csv", config)
        if not outputs.balanced_panel.empty:
            save_dataset(outputs.balanced_panel, "balanced_panel_v03_gcn.csv", config)
        if not outputs.country_crosswalk.empty:
            save_dataset(outputs.country_crosswalk, "country_code_crosswalk_v03.csv", config)
        save_dataset(outputs.siri_targets, "siri_targets_v03.csv", config)
        save_dataset(outputs.gdelt_pressure, "gdelt_pressure_by_country_year.csv", config)
        save_dataset(outputs.graph_index, "graph_samples_v03.csv", config)
        save_dataset(outputs.graph_features, "graph_level_features_v03.csv", config)
        predictions = outputs.predictions
        metrics = outputs.metrics
        product_pool = outputs.product_pool
        graph_index = outputs.graph_index
    save_dataset(predictions, "gcn_predictions.csv", config)
    save_table(metrics, "gcn_metrics.csv", config)
    validation = build_validation_results(product_pool, graph_index, metrics, config, uses_gdelt=uses_gdelt)
    save_table(validation, "validation_v03_gcn.csv", config)
    plot_actual_vs_predicted(predictions, config)
    write_summary(metrics, validation, config, uses_gdelt=uses_gdelt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
