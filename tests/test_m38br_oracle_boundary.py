"""Regression witness for a historical candidate boundary-mask oracle.

This test does not quantify changes to detection recall or false-positive rate.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "milestones/M38B_recovery/arara_m38b.py"


def boundary_mask(endpoint: int, estimated_onset: int, true_onset: int, horizon: int):
    """Reproduce the archived candidate's nine-sample boundary predicate."""
    return tuple(
        0 <= endpoint + offset - estimated_onset + true_onset < horizon
        for offset in range(-8, 1)
    )


class ArchivedOnsetBoundaryTests(unittest.TestCase):
    def test_truth_change_alone_changes_boundary_mask(self):
        first = boundary_mask(179, 80, 80, 180)
        second = boundary_mask(179, 80, 110, 180)
        self.assertEqual(first, (True,) * 9)
        self.assertEqual(second, (False,) * 9)
        self.assertNotEqual(first, second)

    def test_witness_refers_to_exact_archived_source(self):
        if not SOURCE.is_file():
            self.skipTest("Full historical source checkout is unavailable")
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("absolute_source = positions + np.asarray(onset", source)
        self.assertIn("source_valid = (absolute_source >= 0.0)", source)
        self.assertIn("raw_grid = phase * source_valid", source)
        self.assertIn("raw_grid_5d = raw_grid_5d * source_valid", source)


if __name__ == "__main__":
    unittest.main()
