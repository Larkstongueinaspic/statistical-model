# 统计建模竞赛论文设计

日期：2026-04-28

## 1. 背景与目标

本项目已完成 `v0.2` 多产品分析流水线，数据源为 BACI HS07 2008-2024 年中国进口年度双边贸易数据，研究产品包括 `848620`、`854231`、`854232`、`854239` 四类半导体相关 HS6 产品。现有结果已经覆盖数据清洗、描述统计、固定效应回归、份额型结果和稳健性检验。

论文面向 2026 年全国大学生统计建模大赛本科生组。当前可查到的官方要求包括：赛事主题为“服务国家战略 创新统计赋能”，论文正文字符数含空格不超过 16000 字符，并需提交 AI 工具使用情况表等材料。由于尚未找到官方 LaTeX 模板，本项目将自建 XeLaTeX 中文论文模板，同时按统计建模竞赛论文习惯组织内容。

论文目标不是堆叠复杂模型，而是形成一篇数据可靠、模型可解释、结论边界清楚、可复现的本科生组竞赛论文。

## 2. 论文题目与核心定位

暂定题目：

> 大国博弈下中国半导体相关产品进口来源结构演化与供应链风险评估研究

题目保留“大国博弈”的现实背景，但实证承诺收敛到“中国半导体相关产品进口来源结构演化”和“供应链风险评估”。论文不使用“全球数字产品供应链网络”“断链预警平台”“动态图神经网络”等表述作为核心成果，避免题文不符。

核心研究问题：

1. 2018 年以来，中国半导体相关产品进口来源结构是否发生明显变化？
2. 不同半导体相关产品的来源替代路径和风险暴露是否存在差异？
3. 如何构造一个可解释的进口供应链风险评价框架，并据此提出政策建议？

核心表述边界：

- 可以写“政策冲击背景下的结构演化、风险评估与统计证据”。
- 不写成“已经识别出美国出口管制的严格因果效应”。
- 不把美国份额下降直接等同于美国对华出口绝对额下降。

## 3. 数据与样本范围

数据源：

- BACI HS07 2008-2024 年年度双边贸易数据。

样本口径：

- 进口国：中国。
- 观察期：2008-2024 年。
- 观察单元：出口国 × 产品 × 年份。
- 产品范围：
  - `848620`：半导体器件或集成电路制造设备。
  - `854231`：处理器及控制器。
  - `854232`：存储器。
  - `854239`：其他电子集成电路。
- 在每个产品内部保留样本期内曾向中国出口该产品的出口国，并补齐 2008-2024 年；未出现的产品-出口国-年份贸易流按 0 处理。

现有 `v0.2` 多产品面板共 10608 行，其中正向贸易记录 5619 行。

## 4. 统计建模框架

论文采用三层模型框架。

### 4.1 来源结构测度

使用现有 `v0.2` 描述统计结果刻画每个产品的进口结构变化。

核心指标：

- 总进口额。
- 美国进口额。
- 美国进口份额。
- 主要来源国份额。
- HHI 来源集中度。
- 美国份额相对 2017 年的指数变化。

该层回答“结构是否发生变化”。现有结果显示，`848620`、`854231`、`854232` 的美国份额在 2017-2024 年下降，`854239` 则小幅上升，说明半导体相关产品之间存在异质性。

### 4.2 半导体进口供应链风险指数

新增综合风险指数，建议命名为：

> SIRI：Semiconductor Import Risk Index，半导体进口供应链风险指数

指数按产品-年份计算，分数越高表示该产品进口来源结构风险越高。

#### 4.2.1 输入与基础记号

对产品 `p`、年份 `t`、来源国 `i`，记进口额为 `v_{i,p,t}`。缺失贸易流按 0 处理，所有进口额需为非负数。

```text
V_{p,t} = sum_i v_{i,p,t}
s_{i,p,t} = v_{i,p,t} / V_{p,t}, if V_{p,t} > 0
s_{i,p,t} = 0, if V_{p,t} = 0
```

其中 `s_{US,p,t}` 表示美国份额。如果某产品-年份没有美国记录，则 `s_{US,p,t}=0`。若某产品-年份总进口额为 0，则所有份额类指标记为 0，并在验证日志中记录该异常；当前 BACI 样本理论上不应出现核心产品全年总进口额为 0 的情况。

SIRI 包含四个维度：

