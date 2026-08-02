
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m16 as m16
import arara_m2 as m2


def test_seed_plan_is_unique_and_complete():
    cfg = m16.Config()
    plan = m16.build_seed_plan(cfg)
    assert len(plan) == 3

    all_seeds = []
    for world in plan:
        all_seeds.append(
            world["holdout"]["integer_seed"]
        )
        for family in m16.NEGATIVE_FAMILIES:
            all_seeds.append(
                world["calibration_families"][
                    family
                ]["integer_seed"]
            )
        for size in cfg.calibration_sizes:
            all_seeds.append(
                world["sizes"][str(size)][
                    "resampling"
                ]["integer_seed"]
            )
            all_seeds.append(
                world["sizes"][str(size)][
                    "recall_bootstrap"
                ]["integer_seed"]
            )
    assert len(all_seeds) == len(set(all_seeds))


def test_partition_threshold_matches_reference():
    rng = np.random.default_rng(1)
    samples = {
        family: rng.normal(
            size=2_000
        ).astype(np.float32)
        for family in m16.NEGATIVE_FAMILIES
    }
    observed = (
        m16.conservative_threshold_partition(
            samples, 0.005
        )
    )
    expected = m2.conservative_threshold(
        samples, 0.005
    )
    assert observed[0] == expected[0]
    assert observed[1] == expected[1]
    assert observed[2] == expected[2]


def test_holdout_evaluation_perfect_separation_passes():
    cfg = m16.Config(
        bootstrap_replicates_per_calibration=2_000
    )
    positive_scores = {
        stratum: np.full(2_500, 10.0)
        for stratum in m16.POSITIVE_STRATA
    }
    positive_batches = {
        stratum: np.repeat(
            np.arange(20), 125
        ).astype(np.int16)
        for stratum in m16.POSITIVE_STRATA
    }
    negative_scores = {
        family: np.zeros(5_000)
        for family in m16.NEGATIVE_FAMILIES
    }
    result = m16.evaluate_threshold(
        5.0,
        {
            "positive_scores": positive_scores,
            "positive_batches": positive_batches,
            "negative_scores": negative_scores,
        },
        cfg,
        123,
    )
    assert result["pass"]
    assert result["good_strata"] == 8
    assert result["good_batches"] == 20


def test_holdout_evaluation_low_recall_fails():
    cfg = m16.Config(
        bootstrap_replicates_per_calibration=2_000
    )
    positive_scores = {
        stratum: np.zeros(2_500)
        for stratum in m16.POSITIVE_STRATA
    }
    positive_batches = {
        stratum: np.repeat(
            np.arange(20), 125
        ).astype(np.int16)
        for stratum in m16.POSITIVE_STRATA
    }
    negative_scores = {
        family: np.zeros(5_000)
        for family in m16.NEGATIVE_FAMILIES
    }
    result = m16.evaluate_threshold(
        5.0,
        {
            "positive_scores": positive_scores,
            "positive_batches": positive_batches,
            "negative_scores": negative_scores,
        },
        cfg,
        123,
    )
    assert not result["pass"]
    assert result["recall_point"] == 0.0


def test_summary_strong_fail_logic():
    cfg = m16.Config()
    rows = []
    widths = {
        2_000: 1.0,
        10_000: 0.5,
        50_000: 0.2,
    }
    for world in range(3):
        for size in cfg.calibration_sizes:
            center = 7.0
            for resample in range(100):
                offset = (
                    (resample - 49.5) / 99.0
                    * widths[size]
                )
                rows.append(
                    {
                        "world": world,
                        "calibration_size": size,
                        "resample": resample,
                        "threshold": center + offset,
                        "threshold_driver": "quiet",
                        "fpr_control": True,
                        "recall_point": 0.53,
                        "recall_lower_95": 0.52,
                        "recall_upper_95": 0.54,
                        "good_strata": 4,
                        "good_batches": 2,
                        "pass": False,
                    }
                )
    summary, verdict = m16.summarize_results(
        cfg, pd.DataFrame(rows)
    )
    assert verdict["verdict"] == (
        "STRONG_FAIL_CALIBRATION_NOT_PRIMARY"
    )
