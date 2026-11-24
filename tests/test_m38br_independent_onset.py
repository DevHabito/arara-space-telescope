"""Independent mathematical checks of the archived hinge-onset estimator.

No calibration or holdout cases are generated or inspected.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))
from independent_onset import estimate_direct_hinge  # noqa: E402
import observable_candidate as candidate  # noqa: E402


class IndependentOnsetAuditTests(unittest.TestCase):
    def setUp(self):
        self.cfg = candidate.archived.Config()
        self.endpoints = np.array([81, 90, 120, 179], dtype=np.int16)

    def test_direct_reference_agrees_with_archived_prefix_sums_on_noise(self):
        rng = np.random.default_rng(20261103)
        observed = rng.normal(size=(4, 180))
        direct_onset, direct_score = estimate_direct_hinge(observed, self.endpoints)
        original_onset, original_score = candidate.archived.m34.estimate_onset_grid(
            observed, self.endpoints, self.cfg
        )
        np.testing.assert_array_equal(direct_onset, original_onset)
        np.testing.assert_allclose(direct_score, original_score, rtol=1e-8, atol=1e-8)

    def test_direct_reference_agrees_on_unlabelled_curved_fixture(self):
        rng = np.random.default_rng(20261104)
        times = np.arange(180, dtype=np.float64)
        observed = rng.normal(size=(2, 180)) + np.maximum(0.0, times - 84.0)[None, :] * 0.02
        direct_onset, direct_score = estimate_direct_hinge(observed, self.endpoints)
        original_onset, original_score = candidate.archived.m34.estimate_onset_grid(
            observed, self.endpoints, self.cfg
        )
        np.testing.assert_array_equal(direct_onset, original_onset)
        np.testing.assert_allclose(direct_score, original_score, rtol=1e-8, atol=1e-8)

    def test_zero_curve_exposes_undefined_hinge_objective(self):
        observed = np.zeros((1, 180), dtype=np.float64)
        direct_onset, direct_score = estimate_direct_hinge(observed, self.endpoints)
        original_onset, original_score = candidate.archived.m34.estimate_onset_grid(
            observed, self.endpoints, self.cfg
        )
        np.testing.assert_array_equal(direct_onset, original_onset)
        np.testing.assert_array_equal(direct_onset, np.full((1, 4), 70))
        self.assertTrue(np.all(np.isneginf(direct_score)))
        self.assertTrue(np.all(np.isneginf(original_score)))
        self.assertFalse(np.all(np.isfinite(original_score)))

    def test_future_only_data_does_not_change_early_estimates(self):
        rng = np.random.default_rng(20261105)
        observed = rng.normal(size=(2, 180))
        early = np.array([81, 90, 120], dtype=np.int16)
        altered = observed.copy()
        altered[:, 130:] += 500.0
        for estimator in (
            lambda x: estimate_direct_hinge(x, early),
            lambda x: candidate.archived.m34.estimate_onset_grid(x, early, self.cfg),
        ):
            before_onset, before_score = estimator(observed)
            after_onset, after_score = estimator(altered)
            np.testing.assert_array_equal(before_onset, after_onset)
            np.testing.assert_array_equal(before_score, after_score)

    def test_direct_reference_rejects_nonfinite_observations(self):
        observed = np.zeros((1, 180))
        observed[0, 55] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            estimate_direct_hinge(observed, self.endpoints)


if __name__ == "__main__":
    unittest.main()
