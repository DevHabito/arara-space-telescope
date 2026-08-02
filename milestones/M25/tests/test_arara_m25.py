
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m25 as m25


def test_seed_plan_unique():
    cfg = m25.Config()
    plan = m25.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(
            record["seeds"].values()
        )
    assert len(values) == len(set(values))


def test_split_boundaries():
    cfg = m25.Config()
    selection_end, guard, start = (
        m25.split_boundaries(
            np.array([120, 130]),
            cfg,
        )
    )
    assert np.array_equal(
        selection_end,
        np.array([111, 121]),
    )
    assert np.array_equal(
        guard,
        np.array([112, 122]),
    )
    assert np.array_equal(
        start,
        np.array([113, 123]),
    )


def test_selection_and_confirmation_raw_samples_disjoint():
    cfg = m25.Config()
    endpoint = np.array([120])
    selection_end, guard, start = (
        m25.split_boundaries(
            endpoint,
            cfg,
        )
    )
    selection = set(
        range(
            cfg.selection_start,
            int(selection_end[0]) + 1,
        )
    )
    confirmation_raw_dependencies = set(
        range(
            int(start[0]) - 1,
            int(endpoint[0]) + 1,
        )
    )
    assert selection.isdisjoint(
        confirmation_raw_dependencies
    )
    assert int(guard[0]) in (
        confirmation_raw_dependencies
    )


def test_confirmation_score_exact_template():
    cfg = m25.Config()
    endpoint = np.array([120])
    template = np.zeros((1, 180))
    template[0, 113:121] = np.arange(
        1.0, 9.0
    )
    residual = template.copy()
    observed = m25.confirmation_matched_filter(
        residual,
        template,
        endpoint,
        cfg,
    )
    expected = np.sqrt(
        np.sum(np.arange(1.0, 9.0) ** 2)
    )
    assert np.allclose(observed, expected)


def test_split_estimator_uses_only_selection():
    cfg = m25.Config(
        candidate_onset_low=80,
        candidate_onset_high=100,
    )
    endpoint = np.array([120])
    t = np.arange(180)
    residual = np.maximum(
        0.0, t - 91
    )[None, :]
    estimated_1, _ = m25.estimate_onset_split(
        residual,
        endpoint,
        cfg,
    )
    altered = residual.copy()
    altered[:, 113:121] = 1e6
    estimated_2, _ = m25.estimate_onset_split(
        altered,
        endpoint,
        cfg,
    )
    assert np.array_equal(
        estimated_1,
        estimated_2,
    )


def test_threshold_freeze(tmp_path):
    cfg = m25.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(2)
    paths = {}
    for family in m25.NEGATIVE_FAMILIES:
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
    details, table = m25.freeze_threshold(
        cfg,
        paths,
    )
    assert np.isfinite(
        details["threshold"]
    )
    assert np.all(
        table.alerts <= table.allowed
    )


def test_aggregate_strong_fail_from_onset_accuracy():
    cfg = m25.Config(
        holdout_count=3,
        minimum_complete_holdout_passes=2,
        minimum_detection_pass_holdouts=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    holdouts = pd.DataFrame(
        {
            "replication": [0, 1, 2],
            "recall_point": [0.70] * 3,
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
        for stratum in m25.POSITIVE_STRATA:
            rows.append(
                {
                    "replication": replication,
                    "stratum": stratum,
                    "hits": 1750,
                    "n": 2500,
                }
            )
    result = m25.aggregate_results(
        cfg,
        holdouts,
        pd.DataFrame(rows),
        frozen_threshold=4.0,
    )
    assert result["verdict"] == (
        "STRONG_FAIL_SPLIT_SAMPLE_ONSET"
    )
