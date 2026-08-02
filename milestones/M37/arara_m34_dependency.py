
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys
from typing import Dict

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEPENDENCY_DIR = ROOT / "dependency"
for directory in (DEPENDENCY_DIR, ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import arara_m33_dependency as m33


m32 = m33.m32
POSITIVE_STRATA = m33.POSITIVE_STRATA
NEGATIVE_FAMILIES = m33.NEGATIVE_FAMILIES
METHODS = (
    "hinge_exact_t50",
    "rolling_hinge_first_crossing",
)


@dataclass(frozen=True)
class Config(m33.Config):
    version: str = "34.0"
    methods: tuple[str, ...] = METHODS

    endpoint_start: int = 81
    endpoint_stop: int = 179
    primary_latency: int = 0
    secondary_latency: int = 4

    calibration_seed: int = 2026082901
    holdout_root_seed: int = 2026082902
    aggregate_bootstrap_root_seed: int = 2026082903
    paired_difference_bootstrap_seed: int = 2026082904

    calibration_batch_size: int = 250

    prediction_exact_range: tuple[float, float] = (0.74, 0.80)
    prediction_rolling_range: tuple[float, float] = (0.20, 0.55)
    prediction_delta_range: tuple[float, float] = (-0.58, -0.20)
    prediction_rolling_pass_low: int = 0
    prediction_rolling_pass_high: int = 3
    prediction_threshold_range: tuple[float, float] = (5.5, 10.0)

    @property
    def endpoint_grid(self) -> np.ndarray:
        return np.arange(
            self.endpoint_start,
            self.endpoint_stop + 1,
            dtype=np.int16,
        )


build_seed_plan = m32.build_seed_plan
calibration_core = m32.calibration_core
sha256_file = m32.sha256_file


def estimate_onset_grid(
    residual: np.ndarray,
    endpoint_grid: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(residual, dtype=np.float64)
    endpoints = np.asarray(
        endpoint_grid,
        dtype=np.int32,
    )
    if y.ndim != 2:
        raise ValueError("residual must be 2D.")
    if endpoints.ndim != 1:
        raise ValueError("endpoint_grid must be 1D.")

    selection_end = (
        endpoints
        - cfg.confirmation_length
        - cfg.guard_length
    )
    if np.any(
        selection_end
        < cfg.selection_start + 2
    ):
        raise ValueError(
            "Endpoint grid begins before the frozen split is valid."
        )
    if np.any(endpoints >= y.shape[1]):
        raise ValueError(
            "Endpoint grid exceeds the curve length."
        )

    candidates = (
        cfg.hinge_config().candidates.astype(
            np.int32
        )
    )
    time = np.arange(
        y.shape[1],
        dtype=np.float64,
    )
    interval = (
        time >= cfg.selection_start
    )
    y_interval = np.where(
        interval[None, :],
        y,
        0.0,
    )

    prefix_y = np.cumsum(
        y_interval,
        axis=1,
    )
    prefix_y2 = np.cumsum(
        np.square(y_interval),
        axis=1,
    )

    hinge = np.maximum(
        0.0,
        time[None, :]
        - candidates[:, None],
    )
    prefix_yh = np.cumsum(
        y[:, None, :]
        * hinge[None, :, :],
        axis=2,
    )
    prefix_h = np.cumsum(
        hinge,
        axis=1,
    )
    prefix_h2 = np.cumsum(
        np.square(hinge),
        axis=1,
    )

    sum_y = prefix_y[:, selection_end]
    sum_y2 = prefix_y2[:, selection_end]
    sum_yh = np.transpose(
        prefix_yh[:, :, selection_end],
        (0, 2, 1),
    )
    sum_h = np.transpose(
        prefix_h[:, selection_end],
        (1, 0),
    )
    sum_h2 = np.transpose(
        prefix_h2[:, selection_end],
        (1, 0),
    )

    count = (
        selection_end
        - cfg.selection_start
        + 1
    ).astype(np.float64)

    covariance = (
        sum_yh
        - (
            sum_y[:, :, None]
            * sum_h[None, :, :]
            / count[None, :, None]
        )
    )
    variance_y = (
        sum_y2
        - np.square(sum_y)
        / count[None, :]
    )[:, :, None]
    variance_h = (
        sum_h2
        - np.square(sum_h)
        / count[:, None]
    )

    denominator = np.sqrt(
        np.maximum(variance_y, 0.0)
        * np.maximum(
            variance_h[None, :, :],
            0.0,
        )
    )
    correlation = np.divide(
        covariance,
        denominator,
        out=np.zeros_like(covariance),
        where=denominator > 1e-12,
    )
    correlation = np.clip(
        correlation,
        -1.0,
        1.0,
    )

    valid = (
        selection_end[None, :, None]
        - candidates[None, None, :]
        + 1
        >= 3
    )
    positive = (
        correlation > 0.0
    ) & valid
    score = np.full_like(
        correlation,
        -np.inf,
    )
    safe = positive & (
        correlation < 1.0 - 1e-15
    )
    degrees = (
        count[None, :, None]
        - 2.0
    )
    score[safe] = (
        correlation[safe]
        * np.sqrt(
            np.broadcast_to(
                degrees,
                correlation.shape,
            )[safe]
            / (
                1.0
                - np.square(
                    correlation[safe]
                )
            )
        )
    )
    score[
        positive
        & (
            correlation
            >= 1.0 - 1e-15
        )
    ] = np.inf

    index = np.argmax(
        score,
        axis=2,
    )
    estimated = candidates[index].astype(
        np.int16
    )
    maximum = np.take_along_axis(
        score,
        index[:, :, None],
        axis=2,
    )[:, :, 0]
    return estimated, maximum


def fixed_endpoint_windows(
    values: np.ndarray,
    endpoint_grid: np.ndarray,
    length: int,
) -> np.ndarray:
    array = np.asarray(
        values,
        dtype=np.float64,
    )
    endpoints = np.asarray(
        endpoint_grid,
        dtype=np.int32,
    )
    offsets = np.arange(
        -length + 1,
        1,
        dtype=np.int32,
    )
    indices = (
        endpoints[:, None]
        + offsets[None, :]
    )
    return array[:, indices]


def variable_endpoint_windows(
    values: np.ndarray,
    endpoints: np.ndarray,
    length: int,
) -> np.ndarray:
    array = np.asarray(
        values,
        dtype=np.float64,
    )
    endpoint = np.asarray(
        endpoints,
        dtype=np.int32,
    )
    offsets = np.arange(
        -length + 1,
        1,
        dtype=np.int32,
    )
    indices = (
        endpoint[:, None]
        + offsets[None, :]
    )
    return np.take_along_axis(
        array,
        indices,
        axis=1,
    )


def _gather_raw(
    raw: np.ndarray,
    source: np.ndarray,
) -> np.ndarray:
    n = raw.shape[0]
    valid = (
        source >= 0
    ) & (
        source < raw.shape[1]
    )
    clipped = np.clip(
        source,
        0,
        raw.shape[1] - 1,
    )
    gathered = np.take_along_axis(
        raw,
        clipped.reshape(n, -1),
        axis=1,
    ).reshape(source.shape)
    return np.where(
        valid,
        gathered,
        0.0,
    )


def processed_template_grid_windows(
    raw_template: np.ndarray,
    reference_onset: np.ndarray,
    estimated_onset_grid: np.ndarray,
    endpoint_grid: np.ndarray,
    params: dict,
    cfg: Config,
) -> np.ndarray:
    raw = np.asarray(
        raw_template,
        dtype=np.float64,
    )
    reference = np.asarray(
        reference_onset,
        dtype=np.int32,
    )
    estimated = np.asarray(
        estimated_onset_grid,
        dtype=np.int32,
    )
    endpoints = np.asarray(
        endpoint_grid,
        dtype=np.int32,
    )

    offsets = (
        estimated
        - reference[:, None]
    )
    window_time = (
        endpoints[:, None]
        + np.arange(
            -cfg.window_length + 1,
            1,
            dtype=np.int32,
        )[None, :]
    )
    current_source = (
        window_time[None, :, :]
        - offsets[:, :, None]
    )
    previous_source = (
        current_source - 1
    )

    current = _gather_raw(
        raw,
        current_source,
    )
    previous = _gather_raw(
        raw,
        previous_source,
    )

    scale = (
        np.asarray(
            params["target_scale"],
            dtype=np.float64,
        )
        * np.asarray(
            params["residual_scale"],
            dtype=np.float64,
        )
    )[:, None, None]
    phi = np.asarray(
        params["residual_phi"],
        dtype=np.float64,
    )[:, None, None]

    return (
        current
        - phi * previous
    ) / scale


def processed_template_variable_window(
    raw_template: np.ndarray,
    reference_onset: np.ndarray,
    estimated_onset: np.ndarray,
    endpoint: np.ndarray,
    params: dict,
    cfg: Config,
) -> np.ndarray:
    raw = np.asarray(
        raw_template,
        dtype=np.float64,
    )
    reference = np.asarray(
        reference_onset,
        dtype=np.int32,
    )
    estimated = np.asarray(
        estimated_onset,
        dtype=np.int32,
    )
    endpoint = np.asarray(
        endpoint,
        dtype=np.int32,
    )

    offset = (
        estimated - reference
    )
    window_time = (
        endpoint[:, None]
        + np.arange(
            -cfg.window_length + 1,
            1,
            dtype=np.int32,
        )[None, :]
    )
    current_source = (
        window_time
        - offset[:, None]
    )
    previous_source = (
        current_source - 1
    )
    current = _gather_raw(
        raw,
        current_source,
    )
    previous = _gather_raw(
        raw,
        previous_source,
    )

    scale = (
        np.asarray(
            params["target_scale"],
            dtype=np.float64,
        )
        * np.asarray(
            params["residual_scale"],
            dtype=np.float64,
        )
    )[:, None]
    phi = np.asarray(
        params["residual_phi"],
        dtype=np.float64,
    )[:, None]
    return (
        current
        - phi * previous
    ) / scale


def projected_window_score(
    residual_window: np.ndarray,
    template_window: np.ndarray,
    reference_window: np.ndarray,
) -> tuple[np.ndarray, dict]:
    residual = np.asarray(
        residual_window,
        dtype=np.float64,
    )
    template = np.asarray(
        template_window,
        dtype=np.float64,
    )
    reference = np.asarray(
        reference_window,
        dtype=np.float64,
    )
    if (
        residual.shape
        != template.shape
        or residual.shape
        != reference.shape
    ):
        raise ValueError(
            "Window shapes must match."
        )

    reference_energy = np.sum(
        np.square(reference),
        axis=-1,
    )
    reference_valid = (
        reference_energy > 1e-12
    )

    residual_coefficient = np.divide(
        np.sum(
            residual * reference,
            axis=-1,
        ),
        reference_energy,
        out=np.zeros_like(
            reference_energy
        ),
        where=reference_valid,
    )
    template_coefficient = np.divide(
        np.sum(
            template * reference,
            axis=-1,
        ),
        reference_energy,
        out=np.zeros_like(
            reference_energy
        ),
        where=reference_valid,
    )

    residual_projected = (
        residual
        - residual_coefficient[..., None]
        * reference
    )
    template_projected = (
        template
        - template_coefficient[..., None]
        * reference
    )

    original_energy = np.sum(
        np.square(template),
        axis=-1,
    )
    projected_energy = np.sum(
        np.square(template_projected),
        axis=-1,
    )
    template_valid = (
        projected_energy > 1e-12
    )

    score = np.divide(
        np.sum(
            residual_projected
            * template_projected,
            axis=-1,
        ),
        np.sqrt(projected_energy),
        out=np.zeros_like(
            projected_energy
        ),
        where=template_valid,
    )
    retention = np.divide(
        projected_energy,
        original_energy,
        out=np.zeros_like(
            projected_energy
        ),
        where=original_energy > 1e-12,
    )
    return (
        score,
        {
            "reference_degenerate": (
                ~reference_valid
            ),
            "template_degenerate": (
                ~template_valid
            ),
            "energy_retention": np.clip(
                retention,
                0.0,
                1.0,
            ),
        },
    )


def exact_hinge_score(
    residual: np.ndarray,
    raw_template: np.ndarray,
    reference_onset: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    params: dict,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray, dict]:
    estimated, objective = (
        m32.estimate_onset_split(
            residual,
            endpoint,
            cfg,
        )
    )
    residual_window = (
        variable_endpoint_windows(
            residual,
            endpoint,
            cfg.window_length,
        )
    )
    reference_window = (
        variable_endpoint_windows(
            processed_reference,
            endpoint,
            cfg.window_length,
        )
    )
    template_window = (
        processed_template_variable_window(
            raw_template,
            reference_onset,
            estimated,
            endpoint,
            params,
            cfg,
        )
    )
    score, diagnostics = (
        projected_window_score(
            residual_window,
            template_window,
            reference_window,
        )
    )
    diagnostics["hinge_objective"] = objective
    return score, estimated, diagnostics


def rolling_hinge_score_grid(
    residual: np.ndarray,
    raw_template: np.ndarray,
    reference_onset: np.ndarray,
    processed_reference: np.ndarray,
    params: dict,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray, dict]:
    endpoints = cfg.endpoint_grid
    estimated, objective = (
        estimate_onset_grid(
            residual,
            endpoints,
            cfg,
        )
    )
    residual_window = (
        fixed_endpoint_windows(
            residual,
            endpoints,
            cfg.window_length,
        )
    )
    reference_window = (
        fixed_endpoint_windows(
            processed_reference,
            endpoints,
            cfg.window_length,
        )
    )
    template_window = (
        processed_template_grid_windows(
            raw_template,
            reference_onset,
            estimated,
            endpoints,
            params,
            cfg,
        )
    )
    score, diagnostics = (
        projected_window_score(
            residual_window,
            template_window,
            reference_window,
        )
    )
    diagnostics["hinge_objective"] = objective
    return score, estimated, diagnostics


def evaluate_positive_panel(
    panel: m32.m22.m9.PositivePanel,
    cfg: Config,
    core: m32.m22.m9.Config,
) -> dict:
    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_signal

    (
        residual,
        exact_processed_signal,
        processed_reference,
        params,
    ) = m32.m30.m29.sbw_with_reference_nuisance(
        observed,
        raw_signal,
        core.data_config(),
    )

    exact_score, exact_onset, exact_diag = (
        exact_hinge_score(
            residual,
            raw_signal,
            panel.onset,
            processed_reference,
            panel.t100,
            params,
            cfg,
        )
    )
    rolling_grid, rolling_onset, rolling_diag = (
        rolling_hinge_score_grid(
            residual,
            raw_signal,
            panel.onset,
            processed_reference,
            params,
            cfg,
        )
    )
    return {
        "exact_score": exact_score,
        "exact_onset": exact_onset,
        "rolling_score_grid": rolling_grid,
        "rolling_onset_grid": rolling_onset,
        "true_onset": panel.onset.astype(np.int16),
        "true_t50": panel.t100.astype(np.int16),
        "exact_diagnostics": exact_diag,
        "rolling_diagnostics": rolling_diag,
    }


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m32.m22.m9.Config,
) -> dict:
    data_cfg = core.data_config()
    data = m32.m22.m2.generate_negative_family(
        family,
        n,
        rng,
        data_cfg,
    )
    virtual_signal, reference_onset, _, _ = (
        m32.m22.m5.generate_virtual_hypotheses(
            n,
            rng,
            data_cfg,
        )
    )
    endpoint = m32.m22.m9.time_at_fraction(
        virtual_signal,
        cfg.target_fraction,
    )
    (
        residual,
        exact_processed_template,
        processed_reference,
        params,
    ) = m32.m30.m29.sbw_with_reference_nuisance(
        data.y,
        virtual_signal,
        data_cfg,
    )

    exact_score, exact_onset, exact_diag = (
        exact_hinge_score(
            residual,
            virtual_signal,
            reference_onset,
            processed_reference,
            endpoint,
            params,
            cfg,
        )
    )
    rolling_grid, rolling_onset, rolling_diag = (
        rolling_hinge_score_grid(
            residual,
            virtual_signal,
            reference_onset,
            processed_reference,
            params,
            cfg,
        )
    )
    return {
        "exact_score": exact_score,
        "exact_onset": exact_onset,
        "rolling_score_grid": rolling_grid,
        "rolling_onset_grid": rolling_onset,
        "reference_onset": reference_onset.astype(np.int16),
        "virtual_t50": endpoint.astype(np.int16),
        "exact_diagnostics": exact_diag,
        "rolling_diagnostics": rolling_diag,
    }


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> dict:
    rng = np.random.default_rng(
        seed_plan["calibration"][family][
            "integer_seed"
        ]
    )
    core = calibration_core(cfg)

    exact_parts = []
    rolling_max_parts = []
    rolling_argmax_parts = []
    rolling_argmax_onset_parts = []
    exact_energy_parts = []
    rolling_energy_at_max_parts = []

    remaining = (
        cfg.calibration_negatives_per_family
    )
    while remaining > 0:
        n = min(
            cfg.calibration_batch_size,
            remaining,
        )
        output = evaluate_negative_family(
            family,
            n,
            rng,
            cfg,
            core,
        )
        grid = output[
            "rolling_score_grid"
        ]
        argmax = np.argmax(
            grid,
            axis=1,
        )
        row = np.arange(n)
        exact_parts.append(
            output["exact_score"].astype(
                np.float32
            )
        )
        rolling_max_parts.append(
            grid[row, argmax].astype(
                np.float32
            )
        )
        rolling_argmax_parts.append(
            cfg.endpoint_grid[argmax].astype(
                np.int16
            )
        )
        rolling_argmax_onset_parts.append(
            output[
                "rolling_onset_grid"
            ][row, argmax].astype(np.int16)
        )
        exact_energy_parts.append(
            output[
                "exact_diagnostics"
            ]["energy_retention"].astype(
                np.float32
            )
        )
        rolling_energy_at_max_parts.append(
            output[
                "rolling_diagnostics"
            ]["energy_retention"][
                row,
                argmax,
            ].astype(np.float32)
        )
        remaining -= n

    result = {
        "score_hinge_exact_t50": np.concatenate(
            exact_parts
        ),
        "score_rolling_hinge_first_crossing": np.concatenate(
            rolling_max_parts
        ),
        "rolling_argmax_endpoint": np.concatenate(
            rolling_argmax_parts
        ),
        "rolling_argmax_onset": np.concatenate(
            rolling_argmax_onset_parts
        ),
        "exact_energy_retention": np.concatenate(
            exact_energy_parts
        ),
        "rolling_energy_at_max": np.concatenate(
            rolling_energy_at_max_parts
        ),
    }
    for key, values in result.items():
        if (
            len(values)
            != cfg.calibration_negatives_per_family
        ):
            raise RuntimeError(
                f"Wrong calibration size: "
                f"{family}, {key}."
            )
    for method in cfg.methods:
        values = result[f"score_{method}"]
        if not np.isfinite(values).all():
            raise RuntimeError(
                f"Non-finite score: "
                f"{family}, {method}."
            )
    return result


def freeze_thresholds(
    cfg: Config,
    family_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    loaded = {}
    diagnostic_rows = []

    for family in NEGATIVE_FAMILIES:
        with np.load(
            family_paths[family]
        ) as data:
            loaded[family] = {
                method: data[
                    f"score_{method}"
                ].copy()
                for method in cfg.methods
            }
            diagnostic_rows.append(
                {
                    "family": family,
                    "n": len(
                        data[
                            "rolling_argmax_endpoint"
                        ]
                    ),
                    "rolling_argmax_endpoint_mean": float(
                        np.mean(
                            data[
                                "rolling_argmax_endpoint"
                            ]
                        )
                    ),
                    "rolling_argmax_endpoint_median": float(
                        np.median(
                            data[
                                "rolling_argmax_endpoint"
                            ]
                        )
                    ),
                    "rolling_argmax_onset_median": float(
                        np.median(
                            data[
                                "rolling_argmax_onset"
                            ]
                        )
                    ),
                    "exact_energy_mean": float(
                        np.mean(
                            data[
                                "exact_energy_retention"
                            ]
                        )
                    ),
                    "rolling_energy_at_max_mean": float(
                        np.mean(
                            data[
                                "rolling_energy_at_max"
                            ]
                        )
                    ),
                }
            )

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []

    for method in cfg.methods:
        by_family = {
            family: loaded[family][method]
            for family in NEGATIVE_FAMILIES
        }
        threshold, specific, allowed = (
            m32.m22.m2.conservative_threshold(
                by_family,
                cfg.development_fpr_target,
            )
        )
        thresholds[method] = float(threshold)
        family_thresholds[method] = specific
        allowed_counts[method] = allowed

        for family in NEGATIVE_FAMILIES:
            values = by_family[family]
            alerts = int(
                np.sum(values >= threshold)
            )
            if alerts > allowed[family]:
                raise RuntimeError(
                    f"Calibration count exceeded: "
                    f"{method}, {family}."
                )
            rows.append(
                {
                    "method": method,
                    "family": family,
                    "threshold": threshold,
                    "family_specific_threshold": (
                        specific[family]
                    ),
                    "alerts": alerts,
                    "n": len(values),
                    "allowed": allowed[family],
                    "rate": alerts / len(values),
                }
            )

    return (
        {
            "thresholds": thresholds,
            "family_thresholds": family_thresholds,
            "allowed_counts": allowed_counts,
            "calibration_negatives_per_family": (
                cfg.calibration_negatives_per_family
            ),
            "rolling_endpoint_count": int(
                len(cfg.endpoint_grid)
            ),
        },
        pd.DataFrame(rows),
        pd.DataFrame(diagnostic_rows),
    )



def evaluate_holdout(
    cfg: Config,
    seed_record: dict,
    thresholds: dict[str, float],
) -> dict:
    analysis = cfg.analysis_config()
    core = analysis.core_config(seed_record)
    batch_sequences = np.random.SeedSequence(
        seed_record["seeds"]["holdout"]
    ).spawn(cfg.holdout_batches)

    positive_hits = {
        method: {
            stratum: []
            for stratum in POSITIVE_STRATA
        }
        for method in cfg.methods
    }
    positive_batch_counts = {
        method: {
            stratum: np.zeros(
                cfg.holdout_batches,
                dtype=np.int64,
            )
            for stratum in POSITIVE_STRATA
        }
        for method in cfg.methods
    }
    positive_batch_ns = {
        method: {
            stratum: np.zeros(
                cfg.holdout_batches,
                dtype=np.int64,
            )
            for stratum in POSITIVE_STRATA
        }
        for method in cfg.methods
    }
    positive_score_parts = {
        method: [] for method in cfg.methods
    }
    negative_score_parts = {
        method: [] for method in cfg.methods
    }
    negative_counts = {
        method: {
            family: 0
            for family in NEGATIVE_FAMILIES
        }
        for method in cfg.methods
    }
    negative_ns = {
        method: {
            family: 0
            for family in NEGATIVE_FAMILIES
        }
        for method in cfg.methods
    }

    timing_frames = []
    negative_timing_rows = []
    projection_rows = []

    for batch, sequence in enumerate(
        batch_sequences
    ):
        children = sequence.spawn(
            len(POSITIVE_STRATA)
            + len(NEGATIVE_FAMILIES)
        )
        rngs = [
            np.random.default_rng(child)
            for child in children
        ]

        for stratum, rng in zip(
            POSITIVE_STRATA,
            rngs[:len(POSITIVE_STRATA)],
        ):
            shape, context = stratum.split("__")
            panel = m32.m22.m9.generate_positive_panel(
                shape,
                context,
                cfg.holdout_positive_per_stratum_per_batch,
                rng,
                core,
            )
            output = evaluate_positive_panel(
                panel,
                cfg,
                core,
            )

            exact_score = output["exact_score"]
            rolling_grid = output[
                "rolling_score_grid"
            ]
            rolling_max = np.max(
                rolling_grid,
                axis=1,
            )
            exact_hits = (
                exact_score
                >= thresholds[
                    "hinge_exact_t50"
                ]
            )

            crossings = (
                rolling_grid
                >= thresholds[
                    "rolling_hinge_first_crossing"
                ]
            )
            any_crossing = np.any(
                crossings,
                axis=1,
            )
            first_index = np.argmax(
                crossings,
                axis=1,
            )
            row = np.arange(
                len(any_crossing)
            )
            first_endpoint = np.where(
                any_crossing,
                cfg.endpoint_grid[first_index],
                -1,
            ).astype(np.int16)
            hinge_at_alert = np.where(
                any_crossing,
                output["rolling_onset_grid"][
                    row,
                    first_index,
                ],
                -1,
            ).astype(np.int16)

            true_onset = output[
                "true_onset"
            ].astype(np.int16)
            true_t50 = output[
                "true_t50"
            ].astype(np.int16)

            primary_hits = (
                any_crossing
                & (
                    first_endpoint
                    >= true_onset
                )
                & (
                    first_endpoint
                    <= true_t50
                    + cfg.primary_latency
                )
            )
            secondary_hits = (
                any_crossing
                & (
                    first_endpoint
                    >= true_onset
                )
                & (
                    first_endpoint
                    <= true_t50
                    + cfg.secondary_latency
                )
            )
            early = (
                any_crossing
                & (
                    first_endpoint
                    < true_onset
                )
            )
            late_1_to_4 = (
                any_crossing
                & (
                    first_endpoint
                    > true_t50
                )
                & (
                    first_endpoint
                    <= true_t50
                    + cfg.secondary_latency
                )
            )
            late_after_4 = (
                any_crossing
                & (
                    first_endpoint
                    > true_t50
                    + cfg.secondary_latency
                )
            )
            no_alert = ~any_crossing

            hits_by_method = {
                "hinge_exact_t50": exact_hits,
                "rolling_hinge_first_crossing": (
                    primary_hits
                ),
            }
            scores_by_method = {
                "hinge_exact_t50": exact_score,
                "rolling_hinge_first_crossing": (
                    rolling_max
                ),
            }

            for method in cfg.methods:
                hits = hits_by_method[method]
                values = scores_by_method[method]
                positive_hits[method][stratum].append(
                    hits
                )
                positive_batch_counts[
                    method
                ][stratum][batch] += int(
                    hits.sum()
                )
                positive_batch_ns[
                    method
                ][stratum][batch] += len(
                    hits
                )
                positive_score_parts[method].append(
                    values.astype(np.float32)
                )

            timing_frames.append(
                pd.DataFrame(
                    {
                        "replication": (
                            seed_record[
                                "replication"
                            ]
                        ),
                        "batch": batch,
                        "stratum": stratum,
                        "true_onset": true_onset,
                        "true_t50": true_t50,
                        "first_endpoint": (
                            first_endpoint
                        ),
                        "rolling_max_score": (
                            rolling_max
                        ),
                        "primary_hit": (
                            primary_hits
                        ),
                        "secondary_hit_t50_plus4": (
                            secondary_hits
                        ),
                        "early_before_onset": (
                            early
                        ),
                        "late_t50_plus1_to4": (
                            late_1_to_4
                        ),
                        "late_after_t50_plus4": (
                            late_after_4
                        ),
                        "no_alert": no_alert,
                        "latency_from_t50": np.where(
                            any_crossing,
                            (
                                first_endpoint
                                - true_t50
                            ),
                            -999,
                        ),
                        "hinge_onset_at_alert": (
                            hinge_at_alert
                        ),
                        "hinge_error_at_alert": np.where(
                            any_crossing,
                            (
                                hinge_at_alert
                                - true_onset
                            ),
                            -999,
                        ),
                    }
                )
            )

            exact_energy = output[
                "exact_diagnostics"
            ]["energy_retention"]
            rolling_energy = output[
                "rolling_diagnostics"
            ]["energy_retention"]
            energy_at_first = np.where(
                any_crossing,
                rolling_energy[
                    row,
                    first_index,
                ],
                np.nan,
            )
            projection_rows.append(
                {
                    "replication": (
                        seed_record[
                            "replication"
                        ]
                    ),
                    "population": "positive",
                    "group": stratum,
                    "n": len(exact_energy),
                    "exact_energy_sum": float(
                        np.sum(exact_energy)
                    ),
                    "rolling_energy_at_first_sum": float(
                        np.nansum(
                            energy_at_first
                        )
                    ),
                    "rolling_alert_n": int(
                        any_crossing.sum()
                    ),
                    "exact_template_degenerate": int(
                        np.sum(
                            output[
                                "exact_diagnostics"
                            ][
                                "template_degenerate"
                            ]
                        )
                    ),
                    "rolling_template_degenerate_at_first": int(
                        np.sum(
                            np.where(
                                any_crossing,
                                output[
                                    "rolling_diagnostics"
                                ][
                                    "template_degenerate"
                                ][
                                    row,
                                    first_index,
                                ],
                                False,
                            )
                        )
                    ),
                }
            )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[len(POSITIVE_STRATA):],
        ):
            output = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            exact_score = output["exact_score"]
            rolling_grid = output[
                "rolling_score_grid"
            ]
            rolling_max = np.max(
                rolling_grid,
                axis=1,
            )
            exact_alerts = (
                exact_score
                >= thresholds[
                    "hinge_exact_t50"
                ]
            )
            crossings = (
                rolling_grid
                >= thresholds[
                    "rolling_hinge_first_crossing"
                ]
            )
            rolling_alerts = np.any(
                crossings,
                axis=1,
            )
            first_index = np.argmax(
                crossings,
                axis=1,
            )
            first_endpoint = np.where(
                rolling_alerts,
                cfg.endpoint_grid[first_index],
                -1,
            )

            for method, values, alerts in (
                (
                    "hinge_exact_t50",
                    exact_score,
                    exact_alerts,
                ),
                (
                    "rolling_hinge_first_crossing",
                    rolling_max,
                    rolling_alerts,
                ),
            ):
                negative_counts[
                    method
                ][family] += int(
                    alerts.sum()
                )
                negative_ns[
                    method
                ][family] += len(
                    alerts
                )
                negative_score_parts[
                    method
                ].append(
                    values.astype(np.float32)
                )

            negative_timing_rows.append(
                {
                    "replication": (
                        seed_record[
                            "replication"
                        ]
                    ),
                    "batch": batch,
                    "family": family,
                    "n": len(
                        rolling_alerts
                    ),
                    "rolling_alerts": int(
                        rolling_alerts.sum()
                    ),
                    "first_endpoint_median": (
                        float(
                            np.median(
                                first_endpoint[
                                    rolling_alerts
                                ]
                            )
                        )
                        if rolling_alerts.any()
                        else np.nan
                    ),
                    "first_endpoint_minimum": (
                        int(
                            np.min(
                                first_endpoint[
                                    rolling_alerts
                                ]
                            )
                        )
                        if rolling_alerts.any()
                        else -1
                    ),
                }
            )

    positive_scores_all = {
        method: np.concatenate(
            positive_score_parts[method]
        )
        for method in cfg.methods
    }
    negative_scores_all = {
        method: np.concatenate(
            negative_score_parts[method]
        )
        for method in cfg.methods
    }

    method_rows = []
    stratum_rows = []
    negative_rows = []
    batch_rows = []

    for method in cfg.methods:
        (
            summary,
            method_strata,
            method_negative,
            method_batches,
        ) = m32._method_holdout_metrics(
            method,
            positive_hits,
            positive_batch_counts,
            positive_batch_ns,
            negative_counts,
            negative_ns,
            positive_scores_all[method],
            negative_scores_all[method],
            thresholds[method],
            seed_record,
            cfg,
        )
        method_rows.append(summary)
        stratum_rows.extend(
            method_strata
        )
        negative_rows.extend(
            method_negative
        )
        batch_rows.extend(
            method_batches
        )

    pair_rows = []
    total_counts = np.zeros(
        4,
        dtype=np.int64,
    )
    for stratum_index, stratum in enumerate(
        POSITIVE_STRATA
    ):
        exact_hits = np.concatenate(
            positive_hits[
                "hinge_exact_t50"
            ][stratum]
        )
        rolling_hits = np.concatenate(
            positive_hits[
                "rolling_hinge_first_crossing"
            ][stratum]
        )
        codes = (
            exact_hits.astype(np.int8) * 2
            + rolling_hits.astype(np.int8)
        )
        counts = np.bincount(
            codes,
            minlength=4,
        )
        total_counts += counts
        pair_rows.append(
            {
                "replication": (
                    seed_record[
                        "replication"
                    ]
                ),
                "stratum_index": stratum_index,
                "stratum": stratum,
                "neither": int(counts[0]),
                "rolling_only": int(
                    counts[1]
                ),
                "exact_only": int(
                    counts[2]
                ),
                "both": int(counts[3]),
                "n": int(counts.sum()),
            }
        )

    method_frame = pd.DataFrame(
        method_rows
    ).set_index("method")
    paired_summary = {
        "replication": (
            seed_record["replication"]
        ),
        "exact_recall": float(
            method_frame.loc[
                "hinge_exact_t50",
                "recall_point",
            ]
        ),
        "rolling_recall": float(
            method_frame.loc[
                "rolling_hinge_first_crossing",
                "recall_point",
            ]
        ),
        "rolling_minus_exact": float(
            method_frame.loc[
                "rolling_hinge_first_crossing",
                "recall_point",
            ]
            - method_frame.loc[
                "hinge_exact_t50",
                "recall_point",
            ]
        ),
        "neither": int(total_counts[0]),
        "rolling_only": int(
            total_counts[1]
        ),
        "exact_only": int(
            total_counts[2]
        ),
        "both": int(total_counts[3]),
        "positive_score_correlation": float(
            np.corrcoef(
                positive_scores_all[
                    "hinge_exact_t50"
                ],
                positive_scores_all[
                    "rolling_hinge_first_crossing"
                ],
            )[0, 1]
        ),
        "negative_score_correlation": float(
            np.corrcoef(
                negative_scores_all[
                    "hinge_exact_t50"
                ],
                negative_scores_all[
                    "rolling_hinge_first_crossing"
                ],
            )[0, 1]
        ),
    }

    return {
        "method_summary": pd.DataFrame(
            method_rows
        ),
        "stratum_summary": pd.DataFrame(
            stratum_rows
        ),
        "negative_summary": pd.DataFrame(
            negative_rows
        ),
        "batch_summary": pd.DataFrame(
            batch_rows
        ),
        "pair_counts": pd.DataFrame(
            pair_rows
        ),
        "paired_summary": pd.DataFrame(
            [paired_summary]
        ),
        "timing_detail": pd.concat(
            timing_frames,
            ignore_index=True,
        ),
        "negative_timing_summary": pd.DataFrame(
            negative_timing_rows
        ),
        "projection_diagnostics": pd.DataFrame(
            projection_rows
        ),
    }


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    method_details = {}
    bootstrap_frames = []
    sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(len(cfg.methods))

    for method_index, method in enumerate(
        cfg.methods
    ):
        rep = method_summary[
            method_summary.method == method
        ].sort_values("replication")
        bootstrap = (
            m32._hierarchical_method_bootstrap(
                cfg,
                method,
                stratum_summary,
                int(
                    sequences[
                        method_index
                    ].generate_state(
                        1,
                        dtype=np.uint32,
                    )[0]
                ),
            )
        )
        point = float(
            rep.recall_point.mean()
        )
        lower = float(
            np.quantile(
                bootstrap,
                0.05,
            )
        )
        upper = float(
            np.quantile(
                bootstrap,
                0.95,
            )
        )
        pass_count = int(
            rep["pass"].sum()
        )
        fpr_pass_count = int(
            rep.fpr_pass.sum()
        )
        extreme = bool(
            np.any(
                rep.maximum_fpr_upper_one_sided_95
                > cfg.extreme_fpr_upper_limit
            )
        )
        fpr_robust = bool(
            fpr_pass_count
            >= cfg.minimum_fpr_pass_holdouts
            and not extreme
        )
        operational_pass = bool(
            pass_count
            >= cfg.minimum_holdout_passes
            and lower
            >= cfg.minimum_global_recall_lower_one_sided_95
            and fpr_robust
        )
        method_details[method] = {
            "method": method,
            "threshold": thresholds[
                method
            ],
            "threshold_driver": (
                threshold_drivers[
                    method
                ]
            ),
            "aggregate_recall_point": point,
            "aggregate_recall_lower_one_sided_95": (
                lower
            ),
            "aggregate_recall_upper_one_sided_95": (
                upper
            ),
            "holdout_pass_count": (
                pass_count
            ),
            "fpr_pass_holdout_count": (
                fpr_pass_count
            ),
            "fpr_robust": fpr_robust,
            "extreme_fpr_violation": (
                extreme
            ),
            "operational_pass": (
                operational_pass
            ),
            "auroc_mean": float(
                rep.auroc.mean()
            ),
            "average_precision_mean": float(
                rep.average_precision.mean()
            ),
        }
        bootstrap_frames.append(
            pd.DataFrame(
                {
                    "method": method,
                    "replicate": np.arange(
                        cfg.bootstrap_replicates
                    ),
                    "recall": bootstrap,
                }
            )
        )

    pair_array = np.zeros(
        (
            cfg.holdout_count,
            len(POSITIVE_STRATA),
            4,
        ),
        dtype=np.int64,
    )
    for _, row in pair_counts.iterrows():
        pair_array[
            int(row.replication),
            int(row.stratum_index),
        ] = [
            int(row.neither),
            int(row.rolling_only),
            int(row.exact_only),
            int(row.both),
        ]

    delta_bootstrap = (
        m32.m30.hierarchical_paired_bootstrap(
            pair_array,
            cfg.bootstrap_replicates,
            cfg.paired_difference_bootstrap_seed,
        )
    )
    exact = method_details[
        "hinge_exact_t50"
    ]
    rolling = method_details[
        "rolling_hinge_first_crossing"
    ]
    delta_point = (
        rolling[
            "aggregate_recall_point"
        ]
        - exact[
            "aggregate_recall_point"
        ]
    )
    delta_lower = float(
        np.quantile(
            delta_bootstrap,
            0.05,
        )
    )
    delta_upper = float(
        np.quantile(
            delta_bootstrap,
            0.95,
        )
    )

    control_valid = bool(
        exact["operational_pass"]
    )

    if not control_valid:
        verdict = (
            "INVALID_M34_EXACT_ENDPOINT_CONTROL"
        )
    elif rolling[
        "operational_pass"
    ]:
        verdict = (
            "PASS_ROLLING_CAUSAL_ENDPOINT_CANDIDATE"
        )
    elif (
        rolling[
            "holdout_pass_count"
        ]
        <= 2
        or rolling[
            "aggregate_recall_upper_one_sided_95"
        ]
        <= cfg.minimum_global_recall_lower_one_sided_95
        or rolling[
            "extreme_fpr_violation"
        ]
    ):
        verdict = (
            "STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT"
        )
    else:
        verdict = (
            "INCONCLUSIVE_ROLLING_CAUSAL_ENDPOINT"
        )

    prediction = {
        "exact_recall_in_range": bool(
            cfg.prediction_exact_range[0]
            <= exact[
                "aggregate_recall_point"
            ]
            <= cfg.prediction_exact_range[1]
        ),
        "rolling_recall_in_range": bool(
            cfg.prediction_rolling_range[0]
            <= rolling[
                "aggregate_recall_point"
            ]
            <= cfg.prediction_rolling_range[1]
        ),
        "delta_in_range": bool(
            cfg.prediction_delta_range[0]
            <= delta_point
            <= cfg.prediction_delta_range[1]
        ),
        "control_valid": control_valid,
        "both_fpr_robust": bool(
            exact["fpr_robust"]
            and rolling["fpr_robust"]
        ),
        "rolling_pass_count_in_range": bool(
            cfg.prediction_rolling_pass_low
            <= rolling[
                "holdout_pass_count"
            ]
            <= cfg.prediction_rolling_pass_high
        ),
        "rolling_threshold_in_range": bool(
            cfg.prediction_threshold_range[0]
            <= rolling["threshold"]
            <= cfg.prediction_threshold_range[1]
        ),
        "overall_verdict_confirmed": bool(
            verdict
            == "STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": verdict,
        "control_valid": control_valid,
        "method_details": method_details,
        "paired_difference": {
            "rolling_minus_exact_point": (
                delta_point
            ),
            "rolling_minus_exact_lower_one_sided_95": (
                delta_lower
            ),
            "rolling_minus_exact_upper_one_sided_95": (
                delta_upper
            ),
        },
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(
            bootstrap_frames,
            ignore_index=True,
        ),
        "delta_bootstrap": delta_bootstrap,
    }


def write_environment(
    path: Path,
) -> None:
    import scipy
    import sklearn

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m33_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m33_dependency.py"
            )
        ),
        "m32_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m32_dependency.py"
            )
        ),
        "m30_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m30_dependency.py"
            )
        ),
    }
    path.write_text(
        json.dumps(
            environment,
            indent=2,
        ),
        encoding="utf-8",
    )
