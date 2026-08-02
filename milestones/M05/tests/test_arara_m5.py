
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m5 as m5
import arara_m2 as m2


def test_signal_operator_matches_direct_difference():
    cfg = m5.Config().data_config()
    rng = np.random.default_rng(1)
    n = 8
    data = m2.generate_positive_stratum(
        "linear", "clean", n, rng, cfg
    )
    residual_full, processed_signal, _ = (
        m5.sbw_with_signal_operator(
            data.y,
            data.target_signal,
            cfg,
        )
    )
    y_without = data.y.copy()
    y_without[:, 0, :] -= data.target_signal
    residual_without, _, _ = m5.sbw_with_signal_operator(
        y_without,
        np.zeros_like(data.target_signal),
        cfg,
    )
    assert np.allclose(
        residual_full - residual_without,
        processed_signal,
        atol=1e-10,
    )


def test_signal_operator_is_zero_before_onset():
    cfg = m5.Config().data_config()
    rng = np.random.default_rng(2)
    data = m2.generate_positive_stratum(
        "logistic", "concurrent", 10, rng, cfg
    )
    _, processed_signal, _ = m5.sbw_with_signal_operator(
        data.y,
        data.target_signal,
        cfg,
    )
    for i in range(10):
        assert np.allclose(
            processed_signal[i, :data.onset[i]],
            0.0,
        )


def test_virtual_hypotheses_are_valid():
    cfg = m5.Config().data_config()
    signal, onset, t25, shapes = (
        m5.generate_virtual_hypotheses(
            100,
            np.random.default_rng(3),
            cfg,
        )
    )
    assert signal.shape == (100, cfg.n_time)
    assert np.all(t25 >= onset)
    assert set(shapes).issubset(set(m5.POSITIVE_SHAPES))
    assert np.all(
        signal[np.arange(100), t25] >= 0.25
    )


def test_aligned_exact_signal_scores_infinite_without_noise():
    n = 4
    t = 50
    template = np.zeros((n, t))
    template[:, 10:20] = np.linspace(0, 1, 10)
    residual = 3.0 + 5.0 * template
    onset = np.full(n, 10)
    t25 = np.full(n, 19)
    score = m5.aligned_t_score(
        residual,
        template,
        onset,
        t25,
    )
    assert np.isinf(score).all()


def test_aligned_negative_direction_scores_zero():
    template = np.zeros((1, 30))
    template[0, 5:15] = np.linspace(0, 1, 10)
    residual = -template
    score = m5.aligned_t_score(
        residual,
        template,
        np.array([5]),
        np.array([14]),
    )
    assert score[0] == 0.0


def test_future_changes_do_not_modify_baseline_operator():
    cfg = m5.Config().data_config()
    rng = np.random.default_rng(4)
    y = rng.normal(
        size=(3, 1 + cfg.n_references, cfg.n_time)
    )
    signal = np.zeros((3, cfg.n_time))
    r1, g1, p1 = m5.sbw_with_signal_operator(
        y, signal, cfg
    )

    y2 = y.copy()
    y2[:, :, cfg.baseline_n:] += 10000
    r2, g2, p2 = m5.sbw_with_signal_operator(
        y2, signal, cfg
    )
    assert np.allclose(
        p1["target_scale"], p2["target_scale"]
    )
    assert np.allclose(
        p1["beta_hat"], p2["beta_hat"]
    )
    assert np.allclose(
        p1["residual_scale"], p2["residual_scale"]
    )
    assert np.allclose(
        p1["residual_phi"], p2["residual_phi"]
    )
    assert np.allclose(
        r1[:, :cfg.baseline_n],
        r2[:, :cfg.baseline_n],
    )


def test_bootstrap_point_is_near_empirical_recall():
    hits = {
        s: np.array([1] * 60 + [0] * 40, dtype=bool)
        for s in m5.POSITIVE_STRATA
    }
    boot = m5.stratified_bootstrap_recall(
        hits, 2000, 5
    )
    assert abs(boot.mean() - 0.6) < 0.01


def test_float32_threshold_contract():
    maxima = {
        "x": np.array(
            [5, 5, 5, 4, 3, 2, 1],
            dtype=np.float32,
        )
    }
    threshold, _, allowed = m2.conservative_threshold(
        maxima, 2 / 7
    )
    alerts = int(np.sum(maxima["x"] >= threshold))
    assert allowed["x"] == 2
    assert alerts <= 2
