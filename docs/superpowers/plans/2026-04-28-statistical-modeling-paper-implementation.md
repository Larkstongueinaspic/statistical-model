# Statistical Modeling Paper Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible SIRI risk-index extension and a XeLaTeX competition-paper draft for the existing v0.2 statistical modeling project.

**Architecture:** Keep the existing v0.2 pipeline intact and add one focused `risk_index.py` module for SIRI computation, one plotting function for SIRI trends, and minimal runner/validation/report integrations. Paper files live under `paper/` and consume generated `results/v02/` outputs without changing the v0.1 workflow.

**Tech Stack:** Python 3, pandas, numpy, matplotlib, statsmodels, stdlib `unittest`, XeLaTeX/ctex for Chinese paper compilation.

---

## Source Spec

Implement from:

`docs/superpowers/specs/2026-04-28-statistical-modeling-paper-design.md`

## File Structure

### Existing Files To Modify

- `scripts/run_v02_analysis.py`
  - No logic expected here unless import path handling needs adjustment. Main orchestration stays in `scripts/v02_analysis/runner.py`.
- `scripts/v02_analysis/runner.py`
  - Build SIRI tables after `annual/top_2024/top_source_shares/descriptive_stats`.
  - Save SIRI CSV/Markdown outputs.
  - Generate SIRI plot.
  - Pass SIRI results into validation and optional reports.
- `scripts/v02_analysis/plots.py`
  - Add `plot_siri_trend(...)`.
  - Keep existing `create_all_figures(...)` compatible.
- `scripts/v02_analysis/validation.py`
  - Add SIRI validation checks or a helper that returns SIRI checks, then append them to `test_results_v02`.
- `scripts/v02_analysis/reports.py`
  - Add short SIRI summary lines to `summary_v0.2.md` and `abstract_v0.2.md`.

### New Files To Create

- `scripts/v02_analysis/risk_index.py`
  - Own all SIRI formulas, weighting, ranking, sensitivity output, and validation-log text.
- `tests/__init__.py`
  - Make stdlib unittest discovery/imports straightforward.
- `tests/test_v02_risk_index.py`
  - Unit tests for SIRI formulas and edge cases. Uses only stdlib `unittest`, pandas, and numpy; no new dependency.
- `paper/main.tex`
  - Main XeLaTeX entry point.
- `paper/sections/abstract.tex`
- `paper/sections/introduction.tex`
- `paper/sections/data.tex`
- `paper/sections/descriptive.tex`
- `paper/sections/risk_index.tex`
- `paper/sections/regression.tex`
- `paper/sections/conclusion.tex`
- `paper/sections/appendix.tex`
- `paper/references.bib`
- `paper/ai_usage_notes.md`
- `paper/figures/README.md`
- `paper/tables/README.md`
- `paper/tables/product_codes.tex`
- `paper/tables/descriptive_statistics.tex`
- `paper/tables/siri_ranking_2024.tex`
- `paper/tables/siri_weight_sensitivity.tex`
- `paper/tables/regression_summary.tex`

### Generated Outputs

- `results/v02/data/siri_index_by_product_year_v02.csv`
- `results/v02/tables/siri_index_by_product_year_v02.csv`
- `results/v02/tables/siri_index_by_product_year_v02.md`
- `results/v02/tables/siri_ranking_2024_v02.csv`
- `results/v02/tables/siri_ranking_2024_v02.md`
- `results/v02/tables/siri_weight_sensitivity_v02.csv`
- `results/v02/tables/siri_weight_sensitivity_v02.md`
- `results/v02/figures/siri_trend_by_product_v02.png`
- `docs/output/siri_validation_v0.2.md` only if appending to `docs/output/log_v0.2.md` is not clean.
- `paper/main.pdf` when XeLaTeX is available.

---

## Chunk 1: SIRI Core Module And Unit Tests

### Task 1: Add Failing Unit Tests For SIRI Formulas

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_v02_risk_index.py`
- Create later: `scripts/v02_analysis/risk_index.py`

- [ ] **Step 1: Create test package marker**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 2: Write failing tests**

Create `tests/test_v02_risk_index.py`:

Write the test file in small passes: first raw-component tests, then normalization/weight validation tests, then ranking/tie-break tests. Run the failing-test command after each pass if a narrower red/green cycle is useful.

```python
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from scripts.v02_analysis.risk_index import (
    BASELINE_WEIGHTS,
    POLICY_WEIGHTED_WEIGHTS,
    build_siri_panel,
    build_siri_ranking,
    build_siri_weight_sensitivity,
    compute_siri_scores,
    normalize_siri_components,
    validate_weights,
)


def sample_panel() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2008,
                "exporter_code": 842,
                "exporter_name": "USA",
                "import_value_kusd": 40.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2008,
                "exporter_code": 392,
                "exporter_name": "Japan",
                "import_value_kusd": 60.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2009,
                "exporter_code": 842,
                "exporter_name": "USA",
                "import_value_kusd": 20.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2009,
                "exporter_code": 392,
                "exporter_name": "Japan",
                "import_value_kusd": 30.0,
            },
            {
                "product_code": "000001",
                "product_description": "Demo product",
                "year": 2009,
                "exporter_code": 410,
                "exporter_name": "Rep. of Korea",
                "import_value_kusd": 50.0,
            },
        ]
    )


