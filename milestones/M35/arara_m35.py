
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEPENDENCY_DIR = ROOT / "dependency"
for directory in (DEPENDENCY_DIR, ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import arara_m34_dependency as m34


POSITIVE_STRATA = m34.POSITIVE_STRATA
NEGATIVE_FAMILIES = m34.NEGATIVE_FAMILIES
METHODS = m34.METHODS


@dataclass(frozen=True)
class Config(m34.Config):
    version: str = "35.0"

    # The only scientific change from M34:
    # success is allowed through t50 + 4.
    primary_latency: int = 4
    secondary_latency: int = 4

    calibration_seed: int = 2026083001
    holdout_root_seed: int = 2026083002
    aggregate_bootstrap_root_seed: int = 2026083003
    paired_difference_bootstrap_seed: int = 2026083004

    prediction_exact_range: tuple[float, float] = (
        0.74,
        0.80,
    )
    prediction_rolling_range: tuple[float, float] = (
        0.73,
        0.79,
    )
    prediction_delta_range: tuple[float, float] = (
        -0.08,
        0.01,
    )
    prediction_rolling_pass_low: int = 8
    prediction_rolling_pass_high: int = 10
    prediction_threshold_range: tuple[float, float] = (
        6.3,
        7.6,
    )


build_seed_plan = m34.build_seed_plan
calibration_core = m34.calibration_core
estimate_onset_grid = m34.estimate_onset_grid
fixed_endpoint_windows = m34.fixed_endpoint_windows
variable_endpoint_windows = m34.variable_endpoint_windows
processed_template_grid_windows = (
    m34.processed_template_grid_windows
)
processed_template_variable_window = (
    m34.processed_template_variable_window
)
projected_window_score = m34.projected_window_score
exact_hinge_score = m34.exact_hinge_score
rolling_hinge_score_grid = m34.rolling_hinge_score_grid
evaluate_positive_panel = m34.evaluate_positive_panel
evaluate_negative_family = m34.evaluate_negative_family
generate_calibration_family = m34.generate_calibration_family
freeze_thresholds = m34.freeze_thresholds
evaluate_holdout = m34.evaluate_holdout
sha256_file = m34.sha256_file


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    result = m34.aggregate_results(
        cfg,
        method_summary,
        stratum_summary,
        pair_counts,
        thresholds,
        threshold_drivers,
    )

    parent_verdict = result["verdict"]
    if parent_verdict == (
        "INVALID_M34_EXACT_ENDPOINT_CONTROL"
    ):
        verdict = "INVALID_M35_EXACT_ENDPOINT_CONTROL"
    elif parent_verdict == (
        "PASS_ROLLING_CAUSAL_ENDPOINT_CANDIDATE"
    ):
        verdict = "PASS_ROLLING_ENDPOINT_LATENCY4"
    elif parent_verdict == (
        "STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT"
    ):
        verdict = "STRONG_FAIL_ROLLING_ENDPOINT_LATENCY4"
    else:
        verdict = "INCONCLUSIVE_ROLLING_ENDPOINT_LATENCY4"

    exact = result["method_details"]["hinge_exact_t50"]
    rolling = result["method_details"][
        "rolling_hinge_first_crossing"
    ]
    delta = result["paired_difference"][
        "rolling_minus_exact_point"
    ]

    prediction = {
        "exact_recall_in_range": bool(
            cfg.prediction_exact_range[0]
            <= exact["aggregate_recall_point"]
            <= cfg.prediction_exact_range[1]
        ),
        "rolling_recall_in_range": bool(
            cfg.prediction_rolling_range[0]
            <= rolling["aggregate_recall_point"]
            <= cfg.prediction_rolling_range[1]
        ),
        "delta_in_range": bool(
            cfg.prediction_delta_range[0]
            <= delta
            <= cfg.prediction_delta_range[1]
        ),
        "control_valid": bool(
            result["control_valid"]
        ),
        "both_fpr_robust": bool(
            exact["fpr_robust"]
            and rolling["fpr_robust"]
        ),
        "rolling_pass_count_in_range": bool(
            cfg.prediction_rolling_pass_low
            <= rolling["holdout_pass_count"]
            <= cfg.prediction_rolling_pass_high
        ),
        "rolling_threshold_in_range": bool(
            cfg.prediction_threshold_range[0]
            <= rolling["threshold"]
            <= cfg.prediction_threshold_range[1]
        ),
        "overall_verdict_confirmed": bool(
            verdict
            == "PASS_ROLLING_ENDPOINT_LATENCY4"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    result["parent_gate_verdict"] = parent_verdict
    result["verdict"] = verdict
    result["prediction"] = prediction
    return result


def write_environment(path: Path) -> None:
    import scipy
    import sklearn

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m34_dependency_sha256": sha256_file(
            ROOT / "arara_m34_dependency.py"
        ),
        "m33_dependency_sha256": sha256_file(
            ROOT / "arara_m33_dependency.py"
        ),
        "m32_dependency_sha256": sha256_file(
            ROOT / "arara_m32_dependency.py"
        ),
        "m30_dependency_sha256": sha256_file(
            ROOT / "arara_m30_dependency.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
