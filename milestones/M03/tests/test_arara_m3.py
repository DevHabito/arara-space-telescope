
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m3 as m3
import arara_m2 as m2


def test_sbw_output_shapes_and_finite():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(1)
    y = rng.normal(
        size=(4, 1 + cfg.n_references, cfg.n_time)
    )
    residual, q, beta = m3.normalize_sbw(y, cfg)
    assert residual.shape == (4, cfg.n_time)
    assert q.shape == (4, cfg.n_time)
    assert beta.shape == (4,)
    assert np.isfinite(residual).all()
    assert np.isfinite(q).all()
    assert np.isfinite(beta).all()


def test_sbw_is_causal_in_baseline_parameters():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(2)
    y = rng.normal(
        size=(3, 1 + cfg.n_references, cfg.n_time)
    )
    r1, q1, b1 = m3.normalize_sbw(y, cfg)

    y2 = y.copy()
    y2[:, :, cfg.baseline_n:] += 10000
    r2, q2, b2 = m3.normalize_sbw(y2, cfg)

    assert np.allclose(b1, b2)
    assert np.allclose(
        r1[:, : cfg.baseline_n],
        r2[:, : cfg.baseline_n],
    )
    assert np.allclose(
        q1[:, : cfg.baseline_n],
        q2[:, : cfg.baseline_n],
    )


def test_sbw_removes_ideal_shared_component():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(3)
    n = 20
    common = rng.normal(size=(n, cfg.n_time))
    coupling = rng.uniform(
        0.8, 1.2, size=(n, 1 + cfg.n_references)
    )
    # No independent noise: after robust per-star scaling, every series is
    # the same positive common component. The ideal residual must vanish.
    y = coupling[:, :, None] * common[:, None, :]

    residual, q, beta = m3.normalize_sbw(y, cfg)
    assert np.max(np.abs(residual)) < 1e-5


def test_sbw_preserves_target_only_ramp():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(4)
    y = rng.normal(
        size=(12, 1 + cfg.n_references, cfg.n_time)
    )
    y[:, 0, 100:160] += np.linspace(0, 8, 60)
    residual, q, beta = m3.normalize_sbw(y, cfg)
    change = residual[:, 159] - residual[:, 99]
    assert np.median(change) > 1.0


def test_sbw_and_wbs_differ_under_heterogeneous_filters():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(5)
    data = m2.generate_negative_family(
        "shared_oscillation", 100, rng, cfg
    )
    _, wbs, _, _ = m2.normalize_field(data.y, cfg)
    sbw, _, _ = m3.normalize_sbw(data.y, cfg)
    assert not np.allclose(sbw, wbs)


def test_score_is_causal_after_sbw():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(6)
    y = rng.normal(
        size=(2, 1 + cfg.n_references, cfg.n_time)
    )
    r1, _, _ = m3.normalize_sbw(y, cfg)
    s1 = m2.rolling_slope_t_score(
        r1, cfg.detector_windows
    )

    y2 = y.copy()
    y2[:, :, 140:] += 1000
    r2, _, _ = m3.normalize_sbw(y2, cfg)
    s2 = m2.rolling_slope_t_score(
        r2, cfg.detector_windows
    )
    assert np.allclose(s1[:, :140], s2[:, :140])


def test_dependency_generator_produces_all_strata():
    cfg = m3.Config().data_config()
    rng = np.random.default_rng(7)
    for stratum in m3.POSITIVE_STRATA:
        shape, context = stratum.split("__")
        data = m2.generate_positive_stratum(
            shape, context, 5, rng, cfg
        )
        assert data.y.shape[0] == 5


def test_threshold_float32_contract():
    maxima = {
        "x": np.array([5, 5, 5, 4, 3, 2, 1], dtype=np.float32)
    }
    threshold, _, allowed = m2.conservative_threshold(
        maxima, 2 / 7
    )
    alerts = int(np.sum(maxima["x"] >= threshold))
    assert allowed["x"] == 2
    assert alerts <= 2
