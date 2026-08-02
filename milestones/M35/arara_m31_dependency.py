
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

import arara_m30_dependency as m30


POSITIVE_STRATA = m30.POSITIVE_STRATA
NEGATIVE_FAMILIES = m30.NEGATIVE_FAMILIES
METHODS = m30.METHODS


@dataclass(frozen=True)
class Config(m30.Config):
    version: str = "31.0"

    calibration_seed: int = 2026082601
    holdout_root_seed: int = 2026082602
    aggregate_bootstrap_root_seed: int = 2026082603
    paired_difference_bootstrap_seed: int = 2026082604

    prediction_baseline_range: tuple[float, float] = (
        0.27,
        0.34,
    )
    prediction_candidate_range: tuple[float, float] = (
        0.75,
        0.85,
    )
    prediction_delta_range: tuple[float, float] = (
        0.43,
        0.55,
    )
    prediction_candidate_pass_low: int = 8
    prediction_candidate_pass_high: int = 10


build_seed_plan = m30.build_seed_plan
calibration_core = m30.calibration_core
reference_projected_score = m30.reference_projected_score
paired_scores_from_processed = m30.paired_scores_from_processed
evaluate_positive_panel = m30.evaluate_positive_panel
evaluate_negative_family = m30.evaluate_negative_family
generate_calibration_family = m30.generate_calibration_family
freeze_thresholds = m30.freeze_thresholds
evaluate_holdout = m30.evaluate_holdout
hierarchical_paired_bootstrap = m30.hierarchical_paired_bootstrap
sha256_file = m30.sha256_file


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    projection_diagnostics: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    result = m30.aggregate_results(
        cfg,
        method_summary,
        stratum_summary,
        pair_counts,
        projection_diagnostics,
        thresholds,
        threshold_drivers,
    )

    discovery_verdict = result["verdict"]
    if discovery_verdict == "PASS_REFERENCE_PROJECTION_CANDIDATE":
        confirmation_verdict = "CONFIRMED_REFERENCE_PROJECTION"
    elif discovery_verdict == "STRONG_FAIL_REFERENCE_PROJECTION":
        confirmation_verdict = (
            "STRONG_FAIL_REFERENCE_PROJECTION_REPLICATION"
        )
    elif discovery_verdict == "INCONCLUSIVE_REFERENCE_PROJECTION":
        confirmation_verdict = (
            "INCONCLUSIVE_REFERENCE_PROJECTION_REPLICATION"
        )
    else:
        confirmation_verdict = discovery_verdict

    baseline = result["method_details"]["baseline8"]
    candidate = result["method_details"]["reference_projected8"]
    paired = result["paired_superiority"]
    diagnostics = result["projection_diagnostics"]

    prediction = {
        "baseline_recall_in_range": bool(
            cfg.prediction_baseline_range[0]
            <= baseline["aggregate_recall_point"]
            <= cfg.prediction_baseline_range[1]
        ),
        "candidate_recall_in_range": bool(
            cfg.prediction_candidate_range[0]
            <= candidate["aggregate_recall_point"]
            <= cfg.prediction_candidate_range[1]
        ),
        "delta_in_range": bool(
            cfg.prediction_delta_range[0]
            <= paired["delta_point"]
            <= cfg.prediction_delta_range[1]
        ),
        "both_fpr_robust": bool(
            baseline["fpr_robust"]
            and candidate["fpr_robust"]
        ),
        "candidate_holdout_passes_in_range": bool(
            cfg.prediction_candidate_pass_low
            <= candidate["holdout_pass_count"]
            <= cfg.prediction_candidate_pass_high
        ),
        "no_template_degeneracy": bool(
            diagnostics[
                "positive_template_degenerate_fraction"
            ]
            == 0.0
        ),
        "overall_verdict_confirmed": bool(
            confirmation_verdict
            == "CONFIRMED_REFERENCE_PROJECTION"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    result["discovery_rule_verdict"] = discovery_verdict
    result["verdict"] = confirmation_verdict
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
        "m30_dependency_sha256": sha256_file(
            ROOT / "arara_m30_dependency.py"
        ),
        "m22_dependency_sha256": sha256_file(
            ROOT / "arara_m22_dependency.py"
        ),
        "m28_dependency_sha256": sha256_file(
            ROOT / "arara_m28_dependency.py"
        ),
        "m29_dependency_sha256": sha256_file(
            ROOT / "arara_m29_dependency.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
