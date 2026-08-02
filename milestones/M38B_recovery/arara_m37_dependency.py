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

import arara_m36_dependency as m36

m35 = m36.m35
m34 = m36.m34
m32 = m36.m32
m22 = m36.m22
m2 = m36.m2
m9 = m36.m9

SHAPES = m36.SHAPES
SHAPE_TO_INDEX = m36.SHAPE_TO_INDEX
DURATIONS = np.arange(24, 61, dtype=np.int16)
DURATION_TO_INDEX = {int(value): index for index, value in enumerate(DURATIONS)}
POSITIVE_STRATA = m36.POSITIVE_STRATA
NEGATIVE_FAMILIES = m36.NEGATIVE_FAMILIES
METHODS = (
    "rolling_four_shape_exact_duration_latency4",
    "rolling_four_shape_full_duration_bank_latency4",
)


@dataclass(frozen=True)
class Config(m36.Config):
    version: str = "37.0"
    methods: tuple[str, ...] = METHODS
    calibration_batch_size: int = 50

    duration_tolerance: int = 2
    duration_identification_minimum_lower_one_sided_95: float = 0.70
    minimum_duration_identification_holdouts: int = 8

    calibration_seed: int = 2026090201
    holdout_root_seed: int = 2026090202
    aggregate_bootstrap_root_seed: int = 2026090203
    paired_difference_bootstrap_seed: int = 2026090204

    prediction_control_range: tuple[float, float] = (0.73, 0.79)
    prediction_full_range: tuple[float, float] = (0.72, 0.77)
    prediction_delta_range: tuple[float, float] = (-0.05, 0.00)
    prediction_full_threshold_range: tuple[float, float] = (7.2, 8.2)
    prediction_full_pass_low: int = 8
    prediction_full_pass_high: int = 10
    prediction_exact_duration_accuracy_range: tuple[float, float] = (0.03, 0.20)
    prediction_tolerance2_accuracy_range: tuple[float, float] = (0.15, 0.50)


build_seed_plan = m36.build_seed_plan
calibration_core = m36.calibration_core
sha256_file = m36.sha256_file


def build_duration_templates_for_shape(
    shape: str,
    onset: np.ndarray,
    latent_u: np.ndarray,
    n_time: int,
    durations: np.ndarray = DURATIONS,
) -> np.ndarray:
    onset_array = np.asarray(onset, dtype=np.float64)
    latent = np.asarray(latent_u, dtype=np.float64)
    duration_array = np.asarray(durations, dtype=np.float64)
    time = np.arange(n_time, dtype=np.float64)
    x = np.clip(
        (
            time[None, None, :]
            - onset_array[:, None, None]
        )
        / duration_array[None, :, None],
        0.0,
        1.0,
    )
    if shape == "linear":
        return x
    if shape == "power_law":
        gamma = 1.5 + 1.5 * latent
        return x ** gamma[:, None, None]
    if shape == "exponential":
        beta = 1.0 + 3.0 * latent
        return (
            np.exp(beta[:, None, None] * x) - 1.0
        ) / (
            np.exp(beta) - 1.0
        )[:, None, None]
    if shape == "logistic":
        q = 6.0 + 6.0 * latent
        g = 1.0 / (
            1.0
            + np.exp(
                -q[:, None, None]
                * (x - 0.5)
            )
        )
        g0 = 1.0 / (1.0 + np.exp(q / 2.0))
        g1 = 1.0 / (1.0 + np.exp(-q / 2.0))
        return (
            g - g0[:, None, None]
        ) / (
            g1 - g0
        )[:, None, None]
    raise ValueError(f"Unknown shape: {shape}")


def processed_template_duration_windows(
    raw_templates: np.ndarray,
    reference_onset: np.ndarray,
    estimated_onset_grid: np.ndarray,
    endpoint_grid: np.ndarray,
    params: dict,
    cfg: Config,
) -> np.ndarray:
    raw = np.asarray(raw_templates, dtype=np.float64)
    if raw.ndim != 3:
        raise ValueError("raw_templates must have shape (n, hypotheses, time).")
    reference = np.asarray(reference_onset, dtype=np.int32)
    estimated = np.asarray(estimated_onset_grid, dtype=np.int32)
    endpoints = np.asarray(endpoint_grid, dtype=np.int32)
    n, hypothesis_count, n_time = raw.shape
    if reference.shape != (n,):
        raise ValueError("reference_onset shape mismatch.")
    if estimated.shape != (n, len(endpoints)):
        raise ValueError("estimated_onset_grid shape mismatch.")

    offset = estimated - reference[:, None]
    window_time = (
        endpoints[:, None]
        + np.arange(
            -cfg.window_length + 1,
            1,
            dtype=np.int32,
        )[None, :]
    )
    current_source = window_time[None, :, :] - offset[:, :, None]
    previous_source = current_source - 1

    rows = np.arange(n)[:, None, None, None]
    hypotheses = np.arange(hypothesis_count)[None, :, None, None]

    def gather(source: np.ndarray) -> np.ndarray:
        valid = (source >= 0) & (source < n_time)
        clipped = np.clip(source, 0, n_time - 1)
        values = raw[
            rows,
            hypotheses,
            clipped[:, None, :, :],
        ]
        return np.where(valid[:, None, :, :], values, 0.0)

    current = gather(current_source)
    previous = gather(previous_source)
    scale = (
        np.asarray(params["target_scale"], dtype=np.float64)
        * np.asarray(params["residual_scale"], dtype=np.float64)
    )[:, None, None, None]
    phi = np.asarray(
        params["residual_phi"],
        dtype=np.float64,
    )[:, None, None, None]
    return (current - phi * previous) / scale


