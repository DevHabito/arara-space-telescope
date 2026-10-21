"""Uncalibrated observation-only candidate: differential and adverse tests."""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))
import observable_candidate as prototype  # noqa: E402

archived = prototype.archived


def fixture(endpoint_start: int = 179, endpoint_stop: int = 179):
    cfg = archived.Config(endpoint_start=endpoint_start, endpoint_stop=endpoint_stop)
    residual = np.zeros((1, 180), dtype=np.float64)
    residual[0, 171:180] = np.linspace(1.0, 2.0, 9)
    reference = np.zeros_like(residual)
    params = {"residual_phi": np.array([0.2], dtype=np.float64)}
    estimated = np.full((1, len(cfg.endpoint_grid)), 80, dtype=np.int16)
    objective = np.zeros_like(estimated, dtype=np.float64)
    return cfg, residual, reference, params, estimated, objective


class ObservableCandidateTests(unittest.TestCase):
    def test_public_interface_has_no_truth_inputs(self):
        arguments = tuple(inspect.signature(prototype.score_observation_only).parameters)
        self.assertEqual(
            arguments,
            ("residual", "processed_reference", "params", "cfg"),
        )

    def test_fixed_observations_match_archived_candidate_when_mask_is_valid(self):
        cfg, residual, reference, params, estimated, objective = fixture()
        with patch.object(
            archived.m34, "estimate_onset_grid", return_value=(estimated, objective)
        ):
            new = prototype.score_observation_only(residual, reference, params, cfg)
            old = archived.score_latent_grid_bank(
                residual=residual,
                onset=np.array([80], dtype=np.int16),
                true_latent_u=np.array([0.5]),
                template_scale=np.ones(1),
                true_shape_index=np.zeros(1, dtype=np.int8),
                true_duration=np.array([30], dtype=np.int16),
                processed_reference=reference,
                params={"residual_phi": params["residual_phi"],
                        "target_scale": np.ones(1),
                        "residual_scale": np.ones(1)},
                cfg=cfg,
            )
        np.testing.assert_allclose(
            new["grid_score_grid"], old["grid_score_grid"], rtol=1e-10, atol=1e-10
        )
        self.assertEqual(new["grid_shape_index_grid"].shape, (1, 1))

    def test_archived_leak_fixture_no_longer_depends_on_true_onset(self):
        cfg, residual, reference, params, estimated, objective = fixture()
        with patch.object(
            archived.m34, "estimate_onset_grid", return_value=(estimated, objective)
        ):
            new = prototype.score_observation_only(residual, reference, params, cfg)
            leaked = archived.score_latent_grid_bank(
                residual, np.array([110], dtype=np.int16),
                np.array([0.5]), np.ones(1),
                np.zeros(1, dtype=np.int8), np.array([30]),
                reference,
                {"residual_phi": params["residual_phi"],
                 "target_scale": np.ones(1),
                 "residual_scale": np.ones(1)},
                cfg,
            )
            repeat = prototype.score_observation_only(
                residual.copy(), reference.copy(), dict(params), cfg
            )
        np.testing.assert_array_equal(new["grid_score_grid"], repeat["grid_score_grid"])
        self.assertGreater(float(new["grid_score_grid"][0, 0]), 0.0)
        self.assertEqual(float(leaked["grid_score_grid"][0, 0]), 0.0)

    def test_template_equations_match_reference_on_interior_samples(self):
        phase = np.linspace(0, 1, 9)[None, None, None, :]
        latent = np.array([0.0, 0.25, 0.75, 1.0])[:, None, None, None]
        for shape in prototype.SHAPES:
            with self.subTest(shape=shape):
                observed = prototype._shape_template(shape, phase, latent)
                expected = archived._shape_from_phase(shape, phase, latent)
                np.testing.assert_allclose(observed, expected, rtol=1e-12, atol=1e-12)

    def test_real_causal_estimator_path_runs_without_labels(self):
        cfg = archived.Config(endpoint_start=81, endpoint_stop=83)
        rng = np.random.default_rng(701)
        residual = rng.normal(size=(2, 180))
        reference = rng.normal(size=(2, 180))
        result = prototype.score_observation_only(
            residual, reference, {"residual_phi": np.array([0.2, 0.6])}, cfg
        )
        self.assertEqual(result["grid_score_grid"].shape, (2, 3))
        self.assertTrue(np.all(np.isfinite(result["grid_score_grid"])))

    def test_fails_closed_on_nan_input(self):
        cfg, residual, reference, params, _, _ = fixture()
        residual[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            prototype.score_observation_only(residual, reference, params, cfg)

    def test_fails_closed_when_reference_shape_is_wrong(self):
        cfg, residual, reference, params, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, "identical"):
            prototype.score_observation_only(residual, reference[:, :-1], params, cfg)

    def test_fails_closed_on_out_of_range_endpoint(self):
        cfg, residual, reference, params, _, _ = fixture()
        cfg = archived.Config(endpoint_start=180, endpoint_stop=180)
        with self.assertRaisesRegex(ValueError, "endpoint"):
            prototype.score_observation_only(residual, reference, params, cfg)

    def test_fails_closed_on_phi_shape(self):
        cfg, residual, reference, params, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, "coefficient"):
            prototype.score_observation_only(
                residual, reference, {"residual_phi": np.array([0.1, 0.2])}, cfg
            )


if __name__ == "__main__":
    unittest.main()
