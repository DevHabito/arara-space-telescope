
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m6 as m6
import arara_m2 as m2


def test_time_at_fraction_linear():
    signal = np.tile(np.linspace(0, 1, 11), (3, 1))
    t = m6.time_at_fraction(signal, 0.5)
    assert np.array_equal(t, np.array([5, 5, 5]))


def test_t50_is_not_before_t25():
    cfg = m6.Config().data_config()
    rng = np.random.default_rng(1)
    data = m2.generate_positive_stratum("power_law", "clean", 100, rng, cfg)
    t50 = m6.time_at_fraction(data.target_signal, 0.5)
    assert np.all(t50 >= data.t25)


def test_positive_evaluation_returns_valid_segments():
    cfg = m6.Config()
    data, tf, scores = m6._evaluate_positive(
        "linear", "clean", 30, np.random.default_rng(2), cfg
    )
    assert np.all(tf >= data.onset)
    assert np.isfinite(scores).all()


def test_negative_virtual_segments_are_valid():
    cfg = m6.Config()
    _, onset, tf, scores = m6._evaluate_negative(
        "quiet", 30, np.random.default_rng(3), cfg
    )
    assert np.all(tf >= onset)
    assert np.isfinite(scores).all()


def test_only_fraction_changes_vs_m5_operator():
    cfg = m6.Config()
    data_cfg = cfg.data_config()
    rng = np.random.default_rng(4)
    data = m2.generate_positive_stratum(
        "logistic", "concurrent", 20, rng, data_cfg
    )
    t50 = m6.time_at_fraction(data.target_signal, cfg.target_fraction)
    assert np.all(t50 >= data.t25)


def test_float32_threshold_contract():
    maxima = {"x": np.array([5,5,5,4,3,2,1], dtype=np.float32)}
    threshold, _, allowed = m2.conservative_threshold(maxima, 2/7)
    assert int(np.sum(maxima["x"] >= threshold)) <= allowed["x"]
