"""Observation-only implementation of the M29 baseline and AR(1) transform.

The function receives measured star series and a baseline length only.
It does not import the historical implementation or accept injection metadata.
This is an engineering reference, not a calibrated detector.
"""
from __future__ import annotations

import numpy as np


def preprocess_observations(
    stars: np.ndarray, *, baseline_n: int = 50
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Compute residual, nuisance reference and fitted parameters from stars.

    Expected star axis: target followed by one or more reference stars.
    Each baseline-derived parameter is frozen when later samples are processed.
    """
    values = np.asarray(stars, dtype=np.float64)
    if values.ndim != 3 or values.shape[0] < 1 or values.shape[1] < 2:
        raise ValueError("Expected (curve, target-and-references, time) observations")
    if isinstance(baseline_n, bool) or not isinstance(baseline_n, int):
        raise ValueError("Baseline length must be an integer")
    if baseline_n < 3 or values.shape[2] <= baseline_n:
        raise ValueError("Baseline must contain at least three samples and leave future samples")
    if not np.isfinite(values).all():
        raise ValueError("Observed star series must be finite")

    n, _, horizon = values.shape
    residual = np.empty((n, horizon), dtype=np.float64)
    processed_reference = np.empty_like(residual)
    fitted = {
        "target_scale": np.empty(n),
        "beta_hat": np.empty(n),
        "residual_scale": np.empty(n),
        "residual_phi": np.empty(n),
        "reference_baseline_median": np.empty(n),
    }

    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            for curve in range(n):
                series = values[curve]
                baseline = series[:, :baseline_n]
                centers = np.median(baseline, axis=1)
                star_scales = np.maximum(
                    1.4826 * np.median(np.abs(baseline - centers[:, None]), axis=1),
                    1e-8,
                )
                normalized = (series - centers[:, None]) / star_scales[:, None]
                common_reference = np.median(normalized[1:], axis=0)

                x = normalized[0, :baseline_n]
                ref = common_reference[:baseline_n]
                centered_x = x - np.mean(x)
                centered_ref = ref - np.mean(ref)
                reference_variance = float(np.dot(centered_ref, centered_ref))
                coupling = (
                    float(np.dot(centered_x, centered_ref) / reference_variance)
                    if reference_variance > 1e-12 else 0.0
                )
                coupling = float(np.clip(coupling, 0.0, 3.0))
                common_removed = normalized[0] - coupling * common_reference

                base_residual = common_removed[:baseline_n]
                residual_center = float(np.median(base_residual))
                centered_baseline = base_residual - residual_center
                noise_scale = max(
                    1.4826 * float(np.median(np.abs(centered_baseline))), 1e-8
                )
                phi_den = float(np.dot(centered_baseline[:-1], centered_baseline[:-1]))
                phi = (
                    float(np.dot(centered_baseline[1:], centered_baseline[:-1]) / phi_den)
                    if phi_den > 1e-12 else 0.0
                )
                phi = float(np.clip(phi, 0.0, 0.8))

                centered_all = common_removed - residual_center
                residual[curve, 0] = centered_all[0] / noise_scale
                residual[curve, 1:] = (
                    centered_all[1:] - phi * centered_all[:-1]
                ) / noise_scale

                reference_center = float(np.median(ref))
                reference_all = common_reference - reference_center
                processed_reference[curve, 0] = reference_all[0] / noise_scale
                processed_reference[curve, 1:] = (
                    reference_all[1:] - phi * reference_all[:-1]
                ) / noise_scale

                fitted["target_scale"][curve] = star_scales[0]
                fitted["beta_hat"][curve] = coupling
                fitted["residual_scale"][curve] = noise_scale
                fitted["residual_phi"][curve] = phi
                fitted["reference_baseline_median"][curve] = reference_center
    except FloatingPointError as error:
        raise ValueError("Nonfinite preprocessing intermediate") from error
    if not np.isfinite(residual).all() or not np.isfinite(processed_reference).all():
        raise ValueError("Nonfinite preprocessing output")
    if any(not np.isfinite(value).all() for value in fitted.values()):
        raise ValueError("Nonfinite fitted preprocessing parameter")
    return residual, processed_reference, fitted


def score_observed_stars(stars: np.ndarray, cfg, *, baseline_n: int = 50) -> dict:
    """Integrate observation-only preprocessing with the *existing* prototype.

    The downstream candidate still imports archived estimation and projection;
    this is not an independent end-to-end detector.
    """
    from observable_candidate import score_observation_only

    residual, reference, fitted = preprocess_observations(
        stars, baseline_n=baseline_n
    )
    return score_observation_only(residual, reference, fitted, cfg)
