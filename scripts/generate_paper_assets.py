from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "paper" / "figures"
TABLE_DIR = ROOT / "paper" / "tables"
V02_DATA_DIR = ROOT / "results" / "v02" / "data"
V02_TABLE_DIR = ROOT / "results" / "v02" / "tables"
V03_TABLE_DIR = ROOT / "results" / "v03_gcn" / "tables"


PRODUCT_LABELS = {
    848620: "HS848620\nEquipment",
    854231: "HS854231\nProcessors",
    854232: "HS854232\nMemory",
    854239: "HS854239\nOther ICs",
}

PRODUCT_SHORT = {
    848620: "848620 Equipment",
    854231: "854231 Processors",
    854232: "854232 Memory",
    854239: "854239 Other ICs",
}

DIMENSION_COLUMNS = [
    ("concentration_norm", "Source\nconcentration"),
    ("policy_exposure_norm", "Policy\nexposure"),
    ("alternative_insufficiency_norm", "Substitution\ninsufficiency"),
    ("structural_volatility_norm", "Structural\nvolatility"),
]

COUNTRY_SHORT = {
    "Rep. of Korea": "Korea",
    "Other Asia, nes": "Other Asia",
    "Viet Nam": "Vietnam",
    "China, Hong Kong SAR": "Hong Kong",
    "United States of America": "USA",
}

COUNTRY_COLORS = {
    "Japan": "#2d5f9a",
    "Netherlands": "#d07a2d",
    "Singapore": "#4d8f5b",
    "USA": "#b13f4a",
    "Rep. of Korea": "#6f5aa8",
    "Malaysia": "#a4a338",
    "Other Asia, nes": "#3d8da8",
    "Viet Nam": "#c06b96",
    "Ireland": "#7a7a7a",
    "Israel": "#4b78a8",
    "Germany": "#8b5a3c",
    "Other": "#c9c9c9",
}


def _configure_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "axes.titleweight": "bold",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.08,
        }
    )
    return plt, PercentFormatter


def _ensure_dirs() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def _short_country(name: str) -> str:
    return COUNTRY_SHORT.get(name, name)


def _latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def _draw_box(ax, xy, width, height, text, face, edge="#2f4154", fontsize=10):
    import matplotlib.patches as patches

    box = patches.FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.018",
        linewidth=1.3,
        facecolor=face,
        edgecolor=edge,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#1e2b35",
        weight="bold",
        linespacing=1.2,
    )


def _draw_arrow(ax, start, end, color="#536878"):
    import matplotlib.patches as patches

    arrow = patches.FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.4,
        color=color,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arrow)


def plot_research_framework() -> None:
    plt, _ = _configure_matplotlib()
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    nodes = [
        (0.05, 0.58, "BACI HS07\nimport panel", "#dbe9f6"),
        (0.34, 0.58, "Source-structure\nprofiling", "#e8f1df"),
        (0.63, 0.58, "SIRI risk\nindex", "#f5e2d2"),
        (0.63, 0.18, "Fixed-effects\nstatistical tests", "#f2dddd"),
        (0.34, 0.18, "Trade-network\nforecast extension", "#e5def3"),
        (0.05, 0.18, "Policy and\nmonitoring advice", "#e2ece8"),
    ]
    width = 0.22
    height = 0.22
    for x, y, label, color in nodes:
        _draw_box(ax, (x, y), width, height, label, color)

    centers = [(x + width / 2, y + height / 2) for x, y, _, _ in nodes]
    for start, end in zip(centers[:3], centers[1:3]):
        _draw_arrow(ax, (start[0] + width / 2 - 0.01, start[1]), (end[0] - width / 2 + 0.01, end[1]))
    _draw_arrow(ax, (centers[2][0], centers[2][1] - height / 2 + 0.01), (centers[3][0], centers[3][1] + height / 2 - 0.01))
    for start, end in zip(centers[3:], centers[4:]):
        _draw_arrow(ax, (start[0] - width / 2 + 0.01, start[1]), (end[0] + width / 2 - 0.01, end[1]))

    ax.text(0.5, 0.95, "Evidence Chain for Product-Level Semiconductor Import Risk", ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.04, "Descriptive facts -> interpretable risk scoring -> evidence boundaries -> forecasting prototype", ha="center", fontsize=9, color="#485866")
    fig.savefig(FIGURE_DIR / "research_framework_flow.png", dpi=240)
    plt.close(fig)


