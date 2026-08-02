
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m10 as m10
import arara_m9 as m9
import arara_m2 as m2


def test_frozen_fraction_grid():
    assert m10.Config().fractions == (
        0.25, 0.50, 0.75, 1.0
    )


def test_fixed_snr_is_eight():
    assert m10.Config().fixed_snr == 8.0


def test_times_are_ordered():
    cfg = m10.Config()
    panel = m9.generate_positive_panel(
        "power_law",
        "clean",
        40,
        np.random.default_rng(1),
        cfg.panel_config(),
    )
    _, times = m10.evaluate_positive_panel(
        panel, cfg
    )
    assert np.all(times[0.25] <= times[0.50])
    assert np.all(times[0.50] <= times[0.75])
    assert np.all(times[0.75] <= times[1.0])


def test_positive_scores_are_finite():
    cfg = m10.Config()
    panel = m9.generate_positive_panel(
        "linear",
        "concurrent",
        40,
        np.random.default_rng(2),
        cfg.panel_config(),
    )
    scores, _ = m10.evaluate_positive_panel(
        panel, cfg
    )
    for score in scores.values():
        assert np.isfinite(score).all()


def test_negative_times_are_ordered():
    cfg = m10.Config()
    scores, times, onset = (
        m10.evaluate_negative_family(
            "shared_bump",
            40,
            np.random.default_rng(3),
            cfg,
        )
    )
    assert np.all(times[0.25] <= times[0.50])
    assert np.all(times[0.50] <= times[0.75])
    assert np.all(times[0.75] <= times[1.0])
    for score in scores.values():
        assert np.isfinite(score).all()


def test_sample_median_score_increases_from_t25_to_t100():
    cfg = m10.Config()
    panel = m9.generate_positive_panel(
        "logistic",
        "clean",
        200,
        np.random.default_rng(4),
        cfg.panel_config(),
    )
    scores, _ = m10.evaluate_positive_panel(
        panel, cfg
    )
    assert np.median(scores[1.0]) > np.median(
        scores[0.25]
    )


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
