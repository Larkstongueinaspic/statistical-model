from __future__ import annotations

import argparse

import pandas as pd

from v03_gcn.baselines import evaluate_predictions, run_naive_baseline, run_ridge_baseline
from v03_gcn.config import GcnConfig
from v03_gcn.plots import plot_actual_vs_predicted
from v03_gcn.reports import write_summary
from v03_gcn.storage import ensure_output_dirs, save_dataset, save_table
from v03_gcn.validation import build_validation_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v0.3 dynamic GCN/GDELT extension outputs.")
    parser.add_argument("--graph-features", type=str, default="", help="Existing graph_level_features_v03.csv to score.")
    parser.add_argument("--baci-only", action="store_true", help="Run without GDELT features and mark outputs explicitly.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = GcnConfig(disable_gdelt=args.baci_only, allow_baci_only=args.baci_only)
    ensure_output_dirs(config)
    if not args.graph_features:
        raise SystemExit(
            "v0.3 runner needs graph-level features. Build BACI/GDELT inputs first or pass --graph-features."
        )
    features = pd.read_csv(args.graph_features)
    naive = run_naive_baseline(features)
    ridge = run_ridge_baseline(features)
    predictions = pd.concat([naive, ridge], ignore_index=True)
    metrics = evaluate_predictions(predictions, uses_gdelt=not args.baci_only)
    save_dataset(predictions, "gcn_predictions.csv", config)
    save_table(metrics, "gcn_metrics.csv", config)
    validation = build_validation_results(pd.DataFrame(), pd.DataFrame(), metrics, config, uses_gdelt=not args.baci_only)
    save_table(validation, "validation_v03_gcn.csv", config)
    plot_actual_vs_predicted(predictions, config)
    write_summary(metrics, validation, config, uses_gdelt=not args.baci_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
