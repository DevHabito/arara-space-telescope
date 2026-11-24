"""P0.7 checks precommitted in P07_EXPOSURE_PROVENANCE_POLICY.md.

Only declared, untrusted time labels on constructed unlabeled arrays.
No calibration, holdout, detector threshold, or real-telescope measurements.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))

from exposure_provenance import ExposureProvenanceLedger  # noqa: E402
from observed_prefix import score_observed_prefix  # noqa: E402


class ExposureProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(20261103)
        cls.stars = rng.normal(size=(2, 9, 180)) * 0.1
        cls.stars[:, 0, :] += (
            0.08 * np.maximum(np.arange(180, dtype=np.float64) - 69.0, 0.0)
        )

    def ledger(self):
        return ExposureProvenanceLedger(
            curves=2, stars_per_curve=9, session_id="audit-session-A",
            instrument_id="declared-detector-A", target_id="declared-target-A",
            clock_id="unverified-clock-A",
        )

    def append(self, ledger, k, *, frame=None, **updates):
        args = dict(
            cadence_index=k,
            frame=self.stars[:, :, k] if frame is None else frame,
            instrument_id="declared-detector-A",
            target_id="declared-target-A", clock_id="unverified-clock-A",
            start_seconds=1000.0 + 2.0 * k,
            end_seconds=1000.5 + 2.0 * k,
            start_uncertainty_seconds=0.01,
            end_uncertainty_seconds=0.01,
        )
        args.update(updates)
        ledger.append(**args)

    def append_through(self, ledger, endpoint):
        for k in range(endpoint + 1):
            self.append(ledger, k)

    def test_all_latest_scores_equal_direct_prefix_and_full_sequence(self):
        ledger = self.ledger()
        for k in range(180):
            self.append(ledger, k)
            if k in (81, 83, 179):
                actual = ledger.score_latest()
                direct = score_observed_prefix(
                    self.stars[:, :, :k + 1], endpoint=k
                )
                for field in actual:
                    np.testing.assert_array_equal(actual[field], direct[field])
        self.assertFalse(ledger.blocked)
        self.assertEqual(ledger.count, 180)
        self.assertEqual(len(ledger.records), 180)
        self.assertEqual(len(ledger.verify_integrity()), 64)
        self.assertEqual(ledger.records[0].session_id, "audit-session-A")
        self.assertEqual(ledger.records[-1].cadence_index, 179)
        self.assertEqual(ledger.records[-1].start_seconds, 1358.0)
        self.assertEqual(ledger.records[-1].end_seconds, 1358.5)

    def test_ambiguous_positive_duration_rejected_fail_closed(self):
        for end, start_error, end_error in (
            (1000.1, 0.06, 0.06),
            (1000.0, 0.0, 0.0),
            (999.9, 0.0, 0.0),
        ):
            with self.subTest(end=end):
                ledger = self.ledger()
                with self.assertRaisesRegex(ValueError, "definitely positive"):
                    self.append(
                        ledger, 0, end_seconds=end,
                        start_uncertainty_seconds=start_error,
                        end_uncertainty_seconds=end_error,
                    )
                self.assertTrue(ledger.blocked)
                self.assertEqual(ledger.count, 0)
                self.assertEqual(ledger.records, ())

    def test_uncertainty_overlap_rejected_despite_nominal_order(self):
        ledger = self.ledger()
        self.append(ledger, 0)
        # Nominal next start 1000.6 exceeds previous end 1000.5.
        # Bounds overlap: previous end+0.1=1000.6, next start-0.1=1000.5.
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.append(
                ledger, 1, start_seconds=1000.6, end_seconds=1001.1,
                start_uncertainty_seconds=0.1,
                end_uncertainty_seconds=0.1,
            )
        self.assertTrue(ledger.blocked)
        self.assertEqual(ledger.count, 1)
        with self.assertRaisesRegex(ValueError, "blocked"):
            ledger.snapshot()

    def test_negative_nonfinite_boolean_uncertainty_blocks(self):
        for bad in (-0.1, float("nan"), float("inf"),
                    float("-inf"), True, "0.01"):
            with self.subTest(value=bad):
                ledger = self.ledger()
                with self.assertRaises(ValueError):
                    self.append(ledger, 0, start_uncertainty_seconds=bad)
                self.assertTrue(ledger.blocked)
                self.assertEqual(ledger.count, 0)

    def test_invalid_declared_times_and_nonfinite_derived_bounds_block(self):
        examples = (
            {"start_seconds": float("nan")},
            {"end_seconds": float("inf")},
            {"start_seconds": True},
            {"end_seconds": "1001"},
            {"start_seconds": 1e308, "start_uncertainty_seconds": 1e308,
             "end_seconds": 1e308},
        )
        for update in examples:
            with self.subTest(update=update):
                ledger = self.ledger()
                with self.assertRaises(ValueError):
                    self.append(ledger, 0, **update)
                self.assertTrue(ledger.blocked)
                self.assertEqual(ledger.records, ())

    def test_identity_or_cadence_change_blocks_without_new_record(self):
        for update in (
            {"instrument_id": "other"},
            {"target_id": "other"},
            {"clock_id": "other"},
            {"cadence_index": 3},
        ):
            with self.subTest(update=update):
                ledger = self.ledger()
                self.append(ledger, 0)
                with self.assertRaises(ValueError):
                    self.append(ledger, 1, **update)
                self.assertTrue(ledger.blocked)
                self.assertEqual(len(ledger.records), 1)
                with self.assertRaisesRegex(ValueError, "blocked"):
                    self.append(ledger, 1)

    def test_nonfinite_malformed_frame_blocks_on_composed_boundary(self):
        for frame in (
            [[1.0, 2.0], [3.0]], np.full((2, 9), np.nan),
            np.full((2, 9), np.inf), np.zeros((2, 8)),
        ):
            with self.subTest(frame_type=type(frame).__name__):
                ledger = self.ledger()
                with self.assertRaises(ValueError):
                    self.append(ledger, 0, frame=frame)
                self.assertTrue(ledger.blocked)
                self.assertEqual(ledger.count, 0)
                self.assertEqual(ledger.records, ())

    def test_mutating_caller_frame_or_snapshot_does_not_change_digest(self):
        ledger = self.ledger()
        first = self.stars[:, :, 0].copy()
        self.append(ledger, 0, frame=first)
        original_digest = ledger.verify_integrity()
        first[:] = 99
        external_snapshot = ledger.snapshot()
        external_snapshot[:] = -777
        self.assertEqual(ledger.verify_integrity(), original_digest)
        np.testing.assert_array_equal(
            ledger.snapshot()[:, :, 0], self.stars[:, :, 0]
        )

    def test_identical_sequences_have_equal_digest(self):
        first, second = self.ledger(), self.ledger()
        for k in range(5):
            self.append(first, k)
            self.append(second, k)
        self.assertEqual(first.verify_integrity(), second.verify_integrity())
        self.assertEqual(
            tuple(r.digest for r in first.records),
            tuple(r.digest for r in second.records),
        )

    def test_changed_value_changes_digest_without_changing_structure(self):
        first, second = self.ledger(), self.ledger()
        frame = self.stars[:, :, 0].copy()
        changed = frame.copy()
        changed[0, 0] += 0.125
        self.append(first, 0, frame=frame)
        self.append(second, 0, frame=changed)
        self.assertNotEqual(first.verify_integrity(), second.verify_integrity())

    def test_changed_time_changes_digest_when_order_is_still_valid(self):
        first, second = self.ledger(), self.ledger()
        self.append(first, 0)
        self.append(second, 0, end_seconds=1000.6)
        self.assertNotEqual(first.verify_integrity(), second.verify_integrity())

    def test_internal_record_tampering_detected_and_blocks_score(self):
        ledger = self.ledger()
        self.append_through(ledger, 81)
        ledger.verify_integrity()
        ledger._records[0] = replace(
            ledger._records[0], target_id="tampered-without-rehash"
        )
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            ledger.verify_integrity()
        self.assertTrue(ledger.blocked)
        with self.assertRaisesRegex(ValueError, "blocked"):
            ledger.score_latest()
        with self.assertRaisesRegex(ValueError, "blocked"):
            ledger.append(
                cadence_index=82, frame=self.stars[:, :, 82],
                instrument_id="declared-detector-A",
                target_id="declared-target-A", clock_id="unverified-clock-A",
                start_seconds=1164.0, end_seconds=1164.5,
                start_uncertainty_seconds=0.01,
                end_uncertainty_seconds=0.01,
            )

    def test_constructor_rejects_invalid_source_labels(self):
        for patch in (
            {"clock_id": ""}, {"target_id": " "},
            {"instrument_id": 7}, {"session_id": "x" * 129},
        ):
            with self.subTest(patch=patch):
                args = dict(
                    curves=2, stars_per_curve=9,
                    session_id="audit-session-A",
                    instrument_id="declared-detector-A",
                    target_id="declared-target-A",
                    clock_id="unverified-clock-A",
                )
                args.update(patch)
                with self.assertRaises(ValueError):
                    ExposureProvenanceLedger(**args)

    def test_timestamps_remain_unverified_source_claims(self):
        ledger = self.ledger()
        self.append(
            ledger, 0, start_seconds=-1000.0, end_seconds=-999.5
        )
        self.append(
            ledger, 1, start_seconds=1e6, end_seconds=1e6 + 0.5
        )
        self.assertFalse(ledger.blocked)
        self.assertEqual(ledger.count, 2)
        # Large time gaps are allowed; no accepted instrument cadence
        # jitter, epoch or synchronization policy exists.

    def test_source_and_api_have_no_archived_detector_import(self):
        source = (ROOT / "experiments/M38B-R/exposure_provenance.py").read_text()
        for blocked in ("observable_candidate", "arara_m38b",
                        "thresholds.json"):
            self.assertNotIn(blocked, source)


if __name__ == "__main__":
    unittest.main()
