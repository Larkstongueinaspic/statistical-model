# Paper Award Format Upgrade Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the paper and reusable template to match the referenced award-paper style while strengthening the competition narrative without overstating causal or prediction claims.

**Architecture:** Keep `docs/模板.tex` as an independently readable mother template and mirror its key formatting in `paper/main.tex` rather than introducing a shared `.sty` file. Preserve the existing `paper/sections/` split, add a focused literature-review section, and use compact LaTeX-native framework diagrams to show the research pipeline and SIRI system. Verification is compile-first: each chunk ends with syntax/format checks, and the final chunk runs a full XeLaTeX/BibTeX build plus PDF shape checks.

**Tech Stack:** XeLaTeX (`ctexart`, `ctex`, `natbib`, `fancyhdr`, `titlesec`, `enumitem`, `booktabs`, `graphicx`, `caption`), shell tools (`rg`, `sed`, `pdfinfo`, `pdftoppm`), existing LaTeX paper assets.

---

## Source Context

**Spec:** `docs/superpowers/specs/2026-04-29-paper-award-format-upgrade-design.md`

**Primary references:**
- `docs/模板.tex`
- `docs/获奖论文节选.pdf`
- `paper/main.tex`
- `paper/main.pdf`

**Important boundaries:**
- Final PDF stays A4 portrait, not scanned book-spread style.
- Do not modify analysis result data unless a later implementation step explicitly requires regenerating figures.
- Do not claim true GDELT integration.
- Do not claim GCN or the trade-network prototype significantly beats baselines.
- Do not change existing empirical conclusions.

## File Structure

**Create:**
- `paper/sections/literature_review.tex`  
  Focused literature review and theoretical positioning. Single responsibility: explain prior research categories and locate this paper's contribution.

**Modify:**
- `docs/模板.tex`  
  Mother template with award-paper-like formatting, Chinese section numbering, compact spacing, page style, figure/table captions, and numeric references.

- `paper/main.tex`  
  Mirror the mother-template format settings, wire `literature_review`, switch to numeric bibliography, and keep the existing section file architecture.

- `paper/sections/abstract.tex`  
  Convert from default `abstract` environment to a compact reusable abstract block compatible with the new template.

- `paper/sections/introduction.tex`  
  Expand into competition-style introduction: background, significance, research content/technical route, innovations.

- `paper/sections/data.tex`  
  Add subsections and make data/sample/variable construction more explicit.

- `paper/sections/descriptive.tex`  
  Add Chinese-level subsections and tighten the source-structure story.

- `paper/sections/risk_index.tex`  
  Add SIRI indicator-system display and risk layering language grounded in existing results.

- `paper/sections/regression.tex`  
  Add subsections and sharpen statistical-boundary explanation.

- `paper/sections/prediction_extension.tex`  
  Align with the new Chinese hierarchy and keep BACI-only caveats.

- `paper/sections/conclusion.tex`  
  Split conclusions, policy suggestions, and limitations into competition-style paragraphs/subsections.

- `paper/sections/appendix.tex`  
  Keep reproduction, variable notes, and AI-use notes aligned with the new hierarchy.

- `paper/references.bib`  
  Add directly relevant references only; keep bibliography compact and numeric.

**Do not touch unless verification shows a concrete need:**
- `results/**`
- generated result CSVs
- existing figure PNGs under `paper/figures/`

---

## Chunk 1: Template And Paper Shell

### Task 1: Baseline compile and page-shape check

**Files:**
- Read: `paper/main.tex`
- Read: `paper/main.pdf`
- Generated/May change: `paper/main.aux`, `paper/main.bbl`, `paper/main.blg`, `paper/main.log`, `paper/main.out`, `paper/main.toc`, `paper/main.pdf`

- [ ] **Step 1: Run baseline LaTeX compile**

Run:

```bash
(cd paper && xelatex -interaction=nonstopmode main.tex)
(cd paper && bibtex main)
(cd paper && xelatex -interaction=nonstopmode main.tex)
(cd paper && xelatex -interaction=nonstopmode main.tex)
```

Expected: commands complete without fatal LaTeX errors and produce `paper/main.pdf`.

- [ ] **Step 2: Capture current PDF shape**

Run:

```bash
pdfinfo paper/main.pdf | sed -n '1,80p'
```

Expected: `Page size: 595.28 x 841.89 pts (A4)` or equivalent A4 portrait dimensions.

