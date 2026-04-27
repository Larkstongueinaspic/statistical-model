from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AnalysisConfig:
    """Central configuration for the v0.2 reproducible workflow."""

    root: Path = PACKAGE_ROOT
    candidate_product_codes: tuple[str, ...] = ("848620", "854231", "854232", "854239")
    china_code: int = 156
    usa_code: int = 842
    years: tuple[int, ...] = tuple(range(2008, 2025))
    base_year: int = 2017
    chunk_size: int = 1_000_000
    yearly_file_template: str = "BACI_HS07_Y{year}_V202601.csv"

    data_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    data_output_dir: Path = field(init=False)
    figure_output_dir: Path = field(init=False)
    table_output_dir: Path = field(init=False)
    docs_output_dir: Path = field(init=False)
    mpl_config_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_dir", self.root / "BACI_HS07_V202601")
        object.__setattr__(self, "output_dir", self.root / "results" / "v02")
        object.__setattr__(self, "data_output_dir", self.output_dir / "data")
        object.__setattr__(self, "figure_output_dir", self.output_dir / "figures")
        object.__setattr__(self, "table_output_dir", self.output_dir / "tables")
        object.__setattr__(self, "docs_output_dir", self.root / "docs" / "output")
        object.__setattr__(self, "mpl_config_dir", self.root / ".mplconfig")

    def yearly_file(self, year: int) -> Path:
        return self.data_dir / self.yearly_file_template.format(year=year)


def get_config() -> AnalysisConfig:
    return AnalysisConfig()
