from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .config import AnalysisConfig
from .storage import save_text_output


STAGE_TERMS = ["US_Post2018", "US_Post2022", "US_Post2023"]
PERIOD_TERMS = ["US_Period_2018_2021", "US_Period_2022", "US_Period_2023_2024"]


def _extract_terms(model: object, terms: list[str], dependent: str, model_name: str, sample_label: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    conf = model.conf_int()
    for term in terms:
        if term not in model.params.index:
            continue
        coef = float(model.params[term])
        ci_low, ci_high = conf.loc[term].tolist()
        rows.append(
            {
                "model": model_name,
                "sample": sample_label,
                "dependent_variable": dependent,
                "term": term,
                "coef": round(coef, 6),
                "std_error": round(float(model.bse[term]), 6),
                "p_value": round(float(model.pvalues[term]), 6),
                "ci_low": round(float(ci_low), 6),
                "ci_high": round(float(ci_high), 6),
                "nobs": int(model.nobs),
                "r_squared": round(float(model.rsquared), 6),
                "approx_pct_effect": round(float(np.exp(coef) - 1.0), 6)
                if dependent == "ln_import_value"
                else "",
            }
        )
    return rows


def run_stage_model(df: pd.DataFrame, dependent: str, formula_suffix: str, model_name: str, sample_label: str):
    formula = f"{dependent} ~ {' + '.join(STAGE_TERMS)} + {formula_suffix}"
    model = smf.ols(formula=formula, data=df).fit(cov_type="HC1")
    rows = _extract_terms(model, STAGE_TERMS, dependent, model_name, sample_label)
    return model, rows


def run_period_model(df: pd.DataFrame, dependent: str, formula_suffix: str, model_name: str, sample_label: str):
    formula = f"{dependent} ~ {' + '.join(PERIOD_TERMS)} + {formula_suffix}"
    model = smf.ols(formula=formula, data=df).fit(cov_type="HC1")
    rows = _extract_terms(model, PERIOD_TERMS, dependent, model_name, sample_label)
    return model, rows


def run_all_regressions(panel: pd.DataFrame, main_exporter_panel: pd.DataFrame, config: AnalysisConfig) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    models: dict[str, object] = {}
    policy_rows: list[dict[str, object]] = []
    product_rows: list[dict[str, object]] = []
    group_rows: list[dict[str, object]] = []
    robustness_rows: list[dict[str, object]] = []
    share_rows: list[dict[str, object]] = []
    period_rows: list[dict[str, object]] = []

    pooled_suffix = "C(exporter_code) + C(product_code) + C(year)"
    product_suffix = "C(exporter_code) + C(year)"

    baseline_model, rows = run_stage_model(panel, "ln_import_value", pooled_suffix, "pooled_stage_ln", "all_selected_products")
    models["pooled_stage_ln_model_v02.txt"] = baseline_model
    policy_rows.extend(rows)

    share_model, rows = run_stage_model(panel, "import_share", pooled_suffix, "pooled_stage_share", "all_selected_products")
    models["pooled_stage_share_model_v02.txt"] = share_model
    share_rows.extend(rows)

    asinh_model, rows = run_stage_model(panel, "asinh_import_value", pooled_suffix, "robust_asinh", "all_selected_products")
    models["robust_asinh_model_v02.txt"] = asinh_model
    robustness_rows.extend(rows)

    no_covid = panel.loc[~panel["year"].isin([2020, 2021])].copy()
    no_covid_model, rows = run_stage_model(no_covid, "ln_import_value", pooled_suffix, "robust_drop_2020_2021", "all_selected_products")
    models["robust_drop_2020_2021_model_v02.txt"] = no_covid_model
    robustness_rows.extend(rows)

    narrow_model, rows = run_stage_model(main_exporter_panel, "ln_import_value", pooled_suffix, "robust_top10_2024_sources", "top10_2024_sources_plus_us")
    models["robust_top10_2024_sources_model_v02.txt"] = narrow_model
    robustness_rows.extend(rows)

    period_model, rows = run_period_model(panel, "ln_import_value", pooled_suffix, "mutually_exclusive_periods", "all_selected_products")
    models["mutually_exclusive_periods_model_v02.txt"] = period_model
    period_rows.extend(rows)

    for product_code, group in panel.groupby("product_code"):
        product_model, rows = run_stage_model(group, "ln_import_value", product_suffix, f"product_{product_code}_stage_ln", f"HS{product_code}")
        models[f"product_{product_code}_stage_ln_model_v02.txt"] = product_model
        product_rows.extend(rows)

    for product_group, group in panel.groupby("product_group"):
        group_model, rows = run_stage_model(group, "ln_import_value", pooled_suffix, f"group_{product_group}_stage_ln", product_group)
        models[f"group_{product_group}_stage_ln_model_v02.txt"] = group_model
        group_rows.extend(rows)

    results = {
        "policy_stage_regression_results_v02": pd.DataFrame(policy_rows),
        "share_outcome_regression_results_v02": pd.DataFrame(share_rows),
        "product_specific_regression_results_v02": pd.DataFrame(product_rows),
        "product_group_regression_results_v02": pd.DataFrame(group_rows),
        "robustness_results_v02": pd.DataFrame(robustness_rows),
        "mutually_exclusive_period_results_v02": pd.DataFrame(period_rows),
    }
    return results, models


def write_model_outputs(models: dict[str, object], config: AnalysisConfig) -> None:
    for filename, model in models.items():
        save_text_output(model.summary().as_text(), filename, config.table_output_dir)
