# results 目录说明

`results/` 按版本保存分析输出，避免不同阶段的结果混在同一层。

```text
results/
├── v01/
│   ├── data/      # v0.1 单产品清洗数据
│   ├── figures/   # v0.1 单产品图表
│   └── tables/    # v0.1 描述统计、回归和测试表
└── v02/
    ├── data/      # v0.2 多产品清洗数据
    ├── figures/   # v0.2 多产品图表
    └── tables/    # v0.2 筛查表、回归、稳健性和测试表
```

当前建议优先使用 `v02/`，`v01/` 作为单产品基线版本保留。

复跑入口：

```bash
.venv/bin/python scripts/run_v01_analysis.py
.venv/bin/python scripts/run_v02_analysis.py
```
