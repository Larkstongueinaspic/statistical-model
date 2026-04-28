# 年度动态图 GCN 与 GDELT 扩展设计

## 1. 目标

在现有 v0.2 贸易数据、SIRI 风险指数和固定效应回归主线之外，新增一个 v0.3 探索性预测模块：基于年度中国半导体相关产品进口网络，结合 GDELT 新闻事件压力特征，训练年度动态图 GCN，预测下一年产品级 SIRI 风险分数。

该模块定位为论文的“预测与预警扩展”，不替代现有 SIRI 和回归结果，不承担严格因果识别任务。

## 2. 非目标

- 不构建全球实时断链预警平台。
- 不做新闻全文 NLP、主题模型或大语言模型事件抽取。
- 不把 GDELT/Goldstein 指标解释为真实政策强度。
- 不把 GCN 结果写成出口管制因果效应证据。
- 不强依赖 PyTorch Geometric；第一版优先保证可复现。

## 3. 数据范围

### 3.1 年份

沿用现有 BACI HS07 数据范围：

- 原始年份：2008-2024
- 预测样本：用年份 `t` 预测 `t+1`
- 可用转移：2008->2009 到 2023->2024

### 3.2 产品池

核心论文产品仍是现有 4 个 HS6：

```text
848620, 854231, 854232, 854239
```

GCN 训练产品池扩展到以下真实 HS6 候选：

```text
848610, 848620, 848640, 848690,
854110, 854121, 854129, 854130, 854140, 854150, 854160, 854190,
854231, 854232, 854233, 854239, 854290,
853400, 903082, 903141
```

分组：

| 分组 | HS6 |
| --- | --- |
| semiconductor_equipment | 848610, 848620, 848640, 848690 |
| semiconductor_devices | 854110, 854121, 854129, 854130, 854140, 854150, 854160, 854190 |
| integrated_circuits | 854231, 854232, 854233, 854239, 854290 |
| related_hardware | 853400, 903082, 903141 |

实现时必须用 `BACI_HS07_V202601/product_codes_HS07_V202601.csv` 校验候选 HS6 是否存在。不存在、描述为空或无法通过覆盖率筛查的产品写入剔除表，不静默忽略。

产品池来源以 UNSD HS 分类为准，设计参考：

- `8486` 半导体制造相关设备分解：https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/en/32/8486
- `8541` 半导体器件分解：https://unstats.un.org/unsd/classifications/Econ/Detail/EN/2089/8541
- `8542` 集成电路分解：https://unstats.un.org/unsd/classifications/Econ/Detail/EN/2089/8542
- `853400` 印刷电路：https://unstats.un.org/unsd/classifications/Econ/Detail/EN/32/853400
- `903082` 半导体晶圆或器件测量检查仪器：https://unstats.un.org/unsd/classifications/Econ/Detail/EN/32/903082
- `903141` 半导体晶圆、器件或光掩模检查用光学仪器：https://unstats.un.org/unsd/classifications/Econ/Detail/EN/32/903141

### 3.3 产品纳入阈值

产品池校验输出三种状态：

| 状态 | 含义 |
| --- | --- |
| `model` | 进入 GCN 训练与评估 |
| `report_only` | 不进入训练，但若是核心 4 产品则保留在报告中说明 |
| `excluded` | 不进入模型或报告 |

进入 `model` 的默认阈值：

- HS6 存在于 BACI 产品代码表。
- 2008-2024 中至少 12 个年份存在正贸易记录。
- 至少 5 个不同来源国在样本期内对中国有正贸易记录。
- 至少 10 个 `t -> t+1` 转移存在可用 SIRI 标签。
- 样本期总进口额大于 0。

核心 4 产品只要 HS6 存在且总进口额大于 0，就至少保留为 `report_only`。如果核心产品同时满足上述阈值，则进入 `model`。

若最终 `model` 产品数少于 10 个，或带标签图样本少于 100 个，训练流程停止，并在验证表中说明样本不足。

### 3.4 2024 图样本

带标签训练和评估样本只使用 2008-2023 的图，因为标签是 `year + 1` 的 SIRI，最后一个可评估标签年是 2024。2024 图默认不进入训练、验证或测试。

2024 图可作为无标签 `forecast_2025` 输入，但第一版默认关闭；如果启用，只输出预测值，不计入任何评估指标。

## 4. 动态图构造

每个 `product_code, year` 构造一张“中国进口来源国图”。

图定义：

- 节点：该产品该年对中国有贸易记录的来源国，加中国节点。
- 边：来源国 -> 中国。
- 边权重：固定使用 `import_share`，即该来源国在该产品该年中国进口中的份额。
- 时间：年度图快照，2008-2024。
- 样本单位：一个 `product_code, year` 图样本。

