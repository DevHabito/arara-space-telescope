"""P0.4 diagnostic tests fixed before execution in P04_NUMERICAL_AUDIT_POLICY.md.

Analytic vectors are not simulated astronomical positives or negatives.
The archived scorer is imported *only* by one comparison diagnostic.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from pathlib import Path
import json
import math
import sys
import unittest
import warnings

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))

from independent_projection import score_projected  # noqa: E402
from numerical_quality import classify_nonfinite_positions  # noqa: E402
import observable_candidate as existing_candidate  # noqa: E402


def witness(delta: float = 1.2e-6, scale: float = 1.0):
    residual = np.array([[[1., -1., 1., -1., 1., -1., 1., -1.]]])
    reference = np.ones((1, 1, 8)) * scale
    templates = reference[:, None, :, :].copy()
    templates[0, 0, 0, 0] += scale * delta
    return residual, templates, reference


class NumericalQualityAuditTests(unittest.TestCase):
    def test_near_parallel_score_against_exact_geometry_and_log_both_formulas(self):
        target, templates, reference = witness()
        independent, diag = score_projected(target, templates, reference)
        historical, _ = existing_candidate.archived.m37.projected_scores_hypotheses(
            target, templates, reference
        )

        with localcontext() as ctx:
            ctx.prec = 70
            represented_delta = Decimal.from_float(float(templates[0, 0, 0, 0])) - 1
            analytic_energy = Decimal(7) * represented_delta**2 / Decimal(8)
            analytic = (Decimal(8) / Decimal(7)).sqrt()
            self.assertGreater(analytic_energy, Decimal("1e-12"))
            analytic_float = float(analytic)

        self.assertFalse(bool(diag["template_degenerate"][0, 0, 0]))
        np.testing.assert_allclose(
            independent, np.array([[[analytic_float]]]), rtol=0, atol=1e-9
        )
        self.assertTrue(np.isfinite(historical).all())
        # The archive's subtractive formula has no near-singular equivalence
        # requirement: report differences, never loosen the frozen policy.
        print("P04_NEAR_PARALLEL_WITNESS=" + json.dumps({
            "analytic_score": analytic_float,
            "independent_score": float(independent[0, 0, 0]),
            "archived_score": float(historical[0, 0, 0]),
            "independent_absolute_error": abs(
                float(independent[0, 0, 0]) - analytic_float
            ),
            "archived_absolute_error": abs(
                float(historical[0, 0, 0]) - analytic_float
            ),
            "analytic_projected_energy_from_binary64_input": float(analytic_energy),
            "calibration_executed": False,
        }, sort_keys=True, allow_nan=False))

    def test_absolute_floor_breaks_template_reference_scaling_near_singularity(self):
        original, templ, ref = witness()
        unscaled, unscaled_info = score_projected(original, templ, ref)
        low_target, low_template, low_reference = witness(scale=0.1)
        suppressed, low_info = score_projected(
            low_target, low_template, low_reference
        )
        high_target, high_template, high_reference = witness(scale=2.0)
        rescaled, high_info = score_projected(
            high_target, high_template, high_reference
        )

        self.assertFalse(bool(unscaled_info["template_degenerate"][0, 0, 0]))
        self.assertTrue(bool(low_info["template_degenerate"][0, 0, 0]))
        self.assertFalse(bool(high_info["template_degenerate"][0, 0, 0]))
        self.assertEqual(float(suppressed[0, 0, 0]), 0.0)
        self.assertGreater(float(unscaled[0, 0, 0]), 0.0)
        np.testing.assert_allclose(unscaled, rescaled, rtol=0, atol=1e-9)

    def test_reference_cutoff_is_a_numerical_branch_not_a_physical_claim(self):
        ones = np.ones((1, 1, 8))
        template = ones[:, None, :, :].copy()
        weak = ones * 1e-7
        strong = ones * 1e-6
        weak_score, weak_diagnostics = score_projected(ones, template, weak)
        strong_score, strong_diagnostics = score_projected(ones, template, strong)
        self.assertTrue(bool(weak_diagnostics["reference_degenerate"][0, 0]))
        self.assertFalse(bool(strong_diagnostics["reference_degenerate"][0, 0]))
        self.assertAlmostEqual(float(weak_score[0, 0, 0]), math.sqrt(8), delta=1e-12)
        self.assertEqual(float(strong_score[0, 0, 0]), 0.0)
        self.assertTrue(bool(strong_diagnostics["template_degenerate"][0, 0, 0]))

    def test_extreme_finite_reference_is_rejected_for_nonfinite_energy(self):
        residual, templates, reference = witness()
        extreme = np.full(reference.shape, 1e200, dtype=np.float64)
        self.assertTrue(np.isfinite(extreme).all())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            with self.assertRaisesRegex(ValueError, "Nonfinite reference energy"):
                score_projected(residual, templates, extreme)

    def test_quality_location_classifies_missing_prefix_or_future_only(self):
        stars = np.zeros((2, 9, 180))
        stars[0, 2, 25] = np.nan
        stars[1, 7, 82] = np.inf
        before = stars.copy()
        flags = classify_nonfinite_positions(stars, (81, 83))
        np.testing.assert_array_equal(
            flags["prefix_has_nonfinite_grid"],
            np.array([[True, True], [False, True]]),
        )
        np.testing.assert_array_equal(
            flags["future_has_nonfinite_grid"],
            np.array([[False, False], [True, False]]),
        )
        np.testing.assert_array_equal(
            flags["future_only_nonfinite_grid"],
            np.array([[False, False], [True, False]]),
        )
        np.testing.assert_array_equal(flags["whole_series_finite"], [False, False])
        # NaN-preserving equality checks the classifier did not mutate data.
        np.testing.assert_array_equal(stars, before, strict=True)

    def test_future_only_missingness_does_not_become_a_fake_valid_observation(self):
        stars = np.zeros((1, 9, 180))
        stars[0, 0, 130] = np.nan
        flags = classify_nonfinite_positions(stars, (81, 83, 130, 179))
        np.testing.assert_array_equal(
            flags["prefix_has_nonfinite_grid"], [[False, False, True, True]]
        )
        np.testing.assert_array_equal(
            flags["future_only_nonfinite_grid"], [[True, True, False, False]]
        )
        np.testing.assert_array_equal(flags["whole_series_finite"], [False])
        # This is a classifier, not permission to bypass the existing
        # whole-series finiteness check in the offline preprocessor.

    def test_quality_classifier_keeps_curves_independent_and_accepts_finite(self):
        stars = np.zeros((2, 9, 180))
        flags = classify_nonfinite_positions(stars, (81, 179))
        self.assertFalse(flags["prefix_has_nonfinite_grid"].any())
        self.assertFalse(flags["future_only_nonfinite_grid"].any())
        self.assertTrue(flags["whole_series_finite"].all())
        stars[1, 4, 179] = np.nan
        flags = classify_nonfinite_positions(stars, (81, 179))
        self.assertFalse(flags["prefix_has_nonfinite_grid"][0].any())
        np.testing.assert_array_equal(flags["prefix_has_nonfinite_grid"][1], [False, True])
        np.testing.assert_array_equal(flags["future_only_nonfinite_grid"][1], [True, False])

    def test_quality_classifier_fails_closed_on_invalid_geometry(self):
        clean = np.zeros((1, 9, 180))
        for invalid in ((), (83, 81), (81, 81), (180,), (-1,), (81.0,), (True,)):
            with self.subTest(endpoints=invalid), self.assertRaisesRegex(
                ValueError, "increasing"
            ):
                classify_nonfinite_positions(clean, invalid)
        with self.assertRaisesRegex(ValueError, "nonempty"):
            classify_nonfinite_positions(clean[0], (81,))

    def test_quality_classifier_has_no_archive_or_scorer_dependency(self):
        path = ROOT / "experiments/M38B-R/numerical_quality.py"
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("observable_candidate", source)
        self.assertNotIn("arara_m38b", source)


if __name__ == "__main__":
    unittest.main()