def plot_siri_hierarchy() -> None:
    plt, _ = _configure_matplotlib()
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    _draw_box(ax, (0.32, 0.76), 0.36, 0.14, "SIRI composite risk score\n(product-year, 0-100)", "#dbe9f6", fontsize=11)

    dims = [
        (0.04, 0.42, "Source concentration\nHHI of all sources", "#e8f1df"),
        (0.28, 0.42, "Policy exposure\nUSA import share", "#f5e2d2"),
        (0.52, 0.42, "Substitution insufficiency\nnon-USA source HHI", "#f2dddd"),
        (0.76, 0.42, "Structural volatility\nyearly share turnover", "#e5def3"),
    ]
    for x, y, label, color in dims:
        _draw_box(ax, (x, y), 0.20, 0.17, label, color, fontsize=9)
        _draw_arrow(ax, (0.50, 0.76), (x + 0.10, y + 0.17))

    bottom = [
        (0.04, 0.16, "0-1 normalization"),
        (0.28, 0.16, "0-1 normalization"),
        (0.52, 0.16, "0-1 normalization"),
        (0.76, 0.16, "0-1 normalization"),
    ]
    for x, y, label in bottom:
        _draw_box(ax, (x, y), 0.20, 0.10, label, "#f7f7f7", fontsize=8.5)
        _draw_arrow(ax, (x + 0.10, 0.42), (x + 0.10, 0.26))

    ax.text(0.5, 0.05, "Baseline weights: 25% each; sensitivity check raises policy exposure to 40%", ha="center", fontsize=9, color="#485866")
    fig.savefig(FIGURE_DIR / "siri_framework_hierarchy.png", dpi=240)
    plt.close(fig)


