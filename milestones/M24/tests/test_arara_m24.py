
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m24 as m24


def test_seed_plan_unique():
    cfg = m24.Config()
    plan = m24.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_shift_rows():
    x = np.array([
        [1.0, 2.0, 3.0, 4.0],
        [1.0, 2.0, 3.0, 4.0],
    ])
    observed = m24.shift_rows(
        x, np.array([1, -1])
    )
    expected = np.array([
        [0.0, 1.0, 2.0, 3.0],
        [2.0, 3.0, 4.0, 0.0],
    ])
    assert np.array_equal(observed, expected)


def test_hinge_estimator_recovers_exact_hinge():
    cfg = m24.Config(
        candidate_onset_low=80,
        candidate_onset_high=100,
    )
    t = np.arange(180)
    true_onset = 91
    residual = np.maximum(
        0.0, t - true_onset
    )[None, :]
    estimated, score = m24.estimate_onset_hinge(
        residual,
        np.array([120]),
        cfg,
    )
    assert int(estimated[0]) == true_onset
    assert np.isinf(score[0])


def test_hinge_zero_tie_uses_first_candidate():
    cfg = m24.Config(
        candidate_onset_low=70,
        candidate_onset_high=75,
    )
    estimated, score = m24.estimate_onset_hinge(
        np.zeros((2, 180)),
        np.array([100, 110]),
        cfg,
    )
    assert np.array_equal(
        estimated, np.array([70, 70])
    )


def test_threshold_freeze(tmp_path):
    cfg = m24.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(1)
    paths = {}
    for family in m24.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score=rng.normal(
                size=2_000
            ).astype(np.float32),
            estimated_onset=np.full(
                2_000, 80, dtype=np.int16
            ),
            endpoint=np.full(
                2_000, 100, dtype=np.int16
            ),
        )
        paths[family] = path
    details, table = m24.freeze_threshold(
        cfg, paths
    )
    assert np.isfinite(details["threshold"])
    assert np.all(table.alerts <= table.allowed)


def test_aggregate_strong_fail_from_onset_accuracy():
    cfg = m24.Config(
        holdout_count=3,
        minimum_complete_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    holdouts = pd.DataFrame(
        {
            "replication": [0, 1, 2],
            "recall_point": [0.65] * 3,
            "pass": [False] * 3,
            "detection_pass": [True] * 3,
            "onset_pass": [False] * 3,
            "fpr_pass": [True] * 3,
            "maximum_fpr_upper_95": [0.009] * 3,
            "detected_for_onset": [1000] * 3,
            "onset_in_envelope": [400] * 3,
            "early_below_minus2": [300] * 3,
            "late_above_plus1": [300] * 3,
        }
    )
    rows = []
    for replication in range(3):
        for stratum in m24.POSITIVE_STRATA:
            rows.append(
                {
                    "replication": replication,
                    "stratum": stratum,
                    "hits": 1625,
                    "n": 2500,
                }
            )
    result = m24.aggregate_results(
        cfg, holdouts, pd.DataFrame(rows)
    )
    assert result["verdict"] == (
        "STRONG_FAIL_CAUSAL_ONSET_ESTIMATOR"
    )
