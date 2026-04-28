from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .config import GcnConfig


KEYWORDS = (
    "semiconductor",
    "chip",
    "chips",
    "integrated circuit",
    "export control",
    "sanction",
    "technology restriction",
    "trade restriction",
    "entity list",
    "supply chain",
)
TEXT_FIELDS = ("SOURCEURL", "DocumentIdentifier", "EventText")


def _event_year(sql_date: pd.Series) -> pd.Series:
    return sql_date.astype(str).str.slice(0, 4).astype(int)


def _apply_keyword_filter(events: pd.DataFrame, config: GcnConfig) -> tuple[pd.DataFrame, str]:
    if not config.gdelt_apply_keyword_filter:
        return events.copy(), "pre_filtered"
    available_fields = [field for field in TEXT_FIELDS if field in events.columns]
    if not available_fields:
        raise ValueError("Keyword filtering requires SOURCEURL, DocumentIdentifier, or EventText.")
    pattern = re.compile("|".join(re.escape(keyword) for keyword in KEYWORDS), flags=re.IGNORECASE)
    text = events[available_fields].fillna("").astype(str).agg(" ".join, axis=1)
    return events.loc[text.str.contains(pattern, regex=True)].copy(), "keyword_filtered"


def _country_year_grid(crosswalk: pd.DataFrame, years: tuple[int, ...]) -> pd.DataFrame:
    exporters = crosswalk[["exporter_code", "exporter_iso3", "gdelt_country_code"]].drop_duplicates()
    return exporters.merge(pd.DataFrame({"year": list(years)}), how="cross")


def _aggregate_for_exporter(events: pd.DataFrame, exporter_code: int, gdelt_code: str) -> pd.DataFrame:
    if not gdelt_code:
        return pd.DataFrame(
            columns=[
                "exporter_code",
                "year",
                "gdelt_event_count",
                "gdelt_avg_goldstein",
                "gdelt_negative_goldstein_sum",
                "gdelt_mentions",
                "gdelt_avg_tone",
            ]
        )
    paired = events.loc[
        ((events["Actor1CountryCode"] == gdelt_code) & (events["Actor2CountryCode"] == "CHN"))
        | ((events["Actor2CountryCode"] == gdelt_code) & (events["Actor1CountryCode"] == "CHN"))
    ].copy()
    if paired.empty:
        return pd.DataFrame(
            columns=[
                "exporter_code",
                "year",
                "gdelt_event_count",
                "gdelt_avg_goldstein",
                "gdelt_negative_goldstein_sum",
                "gdelt_mentions",
                "gdelt_avg_tone",
            ]
        )
    paired["year"] = _event_year(paired["SQLDATE"])
    paired["NumMentions"] = pd.to_numeric(paired["NumMentions"], errors="coerce").fillna(0.0)
    paired["GoldsteinScale"] = pd.to_numeric(paired["GoldsteinScale"], errors="coerce").fillna(0.0)
    paired["AvgTone"] = pd.to_numeric(paired["AvgTone"], errors="coerce")
    paired["negative_goldstein_weighted"] = np.maximum(-paired["GoldsteinScale"], 0.0) * np.maximum(
        paired["NumMentions"], 1.0
    )
    grouped = paired.groupby("year", as_index=False).agg(
        gdelt_event_count=("SQLDATE", "size"),
        gdelt_avg_goldstein=("GoldsteinScale", "mean"),
        gdelt_negative_goldstein_sum=("negative_goldstein_weighted", "sum"),
        gdelt_mentions=("NumMentions", "sum"),
        gdelt_avg_tone=("AvgTone", "mean"),
    )
    grouped["exporter_code"] = exporter_code
    return grouped


def _train_minmax(series: pd.Series, train_mask: pd.Series) -> pd.Series:
    train = series.loc[train_mask].astype(float)
    min_value = float(train.min()) if not train.empty else 0.0
    max_value = float(train.max()) if not train.empty else 0.0
    if np.isclose(min_value, max_value):
        return pd.Series(0.0, index=series.index)
    scaled = (series.astype(float) - min_value) / (max_value - min_value)
    return scaled.clip(lower=0.0, upper=1.0)


def aggregate_gdelt_pressure(
    events: pd.DataFrame,
    crosswalk: pd.DataFrame,
    years: tuple[int, ...],
    config: GcnConfig,
) -> pd.DataFrame:
    filtered, filter_mode = _apply_keyword_filter(events, config)
    frames = []
    for row in crosswalk.itertuples(index=False):
        frames.append(_aggregate_for_exporter(filtered, int(row.exporter_code), str(row.gdelt_country_code or "")))
    aggregated = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    grid = _country_year_grid(crosswalk, years)
    result = grid.merge(aggregated, on=["exporter_code", "year"], how="left")
    fill_zero = ["gdelt_event_count", "gdelt_negative_goldstein_sum", "gdelt_mentions"]
    for column in fill_zero:
        result[column] = result[column].fillna(0.0)
    for column in ["gdelt_avg_goldstein", "gdelt_avg_tone"]:
        result[column] = result[column].fillna(0.0)
    train_mask = result["year"].isin(config.train_years)
    scaled_columns = [
        _train_minmax(result["gdelt_negative_goldstein_sum"], train_mask),
        _train_minmax(result["gdelt_event_count"], train_mask),
        _train_minmax(result["gdelt_mentions"], train_mask),
    ]
    result["gdelt_pressure_score"] = sum(scaled_columns) / len(scaled_columns)
    result["gdelt_filter_mode"] = filter_mode
    return result[
        [
            "exporter_code",
            "exporter_iso3",
            "gdelt_country_code",
            "year",
            "gdelt_event_count",
            "gdelt_avg_goldstein",
            "gdelt_negative_goldstein_sum",
            "gdelt_mentions",
            "gdelt_avg_tone",
            "gdelt_pressure_score",
            "gdelt_filter_mode",
        ]
    ].sort_values(["exporter_code", "year"], ignore_index=True)
