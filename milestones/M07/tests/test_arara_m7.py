
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m7 as m7
import arara_m2 as m2


def test_default_fraction_is_075():
    assert m7.Config().target_fraction == 0.75


def test_time_at_fraction_linear():
    signal = np.tile(np.linspace(0, 1, 21), (3, 1))
    t = m7.time_at_fraction(signal, 0.75)
    assert np.array_equal(t, np.array([15, 15, 15]))


def test_t75_not_before_t50_or_t25():
    cfg = m7.Config().data_config()
    rng = np.random.default_rng(1)
    data = m2.generate_positive_stratum("power_law", "clean", 100, rng, cfg)
    t50 = m7.time_at_fraction(data.target_signal, 0.50)
    t75 = m7.time_at_fraction(data.target_signal, 0.75)
    assert np.all(t75 >= t50)
    assert np.all(t50 >= data.t25)


def test_positive_evaluation_segments_valid():
    cfg = m7.Config()
    data, tf, scores = m7._evaluate_positive(
        "linear", "clean", 40, np.random.default_rng(2), cfg
    )
    assert np.all(tf >= data.onset)
    assert np.isfinite(scores).all()


def test_negative_virtual_segments_valid():
    cfg = m7.Config()
    _, onset, tf, scores = m7._evaluate_negative(
        "shared_bump", 40, np.random.default_rng(3), cfg
    )
    assert np.all(tf >= onset)
    assert np.isfinite(scores).all()


def test_float32_threshold_contract():
    maxima = {"x": np.array([5,5,5,4,3,2,1], dtype=np.float32)}
    threshold, _, allowed = m2.conservative_threshold(maxima, 2/7)
    assert int(np.sum(maxima["x"] >= threshold)) <= allowed["x"]
