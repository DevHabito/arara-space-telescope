
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m11 as m11


def test_fraction_is_t75():
    assert m11.Config().target_fraction == 0.75


def test_snr_grid_is_frozen():
    assert m11.Config().snr_levels == (
        8.0, 8.5, 9.0, 9.5, 10.0
    )


def test_prediction_is_8_5():
    assert m11.Config().predicted_first_passing_snr == 8.5


def test_core_preserves_parameters():
    cfg = m11.Config()
    core = cfg.core()
    assert core.target_fraction == 0.75
    assert core.snr_levels == cfg.snr_levels
    assert core.predicted_first_passing_snr == 8.5
