# v0.3 Paper Section Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add v0.3 as a正文“预测与预警扩展” section that presents the BACI-only trade-network SIRI prediction work without overstating GDELT or causal claims.

**Architecture:** Keep v0.2 descriptive/SIRI/regression sections as the paper's core evidence. Add one new focused LaTeX section after regression and before conclusion, supported by compact v0.3 tables and one optional figure. Use existing v0.3 outputs from `results/v03_gcn/` as source data and preserve clear wording boundaries: BACI-only, exploratory prediction, not causal evidence.

**Tech Stack:** LaTeX (`ctexart`, `booktabs`, `graphicx`), Python/pandas for table generation if needed, existing project scripts and outputs.

---

## Source Context

**Spec:** `docs/superpowers/specs/2026-04-29-v03-paper-section-design.md`

**Existing v0.3 evidence:**
- `results/v03_gcn/data/gcn_product_pool_v03.csv`
- `results/v03_gcn/data/graph_samples_v03.csv`
- `results/v03_gcn/data/graph_level_features_v03.csv`
- `results/v03_gcn/data/gcn_predictions.csv`
- `results/v03_gcn/tables/gcn_metrics.csv`
- `results/v03_gcn/tables/validation_v03_gcn.csv`
- `results/v03_gcn/figures/gcn_actual_vs_predicted_siri.png`

**Current paper structure:**
- `paper/main.tex` inputs sections in this order: introduction, data, descriptive, risk_index, regression, conclusion, appendix.
- New v0.3 section should be inserted between `regression` and `conclusion`.

## File Structure

**Create:**
- `paper/sections/prediction_extension.tex`
  New正文 section explaining the v0.3 BACI-only trade-network prediction extension.

- `paper/tables/v03_prediction_overview.tex`
  Compact overview of product count, usable graph count, split sample count, and GDELT status.

- `paper/tables/v03_prediction_metrics.tex`
  Compact test-set metrics comparing `naive`, `ridge`, and `gcn_numpy` for all 20 model products and core 4 products.

**Modify:**
- `paper/main.tex`
  Add `\input{sections/prediction_extension}` after regression and before conclusion.

- `paper/sections/abstract.tex`
  Add one sentence about the v0.3 trade-network prediction extension.

- `paper/sections/introduction.tex`
  Update contribution paragraph to mention the prediction/prewarning extension.

- `paper/sections/conclusion.tex`
  Add a guarded conclusion sentence about v0.3 and its BACI-only/GDELT limitation.

- `paper/sections/appendix.tex`
  Add v0.3 reproduction command and clarify that GDELT is not enabled in current paper results.

**Optional Modify:**
- `paper/figures/gcn_actual_vs_predicted_siri.png`
  Copy from `results/v03_gcn/figures/` only if the new section includes the scatter plot.

---

## Chunk 1: v0.3 Paper Tables

### Task 1: Create v0.3 overview table

**Files:**
- Create: `paper/tables/v03_prediction_overview.tex`
- Read: `results/v03_gcn/tables/validation_v03_gcn.csv`
- Read: `results/v03_gcn/data/graph_samples_v03.csv`
- Read: `results/v03_gcn/data/gcn_product_pool_v03.csv`

- [ ] **Step 1: Verify source counts**

Run:

```bash
.venv/bin/python - <<'PY'
import pandas as pd
pool = pd.read_csv("results/v03_gcn/data/gcn_product_pool_v03.csv")
graphs = pd.read_csv("results/v03_gcn/data/graph_samples_v03.csv")
print("model_products", (pool["model_status"] == "model").sum())
print("usable_graphs", (graphs["status"] == "usable").sum())
print(graphs.loc[graphs["status"] == "usable", "split"].value_counts().sort_index().to_dict())
PY
```

Expected:

```text
model_products 20
usable_graphs 320
{'test': 40, 'train': 240, 'validation': 40}
```

- [ ] **Step 2: Create LaTeX table**

Create `paper/tables/v03_prediction_overview.tex` with a `table` environment and `booktabs`.

Table rows:
- 扩展产品数: `20`
- 年度图样本数: `320`
- 训练样本: `240`
- 验证样本: `40`
- 测试样本: `40`
- GDELT 状态: `未启用（BACI-only）`

Use caption:

```latex
\caption{v0.3 贸易网络预测扩展样本概况}
```

Use label:

```latex
\label{tab:v03-overview}
```

- [ ] **Step 3: Inspect table compiles syntactically**

Run:

```bash
sed -n '1,120p' paper/tables/v03_prediction_overview.tex
```

Expected: table uses `\begin{table}`, `\toprule`, `\midrule`, `\bottomrule`, and `\end{table}`.

### Task 2: Create v0.3 metrics comparison table

