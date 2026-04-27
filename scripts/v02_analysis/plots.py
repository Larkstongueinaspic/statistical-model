from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .config import AnalysisConfig


PRODUCT_COLORS = {
    "848620": "#1f4e79",
    "854231": "#c0504d",
    "854232": "#4f7f36",
    "854239": "#8064a2",
}


def configure_matplotlib(config: AnalysisConfig):
    os.environ.setdefault("MPLCONFIGDIR", str(config.mpl_config_dir))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.style.use("default")
    return plt, PercentFormatter


def _add_policy_lines(ax) -> None:
    for year, alpha in [(2018, 0.75), (2022, 0.55), (2023, 0.45)]:
        ax.axvline(year, color="#555555", linestyle="--", linewidth=1.0, alpha=alpha)


def plot_product_lines(
    annual: pd.DataFrame,
    value_column: str,
    title: str,
    ylabel: str,
    filename: str,
    config: AnalysisConfig,
    percent_axis: bool = False,
    scale: float = 1.0,
) -> None:
    plt, PercentFormatter = configure_matplotlib(config)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for product_code, group in annual.groupby("product_code"):
        ax.plot(
            group["year"],
            group[value_column] / scale,
            label=f"HS{product_code}",
            linewidth=2.2,
            color=PRODUCT_COLORS.get(str(product_code), None),
        )
    _add_policy_lines(ax)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_xticks(config.years[::2])
    ax.grid(alpha=0.25, linestyle=":")
    if percent_axis:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / filename, dpi=220)
    plt.close(fig)


def plot_top_2024_sources(top_2024: pd.DataFrame, config: AnalysisConfig) -> None:
    plt, PercentFormatter = configure_matplotlib(config)
    products = top_2024["product_code"].drop_duplicates().tolist()
    n_products = len(products)
    fig, axes = plt.subplots(n_products, 1, figsize=(11, max(3.0 * n_products, 7.5)), sharex=True)
    if n_products == 1:
        axes = [axes]
    for ax, product_code in zip(axes, products):
        group = top_2024.loc[top_2024["product_code"] == product_code].sort_values("share", ascending=True)
        colors = ["#a61c3c" if name == "USA" or "United States" in str(name) else "#1f4e79" for name in group["exporter_name"]]
        ax.barh(group["exporter_name"], group["share"], color=colors, alpha=0.88)
        ax.set_title(f"HS{product_code}: 2024 top source-country shares", loc="left", fontsize=11)
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.grid(axis="x", alpha=0.25, linestyle=":")
    axes[-1].set_xlabel("Share of China's imports")
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / "top_2024_source_shares_by_product_v02.png", dpi=220)
    plt.close(fig)


def plot_us_share_change_index(annual: pd.DataFrame, config: AnalysisConfig) -> None:
    plt, _ = configure_matplotlib(config)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for product_code, group in annual.groupby("product_code"):
        group = group.sort_values("year").copy()
        base = group.loc[group["year"] == config.base_year, "us_share"]
        if base.empty or float(base.iloc[0]) == 0:
            continue
        group["us_share_index_2017"] = group["us_share"] / float(base.iloc[0]) * 100
        ax.plot(
            group["year"],
            group["us_share_index_2017"],
            label=f"HS{product_code}",
            linewidth=2.2,
            color=PRODUCT_COLORS.get(str(product_code), None),
        )
    _add_policy_lines(ax)
    ax.axhline(100, color="#333333", linewidth=1.0, alpha=0.7)
    ax.set_title("USA import-share index by product (2017 = 100)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Index")
    ax.set_xticks(config.years[::2])
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / "usa_share_index_2017_by_product_v02.png", dpi=220)
    plt.close(fig)


def plot_product_group_comparison(annual: pd.DataFrame, config: AnalysisConfig) -> None:
    plt, PercentFormatter = configure_matplotlib(config)
    grouped = (
        annual.groupby(["product_group", "year"], as_index=False)[["total_import_kusd", "us_import_kusd"]]
        .sum()
        .sort_values(["product_group", "year"])
    )
    grouped["us_share"] = np.where(
        grouped["total_import_kusd"] > 0,
        grouped["us_import_kusd"] / grouped["total_import_kusd"],
        0.0,
    )
    fig, ax = plt.subplots(figsize=(10, 5.8))
    for product_group, group in grouped.groupby("product_group"):
        ax.plot(group["year"], group["us_share"], linewidth=2.2, label=product_group.replace("_", " ").title())
    _add_policy_lines(ax)
    ax.set_title("USA share by product group")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share")
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xticks(config.years[::2])
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / "usa_share_by_product_group_v02.png", dpi=220)
    plt.close(fig)


def create_all_figures(annual: pd.DataFrame, top_2024: pd.DataFrame, config: AnalysisConfig) -> None:
    plot_product_lines(
        annual,
        "total_import_kusd",
        "China total imports by selected semiconductor-related product",
        "Billion USD",
        "total_imports_by_product_v02.png",
        config,
        scale=1_000_000.0,
    )
    plot_product_lines(
        annual,
        "us_import_kusd",
        "China imports from the USA by selected product",
        "Billion USD",
        "usa_imports_by_product_v02.png",
        config,
        scale=1_000_000.0,
    )
    plot_product_lines(
        annual,
        "us_share",
        "USA share in China's imports by selected product",
        "Share",
        "usa_import_share_by_product_v02.png",
        config,
        percent_axis=True,
    )
    plot_product_lines(
        annual,
        "hhi",
        "Source concentration by selected product",
        "HHI",
        "source_hhi_by_product_v02.png",
        config,
    )
    plot_top_2024_sources(top_2024, config)
    plot_us_share_change_index(annual, config)
    plot_product_group_comparison(annual, config)
