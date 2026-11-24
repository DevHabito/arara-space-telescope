"""P0.5 observed-prefix acceptance criteria fixed before the implementation.

No calibration, holdouts, scientific positives/negatives or instrument data.
See experiments/M38B-R/P05_PREFIX_CONTRACT_POLICY.md.
"""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/M38B-R"
sys.path.insert(0, str(EXPERIMENT))

from independent_bank import (  # noqa: E402
    IndependentBankConfig, score_independent_bank,
    score_independent_observed_stars,
)
from observed_prefix import score_observed_prefix  # noqa: E402
from observed_preprocessing import preprocess_observations  # noqa: E402


class ObservedPrefixContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(20261103)
        cls.stars = rng.normal(size=(2, 9, 180)) * 0.1
        cls.stars[:, 0, :] += (
            0.08 * np.maximum(np.arange(180, dtype=np.float64) - 69.0, 0.0)
        )
        cls.full = score_independent_observed_stars(
            cls.stars, IndependentBankConfig()
        )

    def test_prefix_outputs_match_full_batch_columns_exactly(self):
        for endpoint in (81, 83, 110, 179):
            with self.subTest(endpoint=endpoint):
                actual = score_observed_prefix(
                    self.stars[:, :, : endpoint + 1].copy(),
                    endpoint=endpoint,
                )
                self.assertEqual(set(actual), set(self.full))
                for name, values in actual.items():
                    expected = self.full[name][:, endpoint - 81: endpoint - 80]
                    np.testing.assert_array_equal(values, expected)

    def test_future_nonfinite_sample_cannot_block_valid_observed_prefix(self):
        corrupted = self.stars.copy()
        corrupted[:, 4, 130] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            score_independent_observed_stars(
                corrupted, IndependentBankConfig(endpoints=(83,))
            )
        result = score_observed_prefix(
            corrupted[:, :, :84], endpoint=83
        )
        for name, value in result.items():
            np.testing.assert_array_equal(value, self.full[name][:, 2:3])

    def test_missing_baseline_or_endpoint_sample_rejected(self):
        for missing in (25, 83):
            with self.subTest(missing_sample=missing):
                prefix = self.stars[:, :, :84].copy()
                prefix[0, 1, missing] = np.nan
                with self.assertRaisesRegex(ValueError, "finite"):
                    score_observed_prefix(prefix, endpoint=83)

    def test_longer_and_shorter_series_are_rejected_without_padding(self):
        for length in (82, 83, 85, 180):
            with self.subTest(length=length):
                with self.assertRaisesRegex(ValueError, "exactly 84"):
                    score_observed_prefix(
                        self.stars[:, :, :length], endpoint=83
                    )

    def test_bad_endpoints_are_rejected_before_preprocessing(self):
        for bad in (0, 80, 180, -1, True, 81.0, "81", None):
            with self.subTest(endpoint=bad):
                with self.assertRaisesRegex(ValueError, "endpoint"):
                    score_observed_prefix(self.stars, endpoint=bad)

    def test_missing_curve_reference_and_dimensions_rejected(self):
        for values in (
            self.stars[0, :, :84],
            self.stars[:, :1, :84],
            self.stars[:0, :, :84],
        ):
            with self.subTest(shape=values.shape):
                with self.assertRaisesRegex(ValueError, "Expected"):
                    score_observed_prefix(values, endpoint=83)

    def test_constant_prefix_fails_closed_with_undefined_alignment(self):
        zeros = np.zeros((1, 9, 82))
        result = score_observed_prefix(zeros, endpoint=81)
        self.assertTrue(np.isneginf(result["grid_score_grid"]).all())
        self.assertFalse(result["alignment_defined_grid"].any())
        for name in (
            "grid_shape_index_grid",
            "grid_duration_grid",
            "grid_latent_index_grid",
        ):
            np.testing.assert_array_equal(result[name], [[-1]])

    def test_permuting_curves_permutates_outputs_only(self):
        raw = self.stars[:, :, :84].copy()
        before = score_observed_prefix(raw, endpoint=83)
        after = score_observed_prefix(raw[::-1].copy(), endpoint=83)
        for name in before:
            np.testing.assert_array_equal(after[name], before[name][::-1])

    def test_public_interface_and_independent_import_boundary(self):
        signature = inspect.signature(score_observed_prefix)
        self.assertEqual(tuple(signature.parameters), ("stars", "endpoint"))
        self.assertEqual(
            signature.parameters["endpoint"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        source = (EXPERIMENT / "observed_prefix.py").read_text(encoding="utf-8")
        for prohibited in ("observable_candidate", "arara_m38b", "simulated_true_onset"):
            self.assertNotIn(prohibited, source)

    def test_prefix_input_is_not_modified(self):
        values = self.stars[:, :, :84].copy()
        initial = values.copy()
        score_observed_prefix(values, endpoint=83)
        np.testing.assert_array_equal(values, initial)

    def test_independent_bank_still_rejects_insufficient_residual(self):
        residual, reference, fitted = preprocess_observations(
            self.stars[:, :, :84]
        )
        with self.assertRaisesRegex(ValueError, "last configured endpoint"):
            score_independent_bank(
                residual[:, :81], reference[:, :81],
                fitted["residual_phi"],
                IndependentBankConfig(endpoints=(83,)),
            )
        with self.assertRaisesRegex(ValueError, "last configured endpoint"):
            score_independent_bank(
                residual, reference, fitted["residual_phi"],
                IndependentBankConfig(),
            )


if __name__ == "__main__":
    unittest.main()
