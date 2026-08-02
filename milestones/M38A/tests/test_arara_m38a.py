
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m38a as m38a


def test_candidate_grids_are_frozen():
    cfg = m38a.Config()
    assert cfg.candidate_grid_sizes == (
        2,
        3,
        5,
        9,
        17,
        33,
        65,
        129,
    )
    assert len(m38a.DURATIONS) == 37
    assert len(cfg.relative_endpoints) == 149
    assert len(cfg.u_mesh) == 2049
    assert len(cfg.phi_mesh) == 33


def test_nearest_uniform_grid_ties_go_lower():
    values = np.array(
        [0.0, 0.125, 0.25, 0.375, 1.0]
    )
    nearest, index = m38a.nearest_uniform_grid(
        values,
        5,
    )
    assert np.allclose(
        nearest,
        [0.0, 0.0, 0.25, 0.25, 1.0],
    )
    assert index.tolist() == [0, 0, 1, 1, 4]


def test_shape_endpoints_and_ranges():
    x = np.array([0.0, 0.25, 0.5, 1.0])
    for shape in m38a.SHAPES:
        for u in (0.0, 0.5, 1.0):
            values = m38a.shape_values(shape, x, u)
            assert np.isclose(values[0], 0.0)
            assert np.isclose(values[-1], 1.0)
            assert np.all(values >= -1e-12)
            assert np.all(values <= 1.0 + 1e-12)
            assert np.all(np.diff(values) >= -1e-12)


def test_exact_full_curve_retention_is_one():
    raw_nodes, raw_weights = m38a.leggauss(128)
    nodes = (raw_nodes + 1.0) / 2.0
    weights = raw_weights / 2.0
    for shape in m38a.SHAPES:
        for u in (0.0, 0.17, 0.5, 0.93, 1.0):
            retention = m38a.full_curve_retention(
                shape,
                u,
                u,
                nodes,
                weights,
            )
            assert np.isclose(retention, 1.0, atol=1e-12)


def test_coefficient_retention_matches_direct():
    rng = np.random.default_rng(7)
    exact = rng.normal(size=(5, 4, 9))
    candidate = rng.normal(size=(5, 4, 9))
    coefficients = m38a.retention_coefficients(
        exact,
        candidate,
    )
    phi = np.array([0.0, 0.2, 0.8])
    observed, valid = m38a.retention_from_coefficients(
        coefficients,
        phi,
        1e-12,
    )

    for p, value in enumerate(phi):
        direct_exact = (
            exact[..., 1:]
            - value * exact[..., :-1]
        )
        direct_candidate = (
            candidate[..., 1:]
            - value * candidate[..., :-1]
        )
        numerator = np.sum(
            direct_exact * direct_candidate,
            axis=-1,
        )
        denominator = np.sqrt(
            np.sum(direct_exact**2, axis=-1)
            * np.sum(direct_candidate**2, axis=-1)
        )
        expected = numerator / denominator
        assert np.all(valid[p])
        assert np.allclose(observed[p], expected)


def test_linear_local_retention_is_one():
    for duration in (24, 42, 60):
        for relative_endpoint in (1, 8, duration, duration + 7):
            for phi in (0.0, 0.4, 0.8):
                observed = m38a.local_retention_continuous(
                    "linear",
                    duration,
                    relative_endpoint,
                    0.13,
                    0.91,
                    phi,
                    1e-12,
                )
                assert np.isclose(observed, 1.0, atol=1e-12)


def test_full_gate_is_deterministic():
    cfg = m38a.Config(
        full_curve_quadrature_points=128
    )
    first, first_rows = m38a.full_curve_gate(5, cfg)
    second, second_rows = m38a.full_curve_gate(5, cfg)
    assert first == second
    assert np.array_equal(
        first_rows.to_numpy(),
        second_rows.to_numpy(),
    )
