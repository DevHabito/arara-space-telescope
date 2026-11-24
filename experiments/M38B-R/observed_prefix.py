"""Endpoint-bounded observation-only diagnostic; not a streaming detector.

A call accepts precisely the measured prefix up to and including endpoint.
No later sample is supplied, ignored, replaced, or synthesized by this path.
No historical ARARA scorer or simulator-truth dependency is imported here.
"""
from __future__ import annotations

import numpy as np

from independent_bank import IndependentBankConfig, score_independent_bank
from observed_preprocessing import preprocess_observations


def score_observed_prefix(
    stars: np.ndarray, *, endpoint: int
) -> dict[str, np.ndarray]:
    """Score only an explicitly complete, finite measured prefix.

    The input's sample axis must be precisely 0..endpoint inclusive.
    For a missing sample *within* that interval, preprocessing fails closed.
    Returns one score column per curve; it does not make a detection claim.
    """
    if type(endpoint) is not int or not 81 <= endpoint <= 179:
        raise ValueError("Expected integer endpoint in the historical 81..179 range")

    observed = np.asarray(stars)
    if (
        observed.ndim != 3
        or observed.shape[0] < 1
        or observed.shape[1] < 2
    ):
        raise ValueError(
            "Expected nonempty (curve, target-and-references, time) prefix"
        )
    if observed.shape[2] != endpoint + 1:
        raise ValueError(
            f"Expected exactly {endpoint + 1} measured samples for endpoint "
            f"{endpoint}; received {observed.shape[2]}"
        )

    residual, reference, fitted = preprocess_observations(
        observed, baseline_n=50
    )
    return score_independent_bank(
        residual, reference, fitted["residual_phi"],
        IndependentBankConfig(endpoints=(endpoint,)),
    )
