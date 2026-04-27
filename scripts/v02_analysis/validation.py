from __future__ import annotations

import numpy as np
import pandas as pd

from .config import AnalysisConfig


def build_test_results(
    products: pd.DataFrame,
    positive_trades: pd.DataFrame,
    panel: pd.DataFrame,
    feasibility: pd.DataFrame,
    annual: pd.DataFrame,
    top_2024: pd.DataFrame,
    regression_tables: dict[str, pd.DataFrame],
    config: AnalysisConfig,
) -> pd.DataFrame:
    tests: list[dict[str, object]] = []

    def add_test(category: str, name: str, passed: bool, detail: str) -> None:
        tests.append({"category": category, "test_name": name, "passed": "PASS" if passed else "FAIL", "detail": detail})

    selected_products = panel["product_code"].astype(str).drop_duplicates().tolist()
    metadata_products = products["product_code"].astype(str).tolist()
    add_test(
        "data",
        "Selected products exist in BACI metadata",
        all(code in metadata_products for code in selected_products),
        f"Selected products: {selected_products}",
    )
    coverage = panel.groupby("product_code")["year"].nunique().to_dict()
    add_test(
        "data",
        "Each selected product has full panel year coverage",
        all(count == len(config.years) for count in coverage.values()),
        f"Year counts by product: {coverage}",
    )
    importer_codes = sorted(panel["importer_code"].astype(int).unique().tolist())
    add_test("data", "Importer is uniquely China (156)", importer_codes == [config.china_code], f"Importer codes: {importer_codes}")
    usa_counts = panel.loc[panel["exporter_code"] == config.usa_code].groupby("product_code")["year"].nunique().to_dict()
    add_test(
        "data",
        "USA exporter code 842 is present for each selected product",
        all(usa_counts.get(code, 0) == len(config.years) for code in selected_products),
        f"USA panel year counts: {usa_counts}",
    )
    add_test(
        "data",
        "Import values are non-negative",
        bool((panel["import_value_kusd"] >= 0).all()),
        f"Min value: {panel['import_value_kusd'].min():.6f} kUSD",
    )
    expected_rows = int(panel.groupby("product_code")["exporter_code"].nunique().sum() * len(config.years))
    add_test(
        "data",
        "Multi-product panel row count matches product-specific exporter-year expansion",
        len(panel) == expected_rows,
        f"Observed rows: {len(panel)}, expected rows: {expected_rows}",
    )
    add_test(
        "data",
        "Post2018/Post2022/Post2023 indicators are correct",
        bool(
            (panel["Post2018"].eq((panel["year"] >= 2018).astype(int))).all()
            and (panel["Post2022"].eq((panel["year"] >= 2022).astype(int))).all()
            and (panel["Post2023"].eq((panel["year"] >= 2023).astype(int))).all()
        ),
        "Recomputed policy indicators from year.",
    )
    add_test(
        "data",
        "Positive trade sample is restricted to China and candidate products",
        bool(
            positive_trades["importer_code"].eq(config.china_code).all()
            and positive_trades["product_code"].isin(config.candidate_product_codes).all()
        ),
        f"Positive rows: {len(positive_trades)}",
    )

    add_test(
        "script",
        "v0.2 output paths are versioned",
        str(config.output_dir).endswith("results/v02"),
        f"Output dir: {config.output_dir}",
    )
    figure_files = sorted(path.name for path in config.figure_output_dir.glob("*.png"))
    add_test("script", "Expected v0.2 figure files were generated", len(figure_files) >= 7, f"Figure files: {figure_files}")
    table_files = sorted(path.name for path in config.table_output_dir.glob("*.csv"))
    add_test("script", "Expected v0.2 table files were generated", len(table_files) >= 8, f"CSV table count: {len(table_files)}")
    add_test(
        "script",
        "v0.1 output directories are not used by v0.2 config",
        config.data_output_dir.parent == config.output_dir,
        f"Data output dir: {config.data_output_dir}",
    )

    panel_totals = panel.groupby(["product_code", "year"], as_index=False)["import_value_kusd"].sum().sort_values(
        ["product_code", "year"]
    )
    annual_totals = annual[["product_code", "year", "total_import_kusd"]].sort_values(["product_code", "year"])
    add_test(
        "result",
        "Annual product totals match panel aggregation",
        bool(np.allclose(panel_totals["import_value_kusd"], annual_totals["total_import_kusd"])),
        "Compared annual summary against panel groupby totals.",
    )
    us_panel = (
        panel.loc[panel["US"] == 1]
        .groupby(["product_code", "year"], as_index=False)["import_value_kusd"]
        .sum()
        .sort_values(["product_code", "year"])
    )
    us_annual = annual[["product_code", "year", "us_import_kusd"]].sort_values(["product_code", "year"])
    add_test(
        "result",
        "US product-year totals match panel aggregation",
        bool(np.allclose(us_panel["import_value_kusd"], us_annual["us_import_kusd"])),
        "Compared US annual summary against panel US groupby totals.",
    )
    share_recalc = np.where(annual["total_import_kusd"] > 0, annual["us_import_kusd"] / annual["total_import_kusd"], 0.0)
    add_test(
        "result",
        "US shares match annual summary arithmetic",
        bool(np.allclose(share_recalc, annual["us_share"])),
        "Recomputed us_share from annual totals.",
    )
    add_test(
        "result",
        "Top 2024 source shares stay within [0,1]",
        bool(((top_2024["share"] >= 0) & (top_2024["share"] <= 1)).all()),
        "Checked top source share bounds.",
    )
    policy_table = regression_tables["policy_stage_regression_results_v02"]
    add_test(
        "result",
        "Post2018/Post2022/Post2023 terms enter pooled policy model",
        set(["US_Post2018", "US_Post2022", "US_Post2023"]).issubset(set(policy_table["term"])),
        f"Terms: {policy_table['term'].tolist()}",
    )
    add_test(
        "result",
        "Pooled policy regression sample size is reasonable",
        int(policy_table["nobs"].max()) == len(panel),
        f"Regression nobs: {policy_table['nobs'].max()}, panel rows: {len(panel)}",
    )
    product_table = regression_tables["product_specific_regression_results_v02"]
    add_test(
        "result",
        "Product-specific regressions cover all selected products",
        set(product_table["sample"].str.replace("HS", "", regex=False)) == set(selected_products),
        f"Product regression samples: {sorted(product_table['sample'].unique().tolist())}",
    )
    failed_feasibility = feasibility.loc[~feasibility["metadata_exists"], "product_code"].astype(str).tolist()
    add_test(
        "result",
        "Candidate feasibility table records metadata status",
        len(failed_feasibility) == 0,
        "All candidate products found in metadata.",
    )
    return pd.DataFrame(tests)