class RiskIndexTests(unittest.TestCase):
    def test_build_siri_panel_computes_raw_components(self) -> None:
        result = build_siri_panel(sample_panel())
        row_2008 = result.loc[result["year"] == 2008].iloc[0]
        row_2009 = result.loc[result["year"] == 2009].iloc[0]

        self.assertAlmostEqual(row_2008["total_import_value_kusd"], 100.0)
        self.assertAlmostEqual(row_2008["concentration_raw"], 0.52)
        self.assertAlmostEqual(row_2008["policy_exposure_raw"], 0.4)
        self.assertAlmostEqual(row_2008["alternative_insufficiency_raw"], 1.0)
        self.assertAlmostEqual(row_2008["structural_volatility_raw"], 0.0)

        self.assertAlmostEqual(row_2009["concentration_raw"], 0.38)
        self.assertAlmostEqual(row_2009["policy_exposure_raw"], 0.2)
        self.assertAlmostEqual(row_2009["alternative_insufficiency_raw"], 0.53125)
        self.assertAlmostEqual(row_2009["structural_volatility_raw"], 0.5)

    def test_normalize_and_score_bounds(self) -> None:
        raw = build_siri_panel(sample_panel())
        normalized = normalize_siri_components(raw)
        scored = compute_siri_scores(normalized, BASELINE_WEIGHTS, score_column="siri_score")

        self.assertTrue(((scored["siri_score"] >= 0) & (scored["siri_score"] <= 100)).all())
        for column in [
            "concentration_norm",
            "policy_exposure_norm",
            "alternative_insufficiency_norm",
            "structural_volatility_norm",
        ]:
            self.assertTrue(((scored[column] >= 0) & (scored[column] <= 1)).all())

    def test_missing_us_and_zero_total_are_handled(self) -> None:
        panel = pd.DataFrame(
            [
                {
                    "product_code": "000002",
                    "product_description": "No US product",
                    "year": 2008,
                    "exporter_code": 392,
                    "exporter_name": "Japan",
                    "import_value_kusd": 0.0,
                }
            ]
        )
        result = build_siri_panel(panel)
        row = result.iloc[0]
        self.assertEqual(row["total_import_value_kusd"], 0.0)
        self.assertEqual(row["policy_exposure_raw"], 0.0)
        self.assertEqual(row["concentration_raw"], 0.0)
        self.assertEqual(row["structural_volatility_raw"], 0.0)

    def test_min_equals_max_normalizes_to_zero(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "product_code": "000001",
                    "product_name": "Demo",
                    "year": 2008,
                    "total_import_value_kusd": 100.0,
                    "concentration_raw": 1.0,
                    "policy_exposure_raw": 0.0,
                    "alternative_insufficiency_raw": 1.0,
                    "structural_volatility_raw": 0.0,
                },
                {
                    "product_code": "000002",
                    "product_name": "Demo 2",
                    "year": 2008,
                    "total_import_value_kusd": 100.0,
                    "concentration_raw": 1.0,
                    "policy_exposure_raw": 0.0,
                    "alternative_insufficiency_raw": 1.0,
                    "structural_volatility_raw": 0.0,
                },
            ]
        )
        normalized = normalize_siri_components(raw)
        self.assertTrue(np.isclose(normalized["concentration_norm"], 0.0).all())
        self.assertTrue(np.isclose(normalized["policy_exposure_norm"], 0.0).all())

    def test_invalid_weights_raise_clear_error(self) -> None:
        with self.assertRaises(ValueError):
            validate_weights({"concentration": 1.0})
        with self.assertRaises(ValueError):
            validate_weights(
                {
                    "concentration": 0.25,
                    "policy_exposure": 0.25,
                    "alternative_insufficiency": 0.25,
                    "structural_volatility": -0.25,
                }
            )

    def test_ranking_and_sensitivity_are_deterministic(self) -> None:
        raw = build_siri_panel(sample_panel())
        normalized = normalize_siri_components(raw)
        scored = compute_siri_scores(normalized, BASELINE_WEIGHTS, score_column="siri_score")
        scored = compute_siri_scores(scored, POLICY_WEIGHTED_WEIGHTS, score_column="siri_score_policy_weighted")

        ranking = build_siri_ranking(scored, target_year=2009)
        sensitivity = build_siri_weight_sensitivity(scored, target_year=2009)

        self.assertEqual(ranking.iloc[0]["rank"], 1)
        self.assertIn("rank_policy_weighted", ranking.columns)
        self.assertIn("rank_change", ranking.columns)
        self.assertIn("policy_weighted_rank", sensitivity.columns)

    def test_ranking_tie_breaks_by_recent_average_then_product_code(self) -> None:
        scored = pd.DataFrame(
            [
                {"product_code": "A", "product_name": "A product", "year": 2022, "siri_score": 20.0, "siri_score_policy_weighted": 20.0},
                {"product_code": "A", "product_name": "A product", "year": 2023, "siri_score": 40.0, "siri_score_policy_weighted": 40.0},
                {"product_code": "A", "product_name": "A product", "year": 2024, "siri_score": 80.0, "siri_score_policy_weighted": 80.0},
                {"product_code": "B", "product_name": "B product", "year": 2022, "siri_score": 40.0, "siri_score_policy_weighted": 40.0},
                {"product_code": "B", "product_name": "B product", "year": 2023, "siri_score": 60.0, "siri_score_policy_weighted": 60.0},
                {"product_code": "B", "product_name": "B product", "year": 2024, "siri_score": 80.0, "siri_score_policy_weighted": 80.0},
                {"product_code": "D", "product_name": "D product", "year": 2022, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "D", "product_name": "D product", "year": 2023, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "D", "product_name": "D product", "year": 2024, "siri_score": 50.0, "siri_score_policy_weighted": 50.0},
                {"product_code": "C", "product_name": "C product", "year": 2022, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "C", "product_name": "C product", "year": 2023, "siri_score": 10.0, "siri_score_policy_weighted": 10.0},
                {"product_code": "C", "product_name": "C product", "year": 2024, "siri_score": 50.0, "siri_score_policy_weighted": 50.0},
            ]
        )
        ranking = build_siri_ranking(scored, target_year=2024)
        self.assertEqual(ranking["product_code"].tolist(), ["B", "A", "C", "D"])
        self.assertEqual(ranking.set_index("product_code").loc["B", "rank"], 1)
        self.assertEqual(ranking.set_index("product_code").loc["A", "rank"], 2)
        self.assertEqual(ranking.set_index("product_code").loc["C", "rank"], 3)
        self.assertEqual(ranking.set_index("product_code").loc["D", "rank"], 4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
.venv/bin/python -m unittest tests.test_v02_risk_index -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.v02_analysis.risk_index'`.

### Task 2: Implement `risk_index.py`

**Files:**
- Create: `scripts/v02_analysis/risk_index.py`
- Test: `tests/test_v02_risk_index.py`

- [ ] **Step 1: Add constants and validation**

Implement:

```python
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


SIRI_COMPONENTS = (
    "concentration",
    "policy_exposure",
    "alternative_insufficiency",
    "structural_volatility",
)
RAW_COLUMNS = tuple(f"{component}_raw" for component in SIRI_COMPONENTS)
NORM_COLUMNS = tuple(f"{component}_norm" for component in SIRI_COMPONENTS)
BASELINE_WEIGHTS = {
    "concentration": 0.25,
    "policy_exposure": 0.25,
    "alternative_insufficiency": 0.25,
    "structural_volatility": 0.25,
}
POLICY_WEIGHTED_WEIGHTS = {
    "concentration": 0.20,
    "policy_exposure": 0.40,
    "alternative_insufficiency": 0.20,
    "structural_volatility": 0.20,
}


def validate_weights(weights: dict[str, float]) -> None:
    missing = set(SIRI_COMPONENTS) - set(weights)
    extra = set(weights) - set(SIRI_COMPONENTS)
    if missing or extra:
        raise ValueError(f"SIRI weights must have exactly {SIRI_COMPONENTS}; missing={missing}, extra={extra}")
    if any(value < 0 for value in weights.values()):
        raise ValueError("SIRI weights must be non-negative.")
    total = float(sum(weights.values()))
    if not np.isclose(total, 1.0):
        raise ValueError(f"SIRI weights must sum to 1.0, got {total:.6f}.")
```

- [ ] **Step 2: Add raw component builder**

Implementation rules:

- Required input columns: `product_code`, `year`, `exporter_code`, `import_value_kusd`.
- Prefer `product_description` as source for `product_name`; fall back to empty string.
- Aggregate duplicates by `product_code/year/exporter_code`.
- Build shares even if USA is absent.
- For `V_{p,t}=0`, all shares are 0.
- For first year per product, `structural_volatility_raw=0`.

Core implementation outline:

```python
def _require_columns(df: pd.DataFrame, required: set[str]) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def build_siri_panel(panel_df: pd.DataFrame, usa_code: int = 842) -> pd.DataFrame:
    _require_columns(panel_df, {"product_code", "year", "exporter_code", "import_value_kusd"})
    if (panel_df["import_value_kusd"] < 0).any():
        raise ValueError("SIRI input import values must be non-negative.")

    product_name_source = "product_description" if "product_description" in panel_df.columns else None
    group_cols = ["product_code", "year", "exporter_code"]
    aggregations = {"import_value_kusd": "sum"}
    if product_name_source:
        aggregations[product_name_source] = "first"

    flows = panel_df.groupby(group_cols, as_index=False).agg(aggregations)
    totals = (
        flows.groupby(["product_code", "year"], as_index=False)["import_value_kusd"]
        .sum()
        .rename(columns={"import_value_kusd": "total_import_value_kusd"})
    )
    flows = flows.merge(totals, on=["product_code", "year"], how="left")
    flows["share"] = np.where(
        flows["total_import_value_kusd"] > 0,
        flows["import_value_kusd"] / flows["total_import_value_kusd"],
        0.0,
    )

    rows: list[dict[str, object]] = []
    for product_code, product_group in flows.groupby("product_code"):
        product_group = product_group.sort_values(["year", "exporter_code"]).copy()
        product_name = ""
        if product_name_source and product_name_source in product_group:
            product_name = str(product_group[product_name_source].dropna().iloc[0])
        previous_shares: dict[int, float] | None = None

        for year, year_group in product_group.groupby("year", sort=True):
            shares = {
                int(row.exporter_code): float(row.share)
                for row in year_group.itertuples(index=False)
            }
            total_import = float(year_group["total_import_value_kusd"].iloc[0])
            us_share = float(shares.get(usa_code, 0.0))
            concentration = float(sum(value * value for value in shares.values())) if total_import > 0 else 0.0
            non_us_share = max(1.0 - us_share, 0.0)
            if total_import <= 0:
                alternative = 0.0
            elif non_us_share > 0:
                alternative = float(
                    sum((share / non_us_share) ** 2 for code, share in shares.items() if code != usa_code)
                )
            else:
                alternative = 1.0
            if previous_shares is None:
                volatility = 0.0
            else:
                exporters = set(shares) | set(previous_shares)
                volatility = 0.5 * sum(abs(shares.get(code, 0.0) - previous_shares.get(code, 0.0)) for code in exporters)
            rows.append(
                {
                    "product_code": str(product_code),
                    "product_name": product_name,
                    "year": int(year),
                    "total_import_value_kusd": total_import,
                    "concentration_raw": concentration,
                    "policy_exposure_raw": us_share,
                    "alternative_insufficiency_raw": alternative,
                    "structural_volatility_raw": float(volatility),
                }
            )
            previous_shares = shares
    return pd.DataFrame(rows).sort_values(["product_code", "year"], ignore_index=True)
```

- [ ] **Step 3: Add normalization and scoring**

Implement:

```python
def normalize_siri_components(siri_df: pd.DataFrame) -> pd.DataFrame:
    result = siri_df.copy()
    for component in SIRI_COMPONENTS:
        raw = f"{component}_raw"
        norm = f"{component}_norm"
        min_value = float(result[raw].min())
        max_value = float(result[raw].max())
        if np.isclose(max_value, min_value):
            result[norm] = 0.0
        else:
            result[norm] = (result[raw] - min_value) / (max_value - min_value)
    return result


def compute_siri_scores(siri_df: pd.DataFrame, weights: dict[str, float], score_column: str) -> pd.DataFrame:
    validate_weights(weights)
    result = siri_df.copy()
    score = sum(result[f"{component}_norm"] * weight for component, weight in weights.items())
    result[score_column] = score * 100.0
    return result
```

- [ ] **Step 4: Add deterministic ranking helpers**

Implement `build_siri_ranking` with the exact output schema required by the spec:

```python
def _recent_average(scored: pd.DataFrame, score_column: str, target_year: int) -> pd.DataFrame:
    recent = scored.loc[scored["year"].between(target_year - 2, target_year)]
    return (
        recent.groupby("product_code", as_index=False)[score_column]
        .mean()
        .rename(columns={score_column: f"{score_column}_recent_mean"})
    )


def _rank_for_score(scored: pd.DataFrame, score_column: str, rank_column: str, target_year: int) -> pd.DataFrame:
    target = scored.loc[scored["year"] == target_year].copy()
    recent_average = _recent_average(scored, score_column, target_year)
    target = target.merge(recent_average, on="product_code", how="left")
    target = target.sort_values(
        [score_column, f"{score_column}_recent_mean", "product_code"],
        ascending=[False, False, True],
        ignore_index=True,
    )
    target[rank_column] = range(1, len(target) + 1)
    return target[["product_code", rank_column]]


def build_siri_ranking(scored: pd.DataFrame, target_year: int = 2024) -> pd.DataFrame:
    baseline_rank = _rank_for_score(scored, "siri_score", "rank", target_year)
    policy_rank = _rank_for_score(scored, "siri_score_policy_weighted", "rank_policy_weighted", target_year)
    target = scored.loc[scored["year"] == target_year, [
        "product_code",
        "product_name",
        "year",
        "siri_score",
        "siri_score_policy_weighted",
    ]].copy()
    result = target.merge(baseline_rank, on="product_code", how="left").merge(policy_rank, on="product_code", how="left")
    result["rank_change"] = result["rank_policy_weighted"] - result["rank"]
    return result.sort_values(["rank", "product_code"], ignore_index=True)[[
        "rank",
        "product_code",
        "product_name",
        "year",
        "siri_score",
        "siri_score_policy_weighted",
        "rank_policy_weighted",
        "rank_change",
    ]]
```

- [ ] **Step 5: Add sensitivity output helper**

Implement:

```python
def build_siri_weight_sensitivity(scored: pd.DataFrame, target_year: int = 2024) -> pd.DataFrame:
    ranking = build_siri_ranking(scored, target_year=target_year)
    result = ranking.rename(
        columns={
            "rank": "baseline_rank",
            "rank_policy_weighted": "policy_weighted_rank",
            "siri_score": "baseline_siri_score",
            "siri_score_policy_weighted": "policy_weighted_siri_score",
        }
    )
    return result[[
        "product_code",
        "product_name",
        "baseline_rank",
        "policy_weighted_rank",
        "rank_change",
        "baseline_siri_score",
        "policy_weighted_siri_score",
    ]].sort_values(["baseline_rank", "product_code"], ignore_index=True)
```

- [ ] **Step 6: Add combined output builder**

Implement:

```python


def build_siri_outputs(panel_df: pd.DataFrame, target_year: int = 2024) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = build_siri_panel(panel_df)
    normalized = normalize_siri_components(raw)
    scored = compute_siri_scores(normalized, BASELINE_WEIGHTS, "siri_score")
    scored = compute_siri_scores(scored, POLICY_WEIGHTED_WEIGHTS, "siri_score_policy_weighted")
    ranking = build_siri_ranking(scored, target_year=target_year)
    sensitivity = build_siri_weight_sensitivity(scored, target_year=target_year)
    return scored, ranking, sensitivity
```

- [ ] **Step 7: Run unit tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_v02_risk_index -v
```

Expected: PASS all tests.

- [ ] **Step 8: Commit SIRI core**

```bash
git add scripts/v02_analysis/risk_index.py tests/__init__.py tests/test_v02_risk_index.py
git commit -m "feat: add SIRI risk index core"
```

---

## Chunk 2: Pipeline Integration, Outputs, And Validation

### Task 3: Integrate SIRI Outputs Into v0.2 Runner

**Files:**
- Modify: `scripts/v02_analysis/runner.py`
- Modify: `scripts/v02_analysis/storage.py` only if a helper is needed; prefer existing `save_dataset` and `save_table`.
- Create generated outputs under `results/v02/`.

- [ ] **Step 1: Run current v0.2 pipeline as baseline**

Run:

```bash
.venv/bin/python scripts/run_v02_analysis.py
```

Expected: exits 0 and regenerates existing v0.2 outputs. If BACI raw files are missing, stop and restore data before continuing.

- [ ] **Step 2: Modify runner imports**

Add:

```python
from .risk_index import build_siri_outputs
```

Keep the existing `.plots import create_all_figures` line unchanged in this task. Plot integration happens after `plot_siri_trend` exists.

- [ ] **Step 3: Build SIRI after descriptive outputs are ready**

After `main_exporter_panel = build_main_exporter_panel(panel)`, add:

```python
siri_index, siri_ranking, siri_sensitivity = build_siri_outputs(panel, target_year=2024)
```

- [ ] **Step 4: Save SIRI outputs**

In the write section, add:

```python
save_dataset(siri_index, "siri_index_by_product_year_v02.csv", config)
save_table(siri_index, "siri_index_by_product_year_v02", config)
save_table(siri_ranking, "siri_ranking_2024_v02", config)
save_table(siri_sensitivity, "siri_weight_sensitivity_v02", config)
```

- [ ] **Step 5: Run pipeline and verify new table/data outputs exist**

Run:

```bash
.venv/bin/python scripts/run_v02_analysis.py
```

Expected new files:

```text
results/v02/data/siri_index_by_product_year_v02.csv
results/v02/tables/siri_index_by_product_year_v02.csv
results/v02/tables/siri_index_by_product_year_v02.md
results/v02/tables/siri_ranking_2024_v02.csv
results/v02/tables/siri_ranking_2024_v02.md
results/v02/tables/siri_weight_sensitivity_v02.csv
results/v02/tables/siri_weight_sensitivity_v02.md
```

### Task 4: Add SIRI Plot

**Files:**
- Modify: `scripts/v02_analysis/plots.py`

- [ ] **Step 1: Add plot function**

Add:

```python
def plot_siri_trend(siri_index: pd.DataFrame, config: AnalysisConfig) -> None:
    plt, _ = configure_matplotlib(config)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for product_code, group in siri_index.groupby("product_code"):
        group = group.sort_values("year")
        ax.plot(
            group["year"],
            group["siri_score"],
            label=f"HS{product_code}",
            linewidth=2.2,
            color=PRODUCT_COLORS.get(str(product_code), None),
        )
    _add_policy_lines(ax)
    ax.set_title("SIRI risk index by selected semiconductor-related product")
    ax.set_xlabel("Year")
    ax.set_ylabel("SIRI score")
    ax.set_xticks(config.years[::2])
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / "siri_trend_by_product_v02.png", dpi=220)
    plt.close(fig)
