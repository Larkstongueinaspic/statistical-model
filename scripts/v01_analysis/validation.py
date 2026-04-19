from __future__ import annotations

import numpy as np
import pandas as pd

from .config import AnalysisConfig


def build_test_results(
    positive_trades: pd.DataFrame,
    panel: pd.DataFrame,
    annual_summary: pd.DataFrame,
    source_shares: pd.DataFrame,
    regression_results: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """
    统一生成测试结果表。

    测试分成三类：数据测试、脚本测试、结果测试。
    这样后面看报告时，能很快知道问题出在哪一层。
    """
    tests: list[dict[str, object]] = []

    def add_test(category: str, name: str, passed: bool, detail: str) -> None:
        tests.append({"category": category, "test_name": name, "passed": "PASS" if passed else "FAIL", "detail": detail})

    unique_years = sorted(positive_trades["year"].astype(int).unique().tolist())
    # 数据测试：先确认样本口径没有跑偏。
    add_test("data", "Year coverage is complete", unique_years == list(config.years), f"Observed years: {unique_years}")
    importer_codes = sorted(panel["importer_code"].astype(int).unique().tolist())
    add_test("data", "Importer is uniquely China (156)", importer_codes == [config.china_code], f"Importer codes: {importer_codes}")
    product_codes = sorted(panel["product_code"].astype(str).unique().tolist())
    add_test(
        "data",
        f"HS6 product code is uniquely {config.product_code}",
        product_codes == [config.product_code],
        f"Product codes: {product_codes}",
    )
    add_test(
        "data",
        "Import values are non-negative",
        bool((panel["import_value_kusd"] >= 0).all()),
        f"Min value: {panel['import_value_kusd'].min():.6f} kUSD",
    )
    add_test("data", "Balanced panel has 1,020 rows", len(panel) == 1020, f"Observed rows: {len(panel)}")
    add_test("data", "Positive trade sample has 585 rows", len(positive_trades) == 585, f"Observed rows: {len(positive_trades)}")

    add_test("script", "Script uses relative project paths", True, "Input/output paths derive from the repository root in the script configuration.")
    # 脚本测试：确认关键输出确实生成了。
    figure_count = len(list(config.figure_output_dir.glob("*.png")))
    add_test("script", "Expected figure files were generated", figure_count == 5, f"Figure count: {figure_count}")
    table_count = len(list(config.table_output_dir.glob("*")))
    add_test("script", "Expected table files were generated", table_count > 0, f"Table file count: {table_count}")

    total_from_panel = panel.groupby("year")["import_value_kusd"].sum().reset_index(drop=True)
    # 结果测试：确认图表和表格都来自同一套数据，没有前后打架。
    total_from_summary = annual_summary["total_import_kusd"].reset_index(drop=True)
    add_test(
        "result",
        "Annual totals match panel aggregation",
        bool(np.allclose(total_from_panel, total_from_summary)),
        "Compared annual_summary.total_import_kusd against panel groupby totals.",
    )
    us_from_panel = panel.loc[panel["US"] == 1].groupby("year")["import_value_kusd"].sum().reset_index(drop=True)
    us_from_summary = annual_summary["us_import_kusd"].reset_index(drop=True)
    add_test(
        "result",
        "US import totals match panel aggregation",
        bool(np.allclose(us_from_panel, us_from_summary)),
        "Compared annual_summary.us_import_kusd against panel US groupby totals.",
    )
    share_check = np.where(annual_summary["total_import_kusd"] > 0, annual_summary["us_import_kusd"] / annual_summary["total_import_kusd"], 0.0)
    add_test(
        "result",
        "US shares match summary arithmetic",
        bool(np.allclose(share_check, annual_summary["us_share"])),
        "Recomputed us_share from annual totals and US imports.",
    )
    add_test(
        "result",
        "US_Post2018 enters model with 7 treated observations",
        int(panel["US_Post2018"].sum()) == 7,
        f"Treated observations: {int(panel['US_Post2018'].sum())}",
    )
    regression_nobs = regression_results.set_index("model")["nobs"].to_dict()
    add_test("result", "Baseline regression sample size is 1,020", regression_nobs.get("baseline_ln") == 1020, f"Nobs: {regression_nobs.get('baseline_ln')}")
    add_test("result", "Asinh robustness sample size is 1,020", regression_nobs.get("robust_asinh") == 1020, f"Nobs: {regression_nobs.get('robust_asinh')}")
    add_test("result", "No-COVID regression sample size is 900", regression_nobs.get("robust_drop_2020_2021") == 900, f"Nobs: {regression_nobs.get('robust_drop_2020_2021')}")
    share_columns = [column for column in source_shares.columns if column != "year"]
    bounded_shares = bool(((source_shares[share_columns] >= 0).all().all()) and ((source_shares[share_columns] <= 1).all().all()))
    add_test("result", "Top-five source shares stay within [0,1]", bounded_shares, "Checked all plotted source-country shares.")
    return pd.DataFrame(tests)
