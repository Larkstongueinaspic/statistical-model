from __future__ import annotations

import pandas as pd

from .config import AnalysisConfig


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _coef_phrase(df: pd.DataFrame, term: str) -> str:
    row = df.loc[df["term"] == term].iloc[0]
    return f"{row['coef']:.4f} (p={row['p_value']:.4f})"


def build_report_numbers(annual: pd.DataFrame, policy: pd.DataFrame, share: pd.DataFrame, robustness: pd.DataFrame) -> dict[str, object]:
    numbers: dict[str, object] = {}
    for code in annual["product_code"].drop_duplicates():
        product = annual.loc[annual["product_code"] == code]
        share_2017 = float(product.loc[product["year"] == 2017, "us_share"].iloc[0])
        share_2024 = float(product.loc[product["year"] == 2024, "us_share"].iloc[0])
        total_2024 = float(product.loc[product["year"] == 2024, "total_import_kusd"].iloc[0])
        hhi_2017 = float(product.loc[product["year"] == 2017, "hhi"].iloc[0])
        hhi_2024 = float(product.loc[product["year"] == 2024, "hhi"].iloc[0])
        numbers[f"{code}_us_share_2017"] = share_2017
        numbers[f"{code}_us_share_2024"] = share_2024
        numbers[f"{code}_us_share_change_pp"] = (share_2024 - share_2017) * 100
        numbers[f"{code}_total_2024_billion"] = total_2024 / 1_000_000.0
        numbers[f"{code}_hhi_2017"] = hhi_2017
        numbers[f"{code}_hhi_2024"] = hhi_2024
    numbers["policy_us_post2018"] = _coef_phrase(policy, "US_Post2018")
    numbers["policy_us_post2022"] = _coef_phrase(policy, "US_Post2022")
    numbers["policy_us_post2023"] = _coef_phrase(policy, "US_Post2023")
    numbers["share_us_post2018"] = _coef_phrase(share, "US_Post2018")
    numbers["share_us_post2022"] = _coef_phrase(share, "US_Post2022")
    numbers["share_us_post2023"] = _coef_phrase(share, "US_Post2023")
    asinh = robustness.loc[robustness["model"] == "robust_asinh"]
    no_covid = robustness.loc[robustness["model"] == "robust_drop_2020_2021"]
    narrow = robustness.loc[robustness["model"] == "robust_top10_2024_sources"]
    numbers["asinh_us_post2023"] = _coef_phrase(asinh, "US_Post2023")
    numbers["no_covid_us_post2023"] = _coef_phrase(no_covid, "US_Post2023")
    numbers["narrow_us_post2023"] = _coef_phrase(narrow, "US_Post2023")
    return numbers


