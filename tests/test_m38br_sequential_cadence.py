"""P0.6 temporal-order and missing-cadence tests fixed before implementation.

These are unlabelled numerical fixtures, not telescope observations or
calibration. The pre-outcome contract is P06_SEQUENTIAL_CADENCE_POLICY.md.
"""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest

import numpy as np

EXPERIMENT = Path(__file__).resolve().parents[1] / "experiments/M38B-R"
sys.path.insert(0, str(EXPERIMENT))

from observed_prefix import score_observed_prefix  # noqa: E402
from sequential_cadence import CadenceLedger  # noqa: E402


class SequentialCadenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(20261103)
        cls.stars = rng.normal(size=(2, 9, 180)) * 0.1
        cls.stars[:, 0, :] += (
            0.08 * np.maximum(np.arange(180, dtype=np.float64) - 69.0, 0.0)
        )

    def new_ledger(self) -> CadenceLedger:
        return CadenceLedger(curves=2, stars_per_curve=9)

    def add_through(self, ledger: CadenceLedger, last: int) -> None:
        for index in range(last + 1):
            ledger.append(
                cadence_index=index,
                timestamp_seconds=1000.0 + 0.5 * index,
                frame=self.stars[:, :, index],
            )

    def test_eligible_prefixes_match_direct_scoring_bitwise(self):
        ledger = self.new_ledger()
        for index in range(180):
            ledger.append(
                cadence_index=index,
                timestamp_seconds=1000.0 + 0.5 * index,
                frame=self.stars[:, :, index],
            )
            if index in (81, 83, 179):
                actual = ledger.score_latest()
                direct = score_observed_prefix(
                    self.stars[:, :, :index + 1], endpoint=index
                )
                self.assertEqual(set(actual), set(direct))
                for key in actual:
                    np.testing.assert_array_equal(actual[key], direct[key])
        self.assertEqual(ledger.count, 180)
        self.assertEqual(ledger.latest_index, 179)
        self.assertEqual(len(ledger.declared_times), 180)
        self.assertEqual(ledger.declared_times[0], 1000.0)
        self.assertEqual(ledger.declared_times[-1], 1089.5)
        self.assertFalse(ledger.blocked)

    def test_gap_is_irrecoverable_and_cannot_score_or_snapshot(self):
        ledger = self.new_ledger()
        ledger.append(
            cadence_index=0, timestamp_seconds=1000.0,
            frame=self.stars[:, :, 0],
        )
        with self.assertRaisesRegex(ValueError, "gaps"):
            ledger.append(
                cadence_index=2, timestamp_seconds=1001.0,
                frame=self.stars[:, :, 2],
            )
        self.assertTrue(ledger.blocked)
        self.assertEqual(ledger.count, 1)
        self.assertEqual(ledger.declared_times, (1000.0,))
        with self.assertRaisesRegex(ValueError, "blocked"):
            ledger.append(
                cadence_index=1, timestamp_seconds=1000.5,
                frame=self.stars[:, :, 1],
            )
        with self.assertRaisesRegex(ValueError, "blocked"):
            ledger.snapshot()
        with self.assertRaisesRegex(ValueError, "blocked"):
            ledger.score_latest()

    def test_duplicates_and_reversed_indices_block_separate_ledgers(self):
        for bad_index in (1, 0):
            with self.subTest(index=bad_index):
                ledger = self.new_ledger()
                self.add_through(ledger, 1)
                with self.assertRaisesRegex(ValueError, "gaps"):
                    ledger.append(
                        cadence_index=bad_index,
                        timestamp_seconds=1002.0,
                        frame=self.stars[:, :, bad_index],
                    )
                self.assertEqual(ledger.count, 2)
                self.assertTrue(ledger.blocked)

    def test_invalid_or_backward_declared_timestamps_block_segment(self):
        for bad_time in (1000.0, 999.0, float("nan"), float("inf"),
                         float("-inf"), True, "1001", None):
            with self.subTest(timestamp=bad_time):
                ledger = self.new_ledger()
                self.add_through(ledger, 0)
                with self.assertRaises(ValueError):
                    ledger.append(
                        cadence_index=1, timestamp_seconds=bad_time,
                        frame=self.stars[:, :, 1],
                    )
                self.assertTrue(ledger.blocked)
                self.assertEqual(ledger.count, 1)
                with self.assertRaisesRegex(ValueError, "blocked"):
                    ledger.snapshot()

    def test_invalid_measured_frames_block_segment_without_imputation(self):
        nan_frame = self.stars[:, :, 1].copy()
        nan_frame[0, 0] = np.nan
        inf_frame = self.stars[:, :, 1].copy()
        inf_frame[1, 3] = np.inf
        invalid = (
            nan_frame, inf_frame, self.stars[:, :1, 1],
            self.stars[0, :, 1], np.full((2, 9), "1"),
        )
        for frame in invalid:
            with self.subTest(shape=np.asarray(frame).shape):
                ledger = self.new_ledger()
                self.add_through(ledger, 0)
                with self.assertRaises(ValueError):
                    ledger.append(
                        cadence_index=1, timestamp_seconds=1000.5,
                        frame=frame,
                    )
                self.assertTrue(ledger.blocked)
                self.assertEqual(ledger.count, 1)

    def test_frame_and_snapshot_are_owned_copies(self):
        ledger = self.new_ledger()
        first = self.stars[:, :, 0].copy()
        expected = first.copy()
        ledger.append(
            cadence_index=0, timestamp_seconds=1000.0, frame=first
        )
        first[:] = 500.0
        snap = ledger.snapshot()
        np.testing.assert_array_equal(snap[:, :, 0], expected)
        snap[:, :, 0] = -200.0
        np.testing.assert_array_equal(
            ledger.snapshot()[:, :, 0], expected
        )

    def test_scoring_too_early_fails_without_poisoning_valid_ledger(self):
        ledger = self.new_ledger()
        self.add_through(ledger, 80)
        with self.assertRaisesRegex(ValueError, "0..81"):
            ledger.score_latest()
        self.assertFalse(ledger.blocked)
        ledger.append(
            cadence_index=81, timestamp_seconds=1040.5,
            frame=self.stars[:, :, 81],
        )
        self.assertEqual(ledger.score_latest()["grid_score_grid"].shape, (2, 1))

    def test_cadence_beyond_historical_horizon_and_bool_index_block(self):
        for bad in (180, True):
            with self.subTest(bad_index=bad):
                ledger = self.new_ledger()
                if bad == 180:
                    self.add_through(ledger, 179)
                with self.assertRaisesRegex(ValueError, "Cadence index"):
                    ledger.append(
                        cadence_index=bad,
                        timestamp_seconds=2000.0,
                        frame=self.stars[:, :, 0],
                    )
                self.assertTrue(ledger.blocked)

    def test_invalid_constructor_dimensions_rejected(self):
        for curves, stars in ((0, 9), (True, 9), (2.0, 9),
                              (2, 1), (2, False), (2, 2.0)):
            with self.subTest(curves=curves, stars=stars):
                with self.assertRaises(ValueError):
                    CadenceLedger(curves=curves, stars_per_curve=stars)

    def test_metadata_is_only_declared_order_not_calibrated_spacing(self):
        ledger = self.new_ledger()
        ledger.append(
            cadence_index=0, timestamp_seconds=8.0,
            frame=self.stars[:, :, 0],
        )
        ledger.append(
            cadence_index=1, timestamp_seconds=8.001,
            frame=self.stars[:, :, 1],
        )
        ledger.append(
            cadence_index=2, timestamp_seconds=9e6,
            frame=self.stars[:, :, 2],
        )
        self.assertEqual(ledger.declared_times, (8.0, 8.001, 9000000.0))
        self.assertFalse(ledger.blocked)
        # No claim is made that the producer's timestamps are trustworthy.

    def test_score_only_latest_without_earlier_endpoint_argument(self):
        ledger = self.new_ledger()
        self.add_through(ledger, 83)
        self.assertEqual(ledger.latest_index, 83)
        self.assertEqual(
            tuple(inspect.signature(ledger.score_latest).parameters), ()
        )
        with self.assertRaises(TypeError):
            ledger.score_latest(endpoint=81)

    def test_no_historical_scorer_import_or_output_threshold(self):
        source = (EXPERIMENT / "sequential_cadence.py").read_text(
            encoding="utf-8"
        )
        for forbidden in ("arara_m38b", "observable_candidate",
                          "thresholds.json", "holdout"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(
            tuple(inspect.signature(CadenceLedger.append).parameters),
            ("self", "cadence_index", "timestamp_seconds", "frame")
        )


if __name__ == "__main__":
    unittest.main()
