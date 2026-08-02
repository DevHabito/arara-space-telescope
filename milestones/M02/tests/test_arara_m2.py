
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

from arara_m2 import (
    Config,
    _normalized_logistic,
    conservative_threshold,
    clopper_pearson_upper,
    early_hits,
    first_crossing,
    generate_positive_stratum,
    normalize_field,
    rolling_slope_t_score,
)


def test_logistic_normalization_endpoints():
    x = np.array([[0.0, 1.0]])
    q = np.array([8.0])
    y = _normalized_logistic(x, q)
    assert np.isclose(y[0, 0], 0.0)
    assert np.isclose(y[0, 1], 1.0)


def test_positive_event_only_enters_target():
    cfg = Config()
    data = generate_positive_stratum(
        "linear", "clean", 20, np.random.default_rng(1), cfg
    )
    assert np.allclose(data.target_signal[:, : cfg.onset_low], 0.0)
    assert np.all(data.t25 >= data.onset)
    assert data.y.shape == (20, 1 + cfg.n_references, cfg.n_time)


def test_normalization_is_causal():
    cfg = Config()
    rng = np.random.default_rng(2)
    y = rng.normal(size=(3, 1 + cfg.n_references, cfg.n_time))
    target1, residual1, q1, beta1 = normalize_field(y, cfg)

    y2 = y.copy()
    y2[:, :, cfg.baseline_n:] += 10_000.0
    target2, residual2, q2, beta2 = normalize_field(y2, cfg)

    assert np.allclose(beta1, beta2)
    assert np.allclose(
        target1[:, : cfg.baseline_n],
        target2[:, : cfg.baseline_n],
    )
    assert np.allclose(
        q1[:, : cfg.baseline_n],
        q2[:, : cfg.baseline_n],
    )
    assert np.allclose(
        residual1[:, : cfg.baseline_n],
        residual2[:, : cfg.baseline_n],
    )


def test_reference_median_robust_to_one_extreme_reference():
    cfg = Config()
    rng = np.random.default_rng(3)
    y = rng.normal(size=(1, 1 + cfg.n_references, cfg.n_time))
    _, _, q1, _ = normalize_field(y, cfg)
    y[:, 1, 80] += 1e6
    _, _, q2, _ = normalize_field(y, cfg)
    assert np.isfinite(q2).all()
    assert abs(q2[0, 80] - q1[0, 80]) < 5.0


def test_ideal_common_mode_is_substantially_removed():
    cfg = Config()
    rng = np.random.default_rng(4)
    common = rng.normal(size=(5, cfg.n_time))
    independent = 0.05 * rng.normal(
        size=(5, 1 + cfg.n_references, cfg.n_time)
    )
    y = common[:, None, :] + independent
    target, residual, q, beta = normalize_field(y, cfg)
    assert np.median(np.var(residual, axis=1)) < np.median(
        np.var(target, axis=1)
    )


def test_target_only_event_survives_reference_subtraction():
    cfg = Config()
    rng = np.random.default_rng(5)
    y = rng.normal(
        size=(4, 1 + cfg.n_references, cfg.n_time)
    )
    ramp = np.linspace(0, 8, 60)
    y[:, 0, 100:160] += ramp
    target, residual, q, beta = normalize_field(y, cfg)
    target_change = target[:, 159] - target[:, 99]
    residual_change = residual[:, 159] - residual[:, 99]
    assert np.median(residual_change) > 0.5 * np.median(target_change)


def test_rolling_detector_is_causal():
    rng = np.random.default_rng(6)
    z = rng.normal(size=(2, 100))
    s1 = rolling_slope_t_score(z, (8, 16, 32))
    z2 = z.copy()
    z2[:, 80:] += 1000
    s2 = rolling_slope_t_score(z2, (8, 16, 32))
    assert np.allclose(s1[:, :80], s2[:, :80])


def test_exact_positive_slope_not_zero():
    rise = np.tile(np.linspace(0, 10, 80), (3, 1))
    score = rolling_slope_t_score(rise, (8, 16, 32))
    assert np.nanmax(score) > 0


def test_first_crossing_not_argmax():
    scores = np.array([[0, 0, 2, 3, 10]], dtype=float)
    first = first_crossing(scores, 2.0, 0)
    assert first[0] == 2


def test_early_hit_rejects_pre_onset_alarm():
    scores = np.array([[0, 5, 0, 6, 0]], dtype=float)
    hit, first = early_hits(
        scores,
        4,
        np.array([3]),
        np.array([4]),
        0,
    )
    assert first[0] == 1
    assert not hit[0]


def test_conservative_threshold_float32_ties():
    maxima = {
        "x": np.array([5, 5, 5, 4, 3, 2, 1], dtype=np.float32)
    }
    threshold, _, allowed = conservative_threshold(maxima, 2 / 7)
    alerts = int(np.sum(maxima["x"] >= threshold))
    assert allowed["x"] == 2
    assert alerts <= 2


def test_clopper_pearson_boundaries():
    assert 0 < clopper_pearson_upper(0, 100) < 0.1
    assert clopper_pearson_upper(100, 100) == 1.0


def test_concurrent_context_changes_reference_field():
    cfg = Config(reference_impulse_probability=0.0)
    # The concurrent generator must record a shared artifact for every curve.
    data = generate_positive_stratum(
        "linear", "concurrent", 40, np.random.default_rng(123), cfg
    )
    assert np.all(data.artifact_family != "none")
    # A shared artifact should create nonzero target-reference covariance
    # after the earliest possible event/artifact region.
    ref_median = np.median(data.y[:, 1:, 70:], axis=1)
    target = data.y[:, 0, 70:]
    cov = np.mean(
        (ref_median - ref_median.mean(axis=1, keepdims=True))
        * (target - target.mean(axis=1, keepdims=True)),
        axis=1,
    )
    assert np.median(cov) > 0
