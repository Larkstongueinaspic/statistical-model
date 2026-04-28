from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GcnConfig:
    """Configuration for the v0.3 dynamic GCN workflow."""

    root: Path = PACKAGE_ROOT
    years: tuple[int, ...] = tuple(range(2008, 2025))
    train_years: tuple[int, ...] = tuple(range(2008, 2020))
    validation_years: tuple[int, ...] = (2020, 2021)
    test_years: tuple[int, ...] = (2022, 2023)
    min_positive_years: int = 12
    min_exporter_count: int = 5
    min_labeled_transitions: int = 10
    min_model_products: int = 10
    min_labeled_graphs: int = 100
    disable_gdelt: bool = False
    allow_baci_only: bool = False
    gdelt_apply_keyword_filter: bool = False
    add_reverse_edges: bool = True
    add_self_loops: bool = True
    random_seed: int = 20260428
    hidden_dim: int = 32
    epochs: int = 300
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    early_stopping_patience: int = 30

    baci_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    data_output_dir: Path = field(init=False)
    table_output_dir: Path = field(init=False)
    figure_output_dir: Path = field(init=False)
    model_output_dir: Path = field(init=False)
    docs_output_dir: Path = field(init=False)
    gdelt_input_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "baci_dir", self.root / "BACI_HS07_V202601")
        object.__setattr__(self, "output_dir", self.root / "results" / "v03_gcn")
        object.__setattr__(self, "data_output_dir", self.output_dir / "data")
        object.__setattr__(self, "table_output_dir", self.output_dir / "tables")
        object.__setattr__(self, "figure_output_dir", self.output_dir / "figures")
        object.__setattr__(self, "model_output_dir", self.output_dir / "models")
        object.__setattr__(self, "docs_output_dir", self.root / "docs" / "output")
        object.__setattr__(self, "gdelt_input_dir", self.root / "data" / "gdelt")


def get_config() -> GcnConfig:
    return GcnConfig()