1. 来源集中风险：HHI 越高，风险越高。
2. 政策暴露风险：美国进口份额越高，在出口管制背景下的政策不确定性暴露越高。
3. 替代不足风险：非美国主要来源国数量越少、份额越集中，替代空间越弱。
4. 结构波动风险：相邻年份来源份额变化越大，供应链重组压力越高。

四个维度的原始指标定义如下：

```text
concentration_raw_{p,t} = sum_i s_{i,p,t}^2

policy_exposure_raw_{p,t} = s_{US,p,t}

non_us_share_{p,t} = 1 - s_{US,p,t}
q_{i,p,t} = s_{i,p,t} / non_us_share_{p,t}, for i != US and non_us_share_{p,t} > 0
alternative_insufficiency_raw_{p,t} = sum_{i != US} q_{i,p,t}^2, if non_us_share_{p,t} > 0
alternative_insufficiency_raw_{p,t} = 1, if non_us_share_{p,t} = 0

structural_volatility_raw_{p,t}
= 0.5 * sum_i abs(s_{i,p,t} - s_{i,p,t-1}), if t is not the first year for product p
structural_volatility_raw_{p,t} = 0, if t is the first year for product p
```

解释：

- `concentration_raw` 使用全来源 HHI，衡量总体集中度。
- `policy_exposure_raw` 使用美国份额，衡量出口管制背景下的政策暴露。
- `alternative_insufficiency_raw` 使用非美国来源内部 HHI，衡量替代来源是否集中于少数国家。该值越高，说明非美国替代来源越集中，替代弹性越弱。
- `structural_volatility_raw` 使用相邻年份来源份额的总变差距离，取值理论范围为 0-1。首年没有上一期可比值，记为 0，并在论文中说明首年不用于判断波动风险。

计算方式：

- 各维度先做 0-1 标准化。标准化范围使用全部产品-年份样本。
- 基准指数采用等权加总，降低主观赋权。
- 指数可放大到 0-100 分，便于论文展示。

标准化公式：

```text
norm(x_j) = (x_j - min(x)) / (max(x) - min(x)), if max(x) > min(x)
norm(x_j) = 0, if max(x) = min(x)
```

若某一维度在全部产品-年份样本中 `max=min`，说明该维度没有区分度，统一记为 0，并在验证日志中提示。

基准 SIRI：

```text
SIRI_{p,t}
= 100 * (
    0.25 * concentration_norm_{p,t}
  + 0.25 * policy_exposure_norm_{p,t}
  + 0.25 * alternative_insufficiency_norm_{p,t}
  + 0.25 * structural_volatility_norm_{p,t}
)
```

稳健性设计：

- 将“政策暴露风险”权重从 25% 提高到 40%，其余维度等比例调整。
- 比较产品风险排序是否基本稳定。
- 若排序稳定，说明指数结论不依赖单一权重设定。

敏感性权重：

```text
concentration = 0.20
policy_exposure = 0.40
alternative_insufficiency = 0.20
structural_volatility = 0.20
```

产品风险排序以最近一年 2024 年 SIRI 为主；如出现并列，按 2022-2024 年平均 SIRI 降序排序；仍并列时按产品代码升序排序。

### 4.3 政策节点统计检验

沿用现有固定效应回归作为支撑证据：

```text
ln(import_value + 1)
= beta1 * US_Post2018
+ beta2 * US_Post2022
+ beta3 * US_Post2023
+ exporter fixed effects
+ product fixed effects
+ year fixed effects
+ error
```

并保留现有份额型结果、分产品回归、产品组回归和稳健性检验。

解释口径：

- 描述统计与 SIRI 指数可以显示来源结构重组和产品风险差异。
- 固定效应回归结果不显著时，不回避、不弱化，而是作为“不能将结构变化简单归因为出口管制单一因素”的统计提醒。
- 论文将回归放在“统计检验与证据边界”章节，而不是把它作为唯一核心模型。

## 5. 需要补充的高性价比成果

一周内必须补充的增强项只保留三项：

1. SIRI 综合风险指数。
2. SIRI 趋势图和产品风险排序表。
3. 权重敏感性检验表。

可选增强项：

- 事件研究式趋势图，用于展示 2017 年前后美国份额或 SIRI 的变化，但不作为必须项。

不纳入本轮：

- GDELT 新闻数据。
- Goldstein 冲突指数。
- 图神经网络。
- 断链预警平台。
- 大量新产品扩展。
- 严格因果识别设计。

