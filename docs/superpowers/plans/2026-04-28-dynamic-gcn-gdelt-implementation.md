# Dynamic GCN GDELT Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build v0.3 modules that validate an expanded HS6 product pool, aggregate GDELT pressure features, construct yearly China-import trade graphs, run aligned baselines, and provide a GCN-ready training entrypoint.

**Architecture:** Add a new `scripts/v03_gcn/` package and `scripts/run_v03_gcn_analysis.py` without changing v0.2. Keep each module focused: config/storage, product pool, targets, GDELT, graph construction, baselines, model/training, validation, reports. Implement test-first with toy data so the code is verifiable before full BACI/GDELT data is available.

**Tech Stack:** Python 3.14, pandas, numpy, matplotlib, unittest. `torch` and `scikit-learn` are optional runtime dependencies; v0.3 must fail clearly when unavailable.

---

## Chunk 1: Core Data Contracts

### Task 1: v03 package, config, storage, and product pool

**Files:**
- Create: `scripts/v03_gcn/__init__.py`
- Create: `scripts/v03_gcn/config.py`
- Create: `scripts/v03_gcn/storage.py`
- Create: `scripts/v03_gcn/product_pool.py`
- Create: `tests/test_v03_product_pool.py`

- [ ] Write failing tests for product pool validation, core-product report-only behavior, and country crosswalk.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest tests.test_v03_product_pool -v` and confirm failures.
- [ ] Implement `GcnConfig`, storage helpers, product pool constants, `build_product_pool()`, and `build_country_crosswalk()`.
- [ ] Re-run product pool tests and confirm pass.

### Task 2: SIRI targets for expanded products

**Files:**
- Create: `scripts/v03_gcn/siri_targets.py`
- Create: `tests/test_v03_siri_targets.py`

- [ ] Write failing tests for target year alignment and missing-target filtering inputs.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest tests.test_v03_siri_targets -v` and confirm failures.
- [ ] Implement target generation by wrapping existing `scripts.v02_analysis.risk_index.build_siri_outputs()`.
- [ ] Re-run target tests and confirm pass.

## Chunk 2: GDELT and Graph Samples

### Task 3: GDELT pressure aggregation

**Files:**
- Create: `scripts/v03_gcn/gdelt.py`
- Create: `tests/test_v03_gdelt.py`

- [ ] Write failing tests for bidirectional China-exporter aggregation, negative Goldstein weighting, keyword filtering, train-minmax scaling, and missing country-years.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest tests.test_v03_gdelt -v` and confirm failures.
- [ ] Implement `aggregate_gdelt_pressure()` and helper functions.
- [ ] Re-run GDELT tests and confirm pass.

### Task 4: Trade graph construction

**Files:**
- Create: `scripts/v03_gcn/trade_graphs.py`
- Create: `tests/test_v03_trade_graphs.py`

- [ ] Write failing tests for source->China graph tensors, reverse/self-loop edges, node feature filling, graph-level feature schema, and sample alignment.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest tests.test_v03_trade_graphs -v` and confirm failures.
- [ ] Implement `GraphSample`, `build_graph_samples()`, and `build_graph_level_features()`.
- [ ] Re-run trade graph tests and confirm pass.

## Chunk 3: Models, Runner, Outputs

### Task 5: Baselines and metrics

**Files:**
- Create: `scripts/v03_gcn/baselines.py`
- Create: `tests/test_v03_baselines.py`

- [ ] Write failing tests for naive baseline, numpy ridge baseline, aligned metrics, core4 scope rows, and undefined Spearman.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest tests.test_v03_baselines -v` and confirm failures.
- [ ] Implement baselines and metric helpers using numpy only.
- [ ] Re-run baseline tests and confirm pass.

### Task 6: GCN model/training entrypoint

**Files:**
- Create: `scripts/v03_gcn/gcn_model.py`
- Create: `scripts/v03_gcn/training.py`
- Create: `tests/test_v03_training.py`

- [ ] Write failing tests for dependency error when torch is missing and toy tensor preparation behavior.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest tests.test_v03_training -v` and confirm failures.
- [ ] Implement torch availability checks and a minimal GCN class gated behind torch import.
- [ ] Re-run training tests and confirm pass.

### Task 7: Runner, reports, validation, and requirements

**Files:**
- Create: `scripts/v03_gcn/validation.py`
- Create: `scripts/v03_gcn/reports.py`
- Create: `scripts/v03_gcn/plots.py`
- Create: `scripts/run_v03_gcn_analysis.py`
- Modify: `requirements.txt`

- [ ] Write or update tests for validation status and runner import safety if needed.
- [ ] Implement output validation, summary writer, simple plots, and runner orchestration.
- [ ] Add `scikit-learn` and `torch` to `requirements.txt` as declared dependencies.
- [ ] Run `../statistical-model/.venv/bin/python -m unittest discover -v`.
- [ ] Commit the completed implementation.
