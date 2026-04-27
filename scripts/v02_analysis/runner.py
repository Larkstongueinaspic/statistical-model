from __future__ import annotations

import pandas as pd

from .config import get_config
from .datasets import (
    build_annual_product_summary,
    build_balanced_panel,
    build_candidate_feasibility,
    build_descriptive_stats,
    build_main_exporter_panel,
    build_positive_trade_sample,
    build_top_2024_source_shares,
    build_top_source_shares_over_time,
    load_country_codes,
    load_product_codes,
    selected_product_codes,
)
from .models import run_all_regressions, write_model_outputs
from .plots import create_all_figures, plot_siri_trend
from .risk_index import build_siri_outputs
from .reports import write_abstract, write_summary
from .storage import ensure_output_dirs, save_dataset, save_table
from .validation import build_siri_test_results, build_test_results, write_siri_validation_log


def main() -> int:
    config = get_config()
    ensure_output_dirs(config)

    country_codes = load_country_codes(config)
    products = load_product_codes(config)
    positive_trades, year_checks = build_positive_trade_sample(country_codes, products, config)
    feasibility = build_candidate_feasibility(positive_trades, products, config)
    selected_products = selected_product_codes(feasibility, config)

    print(f"[2/6] Selected v0.2 products: {', '.join(selected_products)}", flush=True)
    panel = build_balanced_panel(positive_trades, selected_products, config)
    annual = build_annual_product_summary(panel)
    top_2024 = build_top_2024_source_shares(panel)
    top_source_shares = build_top_source_shares_over_time(panel)
    descriptive_stats = build_descriptive_stats(panel)
    main_exporter_panel = build_main_exporter_panel(panel)
    siri_index, siri_ranking, siri_sensitivity = build_siri_outputs(panel, target_year=2024)

    print("[3/6] Running v0.2 regressions...", flush=True)
    regression_tables, models = run_all_regressions(panel, main_exporter_panel, config)

    print("[4/6] Writing v0.2 datasets, tables, and figures...", flush=True)
    save_dataset(positive_trades, "positive_trades_candidate_products_china_2008_2024.csv", config)
    save_dataset(panel, "balanced_panel_multi_product_china_2008_2024.csv", config)
    save_dataset(annual, "annual_product_summary_multi_product_china_2008_2024.csv", config)
    save_dataset(top_2024, "top_2024_source_shares_multi_product_china.csv", config)
    save_dataset(top_source_shares, "top_source_shares_over_time_multi_product_china.csv", config)
    save_dataset(main_exporter_panel, "main_exporter_panel_top10_2024_sources_china_2008_2024.csv", config)
    save_dataset(siri_index, "siri_index_by_product_year_v02.csv", config)
    year_checks.to_csv(config.table_output_dir / "yearly_positive_trade_checks_v02.csv", index=False)

    save_table(feasibility, "candidate_product_feasibility_v02", config)
    save_table(descriptive_stats, "descriptive_statistics_v02", config)
    save_table(annual, "annual_product_summary_v02", config)
    save_table(top_2024, "top_2024_source_shares_v02", config)
    save_table(top_source_shares, "top_source_shares_over_time_v02", config)
    save_table(siri_index, "siri_index_by_product_year_v02", config)
    save_table(siri_ranking, "siri_ranking_2024_v02", config)
    save_table(siri_sensitivity, "siri_weight_sensitivity_v02", config)
    for stem, table in regression_tables.items():
        save_table(table, stem, config)
    write_model_outputs(models, config)
    create_all_figures(annual, top_2024, config)
    plot_siri_trend(siri_index, config)

    print("[5/6] Running v0.2 validation checks...", flush=True)
    test_results = build_test_results(
        products,
        positive_trades,
        panel,
        feasibility,
        annual,
        top_2024,
        regression_tables,
        config,
    )
    siri_test_results = build_siri_test_results(siri_index, siri_ranking, siri_sensitivity, config)
    test_results = pd.concat([test_results, siri_test_results], ignore_index=True)
    save_table(test_results, "test_results_v02", config)
    write_siri_validation_log(siri_index, config)

    print("[6/6] Writing v0.2 summary and abstract...", flush=True)
    write_summary(selected_products, annual, top_2024, regression_tables, siri_ranking, config)
    write_abstract(selected_products, panel, annual, regression_tables, siri_ranking, config)

    print("Completed v0.2 multi-product analysis.", flush=True)
    return 0