## 6. LaTeX 论文结构

新建 `paper/` 目录，使用 XeLaTeX 编译中文论文。建议文件结构：

```text
paper/
├── main.tex
├── references.bib
├── figures/
├── tables/
└── sections/
    ├── abstract.tex
    ├── introduction.tex
    ├── data.tex
    ├── descriptive.tex
    ├── risk_index.tex
    ├── regression.tex
    ├── conclusion.tex
    └── appendix.tex
```

论文章节：

1. 首页：标题、队伍信息、指导教师信息。
2. 摘要与关键词：摘要约 300-500 字，关键词 4-5 个。
3. 研究背景与问题提出。
4. 数据来源与变量构造。
5. 描述性统计与来源结构演化。
6. 半导体进口供应链风险指数构建。
7. 政策节点下的统计检验与稳健性分析。
8. 结论与政策建议。
9. 参考文献。
10. 附录：数据处理流程、变量定义、复现命令、补充表格、AI 工具使用说明草稿。

正文控制在 16000 字符以内。附录用于承载复现说明和补充材料。

队伍名称、成员、学校和指导教师属于外部输入。实施阶段先在 `paper/main.tex` 使用清晰的宏变量集中管理，例如 `\teamname{}`、`\members{}`、`\advisor{}`。这些信息不阻塞数据、模型和正文草稿交付，但最终提交版 PDF 必须由参赛队补齐，不应保留空白身份信息。

## 7. 图表规划

主文图表优先使用少量高信息密度材料。

建议主图：

1. 多产品总进口趋势图。
2. 美国进口份额趋势图。
3. 2024 年主要来源国结构图。
4. HHI 来源集中度趋势图。
5. SIRI 风险指数趋势图。

建议主表：

1. 产品代码与含义表。
2. 描述统计表。
3. SIRI 产品风险排序表。
4. 固定效应回归结果表。
5. 权重敏感性检验表。

补充表和完整模型输出放入附录。

## 8. 实施边界

允许修改或新增：

- `scripts/v02_analysis/risk_index.py`：新增 SIRI 计算、标准化、排序和敏感性分析函数。
- `scripts/v02_analysis/plots.py`：新增 SIRI 趋势图绘制函数，或在既有绘图模块中加入同等边界清晰的函数。
- `scripts/v02_analysis/reports.py`：如需要，将 SIRI 摘要写入阶段摘要。
- `scripts/run_v02_analysis.py` 中调用新增风险指数输出的入口。
- `results/v02/` 中新增风险指数数据、图表和表格。
- `paper/` 中新增 LaTeX 论文文件。
- `docs/superpowers/specs/` 中保存本设计文档。

不修改：

- `scripts/v01_analysis/`。
- `results/v01/`。
- 与本论文无关的项目配置。

建议函数边界：

```text
build_siri_panel(panel_df) -> DataFrame
normalize_siri_components(siri_df) -> DataFrame
compute_siri_scores(siri_df, weights) -> DataFrame
build_siri_ranking(siri_df, target_year=2024) -> DataFrame
build_siri_weight_sensitivity(siri_df) -> DataFrame
```

权重输入必须包含四个键：`concentration`、`policy_exposure`、`alternative_insufficiency`、`structural_volatility`。权重必须非负且总和为 1；否则抛出清晰错误，不静默修正。

新增产物契约：

```text
results/v02/data/siri_index_by_product_year_v02.csv
results/v02/tables/siri_index_by_product_year_v02.csv
results/v02/tables/siri_index_by_product_year_v02.md
results/v02/tables/siri_ranking_2024_v02.csv
results/v02/tables/siri_ranking_2024_v02.md
results/v02/tables/siri_weight_sensitivity_v02.csv
results/v02/tables/siri_weight_sensitivity_v02.md
results/v02/figures/siri_trend_by_product_v02.png
```

`siri_index_by_product_year_v02.csv` 字段：

```text
product_code
year
total_import_value_kusd
concentration_raw
policy_exposure_raw
alternative_insufficiency_raw
structural_volatility_raw
concentration_norm
policy_exposure_norm
alternative_insufficiency_norm
structural_volatility_norm
siri_score
siri_score_policy_weighted
```

`siri_ranking_2024_v02.csv` 字段：

```text
rank
product_code
product_name
year
siri_score
siri_score_policy_weighted
rank_policy_weighted
rank_change
```