def projected_scores_hypotheses(
    residual_window: np.ndarray,
    template_windows: np.ndarray,
    reference_window: np.ndarray,
) -> tuple[np.ndarray, dict]:
    residual = np.asarray(residual_window, dtype=np.float64)
    templates = np.asarray(template_windows, dtype=np.float64)
    reference = np.asarray(reference_window, dtype=np.float64)
    if residual.ndim != 3 or reference.shape != residual.shape:
        raise ValueError("residual/reference windows must have shape (n, endpoint, window).")
    if templates.ndim != 4:
        raise ValueError("template_windows must have shape (n, hypothesis, endpoint, window).")
    if templates.shape[0] != residual.shape[0] or templates.shape[2:] != residual.shape[1:]:
        raise ValueError("template window dimensions mismatch.")

    reference_energy = np.sum(reference * reference, axis=-1)
    reference_valid = reference_energy > 1e-12
    residual_coefficient = np.divide(
        np.sum(residual * reference, axis=-1),
        reference_energy,
        out=np.zeros_like(reference_energy),
        where=reference_valid,
    )
    residual_projected = residual - residual_coefficient[:, :, None] * reference

    template_reference_dot = np.sum(
        templates * reference[:, None, :, :],
        axis=-1,
    )
    original_energy = np.sum(templates * templates, axis=-1)
    projected_energy = original_energy - np.divide(
        template_reference_dot * template_reference_dot,
        reference_energy[:, None, :],
        out=np.zeros_like(template_reference_dot),
        where=reference_valid[:, None, :],
    )
    projected_energy = np.maximum(projected_energy, 0.0)
    numerator = np.sum(
        templates * residual_projected[:, None, :, :],
        axis=-1,
    )
    valid_template = projected_energy > 1e-12
    score = np.divide(
        numerator,
        np.sqrt(projected_energy),
        out=np.zeros_like(numerator),
        where=valid_template,
    )
    retention = np.divide(
        projected_energy,
        original_energy,
        out=np.zeros_like(projected_energy),
        where=original_energy > 1e-12,
    )
    return score, {
        "energy_retention": np.clip(retention, 0.0, 1.0),
        "template_degenerate": ~valid_template,
        "reference_degenerate": ~reference_valid,
    }


def score_duration_shape_bank(
    residual: np.ndarray,
    onset: np.ndarray,
    latent_u: np.ndarray,
    template_scale: np.ndarray,
    true_shape_index: np.ndarray,
    true_duration: np.ndarray,
    processed_reference: np.ndarray,
    params: dict,
    cfg: Config,
) -> dict:
    endpoints = cfg.endpoint_grid
    estimated_onset, hinge_objective = m34.estimate_onset_grid(
        residual,
        endpoints,
        cfg,
    )
    residual_window = m34.fixed_endpoint_windows(
        residual,
        endpoints,
        cfg.window_length,
    )
    reference_window = m34.fixed_endpoint_windows(
        processed_reference,
        endpoints,
        cfg.window_length,
    )

    n = residual.shape[0]
    endpoint_count = len(endpoints)
    true_shape = np.asarray(true_shape_index, dtype=np.int64)
    true_duration_index = np.asarray(true_duration, dtype=np.int64) - int(DURATIONS[0])
    if np.any(true_duration_index < 0) or np.any(true_duration_index >= len(DURATIONS)):
        raise ValueError("true duration outside frozen bank.")

    control_score = np.full((n, endpoint_count), -np.inf, dtype=np.float64)
    control_shape = np.full((n, endpoint_count), -1, dtype=np.int8)
    control_energy = np.zeros((n, endpoint_count), dtype=np.float64)

    full_score = np.full((n, endpoint_count), -np.inf, dtype=np.float64)
    full_shape = np.full((n, endpoint_count), -1, dtype=np.int8)
    full_duration = np.full((n, endpoint_count), -1, dtype=np.int16)
    full_energy = np.zeros((n, endpoint_count), dtype=np.float64)

    rows = np.arange(n)
    endpoint_rows = np.arange(endpoint_count)[None, :]
    scale = np.asarray(template_scale, dtype=np.float64)[:, None, None]

    for shape_index, shape in enumerate(SHAPES):
        raw = build_duration_templates_for_shape(
            shape,
            onset,
            latent_u,
            residual.shape[1],
            DURATIONS,
        ) * scale
        processed = processed_template_duration_windows(
            raw,
            onset,
            estimated_onset,
            endpoints,
            params,
            cfg,
        )
        scores, diagnostics = projected_scores_hypotheses(
            residual_window,
            processed,
            reference_window,
        )
        energy = diagnostics["energy_retention"]

        exact_scores = scores[
            rows,
            true_duration_index,
            :,
        ]
        exact_energy = energy[
            rows,
            true_duration_index,
            :,
        ]
        control_update = exact_scores > control_score
        control_score = np.where(control_update, exact_scores, control_score)
        control_shape = np.where(control_update, shape_index, control_shape).astype(np.int8)
        control_energy = np.where(control_update, exact_energy, control_energy)

        best_duration_index = np.argmax(scores, axis=1)
        best_scores = np.take_along_axis(
            scores,
            best_duration_index[:, None, :],
            axis=1,
        )[:, 0, :]
        best_energy = np.take_along_axis(
            energy,
            best_duration_index[:, None, :],
            axis=1,
        )[:, 0, :]
        best_duration = DURATIONS[best_duration_index]

        better = best_scores > full_score
        equal = best_scores == full_score
        lexicographically_earlier = (
            (best_duration < full_duration)
            | (
                (best_duration == full_duration)
                & (shape_index < full_shape)
            )
        )
        update = better | (equal & lexicographically_earlier)
        full_score = np.where(update, best_scores, full_score)
        full_duration = np.where(update, best_duration, full_duration).astype(np.int16)
        full_shape = np.where(update, shape_index, full_shape).astype(np.int8)
        full_energy = np.where(update, best_energy, full_energy)

    return {
        "control_score_grid": control_score,
        "control_shape_index_grid": control_shape,
        "control_energy_grid": control_energy,
        "full_score_grid": full_score,
        "full_shape_index_grid": full_shape,
        "full_duration_grid": full_duration,
        "full_energy_grid": full_energy,
        "estimated_onset_grid": estimated_onset,
        "hinge_objective_grid": hinge_objective,
        "true_shape_index": np.asarray(true_shape_index, dtype=np.int8),
        "true_duration": np.asarray(true_duration, dtype=np.int16),
    }