**Files:**
- Create: `paper/tables/v03_prediction_metrics.tex`
- Read: `results/v03_gcn/tables/gcn_metrics.csv`

- [ ] **Step 1: Verify exact test metrics**

Run:

```bash
.venv/bin/python - <<'PY'
import pandas as pd
m = pd.read_csv("results/v03_gcn/tables/gcn_metrics.csv")
cols = ["model", "sample_scope", "mae", "rmse", "spearman_rank_corr", "n_samples", "n_products"]
print(m.loc[m["split"] == "test", cols].to_string(index=False))
PY
```

Expected: six rows, covering `naive`, `ridge`, `gcn_numpy` for `all_model_products` and `core4_model_products`.

- [ ] **Step 2: Create compact LaTeX table**

Create `paper/tables/v03_prediction_metrics.tex` with these columns:

```text
模型 & 样本范围 & MAE & RMSE & Spearman & 样本数
```

Use only `split == test` rows.

Use readable Chinese sample scope labels:
- `all_model_products` -> `全部20个产品`
- `core4_model_products` -> `核心4产品`

Round numeric metrics to 3 decimals.

Use caption:

```latex
\caption{v0.3 测试集预测指标比较}
```

Use label:

```latex
\label{tab:v03-metrics}
```

- [ ] **Step 3: Check wording in table note**

Add a short note below the table:

```latex
\footnotesize 注：当前 v0.3 结果为 BACI-only 贸易网络预测扩展，未接入真实 GDELT 新闻事件数据。
```

---

## Chunk 2: New Prediction Extension Section

### Task 3: Add正文 section for v0.3

**Files:**
- Create: `paper/sections/prediction_extension.tex`
- Read: `docs/superpowers/specs/2026-04-29-v03-paper-section-design.md`
- Read: `docs/superpowers/specs/2026-04-28-dynamic-gcn-gdelt-design.md`

- [ ] **Step 1: Draft section structure**

Create the section with this title:

```latex
\section{预测与预警扩展：基于贸易网络的 SIRI 风险预测}
```

Include four paragraphs:

1. Motivation: v0.2 explains structure and risk; v0.3 asks whether SIRI can be predicted one year ahead.
2. Data/network construction: 20 HS6 products, annual China-import source graphs, source-country nodes, China node, import-share edge weights.
3. Prediction design: use year `t` network and risk features to predict `t+1` SIRI; compare naive, ridge, and `gcn_numpy`.
4. Results/interpretation: validation passed; simple baselines remain strong; graph model is exploratory; no GDELT enabled.

- [ ] **Step 2: Insert overview table**

After the network construction paragraph, add:

```latex
\input{tables/v03_prediction_overview}
```

- [ ] **Step 3: Insert metrics table**

After the model comparison paragraph, add:

```latex
\input{tables/v03_prediction_metrics}
```

- [ ] **Step 4: Use guarded conclusion wording**

Ensure the section includes this substance in Chinese:

```text
年度样本下复杂贸易网络模型并未稳定优于简单基线，但该扩展证明 SIRI 可以被组织为下一年风险预测任务，并为后续接入 GDELT 新闻事件压力变量提供了数据结构和评估框架。
```

Do not use these claims:
- `显著优于`
- `已经接入 GDELT`
- `证明出口管制因果效应`
- `实时预警平台`

### Task 4: Wire section into main LaTeX

**Files:**
- Modify: `paper/main.tex`

- [ ] **Step 1: Add section input**

Insert after:

```latex
\input{sections/regression}
```

this line:

```latex
\input{sections/prediction_extension}
```

- [ ] **Step 2: Verify input order**

Run:

```bash
rg -n "\\\\input\\{sections/" paper/main.tex
```

Expected order:

```text
introduction
data
descriptive
risk_index
regression
prediction_extension
conclusion
appendix
```

---

## Chunk 3: Front/Back Matter Updates

### Task 5: Update abstract carefully

**Files:**
- Modify: `paper/sections/abstract.tex`

- [ ] **Step 1: Add one sentence**

Add one sentence before the final framework sentence:

```text
进一步地，本文将产品池扩展至 20 个半导体相关 HS6 编码，构造年度进口来源网络，并探索基于贸易网络特征预测下一年 SIRI 风险的可行性。
```

- [ ] **Step 2: Do not overemphasize v0.3**

Check that abstract still frames v0.2 descriptive/SIRI/regression as the main evidence and does not mention GDELT as completed.

Run:

```bash
rg -n "GDELT|Goldstein|显著优于|因果" paper/sections/abstract.tex
```

Expected: no `GDELT` or `Goldstein`; `因果` may appear only in the existing cautious regression sentence.

### Task 6: Update introduction contribution paragraph

