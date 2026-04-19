from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import AnalysisConfig


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


def load_product_description(config: AnalysisConfig) -> str:
    product_codes = pd.read_csv(
        config.data_dir / "product_codes_HS07_V202601.csv",
        dtype={"code": "string", "description": "string"},
    )
    match = product_codes.loc[product_codes["code"] == config.product_code, "description"]
    if match.empty:
        raise ValueError(f"Product code {config.product_code} not found in BACI metadata.")
    return str(match.iloc[0])


def load_yearly_positive_trades(year: int, config: AnalysisConfig) -> pd.DataFrame:
    """
    Read one BACI year in chunks and keep only the China-import / target-product rows.

    BACI yearly files are large enough that full-file reads are wasteful for this v0.1 task.
    """
    frames: list[pd.DataFrame] = []
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
        filtered = chunk.loc[(chunk["j"] == config.china_code) & (chunk["k"] == config.product_code)].copy()
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

    year_df = pd.concat(frames, ignore_index=True)
    return year_df.rename(
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
    product_description: str,
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
        print(f"[1/4] Loading BACI year {year}...", flush=True)
        year_df = load_yearly_positive_trades(year, config)
        frames.append(year_df)
        year_checks.append(
            {
                "year": year,
                "positive_trade_rows": int(len(year_df)),
                "yearly_total_import_kusd": float(year_df["import_value_kusd"].sum()) if not year_df.empty else 0.0,
            }
        )

    positive_trades = pd.concat(frames, ignore_index=True)
    positive_trades["product_description"] = product_description
    positive_trades = positive_trades.merge(country_lookup, on="exporter_code", how="left")
    positive_trades["importer_name"] = "China"
    positive_trades["importer_iso3"] = "CHN"
    positive_trades = positive_trades.sort_values(["year", "exporter_code"], ignore_index=True)
    return positive_trades, pd.DataFrame(year_checks)


def build_balanced_panel(
    positive_trades: pd.DataFrame,
    product_description: str,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """
    Expand the sparse trade flows to a balanced exporter-year panel.

    Missing exporter-year combinations are set to zero so the DID specification
    uses a common sample window for treated and control exporters.
    """
    exporter_lookup = (
        positive_trades[["exporter_code", "exporter_name", "exporter_iso3"]]
        .drop_duplicates()
        .sort_values("exporter_code")
        .reset_index(drop=True)
    )
    panel_index = pd.MultiIndex.from_product(
        [exporter_lookup["exporter_code"].tolist(), config.years],
        names=["exporter_code", "year"],
    ).to_frame(index=False)
    annual_values = positive_trades.groupby(["exporter_code", "year"], as_index=False)[
        ["import_value_kusd", "quantity_tons"]
    ].sum()
    panel = panel_index.merge(exporter_lookup, on="exporter_code", how="left").merge(
        annual_values,
        on=["exporter_code", "year"],
        how="left",
    )
    panel["import_value_kusd"] = panel["import_value_kusd"].fillna(0.0)
    panel["quantity_tons"] = panel["quantity_tons"].fillna(0.0)
    panel["importer_code"] = config.china_code
    panel["importer_name"] = "China"
    panel["importer_iso3"] = "CHN"
    panel["product_code"] = config.product_code
    panel["product_description"] = product_description
    panel["US"] = (panel["exporter_code"] == config.usa_code).astype(int)
    panel["Post2018"] = (panel["year"] >= 2018).astype(int)
    panel["US_Post2018"] = panel["US"] * panel["Post2018"]
    panel["ln_import_value"] = np.log(panel["import_value_kusd"] + 1.0)
    panel["asinh_import_value"] = np.arcsinh(panel["import_value_kusd"])
    return panel.sort_values(["exporter_code", "year"], ignore_index=True)


def build_annual_summary(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    annual_total = panel.groupby("year", as_index=False)["import_value_kusd"].sum().rename(
        columns={"import_value_kusd": "total_import_kusd"}
    )
    annual_us = (
        panel.loc[panel["US"] == 1]
        .groupby("year", as_index=False)["import_value_kusd"]
        .sum()
        .rename(columns={"import_value_kusd": "us_import_kusd"})
    )
    annual_exporters = (
        panel.loc[panel["import_value_kusd"] > 0]
        .groupby("year", as_index=False)["exporter_code"]
        .nunique()
        .rename(columns={"exporter_code": "positive_exporter_count"})
    )
    annual_summary = annual_total.merge(annual_us, on="year", how="left").merge(annual_exporters, on="year", how="left")
    annual_summary["us_import_kusd"] = annual_summary["us_import_kusd"].fillna(0.0)
    annual_summary["positive_exporter_count"] = annual_summary["positive_exporter_count"].fillna(0).astype(int)
    annual_summary["us_share"] = np.where(
        annual_summary["total_import_kusd"] > 0,
        annual_summary["us_import_kusd"] / annual_summary["total_import_kusd"],
        0.0,
    )

    hhi_rows: list[dict[str, float | int]] = []
    for year, group in panel.groupby("year"):
        total = float(group["import_value_kusd"].sum())
        shares = group["import_value_kusd"] / total if total > 0 else 0.0
        hhi_rows.append({"year": int(year), "hhi": float((shares**2).sum()) if total > 0 else 0.0})
    annual_summary = annual_summary.merge(pd.DataFrame(hhi_rows), on="year", how="left")

    top_exporters = (
        panel.groupby(["exporter_code", "exporter_name"], as_index=False)["import_value_kusd"]
        .sum()
        .sort_values("import_value_kusd", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )
    top_codes = top_exporters["exporter_code"].tolist()
    source_shares = (
        panel.loc[panel["exporter_code"].isin(top_codes)]
        .pivot_table(index="year", columns="exporter_name", values="import_value_kusd", aggfunc="sum")
        .fillna(0.0)
        .reset_index()
    )
    source_shares = source_shares.merge(annual_summary[["year", "total_import_kusd"]], on="year", how="left")
    share_columns = [column for column in source_shares.columns if column not in {"year", "total_import_kusd"}]
    for column in share_columns:
        source_shares[column] = np.where(
            source_shares["total_import_kusd"] > 0,
            source_shares[column] / source_shares["total_import_kusd"],
            0.0,
        )
    ordered_columns = ["year"] + top_exporters["exporter_name"].tolist()
    return annual_summary, source_shares[ordered_columns]


def build_descriptive_stats(panel: pd.DataFrame, positive_trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_lookup = {
        "Overall": panel,
        "US": panel.loc[panel["US"] == 1],
        "Non-US": panel.loc[panel["US"] == 0],
    }
    metrics = [
        ("Observations", lambda df: len(df), "{:,.0f}"),
        ("Positive trade rows", lambda df: len(df.loc[df["import_value_kusd"] > 0]), "{:,.0f}"),
        ("Exporters", lambda df: df["exporter_code"].nunique(), "{:,.0f}"),
        ("Years", lambda df: df["year"].nunique(), "{:,.0f}"),
        ("Mean import value (kUSD)", lambda df: df["import_value_kusd"].mean(), "{:,.2f}"),
        ("Median import value (kUSD)", lambda df: df["import_value_kusd"].median(), "{:,.2f}"),
        ("Std. dev. import value (kUSD)", lambda df: df["import_value_kusd"].std(), "{:,.2f}"),
        ("Min import value (kUSD)", lambda df: df["import_value_kusd"].min(), "{:,.2f}"),
        ("Max import value (kUSD)", lambda df: df["import_value_kusd"].max(), "{:,.2f}"),
        ("Mean ln(import+1)", lambda df: df["ln_import_value"].mean(), "{:,.4f}"),
    ]

    for metric_name, func, formatter in metrics:
        row = {"Metric": metric_name}
        for label, df in group_lookup.items():
            value = func(df)
            if isinstance(value, (float, np.floating)) and math.isnan(value):
                row[label] = ""
            else:
                row[label] = formatter.format(value)
        rows.append(row)

    stats_df = pd.DataFrame(rows)
    stats_df.loc[stats_df["Metric"] == "Positive trade rows", "Overall"] = f"{len(positive_trades):,.0f}"
    return stats_df
