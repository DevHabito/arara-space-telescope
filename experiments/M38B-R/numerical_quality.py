"""Observation-quality classification for pre-outcome numerical audits.

This function is not a missing-data repair or a streaming scorer. It only
marks where NaN/Inf exists relative to each requested measured endpoint.
It never alters raw values, fits a coefficient or invokes a detector.
"""
from __future__ import annotations

import numpy as np


def classify_nonfinite_positions(
    stars: np.ndarray, endpoints: tuple[int, ...]
) -> dict[str, np.ndarray]:
    """Separate invalid observed prefixes from future-only invalid samples.

    For each curve/endpoint, prefix means the inclusive interval 0..endpoint;
    future means endpoint+1..last sample. A series may have both. The
    'future_only' flag is true only if the measured prefix is entirely finite.
    """
    values = np.asarray(stars, dtype=np.float64)
    if values.ndim != 3 or values.shape[0] < 1 or values.shape[1] < 2 or values.shape[2] < 1:
        raise ValueError("Expected nonempty (curve, target-and-references, time) arrays")
    if (
        not isinstance(endpoints, tuple)
        or not endpoints
        or any(type(endpoint) is not int for endpoint in endpoints)
        or any(endpoint < 0 or endpoint >= values.shape[2] for endpoint in endpoints)
        or any(b <= a for a, b in zip(endpoints, endpoints[1:]))
    ):
        raise ValueError("Expected increasing in-range integer endpoints")

    nonfinite_by_time = ~np.isfinite(values).all(axis=1)
    prefix_nonfinite = np.logical_or.accumulate(nonfinite_by_time, axis=1)
    future_nonfinite = np.logical_or.accumulate(
        nonfinite_by_time[:, ::-1], axis=1
    )[:, ::-1]

    prefix = prefix_nonfinite[:, list(endpoints)]
    future = np.zeros_like(prefix)
    for position, endpoint in enumerate(endpoints):
        if endpoint + 1 < values.shape[2]:
            future[:, position] = future_nonfinite[:, endpoint + 1]

    return {
        "prefix_has_nonfinite_grid": prefix,
        "future_has_nonfinite_grid": future,
        "future_only_nonfinite_grid": future & ~prefix,
        "whole_series_finite": ~nonfinite_by_time.any(axis=1),
    }
