from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m27 as m27


def test_seed_plan_unique():
    cfg = m27.Config()
    plan = m27.build_seed_plan(cfg)
    values = [x["integer_seed"] for x in plan["calibration"].values()]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_confirmation_geometry_is_16_cadences():
    cfg = m27.Config()
    endpoint = np.array([120])
    selection_end, guard, start = m27.m25.split_boundaries(endpoint, cfg)
    assert int(selection_end[0]) == 103
    assert int(guard[0]) == 104
    assert int(start[0]) == 105


def test_exact_positive_score_matches_direct_operator():
    cfg = m27.Config()
    record = m27.build_seed_plan(cfg)["holdouts"][0]
    core = cfg.analysis_config().core_config(record)
    panel = m27.m22.m9.generate_positive_panel(
        "linear", "clean", 20, np.random.default_rng(1), core
    )
    observed = m27.evaluate_positive_panel(panel, cfg, core)
    raw = cfg.fixed_snr * panel.stationary_target_sd[:, None] * panel.shape_values
    y = panel.base_y.copy()
    y[:, 0, :] += raw
    residual, processed, _ = m27.m22.m5.sbw_with_signal_operator(
        y, raw, core.data_config()
    )
    expected = m27.m25.confirmation_matched_filter(
        residual, processed, panel.t100, cfg
    )
    assert np.allclose(observed, expected)


def test_threshold_freeze(tmp_path):
    cfg = m27.Config(calibration_negatives_per_family=2000)
    rng = np.random.default_rng(2)
    paths = {}
    for family in m27.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score=rng.normal(size=2000).astype(np.float32),
            endpoint=np.full(2000, 100, dtype=np.int16),
        )
        paths[family] = path
    details, table = m27.freeze_threshold(cfg, paths)
    assert np.isfinite(details["threshold"])
    assert np.all(table.alerts <= table.allowed)


def _mock(cfg, passes, recall):
    holdouts = pd.DataFrame(
        {
            "replication": np.arange(cfg.holdout_count),
            "recall_point": [recall] * cfg.holdout_count,
            "pass": [True] * passes + [False] * (cfg.holdout_count - passes),
            "fpr_pass": [True] * cfg.holdout_count,
            "maximum_fpr_upper_95": [0.009] * cfg.holdout_count,
        }
    )
    rows = []
    hits = int(recall * 2500)
    for r in range(cfg.holdout_count):
        for stratum in m27.POSITIVE_STRATA:
            rows.append(
                {
                    "replication": r,
                    "stratum": stratum,
                    "hits": hits,
                    "n": 2500,
                }
            )
    return holdouts, pd.DataFrame(rows)


def test_inconclusive_logic():
    cfg = m27.Config(bootstrap_replicates=1000)
    holdouts, strata = _mock(cfg, 5, 0.62)
    result = m27.aggregate_results(cfg, holdouts, strata, 23.0)
    assert result["verdict"] == "INCONCLUSIVE"


def test_strong_fail_logic():
    cfg = m27.Config(bootstrap_replicates=1000)
    holdouts, strata = _mock(cfg, 0, 0.50)
    result = m27.aggregate_results(cfg, holdouts, strata, 23.0)
    assert result["verdict"] == "STRONG_FAIL_EXACT_ONSET_16_CONFIRMATION"


def test_confirmation_window_has_sixteen_points():
    cfg = m27.Config()
    endpoint = np.array([120, 130])
    _, _, start = m27.m25.split_boundaries(endpoint, cfg)
    assert np.array_equal(endpoint - start + 1, np.array([16, 16]))
