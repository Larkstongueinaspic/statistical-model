from __future__ import annotations

import numpy as np
import pandas as pd

from .config import AnalysisConfig


def build_siri_test_results(
    siri_index: pd.DataFrame,
    siri_ranking: pd.DataFrame,
    siri_sensitivity: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    tests: list[dict[str, object]] = []

    def add_test(category: str, name: str, passed: bool, detail: str) -> None:
        tests.append({"category": category, "test_name": name, "passed": "PASS" if passed else "FAIL", "detail": detail})

    expected_rows = len(config.candidate_product_codes) * len(config.years)
    required_columns = {
        "product_code",
        "year",
        "total_import_value_kusd",
        "concentration_raw",
        "policy_exposure_raw",
        "alternative_insufficiency_raw",
        "structural_volatility_raw",
        "concentration_norm",
        "policy_exposure_norm",
        "alternative_insufficiency_norm",
        "structural_volatility_norm",
        "siri_score",
        "siri_score_policy_weighted",
    }
    ranking_columns = {
        "rank",
        "product_code",
        "product_name",
        "year",
        "siri_score",
        "siri_score_policy_weighted",
        "rank_policy_weighted",
        "rank_change",
    }
    sensitivity_columns = {
        "product_code",
        "product_name",
        "baseline_rank",
        "policy_weighted_rank",
        "rank_change",
        "baseline_siri_score",
        "policy_weighted_siri_score",
    }

    add_test("siri", "SIRI output has required columns", required_columns.issubset(siri_index.columns), f"Columns: {siri_index.columns.tolist()}")
    add_test(
        "siri",
        "SIRI product-year row count matches selected products",
        len(siri_index) == expected_rows,
        f"Observed rows: {len(siri_index)}, expected rows: {expected_rows}",
    )
    add_test(
        "siri",
        "SIRI years cover configured range",
        set(siri_index["year"].astype(int)) == set(config.years),
        f"Years: {sorted(siri_index['year'].unique().tolist())}",
    )
    coverage = siri_index.groupby("product_code")["year"].nunique().to_dict()
    add_test(
        "siri",
        "Each SIRI product covers every configured year",
        all(count == len(config.years) for count in coverage.values()),
        f"Coverage: {coverage}",
    )
    add_test(
        "siri",
        "SIRI scores stay within 0-100",
        bool(((siri_index["siri_score"] >= 0) & (siri_index["siri_score"] <= 100)).all()),
        "Checked baseline SIRI score bounds.",
    )
    add_test(
        "siri",
        "Policy-weighted SIRI scores stay within 0-100",
        bool(((siri_index["siri_score_policy_weighted"] >= 0) & (siri_index["siri_score_policy_weighted"] <= 100)).all()),
        "Checked policy-weighted SIRI score bounds.",
    )
    norm_columns = [column for column in siri_index.columns if column.endswith("_norm")]
    add_test(
        "siri",
        "SIRI normalized components stay within 0-1",
        bool(((siri_index[norm_columns] >= 0) & (siri_index[norm_columns] <= 1)).all().all()),
        f"Norm columns: {norm_columns}",
    )
    add_test(
        "siri",
        "SIRI required fields are non-missing",
        bool(siri_index[list(required_columns)].notna().all().all()),
        "Checked required fields for missing values.",
    )
    add_test("siri", "SIRI ranking has required columns", ranking_columns.issubset(siri_ranking.columns), f"Columns: {siri_ranking.columns.tolist()}")
    add_test(
        "siri",
        "SIRI ranking covers all selected products",
        len(siri_ranking) == len(config.candidate_product_codes),
        f"Rows: {len(siri_ranking)}",
    )
    add_test(
        "siri",
        "SIRI ranking product set matches configured products",
        set(siri_ranking["product_code"].astype(str)) == set(config.candidate_product_codes),
        f"Products: {sorted(siri_ranking['product_code'].astype(str).tolist())}",
    )
    add_test(
        "siri",
        "SIRI ranking ranks are unique",
        bool(siri_ranking["rank"].is_unique and siri_ranking["rank_policy_weighted"].is_unique),
        "Checked baseline and policy-weighted ranks.",
    )
    add_test("siri", "SIRI sensitivity has required columns", sensitivity_columns.issubset(siri_sensitivity.columns), f"Columns: {siri_sensitivity.columns.tolist()}")
    add_test(
        "siri",
        "SIRI sensitivity covers all selected products",
        len(siri_sensitivity) == len(config.candidate_product_codes),
        f"Rows: {len(siri_sensitivity)}",
    )
    add_test(
        "siri",
        "SIRI sensitivity product set matches configured products",
        set(siri_sensitivity["product_code"].astype(str)) == set(config.candidate_product_codes),
        f"Products: {sorted(siri_sensitivity['product_code'].astype(str).tolist())}",
    )
    return pd.DataFrame(tests)


def build_siri_validation_log(siri_index: pd.DataFrame) -> str:
    zero_total_rows = int((siri_index["total_import_value_kusd"] == 0).sum())
    constant_norm_dimensions = []
    min_max_lines = []
    for component in ["concentration", "policy_exposure", "alternative_insufficiency", "structural_volatility"]:
        raw = f"{component}_raw"
        raw_min = float(siri_index[raw].min())
        raw_max = float(siri_index[raw].max())
        if raw_min == raw_max:
            constant_norm_dimensions.append(raw)
        min_max_lines.append(f"- {raw}: min={raw_min:.6f}, max={raw_max:.6f}")
    missing_or_zero_us_rows = int((siri_index["policy_exposure_raw"] == 0).sum())
    return "\n".join(
        [
            "# SIRI validation-v0.2",
            "",
            f"- Rows: {len(siri_index)}",
            f"- Zero total product-year rows: {zero_total_rows}",
            f"- Product-year rows with missing USA record or zero US policy exposure: {missing_or_zero_us_rows}",
            f"- Raw dimensions with min=max: {constant_norm_dimensions if constant_norm_dimensions else 'none'}",
            "- Raw component ranges:",
            *min_max_lines,
            "",
        ]
    )


def write_siri_validation_log(siri_index: pd.DataFrame, config: AnalysisConfig) -> None:
    target = config.docs_output_dir / "siri_validation_v0.2.md"
    target.write_text(build_siri_validation_log(siri_index), encoding="utf-8")


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
