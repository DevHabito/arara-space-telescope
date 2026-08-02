
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m21 as m21


def test_fixed_condition():
    cfg = m21.Config()
    assert cfg.fixed_snr == 13.75
    assert cfg.target_fraction == 0.50


def test_seed_plan_has_ten_unique_replications():
    cfg = m21.Config()
    plan = m21.build_seed_plan(cfg)
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


def test_core_uses_same_candidate_level():
    cfg = m21.Config()
    seed_record = m21.build_seed_plan(cfg)[0]
    core = m21.core_config(cfg, seed_record)
    assert core.snr_levels == (13.75,)
    assert core.target_fraction == 0.50


def test_numeric_pass_becomes_confirmatory():
    cfg = m21.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.66] * 10,
            "pass": [True] * 8 + [False] * 2,
            "fpr_pass": [True] * 10,
            "maximum_fpr_upper_95": [0.009] * 10,
        }
    )
    counts = np.full((10, 8), 1650)
    ns = np.full((10, 8), 2500)
    result = m21.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["numeric_verdict"] == "PASS"
    assert result["verdict"] == "PASS_CONFIRMATORY"


def test_seven_passes_are_inconclusive():
    cfg = m21.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.66] * 10,
            "pass": [True] * 7 + [False] * 3,
            "fpr_pass": [True] * 10,
            "maximum_fpr_upper_95": [0.009] * 10,
        }
    )
    counts = np.full((10, 8), 1650)
    ns = np.full((10, 8), 2500)
    result = m21.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "INCONCLUSIVE"


def test_extreme_fpr_forces_failure():
    cfg = m21.Config()
    summary = pd.DataFrame(
        {
            "recall_point": [0.66] * 10,
            "pass": [True] * 10,
            "fpr_pass": [True] * 9 + [False],
            "maximum_fpr_upper_95": (
                [0.009] * 9 + [0.016]
            ),
        }
    )
    counts = np.full((10, 8), 1650)
    ns = np.full((10, 8), 2500)
    result = m21.aggregate_results(
        cfg, summary, counts, ns
    )
    assert result["verdict"] == "STRONG_FAIL"
