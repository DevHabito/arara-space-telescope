"""AR-OBS003-P01 regression tests using only artificial arrays, no archive data."""

import hashlib
import json
import unittest

import numpy as np

from scripts.ar_obs003_pixel_aperture import (
    LC_FROZEN_SHA,
    PROTOCOL,
    SECTOR,
    TIC_ID,
    assess_hypotheses,
    canonical_digest,
    describe_aperture,
    evaluate_paired_cadences,
    validate_ids,
)


def make_fixture():
    """Return deliberately shuffled cadences, one ineligible pixel and one extra LC row."""
    tp_ids = np.array([11, 12, 13, 14], dtype=np.int32)
    lc_ids = np.array([14, 11, 13, 12, 15], dtype=np.int32)
    tp_quality = np.zeros(4, dtype=np.int32)
    lc_quality = np.zeros(5, dtype=np.int32)
    tp_time = np.array([1.1, 1.2, 1.3, 1.4])
    lc_time = np.array([1.4, 1.1, 1.3, 1.2, 1.5])
    selected = np.array([[True, False], [False, True]], dtype=bool)
    flux = np.array([
        [[1.0, 20.0], [15.0, 3.0]],
        [[2.0, 20.0], [15.0, 4.0]],
        [[3.0, 20.0], [15.0, np.nan]],
        [[5.0, 20.0], [15.0, 6.0]],
    ])
    lc_sap = np.array([11.0, 4.0, 5.0, 6.0, 3.0])
    return (tp_ids, tp_quality, tp_time, flux, selected,
            lc_ids, lc_quality, lc_time, lc_sap)


