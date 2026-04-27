from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import AnalysisConfig


PRODUCT_GROUPS = {
    "848620": "equipment",
    "854231": "integrated_circuit",
    "854232": "integrated_circuit",
    "854239": "integrated_circuit",
}


def load_country_codes(config: AnalysisConfig) -> pd.DataFrame:
    return pd.read_csv(
        config.data_dir / "country_codes_V202601.csv",
        dtype={
            "country_code": "int64",
            "country_name": "string",
            "country_iso2": "string",
            "country_iso3": "string",
        },
    )


def load_product_codes(config: AnalysisConfig) -> pd.DataFrame:
    product_codes = pd.read_csv(
        config.data_dir / "product_codes_HS07_V202601.csv",
        dtype={"code": "string", "description": "string"},
    )
    products = product_codes.loc[product_codes["code"].isin(config.candidate_product_codes)].copy()
    products["product_group"] = products["code"].map(PRODUCT_GROUPS).fillna("other")
    return products.rename(columns={"code": "product_code", "description": "product_description"})


def load_yearly_candidate_trades(year: int, config: AnalysisConfig) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    candidate_set = set(config.candidate_product_codes)
    for chunk in pd.read_csv(
        config.yearly_file(year),
        usecols=["t", "i", "j", "k", "v", "q"],
        dtype={
            "t": "int16",
            "i": "int32",
            "j": "int32",
            "k": "string",
            "v": "float64",
            "q": "float64",
        },
        na_values=[""],
        keep_default_na=True,
        chunksize=config.chunk_size,
    ):
        filtered = chunk.loc[(chunk["j"] == config.china_code) & (chunk["k"].isin(candidate_set))].copy()
        if not filtered.empty:
            frames.append(filtered)
    if not frames:
        return pd.DataFrame(
            columns=[
                "year",
                "exporter_code",
                "importer_code",
                "product_code",
                "import_value_kusd",
                "quantity_tons",
            ]
        )
    return pd.concat(frames, ignore_index=True).rename(
        columns={
            "t": "year",
            "i": "exporter_code",
            "j": "importer_code",
            "k": "product_code",
            "v": "import_value_kusd",
            "q": "quantity_tons",
        }
    )