def evaluate_positive_panel(panel, cfg: Config, core) -> dict:
    template_scale = cfg.fixed_snr * panel.stationary_target_sd
    raw_true = panel.true_shape_values * template_scale[:, None]
    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_true
    residual, _, processed_reference, params = m32.m30.m29.sbw_with_reference_nuisance(
        observed,
        raw_true,
        core.data_config(),
    )
    output = score_duration_shape_bank(
        residual,
        panel.onset,
        panel.latent_u,
        template_scale,
        panel.true_shape_index,
        panel.duration,
        processed_reference,
        params,
        cfg,
    )
    output.update({
        "true_onset": panel.onset.astype(np.int16),
        "true_t50": panel.true_t50.astype(np.int16),
    })
    return output


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core,
) -> dict:
    data_cfg = core.data_config()
    data = m2.generate_negative_family(family, n, rng, data_cfg)
    virtual = m36.generate_virtual_shape_bank(
        n,
        rng,
        cfg,
        data_cfg=data_cfg,
    )
    residual, _, processed_reference, params = m32.m30.m29.sbw_with_reference_nuisance(
        data.y,
        virtual["true_signal"],
        data_cfg,
    )
    output = score_duration_shape_bank(
        residual,
        virtual["onset"],
        virtual["latent_u"],
        np.ones(n, dtype=np.float64),
        virtual["true_shape_index"],
        virtual["duration"],
        processed_reference,
        params,
        cfg,
    )
    output.update({
        "true_onset": virtual["onset"],
        "true_t50": virtual["true_t50"],
    })
    return output


def first_crossing(score_grid: np.ndarray, threshold: float, cfg: Config):
    return m36.first_crossing(score_grid, threshold, cfg)


def generate_calibration_family(family: str, cfg: Config, seed_plan: dict) -> dict:
    rng = np.random.default_rng(seed_plan["calibration"][family]["integer_seed"])
    core = calibration_core(cfg)
    pieces = {key: [] for key in (
        "score_rolling_four_shape_exact_duration_latency4",
        "score_rolling_four_shape_full_duration_bank_latency4",
        "control_argmax_endpoint",
        "full_argmax_endpoint",
        "full_argmax_shape_index",
        "full_argmax_duration",
        "true_shape_index",
        "true_duration",
        "control_energy_at_max",
        "full_energy_at_max",
    )}
    remaining = cfg.calibration_negatives_per_family
    while remaining > 0:
        n = min(cfg.calibration_batch_size, remaining)
        output = evaluate_negative_family(family, n, rng, cfg, core)
        control_grid = output["control_score_grid"]
        full_grid = output["full_score_grid"]
        control_argmax = np.argmax(control_grid, axis=1)
        full_argmax = np.argmax(full_grid, axis=1)
        row = np.arange(n)
        pieces["score_rolling_four_shape_exact_duration_latency4"].append(
            control_grid[row, control_argmax].astype(np.float32)
        )
        pieces["score_rolling_four_shape_full_duration_bank_latency4"].append(
            full_grid[row, full_argmax].astype(np.float32)
        )
        pieces["control_argmax_endpoint"].append(cfg.endpoint_grid[control_argmax].astype(np.int16))
        pieces["full_argmax_endpoint"].append(cfg.endpoint_grid[full_argmax].astype(np.int16))
        pieces["full_argmax_shape_index"].append(
            output["full_shape_index_grid"][row, full_argmax].astype(np.int8)
        )
        pieces["full_argmax_duration"].append(
            output["full_duration_grid"][row, full_argmax].astype(np.int16)
        )
        pieces["true_shape_index"].append(output["true_shape_index"].astype(np.int8))
        pieces["true_duration"].append(output["true_duration"].astype(np.int16))
        pieces["control_energy_at_max"].append(
            output["control_energy_grid"][row, control_argmax].astype(np.float32)
        )
        pieces["full_energy_at_max"].append(
            output["full_energy_grid"][row, full_argmax].astype(np.float32)
        )
        remaining -= n
    result = {key: np.concatenate(values) for key, values in pieces.items()}
    for key, values in result.items():
        if len(values) != cfg.calibration_negatives_per_family:
            raise RuntimeError(f"Wrong calibration size: {family}, {key}")
    for method in cfg.methods:
        values = result[f"score_{method}"]
        if not np.isfinite(values).all():
            raise RuntimeError(f"Non-finite calibration score: {family}, {method}")
    return result


