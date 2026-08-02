from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m26 as m26


def test_seed_plan_unique():
    cfg = m26.Config()
    plan = m26.build_seed_plan(cfg)
    values = [x["integer_seed"] for x in plan["calibration"].values()]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_confirmation_geometry_matches_m25():
    cfg = m26.Config()
    endpoint = np.array([120])
    selection_end, guard, start = m26.m25.split_boundaries(endpoint, cfg)
    assert int(selection_end[0]) == 111
    assert int(guard[0]) == 112
    assert int(start[0]) == 113


def test_exact_positive_score_matches_direct_operator():
    cfg = m26.Config()
    record = m26.build_seed_plan(cfg)["holdouts"][0]
    core = cfg.analysis_config().core_config(record)
    panel = m26.m22.m9.generate_positive_panel(
        "linear", "clean", 20, np.random.default_rng(1), core
    )
    observed = m26.evaluate_positive_panel(panel, cfg, core)
    raw = cfg.fixed_snr * panel.stationary_target_sd[:, None] * panel.shape_values
    y = panel.base_y.copy()
    y[:, 0, :] += raw
    residual, processed, _ = m26.m22.m5.sbw_with_signal_operator(
        y, raw, core.data_config()
    )
    expected = m26.m25.confirmation_matched_filter(
        residual, processed, panel.t100, cfg
    )
    assert np.allclose(observed, expected)


def test_threshold_freeze(tmp_path):
    cfg = m26.Config(calibration_negatives_per_family=2000)
    rng = np.random.default_rng(2)
    paths = {}
    for family in m26.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score=rng.normal(size=2000).astype(np.float32),
            endpoint=np.full(2000, 100, dtype=np.int16),
        )
        paths[family] = path
    details, table = m26.freeze_threshold(cfg, paths)
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
        for stratum in m26.POSITIVE_STRATA:
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
    cfg = m26.Config(bootstrap_replicates=1000)
    holdouts, strata = _mock(cfg, 5, 0.62)
    result = m26.aggregate_results(cfg, holdouts, strata, 16.0)
    assert result["verdict"] == "INCONCLUSIVE"


def test_strong_fail_logic():
    cfg = m26.Config(bootstrap_replicates=1000)
    holdouts, strata = _mock(cfg, 0, 0.50)
    result = m26.aggregate_results(cfg, holdouts, strata, 16.0)
    assert result["verdict"] == "STRONG_FAIL_EXACT_ONSET_SPLIT_CONFIRMATION"
