"""Independent pre-outcome reference for the complete M38B-R template bank.

No historical ARARA, cached labels, simulator truth, or archived scorer imports.
The entire bank is recomputed from observed residuals, references, fitted
AR(1) coefficients, a causal hinge estimator, and fixed template equations.

The output is an uncalibrated diagnostic score, never a detection decision.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from independent_onset import estimate_direct_hinge
from independent_projection import score_projected

SHAPES = ("linear", "power_law", "exponential", "logistic")
DURATIONS = tuple(range(24, 61))
LATENT_VALUES = (0.0, 0.25, 0.5, 0.75, 1.0)
UNIQUE_EVALUATIONS_PER_ENDPOINT = 37 * (1 + 3 * 5)


@dataclass(frozen=True)
class IndependentBankConfig:
    """Historical candidate geometry; short grids are diagnostic only."""

    endpoints: tuple[int, ...] = tuple(range(81, 180))
    window_length: int = 8
    selection_start: int = 50
    guard_length: int = 1
    confirmation_length: int = 8
    first_candidate: int = 70
    last_candidate: int = 120

    def __post_init__(self) -> None:
        if (
            self.window_length != 8
            or self.selection_start != 50
            or self.guard_length != 1
            or self.confirmation_length != 8
            or self.first_candidate != 70
            or self.last_candidate != 120
        ):
            raise ValueError("Independent bank requires declared historical geometry")
        if (
            not isinstance(self.endpoints, tuple)
            or not self.endpoints
            or any(type(e) is not int or e < 81 or e > 179 for e in self.endpoints)
            or any(right <= left for left, right in zip(self.endpoints, self.endpoints[1:]))
        ):
            raise ValueError("Expected increasing unique endpoints within 81..179")


def bank_order() -> tuple[tuple[int, int, int], ...]:
    """Sorted tie order: latent index, duration, shape index.

    Linear templates are latent invariant, so evaluate them at latent zero.
    The physical model is not inferred from this discrete tuple order.
    """
    choices = []
    for latent_index in range(len(LATENT_VALUES)):
        for duration in DURATIONS:
            for shape_index, shape in enumerate(SHAPES):
                if shape == "linear" and latent_index != 0:
                    continue
                choices.append((latent_index, duration, shape_index))
    return tuple(choices)


BANK_ORDER = bank_order()


def _template(shape_index: int, phase: np.ndarray, latent: float) -> np.ndarray:
    """Evaluate declared functions on [0, 1], without archived helpers."""
    if shape_index == 0:
        return phase
    if shape_index == 1:
        return phase ** (1.5 + 1.5 * latent)
    if shape_index == 2:
        slope = 1.0 + 3.0 * latent
        return np.expm1(slope * phase) / np.expm1(slope)
    if shape_index == 3:
        slope = 6.0 + 6.0 * latent
        logistic = 1.0 / (1.0 + np.exp(-slope * (phase - 0.5)))
        at_zero = 1.0 / (1.0 + np.exp(slope / 2.0))
        at_one = 1.0 / (1.0 + np.exp(-slope / 2.0))
        return (logistic - at_zero) / (at_one - at_zero)
    raise ValueError("Invalid template shape index")


def score_independent_bank(
    residual: np.ndarray,
    processed_reference: np.ndarray,
    residual_phi: np.ndarray,
    cfg: IndependentBankConfig = IndependentBankConfig(),
) -> dict[str, np.ndarray]:
    """Independent onset, all shape/duration/latent templates, and projection.

    For a missing admissible onset, scores are -inf and parameter labels -1
    rather than silently interpreting the archived first-candidate convention.
    """
    target = np.asarray(residual, dtype=np.float64)
    reference = np.asarray(processed_reference, dtype=np.float64)
    phi = np.asarray(residual_phi, dtype=np.float64)
    if (
        target.ndim != 2
        or target.shape[0] == 0
        or target.shape[1] <= cfg.endpoints[-1]
    ):
        raise ValueError(
            "Expected nonempty (curve, time) residual extending through "
            "the last configured endpoint"
        )
    if reference.shape != target.shape:
        raise ValueError("Reference/residual shapes do not agree")
    if phi.shape != (target.shape[0],):
        raise ValueError("Expected a fitted AR(1) coefficient per curve")
    if not all(np.isfinite(v).all() for v in (target, reference, phi)):
        raise ValueError("All observed inputs and coefficients must be finite")
    if np.any((phi < 0.0) | (phi > 0.8)):
        raise ValueError("AR(1) coefficient lies outside fitted 0..0.8 interval")

    endpoints = np.asarray(cfg.endpoints, dtype=np.int64)
    if endpoints[-1] >= target.shape[1]:
        raise ValueError("Endpoint leaves measured observation series")
    estimated, objective = estimate_direct_hinge(
        target, endpoints,
        selection_start=cfg.selection_start,
        confirmation_length=cfg.confirmation_length,
        guard_length=cfg.guard_length,
        first_candidate=cfg.first_candidate,
        last_candidate=cfg.last_candidate,
    )
    # Negative infinity means no admissible positive onset objective.
    # It is a defined failure state, not a malformed numerical result.
    # Positive infinity can arise from an exactly unit correlation.
    if np.isnan(objective).any():
        raise ValueError("Invalid onset objective")
    alignment_defined = ~np.isneginf(objective)
    n = target.shape[0]
    e = len(endpoints)
    output = {
        "grid_score_grid": np.full((n, e), -np.inf, dtype=np.float64),
        "grid_shape_index_grid": np.full((n, e), -1, dtype=np.int8),
        "grid_duration_grid": np.full((n, e), -1, dtype=np.int16),
        "grid_latent_index_grid": np.full((n, e), -1, dtype=np.int8),
        "grid_energy_grid": np.zeros((n, e), dtype=np.float64),
        "estimated_onset_grid": estimated.astype(np.int16),
        "hinge_objective_grid": objective,
        "alignment_defined_grid": alignment_defined,
        "winner_margin_grid": np.zeros((n, e), dtype=np.float64),
    }
    if len(BANK_ORDER) != UNIQUE_EVALUATIONS_PER_ENDPOINT:
        raise RuntimeError("Independent bank order is incomplete")

    for endpoint_index, endpoint in enumerate(endpoints):
        raw_times = np.arange(endpoint - 8, endpoint + 1)
        endpoint_residual = target[:, endpoint - 7: endpoint + 1][:, None, :]
        endpoint_reference = reference[:, endpoint - 7: endpoint + 1][:, None, :]
        positions = raw_times[None, :] - estimated[:, endpoint_index, None]

        phase_by_duration = {
            d: np.clip(positions / d, 0.0, 1.0) for d in DURATIONS
        }
        filtered = np.empty((n, len(BANK_ORDER), 8), dtype=np.float64)
        for hypothesis_index, (latent_index, duration, shape_index) in enumerate(BANK_ORDER):
            raw = _template(
                shape_index, phase_by_duration[duration], LATENT_VALUES[latent_index]
            )
            filtered[:, hypothesis_index, :] = (
                raw[:, 1:] - phi[:, None] * raw[:, :-1]
            )
        scores, diagnostics = score_projected(
            endpoint_residual, filtered[:, :, None, :], endpoint_reference
        )
        scores = scores[:, :, 0]
        retention = diagnostics["energy_retention"][:, :, 0]
        winner = np.argmax(scores, axis=1)
        best = scores[np.arange(n), winner]
        second = np.partition(scores, -2, axis=1)[:, -2]
        margin = best - second
        for curve in range(n):
            if not alignment_defined[curve, endpoint_index]:
                continue
            latent_index, duration, shape_index = BANK_ORDER[int(winner[curve])]
            output["grid_score_grid"][curve, endpoint_index] = best[curve]
            output["grid_shape_index_grid"][curve, endpoint_index] = shape_index
            output["grid_duration_grid"][curve, endpoint_index] = duration
            output["grid_latent_index_grid"][curve, endpoint_index] = latent_index
            output["grid_energy_grid"][curve, endpoint_index] = retention[curve, winner[curve]]
            output["winner_margin_grid"][curve, endpoint_index] = margin[curve]
    return output


def score_independent_observed_stars(
    stars: np.ndarray,
    cfg: IndependentBankConfig = IndependentBankConfig(),
) -> dict[str, np.ndarray]:
    """Observed-star entrypoint with no historical scorer or oracle dependency."""
    from observed_preprocessing import preprocess_observations

    residual, reference, fitted = preprocess_observations(stars)
    return score_independent_bank(residual, reference, fitted["residual_phi"], cfg)
