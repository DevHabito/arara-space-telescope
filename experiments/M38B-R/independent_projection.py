"""Independent vector-projection scorer for numerical comparison, not astronomy.

The archived routine subtracts squared reference energy from template energy.
Here Gram–Schmidt vectors are formed explicitly before squaring, to expose
conditioning differences. No archived scoring modules are imported here.
"""
from __future__ import annotations

import numpy as np

ENERGY_FLOOR = 1e-12


def score_projected(
    residual_windows: np.ndarray,
    template_windows: np.ndarray,
    reference_windows: np.ndarray,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Compute projected matched-filter scores for fixed observed windows.

    residual/reference: [curve, endpoint, sample].
    templates: [curve, hypothesis, endpoint, sample].
    Zero-energy references are ignored. Degenerate templates score zero.
    Floating-point agreement with the archived formula is not guaranteed
    close to the projection's singular directions.
    """
    residual = np.asarray(residual_windows, dtype=np.float64)
    templates = np.asarray(template_windows, dtype=np.float64)
    reference = np.asarray(reference_windows, dtype=np.float64)

    if residual.ndim != 3 or templates.ndim != 4:
        raise ValueError("Expected 3D residuals and 4D templates")
    if (
        reference.shape != residual.shape
        or templates.shape[0] != residual.shape[0]
        or templates.shape[2:] != residual.shape[1:]
    ):
        raise ValueError("Mismatched projected-score array shapes")
    if not residual.size or not templates.size or not reference.size:
        raise ValueError("Empty projected-score arrays")
    if not all(np.all(np.isfinite(value)) for value in (residual, templates, reference)):
        raise ValueError("Projected-score inputs must be finite")

    reference_energy = np.einsum("ces,ces->ce", reference, reference)
    reference_valid = reference_energy > ENERGY_FLOOR
    safe_reference_energy = np.where(reference_valid, reference_energy, 1.0)

    residual_dot = np.einsum("ces,ces->ce", residual, reference)
    residual_coefficient = np.where(
        reference_valid, residual_dot / safe_reference_energy, 0.0
    )
    residual_orthogonal = residual - residual_coefficient[..., None] * reference

    template_dot = np.einsum("ches,ces->che", templates, reference)
    template_coefficient = np.where(
        reference_valid[:, None, :],
        template_dot / safe_reference_energy[:, None, :],
        0.0,
    )
    template_orthogonal = (
        templates - template_coefficient[..., None] * reference[:, None, :, :]
    )

    original_energy = np.einsum("ches,ches->che", templates, templates)
    projected_energy = np.einsum(
        "ches,ches->che", template_orthogonal, template_orthogonal
    )
    template_valid = projected_energy > ENERGY_FLOOR
    score_denominator = np.sqrt(np.where(template_valid, projected_energy, 1.0))
    numerator = np.einsum(
        "ches,ces->che", template_orthogonal, residual_orthogonal
    )
    score = np.where(template_valid, numerator / score_denominator, 0.0)

    safe_original = np.where(original_energy > ENERGY_FLOOR, original_energy, 1.0)
    retention = np.where(
        original_energy > ENERGY_FLOOR, projected_energy / safe_original, 0.0
    )

    return score, {
        "energy_retention": np.clip(retention, 0.0, 1.0),
        "template_degenerate": ~template_valid,
        "reference_degenerate": ~reference_valid,
    }
