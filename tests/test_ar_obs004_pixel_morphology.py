"""Synthetic-only checks for AR-OBS004 observational audit and frozen gates."""

import hashlib
import json
import unittest

import numpy as np

from scripts.ar_obs004_pixel_morphology import (
    PROTOCOL,
    SHIFT,
    TPF_FROZEN_SHA,
    background_medians,
    correlation,
    digest,
    pixel_photocenters,
    summarize_background,
    summarize_movement,
    verdicts,
)


class PixelMorphologyAuditTests(unittest.TestCase):
    def test_frozen_source_and_control(self):
        self.assertEqual(PROTOCOL, "AR-OBS004-P01")
        self.assertEqual(SHIFT, 24)
        self.assertEqual(
            TPF_FROZEN_SHA,
            "c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b",
        )

    def test_pixel_photocenter_positive_weights_and_coordinates(self):
        data = np.array([
            [[1.0, 4.0], [8.0, 3.0]],
            [[-2.0, 6.0], [7.0, 0.0]],
            [[np.nan, 4.0], [8.0, 3.0]],
            [[0.0, 3.0], [4.0, 0.0]],
        ])
        selection = np.array([[True, True], [False, True]])
        cx, cy, valid = pixel_photocenters(data, selection)
        np.testing.assert_array_equal(valid, [True, True, False, True])
        self.assertAlmostEqual(cx[0], 7.0 / 8.0)
        self.assertAlmostEqual(cy[0], 3.0 / 8.0)
        self.assertAlmostEqual(cx[1], 1.0)
        self.assertAlmostEqual(cx[3], 1.0)
        self.assertTrue(np.isnan(cx[2]))

    def test_pixel_centroid_rejects_empty_or_wrong_mask(self):
        cube = np.ones((3, 2, 2))
        with self.assertRaises(ValueError):
            pixel_photocenters(cube, np.zeros((2, 2), dtype=bool))
        with self.assertRaises(ValueError):
            pixel_photocenters(cube, np.ones((3, 2), dtype=bool))
        with self.assertRaises(ValueError):
            pixel_photocenters(cube, np.ones((2, 2), dtype=int))
        _, _, valid = pixel_photocenters(
            np.zeros((3, 2, 2)), np.ones((2, 2), dtype=bool)
        )
        self.assertFalse(np.any(valid))

    def test_background_uses_only_selected_pixels_and_requires_finite_values(self):
        cube = np.array([
            [[1.0, 50.0], [2.0, 3.0]],
            [[2.0, np.nan], [4.0, 7.0]],
            [[3.0, 70.0], [9.0, 11.0]],
        ])
        mask = np.array([[True, False], [False, True]])
        bg, valid = background_medians(cube, mask)
        np.testing.assert_array_equal(valid, [True, True, True])
        np.testing.assert_allclose(bg, [2.0, 4.5, 7.0])
        bg, valid = background_medians(cube, np.array([[False, True], [False, True]]))
        self.assertFalse(valid[1])
        self.assertTrue(np.isnan(bg[1]))

    def test_background_requires_mask(self):
        with self.assertRaises(ValueError):
            background_medians(np.ones((5, 2, 2)), np.zeros((2, 2), dtype=bool))

    def test_pearson_and_shift_control(self):
        rng = np.random.default_rng(4242)
        values = rng.normal(size=180)
        self.assertAlmostEqual(correlation(values, values), 1.0, places=12)
        self.assertLess(abs(correlation(values, np.roll(values, SHIFT))), 0.25)
        self.assertIsNone(correlation(values[:30], values[:30]))
        self.assertIsNone(correlation(np.ones(180), values))

    def test_step_difference_uses_only_adjacent_valid_cadences(self):
        rng = np.random.default_rng(7788)
        stepsx = rng.normal(size=179)
        stepsy = rng.normal(size=179)
        cx = np.r_[0.0, np.cumsum(stepsx)]
        cy = np.r_[0.0, np.cumsum(stepsy)]
        ids = np.arange(180, dtype=int)
        q = np.zeros(180, dtype=int)
        valid = np.ones(180, dtype=bool)
        positions = summarize_movement(
            ids, q, ids.astype(float), cx, cy, valid, cx.copy(), cy.copy()
        )
        self.assertEqual(positions["eligible_consecutive_pairs"], 179)
        self.assertAlmostEqual(positions["x"]["r_zero_lag"], 1.0, places=12)
        self.assertAlmostEqual(positions["y"]["r_zero_lag"], 1.0, places=12)
        background = {
            "QUALITY_ZERO": {"finite_background_rows": 180, "median_estimated_background": 1.0},
            "BIT_13_SCATTERED_LIGHT": {"finite_background_rows": 40, "median_estimated_background": 2.0},
            "bit13_minus_quality_zero_median": 1.0,
        }
        v = verdicts(positions, background)
        self.assertEqual(v["H1_x_movement_association"], "SUPPORTED_IN_SELECTED_PRODUCT")
        self.assertEqual(v["H2_y_movement_association"], "SUPPORTED_IN_SELECTED_PRODUCT")
        self.assertEqual(v["H3_background_flag_selection"], "SUPPORTED_IN_SELECTED_PRODUCT")

        q[20] = 32
        ids[90:] += 4
        positions = summarize_movement(
            ids, q, ids.astype(float), cx, cy, valid, cx, cy
        )
        self.assertEqual(positions["eligible_consecutive_pairs"], 176)

    def test_quality_13_background_comparison_is_not_labeling(self):
        q = np.zeros(180, dtype=np.int32)
        q[100:140] = 4096
        q[140:150] = 32
        q[150:] = 4096 | 32
        bg = np.where((q & 4096) != 0, 20.0, 2.0)
        finite = np.ones(180, dtype=bool)
        finite[105] = False
        out = summarize_background(bg, finite, q)
        self.assertEqual(out["QUALITY_ZERO"]["total_rows"], 100)
        self.assertEqual(out["BIT_13_SCATTERED_LIGHT"]["total_rows"], 70)
        self.assertEqual(out["BIT_13_SCATTERED_LIGHT"]["finite_background_rows"], 69)
        self.assertEqual(out["BIT_6_DESATURATION"]["total_rows"], 40)
        self.assertAlmostEqual(out["bit13_minus_quality_zero_median"], 18.0)

    def test_non_evaluable_and_negative_hypotheses(self):
        movement = {
            "eligible_consecutive_pairs": 99,
            "x": {"r_zero_lag": None, "r_shift24": None},
            "y": {"r_zero_lag": 0.1, "r_shift24": 0.02},
        }
        background = {
            "QUALITY_ZERO": {"finite_background_rows": 99, "median_estimated_background": 1.0},
            "BIT_13_SCATTERED_LIGHT": {"finite_background_rows": 29, "median_estimated_background": 2.0},
            "bit13_minus_quality_zero_median": 1.0,
        }
        out = verdicts(movement, background)
        self.assertTrue(all(v == "NOT_EVALUABLE" for v in out.values()))
        movement["eligible_consecutive_pairs"] = 120
        movement["x"] = {"r_zero_lag": 0.15, "r_shift24": 0.01}
        movement["y"] = {"r_zero_lag": -0.8, "r_shift24": -0.75}
        background["QUALITY_ZERO"]["finite_background_rows"] = 110
        background["BIT_13_SCATTERED_LIGHT"]["finite_background_rows"] = 35
        background["bit13_minus_quality_zero_median"] = -1.0
        out = verdicts(movement, background)
        self.assertTrue(all(v == "NOT_SUPPORTED_IN_SELECTED_PRODUCT" for v in out.values()))

    def test_payload_hash_deterministic(self):
        self.assertEqual(
            digest({"z": 1, "a": 2}),
            hashlib.sha256(b'{"a":2,"z":1}').hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
