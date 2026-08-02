from __future__ import annotations

import math
from dataclasses import dataclass
import numpy as np
from scipy.integrate import quad
from scipy.stats import ncx2
from scipy.special import betaln, gammaln, logsumexp

H = 6.62607015e-34  # J s, exact SI
AB_ZERO_W_M2_HZ = 3631e-26  # 3631 Jy


def photon_count_flat_fnu(
    magnitude_ab: float,
    diameter_m: float,
    exposure_s: float,
    lambda_min_m: float,
    lambda_max_m: float,
    throughput: float,
) -> float:
    """Expected detected photons/electrons for flat F_nu and constant throughput.

    N = A * t * eta * F_nu / h * ln(lambda_max/lambda_min).
    Throughput is dimensionless and may include QE.
    """
    if not (lambda_max_m > lambda_min_m > 0):
        raise ValueError("Wavelength bounds must be positive and ordered")
    if diameter_m <= 0 or exposure_s <= 0 or not (0 <= throughput <= 1):
        raise ValueError("Invalid physical parameter")
    area = math.pi * (diameter_m / 2.0) ** 2
    fnu = AB_ZERO_W_M2_HZ * 10 ** (-0.4 * magnitude_ab)
    return area * exposure_s * throughput * fnu / H * math.log(lambda_max_m / lambda_min_m)


def photon_count_numeric(**kwargs: float) -> float:
    """Numerical integration of the same flat-F_nu model for verification."""
    magnitude_ab = kwargs["magnitude_ab"]
    diameter_m = kwargs["diameter_m"]
    exposure_s = kwargs["exposure_s"]
    l1 = kwargs["lambda_min_m"]
    l2 = kwargs["lambda_max_m"]
    throughput = kwargs["throughput"]
    area = math.pi * (diameter_m / 2.0) ** 2
    fnu = AB_ZERO_W_M2_HZ * 10 ** (-0.4 * magnitude_ab)
    val, _ = quad(lambda lam: fnu / (H * lam), l1, l2, epsabs=0.0, epsrel=1e-12)
    return area * exposure_s * throughput * val


def snr_aperture(
    source_e: float,
    sky_e_per_pix: float,
    dark_e_per_pix: float,
    read_noise_e: float,
    n_pix: float,
) -> float:
    if min(source_e, sky_e_per_pix, dark_e_per_pix, read_noise_e, n_pix) < 0:
        raise ValueError("Noise/count inputs must be non-negative")
    variance = source_e + n_pix * (sky_e_per_pix + dark_e_per_pix + read_noise_e**2)
    return 0.0 if variance <= 0 else source_e / math.sqrt(variance)


def encircled_energy_offset_gaussian(radius: float, sigma: float, offset: float) -> float:
    """Circular-aperture encircled energy for a displaced isotropic 2-D Gaussian.

    Equivalent to a non-central chi-square CDF with df=2 and noncentrality (d/sigma)^2.
    """
    if radius < 0 or sigma <= 0 or offset < 0:
        raise ValueError("radius/offset must be non-negative and sigma positive")
    x = (radius / sigma) ** 2
    nc = (offset / sigma) ** 2
    return float(ncx2.cdf(x, df=2, nc=nc))


def ppv(prevalence: float, tpr: float, fpr: float) -> float:
    if not (0 <= prevalence <= 1 and 0 <= tpr <= 1 and 0 <= fpr <= 1):
        raise ValueError("Probabilities must be in [0,1]")
    den = prevalence * tpr + (1 - prevalence) * fpr
    return 0.0 if den == 0 else prevalence * tpr / den


def binomial_tail(n: int, m: int, p: float) -> float:
    from math import comb
    if not (0 <= p <= 1) or not (0 <= m <= n):
        raise ValueError("Invalid binomial parameters")
    return float(sum(comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(m, n + 1)))


def beta_binomial_tail(n: int, m: int, p: float, rho: float) -> float:
    """Exchangeable beta-binomial tail parameterized by marginal p and ICC rho.

    rho=0 is evaluated by the binomial limit. This model is only a sensitivity model;
    exchangeability and a single ICC are assumptions, not empirical facts.
    """
    if rho < 0 or rho >= 1:
        raise ValueError("rho must be in [0,1)")
    if rho == 0:
        return binomial_tail(n, m, p)
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    alpha = p * (1 - rho) / rho
    beta = (1 - p) * (1 - rho) / rho
    terms = []
    for j in range(m, n + 1):
        logcomb = gammaln(n + 1) - gammaln(j + 1) - gammaln(n - j + 1)
        terms.append(logcomb + betaln(alpha + j, beta + n - j) - betaln(alpha, beta))
    return float(math.exp(logsumexp(terms)))


def raw_data_volume_bytes(nx: int, ny: int, bits_per_pixel: int, frames_per_day: int) -> int:
    if min(nx, ny, bits_per_pixel, frames_per_day) < 0:
        raise ValueError("Inputs must be non-negative")
    total_bits = nx * ny * bits_per_pixel * frames_per_day
    return math.ceil(total_bits / 8)


@dataclass(frozen=True)
class OrbitEnergyInputs:
    orbit_minutes: float
    sunlight_fraction: float
    solar_power_w: float
    solar_to_bus_efficiency: float
    base_power_w: float
    payload_on_power_w: float
    payload_duty_cycle: float
    heater_energy_wh_per_orbit: float
    tx_energy_wh_per_orbit: float
    other_energy_wh_per_orbit: float = 0.0


def orbit_energy_margin_wh(x: OrbitEnergyInputs) -> float:
    """Dimensionally explicit per-orbit energy margin.

    This is an accounting identity, not a mission reliability model.
    """
    if x.orbit_minutes <= 0 or not (0 <= x.sunlight_fraction <= 1):
        raise ValueError("Invalid orbit parameters")
    if not (0 <= x.solar_to_bus_efficiency <= 1 and 0 <= x.payload_duty_cycle <= 1):
        raise ValueError("Efficiencies/duty must lie in [0,1]")
    if min(x.solar_power_w, x.base_power_w, x.payload_on_power_w,
           x.heater_energy_wh_per_orbit, x.tx_energy_wh_per_orbit,
           x.other_energy_wh_per_orbit) < 0:
        raise ValueError("Power/energy terms must be non-negative")
    orbit_h = x.orbit_minutes / 60.0
    generated = x.solar_power_w * x.sunlight_fraction * orbit_h * x.solar_to_bus_efficiency
    consumed = (
        x.base_power_w * orbit_h
        + x.payload_on_power_w * x.payload_duty_cycle * orbit_h
        + x.heater_energy_wh_per_orbit
        + x.tx_energy_wh_per_orbit
        + x.other_energy_wh_per_orbit
    )
    return generated - consumed
