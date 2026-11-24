"""P0.3 predeclared independent-bank numerical and provenance checks.

The stable-comparison tolerance is stated in
experiments/M38B-R/INDEPENDENT_BANK_COMPARISON_POLICY.md before code execution.
No scientific positives, negative-family calibration or holdouts are generated.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BANK_DIR = ROOT / "experiments/M38B-R"
sys.path.insert(0, str(BANK_DIR))
import independent_bank as independent  # noqa: E402
import observable_candidate as archived_candidate  # noqa: E402
from observed_preprocessing import preprocess_observations  # noqa: E402

RTOL = 1e-9
ATOL = 1e-9
SAFE_MARGIN = 1e-7


class IndependentBankAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(20261103)
        time = np.arange(180)
        cls.residual = (
            rng.normal(size=(2, 180)) * 0.02
            + np.maximum(time - 70, 0)[None, :] * 0.2
        )
        cls.reference = rng.normal(size=(2, 180))
        cls.phi = np.array([0.1, 0.4])
        cls.config = replace(
            independent.IndependentBankConfig(), endpoints=(81, 82, 83)
        )
        cls.archive_cfg = archived_candidate.archived.Config(
            endpoint_start=81, endpoint_stop=83
        )

    def test_bank_count_and_explicit_tie_order(self):
        order = independent.BANK_ORDER
        self.assertEqual(len(order), 592)
        self.assertEqual(len(set(order)), 592)
        self.assertEqual(order[0], (0, 24, 0))
        self.assertEqual(order, tuple(sorted(order)))
        self.assertEqual(sum(shape == 0 for _, _, shape in order), 37)
        self.assertEqual(len(independent.IndependentBankConfig().endpoints), 99)
        self.assertEqual(len(order) * 99, 58608)

    def test_source_module_has_no_historical_scorer_import(self):
        src = (BANK_DIR / "independent_bank.py").read_text(encoding="utf-8")
        import re
        self.assertIsNone(re.search(
            r"^\s*(?:from|import)\s+(?:arara_|observable_candidate)",
            src, flags=re.MULTILINE,
        ))

    def test_well_conditioned_max_scores_match_existing_candidate(self):
        alt = independent.score_independent_bank(
            self.residual, self.reference, self.phi, self.config
        )
        old = archived_candidate.score_observation_only(
            self.residual, self.reference,
            {"residual_phi": self.phi}, self.archive_cfg
        )
        self.assertTrue(alt["alignment_defined_grid"].all())
        np.testing.assert_allclose(
            alt["grid_score_grid"], old["grid_score_grid"],
            rtol=RTOL, atol=ATOL,
        )
        confident = alt["winner_margin_grid"] > SAFE_MARGIN
        for key in (
            "grid_shape_index_grid", "grid_duration_grid",
            "grid_latent_index_grid",
        ):
            np.testing.assert_array_equal(alt[key][confident], old[key][confident])

    def test_entire_99_endpoint_bank_matches_on_unlabelled_curve(self):
        cfg = independent.IndependentBankConfig()
        result = independent.score_independent_bank(
            self.residual[:1], self.reference[:1], self.phi[:1], cfg
        )
        archive = archived_candidate.score_observation_only(
            self.residual[:1], self.reference[:1],
            {"residual_phi": self.phi[:1]},
            archived_candidate.archived.Config(),
        )
        mask = result["alignment_defined_grid"]
        self.assertEqual(result["grid_score_grid"].shape, (1, 99))
        self.assertTrue(mask.all())
        np.testing.assert_allclose(
            result["grid_score_grid"], archive["grid_score_grid"],
            rtol=RTOL, atol=ATOL,
        )
        confident = mask & (result["winner_margin_grid"] > SAFE_MARGIN)
        for key in (
            "grid_shape_index_grid", "grid_duration_grid",
            "grid_latent_index_grid",
        ):
            np.testing.assert_array_equal(
                result[key][confident], archive[key][confident]
            )

    def test_undefined_onset_fails_closed_and_does_not_report_shape(self):
        zeros = np.zeros((1, 180))
        cfg = self.config
        result = independent.score_independent_bank(
            zeros, zeros, np.array([0.0]), cfg
        )
        self.assertFalse(result["alignment_defined_grid"].any())
        self.assertTrue(np.isneginf(result["grid_score_grid"]).all())
        for key in (
            "grid_shape_index_grid", "grid_duration_grid",
            "grid_latent_index_grid",
        ):
            np.testing.assert_array_equal(
                result[key], np.full((1, 3), -1)
            )
        # Existing prototype is a different diagnostic: it does not
        # mark undefined alignment as a fail-closed score.

    def test_future_only_change_preserves_all_early_outputs(self):
        rng = np.random.default_rng(20261104)
        stars = rng.normal(size=(2, 9, 180))
        altered = stars.copy()
        altered[:, :, 110:] = rng.normal(
            loc=100.0, scale=30.0, size=altered[:, :, 110:].shape
        )
        first = independent.score_independent_observed_stars(stars, self.config)
        later = independent.score_independent_observed_stars(altered, self.config)
        for name in first:
            np.testing.assert_array_equal(first[name], later[name])

    def test_future_nonfinite_samples_block_offline_validation(self):
        # This documents a remaining *online* causality limitation. With a
        # fixed, valid past, changing an unseen future sample to NaN makes
        # the whole-array preflight reject the observation.
        rng = np.random.default_rng(20261106)
        stars = rng.normal(size=(1, 9, 180))
        observed = independent.score_independent_observed_stars(
            stars, self.config
        )
        self.assertEqual(observed["grid_score_grid"].shape, (1, 3))
        changed = stars.copy()
        changed[0, 4, 130] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            independent.score_independent_observed_stars(
                changed, self.config
            )

        residual = self.residual.copy()
        residual[0, 130] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            independent.score_independent_bank(
                residual, self.reference, self.phi, self.config
            )

    def test_no_oracle_input_at_public_entrypoint(self):
        import inspect
        self.assertEqual(
            tuple(inspect.signature(
                independent.score_independent_observed_stars
            ).parameters), ("stars", "cfg")
        )
        self.assertEqual(
            tuple(inspect.signature(independent.score_independent_bank).parameters),
            ("residual", "processed_reference", "residual_phi", "cfg")
        )

    def test_rejects_invalid_phi_and_geometry(self):
        with self.assertRaisesRegex(ValueError, "coefficient"):
            independent.score_independent_bank(
                self.residual, self.reference, np.array([np.nan, 0.1]), self.config
            )
        with self.assertRaisesRegex(ValueError, "0..0.8"):
            independent.score_independent_bank(
                self.residual, self.reference, np.array([0.9, 0.1]), self.config
            )
        with self.assertRaisesRegex(ValueError, "geometry"):
            replace(self.config, guard_length=0)
        with self.assertRaisesRegex(ValueError, "increasing"):
            replace(self.config, endpoints=(83, 82))

    def test_rejects_finite_observation_overflow_during_projection(self):
        huge = np.zeros_like(self.reference)
        huge[:, 81:84] = 1e200
        with self.assertRaisesRegex(ValueError, "Nonfinite reference energy"):
            independent.score_independent_bank(
                self.residual, huge, self.phi, self.config
            )


if __name__ == "__main__":
    unittest.main()