- [ ] **Step 3: Record baseline generated-file state**

Run:

```bash
git status --short paper
git diff --name-only -- paper/main.pdf paper/main.aux paper/main.bbl paper/main.blg paper/main.log paper/main.out paper/main.toc
```

Expected: only generated aux/log/pdf files may appear modified. Do not commit baseline generated artifacts in this task; leave any tracked `paper/main.pdf` refresh decision to Chunk 4.

### Task 2: Upgrade mother template format

**Files:**
- Modify: `docs/模板.tex`
- Generated/May change: `docs/模板.aux`, `docs/模板.bbl`, `docs/模板.blg`, `docs/模板.log`, `docs/模板.out`, `docs/模板.toc`, `docs/模板.pdf`

- [ ] **Step 1: Add required format packages**

Ensure the preamble includes these packages:

```latex
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{float}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[numbers,sort&compress]{natbib}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{titling}
```

Expected: `natbib` is loaded once, in numeric mode.

- [ ] **Step 2: Add compact award-paper style settings**

Add or update this block after package imports:

```latex
\geometry{left=2.8cm,right=2.8cm,top=2.6cm,bottom=2.6cm}
\hypersetup{colorlinks=true, linkcolor=black, citecolor=black, urlcolor=black}
\graphicspath{{figures/}}

\setlength{\parindent}{2em}
\setlength{\parskip}{0pt}
\linespread{1.18}
\setlist{nosep,leftmargin=2em}
\captionsetup{font=small,labelfont=bf,labelsep=space}
\captionsetup[table]{position=top}
\setlength{\floatsep}{8pt plus 2pt minus 2pt}
\setlength{\textfloatsep}{10pt plus 2pt minus 2pt}
\setlength{\intextsep}{8pt plus 2pt minus 2pt}
```

Expected: paragraph and float spacing are compact but still readable.

- [ ] **Step 3: Add Chinese section numbering**

Add:

```latex
\renewcommand\thesection{\chinese{section}}
\renewcommand\thesubsection{（\chinese{subsection}）}
\renewcommand\thesubsubsection{\arabic{subsubsection}.}

\titleformat{\section}{\centering\bfseries\large}{\thesection、}{0pt}{}
\titleformat{\subsection}{\bfseries\normalsize}{\thesubsection}{0pt}{}
\titleformat{\subsubsection}{\bfseries\normalsize}{\thesubsubsection}{0.5em}{}
\titlespacing*{\section}{0pt}{1.2ex plus .2ex}{0.8ex}
\titlespacing*{\subsection}{0pt}{0.8ex plus .2ex}{0.4ex}
\titlespacing*{\subsubsection}{0pt}{0.6ex plus .2ex}{0.3ex}
```

Expected: rendered headings follow `一、` / `（一）` / `1.` hierarchy.

- [ ] **Step 4: Add page style and reusable abstract command**

Ensure `\papertitle` is defined before the page-style block. If the template already defines it, keep that definition; otherwise add:

```latex
\newcommand{\papertitle}{大国博弈下中国半导体相关产品进口来源结构演化与供应链风险评估研究}
```

Then add:

```latex
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\small \papertitle}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

\newcommand{\paperabstract}[2]{%
  \begin{center}
  {\bfseries\large 摘\quad 要}
  \end{center}
  \vspace{0.5ex}
  #1
  \vspace{0.8ex}

  \noindent\textbf{关键词：}#2
}
```

Expected: template has one reusable abstraction for abstract formatting.

- [ ] **Step 5: Keep cover page free of headers**

In the template body, ensure the cover page uses:

```latex
\maketitle
\thispagestyle{empty}
\clearpage
```

Expected: the cover page has no header, footer, or page number.

- [ ] **Step 6: Keep template self-contained and compile it**

Ensure `docs/模板.tex` remains a complete example document and contains placeholder content only where it is visibly a template, not paper production text.

Run:

```bash
rg -n "paperabstract|titleformat|numbers,sort&compress|fancyhead" docs/模板.tex
(cd docs && xelatex -interaction=nonstopmode 模板.tex)
```

Expected: all four patterns are found, XeLaTeX produces `docs/模板.pdf`, and any bibliography warnings are non-fatal template warnings.

### Task 3: Mirror shell formatting in `paper/main.tex`