图只纳入当年正贸易额来源国。若某产品某年没有任何正贸易来源国，该图跳过并记录原因。

节点特征：

| 特征 | 来源国节点 | 中国节点 |
| --- | --- | --- |
| `import_share` | 来源国份额 | `1.0` |
| `ln_import_value` | `log(import_value_kusd + 1)` | `log(product_year_total_kusd + 1)` |
| `is_usa` | 美国为 `1`，其他为 `0` | `0` |
| `is_china` | `0` | `1` |
| `source_rank_norm` | `(rank - 1) / max(source_count - 1, 1)`，最大来源国为 0 | `0` |
| `source_hhi_context` | 产品年度来源 HHI，所有节点同值 | 产品年度来源 HHI |
| `gdelt_pressure_score` | 来源国-中国年度压力分数；缺失为 0 | 按 `import_share` 加权的来源国压力均值 |

图卷积邻接矩阵：

- 默认加入反向边 `中国 -> 来源国`，权重同 `import_share`。
- 默认加入 self-loop。
- 手写 GCN 使用加权无向化邻接：`A = directed_edges + reverse_edges + I`。
- 归一化方式固定为 `A_norm = D^(-1/2) A D^(-1/2)`。
- `edge_weight_type` 默认为 `import_share`，不提供运行时切换，避免结果口径漂移。

标签：

```text
target = SIRI(product_code, year + 1)
```

标签来源：

- 优先由 v0.3 扩展产品池面板调用现有 `scripts.v02_analysis.risk_index.build_siri_outputs()` 重新计算。
- 使用字段：`product_code`, `year`, `siri_score`。
- 标签表命名：`results/v03_gcn/data/siri_targets_v03.csv`。
- 若某个 `product_code, year + 1` 缺少 SIRI 标签，对应图样本剔除并记录 `missing_target`。

输出中每条预测记录必须包含：

```text
product_code, train_year, target_year, actual_siri, predicted_siri, error
```

图样本索引输出 `graph_samples_v03.csv`：

```text
sample_id, product_code, graph_year, target_year, node_count,
edge_count, target_siri, split, status, skip_reason
```

## 5. GDELT 特征

GDELT 只作为轻量真实新闻事件压力特征，不做新闻全文建模。

聚合粒度：

- 国家对：出口国 - 中国
- 年份：2008-2024
- 主题：科技、半导体、芯片、出口管制、制裁、贸易限制等。第一版要求输入 CSV 已通过 GDELT 查询或外部脚本预筛选到相关主题；v0.3 模块只验证字段并做年度聚合。

预期输入字段：

```text
SQLDATE, Actor1CountryCode, Actor2CountryCode, EventCode,
GoldsteinScale, NumMentions, AvgTone
```

可选输入字段：

```text
EventRootCode, EventBaseCode, SOURCEURL, Actor1Name, Actor2Name
```

如果输入包含 `SOURCEURL` 或文本字段，可追加关键词过滤；如果没有文本字段，不在 v0.3 内二次做主题过滤，报告中标记为“pre-filtered GDELT events”。

国家代码映射：

- BACI 使用 `country_codes_V202601.csv` 中的 `country_iso3`。
- GDELT 事件字段使用 `Actor1CountryCode` / `Actor2CountryCode`。
- v0.3 生成 `country_code_crosswalk_v03.csv`，字段为 `exporter_code`, `exporter_iso3`, `gdelt_country_code`, `mapping_status`。
- 默认先用 `exporter_iso3 == gdelt_country_code` 精确匹配。
- 对无法匹配的来源国，压力特征填 0，并在 crosswalk 中标记 `missing_gdelt_code`。
- `Other Asia, nes` 等非标准地区节点默认填 0，不强行映射。

年度聚合指标：

| 字段 | 含义 |
| --- | --- |
| `gdelt_event_count` | 相关事件数量 |
| `gdelt_avg_goldstein` | 平均 Goldstein 分数 |
| `gdelt_negative_goldstein_sum` | `sum(max(-GoldsteinScale, 0) * max(NumMentions, 1))` |
| `gdelt_mentions` | 新闻提及数累计 |
| `gdelt_avg_tone` | 平均新闻语调 |
| `gdelt_pressure_score` | 标准化综合压力分数 |

压力分数建议：

```text
gdelt_pressure_score =
  mean(
    minmax_train(gdelt_negative_goldstein_sum),
    minmax_train(gdelt_event_count),
    minmax_train(gdelt_mentions)
  )
```

标准化规则：

