from __future__ import annotations

from .config import get_config
from .datasets import (
    build_annual_summary,
    build_balanced_panel,
    build_descriptive_stats,
    build_positive_trade_sample,
    load_country_codes,
    load_product_description,
)
from .models import run_all_regressions, write_model_outputs
from .plots import create_all_figures
from .storage import ensure_output_dirs, save_dataset, save_table
from .validation import build_test_results


def main() -> int:
    config = get_config()
    ensure_output_dirs(config)

    # 第 1 步：先把论文真正要用的最小原始样本抽出来。
    country_codes = load_country_codes(config)
    product_description = load_product_description(config)
    positive_trades, year_checks = build_positive_trade_sample(country_codes, product_description, config)

    # 第 2 步：先准备好所有分析数据，再做图和回归。
    panel = build_balanced_panel(positive_trades, product_description, config)
    annual_summary, source_shares = build_annual_summary(panel)
    descriptive_stats = build_descriptive_stats(panel, positive_trades)

    print("[2/4] Running regressions...", flush=True)
    # 第 3 步：跑基准回归和最小稳健性。
    regression_results, models = run_all_regressions(panel)

    print("[3/4] Writing datasets, tables, and figures...", flush=True)
    # 第 4 步：统一把中间数据、图和表写到 results/ 下面。
    save_dataset(positive_trades, "positive_trades_848620_china_2008_2024.csv", config)
    save_dataset(panel, "balanced_panel_848620_china_2008_2024.csv", config)
    save_dataset(annual_summary, "annual_summary_848620_china_2008_2024.csv", config)
    save_dataset(source_shares, "top5_source_shares_848620_china_2008_2024.csv", config)
    year_checks.to_csv(config.table_output_dir / "yearly_positive_trade_checks.csv", index=False)

    save_table(descriptive_stats, "descriptive_statistics_848620", config)
    save_table(regression_results, "regression_results_848620", config)
    save_table(source_shares, "top5_source_shares_848620", config)
    save_table(annual_summary, "annual_summary_848620", config)
    write_model_outputs(models, config)
    create_all_figures(annual_summary, source_shares, config)

    print("[4/4] Running validation checks...", flush=True)
    # 最后一步：把所有关键测试结果汇总成一张表，便于交付前自检。
    test_results = build_test_results(positive_trades, panel, annual_summary, source_shares, regression_results, config)
    save_table(test_results, "test_results_848620", config)

    print("Completed v0.1 analysis for HS848620.", flush=True)
    return 0
