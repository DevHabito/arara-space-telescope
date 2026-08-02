
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m22 as m22


def test_shift_signal_zero_and_boundaries():
    x = np.array([[1.0, 2.0, 3.0, 4.0]])
    assert np.array_equal(
        m22.shift_signal(x, 0), x
    )
    assert np.array_equal(
        m22.shift_signal(x, 2),
        np.array([[0.0, 0.0, 1.0, 2.0]])
    )
    assert np.array_equal(
        m22.shift_signal(x, -2),
        np.array([[3.0, 4.0, 0.0, 0.0]])
    )


def test_operator_matches_sbw_processed_signal():
    cfg = m22.Config()
    seed_record = m22.build_seed_plan(cfg)[0]
    core = cfg.core_config(seed_record)
    rng = np.random.default_rng(1)
    panel = m22.m9.generate_positive_panel(
        "linear", "clean", 20, rng, core
    )
    raw = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    y = panel.base_y.copy()
    y[:, 0, :] += raw
    _, expected, params = (
        m22.m5.sbw_with_signal_operator(
            y, raw, core.data_config()
        )
    )
    observed = m22.apply_signal_operator(
        raw, params
    )
    assert np.allclose(observed, expected)


def test_zero_offset_matches_oracle_score():
    cfg = m22.Config()
    seed_record = m22.build_seed_plan(cfg)[0]
    core = cfg.core_config(seed_record)
    rng = np.random.default_rng(2)
    panel = m22.m9.generate_positive_panel(
        "power_law", "concurrent", 30, rng, core
    )
    observed = m22.score_positive_offsets(
        panel, cfg
    )[0]
    expected, _ = m22.m9.evaluate_positive_panel(
        panel, cfg.fixed_snr, core
    )
    assert np.allclose(observed, expected)


def test_seed_plan_unique():
    cfg = m22.Config()
    plan = m22.build_seed_plan(cfg)
    assert len(plan) == 10
    values = []
    for record in plan:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_overall_pass_requires_both_signs():
    cfg = m22.Config(
        bootstrap_replicates=1000
    )
    rep_rows = []
    stratum_rows = []
    for offset in cfg.onset_offsets:
        for r in range(10):
            passed = (
                offset in (-2, 0, 2)
                and r < 8
            )
            rep_rows.append(
                {
                    "replication": r,
                    "offset": offset,
                    "recall_point": (
                        0.65 if passed else 0.59
                    ),
                    "fpr_pass": True,
                    "maximum_fpr_upper_95": 0.009,
                    "pass": passed,
                }
            )
            for stratum in m22.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": r,
                        "offset": offset,
                        "stratum": stratum,
                        "hits": (
                            1625 if passed else 1475
                        ),
                        "n": 2500,
                    }
                )
    result = m22.aggregate_results(
        cfg,
        pd.DataFrame(rep_rows),
        pd.DataFrame(stratum_rows),
    )
    assert result["verdict"] == (
        "PASS_ONSET_TOLERANCE_PM2"
    )
