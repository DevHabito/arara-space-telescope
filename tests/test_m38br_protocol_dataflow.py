"""P0.2 counterfactual input-provenance diagnostics without science outcomes."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))

import observable_candidate as candidate  # noqa: E402
from observed_preprocessing import score_observed_stars  # noqa: E402
from provenance_contract import historical_geometry_findings  # noqa: E402


class ProtocolDataflowAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(20261103)
        self.observed = rng.normal(size=(2, 9, 180))
        self.residual = rng.normal(size=(2, 180))
        self.reference = rng.normal(size=(2, 180))
        self.short_cfg = candidate.archived.Config(endpoint_start=81, endpoint_stop=83)

    def test_historical_default_geometry_has_no_drift_findings(self):
        self.assertEqual(
            historical_geometry_findings(candidate.archived.Config()), ()
        )

    def test_short_fixture_is_explicitly_off_historical_protocol(self):
        findings = historical_geometry_findings(self.short_cfg)
        self.assertTrue(any(x.startswith("GEOMETRY_DRIFT:endpoint_stop:") for x in findings))

    def test_altered_hinge_candidate_bounds_are_detected(self):
        changed = replace(candidate.archived.Config(), candidate_onset_high=119)
        findings = historical_geometry_findings(changed)
        self.assertTrue(any("candidate_onset_high" in x for x in findings))

    def test_selection_split_changes_are_detected(self):
        changed = replace(candidate.archived.Config(), selection_start=51)
        self.assertTrue(any("selection_start" in x for x in historical_geometry_findings(changed)))

    def test_changed_baseline_is_not_called_historical_geometry(self):
        self.assertTrue(any(
            x.startswith("BASELINE_DRIFT:") for x in
            historical_geometry_findings(candidate.archived.Config(), baseline_n=49)
        ))

    def test_low_level_candidate_accepts_partial_endpoint_grid(self):
        result = candidate.score_observation_only(
            self.residual, self.reference,
            {"residual_phi": np.array([0.2, 0.4])}, self.short_cfg
        )
        self.assertEqual(result["grid_score_grid"].shape, (2, 3))
        # Permissive diagnostic fixture != an immutable prospective run.
        self.assertNotEqual(historical_geometry_findings(self.short_cfg), ())

    def test_hidden_metadata_added_to_params_is_ignored_at_score_boundary(self):
        fitted = {"residual_phi": np.array([0.2, 0.4])}
        baseline = candidate.score_observation_only(
            self.residual, self.reference, fitted, self.short_cfg
        )
        enriched = dict(fitted)
        enriched.update({
            "true_onset": np.array([80, 110]),
            "true_duration": np.array([24, 60]),
            "true_latent_u": np.array([0.0, 1.0]),
            "true_shape_index": np.array([0, 3]),
            "raw_true": self.residual.copy(),
            "virtual_negative_label": np.array([1, 0]),
        })
        repeat = candidate.score_observation_only(
            self.residual.copy(), self.reference.copy(), enriched, self.short_cfg
        )
        self.assertEqual(set(baseline), set(repeat))
        for key in baseline:
            np.testing.assert_array_equal(baseline[key], repeat[key])

    def test_direct_supplied_phi_changes_the_template_calculation(self):
        original = candidate.archived.m37.projected_scores_hypotheses
        templates: list[list[np.ndarray]] = [[], []]
        for i, phi in enumerate((0.0, 0.8)):
            def recorder(residual, hypotheses, reference):
                templates[i].append(hypotheses.copy())
                return original(residual, hypotheses, reference)

            with patch.object(
                candidate.archived.m37, "projected_scores_hypotheses",
                side_effect=recorder
            ):
                candidate.score_observation_only(
                    self.residual, self.reference,
                    {"residual_phi": np.full(2, phi)}, self.short_cfg
                )
        self.assertEqual(len(templates[0]), len(templates[1]))
        self.assertGreater(len(templates[0]), 0)
        self.assertTrue(any(
            not np.array_equal(first, second)
            for first, second in zip(templates[0], templates[1])
        ))

    def test_observed_frontend_is_equivariant_under_curve_permutation(self):
        forward = score_observed_stars(self.observed, self.short_cfg)
        reversed_result = score_observed_stars(self.observed[::-1].copy(), self.short_cfg)
        self.assertEqual(set(forward), set(reversed_result))
        for key in forward:
            np.testing.assert_allclose(
                reversed_result[key], forward[key][::-1],
                rtol=0, atol=0, equal_nan=True,
            )

    def test_missing_untrusted_phi_fails_without_a_fallback(self):
        with self.assertRaises(KeyError):
            candidate.score_observation_only(
                self.residual, self.reference, {}, self.short_cfg
            )


if __name__ == "__main__":
    unittest.main()