def build_positive_trade_sample(
    country_codes: pd.DataFrame,
    products: pd.DataFrame,
    config: AnalysisConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    year_checks: list[dict[str, object]] = []
    country_lookup = country_codes[["country_code", "country_name", "country_iso3"]].rename(
        columns={
            "country_code": "exporter_code",
            "country_name": "exporter_name",
            "country_iso3": "exporter_iso3",
        }
    )

    for year in config.years:
        print(f"[1/6] Loading BACI year {year} for candidate products...", flush=True)
        year_df = load_yearly_candidate_trades(year, config)
        frames.append(year_df)
        for product_code in config.candidate_product_codes:
            product_year = year_df.loc[year_df["product_code"] == product_code]
            year_checks.append(
                {
                    "year": year,
                    "product_code": product_code,
                    "positive_trade_rows": int(len(product_year)),
                    "yearly_total_import_kusd": float(product_year["import_value_kusd"].sum())
                    if not product_year.empty
                    else 0.0,
                }
            )

    positive_trades = pd.concat(frames, ignore_index=True)
    positive_trades = positive_trades.merge(products, on="product_code", how="left")
    positive_trades = positive_trades.merge(country_lookup, on="exporter_code", how="left")
    positive_trades["importer_name"] = "China"
    positive_trades["importer_iso3"] = "CHN"
    positive_trades["product_group"] = positive_trades["product_group"].fillna(
        positive_trades["product_code"].map(PRODUCT_GROUPS)
    )
    sort_columns = ["product_code", "year", "exporter_code"]
    return positive_trades.sort_values(sort_columns, ignore_index=True), pd.DataFrame(year_checks)


def _format_source_list(rows: pd.DataFrame) -> str:
    parts = []
    for _, row in rows.iterrows():
        parts.append(f"{row['exporter_name']} {row['share'] * 100:.2f}%")
    return "; ".join(parts)


def build_candidate_feasibility(
    positive_trades: pd.DataFrame,
    products: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    product_year_totals = (
        positive_trades.groupby(["product_code", "year"], as_index=False)["import_value_kusd"]
        .sum()
        .rename(columns={"import_value_kusd": "total_import_kusd"})
    )
    us_year_totals = (
        positive_trades.loc[positive_trades["exporter_code"] == config.usa_code]
        .groupby(["product_code", "year"], as_index=False)["import_value_kusd"]
        .sum()
        .rename(columns={"import_value_kusd": "us_import_kusd"})
    )
    shares = product_year_totals.merge(us_year_totals, on=["product_code", "year"], how="left")
    shares["us_import_kusd"] = shares["us_import_kusd"].fillna(0.0)
    shares["us_share"] = np.where(
        shares["total_import_kusd"] > 0,
        shares["us_import_kusd"] / shares["total_import_kusd"],
        np.nan,
    )
    product_lookup = products.set_index("product_code")

    for product_code in config.candidate_product_codes:
        product_rows = positive_trades.loc[positive_trades["product_code"] == product_code].copy()
        observed_years = sorted(product_rows["year"].astype(int).unique().tolist())
        exporter_count = int(product_rows["exporter_code"].nunique())
        positive_rows = int(len(product_rows))
        us_positive_years = int(product_rows.loc[product_rows["exporter_code"] == config.usa_code, "year"].nunique())
        share_2017 = shares.loc[
            (shares["product_code"] == product_code) & (shares["year"] == 2017),
            "us_share",
        ]
        share_2024 = shares.loc[
            (shares["product_code"] == product_code) & (shares["year"] == 2024),
            "us_share",
        ]
        top_2024 = (
            product_rows.loc[product_rows["year"] == 2024]
            .groupby(["exporter_code", "exporter_name"], as_index=False)["import_value_kusd"]
            .sum()
            .sort_values("import_value_kusd", ascending=False)
            .head(5)
        )
        total_2024 = float(top_2024["import_value_kusd"].sum())
        product_total_2024 = float(
            product_rows.loc[product_rows["year"] == 2024, "import_value_kusd"].sum()
        )
        top_2024["share"] = np.where(
            product_total_2024 > 0,
            top_2024["import_value_kusd"] / product_total_2024,
            0.0,
        )
        metadata_exists = product_code in product_lookup.index
        keep = bool(
            metadata_exists
            and len(observed_years) >= 15
            and exporter_count >= 10
            and positive_rows >= 100
            and us_positive_years >= 1
        )
        rows.append(
            {
                "product_code": product_code,
                "product_group": PRODUCT_GROUPS.get(product_code, "other"),
                "metadata_exists": metadata_exists,
                "description": str(product_lookup.loc[product_code, "product_description"])
                if metadata_exists
                else "",
                "year_coverage": f"{min(observed_years)}-{max(observed_years)} ({len(observed_years)}/{len(config.years)})"
                if observed_years
                else "none",
                "exporter_count": exporter_count,
                "positive_trade_records": positive_rows,
                "us_positive_years": us_positive_years,
                "us_share_2017": round(float(share_2017.iloc[0]), 6) if not share_2017.empty else np.nan,
                "us_share_2024": round(float(share_2024.iloc[0]), 6) if not share_2024.empty else np.nan,
                "us_share_change_2017_2024_pp": round(float((share_2024.iloc[0] - share_2017.iloc[0]) * 100), 4)
                if (not share_2017.empty and not share_2024.empty)
                else np.nan,
                "top_2024_sources": _format_source_list(top_2024),
                "top5_2024_share": round(float(total_2024 / product_total_2024), 6) if product_total_2024 > 0 else np.nan,
                "selected_for_v02": keep,
                "selection_reason": "Passes coverage, scale, exporter, and US-exposure screens."
                if keep
                else "Excluded by coverage, scale, exporter, or US-exposure screen.",
            }
        )
    return pd.DataFrame(rows)


def selected_product_codes(feasibility: pd.DataFrame, config: AnalysisConfig) -> tuple[str, ...]:
    selected = feasibility.loc[feasibility["selected_for_v02"], "product_code"].astype(str).tolist()
    if config.candidate_product_codes[0] not in selected:
        selected.insert(0, config.candidate_product_codes[0])
    if len(selected) < 2:
        fallback = (
            feasibility.loc[~feasibility["product_code"].isin(selected)]
            .sort_values(["positive_trade_records", "exporter_count"], ascending=False)["product_code"]
            .astype(str)
            .head(2 - len(selected))
            .tolist()
        )
        selected.extend(fallback)
    return tuple(dict.fromkeys(selected))


def build_balanced_panel(
    positive_trades: pd.DataFrame,
    selected_products: tuple[str, ...],
    config: AnalysisConfig,
) -> pd.DataFrame:
    selected_trades = positive_trades.loc[positive_trades["product_code"].isin(selected_products)].copy()
    product_lookup = (
        selected_trades[["product_code", "product_description", "product_group"]]
        .drop_duplicates()
        .set_index("product_code")
    )
    exporter_lookup = (
        selected_trades[["exporter_code", "exporter_name", "exporter_iso3"]]
        .drop_duplicates()
        .sort_values("exporter_code")
    )
    index_frames: list[pd.DataFrame] = []
    for product_code, product_group in selected_trades.groupby("product_code"):
        exporters = sorted(product_group["exporter_code"].astype(int).unique().tolist())
        product_index = pd.MultiIndex.from_product(
            [[product_code], exporters, config.years],
            names=["product_code", "exporter_code", "year"],
        ).to_frame(index=False)
        index_frames.append(product_index)
    panel_index = pd.concat(index_frames, ignore_index=True)
    annual_values = selected_trades.groupby(["product_code", "exporter_code", "year"], as_index=False)[
        ["import_value_kusd", "quantity_tons"]
    ].sum()
    panel = (
        panel_index.merge(exporter_lookup, on="exporter_code", how="left")
        .merge(product_lookup.reset_index(), on="product_code", how="left")
        .merge(annual_values, on=["product_code", "exporter_code", "year"], how="left")
    )
    panel["import_value_kusd"] = panel["import_value_kusd"].fillna(0.0)
    panel["quantity_tons"] = panel["quantity_tons"].fillna(0.0)
    panel["importer_code"] = config.china_code
    panel["importer_name"] = "China"
    panel["importer_iso3"] = "CHN"
    panel["US"] = (panel["exporter_code"] == config.usa_code).astype(int)
    panel["Post2018"] = (panel["year"] >= 2018).astype(int)
    panel["Post2022"] = (panel["year"] >= 2022).astype(int)
    panel["Post2023"] = (panel["year"] >= 2023).astype(int)
    panel["US_Post2018"] = panel["US"] * panel["Post2018"]
    panel["US_Post2022"] = panel["US"] * panel["Post2022"]
    panel["US_Post2023"] = panel["US"] * panel["Post2023"]
    panel["Period_2018_2021"] = ((panel["year"] >= 2018) & (panel["year"] <= 2021)).astype(int)
    panel["Period_2022"] = (panel["year"] == 2022).astype(int)
    panel["Period_2023_2024"] = (panel["year"] >= 2023).astype(int)
    panel["US_Period_2018_2021"] = panel["US"] * panel["Period_2018_2021"]
    panel["US_Period_2022"] = panel["US"] * panel["Period_2022"]
    panel["US_Period_2023_2024"] = panel["US"] * panel["Period_2023_2024"]
    panel["ln_import_value"] = np.log(panel["import_value_kusd"] + 1.0)
    panel["asinh_import_value"] = np.arcsinh(panel["import_value_kusd"])
    totals = panel.groupby(["product_code", "year"], as_index=False)["import_value_kusd"].sum().rename(
        columns={"import_value_kusd": "product_year_total_kusd"}
    )
    panel = panel.merge(totals, on=["product_code", "year"], how="left")
    panel["import_share"] = np.where(
        panel["product_year_total_kusd"] > 0,
        panel["import_value_kusd"] / panel["product_year_total_kusd"],
        0.0,
    )
    panel["post2018_label"] = np.where(panel["Post2018"] == 1, "2018+", "pre-2018")
    return panel.sort_values(["product_code", "exporter_code", "year"], ignore_index=True)


def build_annual_product_summary(panel: pd.DataFrame) -> pd.DataFrame:
    total = panel.groupby(["product_code", "product_description", "product_group", "year"], as_index=False)[
        "import_value_kusd"
    ].sum()
    total = total.rename(columns={"import_value_kusd": "total_import_kusd"})
    us = (
        panel.loc[panel["US"] == 1]
        .groupby(["product_code", "year"], as_index=False)["import_value_kusd"]
        .sum()
        .rename(columns={"import_value_kusd": "us_import_kusd"})
    )
    exporters = (
        panel.loc[panel["import_value_kusd"] > 0]
        .groupby(["product_code", "year"], as_index=False)["exporter_code"]
        .nunique()
        .rename(columns={"exporter_code": "positive_exporter_count"})
    )
    annual = total.merge(us, on=["product_code", "year"], how="left").merge(
        exporters,
        on=["product_code", "year"],
        how="left",
    )
    annual["us_import_kusd"] = annual["us_import_kusd"].fillna(0.0)
    annual["positive_exporter_count"] = annual["positive_exporter_count"].fillna(0).astype(int)
    annual["us_share"] = np.where(
        annual["total_import_kusd"] > 0,
        annual["us_import_kusd"] / annual["total_import_kusd"],
        0.0,
    )
    hhi = (
        panel.assign(share_sq=panel["import_share"] ** 2)
        .groupby(["product_code", "year"], as_index=False)["share_sq"]
        .sum()
        .rename(columns={"share_sq": "hhi"})
    )
    return annual.merge(hhi, on=["product_code", "year"], how="left").sort_values(
        ["product_code", "year"],
        ignore_index=True,
    )


def build_top_2024_source_shares(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for product_code, group in panel.loc[panel["year"] == 2024].groupby("product_code"):
        total = float(group["import_value_kusd"].sum())
        top = (
            group.groupby(["product_code", "product_description", "product_group", "exporter_code", "exporter_name"], as_index=False)[
                "import_value_kusd"
            ]
            .sum()
            .sort_values("import_value_kusd", ascending=False)
            .head(8)
            .copy()
        )
        top["share"] = np.where(total > 0, top["import_value_kusd"] / total, 0.0)
        top["rank_2024"] = range(1, len(top) + 1)
        rows.append(top)
    return pd.concat(rows, ignore_index=True)


def build_top_source_shares_over_time(panel: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for product_code, group in panel.groupby("product_code"):
        top_exporters = (
            group.groupby(["exporter_code", "exporter_name"], as_index=False)["import_value_kusd"]
            .sum()
            .sort_values("import_value_kusd", ascending=False)
            .head(top_n)
        )
        top_codes = top_exporters["exporter_code"].tolist()
        shares = group.loc[group["exporter_code"].isin(top_codes), [
            "product_code",
            "year",
            "exporter_code",
            "exporter_name",
            "import_value_kusd",
            "product_year_total_kusd",
        ]].copy()
        shares["share"] = np.where(
            shares["product_year_total_kusd"] > 0,
            shares["import_value_kusd"] / shares["product_year_total_kusd"],
            0.0,
        )
        shares = shares.merge(
            top_exporters[["exporter_code"]].assign(top_rank=range(1, len(top_exporters) + 1)),
            on="exporter_code",
            how="left",
        )
        rows.append(shares)
    return pd.concat(rows, ignore_index=True).sort_values(["product_code", "top_rank", "year"], ignore_index=True)


def build_descriptive_stats(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = {"All selected products": panel}
    for product_code, group in panel.groupby("product_code"):
        groups[f"HS{product_code}"] = group
    metrics = [
        ("Observations", lambda df: len(df), "{:,.0f}"),
        ("Positive trade rows", lambda df: len(df.loc[df["import_value_kusd"] > 0]), "{:,.0f}"),
        ("Exporters", lambda df: df[["product_code", "exporter_code"]].drop_duplicates().shape[0], "{:,.0f}"),
        ("Years", lambda df: df["year"].nunique(), "{:,.0f}"),
        ("Mean import value (kUSD)", lambda df: df["import_value_kusd"].mean(), "{:,.2f}"),
        ("Median import value (kUSD)", lambda df: df["import_value_kusd"].median(), "{:,.2f}"),
        ("Std. dev. import value (kUSD)", lambda df: df["import_value_kusd"].std(), "{:,.2f}"),
        ("Max import value (kUSD)", lambda df: df["import_value_kusd"].max(), "{:,.2f}"),
        ("Mean import share", lambda df: df["import_share"].mean(), "{:,.6f}"),
    ]
    for metric_name, func, formatter in metrics:
        row = {"Metric": metric_name}
        for label, df in groups.items():
            value = func(df)
            if isinstance(value, (float, np.floating)) and math.isnan(value):
                row[label] = ""
            else:
                row[label] = formatter.format(value)
        rows.append(row)
    return pd.DataFrame(rows)


def build_main_exporter_panel(panel: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    keep_frames: list[pd.DataFrame] = []
    for product_code, group in panel.groupby("product_code"):
        top_2024 = (
            group.loc[group["year"] == 2024]
            .sort_values("import_value_kusd", ascending=False)["exporter_code"]
            .head(top_n)
            .astype(int)
            .tolist()
        )
        keep_codes = set(top_2024)
        keep_codes.add(842)
        keep_frames.append(group.loc[group["exporter_code"].isin(keep_codes)].copy())
    return pd.concat(keep_frames, ignore_index=True)
