from __future__ import annotations

import numpy as np
import pandas as pd


SIRI_COMPONENTS = (
    "concentration",
    "policy_exposure",
    "alternative_insufficiency",
    "structural_volatility",
)
RAW_COLUMNS = tuple(f"{component}_raw" for component in SIRI_COMPONENTS)
NORM_COLUMNS = tuple(f"{component}_norm" for component in SIRI_COMPONENTS)
BASELINE_WEIGHTS = {
    "concentration": 0.25,
    "policy_exposure": 0.25,
    "alternative_insufficiency": 0.25,
    "structural_volatility": 0.25,
}
POLICY_WEIGHTED_WEIGHTS = {
    "concentration": 0.20,
    "policy_exposure": 0.40,
    "alternative_insufficiency": 0.20,
    "structural_volatility": 0.20,
}


def validate_weights(weights: dict[str, float]) -> None:
    missing = set(SIRI_COMPONENTS) - set(weights)
    extra = set(weights) - set(SIRI_COMPONENTS)
    if missing or extra:
        raise ValueError(f"SIRI weights must have exactly {SIRI_COMPONENTS}; missing={missing}, extra={extra}")
    if any(value < 0 for value in weights.values()):
        raise ValueError("SIRI weights must be non-negative.")
    total = float(sum(weights.values()))
    if not np.isclose(total, 1.0):
        raise ValueError(f"SIRI weights must sum to 1.0, got {total:.6f}.")


def _require_columns(df: pd.DataFrame, required: set[str]) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def build_siri_panel(panel_df: pd.DataFrame, usa_code: int = 842) -> pd.DataFrame:
    _require_columns(panel_df, {"product_code", "year", "exporter_code", "import_value_kusd"})
    if (panel_df["import_value_kusd"] < 0).any():
        raise ValueError("SIRI input import values must be non-negative.")

    product_name_source = "product_description" if "product_description" in panel_df.columns else None
    group_cols = ["product_code", "year", "exporter_code"]
    aggregations = {"import_value_kusd": "sum"}
    if product_name_source:
        aggregations[product_name_source] = "first"

    flows = panel_df.groupby(group_cols, as_index=False).agg(aggregations)
    totals = (
        flows.groupby(["product_code", "year"], as_index=False)["import_value_kusd"]
        .sum()
        .rename(columns={"import_value_kusd": "total_import_value_kusd"})
    )
    flows = flows.merge(totals, on=["product_code", "year"], how="left")
    flows["share"] = np.where(
        flows["total_import_value_kusd"] > 0,
        flows["import_value_kusd"] / flows["total_import_value_kusd"],
        0.0,
    )

    rows: list[dict[str, object]] = []
    for product_code, product_group in flows.groupby("product_code"):
        product_group = product_group.sort_values(["year", "exporter_code"]).copy()
        product_name = ""
        if product_name_source and product_name_source in product_group:
            product_names = product_group[product_name_source].dropna()
            if not product_names.empty:
                product_name = str(product_names.iloc[0])
        previous_shares: dict[int, float] | None = None

        for year, year_group in product_group.groupby("year", sort=True):
            shares = {
                int(row.exporter_code): float(row.share)
                for row in year_group.itertuples(index=False)
            }
            total_import = float(year_group["total_import_value_kusd"].iloc[0])
            us_share = float(shares.get(usa_code, 0.0))
            concentration = float(sum(value * value for value in shares.values())) if total_import > 0 else 0.0
            non_us_share = max(1.0 - us_share, 0.0)
            if total_import <= 0:
                alternative = 0.0
            elif non_us_share > 0:
                alternative = float(
                    sum((share / non_us_share) ** 2 for code, share in shares.items() if code != usa_code)
                )
            else:
                alternative = 1.0

            if previous_shares is None:
                volatility = 0.0
            else:
                exporters = set(shares) | set(previous_shares)
                volatility = 0.5 * sum(
                    abs(shares.get(code, 0.0) - previous_shares.get(code, 0.0))
                    for code in exporters
                )

            rows.append(
                {
                    "product_code": str(product_code),
                    "product_name": product_name,
                    "year": int(year),
                    "total_import_value_kusd": total_import,
                    "concentration_raw": concentration,
                    "policy_exposure_raw": us_share,
                    "alternative_insufficiency_raw": alternative,
                    "structural_volatility_raw": float(volatility),
                }
            )
            previous_shares = shares

    return pd.DataFrame(rows).sort_values(["product_code", "year"], ignore_index=True)


