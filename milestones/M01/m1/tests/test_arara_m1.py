
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

from arara_m1 import (
    Config,
    _normalized_logistic,
    causal_normalize,
    clopper_pearson_upper,
    conservative_threshold,
    cusum_score,
    early_hits,
    first_crossing,
    generate_positive_family,
    rolling_slope_t_score,
)


def test_logistic_endpoints():
    x = np.array([[0.0, 1.0]])
    q = np.array([8.0])
    y = _normalized_logistic(x, q)
    assert np.isclose(y[0, 0], 0.0)
    assert np.isclose(y[0, 1], 1.0)


def test_positive_signal_is_zero_through_onset_and_reaches_amplitude():
    cfg = Config()
    data = generate_positive_family("linear", 30, np.random.default_rng(1), cfg)
    for i in range(30):
        assert np.allclose(data.signal[i, : data.onset[i] + 1], 0.0)
        assert np.isclose(data.signal[i, -1], data.signal[i].max())
        assert data.t25[i] >= data.onset[i]


def test_normalization_does_not_use_future():
    cfg = Config()
    rng = np.random.default_rng(2)
    y = rng.normal(size=(4, cfg.n_time))
    z1, mu1, phi1 = causal_normalize(y, cfg)
    y2 = y.copy()
    y2[:, cfg.baseline_n:] += 10_000.0
    z2, mu2, phi2 = causal_normalize(y2, cfg)
    assert np.allclose(mu1, mu2)
    assert np.allclose(phi1, phi2)
    assert np.allclose(z1[:, :cfg.baseline_n], z2[:, :cfg.baseline_n])


def test_rolling_detector_is_causal():
    rng = np.random.default_rng(3)
    z = rng.normal(size=(2, 100))
    s1 = rolling_slope_t_score(z, (8, 16, 32))
    z2 = z.copy()
    z2[:, 80:] += 1000
    s2 = rolling_slope_t_score(z2, (8, 16, 32))
    assert np.allclose(s1[:, :80], s2[:, :80])


def test_first_crossing_not_argmax():
    scores = np.array([[0, 0, 2, 3, 10]], dtype=float)
    first = first_crossing(scores, 2.0, 0)
    assert first[0] == 2


def test_early_hit_rejects_pre_onset_alarm():
    scores = np.array([[0, 5, 0, 6, 0]], dtype=float)
    hit, first = early_hits(
        scores,
        threshold=4,
        onset=np.array([3]),
        t25=np.array([4]),
        start=0,
    )
    assert first[0] == 1
    assert not hit[0]


def test_conservative_threshold_respects_allowed_count_with_ties():
    maxima = {"x": np.array([5, 5, 5, 4, 3, 2, 1], dtype=float)}
    threshold, _, allowed = conservative_threshold(maxima, target_fpr=2/7)
    alerts = int(np.sum(maxima["x"] >= threshold))
    assert allowed["x"] == 2
    assert alerts <= 2


def test_cusum_known_recurrence():
    z = np.array([[0.0, 1.0, 1.0, -1.0, 2.0]])
    score = cusum_score(z, 0.5)
    expected = np.array([[0.0, 0.5, 1.0, 0.0, 1.5]])
    assert np.allclose(score, expected)


def test_clopper_pearson_boundaries():
    assert 0 < clopper_pearson_upper(0, 100) < 0.1
    assert clopper_pearson_upper(100, 100) == 1.0


def test_m1_positive_slope_scores_above_flat():
    flat = np.zeros((10, 80))
    rise = np.tile(np.linspace(0, 10, 80), (10, 1))
    s_flat = rolling_slope_t_score(flat, (8, 16, 32))
    s_rise = rolling_slope_t_score(rise, (8, 16, 32))
    assert np.nanmax(s_rise) > np.nanmax(s_flat)


def test_conservative_threshold_float32_precision():
    maxima = {"x": np.array([5, 5, 5, 4, 3, 2, 1], dtype=np.float32)}
    threshold, _, allowed = conservative_threshold(maxima, target_fpr=2/7)
    alerts = int(np.sum(maxima["x"] >= threshold))
    assert allowed["x"] == 2
    assert alerts <= 2
