
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys
from typing import Dict, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEPENDENCY_DIR = ROOT / "dependency"
for directory in (DEPENDENCY_DIR, ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import arara_m37_dependency as m37


SHAPES = m37.SHAPES
DURATIONS = m37.DURATIONS
POSITIVE_STRATA = m37.POSITIVE_STRATA
NEGATIVE_FAMILIES = m37.NEGATIVE_FAMILIES
METHODS = m37.METHODS


@dataclass(frozen=True)
class Config(m37.Config):
    version: str = "37R.0"

    calibration_block_count: int = 4
    calibration_negatives_per_block: int = 50_000
    calibration_negatives_per_family: int = 200_000
    calibration_batch_size: int = 50

    calibration_seed: int = 2026090301
    holdout_root_seed: int = 2026090302
    aggregate_bootstrap_root_seed: int = 2026090303
    paired_difference_bootstrap_seed: int = 2026090304

    prediction_control_threshold_range: tuple[float, float] = (
        7.10,
        7.24,
    )
    prediction_full_threshold_range: tuple[float, float] = (
        7.40,
        7.65,
    )
    prediction_control_range: tuple[float, float] = (
        0.745,
        0.765,
    )
    prediction_full_range: tuple[float, float] = (
        0.725,
        0.750,
    )
    prediction_delta_range: tuple[float, float] = (
        -0.035,
        -0.005,
    )
    prediction_control_pass_low: int = 5
    prediction_control_pass_high: int = 10
    prediction_full_pass_low: int = 2
    prediction_full_pass_high: int = 9

    def __post_init__(self) -> None:
        if (
            self.calibration_block_count
            * self.calibration_negatives_per_block
            != self.calibration_negatives_per_family
        ):
            raise ValueError(
                "Calibration block product does not equal pooled size."
            )
        if (
            self.calibration_negatives_per_block
            % self.calibration_batch_size
            != 0
        ):
            raise ValueError(
                "Block size must be divisible by frozen batch size."
            )


def _seed_record(
    sequence: np.random.SeedSequence,
) -> dict:
    return {
        "integer_seed": int(
            sequence.generate_state(
                1,
                dtype=np.uint32,
            )[0]
        ),
        "entropy": int(sequence.entropy),
        "spawn_key": list(sequence.spawn_key),
    }


def build_seed_plan(
    cfg: Config,
) -> dict:
    calibration_sequences = (
        np.random.SeedSequence(
            cfg.calibration_seed
        ).spawn(
            cfg.calibration_block_count
            * len(NEGATIVE_FAMILIES)
        )
    )

    calibration_blocks = {}
    cursor = 0
    for block in range(
        cfg.calibration_block_count
    ):
        block_record = {}
        for family in NEGATIVE_FAMILIES:
            block_record[family] = (
                _seed_record(
                    calibration_sequences[
                        cursor
                    ]
                )
            )
            cursor += 1
        calibration_blocks[
            str(block)
        ] = block_record

    parent_plan = m37.build_seed_plan(
        cfg
    )
    return {
        "calibration_blocks": (
            calibration_blocks
        ),
        "holdouts": (
            parent_plan["holdouts"]
        ),
    }


def combine_calibration_blocks(
    block_paths: Iterable[Path],
    expected_per_block: int,
    expected_total: int,
) -> dict[str, np.ndarray]:
    paths = list(block_paths)
    if not paths:
        raise ValueError(
            "No calibration blocks supplied."
        )

    keys = None
    collected = {}
    for path in paths:
        with np.load(path) as data:
            current_keys = list(
                data.files
            )
            if keys is None:
                keys = current_keys
                collected = {
                    key: []
                    for key in keys
                }
            if current_keys != keys:
                raise RuntimeError(
                    f"Calibration key mismatch in {path}."
                )
            block_n = len(
                data[keys[0]]
            )
            if (
                block_n
                != expected_per_block
            ):
                raise RuntimeError(
                    f"Wrong block size in {path}: {block_n}."
                )
            for key in keys:
                if (
                    len(data[key])
                    != block_n
                ):
                    raise RuntimeError(
                        f"Length mismatch for {key} in {path}."
                    )
                collected[key].append(
                    data[key].copy()
                )

    output = {
        key: np.concatenate(
            values
        )
        for key, values in (
            collected.items()
        )
    }
    for key, values in output.items():
        if len(values) != expected_total:
            raise RuntimeError(
                f"Wrong pooled size for {key}: {len(values)}."
            )
    return output


# Mathematical identity with M37.
build_duration_templates_for_shape = (
    m37.build_duration_templates_for_shape
)
processed_template_duration_windows = (
    m37.processed_template_duration_windows
)
projected_scores_hypotheses = (
    m37.projected_scores_hypotheses
)
score_duration_shape_bank = (
    m37.score_duration_shape_bank
)
evaluate_positive_panel = (
    m37.evaluate_positive_panel
)
evaluate_negative_family = (
    m37.evaluate_negative_family
)
generate_calibration_family = (
    m37.generate_calibration_family
)
freeze_thresholds = m37.freeze_thresholds
identification_row = m37.identification_row
evaluate_holdout = m37.evaluate_holdout
first_crossing = m37.first_crossing
calibration_core = m37.calibration_core
sha256_file = m37.sha256_file


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    identification_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    result = m37.aggregate_results(
        cfg,
        method_summary,
        stratum_summary,
        identification_summary,
        pair_counts,
        thresholds,
        threshold_drivers,
    )

    parent_verdict = result[
        "verdict"
    ]
    verdict_map = {
        "INVALID_M37_EXACT_DURATION_CONTROL": (
            "INVALID_M37R_EXACT_DURATION_CONTROL"
        ),
        "PASS_FULL_DURATION_BANK_AND_IDENTIFICATION": (
            "PASS_M37R_FULL_DURATION_BANK_AND_IDENTIFICATION"
        ),
        "PASS_DETECTION_DURATION_UNRELIABLE": (
            "PASS_M37R_DETECTION_DURATION_UNRELIABLE"
        ),
        "STRONG_FAIL_FULL_DURATION_BANK": (
            "STRONG_FAIL_M37R_FULL_DURATION_BANK"
        ),
        "INCONCLUSIVE_FULL_DURATION_BANK": (
            "INCONCLUSIVE_M37R_FULL_DURATION_BANK"
        ),
    }
    verdict = verdict_map[
        parent_verdict
    ]

    control = result[
        "method_details"
    ][
        "rolling_four_shape_exact_duration_latency4"
    ]
    full = result[
        "method_details"
    ][
        "rolling_four_shape_full_duration_bank_latency4"
    ]
    delta = result[
        "paired_difference"
    ][
        "full_minus_control_point"
    ]
    duration = result[
        "duration_identification"
    ]

    prediction = {
        "control_threshold_in_range": bool(
            cfg.prediction_control_threshold_range[0]
            <= control["threshold"]
            <= cfg.prediction_control_threshold_range[1]
        ),
        "full_threshold_in_range": bool(
            cfg.prediction_full_threshold_range[0]
            <= full["threshold"]
            <= cfg.prediction_full_threshold_range[1]
        ),
        "control_recall_in_range": bool(
            cfg.prediction_control_range[0]
            <= control[
                "aggregate_recall_point"
            ]
            <= cfg.prediction_control_range[1]
        ),
        "full_recall_in_range": bool(
            cfg.prediction_full_range[0]
            <= full[
                "aggregate_recall_point"
            ]
            <= cfg.prediction_full_range[1]
        ),
        "delta_in_range": bool(
            cfg.prediction_delta_range[0]
            <= delta
            <= cfg.prediction_delta_range[1]
        ),
        "control_pass_count_in_range": bool(
            cfg.prediction_control_pass_low
            <= control[
                "holdout_pass_count"
            ]
            <= cfg.prediction_control_pass_high
        ),
        "full_pass_count_in_range": bool(
            cfg.prediction_full_pass_low
            <= full[
                "holdout_pass_count"
            ]
            <= cfg.prediction_full_pass_high
        ),
        "both_fpr_robust": bool(
            control["fpr_robust"]
            and full["fpr_robust"]
        ),
        "duration_identification_below_gate": bool(
            duration[
                "duration_tolerance2_accuracy_lower_one_sided_95"
            ]
            < cfg.duration_identification_minimum_lower_one_sided_95
        ),
        "overall_verdict_confirmed": bool(
            verdict
            == "INCONCLUSIVE_M37R_FULL_DURATION_BANK"
        ),
    }
    prediction[
        "fully_confirmed"
    ] = bool(
        all(prediction.values())
    )

    result[
        "parent_m37_label"
    ] = parent_verdict
    result["verdict"] = verdict
    result["prediction"] = (
        prediction
    )
    return result


def write_environment(
    path: Path,
) -> None:
    import scipy
    import sklearn

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m37_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m37_dependency.py"
            )
        ),
        "m36_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m36_dependency.py"
            )
        ),
        "m32_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m32_dependency.py"
            )
        ),
    }
    path.write_text(
        json.dumps(
            environment,
            indent=2,
        ),
        encoding="utf-8",
    )