def normalize_siri_components(siri_df: pd.DataFrame) -> pd.DataFrame:
    result = siri_df.copy()
    for component in SIRI_COMPONENTS:
        raw = f"{component}_raw"
        norm = f"{component}_norm"
        min_value = float(result[raw].min())
        max_value = float(result[raw].max())
        if np.isclose(max_value, min_value):
            result[norm] = 0.0
        else:
            result[norm] = (result[raw] - min_value) / (max_value - min_value)
    return result


def compute_siri_scores(siri_df: pd.DataFrame, weights: dict[str, float], score_column: str) -> pd.DataFrame:
    validate_weights(weights)
    result = siri_df.copy()
    score = sum(result[f"{component}_norm"] * weight for component, weight in weights.items())
    result[score_column] = score * 100.0
    return result


def _recent_average(scored: pd.DataFrame, score_column: str, target_year: int) -> pd.DataFrame:
    recent = scored.loc[scored["year"].between(target_year - 2, target_year)]
    return (
        recent.groupby("product_code", as_index=False)[score_column]
        .mean()
        .rename(columns={score_column: f"{score_column}_recent_mean"})
    )


def _rank_for_score(scored: pd.DataFrame, score_column: str, rank_column: str, target_year: int) -> pd.DataFrame:
    target = scored.loc[scored["year"] == target_year].copy()
    recent_average = _recent_average(scored, score_column, target_year)
    target = target.merge(recent_average, on="product_code", how="left")
    target = target.sort_values(
        [score_column, f"{score_column}_recent_mean", "product_code"],
        ascending=[False, False, True],
        ignore_index=True,
    )
    target[rank_column] = range(1, len(target) + 1)
    return target[["product_code", rank_column]]


def build_siri_ranking(scored: pd.DataFrame, target_year: int = 2024) -> pd.DataFrame:
    baseline_rank = _rank_for_score(scored, "siri_score", "rank", target_year)
    policy_rank = _rank_for_score(scored, "siri_score_policy_weighted", "rank_policy_weighted", target_year)
    target = scored.loc[
        scored["year"] == target_year,
        [
            "product_code",
            "product_name",
            "year",
            "siri_score",
            "siri_score_policy_weighted",
        ],
    ].copy()
    result = target.merge(baseline_rank, on="product_code", how="left").merge(policy_rank, on="product_code", how="left")
    result["rank_change"] = result["rank_policy_weighted"] - result["rank"]
    return result.sort_values(["rank", "product_code"], ignore_index=True)[
        [
            "rank",
            "product_code",
            "product_name",
            "year",
            "siri_score",
            "siri_score_policy_weighted",
            "rank_policy_weighted",
            "rank_change",
        ]
    ]


def build_siri_weight_sensitivity(scored: pd.DataFrame, target_year: int = 2024) -> pd.DataFrame:
    ranking = build_siri_ranking(scored, target_year=target_year)
    result = ranking.rename(
        columns={
            "rank": "baseline_rank",
            "rank_policy_weighted": "policy_weighted_rank",
            "siri_score": "baseline_siri_score",
            "siri_score_policy_weighted": "policy_weighted_siri_score",
        }
    )
    return result[
        [
            "product_code",
            "product_name",
            "baseline_rank",
            "policy_weighted_rank",
            "rank_change",
            "baseline_siri_score",
            "policy_weighted_siri_score",
        ]
    ].sort_values(["baseline_rank", "product_code"], ignore_index=True)


def build_siri_outputs(panel_df: pd.DataFrame, target_year: int = 2024) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = build_siri_panel(panel_df)
    normalized = normalize_siri_components(raw)
    scored = compute_siri_scores(normalized, BASELINE_WEIGHTS, "siri_score")
    scored = compute_siri_scores(scored, POLICY_WEIGHTED_WEIGHTS, "siri_score_policy_weighted")
    ranking = build_siri_ranking(scored, target_year=target_year)
    sensitivity = build_siri_weight_sensitivity(scored, target_year=target_year)
    return scored, ranking, sensitivity
