"""Direct-sum reference for the archived causal hinge-onset statistic.

This is a source-independent numerical diagnostic, not a calibrated detector.
No archived ARARA module is imported here, and no simulated truth is used.
"""
from __future__ import annotations

import numpy as np


def estimate_direct_hinge(
    residual: np.ndarray,
    endpoints: np.ndarray,
    *,
    selection_start: int = 50,
    confirmation_length: int = 8,
    guard_length: int = 1,
    first_candidate: int = 70,
    last_candidate: int = 120,
) -> tuple[np.ndarray, np.ndarray]:
    """Reference calculation using centered sums, not archived prefix sums.

    An undefined optimum preserves the archived diagnostic convention:
    the first candidate is returned with score -inf. The returned onset
    must never be interpreted without checking whether the score is finite.
    """
    observed = np.asarray(residual, dtype=np.float64)
    times = np.asarray(endpoints)
    if observed.ndim != 2 or observed.shape[0] == 0 or observed.shape[1] == 0:
        raise ValueError("Expected nonempty (curve, time) observations")
    if times.ndim != 1 or times.size == 0 or not np.issubdtype(times.dtype, np.integer):
        raise ValueError("Expected nonempty integer endpoints")
    if not np.isfinite(observed).all():
        raise ValueError("Observations must be finite")
    if selection_start < 0 or confirmation_length < 1 or guard_length < 0:
        raise ValueError("Invalid temporal split")
    if first_candidate < 0 or last_candidate < first_candidate:
        raise ValueError("Invalid onset candidate bounds")
    if np.any(times >= observed.shape[1]):
        raise ValueError("Endpoint exceeds observed horizon")

    estimated = np.full((observed.shape[0], times.size), first_candidate, dtype=np.int64)
    objective = np.full((observed.shape[0], times.size), -np.inf, dtype=np.float64)

    for endpoint_index, endpoint_value in enumerate(times):
        endpoint = int(endpoint_value)
        selection_end = endpoint - confirmation_length - guard_length
        if selection_end < selection_start + 2:
            raise ValueError("Endpoint precedes minimum selection interval")
        selection_times = np.arange(selection_start, selection_end + 1, dtype=np.float64)
        count = selection_times.size
        for curve_index in range(observed.shape[0]):
            selected = observed[curve_index, selection_start : selection_end + 1]
            centered = selected - selected.mean()
            variance = np.dot(centered, centered)
            for candidate in range(first_candidate, last_candidate + 1):
                if selection_end - candidate + 1 < 3:
                    continue
                hinge = np.maximum(0.0, selection_times - candidate)
                centered_hinge = hinge - hinge.mean()
                denominator = np.sqrt(variance * np.dot(centered_hinge, centered_hinge))
                correlation = 0.0 if denominator <= 1e-12 else float(
                    np.clip(np.dot(centered, centered_hinge) / denominator, -1.0, 1.0)
                )
                if correlation <= 0.0:
                    continue
                value = (
                    np.inf if correlation >= 1.0 - 1e-15 else
                    correlation * np.sqrt((count - 2) / (1.0 - correlation**2))
                )
                if value > objective[curve_index, endpoint_index]:
                    objective[curve_index, endpoint_index] = value
                    estimated[curve_index, endpoint_index] = candidate
    return estimated, objective
