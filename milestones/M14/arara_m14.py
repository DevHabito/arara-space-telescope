
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
M9_DIR = ROOT / "m9"
if str(M9_DIR) not in sys.path:
    sys.path.insert(0, str(M9_DIR))

import arara_m9 as m9


@dataclass(frozen=True)
class Config:
    version: str = "14.0"
    target_fraction: float = 0.50
    snr_levels: tuple[float, ...] = (
        10.5, 11.0, 11.5, 12.0
    )

    development_root_seed: int = 2026080901
    holdout_root_seed: int = 2026080902
    bootstrap_seed: int = 2026080903

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
    predicted_first_passing_snr: float = 12.0
    bootstrap_replicates: int = 10_000

    def core(self) -> m9.Config:
        return m9.Config(
            version=self.version,
            snr_levels=self.snr_levels,
            target_fraction=self.target_fraction,
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
            strong_fail_snr12_recall_upper=0.50,
            bootstrap_replicates=self.bootstrap_replicates,
            predicted_first_passing_snr=(
                self.predicted_first_passing_snr
            ),
        )


def evaluate_development(cfg: Config):
    return m9.evaluate_development(cfg.core())


def evaluate_holdout(threshold: float, cfg: Config):
    return m9.evaluate_holdout(threshold, cfg.core())


def sha256_file(path: Path) -> str:
    return m9.sha256_file(path)


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
        "m9_dependency_sha256": sha256_file(
            M9_DIR / "arara_m9.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
