"""Numerical independence, degeneracy and metamorphic projection audit.

The independent scorer imports no archived scorer. The test harness imports
archived M37 only as a baseline, and does not generate scientific outcomes.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

PROJECT = Path(__file__).resolve().parents[1] / "experiments/M38B-R"
sys.path.insert(0, str(PROJECT))
from independent_projection import score_projected  # noqa: E402
import observable_candidate as candidate  # noqa: E402


class IndependentProjectionTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(20261021)
        self.residual = rng.normal(size=(3, 4, 8))
        self.templates = rng.normal(size=(3, 5, 4, 8))
        self.reference = rng.normal(size=(3, 4, 8))

    def test_well_conditioned_matches_actual_archive(self):
        observed, diagnostics = score_projected(
            self.residual, self.templates, self.reference
        )
        original, baseline = candidate.archived.m37.projected_scores_hypotheses(
            self.residual, self.templates, self.reference
        )
        np.testing.assert_allclose(observed, original, rtol=1e-11, atol=1e-11)
        np.testing.assert_allclose(
            diagnostics["energy_retention"], baseline["energy_retention"],
            rtol=1e-11, atol=1e-11
        )
        np.testing.assert_array_equal(
            diagnostics["template_degenerate"], baseline["template_degenerate"]
        )

    def test_zero_reference_reduces_to_unprojected_score(self):
        actual, details = score_projected(
            self.residual, self.templates, np.zeros_like(self.reference)
        )
        numerator = np.sum(
            self.templates * self.residual[:, None, :, :], axis=-1
        )
        norm = np.sqrt(np.sum(self.templates ** 2, axis=-1))
        np.testing.assert_allclose(actual, numerator / norm, atol=1e-12)
        self.assertTrue(np.all(details["reference_degenerate"]))

    def test_zero_template_scores_zero(self):
        actual, details = score_projected(
            self.residual, np.zeros_like(self.templates), self.reference
        )
        self.assertTrue(np.all(actual == 0.0))
        self.assertTrue(np.all(details["template_degenerate"]))

    def test_parallel_template_is_degenerate(self):
        same = np.broadcast_to(
            self.reference[:, None, :, :], self.templates.shape
        ).copy()
        actual, details = score_projected(self.residual, same, self.reference)
        self.assertTrue(np.all(actual == 0.0))
        self.assertTrue(np.all(details["template_degenerate"]))

    def test_zero_energy_reference_threshold_matches_archive(self):
        small_reference = np.full_like(self.reference, 1e-8)
        actual, details = score_projected(
            self.residual, self.templates, small_reference
        )
        original, _ = candidate.archived.m37.projected_scores_hypotheses(
            self.residual, self.templates, small_reference
        )
        np.testing.assert_allclose(actual, original, rtol=1e-12, atol=1e-12)
        self.assertTrue(np.all(details["reference_degenerate"]))

    def test_rejects_nonfinite_inputs(self):
        self.residual[0, 0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            score_projected(self.residual, self.templates, self.reference)

    def test_rejects_wrong_dimensions(self):
        with self.assertRaisesRegex(ValueError, "3D residuals"):
            score_projected(self.residual[0], self.templates, self.reference)

    def test_rejects_wrong_shapes(self):
        with self.assertRaisesRegex(ValueError, "Mismatched"):
            score_projected(self.residual, self.templates, self.reference[..., :-1])

    def test_rejects_empty_arrays(self):
        with self.assertRaisesRegex(ValueError, "Empty"):
            score_projected(
                np.zeros((0, 2, 8)), np.zeros((0, 3, 2, 8)),
                np.zeros((0, 2, 8))
            )

    def test_positive_scale_of_target_scales_score(self):
        scores, _ = score_projected(
            self.residual, self.templates, self.reference
        )
        scaled, _ = score_projected(
            2.3 * self.residual, self.templates, self.reference
        )
        np.testing.assert_allclose(scaled, 2.3 * scores, rtol=1e-11, atol=1e-11)

    def test_projected_template_is_orthogonal_when_well_conditioned(self):
        energy = np.sum(self.reference * self.reference, axis=-1)
        dot = np.sum(
            self.templates * self.reference[:, None, :, :], axis=-1
        )
        projected = self.templates - (
            dot / energy[:, None, :]
        )[..., None] * self.reference[:, None, :, :]
        np.testing.assert_allclose(
            np.sum(projected * self.reference[:, None, :, :], axis=-1),
            0.0, rtol=0, atol=1e-14
        )

    def test_near_parallel_diagnostic_does_not_assume_agreement(self):
        residual = np.array([[[1., -1., 1., -1., 1., -1., 1., -1.]]])
        reference = np.ones((1, 1, 8))
        template = reference[:, None, :, :].copy()
        template[0, 0, 0, 0] += 1.2e-6
        new, _ = score_projected(residual, template, reference)
        old, _ = candidate.archived.m37.projected_scores_hypotheses(
            residual, template, reference
        )
        self.assertTrue(np.all(np.isfinite(new)))
        self.assertTrue(np.all(np.isfinite(old)))
        # The diagnostic script reports numerical differences without
        # declaring the historically calculated score scientifically invalid.
        self.assertEqual(new.shape, old.shape)

    def test_full_candidate_using_independent_projector_matches_stable_fixture(self):
        cfg = candidate.archived.Config(endpoint_start=81, endpoint_stop=83)
        rng = np.random.default_rng(412)
        residual = rng.normal(size=(2, 180))
        reference = rng.normal(size=(2, 180))
        params = {"residual_phi": np.array([0.1, 0.4])}
        baseline = candidate.score_observation_only(
            residual, reference, params, cfg
        )
        with patch.object(
            candidate.archived.m37, "projected_scores_hypotheses",
            side_effect=score_projected
        ):
            independently_scored = candidate.score_observation_only(
                residual, reference, params, cfg
            )
        np.testing.assert_allclose(
            baseline["grid_score_grid"],
            independently_scored["grid_score_grid"],
            rtol=1e-10, atol=1e-10
        )
        np.testing.assert_array_equal(
            baseline["grid_shape_index_grid"],
            independently_scored["grid_shape_index_grid"]
        )

    def test_rejects_finite_inputs_that_overflow_energy(self):
        huge = np.full_like(self.reference, 1e200)
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            score_projected(self.residual, self.templates, huge)


if __name__ == "__main__":
    unittest.main()
