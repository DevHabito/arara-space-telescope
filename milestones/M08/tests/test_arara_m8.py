
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m8 as m8
import arara_m2 as m2


def test_default_fraction_is_one():
    assert m8.Config().target_fraction == 1.0


def test_time_at_full_amplitude_linear():
    signal = np.tile(np.linspace(0, 1, 21), (3, 1))
    t = m8.time_at_fraction(signal, 1.0)
    assert np.array_equal(t, np.array([20, 20, 20]))


def test_t100_not_before_t75():
    cfg = m8.Config().data_config()
    rng = np.random.default_rng(1)
    data = m2.generate_positive_stratum("exponential", "clean", 100, rng, cfg)
    t75 = m8.time_at_fraction(data.target_signal, 0.75)
    t100 = m8.time_at_fraction(data.target_signal, 1.0)
    assert np.all(t100 >= t75)


def test_positive_evaluation_valid():
    cfg = m8.Config()
    data, tf, scores = m8._evaluate_positive(
        "logistic", "concurrent", 40, np.random.default_rng(2), cfg
    )
    assert np.all(tf >= data.onset)
    assert np.isfinite(scores).all()


def test_negative_virtual_segments_valid():
    cfg = m8.Config()
    _, onset, tf, scores = m8._evaluate_negative(
        "shared_ramp", 40, np.random.default_rng(3), cfg
    )
    assert np.all(tf >= onset)
    assert np.isfinite(scores).all()


def test_float32_threshold_contract():
    maxima = {"x": np.array([5,5,5,4,3,2,1], dtype=np.float32)}
    threshold, _, allowed = m2.conservative_threshold(maxima, 2/7)
    assert int(np.sum(maxima["x"] >= threshold)) <= allowed["x"]