- 固定使用 min-max。
- min/max 只在训练图年份 2008-2019 的 country-year 聚合值上拟合，避免时间泄漏。
- 验证/测试年份使用训练期 min/max 转换，并裁剪到 `[0, 1]`。
- 缺失 country-year 的原始聚合值填 0，再做标准化；若训练期 min=max，则该分量全部置 0。

GDELT 文件策略：

- `data/gdelt/` 保存原始或手工下载缓存，不纳入 Git。
- `results/v03_gcn/data/gdelt_pressure_by_country_year.csv` 保存可复现聚合结果。
- 如果 GDELT 原始文件缺失，允许以 `disable_gdelt=True` 跑 BACI-only GCN，但报告必须明确标记 GDELT 未启用。
- 论文写 GDELT 结果前必须使用真实 GDELT 聚合文件，不能用零填充或示例数据冒充。

`gdelt_pressure_by_country_year.csv` schema：

```text
exporter_code, exporter_iso3, gdelt_country_code, year,
gdelt_event_count, gdelt_avg_goldstein,
gdelt_negative_goldstein_sum, gdelt_mentions,
gdelt_avg_tone, gdelt_pressure_score
```

## 6. 模型与评估

第一版使用轻量图卷积回归模型：

```text
GCN encoder -> graph mean pooling -> MLP regression head
```

如果 `torch_geometric` 可用，可以使用 `GCNConv`。默认实现不依赖 `torch_geometric`，用纯 `torch` 实现简化图卷积：

```text
H = ReLU(A_norm X W)
graph_embedding = mean_pool(H)
prediction = MLP(graph_embedding)
```

时间切分：

| 集合 | 训练年份 | 目标年份 |
| --- | --- | --- |
| train | 2008-2019 | 2009-2020 |
| validation | 2020-2021 | 2021-2022 |
| test | 2022-2023 | 2023-2024 |

评估指标：

- MAE
- RMSE
- Spearman risk-rank correlation
- 核心 4 产品 MAE

必须包含基线：

| 基线 | 含义 |
| --- | --- |
| naive | 用上一年 SIRI 预测下一年 SIRI |
| ridge | 用聚合表格特征训练 Ridge 回归 |
| gcn | 用年度贸易图和 GDELT 特征训练图卷积模型 |

Ridge 使用的聚合表格特征固定为：

```text
current_siri_score,
concentration_raw,
policy_exposure_raw,
alternative_insufficiency_raw,
structural_volatility_raw,
log_total_import_value,
source_count,
top1_import_share,
usa_import_share,
weighted_gdelt_pressure_score,
product_group one-hot
```

其中 `current_siri_score` 为图年份 `t` 的 SIRI，标签为 `t+1` 的 SIRI。Ridge 只能使用与 GCN 同一图年份可见的信息。

解释规则：

- 如果 GCN 优于基线，写“动态图特征改善了风险预测”。
- 如果 GCN 不优于基线，写“年度样本下复杂模型优势有限，但提供了可扩展预警框架”。

`gcn_metrics.csv` schema：

```text
model, split, mae, rmse, spearman_rank_corr,
n_samples, n_products, uses_gdelt
```

`gcn_predictions.csv` schema：

```text
model, split, product_code, product_group, is_core_product,
train_year, target_year, actual_siri, predicted_siri, error,
uses_gdelt
```

## 7. 代码结构

新增 v0.3 GCN 模块，不破坏 v0.2：

```text
scripts/
  run_v03_gcn_analysis.py
  v03_gcn/
    __init__.py
    config.py
    product_pool.py
    trade_graphs.py
    gdelt.py
    siri_targets.py
    baselines.py
    gcn_model.py
    training.py
    plots.py
    reports.py
    validation.py
    storage.py
```

模块接口：

| 模块 | 主要输入 | 主要输出 | 核心职责 |
| --- | --- | --- | --- |
| `config.py` | CLI/defaults | `GcnConfig` | 集中管理路径、产品池、阈值、训练参数 |
| `product_pool.py` | BACI product codes, country codes | `gcn_product_pool_v03.csv`, crosswalk | 校验 HS6、分组、核心产品、国家代码映射 |
| `siri_targets.py` | 扩展产品 panel | `siri_targets_v03.csv` | 复用 SIRI 逻辑生成产品年标签 |
| `gdelt.py` | pre-filtered GDELT CSV, crosswalk | `gdelt_pressure_by_country_year.csv` | 聚合和标准化 GDELT 压力 |
| `trade_graphs.py` | panel, targets, gdelt pressure | `GraphSample` list, `graph_samples_v03.csv` | 构造年度产品图和节点特征 |
| `baselines.py` | graph-level feature table | baseline predictions, metrics | 训练 naive 和 Ridge 基线 |
| `gcn_model.py` | graph tensors | torch model | 定义简化 GCN |
| `training.py` | graph samples, config | predictions, metrics, model artifact | 时间切分、训练、验证、测试 |
| `plots.py` | predictions, metrics | figures | 输出预测图 |
| `reports.py` | outputs | summary markdown | 写 v0.3 总结 |
| `validation.py` | all outputs | validation table | 检查样本量、字段、GDELT 状态、指标 |
| `storage.py` | DataFrames/text/models | files | 统一写入结果目录 |

