
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import platform
import sys
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize_scalar
from numpy.polynomial.legendre import leggauss


ROOT = Path(__file__).resolve().parent

SHAPES = (
    "linear",
    "power_law",
    "exponential",
    "logistic",
)
DURATIONS = np.arange(24, 61, dtype=np.int16)
CANDIDATE_GRID_SIZES = (
    2,
    3,
    5,
    9,
    17,
    33,
    65,
    129,
)


@dataclass(frozen=True)
class Config:
    version: str = "38A.0"

    snr_retention_minimum: float = 0.995
    local_mesh_guard_minimum: float = 0.9955

    full_curve_quadrature_points: int = 512
    full_curve_optimizer_absolute_tolerance: float = 1e-12

    relative_endpoint_start: int = -39
    relative_endpoint_stop: int = 109
    window_length: int = 8

    u_mesh_count: int = 2049
    phi_start: float = 0.0
    phi_stop: float = 0.8
    phi_step: float = 0.025

    degenerate_norm_threshold: float = 1e-12
    refinement_geometry_count: int = 512
    refinement_seed: int = 2026090401
    refinement_tolerance: float = 1e-10

    candidate_grid_sizes: tuple[int, ...] = (
        CANDIDATE_GRID_SIZES
    )

    @property
    def u_mesh(self) -> np.ndarray:
        return np.linspace(
            0.0,
            1.0,
            self.u_mesh_count,
            dtype=np.float64,
        )

    @property
    def phi_mesh(self) -> np.ndarray:
        count = int(
            round(
                (
                    self.phi_stop
                    - self.phi_start
                )
                / self.phi_step
            )
        ) + 1
        return np.linspace(
            self.phi_start,
            self.phi_stop,
            count,
            dtype=np.float64,
        )

    @property
    def relative_endpoints(self) -> np.ndarray:
        return np.arange(
            self.relative_endpoint_start,
            self.relative_endpoint_stop + 1,
            dtype=np.int16,
        )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def uniform_grid(k: int) -> np.ndarray:
    if k < 2:
        raise ValueError(
            "A latent grid must contain at least two points."
        )
    return np.linspace(
        0.0,
        1.0,
        k,
        dtype=np.float64,
    )