**Files:**
- Modify: `paper/main.tex`
- Generated/May change: `paper/main.aux`, `paper/main.bbl`, `paper/main.blg`, `paper/main.log`, `paper/main.out`, `paper/main.toc`, `paper/main.pdf`

- [ ] **Step 1: Update package imports**

Make `paper/main.tex` use the same key package set as `docs/模板.tex`. In particular:

```latex
\usepackage[numbers,sort&compress]{natbib}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{titling}
```

Expected: no duplicate `natbib` import remains.

- [ ] **Step 2: Mirror page, spacing, heading, and abstract settings**

Copy the compact spacing, Chinese heading, page-style, and `\paperabstract` definitions from the template into `paper/main.tex`.

Also ensure `\papertitle` remains defined before the `fancyhdr` block in `paper/main.tex`, and preserve the cover sequence:

```latex
\maketitle
\thispagestyle{empty}
\clearpage
```

Expected: `docs/模板.tex` and `paper/main.tex` have the same key formatting macros, but no shared `.sty` file is introduced; the cover page still has no header/footer.

- [ ] **Step 3: Change bibliography style**

Replace:

```latex
\bibliographystyle{plainnat}
```

with:

```latex
\bibliographystyle{unsrtnat}
```

Expected: references render in numeric order-of-citation style.

- [ ] **Step 4: Compile shell**

Run:

```bash
(cd paper && xelatex -interaction=nonstopmode main.tex)
(cd paper && bibtex main)
(cd paper && xelatex -interaction=nonstopmode main.tex)
(cd paper && xelatex -interaction=nonstopmode main.tex)
```

Expected: compile completes. Warnings about undefined references are acceptable only before the final two runs; final run should not contain unresolved citation/reference warnings.

- [ ] **Step 5: Verify shell keeps A4 portrait**

Run:

```bash
pdfinfo paper/main.pdf | sed -n '1,80p'
```

Expected: `Page size` is A4 portrait, approximately `595 x 842 pts`, and page rotation is `0`.

- [ ] **Step 6: Commit shell changes**

Run:

```bash
git status --short docs/模板.tex docs/模板.pdf docs/模板.aux docs/模板.bbl docs/模板.blg docs/模板.log docs/模板.out docs/模板.toc paper/main.tex paper/main.pdf paper/main.aux paper/main.bbl paper/main.blg paper/main.log paper/main.out paper/main.toc
git add docs/模板.tex paper/main.tex
git diff --cached --name-only
git commit -m "style: align paper template shell"
```

Expected: the status command surfaces any generated template/paper artifacts before commit. Commit includes only `docs/模板.tex` and `paper/main.tex` unless the project intentionally tracks refreshed generated PDFs in a later verification step.

---

## Chunk 2: Structure And Literature Review

### Task 4: Convert abstract to reusable block

**Files:**
- Modify: `paper/sections/abstract.tex`
- Read: `paper/main.tex`

- [ ] **Step 1: Replace default abstract environment without dropping content**

Replace the entire file with a `\paperabstract` call that preserves the current abstract text:

```latex
\paperabstract{%
在大国科技竞争和出口管制持续强化的背景下，半导体相关产品进口来源结构已成为评估产业链供应链安全的重要切入点。本文基于 CEPII BACI HS07 数据库 \citep{cepii_baci}，构建 2008--2024 年中国自全球进口四类半导体相关 HS6 产品的出口国--产品--年份平衡面板数据，从描述统计、风险指数和统计检验三个层次考察政策冲击下的进口来源结构演化。研究首先从进口规模、美国份额、主要来源国和 HHI 集中度四个角度刻画结构变化事实；其次构建半导体进口供应链风险指数 SIRI，将来源集中、政策暴露、替代不足和结构波动纳入统一评分框架，按产品--年份计算 0--100 综合风险分值；最后结合多产品固定效应回归、份额型结果和多项稳健性检验，讨论政策节点下的统计证据边界。结果显示，2017--2024 年间，半导体制造设备（848620）的美国进口份额从 27.92\% 降至 9.88\%，处理器及控制器（854231）和存储器（854232）同样下降，但其他电子集成电路（854239）方向相反。2024 年 SIRI 排序显示，854239 和 854232 的综合风险相对更高，主要驱动因素是来源集中和替代不足而非政策暴露——提示高对美依赖不等于高综合风险。固定效应回归中 US 与 Post2018、Post2022、Post2023 的交互项均不显著，不支持将结构变化简单归因为出口管制的严格因果效应。进一步地，本文在未接入 GDELT 的 BACI-only 设定下，将产品池扩展至 20 个半导体相关 HS6 编码，构造年度进口来源网络，并进行下一年 SIRI 风险预测的原型验证。本文为关键半导体产品进口安全监测提供了可解释、可复现的统计建模框架，并讨论了结论的适用范围与局限。
}{大国博弈；半导体；进口来源结构；供应链风险；统计建模}
```

Expected: no `\begin{abstract}` or separate keyword line remains.

- [ ] **Step 2: Verify abstract conversion**

Run:

```bash
rg -n "\\\\begin\\{abstract\\}|\\\\end\\{abstract\\}|BACI-only|GDELT" paper/sections/abstract.tex
```

Expected: `BACI-only` and `GDELT` are present; `\begin{abstract}` and `\end{abstract}` are absent.

- [ ] **Step 3: Compile abstract**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
```

Expected: no `Environment abstract undefined` or macro errors; abstract title renders via `\paperabstract`.

### Task 5: Rewrite introduction into competition structure

**Files:**
- Modify: `paper/sections/introduction.tex`

- [ ] **Step 1: Add section and subsection structure**

Make the file start with:

```latex
\section{绪论}

\subsection{研究背景与问题提出}
```

Then keep the existing policy-background material.

- [ ] **Step 2: Add research significance subsection**

Add:

```latex
\subsection{研究意义}
```

Content requirements:
- Explain why semiconductor import-source structure matters for industrial-chain security.
- Explain why product heterogeneity matters.
- Explain why honest statistical boundaries matter for competition-quality modeling.

Keep this subsection concise: 2 to 3 paragraphs.

- [ ] **Step 3: Add research content and technical route subsection**

Add:

```latex
\subsection{研究内容与技术路线}
```

Include a compact LaTeX-native framework figure:

```latex
\begin{figure}[H]
  \centering
  \small
  \setlength{\fboxsep}{6pt}
  \fbox{\begin{minipage}{0.92\textwidth}
  \centering
  BACI 数据 $\rightarrow$ 产品筛选 $\rightarrow$ 来源结构描述 $\rightarrow$
  SIRI 风险指数 $\rightarrow$ 固定效应检验 $\rightarrow$
  预测扩展 $\rightarrow$ 政策建议
  \end{minipage}}
  \caption{本文研究技术路线}
  \label{fig:research-framework}
\end{figure}
```

Expected: one visible framework figure, not a decorative graphic.

- [ ] **Step 4: Add innovation subsection**

Add:

```latex
\subsection{主要创新点}
```

List exactly three innovations:
- Product-level import-source heterogeneity perspective.
- Explainable SIRI index.
- Evidence chain that separates descriptive restructuring, risk evaluation, statistical boundary, and prediction extension.

- [ ] **Step 5: Compile and inspect introduction**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
rg -n "绪论|研究背景与问题提出|研究意义|研究内容与技术路线|主要创新点|本文研究技术路线" main.toc sections/introduction.tex
```

Expected: no LaTeX errors; the four introduction subsections and `本文研究技术路线` are visible in source/TOC after the second compile.

### Task 6: Add literature review section

**Files:**
- Create: `paper/sections/literature_review.tex`
- Modify: `paper/main.tex`
- Modify: `paper/references.bib`

- [ ] **Step 1: Create `literature_review.tex`**

Create the file with this concrete structure and content direction:

```latex
\section{文献综述与理论基础}

\subsection{供应链风险测度研究}
供应链风险研究通常强调风险来源、脆弱性与恢复能力之间的关系。已有研究指出，供应链中断并不只来自单一节点失效，还与供应商集中、替代能力不足和冲击传播路径有关 \citep{chopra2004managing,juttner2005supply}。因此，若只观察某一来源国份额，容易低估非美来源内部高度集中的结构性风险。

\subsection{半导体贸易与出口管制研究}
半导体产业具有高度国际分工特征，制造设备、设计、晶圆制造、封测和终端需求分布在不同国家和地区。全球价值链研究表明，产品级贸易结构能够揭示宏观总量数据难以识别的依赖关系 \citep{baldwin2016great}。美国对先进计算芯片和半导体制造设备的出口管制构成本文的重要政策背景 \citep{us_bis_controls}，但贸易来源变化还会受到产业周期、第三方产能调整和中国需求扩张共同影响。

\subsection{贸易网络与风险预测研究}
网络视角将国家和产品之间的贸易关系视为带权连接，有助于刻画集中度、替代路径和冲击传播。社会经济网络研究为分析节点、边权和结构位置提供了基础工具 \citep{jackson2010social}；图表示学习方法进一步说明，网络结构可以被组织为预测任务的输入 \citep{hamilton2017inductive}。本文的 v0.3 扩展只将年度贸易网络用于下一年 SIRI 风险预测原型，不把预测模型解释为政策因果识别。

\subsection{文献评述与本文定位}
综上，既有研究为供应链风险测度、半导体政策背景和网络化预测提供了基础，但仍需要一个能够落到产品级进口来源结构的可解释框架。本文的定位是：基于 BACI 产品级贸易数据，先刻画中国半导体相关产品进口来源重组事实，再构造 SIRI 风险指数进行综合评价，最后用固定效应回归和预测扩展分别讨论统计证据边界与预警可扩展性。
```

Expected: each subsection is 1 to 2 focused paragraphs and does not become broad textbook exposition.

- [ ] **Step 2: Add citations**

Add these compact BibTeX entries to `paper/references.bib` if they are not already present:

```bibtex
@article{chopra2004managing,
  author = {Chopra, Sunil and Sodhi, ManMohan S.},
  title = {Managing Risk to Avoid Supply-Chain Breakdown},
  journal = {MIT Sloan Management Review},
  year = {2004},
  volume = {46},
  number = {1},
  pages = {53--61}
}

@article{juttner2005supply,
  author = {Juttner, Uta},
  title = {Supply Chain Risk Management: Understanding the Business Requirements from a Practitioner Perspective},
  journal = {The International Journal of Logistics Management},
  year = {2005},
  volume = {16},
  number = {1},
  pages = {120--141}
}

@book{baldwin2016great,
  author = {Baldwin, Richard},
  title = {The Great Convergence: Information Technology and the New Globalization},
  publisher = {Harvard University Press},
  year = {2016}
}

@book{jackson2010social,
  author = {Jackson, Matthew O.},
  title = {Social and Economic Networks},
  publisher = {Princeton University Press},
  year = {2010}
}

@inproceedings{hamilton2017inductive,
  author = {Hamilton, William L. and Ying, Rex and Leskovec, Jure},
  title = {Inductive Representation Learning on Large Graphs},
  booktitle = {Advances in Neural Information Processing Systems},
  year = {2017}
}
```

Expected: new citations are directly used in `literature_review.tex`; total new references in this task is 5.

- [ ] **Step 3: Wire section into main**

In `paper/main.tex`, insert after:

```latex
\input{sections/introduction}
```

this line:

```latex
\input{sections/literature_review}
```

- [ ] **Step 4: Compile bibliography**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

Expected: no unresolved citation warnings for new references.
Also verify numeric references:

```bash
rg -n "\\[[0-9]+\\]|plainnat|unsrtnat" main.bbl main.aux main.log
```

Expected: `unsrtnat` is present in build artifacts or bibliography output and no unresolved-citation warning remains.

- [ ] **Step 5: Commit structure and literature review**

Run:

```bash
git add paper/main.tex paper/sections/abstract.tex paper/sections/introduction.tex paper/sections/literature_review.tex paper/references.bib
git commit -m "paper: add competition-style intro and literature review"
```

Expected: commit excludes unrelated result files.

---

## Chunk 3: Section Rework And Competition Enhancements

### Task 7: Add subsection hierarchy to data and descriptive sections

**Files:**
- Modify: `paper/sections/data.tex`
- Modify: `paper/sections/descriptive.tex`

- [ ] **Step 1: Restructure data section**

Make `paper/sections/data.tex` use these subsections:

```latex
\section{数据来源与变量构造}
\subsection{数据来源与样本范围}
\subsection{产品选择与样本构造}
\subsection{变量定义与模型设定}
```

Preserve existing facts:
- BACI HS07, 2008--2024.
- Importer is China.
- Four core HS6 products.
- Balanced panel has 10608 rows and 5619 positive trade records.
- HC1 robust standard errors.

- [ ] **Step 2: Restructure descriptive section**

Make `paper/sections/descriptive.tex` use these subsections:

```latex
\section{半导体进口来源结构演化分析}
\subsection{总进口规模变化}
\subsection{美国来源份额变化}
\subsection{主要来源国结构}
\subsection{来源集中度与替代路径}
```

Preserve all existing figure inputs and numeric claims.

- [ ] **Step 3: Compile section changes**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
```

Expected: no missing figure or missing table errors.

### Task 8: Strengthen SIRI section with indicator system and risk layering

**Files:**
- Modify: `paper/sections/risk_index.tex`
- Read: `paper/tables/siri_ranking_2024.tex`
- Read: `paper/tables/siri_weight_sensitivity.tex`
- Read: `results/v02/tables/siri_index_by_product_year_v02.csv`

- [ ] **Step 1: Verify SIRI ranking and component sources**

Run:

```bash
sed -n '1,180p' paper/tables/siri_ranking_2024.tex
sed -n '1,180p' paper/tables/siri_weight_sensitivity.tex
.venv/bin/python - <<'PY'
import pandas as pd
s = pd.read_csv("results/v02/tables/siri_index_by_product_year_v02.csv")
cols = [
    "product_code",
    "siri_score",
    "policy_exposure_raw",
    "concentration_raw",
    "alternative_insufficiency_raw",
    "structural_volatility_raw",
]
print(s.loc[s["year"] == 2024, cols].sort_values("siri_score", ascending=False).round(6).to_string(index=False))
PY
```

Expected:

```text
 product_code  siri_score  policy_exposure_raw  concentration_raw  alternative_insufficiency_raw  structural_volatility_raw
       854239   39.465779             0.039403           0.471606                       0.509406                   0.014469
       854232   34.987849             0.001379           0.431708                       0.432899                   0.085017
       848620   18.158904             0.098787           0.208881                       0.245169                   0.045203
       854231   14.154254             0.097216           0.147702                       0.169629                   0.097140
```

Interpretation requirement: the risk-layer paragraph must match these facts. 854239 and 854232 are higher risk by SIRI and by concentration/alternative-insufficiency components; 848620 has higher policy exposure but lower concentration; 854231 has the lowest SIRI and lowest concentration/alternative-insufficiency values among the four.

- [ ] **Step 2: Add subsection hierarchy**

Use:

```latex
\section{SIRI 供应链风险指数构建与评估}
\subsection{指标体系设计}
\subsection{指数计算方法}
\subsection{产品风险排序与分层}
\subsection{权重敏感性检验}
```

Preserve existing SIRI formulas, ranking table, sensitivity table, and numeric claims while moving them under the new subsections.

- [ ] **Step 3: Add SIRI indicator-system figure**

In `指标体系设计`, add:

```latex
\begin{figure}[H]
  \centering
  \small
  \setlength{\fboxsep}{6pt}
  \fbox{\begin{minipage}{0.90\textwidth}
  \begin{center}
  \textbf{SIRI 半导体进口供应链风险指数}
  \end{center}
  \begin{tabular}{@{}ll@{}}
  来源集中风险 & 全来源 HHI \\
  政策暴露风险 & 美国来源进口份额 \\
  替代不足风险 & 非美国来源内部 HHI \\
  结构波动风险 & 相邻年份来源份额总变差距离 \\
  \end{tabular}
  \end{minipage}}
  \caption{SIRI 指标体系}
  \label{fig:siri-framework}
\end{figure}
```

Expected: figure is compact and text-based.

- [ ] **Step 4: Add risk layering paragraph**

In `产品风险排序与分层`, add a guarded paragraph:

```text
按照 2024 年 SIRI 排序，854239 和 854232 属于相对高风险产品，主要风险来自来源集中和替代不足；848620 属于中等风险产品，虽然政策暴露较高，但日本、荷兰、新加坡和美国之间形成较多极的来源结构；854231 风险最低，主要得益于来源分布更均衡。
```

Expected: this paragraph uses relative risk language, not absolute alarm language.

- [ ] **Step 5: Compile SIRI changes**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
```

Expected: no overfull errors severe enough to obscure the indicator figure.

### Task 9: Align regression and prediction sections with new hierarchy

**Files:**
- Modify: `paper/sections/regression.tex`
- Modify: `paper/sections/prediction_extension.tex`
- Read/verify: `paper/sections/abstract.tex`
- Read/verify: `paper/sections/conclusion.tex`

- [ ] **Step 1: Add regression subsections**