def plot_v03_workflow() -> None:
    plt, _ = _configure_matplotlib()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    nodes = [
        (0.04, 0.58, "BACI trade\ndata", "#dbe9f6"),
        (0.24, 0.58, "20 HS6\nproduct pool", "#e8f1df"),
        (0.44, 0.58, "Annual source\nnetworks", "#f5e2d2"),
        (0.64, 0.58, "Feature and\nSIRI target set", "#e5def3"),
        (0.84, 0.58, "Forecast\nmodels", "#f2dddd"),
        (0.44, 0.18, "Product-year\ngraph samples", "#f7f7f7"),
        (0.64, 0.18, "Next-year\nSIRI labels", "#f7f7f7"),
        (0.84, 0.18, "MAE / RMSE /\nrank evaluation", "#f7f7f7"),
    ]
    width, height = 0.14, 0.18
    for x, y, label, color in nodes:
        _draw_box(ax, (x, y), width, height, label, color, fontsize=9)

    top_centers = [(x + width / 2, y + height / 2) for x, y, _, _ in nodes[:5]]
    for start, end in zip(top_centers, top_centers[1:]):
        _draw_arrow(ax, (start[0] + width / 2 - 0.005, start[1]), (end[0] - width / 2 + 0.005, end[1]))
    _draw_arrow(ax, (0.51, 0.58), (0.51, 0.36))
    _draw_arrow(ax, (0.71, 0.36), (0.71, 0.58))
    _draw_arrow(ax, (0.71, 0.27), (0.84, 0.27))
    _draw_arrow(ax, (0.91, 0.58), (0.91, 0.36))

    ax.text(0.5, 0.94, "BACI-only Trade-Network Forecasting Extension", ha="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.05, "Naive baseline, Ridge features, and lightweight trade-network prototype are evaluated on time-based splits", ha="center", fontsize=9, color="#485866")
    fig.savefig(FIGURE_DIR / "v03_prediction_workflow.png", dpi=240)
    plt.close(fig)


def plot_policy_timeline() -> None:
    plt, _ = _configure_matplotlib()
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.set_xlim(2017.2, 2025.6)
    ax.set_ylim(-1.2, 1.2)
    ax.axis("off")
    ax.hlines(0, 2018, 2024.9, color="#5c6670", linewidth=1.6)

    events = [
        (2018.0, "2018\nEntity List\nrestrictions", 0.55, "#dbe9f6"),
        (2022.58, "Aug 2022\nCHIPS and\nScience Act", -0.72, "#e8f1df"),
        (2022.77, "Oct 2022\nadvanced chips\nand SME controls", 0.72, "#f5e2d2"),
        (2023.80, "Oct 2023\nrules tightened\nand corrected", -0.72, "#f2dddd"),
        (2024.92, "Dec 2024\nHBM / FDP /\nSME updates", 0.72, "#e5def3"),
    ]
    for x, label, y, color in events:
        ax.plot(x, 0, marker="o", markersize=8, color="#2f4154")
        ax.vlines(x, 0, y * 0.72, color="#788895", linewidth=1.1)
        _draw_box(ax, (x - 0.47, y - 0.18), 0.94, 0.36, label, color, fontsize=8.2)

    ax.text(2021.4, 1.08, "Selected U.S. Semiconductor Export-Control Milestones within the 2008-2024 Sample Window", ha="center", fontsize=12, weight="bold")
    fig.savefig(FIGURE_DIR / "policy_timeline.png", dpi=240)
    plt.close(fig)


def plot_source_structure_area() -> None:
    plt, PercentFormatter = _configure_matplotlib()
    panel = pd.read_csv(V02_DATA_DIR / "balanced_panel_multi_product_china_2008_2024.csv")
    years = sorted(panel["year"].unique())
    products = sorted(panel["product_code"].unique())

    fig, axes = plt.subplots(len(products), 1, figsize=(11, 10.8), sharex=True)
    if len(products) == 1:
        axes = [axes]

    for ax, product_code in zip(axes, products):
        product = panel.loc[panel["product_code"] == product_code].copy()
        shares = (
            product.groupby(["year", "exporter_name"], as_index=False)["import_value_kusd"]
            .sum()
            .merge(product.groupby("year", as_index=False)["import_value_kusd"].sum().rename(columns={"import_value_kusd": "total"}), on="year")
        )
        shares["share"] = np.where(shares["total"] > 0, shares["import_value_kusd"] / shares["total"], 0.0)

        top_2024 = shares.loc[shares["year"] == 2024].nlargest(5, "share")["exporter_name"].tolist()
        selected = list(top_2024)
        if "USA" not in selected:
            selected.append("USA")
        selected = selected[:7]

        pivot = shares.pivot_table(index="year", columns="exporter_name", values="share", aggfunc="sum").reindex(years).fillna(0)
        selected = [country for country in selected if country in pivot.columns]
        area = pivot[selected].copy()
        area["Other"] = (1 - area.sum(axis=1)).clip(lower=0)
        labels = [_short_country(country) for country in area.columns]
        colors = [COUNTRY_COLORS.get(country, "#8ba3bd") for country in area.columns]

        ax.stackplot(years, [area[column].to_numpy() for column in area.columns], labels=labels, colors=colors, alpha=0.92)
        for year in [2018, 2022, 2023]:
            ax.axvline(year, color="#303030", linestyle="--", linewidth=0.8, alpha=0.55)
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.grid(axis="y", alpha=0.20, linestyle=":")
        ax.set_title(PRODUCT_SHORT.get(product_code, str(product_code)), loc="left", pad=2)
        ax.legend(loc="center left", bbox_to_anchor=(1.005, 0.5), frameon=False, ncol=1)

    axes[-1].set_xlabel("Year")
    for ax in axes:
        ax.set_ylabel("Share")
    fig.suptitle("China Import Source Structure by Product, 2008-2024", fontsize=13, weight="bold", y=0.985)
    fig.subplots_adjust(right=0.78, hspace=0.35, top=0.93)
    fig.savefig(FIGURE_DIR / "source_structure_100pct_area.png", dpi=240)
    plt.close(fig)


def plot_siri_radar() -> None:
    plt, _ = _configure_matplotlib()
    siri = pd.read_csv(V02_DATA_DIR / "siri_index_by_product_year_v02.csv")
    data = siri.loc[siri["year"] == 2024].sort_values("product_code")
    columns = [column for column, _ in DIMENSION_COLUMNS]
    labels = [label for _, label in DIMENSION_COLUMNS]
    angles = np.linspace(0, 2 * math.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7.2, 7.2), subplot_kw={"projection": "polar"})
    colors = ["#2d5f9a", "#b13f4a", "#4d8f5b", "#6f5aa8"]
    for (_, row), color in zip(data.iterrows(), colors):
        values = [float(row[column]) * 100 for column in columns]
        values += values[:1]
        ax.plot(angles, values, color=color, linewidth=2.1, label=PRODUCT_SHORT[int(row["product_code"])])
        ax.fill(angles, values, color=color, alpha=0.10)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"])
    ax.grid(alpha=0.28)
    ax.set_title("2024 SIRI Dimension Profiles", pad=24, fontsize=13, weight="bold")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.20), ncol=2, frameon=False)
    fig.savefig(FIGURE_DIR / "siri_2024_radar.png", dpi=240)
    plt.close(fig)


