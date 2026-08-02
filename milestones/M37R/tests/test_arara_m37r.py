
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m37r as m37r


def test_protocol_counts():
    cfg = m37r.Config()
    assert cfg.calibration_block_count == 4
    assert cfg.calibration_negatives_per_block == 50_000
    assert cfg.calibration_negatives_per_family == 200_000
    assert (
        cfg.calibration_block_count
        * cfg.calibration_negatives_per_block
        == cfg.calibration_negatives_per_family
    )
    assert len(m37r.DURATIONS) == 37
    assert (
        len(m37r.DURATIONS)
        * len(m37r.SHAPES)
        * len(cfg.endpoint_grid)
        == 14_652
    )


def test_mathematics_are_imported_by_identity():
    assert (
        m37r.score_duration_shape_bank
        is m37r.m37.score_duration_shape_bank
    )
    assert (
        m37r.evaluate_positive_panel
        is m37r.m37.evaluate_positive_panel
    )
    assert (
        m37r.evaluate_negative_family
        is m37r.m37.evaluate_negative_family
    )
    assert (
        m37r.evaluate_holdout
        is m37r.m37.evaluate_holdout
    )


def test_seed_plan_has_twenty_unique_calibration_seeds():
    cfg = m37r.Config()
    plan = m37r.build_seed_plan(cfg)
    calibration = []
    for block in range(cfg.calibration_block_count):
        for family in m37r.NEGATIVE_FAMILIES:
            calibration.append(
                plan["calibration_blocks"][str(block)][family][
                    "integer_seed"
                ]
            )
    assert len(calibration) == 20
    assert len(set(calibration)) == 20

    holdout_values = []
    for record in plan["holdouts"]:
        holdout_values.extend(record["seeds"].values())
    assert len(holdout_values) == len(set(holdout_values))


def test_combine_calibration_blocks(tmp_path):
    rng = np.random.default_rng(1)
    paths = []
    for block in range(4):
        path = tmp_path / f"block_{block}.npz"
        np.savez_compressed(
            path,
            score_a=rng.normal(size=10),
            score_b=rng.normal(size=10),
            label=np.full(10, block, dtype=np.int8),
        )
        paths.append(path)

    combined = m37r.combine_calibration_blocks(
        paths,
        expected_per_block=10,
        expected_total=40,
    )
    assert len(combined["score_a"]) == 40
    assert np.array_equal(
        combined["label"],
        np.repeat(np.arange(4, dtype=np.int8), 10),
    )


def test_pooled_threshold_counts(tmp_path):
    cfg = m37r.Config(
        calibration_block_count=4,
        calibration_negatives_per_block=500,
        calibration_negatives_per_family=2_000,
    )
    rng = np.random.default_rng(2)
    paths = {}
    for family in m37r.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_rolling_four_shape_exact_duration_latency4=(
                rng.normal(size=2_000).astype(np.float32)
            ),
            score_rolling_four_shape_full_duration_bank_latency4=(
                rng.normal(size=2_000).astype(np.float32)
            ),
            control_argmax_endpoint=rng.integers(
                81, 180, size=2_000, dtype=np.int16
            ),
            full_argmax_endpoint=rng.integers(
                81, 180, size=2_000, dtype=np.int16
            ),
            full_argmax_shape_index=rng.integers(
                0, 4, size=2_000, dtype=np.int8
            ),
            full_argmax_duration=rng.integers(
                24, 61, size=2_000, dtype=np.int16
            ),
            true_shape_index=rng.integers(
                0, 4, size=2_000, dtype=np.int8
            ),
            true_duration=rng.integers(
                24, 61, size=2_000, dtype=np.int16
            ),
            control_energy_at_max=np.ones(2_000, dtype=np.float32),
            full_energy_at_max=np.ones(2_000, dtype=np.float32),
        )
        paths[family] = path

    details, table, diagnostics = m37r.freeze_thresholds(
        cfg,
        paths,
    )
    assert details["calibration_negatives_per_family"] == 2_000
    assert np.all(table["allowed"] == 10)
    assert np.all(table["alerts"] <= table["allowed"])
    assert len(diagnostics) == 5


def _mock_frames(
    cfg,
    control_recall,
    full_recall,
    control_pass,
    full_pass,
    tolerance_accuracy,
):
    method_rows = []
    stratum_rows = []
    identification_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            (
                "rolling_four_shape_exact_duration_latency4",
                control_recall,
                control_pass,
            ),
            (
                "rolling_four_shape_full_duration_bank_latency4",
                full_recall,
                full_pass,
            ),
        ):
            method_rows.append(
                {
                    "replication": replication,
                    "method": method,
                    "recall_point": recall,
                    "pass": passed,
                    "fpr_pass": True,
                    "maximum_fpr_upper_one_sided_95": 0.009,
                    "auroc": 0.99,
                    "average_precision": 0.99,
                }
            )
            hits = int(round(recall * 2_500))
            for stratum in m37r.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2_500,
                    }
                )

        hit_n = int(round(full_recall * 20_000))
        tolerance_correct = int(
            round(tolerance_accuracy * hit_n)
        )
        identification_rows.append(
            {
                "replication": replication,
                "primary_hit_n": hit_n,
                "duration_exact_correct": int(round(0.03 * hit_n)),
                "duration_tolerance2_correct": tolerance_correct,
                "shape_correct": int(round(0.29 * hit_n)),
                "duration_identification_pass": (
                    tolerance_accuracy >= 0.72
                ),
            }
        )

        control_hits = int(round(control_recall * 2_500))
        full_hits = int(round(full_recall * 2_500))
        both = min(control_hits, full_hits)
        for index, stratum in enumerate(m37r.POSITIVE_STRATA):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2_500 - max(control_hits, full_hits),
                    "full_only": max(full_hits - control_hits, 0),
                    "control_only": max(control_hits - full_hits, 0),
                    "both": both,
                    "n": 2_500,
                }
            )

    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(identification_rows),
        pd.DataFrame(pair_rows),
    )


def test_invalid_control_label():
    cfg = m37r.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        control_recall=0.75,
        full_recall=0.74,
        control_pass=False,
        full_pass=True,
        tolerance_accuracy=0.2,
    )
    result = m37r.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_four_shape_exact_duration_latency4": 7.16,
            "rolling_four_shape_full_duration_bank_latency4": 7.50,
        },
        threshold_drivers={
            "rolling_four_shape_exact_duration_latency4": "shared_step",
            "rolling_four_shape_full_duration_bank_latency4": "shared_step",
        },
    )
    assert result["verdict"] == (
        "INVALID_M37R_EXACT_DURATION_CONTROL"
    )


def test_detection_pass_duration_unreliable_label():
    cfg = m37r.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_duration_identification_holdouts=2,
        bootstrap_replicates=1_000,
        prediction_control_pass_low=2,
        prediction_control_pass_high=3,
        prediction_full_pass_low=2,
        prediction_full_pass_high=3,
    )
    frames = _mock_frames(
        cfg,
        control_recall=0.755,
        full_recall=0.74,
        control_pass=True,
        full_pass=True,
        tolerance_accuracy=0.2,
    )
    result = m37r.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_four_shape_exact_duration_latency4": 7.16,
            "rolling_four_shape_full_duration_bank_latency4": 7.50,
        },
        threshold_drivers={
            "rolling_four_shape_exact_duration_latency4": "shared_step",
            "rolling_four_shape_full_duration_bank_latency4": "shared_step",
        },
    )
    assert result["verdict"] == (
        "PASS_M37R_DETECTION_DURATION_UNRELIABLE"
    )