**Files:**
- Modify: `paper/sections/introduction.tex`

- [ ] **Step 1: Extend contribution paragraph**

Revise the final contribution paragraph from three contributions to four, or merge the fourth into the third:

```text
其四，进一步将 SIRI 风险指数组织为下一年预测任务，构建 BACI-only 年度贸易网络样本，为后续接入新闻事件压力变量和供应链预警扩展提供可复现的数据结构。
```

- [ ] **Step 2: Preserve cautious scope**

Ensure introduction does not claim full GDELT modeling.

Run:

```bash
rg -n "GDELT|Goldstein|新闻事件压力" paper/sections/introduction.tex
```

Expected: either no match, or only future-oriented wording.

### Task 7: Update conclusion and limitations

**Files:**
- Modify: `paper/sections/conclusion.tex`

- [ ] **Step 1: Add fourth finding or extension paragraph**

After the fixed-effect regression finding, add:

```text
第四，预测扩展结果表明，年度贸易网络可以为 SIRI 风险预测提供结构化输入。当前 BACI-only 设定下，简单基线模型在全产品测试集上仍具有较强竞争力，说明年度样本下复杂图模型优势有限；但该框架为后续接入 GDELT 新闻事件压力变量和更高频风险监测提供了可扩展基础。
```

- [ ] **Step 2: Update limitation paragraph**

Add current v0.3 limitation:

```text
预测扩展尚未接入真实 GDELT 新闻事件数据，图模型结果应理解为贸易网络预测框架的原型验证。
```

- [ ] **Step 3: Check overclaiming**

Run:

```bash
rg -n "显著优于|证明|实时|GDELT 新闻事件压力建模" paper/sections/conclusion.tex
```

Expected: no overclaiming phrases.

### Task 8: Update appendix reproduction note

**Files:**
- Modify: `paper/sections/appendix.tex`

- [ ] **Step 1: Add v0.3 command**

Under reproduction commands, add:

```latex
.venv/bin/python scripts/run_v03_gcn_analysis.py --baci-only
```

- [ ] **Step 2: Add one explanatory sentence**

Add:

```text
本文 v0.3 扩展结果使用 BACI-only 模式生成；若需启用 GDELT 新闻事件压力变量，需要另行准备预筛选后的 GDELT 事件 CSV。
```

---

## Chunk 4: Build, Verification, and Commit

### Task 9: Compile paper

**Files:**
- Read/write: `paper/main.pdf`

- [ ] **Step 1: Compile LaTeX**

Run from project root:

```bash
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
```

If `latexmk` is unavailable, use the existing local TeX command available on the machine, then document the command used.

- [ ] **Step 2: Inspect compile result**

Expected:
- command exits `0`
- `paper/main.pdf` updated
- no missing input table/section errors

### Task 10: Run project verification

**Files:**
- Read: test outputs

- [ ] **Step 1: Run unit tests**

Run:

```bash
.venv/bin/python -m unittest discover -v
```

Expected:

```text
Ran 29 tests
OK
```

- [ ] **Step 2: Verify v0.3 validation table**

Run:

```bash
sed -n '1,120p' results/v03_gcn/tables/validation_v03_gcn.csv
```

Expected: all four `passed` values are `1`.

- [ ] **Step 3: Search paper for forbidden claims**

Run:

```bash
rg -n "已完成 GDELT|显著优于所有|证明美国出口管制|实时断链预警平台|Goldstein 指标解释为真实政策强度" paper
```

Expected: no matches.

### Task 11: Commit focused paper update

**Files:**
- Stage only paper source files, new paper tables, and optional copied figure.
- Do not accidentally stage raw BACI data.

- [ ] **Step 1: Review git status**

Run:

```bash
git status --short
```

- [ ] **Step 2: Stage intended files**

Example:

```bash
git add paper/main.tex \
  paper/sections/abstract.tex \
  paper/sections/introduction.tex \
  paper/sections/conclusion.tex \
  paper/sections/appendix.tex \
  paper/sections/prediction_extension.tex \
  paper/tables/v03_prediction_overview.tex \
  paper/tables/v03_prediction_metrics.tex
```

Include `paper/main.pdf` only if compiled and intended for version control in this repo.

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "paper: add v03 prediction extension section"
```

Expected: commit succeeds and contains only the paper update files.

---

## Final Review Checklist

- [ ] v0.3 is in正文 as one section after regression.
- [ ] v0.3 is clearly marked as BACI-only.
- [ ] No completed GDELT claim appears in the paper.
- [ ] No causal interpretation is attached to prediction results.
- [ ] Tables cite 20 model products and 320 usable graph samples.
- [ ] Test-set metrics are rounded and readable.
- [ ] Paper compiles successfully.
- [ ] Unit tests still pass.
