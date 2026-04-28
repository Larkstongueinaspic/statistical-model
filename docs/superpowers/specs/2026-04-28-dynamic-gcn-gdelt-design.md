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

## 4. 动态图构造

每个 `product_code, year` 构造一张“中国进口来源国图”。

图定义：

- 节点：该产品该年对中国有贸易记录的来源国，加中国节点。
- 边：来源国 -> 中国。
- 边权重：该来源国向中国出口该产品的进口额或进口份额。
- 时间：年度图快照，2008-2024。
- 样本单位：一个 `product_code, year` 图样本。

节点特征：

| 特征 | 含义 |
| --- | --- |
| `import_share` | 来源国在该产品该年中国进口中的份额 |
| `ln_import_value` | `log(import_value_kusd + 1)` |
| `is_usa` | 是否美国 |
| `is_china` | 是否中国节点 |
| `source_rank_norm` | 来源国排名归一化 |
| `source_hhi_context` | 产品年度来源集中度 |
| `gdelt_pressure_score` | 出口国-中国年度 GDELT 科技摩擦压力 |

为了适配普通 GCN，图中允许加入反向边 `中国 -> 来源国`，但输出文档必须记录是否启用反向边。

标签：

```text
target = SIRI(product_code, year + 1)
```

输出中每条预测记录必须包含：

```text
product_code, train_year, target_year, actual_siri, predicted_siri, error
```

## 5. GDELT 特征

GDELT 只作为轻量真实新闻事件压力特征，不做新闻全文建模。

聚合粒度：

- 国家对：出口国 - 中国
- 年份：2008-2024
- 主题：科技、半导体、芯片、出口管制、制裁、贸易限制等关键词或事件筛选条件

预期输入字段：

```text
SQLDATE, Actor1CountryCode, Actor2CountryCode, EventCode,
GoldsteinScale, NumMentions, AvgTone
```

年度聚合指标：

| 字段 | 含义 |
| --- | --- |
| `gdelt_event_count` | 相关事件数量 |
| `gdelt_avg_goldstein` | 平均 Goldstein 分数 |
| `gdelt_negative_goldstein_sum` | 负向 Goldstein 强度累计 |
| `gdelt_mentions` | 新闻提及数累计 |
| `gdelt_avg_tone` | 平均新闻语调 |
| `gdelt_pressure_score` | 标准化综合压力分数 |

压力分数建议：

```text
gdelt_pressure_score =
  z_or_minmax(gdelt_negative_goldstein_sum)
  + z_or_minmax(gdelt_event_count)
  + z_or_minmax(gdelt_mentions)
```

GDELT 文件策略：

- `data/gdelt/` 保存原始或手工下载缓存，不纳入 Git。
- `results/v03_gcn/data/gdelt_pressure_by_country_year.csv` 保存可复现聚合结果。
- 如果 GDELT 原始文件缺失，允许以 `disable_gdelt=True` 跑 BACI-only GCN，但报告必须明确标记 GDELT 未启用。
- 论文写 GDELT 结果前必须使用真实 GDELT 聚合文件，不能用零填充或示例数据冒充。

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

解释规则：

- 如果 GCN 优于基线，写“动态图特征改善了风险预测”。
- 如果 GCN 不优于基线，写“年度样本下复杂模型优势有限，但提供了可扩展预警框架”。

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

## 8. 错误处理

- BACI 原始目录不存在：停止并提示放置或软链接 `BACI_HS07_V202601`。
- HS6 编码不存在：写入剔除表，并从模型池剔除。
- 产品年份覆盖不足：写入剔除原因。
- GDELT 文件缺失：若 `disable_gdelt=True` 则继续 BACI-only；否则停止并提示准备 GDELT 文件。
- `torch` 缺失：训练入口停止并提示安装依赖。
- 图样本为空：跳过并记录 `product_code, year, reason`。
- 有效样本不足：停止训练并说明产品数、年份数和图样本数。

## 9. 测试

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

## 10. 论文产出

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

## 11. 实施前置条件

- 在 `statistical-model-gcn` worktree 中准备 `BACI_HS07_V202601/`，可复制原始数据或建立软链接。
- 准备 Python 环境。
- 新增依赖至少包括 `scikit-learn` 和 `torch`。
- 如果使用真实 GDELT，需准备本地 CSV 或允许脚本下载/读取缓存。

## 12. 成功标准

- v0.2 现有测试和流程不被破坏。
- v0.3 能生成产品池、动态图样本、SIRI 目标、基线结果、GCN 预测结果和图表。
- 输出明确区分核心 4 产品和扩展训练产品池。
- 报告明确说明是否启用真实 GDELT。
- 论文表述不夸大 GCN/GDELT 的因果含义。