def plot_siri_contribution() -> None:
    plt, _ = _configure_matplotlib()
    siri = pd.read_csv(V02_DATA_DIR / "siri_index_by_product_year_v02.csv")
    products = sorted(siri["product_code"].unique())
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.2), sharex=True, sharey=True)
    axes = axes.ravel()
    colors = ["#2d5f9a", "#d07a2d", "#4d8f5b", "#6f5aa8"]

    for ax, product_code in zip(axes, products):
        product = siri.loc[siri["product_code"] == product_code].sort_values("year")
        bottom = np.zeros(len(product))
        for (column, label), color in zip(DIMENSION_COLUMNS, colors):
            contribution = product[column].to_numpy() * 25
            ax.bar(product["year"], contribution, bottom=bottom, color=color, width=0.75, label=label.replace("\n", " "))
            bottom += contribution
        for year in [2018, 2022, 2023]:
            ax.axvline(year, color="#303030", linestyle="--", linewidth=0.8, alpha=0.45)
        ax.set_title(PRODUCT_SHORT.get(product_code, str(product_code)), loc="left")
        ax.grid(axis="y", alpha=0.20, linestyle=":")
        ax.set_ylim(0, 100)

    for ax in axes[2:]:
        ax.set_xlabel("Year")
    for ax in axes[::2]:
        ax.set_ylabel("SIRI contribution")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle("Decomposition of SIRI Scores by Dimension", fontsize=13, weight="bold", y=0.99)
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    fig.savefig(FIGURE_DIR / "siri_dimension_contribution.png", dpi=240)
    plt.close(fig)


def plot_policy_interaction_forest() -> None:
    plt, _ = _configure_matplotlib()
    policy = pd.read_csv(V02_TABLE_DIR / "policy_stage_regression_results_v02.csv")
    share = pd.read_csv(V02_TABLE_DIR / "share_outcome_regression_results_v02.csv")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    specs = [
        (axes[0], policy, "ln(import + 1)", 1.0, "Coefficient"),
        (axes[1], share, "Import share", 100.0, "Percentage points"),
    ]
    term_labels = {"US_Post2018": "US x Post2018", "US_Post2022": "US x Post2022", "US_Post2023": "US x Post2023"}

    for ax, df, title, scale, xlabel in specs:
        df = df.copy()
        df["label"] = df["term"].map(term_labels)
        y = np.arange(len(df))[::-1]
        coef = df["coef"].to_numpy() * scale
        ci_low = df["ci_low"].to_numpy() * scale
        ci_high = df["ci_high"].to_numpy() * scale
        xerr = np.vstack([coef - ci_low, ci_high - coef])
        ax.errorbar(coef, y, xerr=xerr, fmt="o", color="#2d5f9a", ecolor="#6f7f8f", elinewidth=2, capsize=4)
        ax.axvline(0, color="#303030", linewidth=1.0, linestyle="--")
        ax.set_yticks(y)
        ax.set_yticklabels(df["label"])
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        ax.grid(axis="x", alpha=0.22, linestyle=":")

    fig.suptitle("Policy Interaction Estimates with 95% Confidence Intervals", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIGURE_DIR / "policy_interaction_forest.png", dpi=240)
    plt.close(fig)


