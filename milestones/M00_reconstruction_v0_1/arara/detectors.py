from __future__ import annotations

import numpy as np


def robust_center_scale(x: np.ndarray) -> tuple[float, float]:
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    sigma = 1.4826 * mad
    if sigma < 1e-8:
        sigma = float(np.std(x, ddof=1))
    return med, max(sigma, 1e-8)


def flux_z_score(flux: np.ndarray, baseline_end: int = 36) -> np.ndarray:
    med, sigma = robust_center_scale(flux[:baseline_end])
    return np.maximum((flux - med) / sigma, 0.0)


def cusum_score(flux: np.ndarray, baseline_end: int = 36, allowance: float = 0.5) -> np.ndarray:
    med, sigma = robust_center_scale(flux[:baseline_end])
    z = (flux - med) / sigma
    out = np.zeros_like(z)
    for i in range(baseline_end, len(z)):
        out[i] = max(0.0, out[i - 1] + z[i] - allowance)
    return out


def dp1_reconstructed_score(
    flux: np.ndarray,
    cadence_s: float,
    baseline_end: int = 36,
    window: int = 6,
) -> np.ndarray:
    """Corrected reconstruction of the DP1 idea.

    This is not claimed to be the deleted implementation. It preserves the published
    feature logic but defines every feature explicitly and keeps housekeeping outside
    the external detector, so the internal gate can be audited separately.
    """
    med, sigma = robust_center_scale(flux[:baseline_end])
    z = (flux - med) / sigma
    zpos = np.maximum(z, 0.0)
    ewma = np.zeros_like(z)
    alpha = 0.25
    for i in range(1, len(z)):
        ewma[i] = alpha * zpos[i] + (1 - alpha) * ewma[i - 1]

    slope = np.zeros_like(z)
    mono = np.zeros_like(z)
    rough = np.zeros_like(z)
    drops = np.zeros_like(z)
    hours_per_step = cadence_s / 3600.0
    for i in range(baseline_end, len(z)):
        j = max(baseline_end, i - window + 1)
        w = z[j:i + 1]
        if len(w) >= 3:
            x = np.arange(len(w), dtype=float) * hours_per_step
            xc = x - x.mean()
            denom = float(np.sum(xc**2))
            raw_slope = 0.0 if denom == 0 else float(np.sum(xc * (w - w.mean())) / denom)
            slope[i] = max(raw_slope, 0.0)
            d = np.diff(w)
            mono[i] = float(np.mean(d > 0))
            rough[i] = float(np.sqrt(np.mean(d**2)) / np.sqrt(2.0))
            drops[i] = float(np.mean(np.maximum(-d, 0.0)))

    raw = (
        0.35 * zpos
        + 1.85 * slope
        + 0.55 * ewma
        + 1.10 * mono
        - 0.45 * rough
        - 0.50 * drops
    )
    raw[:baseline_end] = 0.0
    return np.maximum(raw, 0.0)


def housekeeping_instability(housekeeping: np.ndarray) -> np.ndarray:
    """Auditable internal score: largest absolute standardized channel excursion."""
    return np.max(np.abs(housekeeping), axis=1)
