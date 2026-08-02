
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m15 as m15


def test_seed_plan_has_ten_unique_replications():
    cfg = m15.Config()
    plan = m15.build_seed_plan(cfg)
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


def test_core_is_fixed_at_12_and_t50():
    cfg = m15.Config()
    seed_record = m15.build_seed_plan(cfg)[0]
    core = m15.core_config(cfg, seed_record)
    assert core.snr_levels == (12.0,)
    assert core.target_fraction == 0.50


def test_hierarchical_bootstrap_tracks_point():
    counts = np.full((10, 8), 1500)
    ns = np.full((10, 8), 2500)
    boot = m15.hierarchical_bootstrap(
        counts, ns, 2000, 123
    )
    assert abs(boot.mean() - 0.60) < 0.005


def test_aggregate_pass_logic():
    cfg = m15.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.63] * 10,
            "pass": [True] * 8 + [False] * 2,
            "fpr_pass": [True] * 10,
            "maximum_fpr_upper_95": [0.009] * 10,
        }
    )
    counts = np.full((10, 8), 1575)
    ns = np.full((10, 8), 2500)
    result = m15.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "PASS"


def test_extreme_fpr_forces_strong_failure():
    cfg = m15.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.63] * 10,
            "pass": [True] * 10,
            "fpr_pass": [True] * 9 + [False],
            "maximum_fpr_upper_95": (
                [0.009] * 9 + [0.016]
            ),
        }
    )
    counts = np.full((10, 8), 1575)
    ns = np.full((10, 8), 2500)
    result = m15.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "STRONG_FAIL"