输出目录：

```text
results/v03_gcn/
  data/
  tables/
  figures/
  models/
docs/output/
  summary_v0.3_gcn.md
  abstract_v0.3_gcn.md
```

## 8. 配置项与默认值

| 配置 | 默认值 |
| --- | --- |
| `years` | `2008-2024` |
| `train_years` | `2008-2019` |
| `validation_years` | `2020-2021` |
| `test_years` | `2022-2023` |
| `min_positive_years` | `12` |
| `min_exporter_count` | `5` |
| `min_labeled_transitions` | `10` |
| `min_model_products` | `10` |
| `min_labeled_graphs` | `100` |
| `disable_gdelt` | `False` |
| `allow_baci_only` | CLI 显式开启 |
| `add_reverse_edges` | `True` |
| `add_self_loops` | `True` |
| `edge_weight_type` | `import_share` |
| `gdelt_scaler` | `train_minmax` |
| `random_seed` | `20260428` |
| `hidden_dim` | `32` |
| `epochs` | `300` |
| `learning_rate` | `0.001` |
| `weight_decay` | `0.0001` |
| `early_stopping_patience` | `30` |

## 9. 错误处理

- BACI 原始目录不存在：停止并提示放置或软链接 `BACI_HS07_V202601`。
- HS6 编码不存在：写入剔除表，并从模型池剔除。
- 产品年份覆盖不足：写入剔除原因。
- GDELT 文件缺失：若 `disable_gdelt=True` 则继续 BACI-only；否则停止并提示准备 GDELT 文件。
- `torch` 缺失：训练入口停止并提示安装依赖。
- 图样本为空：跳过并记录 `product_code, year, reason`。
- 有效样本不足：停止训练并说明产品数、年份数和图样本数。

## 10. 测试

新增测试：

```text
tests/test_v03_product_pool.py
tests/test_v03_trade_graphs.py
tests/test_v03_gdelt.py
tests/test_v03_baselines.py
tests/test_v03_training.py
```

测试覆盖：

- 产品池编码、分组、核心产品标记。
- 小样本能构造来源国 -> 中国图。
- 节点特征、边权、标签年份正确。
- 小型 GDELT CSV 能聚合年度压力指标。
- 缺失值和负 Goldstein 处理正确。
- naive/ridge 基线输出指标正确。
- toy graphs 能跑一轮训练流程。

## 11. 论文产出

目标产出：

```text
results/v03_gcn/data/gcn_product_pool_v03.csv
results/v03_gcn/data/gdelt_pressure_by_country_year.csv
results/v03_gcn/data/gcn_predictions.csv
results/v03_gcn/tables/gcn_metrics.csv
results/v03_gcn/tables/gcn_core_product_predictions.md
results/v03_gcn/figures/gcn_actual_vs_predicted_siri.png
results/v03_gcn/figures/gcn_core_product_forecast.png
docs/output/summary_v0.3_gcn.md
```

论文写法：

- 主体结论仍由描述统计、SIRI 和回归支撑。
- GCN 放入“预测与预警扩展”章节。
- GDELT 被称为“新闻事件压力代理变量”。
- GCN 结果被称为“探索性预测”，不作为因果证据。

## 12. 实施阶段

实施计划应拆为五个阶段，并在每个阶段运行对应验证：

1. 产品池、国家 crosswalk、扩展 panel 与 SIRI target。
2. GDELT 聚合与压力分数标准化。
3. 图样本构造与 graph-level 特征表。
4. naive/Ridge 基线与 GCN 训练评估。
5. 图表、summary、论文段落素材和最终验证。

## 13. 实施前置条件

- 在 `statistical-model-gcn` worktree 中准备 `BACI_HS07_V202601/`，可复制原始数据或建立软链接。
- 准备 Python 环境。
- 新增依赖至少包括 `scikit-learn` 和 `torch`。
- 如果使用真实 GDELT，需准备本地 CSV 或允许脚本下载/读取缓存。

## 14. 成功标准

- v0.2 现有测试和流程不被破坏。
- v0.3 能生成产品池、动态图样本、SIRI 目标、基线结果、GCN 预测结果和图表。
- 输出明确区分核心 4 产品和扩展训练产品池。
- 报告明确说明是否启用真实 GDELT。
- 论文表述不夸大 GCN/GDELT 的因果含义。
