
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
M15_DIR = ROOT / "m15"
if str(M15_DIR) not in sys.path:
    sys.path.insert(0, str(M15_DIR))

import arara_m15 as m15


@dataclass(frozen=True)
class Config:
    version: str = "20.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    replication_count: int = 10
    replication_root_seed: int = 2026081501
    aggregate_bootstrap_seed: int = 2026081502

    development_base_fields_per_shape_context: int = 1000
    development_negatives_per_family: int = 2000
    holdout_positive_per_stratum_total: int = 2500
    holdout_negative_per_family_total: int = 5000
    holdout_batches: int = 20
    holdout_positive_per_stratum_per_batch: int = 125
    holdout_negative_per_family_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    extreme_fpr_upper_limit: float = 0.015
    minimum_replication_passes: int = 8
    minimum_fpr_pass_replications: int = 9
    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    bootstrap_replicates: int = 10_000

    prediction_pass_count_low: int = 8
    prediction_pass_count_high: int = 10
    prediction_recall_low: float = 0.645
    prediction_recall_high: float = 0.675
    prediction_verdict: str = "PASS_REFINEMENT_CANDIDATE"


def build_seed_plan(cfg: Config):
    return m15.build_seed_plan(cfg)


def core_config(cfg: Config, seed_record: dict):
    return m15.core_config(cfg, seed_record)


def run_replication(cfg: Config, seed_record: dict):
    return m15.run_replication(cfg, seed_record)


def hierarchical_bootstrap(
    replication_stratum_counts,
    replication_stratum_ns,
    replicates,
    seed,
):
    return m15.hierarchical_bootstrap(
        replication_stratum_counts,
        replication_stratum_ns,
        replicates,
        seed,
    )


def aggregate_results(
    cfg: Config,
    replication_summaries,
    stratum_counts,
    stratum_ns,
):
    raw = m15.aggregate_results(
        cfg,
        replication_summaries,
        stratum_counts,
        stratum_ns,
    )
    bootstrap = raw.pop("bootstrap")
    numeric_verdict = raw["verdict"]
    scientific_verdict = (
        "PASS_REFINEMENT_CANDIDATE"
        if numeric_verdict == "PASS"
        else numeric_verdict
    )

    scientific = {
        "verdict": scientific_verdict,
        "numeric_verdict": numeric_verdict,
        "aggregate_recall_point": raw[
            "aggregate_recall_point"
        ],
        "aggregate_recall_lower_95": raw[
            "aggregate_recall_lower_95"
        ],
        "aggregate_recall_upper_95": raw[
            "aggregate_recall_upper_95"
        ],
        "replication_pass_count": raw[
            "replication_pass_count"
        ],
        "fpr_pass_replication_count": raw[
            "fpr_pass_replication_count"
        ],
        "extreme_fpr_violation": raw[
            "extreme_fpr_violation"
        ],
        "fpr_robust": raw["fpr_robust"],
        "minimum_replication_passes": raw[
            "minimum_replication_passes"
        ],
        "requires_independent_confirmation": (
            scientific_verdict
            == "PASS_REFINEMENT_CANDIDATE"
        ),
    }

    prediction = {
        "pass_count_confirmed": bool(
            cfg.prediction_pass_count_low
            <= scientific["replication_pass_count"]
            <= cfg.prediction_pass_count_high
        ),
        "aggregate_recall_confirmed": bool(
            cfg.prediction_recall_low
            <= scientific["aggregate_recall_point"]
            <= cfg.prediction_recall_high
        ),
        "verdict_confirmed": bool(
            scientific["verdict"]
            == cfg.prediction_verdict
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )
    scientific["prediction"] = prediction
    scientific["bootstrap"] = bootstrap
    return scientific


def sha256_file(path: Path) -> str:
    return m15.sha256_file(path)


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
        "m15_dependency_sha256": sha256_file(
            M15_DIR / "arara_m15.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