```

- [ ] **Step 2: Run pipeline**

Import the new function in `runner.py`:

```python
from .plots import create_all_figures, plot_siri_trend
```

After `create_all_figures(annual, top_2024, config)`, add:

```python
plot_siri_trend(siri_index, config)
```

Then run:

```bash
.venv/bin/python scripts/run_v02_analysis.py
```

Expected: `results/v02/figures/siri_trend_by_product_v02.png` exists and is non-empty.

### Task 5: Add Validation Checks And Log

**Files:**
- Modify: `scripts/v02_analysis/validation.py`
- Modify: `scripts/v02_analysis/runner.py`

- [ ] **Step 1: Add SIRI validation helper**

In `validation.py`, add:

```python
def build_siri_test_results(
    siri_index: pd.DataFrame,
    siri_ranking: pd.DataFrame,
    siri_sensitivity: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    tests: list[dict[str, object]] = []

    def add_test(category: str, name: str, passed: bool, detail: str) -> None:
        tests.append({"category": category, "test_name": name, "passed": "PASS" if passed else "FAIL", "detail": detail})

    expected_rows = len(config.candidate_product_codes) * len(config.years)
    required_columns = {
        "product_code",
        "year",
        "total_import_value_kusd",
        "concentration_raw",
        "policy_exposure_raw",
        "alternative_insufficiency_raw",
        "structural_volatility_raw",
        "concentration_norm",
        "policy_exposure_norm",
        "alternative_insufficiency_norm",
        "structural_volatility_norm",
        "siri_score",
        "siri_score_policy_weighted",
    }
    ranking_columns = {
        "rank",
        "product_code",
        "product_name",
        "year",
        "siri_score",
        "siri_score_policy_weighted",
        "rank_policy_weighted",
        "rank_change",
    }
    sensitivity_columns = {
        "product_code",
        "product_name",
        "baseline_rank",
        "policy_weighted_rank",
        "rank_change",
        "baseline_siri_score",
        "policy_weighted_siri_score",
    }

    add_test("siri", "SIRI output has required columns", required_columns.issubset(siri_index.columns), f"Columns: {siri_index.columns.tolist()}")
    add_test("siri", "SIRI product-year row count matches selected products", len(siri_index) == expected_rows, f"Observed rows: {len(siri_index)}, expected rows: {expected_rows}")
    add_test("siri", "SIRI years cover configured range", set(siri_index["year"].astype(int)) == set(config.years), f"Years: {sorted(siri_index['year'].unique().tolist())}")
    coverage = siri_index.groupby("product_code")["year"].nunique().to_dict()
    add_test("siri", "Each SIRI product covers every configured year", all(count == len(config.years) for count in coverage.values()), f"Coverage: {coverage}")
    add_test("siri", "SIRI scores stay within 0-100", bool(((siri_index["siri_score"] >= 0) & (siri_index["siri_score"] <= 100)).all()), "Checked baseline SIRI score bounds.")
    add_test("siri", "Policy-weighted SIRI scores stay within 0-100", bool(((siri_index["siri_score_policy_weighted"] >= 0) & (siri_index["siri_score_policy_weighted"] <= 100)).all()), "Checked policy-weighted SIRI score bounds.")
    norm_columns = [column for column in siri_index.columns if column.endswith("_norm")]
    add_test("siri", "SIRI normalized components stay within 0-1", bool(((siri_index[norm_columns] >= 0) & (siri_index[norm_columns] <= 1)).all().all()), f"Norm columns: {norm_columns}")
    add_test("siri", "SIRI required fields are non-missing", bool(siri_index[list(required_columns)].notna().all().all()), "Checked required fields for missing values.")
    add_test("siri", "SIRI ranking has required columns", ranking_columns.issubset(siri_ranking.columns), f"Columns: {siri_ranking.columns.tolist()}")
    add_test("siri", "SIRI ranking covers all selected products", len(siri_ranking) == len(config.candidate_product_codes), f"Rows: {len(siri_ranking)}")
    add_test("siri", "SIRI sensitivity has required columns", sensitivity_columns.issubset(siri_sensitivity.columns), f"Columns: {siri_sensitivity.columns.tolist()}")
    add_test("siri", "SIRI sensitivity covers all selected products", len(siri_sensitivity) == len(config.candidate_product_codes), f"Rows: {len(siri_sensitivity)}")
    return pd.DataFrame(tests)
```

- [ ] **Step 2: Append SIRI validation into runner**

Import `build_siri_test_results`, then after existing `test_results = build_test_results(...)`:

```python
siri_test_results = build_siri_test_results(siri_index, siri_ranking, siri_sensitivity, config)
test_results = pd.concat([test_results, siri_test_results], ignore_index=True)
```

If `pd` is not imported in `runner.py`, either import pandas as `pd` or add a small helper in `validation.py` that concatenates.

- [ ] **Step 3: Add validation log writer in `validation.py`**

In `validation.py`, add:

```python
def build_siri_validation_log(siri_index: pd.DataFrame) -> str:
    zero_total_rows = int((siri_index["total_import_value_kusd"] == 0).sum())
    constant_norm_dimensions = []
    min_max_lines = []
    for component in ["concentration", "policy_exposure", "alternative_insufficiency", "structural_volatility"]:
        raw = f"{component}_raw"
        raw_min = float(siri_index[raw].min())
        raw_max = float(siri_index[raw].max())
        if raw_min == raw_max:
            constant_norm_dimensions.append(raw)
        min_max_lines.append(f"- {raw}: min={raw_min:.6f}, max={raw_max:.6f}")
    missing_or_zero_us_rows = int((siri_index["policy_exposure_raw"] == 0).sum())
    return "\\n".join(
        [
            "# SIRI validation-v0.2",
            "",
            f"- Rows: {len(siri_index)}",
            f"- Zero total product-year rows: {zero_total_rows}",
            f"- Product-year rows with missing USA record or zero US policy exposure: {missing_or_zero_us_rows}",
            f"- Raw dimensions with min=max: {constant_norm_dimensions if constant_norm_dimensions else 'none'}",
            "- Raw component ranges:",
            *min_max_lines,
            "",
        ]
    )


def write_siri_validation_log(siri_index: pd.DataFrame, config) -> None:
    target = config.docs_output_dir / "siri_validation_v0.2.md"
    target.write_text(build_siri_validation_log(siri_index), encoding="utf-8")
```

- [ ] **Step 4: Call validation log writer**

In `runner.py`, after SIRI outputs are built and before final reports:

```python
write_siri_validation_log(siri_index, config)
```

Import it from validation:

```python
from .validation import build_siri_test_results, build_test_results, write_siri_validation_log
```

- [ ] **Step 5: Run validations**

Run:

```bash
.venv/bin/python -m unittest tests.test_v02_risk_index -v
.venv/bin/python scripts/run_v02_analysis.py
```

Expected:

- unittest PASS.
- v0.2 pipeline exits 0.
- `results/v02/tables/test_results_v02.csv` includes `category == "siri"` rows and all are `PASS`.
- `docs/output/siri_validation_v0.2.md` exists.

### Task 6: Update v0.2 Summary And Abstract With SIRI

**Files:**
- Modify: `scripts/v02_analysis/reports.py`
- Modify: `scripts/v02_analysis/runner.py`

- [ ] **Step 1: Update report function signatures**

Change:

```python
def write_summary(..., regression_tables: dict[str, pd.DataFrame], config: AnalysisConfig) -> None:
```

to accept optional SIRI ranking:

```python
def write_summary(..., regression_tables: dict[str, pd.DataFrame], siri_ranking: pd.DataFrame, config: AnalysisConfig) -> None:
```

Do the same for `write_abstract`.

- [ ] **Step 2: Add concise SIRI lines to summary**

In `write_summary`, add a short section or bullet:

```python
top_risk = siri_ranking.sort_values("rank").iloc[0]
siri_line = f"- SIRI 综合风险指数显示，2024 年风险最高的产品为 `{top_risk.product_code}`，基准得分为 {top_risk.siri_score:.2f}。权重敏感性检验用于确认风险排序是否依赖政策暴露权重。"
```

Keep wording conservative. Do not claim strict causal effects.

- [ ] **Step 3: Add concise SIRI lines to abstract**

In `write_abstract`, add one bullet under sample/method or findings:

```python
top_risk = siri_ranking.sort_values("rank").iloc[0]
siri_abstract_line = f"- 本文进一步构建 SIRI 半导体进口供应链风险指数。2024 年基准风险排序最高的产品为 `{top_risk.product_code}`，该指数用于综合刻画来源集中、政策暴露、替代不足和结构波动风险。"
```

Keep this as risk evaluation language, not causal identification language.

- [ ] **Step 4: Pass SIRI ranking from runner**

Update calls:

```python
write_summary(selected_products, annual, top_2024, regression_tables, siri_ranking, config)
write_abstract(selected_products, panel, annual, regression_tables, siri_ranking, config)
```

- [ ] **Step 5: Run pipeline and inspect generated docs**

Run:

```bash
.venv/bin/python scripts/run_v02_analysis.py
rg -n "SIRI|风险指数" docs/output/summary_v0.2.md docs/output/abstract_v0.2.md
```

Expected: both docs contain SIRI-related language.

- [ ] **Step 6: Commit pipeline integration**

```bash
git add scripts/v02_analysis/runner.py scripts/v02_analysis/plots.py scripts/v02_analysis/validation.py scripts/v02_analysis/reports.py results/v02 docs/output
git commit -m "feat: integrate SIRI outputs into v0.2 pipeline"
```

---

## Chunk 3: LaTeX Paper Scaffold And Draft

### Task 7: Create Paper Skeleton

**Files:**
- Create: `paper/main.tex`
- Create: `paper/sections/abstract.tex`
- Create: `paper/sections/introduction.tex`
- Create: `paper/sections/data.tex`
- Create: `paper/sections/descriptive.tex`
- Create: `paper/sections/risk_index.tex`
- Create: `paper/sections/regression.tex`
- Create: `paper/sections/conclusion.tex`
- Create: `paper/sections/appendix.tex`
- Create: `paper/references.bib`
- Create: `paper/ai_usage_notes.md`

- [ ] **Step 1: Create directories**

```bash
mkdir -p paper/sections paper/figures paper/tables
```

Create `paper/figures/README.md` explaining that paper figures are referenced from `../results/v02/figures/` through `\graphicspath`.

Create `paper/tables/README.md` explaining that LaTeX tables in this directory are compact paper-facing tables derived from generated CSV/Markdown outputs under `results/v02/tables/`.

- [ ] **Step 2: Create `paper/main.tex`**

Use `ctexart` and keep team metadata centralized:

```tex
\documentclass[UTF8,a4paper,12pt]{ctexart}

\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{float}
\usepackage{amsmath}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{natbib}

\geometry{left=2.8cm,right=2.8cm,top=2.6cm,bottom=2.6cm}
\hypersetup{colorlinks=true, linkcolor=black, citecolor=black, urlcolor=black}
\graphicspath{{../results/v02/figures/}}

\newcommand{\papertitle}{大国博弈下中国半导体相关产品进口来源结构演化与供应链风险评估研究}
\newcommand{\school}{最终提交前由参赛队填写}
\newcommand{\teamname}{最终提交前由参赛队填写}
\newcommand{\members}{最终提交前由参赛队填写}
\newcommand{\advisor}{最终提交前由参赛队填写}

\title{\papertitle}
\author{\school\\\teamname\\成员：\members\\指导教师：\advisor}
\date{2026年}

\begin{document}
\maketitle
\thispagestyle{empty}
\clearpage

\input{sections/abstract}
\clearpage
\tableofcontents
\clearpage

\input{sections/introduction}
\input{sections/data}
\input{sections/descriptive}
\input{sections/risk_index}
\input{sections/regression}
\input{sections/conclusion}

\bibliographystyle{plainnat}
\bibliography{references}

\appendix
\input{sections/appendix}

\end{document}
```

- [ ] **Step 3: Create section placeholders with real headings**

Each section file should contain headings and concise draft bullets, not empty placeholders. Example for `paper/sections/risk_index.tex`:

```tex
\section{半导体进口供应链风险指数构建}

本文构建半导体进口供应链风险指数 SIRI，从来源集中风险、政策暴露风险、替代不足风险和结构波动风险四个维度评价产品层面的进口来源结构风险。

\subsection{指标定义}

\begin{align}
SIRI_{p,t}=100\times(&0.25C_{p,t}+0.25P_{p,t}\\
&+0.25A_{p,t}+0.25V_{p,t})
\end{align}

其中，$C_{p,t}$ 表示来源集中风险，$P_{p,t}$ 表示政策暴露风险，$A_{p,t}$ 表示替代不足风险，$V_{p,t}$ 表示结构波动风险。四个维度均经 0--1 标准化处理。

\subsection{结果分析}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.92\textwidth]{siri_trend_by_product_v02.png}
    \caption{半导体相关产品 SIRI 风险指数变化趋势}
    \label{fig:siri-trend}
