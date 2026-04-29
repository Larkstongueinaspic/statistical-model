# 快速入门

测试前请先部署 BACI—HS07 数据库！
运行以下代码获得压缩包并在项目根目录内解压：

```bash
wget https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS07_V202601.zip
unzip BACI_HS07_V202601.zip
```

然后创建 Python 虚拟环境后安装 `requirements.txt` 依赖。

这是一个围绕“中国自美国进口半导体相关产品是否发生变化”展开的小型数据分析项目。  
当前版本的重点仍然不是复杂建模，而是把一条稳定、可复现、能支撑论文初稿实证章节的分析流水线跑通。

目前已经完成到 v0.2：

- 题目锁定为“美国出口管制对中国半导体相关产品进口的影响研究”
- 数据源固定为 `BACI HS07 2008-2024`
- v0.1 已完成单产品 `HS6=848620`
- v0.2 已扩展到四个半导体相关产品：
  - `848620`：半导体器件或集成电路制造设备
  - `854231`：处理器及控制器
  - `854232`：存储器
  - `854239`：其他电子集成电路
- 已经具备从原始数据到多产品清洗数据、图表、回归表、稳健性检查和测试结果的完整脚本

产品含义以数据库里的 `BACI_HS07_V202601/product_codes_HS07_V202601.csv` 为准。

## 1. 概况

可以简单理解成一条数据流水线：

1. 从 BACI 原始贸易数据中筛出中国进口的半导体相关产品
2. 整理成适合画图和分析的结构化表格
3. 输出多产品描述统计图表
4. 运行带 `Post2018 / Post2022 / Post2023` 的固定效应回归
5. 补充分产品、产品组、份额型结果和稳健性检查
6. 生成结果表、日志、阶段总结和结果摘要

如果你没有统计或建模背景，先把它理解成：
一个 Python 数据工程 + 基础实证分析的小项目，不是一个复杂算法项目。

## 2. 当前主要结果

v0.2 的核心结论比 v0.1 更完整：

- `848620` 的美国份额从 `2017` 年 `27.92%` 降到 `2024` 年 `9.88%`
- `854231` 的美国份额从 `2017` 年 `12.47%` 降到 `2024` 年 `9.72%`
- `854232` 的美国份额从 `2017` 年 `0.95%` 降到 `2024` 年 `0.14%`
- `854239` 的美国份额从 `2017` 年 `2.82%` 升到 `2024` 年 `3.94%`，说明集成电路类产品并不是完全同向变化
- 多产品绝对额回归中，`US_Post2018 / US_Post2022 / US_Post2023` 均不显著
- 份额型结果方向偏负但不显著，更适合作为“美国份额承压”的补充展示，而不是强因果证据

当前最稳妥的写法是：

> 描述统计支持中国半导体相关产品进口来源结构发生重组，美国份额在设备和部分集成电路产品中下降；但简化固定效应模型仍不能支持“美国出口额显著下降”的强因果表述。

## 3. 目录结构

```text
.
├── README.md
├── requirements.txt
├── docs/
│   ├── project/       # 论文框架和工作栈
│   ├── prompts/       # v0.1 / v0.2 执行 prompt
│   └── output/        # 工作日志、结果摘要、阶段总结
├── scripts/
│   ├── run_v01_analysis.py
│   ├── run_v02_analysis.py
│   ├── v01_analysis/  # v0.1 单产品流程
│   └── v02_analysis/  # v0.2 多产品流程
├── results/
│   ├── v01/           # v0.1 单产品数据、图表、表格输出
│   └── v02/           # v0.2 数据、图表、表格输出
└── BACI_HS07_V202601/ # 原始 BACI 数据（本地大文件，不建议纳入版本控制）
```

## 4. 核心模块分工

v0.2 当前是主线。

- `scripts/run_v02_analysis.py`
  主入口。想跑完整个 v0.2 流程时，直接运行这个文件。

- `scripts/v02_analysis/config.py`
  放路径、年份范围、候选产品编码、国家代码等配置。

- `scripts/v02_analysis/datasets.py`
  负责读取 BACI 原始数据、做候选产品筛查、构造多产品面板、年度汇总和主要来源国表。

- `scripts/v02_analysis/models.py`
  负责分阶段政策节点回归、份额型结果、分产品回归、产品组回归和稳健性检查。

- `scripts/v02_analysis/plots.py`
  负责输出多产品总进口、美国进口、美国份额、2024 来源结构、HHI 和产品组图。

- `scripts/v02_analysis/validation.py`
  负责自动检查产品元数据、年份覆盖、样本口径、面板行数、政策变量、图表表格一致性和回归样本数。

