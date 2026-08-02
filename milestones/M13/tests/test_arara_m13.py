
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m13 as m13


def test_fraction_is_t50():
    assert m13.Config().target_fraction == 0.50


def test_snr_grid_is_frozen():
    assert m13.Config().snr_levels == (
        10.0, 12.0, 14.0, 16.0, 18.0
    )


def test_prediction_is_14():
    assert m13.Config().predicted_first_passing_snr == 14.0


def test_core_preserves_parameters():
    cfg = m13.Config()
    core = cfg.core()
    assert core.target_fraction == 0.50
    assert core.snr_levels == cfg.snr_levels
    assert core.predicted_first_passing_snr == 14.0
