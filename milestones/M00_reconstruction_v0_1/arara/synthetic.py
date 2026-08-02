from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class SyntheticSample:
    flux: np.ndarray
    housekeeping: np.ndarray
    instrument_bad: np.ndarray
    kind: str
    onset_idx: int
    reference_idx: int
    cadence_s: float
    decoy_kind: str = "none"
    instrument_kind: str = "none"


def _ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    x = np.zeros(n)
    eps = rng.normal(0.0, sigma, size=n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + eps[i]
    return x


def _instrument_episode(
    rng: np.random.Generator,
    n: int,
    noise_sigma: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Generate latent instrument effects independent of astrophysical class."""
    flux_effect = np.zeros(n)
    hk = rng.normal(0.0, 1.0, size=(n, 7))
    bad = np.zeros(n, dtype=bool)
    kind = "none"
    if rng.random() >= 0.30:
        return flux_effect, hk, bad, kind

    kind = rng.choice(["thermal", "jitter", "step", "radiation", "noise_burst"])
    start = int(rng.integers(40, n - 18))
    duration = int(rng.integers(6, min(24, n - start)))
    sl = slice(start, start + duration)
    bad[sl] = True

    if kind == "thermal":
        ramp = np.linspace(0.0, rng.uniform(2, 7) * noise_sigma, duration)
        flux_effect[sl] += ramp
        hk[sl, 0] += rng.uniform(4.0, 7.0)
        hk[sl, 2] += rng.uniform(2.5, 4.5)
    elif kind == "jitter":
        flux_effect[sl] += rng.normal(0.0, rng.uniform(2, 5) * noise_sigma, duration)
        hk[sl, 1] += rng.uniform(4.0, 8.0)
    elif kind == "step":
        amp = rng.choice([-1, 1]) * rng.uniform(3, 8) * noise_sigma
        flux_effect[start:] += amp
        hk[sl, 2] += rng.uniform(3.0, 6.0)
    elif kind == "radiation":
        j = start + int(rng.integers(0, duration))
        flux_effect[j] += rng.uniform(8, 18) * noise_sigma
        hk[max(0, j - 1):min(n, j + 2), 5] += rng.uniform(5.0, 9.0)
    elif kind == "noise_burst":
        flux_effect[sl] += rng.normal(0.0, rng.uniform(3, 7) * noise_sigma, duration)
        hk[sl, 3] += rng.uniform(3.0, 6.0)
        hk[sl, 6] += rng.uniform(2.5, 5.0)
    return flux_effect, hk, bad, kind


def generate_sample(
    rng: np.random.Generator,
    kind: str,
    n: int = 144,
    cadence_s: float = 200.0,
    baseline_end: int = 36,
) -> SyntheticSample:
    if kind not in {"event", "decoy", "control"}:
        raise ValueError("Unknown kind")
    noise_sigma = float(rng.uniform(0.0015, 0.0045))
    reference_idx = int(rng.integers(88, 116))
    rise_len = int(rng.integers(16, 29))
    onset_idx = reference_idx - rise_len
    if onset_idx <= baseline_end + 8:
        raise RuntimeError("Generator violated clean-baseline contract")

    common = _ar1(rng, n, phi=float(rng.uniform(0.6, 0.92)), sigma=noise_sigma * 0.18)
    white = rng.normal(0.0, noise_sigma, size=n)
    flux = 1.0 + common + white

    inst_flux, hk, inst_bad, inst_kind = _instrument_episode(rng, n, noise_sigma)
    flux += inst_flux

    decoy_kind = "none"
    t = np.arange(n)
    if kind == "event":
        amp = rng.uniform(5.0, 12.0) * noise_sigma
        power = rng.uniform(1.0, 2.2)
        x = np.clip((t - onset_idx) / max(1, rise_len), 0.0, 1.0)
        rise = amp * x**power
        post = amp * (1.0 + 0.15 * np.clip((t - reference_idx) / 20.0, 0, 1))
        flux += np.where(t < reference_idx, rise, post)
    elif kind == "decoy":
        decoy_kind = str(rng.choice(["bump", "sinusoid", "dip", "step", "spike", "red_burst"]))
        amp = rng.uniform(4.0, 11.0) * noise_sigma
        if decoy_kind == "bump":
            center = rng.integers(onset_idx, reference_idx + 5)
            width = rng.uniform(3.0, 10.0)
            flux += amp * np.exp(-0.5 * ((t - center) / width) ** 2)
        elif decoy_kind == "sinusoid":
            period = rng.uniform(12.0, 36.0)
            phase = rng.uniform(0, 2 * np.pi)
            flux += amp * np.sin(2 * np.pi * t / period + phase)
        elif decoy_kind == "dip":
            center = rng.integers(onset_idx, reference_idx + 5)
            width = rng.uniform(3.0, 10.0)
            flux -= amp * np.exp(-0.5 * ((t - center) / width) ** 2)
        elif decoy_kind == "step":
            j = rng.integers(onset_idx, reference_idx)
            flux[j:] += amp
        elif decoy_kind == "spike":
            j = rng.integers(onset_idx, reference_idx)
            flux[j] += amp * rng.uniform(1.5, 3.0)
        elif decoy_kind == "red_burst":
            burst = _ar1(rng, n, phi=0.93, sigma=noise_sigma * 1.4)
            mask = np.zeros(n)
            mask[onset_idx:reference_idx + 10] = 1.0
            flux += burst * mask

    return SyntheticSample(
        flux=flux,
        housekeeping=hk,
        instrument_bad=inst_bad,
        kind=kind,
        onset_idx=onset_idx,
        reference_idx=reference_idx,
        cadence_s=cadence_s,
        decoy_kind=decoy_kind,
        instrument_kind=inst_kind,
    )


def generate_dataset(seed: int, n_per_class: int) -> list[SyntheticSample]:
    rng = np.random.default_rng(seed)
    samples: list[SyntheticSample] = []
    for kind in ("event", "decoy", "control"):
        for _ in range(n_per_class):
            samples.append(generate_sample(rng, kind))
    rng.shuffle(samples)
    return samples
