"""Adversarial pre-outcome provenance checks for M38B-R preprocessing."""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))
from observed_preprocessing import preprocess_observations, score_observed_stars  # noqa: E402
import observable_candidate as candidate  # noqa: E402


class ObservationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(20261103)
        self.observed = self.rng.normal(size=(2, 9, 180))
        self.data_cfg = candidate.archived.m2.Config()
        self.cfg = candidate.archived.Config(endpoint_start=81, endpoint_stop=83)
        self.archive = candidate.archived.m32.m30.m29.sbw_with_reference_nuisance

    def compare_outputs(self, actual, expected):
        np.testing.assert_allclose(actual[0], expected[0], rtol=2e-11, atol=2e-11)
        np.testing.assert_allclose(actual[1], expected[2], rtol=2e-11, atol=2e-11)
        self.assertEqual(set(actual[2]), set(expected[3]))
        for key, value in actual[2].items():
            np.testing.assert_allclose(value, expected[3][key], rtol=2e-11, atol=2e-11)

    def test_observations_only_signature_excludes_oracle_fields(self):
        self.assertEqual(
            tuple(inspect.signature(preprocess_observations).parameters),
            ("stars", "baseline_n"),
        )
        self.assertEqual(
            tuple(inspect.signature(score_observed_stars).parameters),
            ("stars", "cfg", "baseline_n"),
        )

    def test_independent_operational_preprocessing_matches_archived(self):
        truth = self.rng.normal(size=(2, 180))
        self.compare_outputs(
            preprocess_observations(self.observed),
            self.archive(self.observed, truth, self.data_cfg),
        )

    def test_hidden_true_signal_changes_only_archived_diagnostic_output(self):
        zero = np.zeros((2, 180))
        adversarial = self.rng.normal(loc=100.0, scale=30.0, size=(2, 180))
        first = self.archive(self.observed, zero, self.data_cfg)
        altered = self.archive(self.observed, adversarial, self.data_cfg)
        np.testing.assert_array_equal(first[0], altered[0])
        np.testing.assert_array_equal(first[2], altered[2])
        for key in first[3]:
            np.testing.assert_array_equal(first[3][key], altered[3][key])
        self.assertFalse(np.array_equal(first[1], altered[1]))

    def test_no_future_sample_changes_earlier_preprocessing_outputs(self):
        original = preprocess_observations(self.observed)
        changed = self.observed.copy()
        changed[:, :, 110:] += 500.0
        later = preprocess_observations(changed)
        np.testing.assert_array_equal(original[0][:, :110], later[0][:, :110])
        np.testing.assert_array_equal(original[1][:, :110], later[1][:, :110])
        for key in original[2]:
            np.testing.assert_array_equal(original[2][key], later[2][key])

    def test_full_observation_frontend_agrees_with_historical_preprocessor(self):
        direct = score_observed_stars(self.observed, self.cfg)
        archived = self.archive(self.observed, np.zeros((2, 180)), self.data_cfg)
        reference = candidate.score_observation_only(
            archived[0], archived[2], archived[3], self.cfg
        )
        for key, value in direct.items():
            np.testing.assert_allclose(value, reference[key], rtol=2e-10, atol=2e-10)

    def test_full_observation_frontend_is_invariant_to_future_samples(self):
        early = score_observed_stars(self.observed, self.cfg)
        changed = self.observed.copy()
        changed[:, :, 110:] *= -11.0
        repeated = score_observed_stars(changed, self.cfg)
        for key in ("grid_score_grid", "estimated_onset_grid", "hinge_objective_grid"):
            np.testing.assert_array_equal(early[key], repeated[key])

    def test_constant_observations_have_finite_preprocessing(self):
        zeros = np.zeros_like(self.observed)
        observed = preprocess_observations(zeros)
        archived = self.archive(zeros, np.zeros((2, 180)), self.data_cfg)
        self.compare_outputs(observed, archived)
        self.assertTrue(np.all(observed[0] == 0.0))
        self.assertTrue(np.all(observed[1] == 0.0))

    def test_nonfinite_observation_rejected(self):
        broken = self.observed.copy()
        broken[0, 1, 75] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            preprocess_observations(broken)

    def test_nonfinite_intermediate_rejected(self):
        extreme = self.observed * 1e308
        with self.assertRaisesRegex(ValueError, "finite"):
            preprocess_observations(extreme)

    def test_bad_shape_and_baseline_rejected(self):
        for invalid in (
            np.ones((9, 180)),
            np.ones((1, 1, 180)),
            np.ones((0, 9, 180)),
        ):
            with self.subTest(shape=invalid.shape), self.assertRaisesRegex(ValueError, "Expected"):
                preprocess_observations(invalid)
        for length in (0, 2, 180, True, 1.5):
            with self.subTest(baseline=length), self.assertRaisesRegex(ValueError, "Baseline"):
                preprocess_observations(self.observed, baseline_n=length)


if __name__ == "__main__":
    unittest.main()