class PixelApertureAuditTests(unittest.TestCase):
    def test_frozen_source(self):
        self.assertEqual(PROTOCOL, "AR-OBS003-P01")
        self.assertEqual(SECTOR, 5)
        self.assertEqual(TIC_ID, 307210830)
        self.assertEqual(
            LC_FROZEN_SHA,
            "a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae",
        )

    def test_optimal_aperture_uses_second_bit_only(self):
        mask = np.array([[3, 5, 0], [35, 8, 2]], dtype=np.int32)
        selected, report = describe_aperture(mask, (2, 3))
        np.testing.assert_array_equal(
            selected, [[True, False, False], [True, False, True]]
        )
        self.assertEqual(report["optimal_pixel_count"], 3)
        self.assertEqual(report["background_pixel_count"], 1)
        self.assertEqual(report["aperture_bit_counts_1_to_9"]["2"], 3)

    def test_reject_invalid_aperture(self):
        with self.assertRaises(ValueError):
            describe_aperture(np.zeros((2, 2), dtype=int), (2, 2))
        with self.assertRaises(ValueError):
            describe_aperture(np.ones((2, 2), dtype=int), (3, 2))
        with self.assertRaises(ValueError):
            describe_aperture(np.full((2, 2), -1, dtype=int), (2, 2))
        with self.assertRaises(ValueError):
            describe_aperture(np.full((2, 2), 2.0), (2, 2))

    def test_invalid_or_duplicate_cadence_ids_fail(self):
        valid = np.array([9, 10, 11], dtype=np.int32)
        q = np.zeros(3, dtype=np.int32)
        t = np.ones(3)
        np.testing.assert_array_equal(validate_ids(valid, q, t), valid)
        with self.assertRaises(ValueError):
            validate_ids(np.array([9, 9, 11]), q, t)
        with self.assertRaises(ValueError):
            validate_ids(valid, np.array([-1, 0, 0]), t)
        with self.assertRaises(ValueError):
            validate_ids(valid.astype(float), q, t)
        with self.assertRaises(ValueError):
            validate_ids(valid, q[:2], t)

    def test_matches_cadenceno_not_awkward_row_order(self):
        report = evaluate_paired_cadences(*make_fixture())
        self.assertEqual(report["tpf_cadences"], 4)
        self.assertEqual(report["lc_cadences"], 5)
        self.assertEqual(report["matched_cadences"], 4)
        self.assertEqual(report["unmatched_tpf"], 0)
        self.assertEqual(report["unmatched_lc"], 1)
        self.assertEqual(report["quality_mismatch_rows"], 0)
        self.assertEqual(report["time_offset_days_max"], 0.0)
        self.assertEqual(report["eligible_reconstruction_rows"], 3)
        self.assertEqual(
            report["skipped_by_reason"],
            {
                "not_quality_zero_in_both": 0,
                "quality_zero_but_invalid_sap": 0,
                "quality_zero_valid_sap_but_missing_selected_pixel": 1,
            },
        )
        self.assertEqual(report["sap_reconstruction"]["median_relative_error"], 0.0)
        self.assertEqual(report["sap_reconstruction"]["count_relative_error_le_0_001"], 3)

    def test_bad_quality_is_excluded_and_counted(self):
        fixture = list(make_fixture())
        fixture[6] = np.array([0, 0, 4, 0, 0], dtype=np.int32)
        report = evaluate_paired_cadences(*fixture)
        self.assertEqual(report["quality_mismatch_rows"], 1)
        self.assertEqual(report["skipped_by_reason"]["not_quality_zero_in_both"], 1)
        self.assertEqual(report["skipped_by_reason"]["quality_zero_valid_sap_but_missing_selected_pixel"], 0)

    def test_true_sap_discrepancy_rejects_reconstruction(self):
        fixture = list(make_fixture())
        fixture[8] = np.array([11.0, 4.0, 5.0, 60.0, 3.0])
        report = evaluate_paired_cadences(*fixture)
        self.assertEqual(report["sap_reconstruction"]["count_relative_error_le_0_001"], 2)
        self.assertGreater(report["sap_reconstruction"]["max_relative_error"], 0.8)

    def test_schema_shape_rejections(self):
        fixture = list(make_fixture())
        fixture[3] = np.ones((4, 2), dtype=float)
        with self.assertRaises(ValueError):
            evaluate_paired_cadences(*fixture)
        fixture = list(make_fixture())
        fixture[4] = np.ones((2, 3), dtype=bool)
        with self.assertRaises(ValueError):
            evaluate_paired_cadences(*fixture)

    def test_hypotheses_have_independent_fixed_thresholds(self):
        row = {
            "matched_cadences": 120,
            "finite_paired_times": 120,
            "quality_mismatch_rows": 0,
            "time_offset_days_max": 0.0,
            "eligible_reconstruction_rows": 120,
            "sap_reconstruction": {
                "median_relative_error": 0.00005,
                "fraction_relative_error_le_0_001": 0.97,
            },
        }
        data = {"paired_observations": row}
        verdict = assess_hypotheses(data)
        self.assertTrue(all(s.startswith("SUPPORTED_") for s in verdict.values()))
        row["sap_reconstruction"]["fraction_relative_error_le_0_001"] = 0.90
        verdict = assess_hypotheses(data)
        self.assertTrue(verdict["H1_cadence_quality_time_alignment"].startswith("SUPPORTED_"))
        self.assertTrue(verdict["H2_sap_aperture_reconstruction"].startswith("NOT_SUPPORTED_"))
        row["time_offset_days_max"] = 1.1e-6
        verdict = assess_hypotheses(data)
        self.assertTrue(verdict["H1_cadence_quality_time_alignment"].startswith("NOT_SUPPORTED_"))

    def test_digest_is_canonical_and_content_dependent(self):
        data = {"b": 2, "a": 1}
        self.assertEqual(
            canonical_digest(data),
            hashlib.sha256(b'{"a":1,"b":2}').hexdigest(),
        )
        self.assertNotEqual(canonical_digest(data), canonical_digest({"a": 1, "b": 3}))


if __name__ == "__main__":
    unittest.main()