def plot_prediction_metrics() -> None:
    plt, _ = _configure_matplotlib()
    metrics = pd.read_csv(V03_TABLE_DIR / "gcn_metrics.csv")
    test = metrics.loc[metrics["split"] == "test"].copy()
    test["model_label"] = test["model"].map({"naive": "Naive", "ridge": "Ridge", "gcn_numpy": "Trade-network\nprototype"})
    scope_labels = {
        "all_model_products": "All 20 model products",
        "core4_model_products": "Core 4 paper products",
    }

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, (scope, title) in zip(axes, scope_labels.items()):
        group = test.loc[test["sample_scope"] == scope].sort_values("model")
        x = np.arange(len(group))
        width = 0.34
        ax.bar(x - width / 2, group["mae"], width, label="MAE", color="#2d5f9a")
        ax.bar(x + width / 2, group["rmse"], width, label="RMSE", color="#d07a2d")
        ax.set_xticks(x)
        ax.set_xticklabels(group["model_label"])
        ax.set_title(title)
        ax.set_ylabel("Error")
        ax.grid(axis="y", alpha=0.22, linestyle=":")
        for xi, value in zip(x - width / 2, group["mae"]):
            ax.text(xi, value, f"{value:.1f}", ha="center", va="bottom", fontsize=7)
        for xi, value in zip(x + width / 2, group["rmse"]):
            ax.text(xi, value, f"{value:.1f}", ha="center", va="bottom", fontsize=7)

    axes[0].legend(frameon=False)
    fig.suptitle("v0.3 Test-Set Forecast Error Comparison", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIGURE_DIR / "prediction_metrics_bar.png", dpi=240)
    plt.close(fig)


def write_top5_comparison_table() -> None:
    panel = pd.read_csv(V02_DATA_DIR / "balanced_panel_multi_product_china_2008_2024.csv")
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{2017与2024年主要来源国Top5对照}",
        r"\label{tab:source-top5-2017-2024}",
        r"\scriptsize",
        r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.16\textwidth}>{\raggedright\arraybackslash}p{0.39\textwidth}>{\raggedright\arraybackslash}p{0.39\textwidth}@{}}",
        r"\toprule",
        r"产品 & 2017年Top5来源国份额 & 2024年Top5来源国份额 \\",
        r"\midrule",
    ]
    for product_code in sorted(panel["product_code"].unique()):
        row_parts = []
        for year in [2017, 2024]:
            product_year = (
                panel.loc[(panel["product_code"] == product_code) & (panel["year"] == year)]
                .sort_values("import_share", ascending=False)
                .head(5)
            )
            entries = [
                f"{_short_country(str(row.exporter_name))} {row.import_share * 100:.2f}%"
                for row in product_year.itertuples()
            ]
            row_parts.append("; ".join(entries))
        product = _latex_escape(PRODUCT_SHORT[int(product_code)])
        lines.append(f"{product} & {_latex_escape(row_parts[0])} & {_latex_escape(row_parts[1])} \\\\")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption*{注：份额为该来源国占中国对应HS6产品年度进口额的比例，按各年内部份额排序。}",
            r"\end{table}",
            "",
        ]
    )
    (TABLE_DIR / "source_top5_2017_2024.tex").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    _ensure_dirs()
    plot_research_framework()
    plot_siri_hierarchy()
    plot_v03_workflow()
    plot_policy_timeline()
    plot_source_structure_area()
    plot_siri_radar()
    plot_policy_interaction_forest()
    plot_prediction_metrics()
    write_top5_comparison_table()


if __name__ == "__main__":
    main()
