
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m12 as m12
import arara_m9 as m9


def test_fixed_snr_is_nine():
    assert m12.Config().fixed_snr == 9.0


def test_fraction_grid_is_frozen():
    assert m12.Config().fractions == (
        0.25, 0.50, 0.75, 1.0
    )


def test_prediction_is_t75():
    assert m12.Config().predicted_first_passing_fraction == 0.75


def test_times_are_ordered():
    cfg = m12.Config()
    panel = m9.generate_positive_panel(
        "power_law",
        "clean",
        30,
        np.random.default_rng(1),
        cfg.panel_config(),
    )
    _, times = m12.evaluate_positive_panel(panel, cfg)
    assert np.all(times[0.25] <= times[0.50])
    assert np.all(times[0.50] <= times[0.75])
    assert np.all(times[0.75] <= times[1.0])


def test_scores_are_finite():
    cfg = m12.Config()
    panel = m9.generate_positive_panel(
        "logistic",
        "concurrent",
        30,
        np.random.default_rng(2),
        cfg.panel_config(),
    )
    scores, _ = m12.evaluate_positive_panel(panel, cfg)
    for values in scores.values():
        assert np.isfinite(values).all()
