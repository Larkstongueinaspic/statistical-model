from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# 当前文件位于 scripts/v01_analysis/ 下，再向上两层就是项目根目录。
PACKAGE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AnalysisConfig:
    """集中管理项目配置，避免路径和样本口径散落在各个脚本里。"""

    root: Path = PACKAGE_ROOT
    product_code: str = "848620"
    china_code: int = 156
    usa_code: int = 842
    years: tuple[int, ...] = tuple(range(2008, 2025))
    chunk_size: int = 1_000_000
    yearly_file_template: str = "BACI_HS07_Y{year}_V202601.csv"

    data_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    data_output_dir: Path = field(init=False)
    figure_output_dir: Path = field(init=False)
    table_output_dir: Path = field(init=False)
    mpl_config_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        # 所有输入输出路径都从项目根目录统一推导，方便复跑和迁移。
        object.__setattr__(self, "data_dir", self.root / "BACI_HS07_V202601")
        object.__setattr__(self, "output_dir", self.root / "results")
        object.__setattr__(self, "data_output_dir", self.output_dir / "data")
        object.__setattr__(self, "figure_output_dir", self.output_dir / "figures")
        object.__setattr__(self, "table_output_dir", self.output_dir / "tables")
        object.__setattr__(self, "mpl_config_dir", self.root / ".mplconfig")

    def yearly_file(self, year: int) -> Path:
        return self.data_dir / self.yearly_file_template.format(year=year)


def get_config() -> AnalysisConfig:
    """提供统一配置入口，其他模块不需要重复写路径。"""
    return AnalysisConfig()