def write_summary(
    selected_products: tuple[str, ...],
    annual: pd.DataFrame,
    top_2024: pd.DataFrame,
    regression_tables: dict[str, pd.DataFrame],
    config: AnalysisConfig,
) -> None:
    numbers = build_report_numbers(
        annual,
        regression_tables["policy_stage_regression_results_v02"],
        regression_tables["share_outcome_regression_results_v02"],
        regression_tables["robustness_results_v02"],
    )
    product_list = ", ".join(f"`{code}`" for code in selected_products)
    top_lines = []
    for code in selected_products:
        top = top_2024.loc[top_2024["product_code"] == code].sort_values("rank_2024").head(5)
        sources = "、".join(f"{row.exporter_name} {_pct(row.share)}" for row in top.itertuples())
        top_lines.append(f"- `{code}`：{sources}")
    summary = f"""# 阶段总结-v0.2

## 本轮完成内容

- 在不改动 v0.1 的前提下，新建 `scripts/run_v02_analysis.py` 和 `scripts/v02_analysis/`。
- v0.2 产品范围扩展为 {product_list}，覆盖设备类和集成电路类产品。
- 新增 `Post2022`、`Post2023` 及互斥阶段变量，输出多产品面板、筛查表、描述统计表、图表、回归表、稳健性表和测试表。
- 输出路径统一为 `results/v02/`，文档输出为 `docs/output/log_v0.2.md`、`docs/output/summary_v0.2.md`、`docs/output/abstract_v0.2.md`。

## 主要结果

- 美国份额下降不是只发生在 `848620`，但集成电路类产品并非完全同向。`848620` 美国份额从 2017 年 {_pct(numbers['848620_us_share_2017'])} 降至 2024 年 {_pct(numbers['848620_us_share_2024'])}；`854231` 和 `854232` 也下降，而 `854239` 从低基数小幅上升。
- 2024 年主要来源国显示，设备类替代主要集中在日本、荷兰、新加坡等国家；集成电路类产品的主要来源则更多集中在韩国、马来西亚、越南、`Other Asia, nes` 等亚洲生产网络节点。
{chr(10).join(top_lines)}
- 多产品 pooled 回归中，`US_Post2018`、`US_Post2022`、`US_Post2023` 分别为 {numbers['policy_us_post2018']}、{numbers['policy_us_post2022']}、{numbers['policy_us_post2023']}。方向和显著性说明，细化节点后仍不能把结果简单写成“美国对华出口额显著下降”。
- 份额型结果更贴近描述事实：`US_Post2018`、`US_Post2022`、`US_Post2023` 分别为 {numbers['share_us_post2018']}、{numbers['share_us_post2022']}、{numbers['share_us_post2023']}。这些系数方向偏负但不显著，更适合作为“份额承压”的补充证据，而不是强因果证据。

## 与 v0.1 相比新增了什么

- 从单产品 `848620` 扩展到多产品，能够比较设备类与集成电路类产品。
- 从单一 `Post2018` 扩展到 `Post2018 / Post2022 / Post2023`。
- 新增主要来源国收窄对照组、份额型被解释变量、互斥阶段变量和分产品回归。
- 图表从单产品趋势扩展为多产品总额、美国进口额、美国份额、2024 来源结构、HHI、2017 份额指数和产品组对比。

## 当前局限

- 仍是年度 HS6 数据，不能精确对应具体企业、具体管制清单或月度政策窗口。
- `Post2022` 与 `Post2023` 是粗政策节点，不能完全区分出口管制、产业周期和中国进口需求变化。
- 回归仍是简化固定效应模型，控制变量有限，不宜作为强因果识别。
- 份额型结果有解释价值，但份额本身受其他来源国增长影响，不能等同于美国出口能力单独下降。

## 下一轮最值得做的三件事

1. 把政策事件时间线写进论文文本，并核对 `2022`、`2023` 节点的制度含义。
2. 对主要来源国做更清晰的地区/产业链分组，解释设备类和集成电路类替代来源差异。
3. 若继续加强识别，优先做简单事件研究或出口国-产品固定效应，而不是引入复杂外部数据。
"""
    (config.docs_output_dir / "summary_v0.2.md").write_text(summary, encoding="utf-8")