- `scripts/v02_analysis/reports.py`
  负责生成 `summary_v0.2.md` 和 `abstract_v0.2.md`。

- `scripts/v02_analysis/storage.py`
  负责把 CSV、Markdown 表和文本结果写入 `results/v02/`。

v0.1 仍然保留，用于复现单产品基线：

- `scripts/run_v01_analysis.py`
- `scripts/v01_analysis/`

## 5. 环境准备

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 6. 运行

确保原始数据目录 `BACI_HS07_V202601/` 已放在项目根目录后，执行 v0.2：

```bash
.venv/bin/python scripts/run_v02_analysis.py
```

运行完成的主要输出在：

- `results/v02/data/`
- `results/v02/figures/`
- `results/v02/tables/`

文档类输出在：

- `docs/output/log_v0.2.md`
- `docs/output/summary_v0.2.md`
- `docs/output/abstract_v0.2.md`

如果需要复现 v0.1 单产品基线，执行：

```bash
.venv/bin/python scripts/run_v01_analysis.py
```

v0.1 输出仍在：

- `results/v01/data/`
- `results/v01/figures/`
- `results/v01/tables/`
- `docs/output/summary_v0.1.md`
- `docs/output/abstract_v0.1.md`

## 7. 当前分析范围

v0.2 仍然保持小而稳，主要做：

- 进口国固定为中国
- 年份固定为 `2008-2024`
- 产品固定为 `848620 / 854231 / 854232 / 854239`
- 政策节点使用 `Post2018 / Post2022 / Post2023`
- 观察单元为 `出口国 × 产品 × 年份`
- 未出现的产品-出口国-年份贸易流按 `0` 填充
- 模型以固定效应回归、份额型结果和稳健性检查为主

当前仍然不急着做：

- GDELT
- Goldstein 冲突量表
- 新闻文本抽取
- 图神经网络
- 全球预警平台
- 复杂因果识别设计
- 大量外部控制变量

本分支例外：`gcn-gdelt-clean` 只作为 v0.3 探索性扩展，新增 `scripts/v03_gcn/` 和
`scripts/run_v03_gcn_analysis.py`。v0.3 可以跑 BACI-only 图模型，也可以在提供真实
GDELT 事件 CSV 后生成 GDELT 压力变量；这不改变 v0.2 作为论文主线的定位。

v0.3 常用命令：

```bash
python scripts/run_v03_gcn_analysis.py --baci-only
python scripts/run_v03_gcn_analysis.py --gdelt-events data/gdelt/prefiltered_events.csv
```

GDELT CSV 至少需要这些列：

- `SQLDATE`
- `Actor1CountryCode`
- `Actor2CountryCode`
- `GoldsteinScale`
- `NumMentions`
- `AvgTone`

如果开启内置关键词过滤，还需要 `SOURCEURL`、`DocumentIdentifier` 或 `EventText` 之一。

## 8. 上手顺序

如果刚接手，建议按这个顺序看：

1. 先读 `docs/project/最小可行论文框架.md`
2. 再读 `docs/project/工作栈.md`
3. 看 `docs/output/summary_v0.2.md`
4. 跑一遍 `scripts/run_v02_analysis.py`
5. 看 `scripts/v02_analysis/config.py` 和 `runner.py`
6. 再看 `datasets.py`，理解多产品样本是怎么整理出来的
7. 最后看 `models.py`、`plots.py` 和 `validation.py`

如果只想理解 v0.1 与 v0.2 的区别：

1. 先读 `docs/output/summary_v0.1.md`
2. 再读 `docs/output/summary_v0.2.md`
3. 对比 `scripts/run_v01_analysis.py` 和 `scripts/run_v02_analysis.py`

## 9. 下一步做什么

最自然的扩展方向：

1. 补一张政策事件时间线图，明确 `2018 / 2022 / 2023` 节点的制度含义
2. 对主要来源国做地区或产业链分组，解释设备类和集成电路类的替代来源差异
3. 做简单事件研究式图表，展示美国相对主要来源国的年份变化
4. 如果继续加强识别，优先考虑出口国-产品固定效应或更清晰的对照组，而不是马上引入复杂外部数据

## 10. 注意事项

- BACI 原始数据体量较大，脚本已经按分块读取处理，不要轻易改成整文件一次性读入。
- v0.1 输出和 v0.2 输出是分开的，v0.1 统一写入 `results/v01/`，v0.2 统一写入 `results/v02/`。
- 如果要改样本范围，优先改 `scripts/v02_analysis/config.py`，不要在多个文件里手工改常量。
- 当前结论不能写成“美国出口管制已经显著压低中国自美国进口额”。更稳妥的说法是“来源结构重组、美国份额在多数核心产品中承压，但简化模型不支持强因果结论”。
