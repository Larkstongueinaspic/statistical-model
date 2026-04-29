from __future__ import annotations

import pandas as pd

from .config import GcnConfig


CORE_PRODUCT_CODES = ("848620", "854231", "854232", "854239")

PRODUCT_GROUPS = {
    "848610": "semiconductor_equipment",
    "848620": "semiconductor_equipment",
    "848640": "semiconductor_equipment",
    "848690": "semiconductor_equipment",
    "854110": "semiconductor_devices",
    "854121": "semiconductor_devices",
    "854129": "semiconductor_devices",
    "854130": "semiconductor_devices",
    "854140": "semiconductor_devices",
    "854150": "semiconductor_devices",
    "854160": "semiconductor_devices",
    "854190": "semiconductor_devices",
    "854231": "integrated_circuits",
    "854232": "integrated_circuits",
    "854233": "integrated_circuits",
    "854239": "integrated_circuits",
    "854290": "integrated_circuits",
    "853400": "related_hardware",
    "903082": "related_hardware",
    "903141": "related_hardware",
}

GCN_PRODUCT_CODES = tuple(PRODUCT_GROUPS)


def _normalise_product_codes(product_codes: pd.DataFrame) -> pd.DataFrame:
    result = product_codes.copy()
    if "code" in result.columns and "product_code" not in result.columns:
        result = result.rename(columns={"code": "product_code"})
    if "description" in result.columns and "product_description" not in result.columns:
        result = result.rename(columns={"description": "product_description"})
    result["product_code"] = result["product_code"].astype(str)
    if "product_description" not in result.columns:
        result["product_description"] = ""
    return result[["product_code", "product_description"]].drop_duplicates("product_code")


def _coverage_lookup(coverage: pd.DataFrame | None) -> pd.DataFrame:
    if coverage is None:
        return pd.DataFrame(
            columns=[
                "product_code",
                "positive_years",
                "exporter_count",
                "labeled_transitions",
                "total_import_value_kusd",
            ]
        )
    result = coverage.copy()
    result["product_code"] = result["product_code"].astype(str)
    return result


def _passes_model_thresholds(row: pd.Series, config: GcnConfig) -> bool:
    return bool(
        row["metadata_exists"]
        and row["positive_years"] >= config.min_positive_years
        and row["exporter_count"] >= config.min_exporter_count
        and row["labeled_transitions"] >= config.min_labeled_transitions
        and row["total_import_value_kusd"] > 0
    )


def _status_reason(row: pd.Series, config: GcnConfig) -> str:
    reasons: list[str] = []
    if not row["metadata_exists"]:
        reasons.append("missing_product_metadata")
    if row["positive_years"] < config.min_positive_years:
        reasons.append("coverage_below_threshold")
    if row["exporter_count"] < config.min_exporter_count:
        reasons.append("exporter_count_below_threshold")
    if row["labeled_transitions"] < config.min_labeled_transitions:
        reasons.append("labeled_transitions_below_threshold")
    if row["total_import_value_kusd"] <= 0:
        reasons.append("zero_total_import_value")
    return ";".join(reasons) if reasons else "passes_model_thresholds"


def build_product_pool(
    product_codes: pd.DataFrame,
    coverage: pd.DataFrame | None = None,
    config: GcnConfig | None = None,
) -> pd.DataFrame:
    config = config or GcnConfig()
    products = _normalise_product_codes(product_codes)
    coverage_df = _coverage_lookup(coverage)
    rows: list[dict[str, object]] = []

    for code in GCN_PRODUCT_CODES:
        product_match = products.loc[products["product_code"] == code]
        coverage_match = coverage_df.loc[coverage_df["product_code"] == code]
        metadata_exists = not product_match.empty
        description = str(product_match["product_description"].iloc[0]) if metadata_exists else ""
        metrics = {
            "positive_years": 0,
            "exporter_count": 0,
            "labeled_transitions": 0,
            "total_import_value_kusd": 0.0,
        }
        if not coverage_match.empty:
            first = coverage_match.iloc[0]
            for key in metrics:
                metrics[key] = first.get(key, metrics[key])
        row = {
            "product_code": code,
            "product_description": description,
            "product_group": PRODUCT_GROUPS[code],
            "is_core_product": code in CORE_PRODUCT_CODES,
            "metadata_exists": metadata_exists,
            **metrics,
        }
        probe = pd.Series(row)
        passes = _passes_model_thresholds(probe, config)
        reason = _status_reason(probe, config)
        if passes:
            status = "model"
        elif row["is_core_product"] and metadata_exists and float(row["total_import_value_kusd"]) > 0:
            status = "report_only"
        else:
            status = "excluded"
        rows.append({**row, "model_status": status, "status_reason": reason})

    columns = [
        "product_code",
        "product_description",
        "product_group",
        "is_core_product",
        "metadata_exists",
        "positive_years",
        "exporter_count",
        "labeled_transitions",
        "total_import_value_kusd",
        "model_status",
        "status_reason",
    ]
    return pd.DataFrame(rows, columns=columns)


def build_country_crosswalk(country_codes: pd.DataFrame) -> pd.DataFrame:
    result = country_codes.copy()
    if "country_code" in result.columns:
        result = result.rename(columns={"country_code": "exporter_code"})
    if "country_iso3" in result.columns:
        result = result.rename(columns={"country_iso3": "exporter_iso3"})
    if "country_name" in result.columns:
        result = result.rename(columns={"country_name": "exporter_name"})
    result["exporter_iso3"] = result["exporter_iso3"].astype("string")
    result["gdelt_country_code"] = result["exporter_iso3"].fillna("")
    result["mapping_status"] = result["gdelt_country_code"].map(lambda value: "mapped" if value else "missing_gdelt_code")
    return result[
        [
            "exporter_code",
            "exporter_iso3",
            "exporter_name",
            "gdelt_country_code",
            "mapping_status",
        ]
    ]