def write_abstract(
    selected_products: tuple[str, ...],
    panel: pd.DataFrame,
    annual: pd.DataFrame,
    regression_tables: dict[str, pd.DataFrame],
    config: AnalysisConfig,
) -> None:
    numbers = build_report_numbers(
        annual,
        regression_tables["policy_stage_regression_results_v02"],
        regression_tables["share_outcome_regression_results_v02"],
        regression_tables["robustness_results_v02"],
    )
    product_list = ", ".join(f"`{code}`" for code in selected_products)
    positive_rows = int((panel["import_value_kusd"] > 0).sum())
    abstract = f"""# 结果摘要-v0.2

## 样本与方法

- 数据为 BACI HS07 `2008-2024` 年中国进口年度双边贸易数据，产品为 {product_list}。
- 观察单元为 `出口国 × 产品 × 年份`。v0.2 在每个产品内部保留样本期内曾向中国出口该产品的出口国，并补齐 `2008-2024` 年；未出现的产品-出口国-年份贸易流按 `0` 处理。
- 多产品面板共 `{len(panel)}` 行，其中正向贸易记录 `{positive_rows}` 行。
- 核心变量包括 `import_value_kusd`、`ln_import_value`、`asinh_import_value`、`product_code`、`exporter_code`、`year`、`US`、`Post2018`、`Post2022`、`Post2023`、`US_Post2018`、`US_Post2022`、`US_Post2023` 和 `import_share`。
- 基准扩展模型为 `ln(import_value+1) = β1 US_Post2018 + β2 US_Post2022 + β3 US_Post2023 + 出口国固定效应 + 产品固定效应 + 年份固定效应 + error`，并补充分产品、产品组、份额型结果和稳健性估计。

## 多产品描述性事实

- `848620` 的美国份额从 2017 年 {_pct(numbers['848620_us_share_2017'])} 降到 2024 年 {_pct(numbers['848620_us_share_2024'])}，延续 v0.1 的来源替代事实。
- 集成电路类产品存在异质性。`854231` 从 2017 年 {_pct(numbers['854231_us_share_2017'])} 到 2024 年 {_pct(numbers['854231_us_share_2024'])}，`854232` 从 2017 年 {_pct(numbers['854232_us_share_2017'])} 到 2024 年 {_pct(numbers['854232_us_share_2024'])}，但 `854239` 从 2017 年 {_pct(numbers['854239_us_share_2017'])} 到 2024 年 {_pct(numbers['854239_us_share_2024'])}，说明不能把所有集成电路产品写成同一种方向。
- 替代来源存在产品差异：设备类更依赖日本、荷兰、新加坡等设备强国，集成电路类更多体现亚洲生产网络内部的来源调整。
- HHI 指标显示，来源替代不必然意味着来源分散；部分产品在 2024 年仍明显集中于少数主要来源。

## 政策节点回归结果

- pooled `ln(import_value+1)` 模型中，`US_Post2018`、`US_Post2022`、`US_Post2023` 分别为 {numbers['policy_us_post2018']}、{numbers['policy_us_post2022']}、{numbers['policy_us_post2023']}。
- 该结果说明，在多产品和多节点设定下，绝对进口额模型仍不能稳妥支持“美国对华出口额显著下降”的强因果表述。
- 份额型结果中，`US_Post2018`、`US_Post2022`、`US_Post2023` 分别为 {numbers['share_us_post2018']}、{numbers['share_us_post2022']}、{numbers['share_us_post2023']}。方向偏负但统计上不显著，只能作为美国份额承压的补充展示。

## 稳健性结果

- 改用 `asinh(import_value)` 后，`US_Post2023` 为 {numbers['asinh_us_post2023']}。
- 剔除 `2020-2021` 后，`US_Post2023` 为 {numbers['no_covid_us_post2023']}。
- 只保留 2024 年前十来源国加美国的收窄对照组后，`US_Post2023` 为 {numbers['narrow_us_post2023']}。
- 稳健性结果没有把核心结论改写为强负向因果结论，但支持继续把“多数核心产品的美国份额下降”和“来源替代”作为主要经验事实。

## 能写进初稿的结论

- 2018 年后，尤其在 2022-2024 年，中国半导体相关产品进口来源结构发生明显调整，美国份额在设备和部分集成电路产品中下降，另有产品表现出异质性。
- 设备类和集成电路类的替代来源不同，说明不能只用单一产品结果概括整个半导体贸易结构。
- v0.2 更适合写成“来源结构重组和美国份额下降”，而不是“美国出口额被显著压低”。

## 不宜过度表述的结论

- 不宜声称当前模型已经识别出美国出口管制的严格因果效应。
- 不宜把美国份额下降直接等同于美国对华出口绝对额下降。
- 不宜忽略全球半导体周期、中国需求扩张和第三方产能变化对结果的共同影响。
"""
    (config.docs_output_dir / "abstract_v0.2.md").write_text(abstract, encoding="utf-8")