\end{figure}
```

- [ ] **Step 4: Create `paper/references.bib`**

Include at least these entries:

```bibtex
@misc{cepii_baci,
  author = {{CEPII}},
  title = {BACI: International Trade Database at the Product-Level},
  year = {2026},
  url = {https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37}
}

@misc{stats_modeling_2026,
  author = {{全国大学生统计建模大赛组织委员会}},
  title = {2026年全国大学生统计建模大赛通知},
  year = {2026}
}
```

- [ ] **Step 5: Create AI usage notes**

Create `paper/ai_usage_notes.md`:

```markdown
# AI 工具使用记录

| date | tool_name | usage_stage | specific_task | human_review_action | included_in_final_paper | estimated_generated_content_share | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04-28 | Codex | 选题设计 | 提供论文结构与 SIRI 指标公式备选方案，由参赛队筛选确认 | 参赛队审阅后确认研究边界与最终表述 | partial | 1-10% | 最终模型、结果解释和正文由参赛队审核确认 |
```

- [ ] **Step 6: Commit paper skeleton**

```bash
git add paper
git commit -m "docs: add LaTeX paper scaffold"
```

### Task 8: Draft Core Paper Content

**Files:**
- Modify: all `paper/sections/*.tex`
- Modify: `paper/references.bib`
- Create/modify: `paper/tables/product_codes.tex`
- Create/modify: `paper/tables/descriptive_statistics.tex`
- Create/modify: `paper/tables/siri_ranking_2024.tex`
- Create/modify: `paper/tables/siri_weight_sensitivity.tex`
- Create/modify: `paper/tables/regression_summary.tex`

- [ ] **Step 1: Fill abstract**

Write 300-500 Chinese characters. Required elements:

- Background: 大国博弈与半导体供应链安全。
- Data: BACI HS07 2008-2024, four HS6 products.
- Methods: 来源结构测度、SIRI、固定效应回归、稳健性检验。
- Findings: 美国份额在设备和部分 IC 产品下降，产品异质性明显，回归不支持强因果表述。
- Keywords: 大国博弈；半导体；进口来源结构；供应链风险；统计建模。

- [ ] **Step 2: Fill introduction**

Structure:

1. 国家战略和半导体供应链背景。
2. 美国出口管制与政策节点，使用 2018/2022/2023 作为粗节点。
3. 研究问题三条。
4. 本文贡献三条：多产品视角、SIRI 风险指数、严谨证据边界。

- [ ] **Step 3: Fill data section**

Include:

- BACI data source.
- Observation unit.
- Products table.
- Zero-filled balanced panel.
- Variables: `import_value_kusd`, `import_share`, `US`, `Post2018`, `Post2022`, `Post2023`, interaction terms.

Create `paper/tables/product_codes.tex` and include it from `paper/sections/data.tex`:

```tex
\begin{table}[H]
\centering
\caption{研究产品范围}
\label{tab:products}
\begin{tabular}{lll}
\toprule
HS6编码 & 产品类别 & 产品含义 \\
\midrule
848620 & 设备类 & 半导体器件或集成电路制造设备 \\
854231 & 集成电路类 & 处理器及控制器 \\
854232 & 集成电路类 & 存储器 \\
854239 & 集成电路类 & 其他电子集成电路 \\
\bottomrule
\end{tabular}
\end{table}
```

- [ ] **Step 4: Fill descriptive section**

Reference generated figures:

```tex
\includegraphics[width=0.92\textwidth]{total_imports_by_product_v02.png}
\includegraphics[width=0.92\textwidth]{usa_import_share_by_product_v02.png}
\includegraphics[width=0.92\textwidth]{top_2024_source_shares_by_product_v02.png}
\includegraphics[width=0.92\textwidth]{source_hhi_by_product_v02.png}
```

Use exact numbers from `docs/output/abstract_v0.2.md` and SIRI tables; do not invent numbers.

Create `paper/tables/descriptive_statistics.tex` as a compact table derived from `results/v02/tables/descriptive_statistics_v02.md`. Include at least observations, positive trade rows, exporters, years, mean import value, and mean import share. Reference it in `paper/sections/descriptive.tex`:

```tex
\input{tables/descriptive_statistics}
```

- [ ] **Step 5: Fill SIRI section**

Include formulas from the spec:

```tex
HHI_{p,t}=\sum_i s_{i,p,t}^{2}
```

```tex
V_{p,t}=\frac{1}{2}\sum_i |s_{i,p,t}-s_{i,p,t-1}|
```

Explain equal weighting and sensitivity weighting. Reference `siri_trend_by_product_v02.png`.

Create `paper/tables/siri_ranking_2024.tex` from `results/v02/tables/siri_ranking_2024_v02.csv` and include columns `rank`、`product_code`、`siri_score`、`rank_policy_weighted`、`rank_change`.

Create `paper/tables/siri_weight_sensitivity.tex` from `results/v02/tables/siri_weight_sensitivity_v02.csv` and include columns `product_code`、`baseline_rank`、`policy_weighted_rank`、`rank_change`、`baseline_siri_score`、`policy_weighted_siri_score`.

Reference both tables in `paper/sections/risk_index.tex`:

```tex
\input{tables/siri_ranking_2024}
\input{tables/siri_weight_sensitivity}
```

- [ ] **Step 6: Fill regression section**

Include model:

```tex
\ln(Import_{i,p,t}+1)=\beta_1 US_i\times Post2018_t+\beta_2 US_i\times Post2022_t+\beta_3 US_i\times Post2023_t+\alpha_i+\gamma_p+\delta_t+\varepsilon_{i,p,t}
```

Report current pooled results from `results/v02/tables/policy_stage_regression_results_v02.md`, share model from `share_outcome_regression_results_v02.md`, and robustness from `robustness_results_v02.md`.

Required wording: results do not support strict causal claims.

Create `paper/tables/regression_summary.tex` as a compact table with `US_Post2018`、`US_Post2022`、`US_Post2023` coefficients and p-values for the pooled absolute-value model and share model. Reference it in `paper/sections/regression.tex`:

```tex
\input{tables/regression_summary}
```

- [ ] **Step 7: Fill conclusion**

Conclusion:

- 来源结构重组。
- 产品风险异质性。
- 统计证据边界。
- Policy suggestions: differentiated risk monitoring, maintain alternative sources, avoid one-product extrapolation.

- [ ] **Step 8: Fill appendix**

Appendix:

- Reproduction command.
- Variable definition table.
- AI usage notes reference.

- [ ] **Step 9: Run source-level checks before compile**

Run from repository root:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
patterns = ["TO" + "DO", "TB" + "D", "待" + "定义", "占" + "位"]
paths = list(Path("paper/sections").glob("*.tex")) + list(Path("paper/tables").glob("*.tex")) + [Path("paper/references.bib"), Path("paper/ai_usage_notes.md")]
hits = []
for path in paths:
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        if pattern in text:
            hits.append(f"{path}: {pattern}")
assert not hits, "\n".join(hits)
body_paths = [path for path in Path("paper/sections").glob("*.tex") if path.name != "appendix.tex"]
text = "\n".join(path.read_text(encoding="utf-8") for path in body_paths)
chars = len(text)
print(f"paper section characters: {chars}")
assert chars <= 16000
PY
```

Expected: no unresolved placeholders;正文 character check prints a value at or below 16000.

- [ ] **Step 10: Compile or run source-level fallback check**

If XeLaTeX is installed:

```bash
cd paper
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

Expected: `paper/main.pdf` generated.

If XeLaTeX is not installed, run:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import re

for path in Path("paper/sections").glob("*.tex"):
    for image in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", path.read_text(encoding="utf-8")):
        target = Path("results/v02/figures") / image
        assert target.exists(), f"missing figure: {target}"
for table in Path("paper/tables").glob("*.tex"):
    assert table.read_text(encoding="utf-8").strip(), f"empty table: {table}"
main_text = Path("paper/main.tex").read_text(encoding="utf-8")
references_text = Path("paper/references.bib").read_text(encoding="utf-8")
assert "\\bibliography{references}" in main_text
assert "@misc{cepii_baci" in references_text
assert "@misc{stats_modeling_2026" in references_text
cite_keys = set(re.findall(r"\\cite\w*\{([^}]+)\}", "\n".join(path.read_text(encoding="utf-8") for path in Path("paper/sections").glob("*.tex"))))
for key_group in cite_keys:
    for key in [item.strip() for item in key_group.split(",")]:
        assert "{" + key + "," in references_text, f"missing bibliography key: {key}"
print("paper source fallback checks OK")
PY
test -s results/v02/figures/siri_trend_by_product_v02.png
```

Expected: figure/table checks pass; team metadata may remain in macros until参赛队 provides final identity information.

- [ ] **Step 11: Commit paper draft**

```bash
git add paper
git commit -m "docs: draft statistical modeling paper"
```

---

## Chunk 4: Final Verification And Packaging Readiness

### Task 9: Full Verification

**Files:**
- Read generated outputs.
- No code edits unless verification finds a defect.

- [ ] **Step 1: Run unit tests**

```bash
.venv/bin/python -m unittest tests.test_v02_risk_index -v
```

Expected: all PASS.

- [ ] **Step 2: Run full v0.2 pipeline**

```bash
.venv/bin/python scripts/run_v02_analysis.py
```

Expected: exits 0.

- [ ] **Step 3: Check SIRI output contract**

Run:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

root = Path(".")
required_files = [
    "results/v02/data/siri_index_by_product_year_v02.csv",
    "results/v02/tables/siri_index_by_product_year_v02.csv",
    "results/v02/tables/siri_index_by_product_year_v02.md",
    "results/v02/tables/siri_ranking_2024_v02.csv",
    "results/v02/tables/siri_ranking_2024_v02.md",
    "results/v02/tables/siri_weight_sensitivity_v02.csv",
    "results/v02/tables/siri_weight_sensitivity_v02.md",
    "results/v02/figures/siri_trend_by_product_v02.png",
]
for file_name in required_files:
    path = root / file_name
    assert path.exists(), f"missing output: {path}"
    assert path.stat().st_size > 0, f"empty output: {path}"

siri = pd.read_csv(root / "results/v02/data/siri_index_by_product_year_v02.csv")
required_columns = {
    "product_code",
    "year",
    "total_import_value_kusd",
    "concentration_raw",
    "policy_exposure_raw",
    "alternative_insufficiency_raw",
    "structural_volatility_raw",
    "concentration_norm",
    "policy_exposure_norm",
    "alternative_insufficiency_norm",
    "structural_volatility_norm",
    "siri_score",
    "siri_score_policy_weighted",
}
missing = required_columns - set(siri.columns)
assert not missing, missing
assert len(siri) == 68, len(siri)
assert siri["year"].min() == 2008
assert siri["year"].max() == 2024
assert siri["product_code"].nunique() == 4
coverage = siri.groupby("product_code")["year"].nunique()
assert (coverage == 17).all(), coverage.to_dict()
assert siri[list(required_columns)].notna().all().all()
for col in ["siri_score", "siri_score_policy_weighted"]:
    assert siri[col].between(0, 100).all(), col
for col in [c for c in siri.columns if c.endswith("_norm")]:
    assert siri[col].between(0, 1).all(), col
print("SIRI contract OK")
PY
```

Expected: prints `SIRI contract OK`.

- [ ] **Step 4: Check SIRI ranking and sensitivity contracts**

Run:

```bash
.venv/bin/python - <<'PY'
import pandas as pd

ranking = pd.read_csv("results/v02/tables/siri_ranking_2024_v02.csv")
sensitivity = pd.read_csv("results/v02/tables/siri_weight_sensitivity_v02.csv")
ranking_columns = {
    "rank",
    "product_code",
    "product_name",
    "year",
    "siri_score",
    "siri_score_policy_weighted",
    "rank_policy_weighted",
    "rank_change",
}
sensitivity_columns = {
    "product_code",
    "product_name",
    "baseline_rank",
    "policy_weighted_rank",
    "rank_change",
    "baseline_siri_score",
    "policy_weighted_siri_score",
}
assert ranking_columns.issubset(ranking.columns), ranking.columns.tolist()
assert sensitivity_columns.issubset(sensitivity.columns), sensitivity.columns.tolist()
assert len(ranking) == 4, len(ranking)
assert len(sensitivity) == 4, len(sensitivity)
assert set(ranking["product_code"]) == set(sensitivity["product_code"])
assert ranking["rank"].is_unique
assert ranking["rank_policy_weighted"].is_unique
print("SIRI ranking and sensitivity contracts OK")
PY
```

Expected: prints `SIRI ranking and sensitivity contracts OK`.

- [ ] **Step 5: Check validation log**

Run:

```bash
set -e
test -s docs/output/siri_validation_v0.2.md
rg -n "Zero total" docs/output/siri_validation_v0.2.md
rg -n "Raw dimensions with min=max" docs/output/siri_validation_v0.2.md
rg -n "missing USA record or zero US policy exposure" docs/output/siri_validation_v0.2.md
```

Expected: validation log exists and contains edge-case summary lines.

- [ ] **Step 6: Check test results table**

Run:

```bash
.venv/bin/python - <<'PY'
import pandas as pd

tests = pd.read_csv("results/v02/tables/test_results_v02.csv")
failed = tests.loc[tests["passed"] != "PASS"]
print(tests.groupby("category")["passed"].count())
assert failed.empty, failed.to_string(index=False)
PY
```

Expected: no assertion failure.

- [ ] **Step 7: Check paper figure and table references**

Run:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import re

tex_files = [Path("paper/main.tex"), *Path("paper/sections").glob("*.tex")]
for path in tex_files:
    text = path.read_text(encoding="utf-8")
    for image in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
        target = Path("results/v02/figures") / image
        assert target.exists(), f"{path} references missing figure {target}"
        assert target.stat().st_size > 0, f"{path} references empty figure {target}"
for table in [
    "paper/tables/product_codes.tex",
    "paper/tables/descriptive_statistics.tex",
    "paper/tables/siri_ranking_2024.tex",
    "paper/tables/siri_weight_sensitivity.tex",
    "paper/tables/regression_summary.tex",
]:
    target = Path(table)
    assert target.exists(), f"missing table {target}"
    assert target.read_text(encoding="utf-8").strip(), f"empty table {target}"
print("paper figure/table references OK")
PY
```

Expected: prints `paper figure/table references OK`.

- [ ] **Step 8: Check paper character count and unresolved placeholders**

Run:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
patterns = ["TO" + "DO", "TB" + "D", "待" + "定义", "占" + "位"]
paths = list(Path("paper/sections").glob("*.tex")) + list(Path("paper/tables").glob("*.tex")) + [Path("paper/references.bib"), Path("paper/ai_usage_notes.md")]
hits = []
for path in paths:
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        if pattern in text:
            hits.append(f"{path}: {pattern}")
assert not hits, "\n".join(hits)

body_paths = [path for path in Path("paper/sections").glob("*.tex") if path.name != "appendix.tex"]
text = "\n".join(path.read_text(encoding="utf-8") for path in body_paths)
chars = len(text)
print(f"paper section characters: {chars}")
assert chars <= 16000
PY
```

Expected: character count at or below 16000, no unresolved placeholders.

- [ ] **Step 9: Compile paper if TeX is available**

Run:

```bash
if command -v xelatex >/dev/null 2>&1; then
  set -e
  cd paper
  rm -f main.pdf
  xelatex -halt-on-error main.tex
  bibtex main
  xelatex -halt-on-error main.tex
  xelatex -halt-on-error main.tex
  test -s main.pdf
else
  echo "SKIP: xelatex not installed"
fi
```

Expected if available: `paper/main.pdf` exists. If `xelatex` is unavailable, output clearly records the skip.

- [ ] **Step 10: Handle verification failures through prior tasks**

If any verification step fails, stop and return to the task that owns the failing file. Do not make unplanned final-step edits in Task 9.

### Task 10: Final Handoff

**Files:**
- No required edits.

- [ ] **Step 1: Check packaging readiness**

Run:

```bash
set -e
test -s paper/ai_usage_notes.md
test -s paper/main.tex
test -d paper/sections
test -d paper/tables
.venv/bin/python - <<'PY'
from pathlib import Path
main_text = Path("paper/main.tex").read_text(encoding="utf-8")
for macro in ["\\school", "\\teamname", "\\members", "\\advisor"]:
    assert macro in main_text, f"missing metadata macro: {macro}"
text = Path("paper/ai_usage_notes.md").read_text(encoding="utf-8")
required = [
    "date",
    "tool_name",
    "usage_stage",
    "specific_task",
    "human_review_action",
    "included_in_final_paper",
    "estimated_generated_content_share",
    "notes",
]
missing = [field for field in required if field not in text]
assert not missing, missing
print("AI usage notes fields OK")
PY
```

Expected: AI usage notes and paper files exist. Metadata macros are visible so the team can replace them before final submission.

- [ ] **Step 2: Summarize outputs**

Report:

- SIRI files generated.
- Paper draft path.
- Whether `xelatex` compile passed or was skipped due missing TeX.
- AI usage notes path and official AI form mapping readiness.
- Any remaining human inputs: school, team name, members, advisor.

- [ ] **Step 3: Confirm clean git state**

Run:

```bash
git status --short
```

Expected: clean or only intentionally untracked generated files.
