
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
M10_DIR = ROOT / "m10"
if str(M10_DIR) not in sys.path:
    sys.path.insert(0, str(M10_DIR))

import arara_m10 as m10


@dataclass(frozen=True)
class Config:
    version: str = "12.0"
    fixed_snr: float = 9.0
    fractions: tuple[float, ...] = (0.25, 0.50, 0.75, 1.0)

    development_root_seed: int = 2026080701
    holdout_root_seed: int = 2026080702
    bootstrap_seed: int = 2026080703

    development_base_fields_per_shape_context: int = 1000
    development_negatives_per_family: int = 2000
    holdout_positive_per_stratum_total: int = 2500
    holdout_negative_per_family_total: int = 5000
    holdout_batches: int = 20
    holdout_positive_per_stratum_per_batch: int = 125
    holdout_negative_per_family_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    maximum_adjacent_point_drop: float = 0.02
    predicted_first_passing_fraction: float = 0.75
    bootstrap_replicates: int = 10_000

    def panel_config(self):
        base = m10.Config(
            version=self.version,
            fixed_snr=self.fixed_snr,
            fractions=self.fractions,
            development_root_seed=self.development_root_seed,
            holdout_root_seed=self.holdout_root_seed,
            bootstrap_seed=self.bootstrap_seed,
            development_base_fields_per_shape_context=(
                self.development_base_fields_per_shape_context
            ),
            development_negatives_per_family=(
                self.development_negatives_per_family
            ),
            holdout_positive_per_stratum_total=(
                self.holdout_positive_per_stratum_total
            ),
            holdout_negative_per_family_total=(
                self.holdout_negative_per_family_total
            ),
            holdout_batches=self.holdout_batches,
            holdout_positive_per_stratum_per_batch=(
                self.holdout_positive_per_stratum_per_batch
            ),
            holdout_negative_per_family_per_batch=(
                self.holdout_negative_per_family_per_batch
            ),
            development_fpr_target=self.development_fpr_target,
            holdout_fpr_upper_limit=self.holdout_fpr_upper_limit,
            minimum_global_recall_lower_ci=(
                self.minimum_global_recall_lower_ci
            ),
            minimum_stratum_recall_lower_ci=(
                self.minimum_stratum_recall_lower_ci
            ),
            minimum_good_strata=self.minimum_good_strata,
            minimum_good_batches=self.minimum_good_batches,
            batch_recall_threshold=self.batch_recall_threshold,
            maximum_adjacent_point_drop=(
                self.maximum_adjacent_point_drop
            ),
            predicted_first_passing_fraction=(
                self.predicted_first_passing_fraction
            ),
            bootstrap_replicates=self.bootstrap_replicates,
        )
        return base.panel_config()


def evaluate_positive_panel(panel, cfg: Config):
    return m10.evaluate_positive_panel(panel, cfg)


def evaluate_negative_family(family, n, rng, cfg: Config):
    return m10.evaluate_negative_family(family, n, rng, cfg)


def evaluate_development(cfg: Config):
    return m10.evaluate_development(cfg)


def evaluate_holdout(thresholds: dict, cfg: Config):
    return m10.evaluate_holdout(thresholds, cfg)


def sha256_file(path: Path) -> str:
    return m10.sha256_file(path)


def write_environment(path: Path) -> None:
    import numpy
    import pandas
    import scipy
    import sklearn

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m10_dependency_sha256": sha256_file(
            M10_DIR / "arara_m10.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
