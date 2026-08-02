
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m9 as m9
import arara_m2 as m2


def test_snr_levels_are_frozen():
    assert m9.Config().snr_levels == (
        4.0, 6.0, 8.0, 10.0, 12.0
    )


def test_panel_reuses_same_latents_across_snr():
    cfg = m9.Config()
    panel = m9.generate_positive_panel(
        "linear",
        "clean",
        20,
        np.random.default_rng(1),
        cfg,
    )
    score4, signal4 = m9.evaluate_positive_panel(
        panel, 4.0, cfg
    )
    score8, signal8 = m9.evaluate_positive_panel(
        panel, 8.0, cfg
    )
    assert np.allclose(signal8, 2.0 * signal4)
    assert np.array_equal(
        panel.t100,
        m9.time_at_fraction(signal4, 1.0),
    )


def test_signal_amplitude_matches_stationary_sigma():
    cfg = m9.Config()
    panel = m9.generate_positive_panel(
        "logistic",
        "concurrent",
        30,
        np.random.default_rng(2),
        cfg,
    )
    _, signal = m9.evaluate_positive_panel(
        panel, 6.0, cfg
    )
    amplitude = signal.max(axis=1)
    assert np.allclose(
        amplitude,
        6.0 * panel.stationary_target_sd,
    )


def test_concurrent_panel_contains_shared_artifact():
    cfg = m9.Config()
    panel = m9.generate_positive_panel(
        "power_law",
        "concurrent",
        50,
        np.random.default_rng(3),
        cfg,
    )
    assert np.all(panel.artifact_family != "none")


def test_t100_not_before_onset():
    cfg = m9.Config()
    panel = m9.generate_positive_panel(
        "exponential",
        "clean",
        50,
        np.random.default_rng(4),
        cfg,
    )
    assert np.all(panel.t100 >= panel.onset)


def test_negative_scores_are_finite():
    cfg = m9.Config()
    scores, onset, t100 = m9.evaluate_negative_family(
        "shared_bump",
        50,
        np.random.default_rng(5),
        cfg,
    )
    assert np.isfinite(scores).all()
    assert np.all(t100 >= onset)


def test_higher_snr_improves_median_score_in_sample():
    cfg = m9.Config()
    panel = m9.generate_positive_panel(
        "linear",
        "clean",
        200,
        np.random.default_rng(6),
        cfg,
    )
    score4, _ = m9.evaluate_positive_panel(
        panel, 4.0, cfg
    )
    score12, _ = m9.evaluate_positive_panel(
        panel, 12.0, cfg
    )
    assert np.median(score12) > np.median(score4)


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
    assert alerts <= allowed["x"]
