# Policy Timeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hand-curated policy background timeline to the competition paper without claiming GDELT, Goldstein, news-text modeling, GCN, or warning-system results.

**Architecture:** Keep the current paper structure. Modify only the introduction and, if needed, the compiled PDF artifact. Do not change data, model outputs, SIRI formulas, regression tables, or figures.

**Tech Stack:** XeLaTeX, `ctexart`, existing `booktabs`/`float` LaTeX packages, shell verification with `rg` and `git diff --check`.

---

## File Structure

- Modify: `paper/sections/introduction.tex`
  - Add one policy timeline table after the current policy-timeline paragraph.
  - Keep the existing GDELT boundary statement concise and consistent.
- Modify: `paper/main.pdf`
  - Regenerate by compiling `paper/main.tex`.

## Chunk 1: Add Policy Timeline Table

### Task 1: Insert Hand-Curated Timeline In Introduction

**Files:**
- Modify: `paper/sections/introduction.tex`

- [ ] **Step 1: Locate insertion point**

Run:

```bash
sed -n '1,80p' paper/sections/introduction.tex
```

Expected: the paragraph ending with “这些政策节点构成了本文实证分析的基本时间框架。” appears before the current research-boundary paragraph.

- [ ] **Step 2: Add timeline table**

Insert a `table` environment immediately after the policy-timeline paragraph:

```latex
\begin{table}[H]
    \centering
    \caption{半导体相关政策背景时间线}
    \label{tab:policy-timeline}
    \begin{tabular}{p{0.18\textwidth}p{0.50\textwidth}p{0.22\textwidth}}
        \toprule
        时间 & 政策事件 & 与本文变量的关系 \\
        \midrule
        2018 年 & 对华科技限制升级，实体清单和相关限制成为半导体贸易政策背景的重要节点 & 对应 $Post2018$ \\
        2022 年 8 月 & 《芯片与科学法案》通过，产业补贴与限制性条款共同推动供应链重构 & 作为 $Post2022$ 的制度背景之一 \\
        2022 年 10 月 & BIS 发布先进计算和半导体制造相关出口管制规则 & 对应 $Post2022$ \\
        2023 年 & 出口管制规则更新、实体清单扩展和许可审查进一步收紧 & 对应 $Post2023$ \\
        \bottomrule
    \end{tabular}
\end{table}
```

- [ ] **Step 3: Keep boundary statement**

Ensure the following idea remains after the table: the policy nodes are manually organized annual nodes, not GDELT/news-derived continuous shock measures.

## Chunk 2: Compile And Verify

### Task 2: Rebuild PDF And Check Scope

**Files:**
- Modify: `paper/main.pdf`

- [ ] **Step 1: Compile twice**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

Expected: `paper/main.pdf` is regenerated successfully.

- [ ] **Step 2: Check LaTeX log**

Run:

```bash
rg -n "LaTeX Warning|Package .* Warning|Overfull|Undefined control sequence|! LaTeX Error|Rerun LaTeX" paper/main.log
```

Expected: no output.

- [ ] **Step 3: Check forbidden-scope language**

Run:

```bash
rg -n "GDELT|Goldstein|GCN|政策冲击量化|断链预警" paper -S
```

Expected: matches, if any, only appear as explicit “not used / future work / boundary” language.

- [ ] **Step 4: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output.
