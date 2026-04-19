from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .config import AnalysisConfig
from .storage import save_text_output


def run_regression(df: pd.DataFrame, dependent: str) -> tuple[object, dict[str, object]]:
    """
    运行一个最小可行的固定效应回归。

    这里比较的是：2018 年后，美国相对于其他出口国，是否出现了不一样的变化。
    """
    model = smf.ols(
        formula=f"{dependent} ~ US_Post2018 + C(exporter_code) + C(year)",
        data=df,
    ).fit(cov_type="HC1")
    coefficient = model.params["US_Post2018"]
    conf_low, conf_high = model.conf_int().loc["US_Post2018"].tolist()
    result = {
        "dependent_variable": dependent,
        "coef_us_post2018": round(float(coefficient), 6),
        "std_error": round(float(model.bse["US_Post2018"]), 6),
        "p_value": round(float(model.pvalues["US_Post2018"]), 6),
        "ci_low": round(float(conf_low), 6),
        "ci_high": round(float(conf_high), 6),
        "nobs": int(model.nobs),
        "r_squared": round(float(model.rsquared), 6),
        "treatment_observations": int(df["US_Post2018"].sum()),
        "approx_pct_effect": round(float(np.exp(coefficient) - 1.0), 6) if dependent == "ln_import_value" else "",
    }
    return model, result


def run_all_regressions(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """
    把 v0.1 需要的三组回归集中放在一起：
    1. 基准模型
    2. 更换被解释变量
    3. 剔除疫情年份
    """
    baseline_model, baseline_result = run_regression(panel, "ln_import_value")
    asinh_model, asinh_result = run_regression(panel, "asinh_import_value")
    no_covid_panel = panel.loc[~panel["year"].isin([2020, 2021])].copy()
    no_covid_model, no_covid_result = run_regression(no_covid_panel, "ln_import_value")

    regression_results = pd.DataFrame(
        [
            {"model": "baseline_ln", **baseline_result},
            {"model": "robust_asinh", **asinh_result},
            {"model": "robust_drop_2020_2021", **no_covid_result},
        ]
    )
    models = {
        "baseline_ln_model_848620.txt": baseline_model,
        "robust_asinh_model_848620.txt": asinh_model,
        "robust_drop_2020_2021_model_848620.txt": no_covid_model,
    }
    return regression_results, models


def write_model_outputs(models: dict[str, object], config: AnalysisConfig) -> None:
    """把 statsmodels 的长回归结果保存成文本，便于人工阅读和排查。"""
    for filename, model in models.items():
        save_text_output(model.summary().as_text(), filename, config.table_output_dir)
