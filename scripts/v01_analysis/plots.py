from __future__ import annotations

import os

from .config import AnalysisConfig


def configure_matplotlib(config: AnalysisConfig):
    # 先设置可写缓存目录，再导入 matplotlib，避免权限问题。
    os.environ.setdefault("MPLCONFIGDIR", str(config.mpl_config_dir))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.style.use("default")
    return plt, PercentFormatter


def plot_line(
    x,
    y,
    title: str,
    ylabel: str,
    output_name: str,
    config: AnalysisConfig,
    percent_axis: bool = False,
) -> None:
    """画单条时间趋势线，用于总额、美国进口额、美国份额和 HHI。"""
    plt, PercentFormatter = configure_matplotlib(config)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, linewidth=2.4, color="#1f4e79")
    # 2018 是当前 v0.1 的政策分界点，所以在核心图里画一条参考线。
    ax.axvline(2018, color="#a61c3c", linestyle="--", linewidth=1.5)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_xticks(config.years[::2])
    ax.grid(alpha=0.25, linestyle=":")
    if percent_axis:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / output_name, dpi=200)
    plt.close(fig)


def plot_source_shares(source_shares, config: AnalysisConfig) -> None:
    """画前五来源国份额变化图，直观看来源替代。"""
    plt, PercentFormatter = configure_matplotlib(config)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    share_columns = [column for column in source_shares.columns if column != "year"]
    palette = ["#1f4e79", "#4f81bd", "#c0504d", "#9bbb59", "#8064a2"]
    for color, column in zip(palette, share_columns):
        ax.plot(source_shares["year"], source_shares[column], linewidth=2.0, label=column, color=color)
    ax.axvline(2018, color="#a61c3c", linestyle="--", linewidth=1.5)
    ax.set_title("China imports of HS848620: top five source-country shares")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of China's imports")
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xticks(config.years[::2])
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(config.figure_output_dir / "top5_source_country_shares_848620.png", dpi=200)
    plt.close(fig)


def create_all_figures(annual_summary, source_shares, config: AnalysisConfig) -> None:
    # 这里把所有 v0.1 必做图明确列出来，避免后期漏图。
    plot_line(
        annual_summary["year"],
        annual_summary["total_import_kusd"],
        "China imports of HS848620: total annual imports",
        "Thousand USD",
        "china_total_imports_848620.png",
        config,
    )
    plot_line(
        annual_summary["year"],
        annual_summary["us_import_kusd"],
        "China imports of HS848620 from the USA",
        "Thousand USD",
        "china_imports_from_usa_848620.png",
        config,
    )
    plot_line(
        annual_summary["year"],
        annual_summary["us_share"],
        "USA share in China's HS848620 imports",
        "Share",
        "usa_share_848620.png",
        config,
        percent_axis=True,
    )
    plot_source_shares(source_shares, config)
    plot_line(
        annual_summary["year"],
        annual_summary["hhi"],
        "HHI of China's HS848620 import sources",
        "HHI",
        "source_hhi_848620.png",
        config,
    )
