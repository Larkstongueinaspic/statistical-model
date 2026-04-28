from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import GcnConfig
from .product_pool import GCN_PRODUCT_CODES, PRODUCT_GROUPS


def _yearly_file(config: GcnConfig, year: int) -> Path:
    return config.baci_dir / f"BACI_HS07_Y{year}_V202601.csv"


def load_country_codes(config: GcnConfig) -> pd.DataFrame:
    return pd.read_csv(
        config.baci_dir / "country_codes_V202601.csv",
        dtype={
            "country_code": "int64",
            "country_name": "string",
            "country_iso2": "string",
            "country_iso3": "string",
        },
    )


def load_product_codes(config: GcnConfig) -> pd.DataFrame:
    product_codes = pd.read_csv(
        config.baci_dir / "product_codes_HS07_V202601.csv",
        dtype={"code": "string", "description": "string"},
    )
    products = product_codes.loc[product_codes["code"].isin(GCN_PRODUCT_CODES)].copy()
    products["product_group"] = products["code"].map(PRODUCT_GROUPS)
    return products.rename(columns={"code": "product_code", "description": "product_description"})


def load_yearly_candidate_trades(
    year: int,
    candidate_product_codes: tuple[str, ...],
    config: GcnConfig,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    candidate_set = set(candidate_product_codes)
    for chunk in pd.read_csv(
        _yearly_file(config, year),
        usecols=["t", "i", "j", "k", "v", "q"],
        dtype={"t": "int16", "i": "int32", "j": "int32", "k": "string", "v": "float64", "q": "float64"},
        na_values=[""],
        keep_default_na=True,
        chunksize=1_000_000,
    ):
        filtered = chunk.loc[(chunk["j"] == 156) & (chunk["k"].isin(candidate_set))].copy()
        if not filtered.empty:
            frames.append(filtered)
    columns = ["year", "exporter_code", "importer_code", "product_code", "import_value_kusd", "quantity_tons"]
    if not frames:
        return pd.DataFrame(columns=columns)
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
    config: GcnConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    year_checks: list[dict[str, object]] = []
    country_lookup = country_codes[["country_code", "country_name", "country_iso3"]].rename(
        columns={"country_code": "exporter_code", "country_name": "exporter_name", "country_iso3": "exporter_iso3"}
    )
    product_lookup = products[["product_code", "product_description", "product_group"]].drop_duplicates("product_code")
    for year in config.years:
        year_df = load_yearly_candidate_trades(year, GCN_PRODUCT_CODES, config)
        frames.append(year_df)
        for product_code in GCN_PRODUCT_CODES:
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
    positive = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if positive.empty:
        return positive, pd.DataFrame(year_checks)
    positive["product_code"] = positive["product_code"].astype(str)
    positive = positive.merge(product_lookup, on="product_code", how="left")
    positive = positive.merge(country_lookup, on="exporter_code", how="left")
    positive["product_group"] = positive["product_group"].fillna(positive["product_code"].map(PRODUCT_GROUPS))
    positive["importer_name"] = "China"
    positive["importer_iso3"] = "CHN"
    return positive.sort_values(["product_code", "year", "exporter_code"], ignore_index=True), pd.DataFrame(year_checks)


def build_product_coverage(positive_trades: pd.DataFrame, config: GcnConfig) -> pd.DataFrame:
    rows = []
    for product_code in GCN_PRODUCT_CODES:
        product = positive_trades.loc[positive_trades["product_code"].astype(str) == product_code]
        positive_years = int(product.loc[product["import_value_kusd"] > 0, "year"].nunique())
        exporter_count = int(product.loc[product["import_value_kusd"] > 0, "exporter_code"].nunique())
        total = float(product["import_value_kusd"].sum()) if not product.empty else 0.0
        rows.append(
            {
                "product_code": product_code,
                "positive_years": positive_years,
                "exporter_count": exporter_count,
                "labeled_transitions": max(positive_years - 1, 0),
                "total_import_value_kusd": total,
            }
        )
    return pd.DataFrame(rows)


def build_balanced_panel(
    positive_trades: pd.DataFrame,
    selected_products: tuple[str, ...],
    config: GcnConfig,
) -> pd.DataFrame:
    selected = positive_trades.loc[positive_trades["product_code"].astype(str).isin(selected_products)].copy()
    if selected.empty:
        return pd.DataFrame()
    product_lookup = (
        selected[["product_code", "product_description", "product_group"]].drop_duplicates().set_index("product_code")
    )
    exporter_lookup = selected[["exporter_code", "exporter_name", "exporter_iso3"]].drop_duplicates()
    index_frames = []
    for product_code, product_group in selected.groupby("product_code"):
        exporters = sorted(product_group["exporter_code"].astype(int).unique().tolist())
        index_frames.append(
            pd.MultiIndex.from_product(
                [[str(product_code)], exporters, config.years],
                names=["product_code", "exporter_code", "year"],
            ).to_frame(index=False)
        )
    panel_index = pd.concat(index_frames, ignore_index=True)
    annual = selected.groupby(["product_code", "exporter_code", "year"], as_index=False)[
        ["import_value_kusd", "quantity_tons"]
    ].sum()
    panel = (
        panel_index.merge(exporter_lookup, on="exporter_code", how="left")
        .merge(product_lookup.reset_index(), on="product_code", how="left")
        .merge(annual, on=["product_code", "exporter_code", "year"], how="left")
    )
    panel["import_value_kusd"] = panel["import_value_kusd"].fillna(0.0)
    panel["quantity_tons"] = panel["quantity_tons"].fillna(0.0)
    totals = panel.groupby(["product_code", "year"], as_index=False)["import_value_kusd"].sum().rename(
        columns={"import_value_kusd": "product_year_total_kusd"}
    )
    panel = panel.merge(totals, on=["product_code", "year"], how="left")
    panel["import_share"] = np.where(
        panel["product_year_total_kusd"] > 0,
        panel["import_value_kusd"] / panel["product_year_total_kusd"],
        0.0,
    )
    return panel.sort_values(["product_code", "exporter_code", "year"], ignore_index=True)
