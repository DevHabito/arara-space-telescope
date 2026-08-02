
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m35 as m35


def test_only_latency_identity_and_seeds_change():
    cfg = m35.Config()
    parent = m35.m34.Config()

    assert cfg.version == "35.0"
    assert cfg.primary_latency == 4
    assert parent.primary_latency == 0
    assert np.array_equal(
        cfg.endpoint_grid,
        parent.endpoint_grid,
    )
    assert cfg.window_length == parent.window_length
    assert cfg.methods == parent.methods
    assert (
        cfg.calibration_negatives_per_family
        == parent.calibration_negatives_per_family
    )
    assert cfg.calibration_seed != parent.calibration_seed
    assert cfg.holdout_root_seed != parent.holdout_root_seed


def test_mathematical_functions_are_imported():
    assert (
        m35.estimate_onset_grid
        is m35.m34.estimate_onset_grid
    )
    assert (
        m35.rolling_hinge_score_grid
        is m35.m34.rolling_hinge_score_grid
    )
    assert (
        m35.evaluate_holdout
        is m35.m34.evaluate_holdout
    )


def test_seed_plan_unique():
    cfg = m35.Config()
    plan = m35.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def _mock_frames(
    cfg: m35.Config,
    exact_recall: float,
    rolling_recall: float,
    rolling_pass: bool,
):
    method_rows = []
    stratum_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            (
                "hinge_exact_t50",
                exact_recall,
                True,
            ),
            (
                "rolling_hinge_first_crossing",
                rolling_recall,
                rolling_pass,
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
            hits = int(round(recall * 2500))
            for stratum in m35.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        exact_hits = int(round(exact_recall * 2500))
        rolling_hits = int(round(rolling_recall * 2500))
        both = min(exact_hits, rolling_hits)
        for index, stratum in enumerate(
            m35.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2500 - max(
                        exact_hits,
                        rolling_hits,
                    ),
                    "rolling_only": max(
                        rolling_hits - exact_hits,
                        0,
                    ),
                    "exact_only": max(
                        exact_hits - rolling_hits,
                        0,
                    ),
                    "both": both,
                    "n": 2500,
                }
            )

    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(pair_rows),
    )


def test_latency4_pass_label():
    cfg = m35.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
        prediction_rolling_pass_low=2,
        prediction_rolling_pass_high=3,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.77,
        rolling_recall=0.76,
        rolling_pass=True,
    )
    result = m35.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "hinge_exact_t50": 4.1,
            "rolling_hinge_first_crossing": 6.9,
        },
        threshold_drivers={
            "hinge_exact_t50": "shared_ramp",
            "rolling_hinge_first_crossing": "shared_ramp",
        },
    )
    assert result["verdict"] == (
        "PASS_ROLLING_ENDPOINT_LATENCY4"
    )


def test_latency4_strong_fail_label():
    cfg = m35.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.77,
        rolling_recall=0.40,
        rolling_pass=False,
    )
    result = m35.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "hinge_exact_t50": 4.1,
            "rolling_hinge_first_crossing": 6.9,
        },
        threshold_drivers={
            "hinge_exact_t50": "shared_ramp",
            "rolling_hinge_first_crossing": "shared_ramp",
        },
    )
    assert result["verdict"] == (
        "STRONG_FAIL_ROLLING_ENDPOINT_LATENCY4"
    )