def freeze_thresholds(cfg: Config, family_paths: Dict[str, Path]):
    loaded = {}
    diagnostic_rows = []
    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            loaded[family] = {
                method: data[f"score_{method}"].copy()
                for method in cfg.methods
            }
            duration_error = data["full_argmax_duration"].astype(int) - data["true_duration"].astype(int)
            row = {
                "family": family,
                "n": len(duration_error),
                "control_argmax_endpoint_mean": float(np.mean(data["control_argmax_endpoint"])),
                "full_argmax_endpoint_mean": float(np.mean(data["full_argmax_endpoint"])),
                "full_duration_error_median": float(np.median(duration_error)),
                "full_absolute_duration_error_median": float(np.median(np.abs(duration_error))),
                "control_energy_at_max_mean": float(np.mean(data["control_energy_at_max"])),
                "full_energy_at_max_mean": float(np.mean(data["full_energy_at_max"])),
            }
            for shape_index, shape in enumerate(SHAPES):
                row[f"full_selected_{shape}_fraction"] = float(
                    np.mean(data["full_argmax_shape_index"] == shape_index)
                )
            diagnostic_rows.append(row)

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []
    for method in cfg.methods:
        by_family = {family: loaded[family][method] for family in NEGATIVE_FAMILIES}
        threshold, specific, allowed = m2.conservative_threshold(
            by_family,
            cfg.development_fpr_target,
        )
        thresholds[method] = float(threshold)
        family_thresholds[method] = specific
        allowed_counts[method] = allowed
        for family in NEGATIVE_FAMILIES:
            values = by_family[family]
            alerts = int(np.sum(values >= threshold))
            if alerts > allowed[family]:
                raise RuntimeError(f"Calibration count exceeded: {method}, {family}")
            rows.append({
                "method": method,
                "family": family,
                "threshold": threshold,
                "family_specific_threshold": specific[family],
                "alerts": alerts,
                "n": len(values),
                "allowed": allowed[family],
                "rate": alerts / len(values),
            })
    return (
        {
            "thresholds": thresholds,
            "family_thresholds": family_thresholds,
            "allowed_counts": allowed_counts,
            "calibration_negatives_per_family": cfg.calibration_negatives_per_family,
            "control_hypothesis_count": len(cfg.endpoint_grid) * len(SHAPES),
            "full_hypothesis_count": len(cfg.endpoint_grid) * len(SHAPES) * len(DURATIONS),
        },
        pd.DataFrame(rows),
        pd.DataFrame(diagnostic_rows),
    )


def identification_row(
    replication: int,
    true_duration: np.ndarray,
    selected_duration: np.ndarray,
    true_shape: np.ndarray,
    selected_shape: np.ndarray,
    alert_mask: np.ndarray,
    primary_hit_mask: np.ndarray,
    cfg: Config,
) -> dict:
    true_d = np.asarray(true_duration, dtype=np.int16)
    selected_d = np.asarray(selected_duration, dtype=np.int16)
    true_s = np.asarray(true_shape, dtype=np.int8)
    selected_s = np.asarray(selected_shape, dtype=np.int8)
    alerts = np.asarray(alert_mask, dtype=bool)
    hits = np.asarray(primary_hit_mask, dtype=bool)
    error = selected_d.astype(int) - true_d.astype(int)
    hit_n = int(hits.sum())
    alert_n = int(alerts.sum())
    exact = int(np.sum(hits & (error == 0)))
    tolerant = int(np.sum(hits & (np.abs(error) <= cfg.duration_tolerance)))
    shape_correct = int(np.sum(hits & (selected_s == true_s)))
    tol_lower = m22.m5.clopper_pearson_lower(tolerant, hit_n) if hit_n else 0.0
    tol_upper = m2.clopper_pearson_upper(tolerant, hit_n) if hit_n else 1.0
    exact_lower = m22.m5.clopper_pearson_lower(exact, hit_n) if hit_n else 0.0
    selected_error = error[hits]
    return {
        "replication": replication,
        "alert_n": alert_n,
        "primary_hit_n": hit_n,
        "duration_exact_correct": exact,
        "duration_exact_accuracy": exact / hit_n if hit_n else 0.0,
        "duration_exact_accuracy_lower_one_sided_95": exact_lower,
        "duration_tolerance2_correct": tolerant,
        "duration_tolerance2_accuracy": tolerant / hit_n if hit_n else 0.0,
        "duration_tolerance2_accuracy_lower_one_sided_95": tol_lower,
        "duration_tolerance2_accuracy_upper_one_sided_95": tol_upper,
        "duration_identification_pass": bool(
            tol_lower >= cfg.duration_identification_minimum_lower_one_sided_95
        ),
        "shape_correct": shape_correct,
        "shape_accuracy": shape_correct / hit_n if hit_n else 0.0,
        "duration_error_median": float(np.median(selected_error)) if hit_n else np.nan,
        "duration_absolute_error_median": float(np.median(np.abs(selected_error))) if hit_n else np.nan,
    }


