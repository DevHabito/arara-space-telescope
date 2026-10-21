"""Observation-only candidate scorer for an uncalibrated ARARA research prototype.

This deliberately does not modify the frozen M38B source, choose a detection
threshold, report recall, or authorize calibration. The historical scorer is
imported only for its frozen template-family definitions, endpoint windows,
causal onset estimator, and reference projection.

No truth/label/oracle input is accepted by the candidate's public interface.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

_ARCHIVE = Path(__file__).resolve().parents[2] / "milestones" / "M38B_recovery"
if str(_ARCHIVE) not in sys.path:
    sys.path.insert(0, str(_ARCHIVE))

import arara_m38b as archived  # noqa: E402

WINDOW_LENGTH = 8
SHAPES = tuple(archived.SHAPES)
DURATIONS = np.asarray(archived.DURATIONS, dtype=np.int16)
LATENT_GRID = np.asarray(archived.LATENT_GRID, dtype=np.float64)


def _shape_template(shape: str, phase: np.ndarray, latent: np.ndarray) -> np.ndarray:
    """Implement the fixed shape equations without using simulated truth."""
    if shape == "linear":
        return np.broadcast_to(phase, np.broadcast_shapes(phase.shape, latent.shape))
    if shape == "power_law":
        return np.power(phase, 1.5 + 1.5 * latent)
    if shape == "exponential":
        beta = 1.0 + 3.0 * latent
        return np.expm1(beta * phase) / np.expm1(beta)
    if shape == "logistic":
        slope = 6.0 + 6.0 * latent
        sigmoid = 1.0 / (1.0 + np.exp(-slope * (phase - 0.5)))
        left = 1.0 / (1.0 + np.exp(slope / 2.0))
        right = 1.0 / (1.0 + np.exp(-slope / 2.0))
        return (sigmoid - left) / (right - left)
    raise ValueError(f"Unknown frozen template shape: {shape}")


def _validate_inputs(
    residual: np.ndarray,
    processed_reference: np.ndarray,
    params: dict,
    cfg: archived.Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    target = np.asarray(residual, dtype=np.float64)
    reference = np.asarray(processed_reference, dtype=np.float64)
    endpoints = np.asarray(cfg.endpoint_grid, dtype=np.int32)
    if target.ndim != 2 or reference.shape != target.shape:
        raise ValueError("Observed residual and reference require identical (curve, time) shapes.")
    if target.shape[0] == 0 or target.shape[1] < WINDOW_LENGTH + 1:
        raise ValueError("Empty curves or insufficient time samples.")
    if not (np.all(np.isfinite(target)) and np.all(np.isfinite(reference))):
        raise ValueError("Nonfinite observed data.")
    if cfg.window_length != WINDOW_LENGTH or endpoints.ndim != 1 or not len(endpoints):
        raise ValueError("The frozen eight-cadence confirmation window is required.")
    if np.any(endpoints < WINDOW_LENGTH) or np.any(endpoints >= target.shape[1]):
        raise ValueError("Observed endpoint window leaves the measured time series.")
    if not np.array_equal(DURATIONS, np.arange(24, 61)):
        raise ValueError("Frozen duration bank changed.")
    if not np.array_equal(LATENT_GRID, np.array([0.0, 0.25, 0.5, 0.75, 1.0])):
        raise ValueError("Frozen latent grid changed.")
    phi = np.asarray(params["residual_phi"], dtype=np.float64)
    if phi.shape != (target.shape[0],) or not np.all(np.isfinite(phi)):
        raise ValueError("Residual AR coefficient must be finite and curve-specific.")
    return target, reference, endpoints, phi


def score_observation_only(
    residual: np.ndarray,
    processed_reference: np.ndarray,
    params: dict,
    cfg: archived.Config,
) -> dict[str, np.ndarray]:
    """Score the frozen bank using observations and a causal estimated anchor.

    Template boundary validity follows the measured endpoint indices, never a
    simulated true onset. Thresholds from M37R/M38B are not reusable.
    """
    target, reference, endpoints, phi = _validate_inputs(
        residual, processed_reference, params, cfg
    )
    estimated, objective = archived.m34.estimate_onset_grid(target, endpoints, cfg)
    n, time_count = target.shape
    endpoint_count = len(endpoints)
    if estimated.shape != (n, endpoint_count) or not np.all(np.isfinite(estimated)):
        raise ValueError("Invalid observed-onset estimator result.")

    # The nine raw samples yield eight AR(1)-filtered confirmation samples.
    # Each endpoint is already checked to lie entirely inside observed time.
    positions = (
        endpoints[None, :, None].astype(np.float64)
        + np.arange(-WINDOW_LENGTH, 1, dtype=np.float64)[None, None, :]
        - estimated[:, :, None].astype(np.float64)
    )
    phase = np.clip(
        positions[:, None, :, :] / DURATIONS[None, :, None, None],
        0.0,
        1.0,
    )
    target_windows = archived.m34.fixed_endpoint_windows(
        target, endpoints, WINDOW_LENGTH
    )
    reference_windows = archived.m34.fixed_endpoint_windows(
        reference, endpoints, WINDOW_LENGTH
    )

    max_score = np.full((n, endpoint_count), -np.inf, dtype=np.float64)
    best_shape = np.full((n, endpoint_count), -1, dtype=np.int8)
    best_duration = np.full((n, endpoint_count), -1, dtype=np.int16)
    best_latent = np.full((n, endpoint_count), -1, dtype=np.int8)
    best_energy = np.zeros((n, endpoint_count), dtype=np.float64)

    for shape_index, shape in enumerate(SHAPES):
        if shape == "linear":
            raw = phase
            filtered = raw[..., 1:] - phi[:, None, None, None] * raw[..., :-1]
            hypotheses = filtered
        else:
            raw = _shape_template(
                shape,
                phase[:, None, :, :, :],
                LATENT_GRID[None, :, None, None, None],
            )
            filtered = (
                raw[..., 1:]
                - phi[:, None, None, None, None] * raw[..., :-1]
            )
            hypotheses = filtered.reshape(
                n, len(LATENT_GRID) * len(DURATIONS),
                endpoint_count, WINDOW_LENGTH
            )

        scores, diagnostics = archived.m37.projected_scores_hypotheses(
            target_windows, hypotheses, reference_windows
        )
        best_index = np.argmax(scores, axis=1)
        best_scores = np.take_along_axis(
            scores, best_index[:, None, :], axis=1
        )[:, 0, :]
        best_retention = np.take_along_axis(
            diagnostics["energy_retention"], best_index[:, None, :], axis=1
        )[:, 0, :]
        if shape == "linear":
            latent_index = np.zeros_like(best_index, dtype=np.int8)
            duration = DURATIONS[best_index]
        else:
            latent_index = (best_index // len(DURATIONS)).astype(np.int8)
            duration = DURATIONS[best_index % len(DURATIONS)]

        earlier = (
            (latent_index < best_latent)
            | ((latent_index == best_latent)
               & ((duration < best_duration)
                  | ((duration == best_duration) & (shape_index < best_shape))))
        )
        update = (best_scores > max_score) | (
            (best_scores == max_score) & earlier
        )
        max_score = np.where(update, best_scores, max_score)
        best_shape = np.where(update, shape_index, best_shape).astype(np.int8)
        best_duration = np.where(update, duration, best_duration).astype(np.int16)
        best_latent = np.where(update, latent_index, best_latent).astype(np.int8)
        best_energy = np.where(update, best_retention, best_energy)

    return {
        "grid_score_grid": max_score,
        "grid_shape_index_grid": best_shape,
        "grid_duration_grid": best_duration,
        "grid_latent_index_grid": best_latent,
        "grid_energy_grid": best_energy,
        "estimated_onset_grid": estimated,
        "hinge_objective_grid": objective,
    }