其中 `product_name` 映射自现有产品元数据中的产品描述字段；若实现时字段名为 `product_description`，输出论文表格前统一重命名为 `product_name`。

`siri_weight_sensitivity_v02.csv` 字段：

```text
product_code
product_name
baseline_rank
policy_weighted_rank
rank_change
baseline_siri_score
policy_weighted_siri_score
```

## 9. 验证方式

代码侧：

- 跑通 `scripts/run_v02_analysis.py`。
- 检查新增 CSV、Markdown 表和 PNG 图是否生成。
- 检查 SIRI 是否在预期范围内。
- 检查产品-年份覆盖是否完整。
- 检查权重敏感性表是否可复现。

建议验证命令：

```bash
.venv/bin/python scripts/run_v02_analysis.py
```

验收标准：

- `siri_index_by_product_year_v02.csv` 应覆盖 4 个产品 × 17 年 = 68 行。
- `siri_score` 与 `siri_score_policy_weighted` 均应在 0-100 之间。
- `product_code`、`year`、四个 raw 指标、四个 norm 指标和两个 SIRI 分数不得缺失。
- `year` 应完整覆盖 2008-2024 年。
- 标准化指标应在 0-1 之间。
- 若出现产品-年份总进口额为 0、标准化维度 `max=min`、缺失美国记录等情况，脚本应记录说明并按本设计规则处理。
- 权重敏感性表应包含全部 4 个产品，`rank_change` 可为负数、0 或正数。
- 图表 `siri_trend_by_product_v02.png` 应非空生成。
- 验证日志优先写入现有 `docs/output/log_v0.2.md`；如果现有日志生成流程不适合追加，则新增 `docs/output/siri_validation_v0.2.md`。

论文侧：

- 使用 `xelatex` 或 `latexmk -xelatex` 编译 `paper/main.tex`。
- 检查图表路径、交叉引用、参考文献和中文字体。
- 粗略检查正文字符数，确保不超过官方限制。
- 输出 PDF 作为阶段成果。

## 10. 一周交付节奏

1. 补 SIRI 指标、图表和表格，保证数据成果完整。
2. 搭建 LaTeX 模板与章节骨架，把现有摘要和结果迁入论文。
3. 写完整初稿，重点完成背景、数据、模型和结果解释。
4. 压缩字数、统一图表风格、补参考文献和附录。
5. 做查重前自检、AI 使用说明草稿、最终编译和提交包整理。

## 11. AI 工具使用说明边界

由于大赛要求提交 AI 工具使用情况表，论文工作中应保留可说明的使用边界。建议表述为：AI 工具用于论文结构建议、代码辅助、LaTeX 排版辅助和文字润色建议；数据来源、模型设定、结果解释和最终结论由参赛队审核确认。

该说明不是负面声明，而是为了满足竞赛材料要求，避免后续查重、原创性说明和答辩时出现不必要的解释风险。

实施阶段应同步维护 `paper/ai_usage_notes.md`，记录下列字段，便于最终填写官方 AI 工具使用情况表：

```text
date
tool_name
usage_stage
specific_task
human_review_action
included_in_final_paper
estimated_generated_content_share
notes
```

建议记录口径保持克制，强调参赛队人工审核和最终确认：

- `usage_stage` 可填：选题设计、代码辅助、图表说明、LaTeX 排版、文字润色、查错审阅。
- `specific_task` 写具体任务，例如“提供 SIRI 指标公式备选方案，由参赛队筛选确认”“协助生成 LaTeX 表格结构”。
- `human_review_action` 写参赛队做了什么审核，例如“核对数据结果后改写”“删除不准确表述”“仅采纳格式建议”。
- `included_in_final_paper` 用 `yes/no/partial`。
- `estimated_generated_content_share` 用区间，例如 `0%`、`1-10%`、`10-30%`。

最终提交前，根据官方表格字段再做一次格式映射；若官方表格字段不同，以官方表格为准。

## 12. 最终结论口径

论文最终结论建议控制为：

> 本文发现，中国半导体相关产品进口来源结构在 2018 年后出现明显重组，美国份额在设备和部分集成电路产品中下降，产品间风险暴露存在显著异质性。综合风险指数可为关键产品进口安全监测提供可解释工具，但现有固定效应模型不支持将变化简单归因为美国出口管制的严格因果效应。