def nearest_uniform_grid(
    u: np.ndarray,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(
        u,
        dtype=np.float64,
    )
    scaled = values * (k - 1)
    # Exact midpoint ties are assigned to the lower grid point.
    index = np.floor(
        scaled + 0.5 - 1e-14
    ).astype(np.int64)
    index = np.clip(
        index,
        0,
        k - 1,
    )
    grid = uniform_grid(k)
    return grid[index], index


def shape_values(
    shape: str,
    x: np.ndarray,
    u: np.ndarray | float,
) -> np.ndarray:
    phase = np.asarray(
        x,
        dtype=np.float64,
    )
    latent = np.asarray(
        u,
        dtype=np.float64,
    )

    if shape == "linear":
        return np.broadcast_to(
            phase,
            np.broadcast_shapes(
                latent.shape,
                phase.shape,
            ),
        )

    if shape == "power_law":
        gamma = (
            1.5
            + 1.5 * latent
        )
        return np.power(
            phase,
            gamma,
        )

    if shape == "exponential":
        beta = (
            1.0
            + 3.0 * latent
        )
        return (
            np.exp(
                beta * phase
            )
            - 1.0
        ) / (
            np.exp(beta) - 1.0
        )

    if shape == "logistic":
        q = (
            6.0
            + 6.0 * latent
        )
        g = 1.0 / (
            1.0
            + np.exp(
                -q
                * (
                    phase
                    - 0.5
                )
            )
        )
        g0 = 1.0 / (
            1.0
            + np.exp(
                q / 2.0
            )
        )
        g1 = 1.0 / (
            1.0
            + np.exp(
                -q / 2.0
            )
        )
        return (
            g - g0
        ) / (
            g1 - g0
        )

    raise ValueError(
        f"Unknown shape: {shape}"
    )


def shape_values_outer(
    shape: str,
    u: np.ndarray,
    x: np.ndarray,
) -> np.ndarray:
    latent = np.asarray(
        u,
        dtype=np.float64,
    )[:, None, None]
    phase = np.asarray(
        x,
        dtype=np.float64,
    )[None, :, :]
    return shape_values(
        shape,
        phase,
        latent,
    )


def normalized_weighted_correlation(
    left: np.ndarray,
    right: np.ndarray,
    weights: np.ndarray,
) -> float:
    a = np.asarray(
        left,
        dtype=np.float64,
    )
    b = np.asarray(
        right,
        dtype=np.float64,
    )
    w = np.asarray(
        weights,
        dtype=np.float64,
    )
    numerator = float(
        np.sum(
            w * a * b
        )
    )
    left_energy = float(
        np.sum(
            w * a * a
        )
    )
    right_energy = float(
        np.sum(
            w * b * b
        )
    )
    if (
        left_energy <= 0.0
        or right_energy <= 0.0
    ):
        return np.nan
    return numerator / math.sqrt(
        left_energy
        * right_energy
    )


def full_curve_retention(
    shape: str,
    u: float,
    grid_u: float,
    nodes: np.ndarray,
    weights: np.ndarray,
) -> float:
    if shape == "linear":
        return 1.0
    exact = shape_values(
        shape,
        nodes,
        float(u),
    )
    candidate = shape_values(
        shape,
        nodes,
        float(grid_u),
    )
    return normalized_weighted_correlation(
        exact,
        candidate,
        weights,
    )


def full_curve_gate(
    k: int,
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    raw_nodes, raw_weights = leggauss(
        cfg.full_curve_quadrature_points
    )
    nodes = (
        raw_nodes + 1.0
    ) / 2.0
    weights = raw_weights / 2.0
    grid = uniform_grid(k)

    rows = []
    overall_minimum = 1.0
    overall_condition = None

    for shape in SHAPES:
        if shape == "linear":
            rows.append(
                {
                    "shape": shape,
                    "grid_size": k,
                    "grid_index": 0,
                    "grid_u": 0.0,
                    "cell_lower": 0.0,
                    "cell_upper": 1.0,
                    "minimum_u": 0.0,
                    "minimum_retention": 1.0,
                    "optimizer_success": True,
                }
            )
            continue

        boundaries = np.empty(
            k + 1,
            dtype=np.float64,
        )
        boundaries[0] = 0.0
        boundaries[-1] = 1.0
        boundaries[1:-1] = (
            grid[:-1]
            + grid[1:]
        ) / 2.0

        for grid_index, grid_u in enumerate(
            grid
        ):
            lower = float(
                boundaries[grid_index]
            )
            upper = float(
                boundaries[
                    grid_index + 1
                ]
            )

            def objective(value: float) -> float:
                return full_curve_retention(
                    shape,
                    value,
                    float(grid_u),
                    nodes,
                    weights,
                )

            result = minimize_scalar(
                objective,
                bounds=(
                    lower,
                    upper,
                ),
                method="bounded",
                options={
                    "xatol": (
                        cfg.full_curve_optimizer_absolute_tolerance
                    ),
                    "maxiter": 1000,
                },
            )
            candidates = [
                (
                    float(result.x),
                    float(result.fun),
                ),
                (
                    lower,
                    float(
                        objective(
                            lower
                        )
                    ),
                ),
                (
                    upper,
                    float(
                        objective(
                            upper
                        )
                    ),
                ),
            ]
            minimum_u, minimum = min(
                candidates,
                key=lambda item: item[1],
            )
            rows.append(
                {
                    "shape": shape,
                    "grid_size": k,
                    "grid_index": (
                        grid_index
                    ),
                    "grid_u": float(
                        grid_u
                    ),
                    "cell_lower": lower,
                    "cell_upper": upper,
                    "minimum_u": (
                        minimum_u
                    ),
                    "minimum_retention": (
                        minimum
                    ),
                    "optimizer_success": bool(
                        result.success
                    ),
                }
            )

            if minimum < overall_minimum:
                overall_minimum = minimum
                overall_condition = {
                    "shape": shape,
                    "grid_index": (
                        grid_index
                    ),
                    "grid_u": float(
                        grid_u
                    ),
                    "u": minimum_u,
                }

    return (
        {
            "grid_size": k,
            "minimum_retention": float(
                overall_minimum
            ),
            "minimum_condition": (
                overall_condition
            ),
            "pass": bool(
                overall_minimum
                >= cfg.snr_retention_minimum
            ),
        },
        pd.DataFrame(rows),
    )


def raw_confirmation_sequences(
    shape: str,
    duration: int,
    relative_endpoints: np.ndarray,
    latent: np.ndarray,
) -> np.ndarray:
    positions = (
        np.asarray(
            relative_endpoints,
            dtype=np.float64,
        )[:, None]
        + np.arange(
            -8,
            1,
            dtype=np.float64,
        )[None, :]
    )
    phase = np.clip(
        positions
        / float(duration),
        0.0,
        1.0,
    )
    return shape_values_outer(
        shape,
        latent,
        phase,
    )


def retention_coefficients(
    exact_raw: np.ndarray,
    candidate_raw: np.ndarray,
) -> dict[str, np.ndarray]:
    exact_previous = exact_raw[
        ...,
        :-1,
    ]
    exact_current = exact_raw[
        ...,
        1:,
    ]
    candidate_previous = (
        candidate_raw[
            ...,
            :-1,
        ]
    )
    candidate_current = (
        candidate_raw[
            ...,
            1:,
        ]
    )

    return {
        "dot_current": np.sum(
            exact_current
            * candidate_current,
            axis=-1,
        ),
        "dot_cross": np.sum(
            exact_previous
            * candidate_current
            + exact_current
            * candidate_previous,
            axis=-1,
        ),
        "dot_previous": np.sum(
            exact_previous
            * candidate_previous,
            axis=-1,
        ),
        "exact_current_energy": np.sum(
            exact_current
            * exact_current,
            axis=-1,
        ),
        "exact_cross": np.sum(
            exact_current
            * exact_previous,
            axis=-1,
        ),
        "exact_previous_energy": np.sum(
            exact_previous
            * exact_previous,
            axis=-1,
        ),
        "candidate_current_energy": np.sum(
            candidate_current
            * candidate_current,
            axis=-1,
        ),
        "candidate_cross": np.sum(
            candidate_current
            * candidate_previous,
            axis=-1,
        ),
        "candidate_previous_energy": np.sum(
            candidate_previous
            * candidate_previous,
            axis=-1,
        ),
    }


def retention_from_coefficients(
    coefficients: dict[str, np.ndarray],
    phi: np.ndarray,
    degenerate_threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    value = np.asarray(
        phi,
        dtype=np.float64,
    )[:, None, None]
    squared = value * value

    numerator = (
        coefficients[
            "dot_current"
        ][None, :, :]
        - value
        * coefficients[
            "dot_cross"
        ][None, :, :]
        + squared
        * coefficients[
            "dot_previous"
        ][None, :, :]
    )
    exact_energy = (
        coefficients[
            "exact_current_energy"
        ][None, :, :]
        - 2.0
        * value
        * coefficients[
            "exact_cross"
        ][None, :, :]
        + squared
        * coefficients[
            "exact_previous_energy"
        ][None, :, :]
    )
    candidate_energy = (
        coefficients[
            "candidate_current_energy"
        ][None, :, :]
        - 2.0
        * value
        * coefficients[
            "candidate_cross"
        ][None, :, :]
        + squared
        * coefficients[
            "candidate_previous_energy"
        ][None, :, :]
    )

    exact_energy = np.maximum(
        exact_energy,
        0.0,
    )
    candidate_energy = np.maximum(
        candidate_energy,
        0.0,
    )
    valid = (
        exact_energy
        > degenerate_threshold
    ) & (
        candidate_energy
        > degenerate_threshold
    )
    denominator = np.sqrt(
        exact_energy
        * candidate_energy
    )
    retention = np.divide(
        numerator,
        denominator,
        out=np.full_like(
            numerator,
            np.nan,
        ),
        where=valid,
    )
    return retention, valid


def _lowest_records(
    retention: np.ndarray,
    valid: np.ndarray,
    count: int,
    shape: str,
    duration: int,
    relative_endpoints: np.ndarray,
    u_mesh: np.ndarray,
    phi_mesh: np.ndarray,
    nearest_grid: np.ndarray,
    nearest_index: np.ndarray,
) -> list[dict]:
    flat_valid_indices = np.flatnonzero(
        valid.ravel()
    )
    if len(flat_valid_indices) == 0:
        return []
    flat_values = retention.ravel()[
        flat_valid_indices
    ]
    take = min(
        count,
        len(flat_values),
    )
    local = np.argpartition(
        flat_values,
        take - 1,
    )[:take]
    selected_flat = flat_valid_indices[
        local
    ]
    phi_index, u_index, r_index = (
        np.unravel_index(
            selected_flat,
            retention.shape,
        )
    )

    rows = []
    for p, u, r in zip(
        phi_index,
        u_index,
        r_index,
    ):
        rows.append(
            {
                "shape": shape,
                "duration": int(
                    duration
                ),
                "relative_endpoint": int(
                    relative_endpoints[
                        r
                    ]
                ),
                "phi_index": int(p),
                "phi": float(
                    phi_mesh[p]
                ),
                "u_index": int(u),
                "u": float(
                    u_mesh[u]
                ),
                "nearest_grid_index": int(
                    nearest_index[u]
                ),
                "nearest_grid_u": float(
                    nearest_grid[u]
                ),
                "retention": float(
                    retention[
                        p,
                        u,
                        r,
                    ]
                ),
            }
        )
    return rows


def local_mesh_gate(
    k: int,
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    u_mesh = cfg.u_mesh
    phi_mesh = cfg.phi_mesh
    nearest_grid, nearest_index = (
        nearest_uniform_grid(
            u_mesh,
            k,
        )
    )

    worst_rows = []
    minimum = 1.0
    minimum_condition = None
    valid_count = 0
    degenerate_count = 0
    trivially_identical_count = 0

    all_relative = (
        cfg.relative_endpoints
    )

    for shape in SHAPES:
        if shape == "linear":
            total = (
                len(DURATIONS)
                * len(all_relative)
                * len(u_mesh)
                * len(phi_mesh)
            )
            # r <= 0 is zero-template degenerate.
            degenerate = (
                len(DURATIONS)
                * int(
                    np.sum(
                        all_relative <= 0
                    )
                )
                * len(u_mesh)
                * len(phi_mesh)
            )
            valid_count += (
                total - degenerate
            )
            degenerate_count += (
                degenerate
            )
            trivially_identical_count += (
                total - degenerate
            )
            continue

        for duration in DURATIONS:
            duration_int = int(
                duration
            )
            active_relative = np.arange(
                1,
                duration_int + 8,
                dtype=np.int16,
            )
            exact_raw = (
                raw_confirmation_sequences(
                    shape,
                    duration_int,
                    active_relative,
                    u_mesh,
                )
            )
            candidate_raw = (
                raw_confirmation_sequences(
                    shape,
                    duration_int,
                    active_relative,
                    nearest_grid,
                )
            )
            coefficients = (
                retention_coefficients(
                    exact_raw,
                    candidate_raw,
                )
            )
            retention, valid = (
                retention_from_coefficients(
                    coefficients,
                    phi_mesh,
                    cfg.degenerate_norm_threshold,
                )
            )

            valid_count += int(
                valid.sum()
            )
            degenerate_count += int(
                valid.size
                - valid.sum()
            )

            local_minimum = float(
                np.nanmin(
                    retention
                )
            )
            if local_minimum < minimum:
                index = np.nanargmin(
                    retention
                )
                p, u, r = np.unravel_index(
                    index,
                    retention.shape,
                )
                minimum = local_minimum
                minimum_condition = {
                    "shape": shape,
                    "duration": duration_int,
                    "relative_endpoint": int(
                        active_relative[r]
                    ),
                    "phi": float(
                        phi_mesh[p]
                    ),
                    "u": float(
                        u_mesh[u]
                    ),
                    "nearest_grid_u": float(
                        nearest_grid[u]
                    ),
                }

            worst_rows.extend(
                _lowest_records(
                    retention,
                    valid,
                    8,
                    shape,
                    duration_int,
                    active_relative,
                    u_mesh,
                    phi_mesh,
                    nearest_grid,
                    nearest_index,
                )
            )

            # r <= 0 is degenerate for all u and phi.
            inactive_early = int(
                np.sum(
                    all_relative <= 0
                )
            )
            degenerate_count += (
                inactive_early
                * len(u_mesh)
                * len(phi_mesh)
            )

            # r >= d + 8 is independent of u and has retention 1.
            inactive_late = int(
                np.sum(
                    all_relative
                    >= duration_int + 8
                )
            )
            late_count = (
                inactive_late
                * len(u_mesh)
                * len(phi_mesh)
            )
            valid_count += (
                late_count
            )
            trivially_identical_count += (
                late_count
            )

    worst = pd.DataFrame(
        worst_rows
    )
    if len(worst):
        worst = (
            worst.sort_values(
                "retention",
                ascending=True,
            )
            .drop_duplicates(
                subset=[
                    "shape",
                    "duration",
                    "relative_endpoint",
                    "phi_index",
                    "u_index",
                    "nearest_grid_index",
                ]
            )
            .head(
                cfg.refinement_geometry_count
            )
            .reset_index(
                drop=True
            )
        )

    return (
        {
            "grid_size": k,
            "minimum_retention": (
                minimum
            ),
            "minimum_condition": (
                minimum_condition
            ),
            "valid_evaluations": int(
                valid_count
            ),
            "degenerate_evaluations": int(
                degenerate_count
            ),
            "trivially_identical_evaluations": int(
                trivially_identical_count
            ),
            "guard_pass": bool(
                minimum
                >= cfg.local_mesh_guard_minimum
            ),
        },
        worst,
    )


def local_retention_continuous(
    shape: str,
    duration: int,
    relative_endpoint: int,
    u: float,
    grid_u: float,
    phi: float,
    degenerate_threshold: float,
) -> float:
    raw_exact = raw_confirmation_sequences(
        shape,
        duration,
        np.asarray(
            [relative_endpoint],
            dtype=np.int16,
        ),
        np.asarray(
            [u],
            dtype=np.float64,
        ),
    )[0, 0]
    raw_candidate = (
        raw_confirmation_sequences(
            shape,
            duration,
            np.asarray(
                [relative_endpoint],
                dtype=np.int16,
            ),
            np.asarray(
                [grid_u],
                dtype=np.float64,
            ),
        )[0, 0]
    )
    exact = (
        raw_exact[1:]
        - phi
        * raw_exact[:-1]
    )
    candidate = (
        raw_candidate[1:]
        - phi
        * raw_candidate[:-1]
    )
    exact_energy = float(
        np.dot(
            exact,
            exact,
        )
    )
    candidate_energy = float(
        np.dot(
            candidate,
            candidate,
        )
    )
    if (
        exact_energy
        <= degenerate_threshold
        or candidate_energy
        <= degenerate_threshold
    ):
        return np.nan
    return float(
        np.dot(
            exact,
            candidate,
        )
        / math.sqrt(
            exact_energy
            * candidate_energy
        )
    )


def refine_local_worst(
    k: int,
    worst_mesh: pd.DataFrame,
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    if len(worst_mesh) == 0:
        return (
            {
                "grid_size": k,
                "minimum_retention": 1.0,
                "minimum_condition": None,
                "pass": True,
            },
            pd.DataFrame(),
        )

    du = 1.0 / (
        cfg.u_mesh_count - 1
    )
    dphi = cfg.phi_step
    grid = uniform_grid(k)

    rows = []
    overall = 1.0
    overall_condition = None

    for row_index, row in (
        worst_mesh.iterrows()
    ):
        grid_index = int(
            row.nearest_grid_index
        )
        grid_u = float(
            grid[
                grid_index
            ]
        )

        voronoi_lower = (
            0.0
            if grid_index == 0
            else float(
                (
                    grid[
                        grid_index - 1
                    ]
                    + grid_u
                )
                / 2.0
            )
        )
        voronoi_upper = (
            1.0
            if grid_index == k - 1
            else float(
                (
                    grid_u
                    + grid[
                        grid_index + 1
                    ]
                )
                / 2.0
            )
        )

        u_lower = max(
            0.0,
            float(row.u)
            - du / 2.0,
            voronoi_lower,
        )
        u_upper = min(
            1.0,
            float(row.u)
            + du / 2.0,
            voronoi_upper,
        )
        phi_lower = max(
            cfg.phi_start,
            float(row.phi)
            - dphi / 2.0,
        )
        phi_upper = min(
            cfg.phi_stop,
            float(row.phi)
            + dphi / 2.0,
        )

        def objective(
            values: np.ndarray,
        ) -> float:
            retention = (
                local_retention_continuous(
                    str(row["shape"]),
                    int(
                        row.duration
                    ),
                    int(
                        row.relative_endpoint
                    ),
                    float(
                        values[0]
                    ),
                    grid_u,
                    float(
                        values[1]
                    ),
                    cfg.degenerate_norm_threshold,
                )
            )
            if not np.isfinite(
                retention
            ):
                return 1.0
            return retention

        if (
            u_upper
            <= u_lower
            or phi_upper
            <= phi_lower
        ):
            candidates = [
                (
                    float(row.u),
                    float(row.phi),
                    float(
                        objective(
                            np.asarray(
                                [
                                    row.u,
                                    row.phi,
                                ]
                            )
                        )
                    ),
                )
            ]
            success = True
            evaluations = 1
        else:
            result = differential_evolution(
                objective,
                bounds=[
                    (
                        u_lower,
                        u_upper,
                    ),
                    (
                        phi_lower,
                        phi_upper,
                    ),
                ],
                seed=(
                    cfg.refinement_seed
                    + int(row_index)
                ),
                tol=(
                    cfg.refinement_tolerance
                ),
                atol=0.0,
                polish=True,
                updating="immediate",
                workers=1,
                maxiter=200,
                popsize=8,
            )
            candidates = [
                (
                    float(
                        result.x[0]
                    ),
                    float(
                        result.x[1]
                    ),
                    float(
                        result.fun
                    ),
                ),
                (
                    float(row.u),
                    float(row.phi),
                    float(row.retention),
                ),
            ]
            success = bool(
                result.success
            )
            evaluations = int(
                result.nfev
            )

        minimum_u, minimum_phi, minimum = min(
            candidates,
            key=lambda item: item[2],
        )
        record = {
            "grid_size": k,
            "shape": str(
                row["shape"]
            ),
            "duration": int(
                row.duration
            ),
            "relative_endpoint": int(
                row.relative_endpoint
            ),
            "nearest_grid_index": (
                grid_index
            ),
            "nearest_grid_u": (
                grid_u
            ),
            "coarse_u": float(
                row.u
            ),
            "coarse_phi": float(
                row.phi
            ),
            "coarse_retention": float(
                row.retention
            ),
            "refined_u": minimum_u,
            "refined_phi": (
                minimum_phi
            ),
            "refined_retention": (
                minimum
            ),
            "optimizer_success": (
                success
            ),
            "optimizer_evaluations": (
                evaluations
            ),
        }
        rows.append(record)

        if minimum < overall:
            overall = minimum
            overall_condition = (
                record.copy()
            )

    frame = pd.DataFrame(rows)
    return (
        {
            "grid_size": k,
            "minimum_retention": (
                overall
            ),
            "minimum_condition": (
                overall_condition
            ),
            "pass": bool(
                overall
                >= cfg.snr_retention_minimum
            ),
            "optimizer_success_count": int(
                frame[
                    "optimizer_success"
                ].sum()
            ),
            "optimizer_total_count": int(
                len(frame)
            ),
        },
        frame,
    )


def write_environment(
    path: Path,
) -> None:
    import scipy

    data = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
    }
    path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )
