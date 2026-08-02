
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m18 as m18


def test_fixed_condition():
    cfg = m18.Config()
    assert cfg.fixed_snr == 13.0
    assert cfg.target_fraction == 0.50


def test_seed_plan_has_ten_unique_replications():
    cfg = m18.Config()
    plan = m18.build_seed_plan(cfg)
    assert len(plan) == 10
    development = [
        item["seeds"]["development"] for item in plan
    ]
    holdout = [
        item["seeds"]["holdout"] for item in plan
    ]
    assert len(set(development)) == 10
    assert len(set(holdout)) == 10
    assert set(development).isdisjoint(set(holdout))


def test_core_uses_13_sigma():
    cfg = m18.Config()
    seed_record = m18.build_seed_plan(cfg)[0]
    core = m18.core_config(cfg, seed_record)
    assert core.snr_levels == (13.0,)
    assert core.target_fraction == 0.50


def test_inconclusive_prediction_logic():
    cfg = m18.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.59] * 10,
            "pass": [True] * 5 + [False] * 5,
            "fpr_pass": [True] * 10,
            "maximum_fpr_upper_95": [0.009] * 10,
        }
    )
    counts = np.full((10, 8), 1475)
    ns = np.full((10, 8), 2500)
    result = m18.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "STRONG_FAIL"
    # Upper CI is expected to remain <= 0.60 in this constructed case.
    assert result["prediction"]["pass_count_confirmed"]


def test_pass_logic_remains_eight_of_ten():
    cfg = m18.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.64] * 10,
            "pass": [True] * 8 + [False] * 2,
            "fpr_pass": [True] * 10,
            "maximum_fpr_upper_95": [0.009] * 10,
        }
    )
    counts = np.full((10, 8), 1600)
    ns = np.full((10, 8), 2500)
    result = m18.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "PASS"


def test_extreme_fpr_forces_failure():
    cfg = m18.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.64] * 10,
            "pass": [True] * 10,
            "fpr_pass": [True] * 9 + [False],
            "maximum_fpr_upper_95": (
                [0.009] * 9 + [0.016]
            ),
        }
    )
    counts = np.full((10, 8), 1600)
    ns = np.full((10, 8), 2500)
    result = m18.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "STRONG_FAIL"
