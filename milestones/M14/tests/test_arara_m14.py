
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m14 as m14


def test_fraction_is_t50():
    assert m14.Config().target_fraction == 0.50


def test_snr_grid_is_frozen():
    assert m14.Config().snr_levels == (
        10.5, 11.0, 11.5, 12.0
    )


def test_prediction_is_12():
    assert m14.Config().predicted_first_passing_snr == 12.0


def test_core_preserves_parameters():
    cfg = m14.Config()
    core = cfg.core()
    assert core.target_fraction == 0.50
    assert core.snr_levels == cfg.snr_levels
    assert core.predicted_first_passing_snr == 12.0
