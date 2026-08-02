import math
import numpy as np
from sklearn.metrics import roc_auc_score

from arara.math_core import (
    photon_count_flat_fnu, photon_count_numeric, encircled_energy_offset_gaussian,
    binomial_tail, beta_binomial_tail, ppv, raw_data_volume_bytes,
    OrbitEnergyInputs, orbit_energy_margin_wh,
)
from arara.synthetic import generate_dataset
from arara.detectors import flux_z_score
from arara.evaluation import calibrate_threshold, _first_crossing


def test_photon_closed_form_matches_numeric():
    p = dict(magnitude_ab=15.0, diameter_m=0.10, exposure_s=120.0,
             lambda_min_m=600e-9, lambda_max_m=1000e-9, throughput=0.35)
    a = photon_count_flat_fnu(**p)
    b = photon_count_numeric(**p)
    assert abs(a - b) / a < 1e-10


def test_jitter_encircled_energy_is_nonincreasing():
    vals = [encircled_energy_offset_gaussian(3.0, 1.0, d) for d in np.linspace(0, 5, 51)]
    assert all(vals[i + 1] <= vals[i] + 1e-12 for i in range(len(vals) - 1))


def test_beta_binomial_zero_rho_limit():
    for p in [0.01, 0.2, 0.7]:
        assert math.isclose(beta_binomial_tail(7, 4, p, 0.0), binomial_tail(7, 4, p), rel_tol=0, abs_tol=1e-15)


def test_ppv_identity():
    got = ppv(0.01, 0.25, 0.10)
    exp = 0.01 * 0.25 / (0.01 * 0.25 + 0.99 * 0.10)
    assert math.isclose(got, exp)


def test_raw_data_volume():
    assert raw_data_volume_bytes(2048, 2048, 16, 432) == 3_623_878_656


def test_energy_accounting_identity():
    x = OrbitEnergyInputs(orbit_minutes=60, sunlight_fraction=0.5, solar_power_w=20,
                          solar_to_bus_efficiency=1.0, base_power_w=5,
                          payload_on_power_w=10, payload_duty_cycle=0.2,
                          heater_energy_wh_per_orbit=1, tx_energy_wh_per_orbit=1)
    # generated=10 Wh; consumed=5+2+1+1=9 Wh
    assert math.isclose(orbit_energy_margin_wh(x), 1.0)


def test_clean_baseline_contract():
    for s in generate_dataset(123, 50):
        assert s.onset_idx > 44


def test_first_crossing_not_argmax():
    score = np.array([0, 0, 2, 1, 9], dtype=float)
    assert _first_crossing(score, 1.5, 0, len(score)) == 2


def test_threshold_uses_non_events_only():
    data = generate_dataset(321, 20)
    th = calibrate_threshold(data, lambda s: flux_z_score(s.flux), 0.05)
    assert np.isfinite(th) and th >= 0
