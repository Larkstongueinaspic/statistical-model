# 快速入门

测试前请先部署 BACI—HS07 数据库！
运行以下代码获得压缩包并在文件夹内解压：
```bash
wget https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS07_V202601.zip
unzip BACI_HS07_V202601.zip
```

然后创建 Python 虚拟环境后安装 `requirements.txt` 依赖。

这是一个围绕“中国自美国进口半导体相关产品是否发生变化”展开的小型数据分析项目。  
当前版本的重点不是复杂建模，而是先把一条稳定、可复现的分析流水线跑通。

目前已经完成的是 v0.1：

- 题目锁定为“美国出口管制对中国半导体相关产品进口的影响研究”
- 主样本先做 `HS6=848620`。`id=848620`是`Machines and apparatus of a kind used solely or principally for the manufacture of semiconductor devices or of electronic integrated circuits`，其他id可以在数据库里的`product_codes_HS07_V202601.csv`看到
- 数据源固定为 `BACI HS07 2008-2024`
- 已经具备从原始数据到图表、回归表和测试结果的完整脚本

## 1. 概况

可以简单理解成一条数据流水线：

1. 从 BACI 原始贸易数据中筛出目标样本
2. 整理成适合画图和分析的结构化表格
3. 输出描述统计图表
4. 运行一个最小可行的基准回归和两项稳健性检查
5. 生成结果表、日志和阶段总结

如果你没有统计或建模背景，先把它理解成：
一个 Python 数据工程 + 基础分析的小项目，不是一个复杂算法项目。

## 2. 目录结构

```text
.
├── README.md
├── requirements.txt
├── docs/
│   └── output/       # 工作日志、结果摘要、阶段总结
├── scripts/
│   ├── run_v01_analysis.py
│   └── v01_analysis/
│       ├── config.py
│       ├── datasets.py
│       ├── models.py
│       ├── plots.py
│       ├── runner.py
│       ├── storage.py
│       └── validation.py
├── results/          # 运行后生成的数据、图表、表格
└── BACI_HS07_V202601/ # 原始 BACI 数据（本地大文件，不建议纳入版本控制）
```

## 3. 核心模块分工

- `scripts/run_v01_analysis.py`
  主入口。想跑完整个 v0.1 流程时，直接运行这个文件。

- `scripts/v01_analysis/config.py`
  放路径、年份范围、产品编码等配置。

- `scripts/v01_analysis/datasets.py`
  负责读取 BACI 原始数据、筛选目标样本、构造平衡面板和描述性表格。

- `scripts/v01_analysis/models.py`
  负责基准回归与稳健性回归。

- `scripts/v01_analysis/plots.py`
  负责把汇总后的数据画成趋势图、份额图和 HHI 图。

- `scripts/v01_analysis/validation.py`
  负责自动检查样本是否完整、图表与表格是否一致、回归样本数是否合理。

- `scripts/v01_analysis/storage.py`
  负责把 CSV、Markdown 表和文本结果写入 `results/`。

## 4. 环境准备

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 5. 运行

确保原始数据目录 `BACI_HS07_V202601/` 已放在项目根目录后，执行：

```bash
.venv/bin/python scripts/run_v01_analysis.py
```

运行完成的主要输出在：

- `results/data/`
- `results/figures/`
- `results/tables/`

文档类输出在：

- `docs/output/abstract_v0.1.md`
- `docs/output/summary_v0.1.md`

## 6. 当前分析范围

v0.1 故意做得很小，目的是先跑通：

- 只做一个产品：`848620`
- 只做年度数据：`2008-2024`
- 只做一个最基础的政策节点：`2018`
- 只做一个最基础的比较模型

当前不急着做：

- GDELT
- Goldstein 冲突量表
- 新闻文本抽取
- 图神经网络
- 全球预警平台
- 复杂因果识别设计

## 7. 上手顺序

如果刚接手，建议按这个顺序看：

1. 先读 `docs/project/最小可行论文框架.md`
2. 再读 `docs/project/工作栈.md`
3. 跑一遍 `scripts/run_v01_analysis.py`
4. 看 `scripts/v01_analysis/config.py` 和 `runner.py`
5. 再看 `datasets.py`，理解样本是怎么整理出来的
6. 最后再看 `models.py` 和 `plots.py`

## 8. 下一步做什么

最自然的扩展方向：

1. 从单产品扩展到 `2-3` 个产品
2. 把政策节点从 `2018` 扩展到 `2022/2023`
3. 优化脚本配置和输出组织，让多产品版本更容易跑

## 9. 注意事项

- BACI 原始数据体量较大，脚本已经按分块读取处理，不要轻易改成整文件一次性读入。
- 当前 `results/` 和原始数据目录默认不进 Git。
- 如果要改样本范围，改 `config.py`，不要在多个文件里手工改常量。