def evaluate_holdout(cfg: Config, seed_record: dict, thresholds: dict[str, float]) -> dict:
    analysis = cfg.analysis_config()
    core = analysis.core_config(seed_record)
    batch_sequences = np.random.SeedSequence(
        seed_record["seeds"]["holdout"]
    ).spawn(cfg.holdout_batches)

    positive_hits = {
        method: {stratum: [] for stratum in POSITIVE_STRATA}
        for method in cfg.methods
    }
    positive_batch_counts = {
        method: {
            stratum: np.zeros(cfg.holdout_batches, dtype=np.int64)
            for stratum in POSITIVE_STRATA
        }
        for method in cfg.methods
    }
    positive_batch_ns = {
        method: {
            stratum: np.zeros(cfg.holdout_batches, dtype=np.int64)
            for stratum in POSITIVE_STRATA
        }
        for method in cfg.methods
    }
    positive_score_parts = {method: [] for method in cfg.methods}
    negative_score_parts = {method: [] for method in cfg.methods}
    negative_counts = {
        method: {family: 0 for family in NEGATIVE_FAMILIES}
        for method in cfg.methods
    }
    negative_ns = {
        method: {family: 0 for family in NEGATIVE_FAMILIES}
        for method in cfg.methods
    }

    timing_frames = []
    negative_selection_rows = []
    projection_rows = []

    for batch, sequence in enumerate(batch_sequences):
        children = sequence.spawn(len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES))
        rngs = [np.random.default_rng(child) for child in children]

        for stratum, rng in zip(POSITIVE_STRATA, rngs[:len(POSITIVE_STRATA)]):
            shape, context = stratum.split("__")
            panel = m36.generate_positive_panel(
                shape,
                context,
                cfg.holdout_positive_per_stratum_per_batch,
                rng,
                cfg,
                data_cfg=core.data_config(),
            )
            output = evaluate_positive_panel(panel, cfg, core)
            control_grid = output["control_score_grid"]
            full_grid = output["full_score_grid"]
            control_max = np.max(control_grid, axis=1)
            full_max = np.max(full_grid, axis=1)
            control_alert, control_first_index, control_first_endpoint = first_crossing(
                control_grid,
                thresholds["rolling_four_shape_exact_duration_latency4"],
                cfg,
            )
            full_alert, full_first_index, full_first_endpoint = first_crossing(
                full_grid,
                thresholds["rolling_four_shape_full_duration_bank_latency4"],
                cfg,
            )
            n = len(full_alert)
            row = np.arange(n)
            selected_duration = np.where(
                full_alert,
                output["full_duration_grid"][row, full_first_index],
                -1,
            ).astype(np.int16)
            selected_shape = np.where(
                full_alert,
                output["full_shape_index_grid"][row, full_first_index],
                -1,
            ).astype(np.int8)
            control_selected_shape = np.where(
                control_alert,
                output["control_shape_index_grid"][row, control_first_index],
                -1,
            ).astype(np.int8)
            true_onset = output["true_onset"]
            true_t50 = output["true_t50"]
            control_hits = (
                control_alert
                & (control_first_endpoint >= true_onset)
                & (control_first_endpoint <= true_t50 + cfg.primary_latency)
            )
            full_hits = (
                full_alert
                & (full_first_endpoint >= true_onset)
                & (full_first_endpoint <= true_t50 + cfg.primary_latency)
            )
            hits_by_method = {
                "rolling_four_shape_exact_duration_latency4": control_hits,
                "rolling_four_shape_full_duration_bank_latency4": full_hits,
            }
            scores_by_method = {
                "rolling_four_shape_exact_duration_latency4": control_max,
                "rolling_four_shape_full_duration_bank_latency4": full_max,
            }
            for method in cfg.methods:
                hits = hits_by_method[method]
                values = scores_by_method[method]
                positive_hits[method][stratum].append(hits)
                positive_batch_counts[method][stratum][batch] += int(hits.sum())
                positive_batch_ns[method][stratum][batch] += len(hits)
                positive_score_parts[method].append(values.astype(np.float32))

            control_hinge = np.where(
                control_alert,
                output["estimated_onset_grid"][row, control_first_index],
                -1,
            ).astype(np.int16)
            full_hinge = np.where(
                full_alert,
                output["estimated_onset_grid"][row, full_first_index],
                -1,
            ).astype(np.int16)
            timing_frames.append(pd.DataFrame({
                "replication": seed_record["replication"],
                "batch": batch,
                "stratum": stratum,
                "true_shape_index": output["true_shape_index"],
                "true_shape": [SHAPES[int(i)] for i in output["true_shape_index"]],
                "true_duration": output["true_duration"],
                "true_onset": true_onset,
                "true_t50": true_t50,
                "control_alert": control_alert,
                "control_first_endpoint": control_first_endpoint,
                "control_primary_hit": control_hits,
                "control_selected_shape_index": control_selected_shape,
                "full_alert": full_alert,
                "full_first_endpoint": full_first_endpoint,
                "full_primary_hit": full_hits,
                "full_selected_shape_index": selected_shape,
                "full_selected_shape": [SHAPES[int(i)] if i >= 0 else "none" for i in selected_shape],
                "full_selected_duration": selected_duration,
                "duration_error": np.where(full_alert, selected_duration - output["true_duration"], -999),
                "control_latency_from_t50": np.where(control_alert, control_first_endpoint - true_t50, -999),
                "full_latency_from_t50": np.where(full_alert, full_first_endpoint - true_t50, -999),
                "control_hinge_error_at_alert": np.where(control_alert, control_hinge - true_onset, -999),
                "full_hinge_error_at_alert": np.where(full_alert, full_hinge - true_onset, -999),
            }))
            control_energy_at_first = np.where(
                control_alert,
                output["control_energy_grid"][row, control_first_index],
                np.nan,
            )
            full_energy_at_first = np.where(
                full_alert,
                output["full_energy_grid"][row, full_first_index],
                np.nan,
            )
            projection_rows.append({
                "replication": seed_record["replication"],
                "population": "positive",
                "group": stratum,
                "n": n,
                "control_alert_n": int(control_alert.sum()),
                "full_alert_n": int(full_alert.sum()),
                "control_energy_at_first_sum": float(np.nansum(control_energy_at_first)),
                "full_energy_at_first_sum": float(np.nansum(full_energy_at_first)),
            })

        for family, rng in zip(NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]):
            output = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            control_grid = output["control_score_grid"]
            full_grid = output["full_score_grid"]
            control_max = np.max(control_grid, axis=1)
            full_max = np.max(full_grid, axis=1)
            control_alert, _, _ = first_crossing(
                control_grid,
                thresholds["rolling_four_shape_exact_duration_latency4"],
                cfg,
            )
            full_alert, full_first_index, full_first_endpoint = first_crossing(
                full_grid,
                thresholds["rolling_four_shape_full_duration_bank_latency4"],
                cfg,
            )
            n = len(full_alert)
            row = np.arange(n)
            selected_duration = np.where(
                full_alert,
                output["full_duration_grid"][row, full_first_index],
                -1,
            ).astype(np.int16)
            selected_shape = np.where(
                full_alert,
                output["full_shape_index_grid"][row, full_first_index],
                -1,
            ).astype(np.int8)
            for method, values, alerts in (
                ("rolling_four_shape_exact_duration_latency4", control_max, control_alert),
                ("rolling_four_shape_full_duration_bank_latency4", full_max, full_alert),
            ):
                negative_counts[method][family] += int(alerts.sum())
                negative_ns[method][family] += len(alerts)
                negative_score_parts[method].append(values.astype(np.float32))
            negative_selection_rows.append({
                "replication": seed_record["replication"],
                "batch": batch,
                "family": family,
                "n": n,
                "full_alerts": int(full_alert.sum()),
                "selected_duration_mean": float(np.mean(selected_duration[full_alert])) if full_alert.any() else np.nan,
                "selected_duration_median": float(np.median(selected_duration[full_alert])) if full_alert.any() else np.nan,
                "selected_linear": int(np.sum(full_alert & (selected_shape == 0))),
                "selected_power_law": int(np.sum(full_alert & (selected_shape == 1))),
                "selected_exponential": int(np.sum(full_alert & (selected_shape == 2))),
                "selected_logistic": int(np.sum(full_alert & (selected_shape == 3))),
                "first_endpoint_mean": float(np.mean(full_first_endpoint[full_alert])) if full_alert.any() else np.nan,
            })

    positive_scores_all = {
        method: np.concatenate(positive_score_parts[method])
        for method in cfg.methods
    }
    negative_scores_all = {
        method: np.concatenate(negative_score_parts[method])
        for method in cfg.methods
    }
    method_rows, stratum_rows, negative_rows, batch_rows = [], [], [], []
    for method in cfg.methods:
        summary, method_strata, method_negative, method_batches = m32._method_holdout_metrics(
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
        stratum_rows.extend(method_strata)
        negative_rows.extend(method_negative)
        batch_rows.extend(method_batches)

    pair_rows = []
    total_counts = np.zeros(4, dtype=np.int64)
    for stratum_index, stratum in enumerate(POSITIVE_STRATA):
        control_hits = np.concatenate(positive_hits["rolling_four_shape_exact_duration_latency4"][stratum])
        full_hits = np.concatenate(positive_hits["rolling_four_shape_full_duration_bank_latency4"][stratum])
        codes = control_hits.astype(np.int8) * 2 + full_hits.astype(np.int8)
        counts = np.bincount(codes, minlength=4)
        total_counts += counts
        pair_rows.append({
            "replication": seed_record["replication"],
            "stratum_index": stratum_index,
            "stratum": stratum,
            "neither": int(counts[0]),
            "full_only": int(counts[1]),
            "control_only": int(counts[2]),
            "both": int(counts[3]),
            "n": int(counts.sum()),
        })

    timing_detail = pd.concat(timing_frames, ignore_index=True)
    identification = identification_row(
        seed_record["replication"],
        timing_detail["true_duration"].to_numpy(),
        timing_detail["full_selected_duration"].to_numpy(),
        timing_detail["true_shape_index"].to_numpy(),
        timing_detail["full_selected_shape_index"].to_numpy(),
        timing_detail["full_alert"].to_numpy(),
        timing_detail["full_primary_hit"].to_numpy(),
        cfg,
    )
    method_frame = pd.DataFrame(method_rows).set_index("method")
    paired_summary = {
        "replication": seed_record["replication"],
        "control_recall": float(method_frame.loc["rolling_four_shape_exact_duration_latency4", "recall_point"]),
        "full_recall": float(method_frame.loc["rolling_four_shape_full_duration_bank_latency4", "recall_point"]),
        "full_minus_control": float(
            method_frame.loc["rolling_four_shape_full_duration_bank_latency4", "recall_point"]
            - method_frame.loc["rolling_four_shape_exact_duration_latency4", "recall_point"]
        ),
        "neither": int(total_counts[0]),
        "full_only": int(total_counts[1]),
        "control_only": int(total_counts[2]),
        "both": int(total_counts[3]),
        "positive_score_correlation": float(np.corrcoef(
            positive_scores_all["rolling_four_shape_exact_duration_latency4"],
            positive_scores_all["rolling_four_shape_full_duration_bank_latency4"],
        )[0, 1]),
        "negative_score_correlation": float(np.corrcoef(
            negative_scores_all["rolling_four_shape_exact_duration_latency4"],
            negative_scores_all["rolling_four_shape_full_duration_bank_latency4"],
        )[0, 1]),
    }
    return {
        "method_summary": pd.DataFrame(method_rows),
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
        "pair_counts": pd.DataFrame(pair_rows),
        "paired_summary": pd.DataFrame([paired_summary]),
        "identification_summary": pd.DataFrame([identification]),
        "timing_detail": timing_detail,
        "negative_selection_summary": pd.DataFrame(negative_selection_rows),
        "projection_diagnostics": pd.DataFrame(projection_rows),
    }


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    identification_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    method_details = {}
    bootstrap_frames = []
    sequences = np.random.SeedSequence(cfg.aggregate_bootstrap_root_seed).spawn(len(cfg.methods))
    for method_index, method in enumerate(cfg.methods):
        rep = method_summary[method_summary.method == method].sort_values("replication")
        bootstrap = m32._hierarchical_method_bootstrap(
            cfg,
            method,
            stratum_summary,
            int(sequences[method_index].generate_state(1, dtype=np.uint32)[0]),
        )
        point = float(rep.recall_point.mean())
        lower = float(np.quantile(bootstrap, 0.05))
        upper = float(np.quantile(bootstrap, 0.95))
        pass_count = int(rep["pass"].sum())
        fpr_pass_count = int(rep.fpr_pass.sum())
        extreme = bool(np.any(rep.maximum_fpr_upper_one_sided_95 > cfg.extreme_fpr_upper_limit))
        fpr_robust = bool(fpr_pass_count >= cfg.minimum_fpr_pass_holdouts and not extreme)
        operational_pass = bool(
            pass_count >= cfg.minimum_holdout_passes
            and lower >= cfg.minimum_global_recall_lower_one_sided_95
            and fpr_robust
        )
        method_details[method] = {
            "method": method,
            "threshold": thresholds[method],
            "threshold_driver": threshold_drivers[method],
            "aggregate_recall_point": point,
            "aggregate_recall_lower_one_sided_95": lower,
            "aggregate_recall_upper_one_sided_95": upper,
            "holdout_pass_count": pass_count,
            "fpr_pass_holdout_count": fpr_pass_count,
            "fpr_robust": fpr_robust,
            "extreme_fpr_violation": extreme,
            "operational_pass": operational_pass,
            "auroc_mean": float(rep.auroc.mean()),
            "average_precision_mean": float(rep.average_precision.mean()),
        }
        bootstrap_frames.append(pd.DataFrame({
            "method": method,
            "replicate": np.arange(cfg.bootstrap_replicates),
            "recall": bootstrap,
        }))

    pair_array = np.zeros((cfg.holdout_count, len(POSITIVE_STRATA), 4), dtype=np.int64)
    for _, row in pair_counts.iterrows():
        pair_array[int(row.replication), int(row.stratum_index)] = [
            int(row.neither), int(row.full_only), int(row.control_only), int(row.both)
        ]
    delta_bootstrap = m32.m30.hierarchical_paired_bootstrap(
        pair_array,
        cfg.bootstrap_replicates,
        cfg.paired_difference_bootstrap_seed,
    )
    control = method_details["rolling_four_shape_exact_duration_latency4"]
    full = method_details["rolling_four_shape_full_duration_bank_latency4"]
    delta_point = full["aggregate_recall_point"] - control["aggregate_recall_point"]
    delta_lower = float(np.quantile(delta_bootstrap, 0.05))
    delta_upper = float(np.quantile(delta_bootstrap, 0.95))

    hit_n = int(identification_summary.primary_hit_n.sum())
    exact_correct = int(identification_summary.duration_exact_correct.sum())
    tol_correct = int(identification_summary.duration_tolerance2_correct.sum())
    shape_correct = int(identification_summary.shape_correct.sum())
    exact_accuracy = exact_correct / hit_n if hit_n else 0.0
    tol_accuracy = tol_correct / hit_n if hit_n else 0.0
    shape_accuracy = shape_correct / hit_n if hit_n else 0.0
    exact_lower = m22.m5.clopper_pearson_lower(exact_correct, hit_n) if hit_n else 0.0
    tol_lower = m22.m5.clopper_pearson_lower(tol_correct, hit_n) if hit_n else 0.0
    tol_upper = m2.clopper_pearson_upper(tol_correct, hit_n) if hit_n else 1.0
    duration_pass_count = int(identification_summary.duration_identification_pass.sum())
    duration_identification_pass = bool(
        tol_lower >= cfg.duration_identification_minimum_lower_one_sided_95
        and duration_pass_count >= cfg.minimum_duration_identification_holdouts
    )

    control_valid = bool(control["operational_pass"])
    if not control_valid:
        verdict = "INVALID_M37_EXACT_DURATION_CONTROL"
    elif full["operational_pass"] and duration_identification_pass:
        verdict = "PASS_FULL_DURATION_BANK_AND_IDENTIFICATION"
    elif full["operational_pass"]:
        verdict = "PASS_DETECTION_DURATION_UNRELIABLE"
    elif (
        full["holdout_pass_count"] <= 2
        or full["aggregate_recall_upper_one_sided_95"] <= cfg.minimum_global_recall_lower_one_sided_95
        or full["extreme_fpr_violation"]
    ):
        verdict = "STRONG_FAIL_FULL_DURATION_BANK"
    else:
        verdict = "INCONCLUSIVE_FULL_DURATION_BANK"

    prediction = {
        "control_recall_in_range": cfg.prediction_control_range[0] <= control["aggregate_recall_point"] <= cfg.prediction_control_range[1],
        "full_recall_in_range": cfg.prediction_full_range[0] <= full["aggregate_recall_point"] <= cfg.prediction_full_range[1],
        "delta_in_range": cfg.prediction_delta_range[0] <= delta_point <= cfg.prediction_delta_range[1],
        "control_valid": control_valid,
        "both_fpr_robust": bool(control["fpr_robust"] and full["fpr_robust"]),
        "full_threshold_in_range": cfg.prediction_full_threshold_range[0] <= full["threshold"] <= cfg.prediction_full_threshold_range[1],
        "full_pass_count_in_range": cfg.prediction_full_pass_low <= full["holdout_pass_count"] <= cfg.prediction_full_pass_high,
        "exact_duration_accuracy_in_range": cfg.prediction_exact_duration_accuracy_range[0] <= exact_accuracy <= cfg.prediction_exact_duration_accuracy_range[1],
        "tolerance2_accuracy_in_range": cfg.prediction_tolerance2_accuracy_range[0] <= tol_accuracy <= cfg.prediction_tolerance2_accuracy_range[1],
        "overall_verdict_confirmed": verdict == "PASS_DETECTION_DURATION_UNRELIABLE",
    }
    prediction["fully_confirmed"] = bool(all(prediction.values()))
    return {
        "verdict": verdict,
        "control_valid": control_valid,
        "method_details": method_details,
        "paired_difference": {
            "full_minus_control_point": delta_point,
            "full_minus_control_lower_one_sided_95": delta_lower,
            "full_minus_control_upper_one_sided_95": delta_upper,
        },
        "duration_identification": {
            "primary_hit_n": hit_n,
            "duration_exact_correct": exact_correct,
            "duration_exact_accuracy": exact_accuracy,
            "duration_exact_accuracy_lower_one_sided_95": exact_lower,
            "duration_tolerance2_correct": tol_correct,
            "duration_tolerance2_accuracy": tol_accuracy,
            "duration_tolerance2_accuracy_lower_one_sided_95": tol_lower,
            "duration_tolerance2_accuracy_upper_one_sided_95": tol_upper,
            "shape_correct": shape_correct,
            "shape_accuracy": shape_accuracy,
            "holdout_pass_count": duration_pass_count,
            "identification_pass": duration_identification_pass,
        },
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(bootstrap_frames, ignore_index=True),
        "delta_bootstrap": delta_bootstrap,
    }


def write_environment(path: Path) -> None:
    import scipy
    import sklearn
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m36_dependency_sha256": sha256_file(ROOT / "arara_m36_dependency.py"),
        "m35_dependency_sha256": sha256_file(ROOT / "arara_m35_dependency.py"),
        "m34_dependency_sha256": sha256_file(ROOT / "arara_m34_dependency.py"),
        "m32_dependency_sha256": sha256_file(ROOT / "arara_m32_dependency.py"),
    }
    path.write_text(json.dumps(environment, indent=2), encoding="utf-8")