Use:

```latex
\section{政策节点下的统计检验与证据边界}
\subsection{固定效应模型设定}
\subsection{回归结果解释}
\subsection{稳健性分析}
\subsection{统计边界讨论}
```

Keep existing p-values and interpretation. Do not weaken the “not strong causal evidence” boundary.

- [ ] **Step 2: Add prediction-extension subsections**

Use:

```latex
\section{预测与预警扩展：基于贸易网络的 SIRI 风险预测}
\subsection{扩展产品池与年度贸易网络}
\subsection{下一年 SIRI 预测任务}
\subsection{模型比较与结果解释}
\subsection{扩展价值与局限}
```

Keep the existing v0.3 workflow figure and tables. Ensure the section explicitly states all of the following:
- current result is BACI-only,
- product pool expands to 20 HS6 products,
- annual graph samples total 320,
- simple baselines remain competitive on the test set,
- the trade-network prototype does not show stable superiority over baselines,
- the extension value is organizing SIRI as a one-year-ahead prediction task and reserving an interface for future GDELT event-pressure variables.

- [ ] **Step 3: Check forbidden claims**

Run:

```bash
rg -n "显著优于|已经接入|实时预警平台|证明.*因果|GDELT.*已|稳定优于" paper/sections/prediction_extension.tex
```

Expected: no matches. If any match appears, rewrite `paper/sections/prediction_extension.tex` to guarded BACI-only language. Broader paper-wide overclaim checks happen again in Chunk 4.

### Task 10: Strengthen conclusion and appendix

**Files:**
- Modify: `paper/sections/conclusion.tex`
- Modify: `paper/sections/appendix.tex`

- [ ] **Step 1: Add conclusion subsections**

Use:

```latex
\section{结论与政策建议}
\subsection{主要结论}
\subsection{政策建议}
\subsection{研究局限与展望}
```

Keep four existing conclusions but make them scan-friendly.

- [ ] **Step 2: Make policy suggestions more actionable**

Ensure policy suggestions cover:
- product-category differentiated monitoring,
- hidden concentration risk,
- normalizing SIRI as a monitoring tool,
- future integration of firm-level or higher-frequency data.

- [ ] **Step 3: Keep appendix concise**

Use appendix subsections under existing appendix sections. Preserve:
- v0.2 command,
- v0.3 BACI-only command,
- optional GDELT command clearly marked as not used in current results,
- AI-use note.

- [ ] **Step 4: Compile enhanced sections**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
```

Expected: compile completes without fatal errors.

- [ ] **Step 5: Stage and verify enhanced section diff**

Run:

```bash
git add paper/sections/data.tex paper/sections/descriptive.tex paper/sections/risk_index.tex paper/sections/regression.tex paper/sections/prediction_extension.tex paper/sections/conclusion.tex paper/sections/appendix.tex
git diff --cached --name-only
git diff --cached --stat
```

Expected: staged files are exactly the seven section files listed above.

- [ ] **Step 6: Commit enhanced sections**

Run:

```bash
git commit -m "paper: strengthen competition narrative"
```

Expected: commit contains only paper section edits.

---

## Chunk 4: Final Build, Visual Checks, And Cleanup

### Task 11: Full LaTeX verification

**Files:**
- Read/verify: `paper/main.tex`
- Read/verify: `paper/main.pdf`
- Read/verify: `paper/main.log`
- Read/verify: `docs/模板.tex`
- Read/verify: `docs/模板.pdf`
- Read/verify: `docs/模板.log`

- [ ] **Step 1: Full build**

Run:

```bash
cd paper
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

Expected: build completes without fatal errors.

- [ ] **Step 2: Build mother template**

Run:

```bash
cd docs
xelatex -interaction=nonstopmode 模板.tex
```

Expected: `docs/模板.pdf` is produced without fatal errors. Missing bibliography warnings are acceptable only if the template contains example bibliography commands without a local `references.bib`.

- [ ] **Step 3: Check unresolved references/citations**

Run:

```bash
rg -n "undefined|Citation.*undefined|Reference.*undefined|Rerun to get" paper/main.log
```

Expected: no unresolved citation/reference warnings after the final run. If `Rerun to get` remains, run `xelatex` one more time and recheck.

- [ ] **Step 4: Check overfull boxes**

Run:

```bash
rg -n "Overfull \\\\hbox|Overfull \\\\vbox" paper/main.log
```

Expected: no severe overfull boxes. Minor overfull warnings under 5pt may be acceptable; large overfull warnings must be fixed by line breaks, table width, or wording.

### Task 12: PDF shape and page preview checks

**Files:**
- Read/verify: `paper/main.pdf`

- [ ] **Step 1: Verify A4 portrait**

Run:

```bash
pdfinfo paper/main.pdf | sed -n '1,80p'
```

Expected: `Page size` is approximately `595 x 842 pts` or `595.28 x 841.89 pts`, `Page rot` is `0`, and the PDF is a single-page-width A4 portrait document rather than landscape or a horizontal book-spread.

- [ ] **Step 2: Render full low-resolution previews**

Run:

```bash
pdftoppm -png -r 90 paper/main.pdf /tmp/paper-award-upgrade-page
magick montage /tmp/paper-award-upgrade-page-*.png -thumbnail 260x -tile 4x -geometry +8+8 /tmp/paper-award-upgrade-contact.png
```

Expected: preview PNGs exist for every paper page and `/tmp/paper-award-upgrade-contact.png` exists as a contact sheet.

- [ ] **Step 3: Inspect previews**

Open the rendered first pages, representative middle pages, final reference/appendix pages, and the contact sheet with the available image-viewing tool. Check:
- cover/abstract follows compact award-paper style,
- TOC uses Chinese section hierarchy,
- first正文 page has page header and compact spacing,
- framework figure is visible and not oversized.
- representative figure/table captions render as “图 1 标题”“表 1 标题” style and are centered,
- bibliography appears as numeric references rather than author-year references,
- final reference/appendix pages have no broken layout.

Expected: no visibly broken layout, overlap, or huge blank area.

### Task 13: Final content boundary checks

**Files:**
- Verify: `paper/sections/*.tex`
- Verify: `paper/references.bib`

- [ ] **Step 1: Check forbidden/overclaiming language**

Run:

```bash
rg -n "显著优于|稳定优于|优于.*基线|已经接入|已接入|GDELT.*已|实时预警平台|证明.*因果|强因果|严格证明|完全解决|断链预警平台" paper/sections paper/main.tex
```

Expected: no matches unless the sentence is explicitly negating the claim.

- [ ] **Step 2: Check BACI-only caveat remains**

Run:

```bash
rg -n "BACI-only|未接入真实 GDELT|探索性" paper/sections/abstract.tex paper/sections/prediction_extension.tex paper/sections/conclusion.tex paper/sections/appendix.tex
```

Expected: caveats appear in prediction extension and at least one summary/limitation location.

- [ ] **Step 3: Check SIRI risk layering source consistency**

Run:

```bash
sed -n '1,180p' paper/tables/siri_ranking_2024.tex
rg -n "高风险|中等风险|低风险|相对高风险" paper/sections/risk_index.tex paper/sections/conclusion.tex
```

Expected: risk-layering wording matches ranking table and remains relative.

### Task 14: Final git status and commit

**Files:**
- All touched files from previous chunks.

- [ ] **Step 1: Review changed files**

Run:

```bash
git status --short
git diff --stat
```

Expected: only intended docs/template/paper files are changed. Existing unrelated result-file changes may still be present in the working tree, but must not be staged.

- [ ] **Step 2: Commit final PDF if intentionally tracked**

If `paper/main.pdf` is tracked and changed from the verified build, stage it with the paper edits:

```bash
git add paper/main.pdf
```

If the project policy is not to update generated PDFs in commits, leave it unstaged and mention it in the final report.

- [ ] **Step 3: Commit final verification updates**

Run:

```bash
git add docs/模板.tex paper/main.tex paper/sections paper/references.bib
git diff --cached --name-only
git diff --cached --stat
```

Expected: staged files include only intended implementation files. Do not stage `results/**` or unrelated `.gitignore` changes unless explicitly required.

- [ ] **Step 4: Commit final verification updates if any remain**

Run:

```bash
git diff --cached --quiet || git commit -m "paper: apply award format upgrade"
```

Expected: if staged changes remain, they are committed; if no staged changes remain because earlier chunk commits already captured everything, no commit is created and the final report says so.

- [ ] **Step 5: Final report**

Report:
- commits created,
- PDF build status,
- whether `paper/main.pdf` was updated and tracked,
- any remaining warnings or manual review notes.
