from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import platform
import sys
from typing import Dict, Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DEPENDENCY_DIR = ROOT / "dependency"
for directory in (DEPENDENCY_DIR, ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import arara_m37r_dependency as m37r

m37 = m37r.m37
m36 = m37.m36
m34 = m37.m34
m32 = m37.m32
m22 = m37.m22
m2 = m37.m2

SHAPES = m37.SHAPES
DURATIONS = m37.DURATIONS
POSITIVE_STRATA = m37.POSITIVE_STRATA
NEGATIVE_FAMILIES = m37.NEGATIVE_FAMILIES
METHODS = (
    "rolling_full_duration_exact_latent_latency4",
    "rolling_full_duration_latent_grid5_latency4",
)


def load_frozen_latent_grid() -> np.ndarray:
    data = json.loads((ROOT / "FROZEN_LATENT_GRID_M38A.json").read_text(encoding="utf-8"))
    if data.get("verdict") != "PASS_M38A_LATENT_GRID_ELIGIBLE_K5":
        raise RuntimeError("M38A latent grid was not eligible.")
    grid = np.asarray(data["latent_grid"], dtype=np.float64)
    expected = np.asarray([0.0, 0.25, 0.5, 0.75, 1.0], dtype=np.float64)
    if not np.array_equal(grid, expected):
        raise RuntimeError("Frozen latent grid differs from preregistration.")
    if int(data["candidate_hypotheses_for_m38b"]) != 73_260:
        raise RuntimeError("M38A hypothesis count mismatch.")
    return grid


LATENT_GRID = load_frozen_latent_grid()


@dataclass(frozen=True)
class Config(m37r.Config):
    version: str = "38B.0"
    methods: tuple[str, ...] = METHODS
    calibration_block_count: int = 4
    calibration_negatives_per_block: int = 50_000
    calibration_negatives_per_family: int = 200_000
    calibration_batch_size: int = 20
    latent_identification_minimum_lower_one_sided_95: float = 0.70
    minimum_latent_identification_holdouts: int = 8
    latent_half_spacing: float = 0.125
    calibration_seed: int = 2026090501
    holdout_root_seed: int = 2026090502
    aggregate_bootstrap_root_seed: int = 2026090503
    paired_difference_bootstrap_seed: int = 2026090504
    prediction_control_threshold_range: tuple[float, float] = (7.00, 7.22)
    prediction_grid_threshold_range: tuple[float, float] = (7.15, 7.55)
    prediction_control_range: tuple[float, float] = (0.745, 0.765)
    prediction_grid_range: tuple[float, float] = (0.725, 0.755)
    prediction_delta_range: tuple[float, float] = (-0.030, 0.000)
    prediction_control_pass_low: int = 7
    prediction_control_pass_high: int = 10
    prediction_grid_pass_low: int = 4
    prediction_grid_pass_high: int = 9

    def __post_init__(self) -> None:
        super().__post_init__()
        if len(LATENT_GRID) != 5:
            raise ValueError("Frozen latent grid must contain five points.")


def _seed_record(sequence: np.random.SeedSequence) -> dict:
    return {
        "integer_seed": int(sequence.generate_state(1, dtype=np.uint32)[0]),
        "entropy": int(sequence.entropy),
        "spawn_key": list(sequence.spawn_key),
    }


def build_seed_plan(cfg: Config) -> dict:
    calibration_sequences = np.random.SeedSequence(cfg.calibration_seed).spawn(
        cfg.calibration_block_count * len(NEGATIVE_FAMILIES)
    )
    blocks = {}
    cursor = 0
    for block in range(cfg.calibration_block_count):
        record = {}
        for family in NEGATIVE_FAMILIES:
            record[family] = _seed_record(calibration_sequences[cursor])
            cursor += 1
        blocks[str(block)] = record
    parent = m37.build_seed_plan(cfg)
    return {"calibration_blocks": blocks, "holdouts": parent["holdouts"]}


def combine_calibration_blocks(
    block_paths: Iterable[Path], expected_per_block: int, expected_total: int
) -> dict[str, np.ndarray]:
    return m37r.combine_calibration_blocks(block_paths, expected_per_block, expected_total)


calibration_core = m37.calibration_core
first_crossing = m37.first_crossing
sha256_file = m37.sha256_file


def nearest_latent_index(values: np.ndarray) -> np.ndarray:
    latent = np.asarray(values, dtype=np.float64)
    scaled = latent * (len(LATENT_GRID) - 1)
    index = np.floor(scaled + 0.5 - 1e-14).astype(np.int64)
    return np.clip(index, 0, len(LATENT_GRID) - 1).astype(np.int8)


def _shape_from_phase(shape: str, phase: np.ndarray, latent: np.ndarray) -> np.ndarray:
    if shape == "linear":
        return np.broadcast_to(phase, np.broadcast_shapes(phase.shape, latent.shape))
    if shape == "power_law":
        return phase ** (1.5 + 1.5 * latent)
    if shape == "exponential":
        beta = 1.0 + 3.0 * latent
        return (np.exp(beta * phase) - 1.0) / (np.exp(beta) - 1.0)
    if shape == "logistic":
        q = 6.0 + 6.0 * latent
        logistic = 1.0 / (1.0 + np.exp(-q * (phase - 0.5)))
        g0 = 1.0 / (1.0 + np.exp(q / 2.0))
        g1 = 1.0 / (1.0 + np.exp(-q / 2.0))
        return (logistic - g0) / (g1 - g0)
    raise ValueError(shape)


def score_latent_grid_bank(
    residual: np.ndarray,
    onset: np.ndarray,
    true_latent_u: np.ndarray,
    template_scale: np.ndarray,
    true_shape_index: np.ndarray,
    true_duration: np.ndarray,
    processed_reference: np.ndarray,
    params: dict,
    cfg: Config,
) -> dict:
    # Exact identity for the veto control.
    parent = m37.score_duration_shape_bank(
        residual,
        onset,
        true_latent_u,
        template_scale,
        true_shape_index,
        true_duration,
        processed_reference,
        params,
        cfg,
    )

    endpoints = cfg.endpoint_grid
    estimated_onset = parent["estimated_onset_grid"]
    residual_window = m34.fixed_endpoint_windows(residual, endpoints, cfg.window_length)
    reference_window = m34.fixed_endpoint_windows(
        processed_reference, endpoints, cfg.window_length
    )
    n = residual.shape[0]
    endpoint_count = len(endpoints)
    durations = DURATIONS.astype(np.float64)

    positions = (
        endpoints[None, :, None].astype(np.float64)
        + np.arange(-8, 1, dtype=np.float64)[None, None, :]
        - estimated_onset[:, :, None].astype(np.float64)
    )
    absolute_source = positions + np.asarray(onset, dtype=np.float64)[:, None, None]
    source_valid = (absolute_source >= 0.0) & (absolute_source < residual.shape[1])
    phase = np.clip(
        positions[:, None, :, :] / durations[None, :, None, None], 0.0, 1.0
    )
    phi = np.asarray(params["residual_phi"], dtype=np.float64)[:, None, None, None]

    grid_score = np.full((n, endpoint_count), -np.inf, dtype=np.float64)
    grid_shape = np.full((n, endpoint_count), -1, dtype=np.int8)
    grid_duration = np.full((n, endpoint_count), -1, dtype=np.int16)
    grid_latent_index = np.full((n, endpoint_count), -1, dtype=np.int8)
    grid_energy = np.zeros((n, endpoint_count), dtype=np.float64)

    for shape_index, shape in enumerate(SHAPES):
        if shape == "linear":
            raw_grid = phase * source_valid[:, None, :, :]
            processed_grid = raw_grid[..., 1:] - phi * raw_grid[..., :-1]
            grid_scores, grid_diagnostics = m37.projected_scores_hypotheses(
                residual_window, processed_grid, reference_window
            )
            best_hypothesis_index = np.argmax(grid_scores, axis=1)
            best_latent_index = np.zeros_like(best_hypothesis_index, dtype=np.int8)
            best_duration = DURATIONS[best_hypothesis_index]
        else:
            latent_grid = LATENT_GRID[None, :, None, None, None]
            phase_grid = phase[:, None, :, :, :]
            raw_grid_5d = _shape_from_phase(shape, phase_grid, latent_grid)
            raw_grid_5d = raw_grid_5d * source_valid[:, None, None, :, :]
            processed_grid_5d = (
                raw_grid_5d[..., 1:]
                - phi[:, None, :, :, :] * raw_grid_5d[..., :-1]
            )
            processed_grid = processed_grid_5d.reshape(
                n,
                len(LATENT_GRID) * len(DURATIONS),
                endpoint_count,
                cfg.window_length,
            )
            grid_scores, grid_diagnostics = m37.projected_scores_hypotheses(
                residual_window, processed_grid, reference_window
            )
            best_hypothesis_index = np.argmax(grid_scores, axis=1)
            best_latent_index = (
                best_hypothesis_index // len(DURATIONS)
            ).astype(np.int8)
            best_duration = DURATIONS[best_hypothesis_index % len(DURATIONS)]

        best_scores = np.take_along_axis(
            grid_scores, best_hypothesis_index[:, None, :], axis=1
        )[:, 0, :]
        best_energy = np.take_along_axis(
            grid_diagnostics["energy_retention"],
            best_hypothesis_index[:, None, :],
            axis=1,
        )[:, 0, :]
        better = best_scores > grid_score
        equal = best_scores == grid_score
        earlier = (best_latent_index < grid_latent_index) | (
            (best_latent_index == grid_latent_index)
            & (
                (best_duration < grid_duration)
                | ((best_duration == grid_duration) & (shape_index < grid_shape))
            )
        )
        update = better | (equal & earlier)
        grid_score = np.where(update, best_scores, grid_score)
        grid_shape = np.where(update, shape_index, grid_shape).astype(np.int8)
        grid_duration = np.where(update, best_duration, grid_duration).astype(np.int16)
        grid_latent_index = np.where(
            update, best_latent_index, grid_latent_index
        ).astype(np.int8)
        grid_energy = np.where(update, best_energy, grid_energy)

    return {
        "control_score_grid": parent["full_score_grid"],
        "control_shape_index_grid": parent["full_shape_index_grid"],
        "control_duration_grid": parent["full_duration_grid"],
        "control_energy_grid": parent["full_energy_grid"],
        "grid_score_grid": grid_score,
        "grid_shape_index_grid": grid_shape,
        "grid_duration_grid": grid_duration,
        "grid_latent_index_grid": grid_latent_index,
        "grid_latent_value_grid": LATENT_GRID[
            np.clip(grid_latent_index, 0, len(LATENT_GRID) - 1)
        ],
        "grid_energy_grid": grid_energy,
        "estimated_onset_grid": estimated_onset,
        "hinge_objective_grid": parent["hinge_objective_grid"],
        "true_shape_index": np.asarray(true_shape_index, dtype=np.int8),
        "true_duration": np.asarray(true_duration, dtype=np.int16),
        "true_latent_u": np.asarray(true_latent_u, dtype=np.float64),
        "nearest_latent_index": nearest_latent_index(true_latent_u),
    }


def evaluate_positive_panel(panel, cfg: Config, core) -> dict:
    template_scale = cfg.fixed_snr * panel.stationary_target_sd
    raw_true = panel.true_shape_values * template_scale[:, None]
    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_true
    residual, _, processed_reference, params = m32.m30.m29.sbw_with_reference_nuisance(
        observed, raw_true, core.data_config()
    )
    output = score_latent_grid_bank(
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
    output.update(
        {"true_onset": panel.onset.astype(np.int16), "true_t50": panel.true_t50.astype(np.int16)}
    )
    return output


def evaluate_negative_family(
    family: str, n: int, rng: np.random.Generator, cfg: Config, core
) -> dict:
    data_cfg = core.data_config()
    data = m2.generate_negative_family(family, n, rng, data_cfg)
    virtual = m36.generate_virtual_shape_bank(n, rng, cfg, data_cfg=data_cfg)
    residual, _, processed_reference, params = m32.m30.m29.sbw_with_reference_nuisance(
        data.y, virtual["true_signal"], data_cfg
    )
    output = score_latent_grid_bank(
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
    output.update({"true_onset": virtual["onset"], "true_t50": virtual["true_t50"]})
    return output

def calibration_output_from_rng(family: str, n_total: int, rng, cfg: Config) -> dict:
    core = calibration_core(cfg)
    keys = (
        "score_rolling_full_duration_exact_latent_latency4",
        "score_rolling_full_duration_latent_grid5_latency4",
        "control_argmax_endpoint",
        "grid_argmax_endpoint",
        "grid_argmax_shape_index",
        "grid_argmax_duration",
        "grid_argmax_latent_index",
        "grid_argmax_latent_value",
        "true_shape_index",
        "true_duration",
        "true_latent_u",
        "nearest_latent_index",
        "control_energy_at_max",
        "grid_energy_at_max",
    )
    pieces = {key: [] for key in keys}
    remaining = n_total
    while remaining > 0:
        n = min(cfg.calibration_batch_size, remaining)
        output = evaluate_negative_family(family, n, rng, cfg, core)
        control = output["control_score_grid"]
        grid = output["grid_score_grid"]
        control_argmax = np.argmax(control, axis=1)
        grid_argmax = np.argmax(grid, axis=1)
        row = np.arange(n)
        pieces[keys[0]].append(control[row, control_argmax].astype(np.float32))
        pieces[keys[1]].append(grid[row, grid_argmax].astype(np.float32))
        pieces["control_argmax_endpoint"].append(cfg.endpoint_grid[control_argmax].astype(np.int16))
        pieces["grid_argmax_endpoint"].append(cfg.endpoint_grid[grid_argmax].astype(np.int16))
        pieces["grid_argmax_shape_index"].append(output["grid_shape_index_grid"][row, grid_argmax].astype(np.int8))
        pieces["grid_argmax_duration"].append(output["grid_duration_grid"][row, grid_argmax].astype(np.int16))
        pieces["grid_argmax_latent_index"].append(output["grid_latent_index_grid"][row, grid_argmax].astype(np.int8))
        pieces["grid_argmax_latent_value"].append(output["grid_latent_value_grid"][row, grid_argmax].astype(np.float32))
        pieces["true_shape_index"].append(output["true_shape_index"].astype(np.int8))
        pieces["true_duration"].append(output["true_duration"].astype(np.int16))
        pieces["true_latent_u"].append(output["true_latent_u"].astype(np.float32))
        pieces["nearest_latent_index"].append(output["nearest_latent_index"].astype(np.int8))
        pieces["control_energy_at_max"].append(output["control_energy_grid"][row, control_argmax].astype(np.float32))
        pieces["grid_energy_at_max"].append(output["grid_energy_grid"][row, grid_argmax].astype(np.float32))
        remaining -= n
    result = {key: np.concatenate(values) for key, values in pieces.items()}
    for key, values in result.items():
        if len(values) != n_total:
            raise RuntimeError(f"wrong calibration size {family} {key}")
    return result


def freeze_thresholds(cfg: Config, family_paths: Dict[str, Path]):
    loaded = {}
    diagnostics = []
    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            loaded[family] = {method: data[f"score_{method}"].copy() for method in cfg.methods}
            latent_error = data["grid_argmax_latent_value"].astype(float) - data["true_latent_u"].astype(float)
            duration_error = data["grid_argmax_duration"].astype(int) - data["true_duration"].astype(int)
            row = {
                "family": family,
                "n": len(latent_error),
                "control_argmax_endpoint_mean": float(np.mean(data["control_argmax_endpoint"])),
                "grid_argmax_endpoint_mean": float(np.mean(data["grid_argmax_endpoint"])),
                "grid_latent_error_median": float(np.median(latent_error)),
                "grid_absolute_latent_error_median": float(np.median(np.abs(latent_error))),
                "grid_duration_error_median": float(np.median(duration_error)),
                "grid_absolute_duration_error_median": float(np.median(np.abs(duration_error))),
                "control_energy_at_max_mean": float(np.mean(data["control_energy_at_max"])),
                "grid_energy_at_max_mean": float(np.mean(data["grid_energy_at_max"])),
            }
            for i, value in enumerate(LATENT_GRID):
                row[f"selected_u_{value:.2f}_fraction"] = float(np.mean(data["grid_argmax_latent_index"] == i))
            diagnostics.append(row)
    thresholds, family_thresholds, allowed_counts, rows = {}, {}, {}, []
    for method in cfg.methods:
        by_family = {family: loaded[family][method] for family in NEGATIVE_FAMILIES}
        threshold, specific, allowed = m2.conservative_threshold(by_family, cfg.development_fpr_target)
        thresholds[method] = float(threshold)
        family_thresholds[method] = specific
        allowed_counts[method] = allowed
        for family in NEGATIVE_FAMILIES:
            values = by_family[family]
            alerts = int(np.sum(values >= threshold))
            if alerts > allowed[family]:
                raise RuntimeError(f"calibration exceeded {method} {family}")
            rows.append({
                "method": method,
                "family": family,
                "threshold": float(threshold),
                "family_specific_threshold": float(specific[family]),
                "alerts": alerts,
                "n": len(values),
                "allowed": int(allowed[family]),
                "rate": alerts / len(values),
            })
    return (
        {
            "thresholds": thresholds,
            "family_thresholds": family_thresholds,
            "allowed_counts": allowed_counts,
            "calibration_negatives_per_family": cfg.calibration_negatives_per_family,
            "control_hypothesis_count": len(cfg.endpoint_grid) * len(SHAPES) * len(DURATIONS),
            "grid_hypothesis_count": len(cfg.endpoint_grid) * len(SHAPES) * len(DURATIONS) * len(LATENT_GRID),
            "latent_grid": LATENT_GRID.tolist(),
        },
        pd.DataFrame(rows),
        pd.DataFrame(diagnostics),
    )


def latent_identification_row(
    replication,
    true_latent,
    nearest_index,
    selected_latent_index,
    selected_latent_value,
    true_duration,
    selected_duration,
    true_shape,
    selected_shape,
    alert_mask,
    primary_hit_mask,
    cfg: Config,
):
    true_u = np.asarray(true_latent, float)
    nearest = np.asarray(nearest_index, np.int8)
    selected_index = np.asarray(selected_latent_index, np.int8)
    selected_u = np.asarray(selected_latent_value, float)
    hits = np.asarray(primary_hit_mask, bool)
    alerts = np.asarray(alert_mask, bool)
    hit_n = int(hits.sum())
    nearest_correct = int(np.sum(hits & (selected_index == nearest)))
    absolute_error = np.abs(selected_u - true_u)
    half = int(np.sum(hits & (absolute_error <= cfg.latent_half_spacing + 1e-12)))
    quarter = int(np.sum(hits & (absolute_error <= 0.25 + 1e-12)))
    duration_exact = int(np.sum(hits & (np.asarray(selected_duration) == np.asarray(true_duration))))
    shape_correct = int(np.sum(hits & (np.asarray(selected_shape) == np.asarray(true_shape))))
    lower = m22.m5.clopper_pearson_lower(nearest_correct, hit_n) if hit_n else 0.0
    upper = m2.clopper_pearson_upper(nearest_correct, hit_n) if hit_n else 1.0
    errors = absolute_error[hits]
    signed = (selected_u - true_u)[hits]
    return {
        "replication": replication,
        "alert_n": int(alerts.sum()),
        "primary_hit_n": hit_n,
        "nearest_cell_correct": nearest_correct,
        "nearest_cell_accuracy": nearest_correct / hit_n if hit_n else 0.0,
        "nearest_cell_accuracy_lower_one_sided_95": lower,
        "nearest_cell_accuracy_upper_one_sided_95": upper,
        "latent_within_half_spacing_correct": half,
        "latent_within_half_spacing_accuracy": half / hit_n if hit_n else 0.0,
        "latent_within_quarter_correct": quarter,
        "latent_within_quarter_accuracy": quarter / hit_n if hit_n else 0.0,
        "latent_identification_pass": bool(lower >= cfg.latent_identification_minimum_lower_one_sided_95),
        "latent_error_median": float(np.median(signed)) if hit_n else np.nan,
        "latent_absolute_error_median": float(np.median(errors)) if hit_n else np.nan,
        "duration_exact_correct": duration_exact,
        "duration_exact_accuracy": duration_exact / hit_n if hit_n else 0.0,
        "shape_correct": shape_correct,
        "shape_accuracy": shape_correct / hit_n if hit_n else 0.0,
    }

def evaluate_holdout(cfg: Config, seed_record: dict, thresholds: dict[str, float]) -> dict:
    analysis = cfg.analysis_config()
    core = analysis.core_config(seed_record)
    batch_sequences = np.random.SeedSequence(seed_record["seeds"]["holdout"]).spawn(cfg.holdout_batches)
    control_method, grid_method = cfg.methods

    positive_hits = {method: {stratum: [] for stratum in POSITIVE_STRATA} for method in cfg.methods}
    positive_batch_counts = {
        method: {stratum: np.zeros(cfg.holdout_batches, dtype=np.int64) for stratum in POSITIVE_STRATA}
        for method in cfg.methods
    }
    positive_batch_ns = {
        method: {stratum: np.zeros(cfg.holdout_batches, dtype=np.int64) for stratum in POSITIVE_STRATA}
        for method in cfg.methods
    }
    positive_score_parts = {method: [] for method in cfg.methods}
    negative_score_parts = {method: [] for method in cfg.methods}
    negative_counts = {method: {family: 0 for family in NEGATIVE_FAMILIES} for method in cfg.methods}
    negative_ns = {method: {family: 0 for family in NEGATIVE_FAMILIES} for method in cfg.methods}
    timing_frames, negative_selection_rows, projection_rows = [], [], []

    for batch, sequence in enumerate(batch_sequences):
        children = sequence.spawn(len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES))
        rngs = [np.random.default_rng(child) for child in children]

        for stratum, rng in zip(POSITIVE_STRATA, rngs[: len(POSITIVE_STRATA)]):
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
            candidate_grid = output["grid_score_grid"]
            control_max, candidate_max = np.max(control_grid, axis=1), np.max(candidate_grid, axis=1)
            control_alert, control_first_index, control_first_endpoint = first_crossing(
                control_grid, thresholds[control_method], cfg
            )
            grid_alert, grid_first_index, grid_first_endpoint = first_crossing(
                candidate_grid, thresholds[grid_method], cfg
            )
            n = len(grid_alert)
            row = np.arange(n)
            control_selected_duration = np.where(
                control_alert, output["control_duration_grid"][row, control_first_index], -1
            ).astype(np.int16)
            control_selected_shape = np.where(
                control_alert, output["control_shape_index_grid"][row, control_first_index], -1
            ).astype(np.int8)
            selected_duration = np.where(
                grid_alert, output["grid_duration_grid"][row, grid_first_index], -1
            ).astype(np.int16)
            selected_shape = np.where(
                grid_alert, output["grid_shape_index_grid"][row, grid_first_index], -1
            ).astype(np.int8)
            selected_latent_index = np.where(
                grid_alert, output["grid_latent_index_grid"][row, grid_first_index], -1
            ).astype(np.int8)
            selected_latent_value = np.where(
                grid_alert, output["grid_latent_value_grid"][row, grid_first_index], np.nan
            ).astype(float)
            true_onset, true_t50 = output["true_onset"], output["true_t50"]
            control_hits = control_alert & (control_first_endpoint >= true_onset) & (
                control_first_endpoint <= true_t50 + cfg.primary_latency
            )
            grid_hits = grid_alert & (grid_first_endpoint >= true_onset) & (
                grid_first_endpoint <= true_t50 + cfg.primary_latency
            )
            for method, hits, values in (
                (control_method, control_hits, control_max),
                (grid_method, grid_hits, candidate_max),
            ):
                positive_hits[method][stratum].append(hits)
                positive_batch_counts[method][stratum][batch] += int(hits.sum())
                positive_batch_ns[method][stratum][batch] += len(hits)
                positive_score_parts[method].append(values.astype(np.float32))

            control_hinge = np.where(
                control_alert, output["estimated_onset_grid"][row, control_first_index], -1
            ).astype(np.int16)
            grid_hinge = np.where(
                grid_alert, output["estimated_onset_grid"][row, grid_first_index], -1
            ).astype(np.int16)
            timing_frames.append(
                pd.DataFrame(
                    {
                        "replication": seed_record["replication"],
                        "batch": batch,
                        "stratum": stratum,
                        "true_shape_index": output["true_shape_index"],
                        "true_shape": [SHAPES[int(i)] for i in output["true_shape_index"]],
                        "true_duration": output["true_duration"],
                        "true_latent_u": output["true_latent_u"],
                        "nearest_latent_index": output["nearest_latent_index"],
                        "nearest_latent_value": LATENT_GRID[output["nearest_latent_index"]],
                        "true_onset": true_onset,
                        "true_t50": true_t50,
                        "control_alert": control_alert,
                        "control_first_endpoint": control_first_endpoint,
                        "control_primary_hit": control_hits,
                        "control_selected_shape_index": control_selected_shape,
                        "control_selected_duration": control_selected_duration,
                        "grid_alert": grid_alert,
                        "grid_first_endpoint": grid_first_endpoint,
                        "grid_primary_hit": grid_hits,
                        "grid_selected_shape_index": selected_shape,
                        "grid_selected_shape": [SHAPES[int(i)] if i >= 0 else "none" for i in selected_shape],
                        "grid_selected_duration": selected_duration,
                        "grid_selected_latent_index": selected_latent_index,
                        "grid_selected_latent_value": selected_latent_value,
                        "latent_error": np.where(grid_alert, selected_latent_value - output["true_latent_u"], np.nan),
                        "latent_absolute_error": np.where(grid_alert, np.abs(selected_latent_value - output["true_latent_u"]), np.nan),
                        "duration_error": np.where(grid_alert, selected_duration - output["true_duration"], -999),
                        "control_latency_from_t50": np.where(control_alert, control_first_endpoint - true_t50, -999),
                        "grid_latency_from_t50": np.where(grid_alert, grid_first_endpoint - true_t50, -999),
                        "control_hinge_error_at_alert": np.where(control_alert, control_hinge - true_onset, -999),
                        "grid_hinge_error_at_alert": np.where(grid_alert, grid_hinge - true_onset, -999),
                    }
                )
            )
            control_energy = np.where(
                control_alert, output["control_energy_grid"][row, control_first_index], np.nan
            )
            grid_energy = np.where(
                grid_alert, output["grid_energy_grid"][row, grid_first_index], np.nan
            )
            projection_rows.append(
                {
                    "replication": seed_record["replication"],
                    "population": "positive",
                    "group": stratum,
                    "n": n,
                    "control_alert_n": int(control_alert.sum()),
                    "grid_alert_n": int(grid_alert.sum()),
                    "control_energy_at_first_sum": float(np.nansum(control_energy)),
                    "grid_energy_at_first_sum": float(np.nansum(grid_energy)),
                }
            )

        for family, rng in zip(NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA) :]):
            output = evaluate_negative_family(
                family, cfg.holdout_negative_per_family_per_batch, rng, cfg, core
            )
            control_grid, candidate_grid = output["control_score_grid"], output["grid_score_grid"]
            control_max, candidate_max = np.max(control_grid, axis=1), np.max(candidate_grid, axis=1)
            control_alert, _, _ = first_crossing(control_grid, thresholds[control_method], cfg)
            grid_alert, grid_first_index, grid_first_endpoint = first_crossing(
                candidate_grid, thresholds[grid_method], cfg
            )
            n = len(grid_alert)
            row = np.arange(n)
            selected_duration = np.where(
                grid_alert, output["grid_duration_grid"][row, grid_first_index], -1
            ).astype(np.int16)
            selected_shape = np.where(
                grid_alert, output["grid_shape_index_grid"][row, grid_first_index], -1
            ).astype(np.int8)
            selected_latent_index = np.where(
                grid_alert, output["grid_latent_index_grid"][row, grid_first_index], -1
            ).astype(np.int8)
            selected_latent_value = np.where(
                grid_alert, output["grid_latent_value_grid"][row, grid_first_index], np.nan
            )
            for method, values, alerts in (
                (control_method, control_max, control_alert),
                (grid_method, candidate_max, grid_alert),
            ):
                negative_counts[method][family] += int(alerts.sum())
                negative_ns[method][family] += len(alerts)
                negative_score_parts[method].append(values.astype(np.float32))
            record = {
                "replication": seed_record["replication"],
                "batch": batch,
                "family": family,
                "n": n,
                "grid_alerts": int(grid_alert.sum()),
                "selected_duration_mean": float(np.mean(selected_duration[grid_alert])) if grid_alert.any() else np.nan,
                "selected_latent_mean": float(np.mean(selected_latent_value[grid_alert])) if grid_alert.any() else np.nan,
                "first_endpoint_mean": float(np.mean(grid_first_endpoint[grid_alert])) if grid_alert.any() else np.nan,
            }
            for i, value in enumerate(LATENT_GRID):
                record[f"selected_u_{value:.2f}"] = int(np.sum(grid_alert & (selected_latent_index == i)))
            for i, shape in enumerate(SHAPES):
                record[f"selected_{shape}"] = int(np.sum(grid_alert & (selected_shape == i)))
            negative_selection_rows.append(record)

    positive_scores_all = {method: np.concatenate(positive_score_parts[method]) for method in cfg.methods}
    negative_scores_all = {method: np.concatenate(negative_score_parts[method]) for method in cfg.methods}
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
        control_hits = np.concatenate(positive_hits[control_method][stratum])
        grid_hits = np.concatenate(positive_hits[grid_method][stratum])
        codes = control_hits.astype(np.int8) * 2 + grid_hits.astype(np.int8)
        counts = np.bincount(codes, minlength=4)
        total_counts += counts
        pair_rows.append(
            {
                "replication": seed_record["replication"],
                "stratum_index": stratum_index,
                "stratum": stratum,
                "neither": int(counts[0]),
                "grid_only": int(counts[1]),
                "control_only": int(counts[2]),
                "both": int(counts[3]),
                "n": int(counts.sum()),
            }
        )
    timing_detail = pd.concat(timing_frames, ignore_index=True)
    identification = latent_identification_row(
        seed_record["replication"],
        timing_detail["true_latent_u"].to_numpy(),
        timing_detail["nearest_latent_index"].to_numpy(),
        timing_detail["grid_selected_latent_index"].to_numpy(),
        timing_detail["grid_selected_latent_value"].to_numpy(),
        timing_detail["true_duration"].to_numpy(),
        timing_detail["grid_selected_duration"].to_numpy(),
        timing_detail["true_shape_index"].to_numpy(),
        timing_detail["grid_selected_shape_index"].to_numpy(),
        timing_detail["grid_alert"].to_numpy(),
        timing_detail["grid_primary_hit"].to_numpy(),
        cfg,
    )
    method_frame = pd.DataFrame(method_rows).set_index("method")
    paired_summary = {
        "replication": seed_record["replication"],
        "control_recall": float(method_frame.loc[control_method, "recall_point"]),
        "grid_recall": float(method_frame.loc[grid_method, "recall_point"]),
        "grid_minus_control": float(method_frame.loc[grid_method, "recall_point"] - method_frame.loc[control_method, "recall_point"]),
        "neither": int(total_counts[0]),
        "grid_only": int(total_counts[1]),
        "control_only": int(total_counts[2]),
        "both": int(total_counts[3]),
        "positive_score_correlation": float(np.corrcoef(positive_scores_all[control_method], positive_scores_all[grid_method])[0, 1]),
        "negative_score_correlation": float(np.corrcoef(negative_scores_all[control_method], negative_scores_all[grid_method])[0, 1]),
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
    method_details, bootstrap_frames = {}, []
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
        lower, upper = float(np.quantile(bootstrap, 0.05)), float(np.quantile(bootstrap, 0.95))
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
        bootstrap_frames.append(pd.DataFrame({"method": method, "replicate": np.arange(cfg.bootstrap_replicates), "recall": bootstrap}))

    pair_array = np.zeros((cfg.holdout_count, len(POSITIVE_STRATA), 4), dtype=np.int64)
    for _, row in pair_counts.iterrows():
        pair_array[int(row.replication), int(row.stratum_index)] = [
            int(row.neither), int(row.grid_only), int(row.control_only), int(row.both)
        ]
    delta_bootstrap = m32.m30.hierarchical_paired_bootstrap(
        pair_array, cfg.bootstrap_replicates, cfg.paired_difference_bootstrap_seed
    )
    control_method, grid_method = cfg.methods
    control, grid = method_details[control_method], method_details[grid_method]
    delta_point = grid["aggregate_recall_point"] - control["aggregate_recall_point"]
    delta_lower, delta_upper = float(np.quantile(delta_bootstrap, 0.05)), float(np.quantile(delta_bootstrap, 0.95))

    hit_n = int(identification_summary.primary_hit_n.sum())
    nearest_correct = int(identification_summary.nearest_cell_correct.sum())
    half_correct = int(identification_summary.latent_within_half_spacing_correct.sum())
    quarter_correct = int(identification_summary.latent_within_quarter_correct.sum())
    duration_exact = int(identification_summary.duration_exact_correct.sum())
    shape_correct = int(identification_summary.shape_correct.sum())
    nearest_accuracy = nearest_correct / hit_n if hit_n else 0.0
    nearest_lower = m22.m5.clopper_pearson_lower(nearest_correct, hit_n) if hit_n else 0.0
    nearest_upper = m2.clopper_pearson_upper(nearest_correct, hit_n) if hit_n else 1.0
    identification_pass_count = int(identification_summary.latent_identification_pass.sum())
    latent_identification_pass = bool(
        nearest_lower >= cfg.latent_identification_minimum_lower_one_sided_95
        and identification_pass_count >= cfg.minimum_latent_identification_holdouts
    )
    control_valid = bool(control["operational_pass"])
    if not control_valid:
        verdict = "INVALID_M38B_EXACT_LATENT_CONTROL"
    elif grid["operational_pass"] and latent_identification_pass:
        verdict = "PASS_M38B_LATENT_GRID_AND_IDENTIFICATION"
    elif grid["operational_pass"]:
        verdict = "PASS_M38B_DETECTION_LATENT_UNRELIABLE"
    elif (
        grid["holdout_pass_count"] <= 2
        or grid["aggregate_recall_upper_one_sided_95"] <= cfg.minimum_global_recall_lower_one_sided_95
        or grid["extreme_fpr_violation"]
    ):
        verdict = "STRONG_FAIL_M38B_LATENT_GRID_BANK"
    else:
        verdict = "INCONCLUSIVE_M38B_LATENT_GRID_BANK"
    prediction = {
        "control_threshold_in_range": cfg.prediction_control_threshold_range[0] <= control["threshold"] <= cfg.prediction_control_threshold_range[1],
        "grid_threshold_in_range": cfg.prediction_grid_threshold_range[0] <= grid["threshold"] <= cfg.prediction_grid_threshold_range[1],
        "control_recall_in_range": cfg.prediction_control_range[0] <= control["aggregate_recall_point"] <= cfg.prediction_control_range[1],
        "grid_recall_in_range": cfg.prediction_grid_range[0] <= grid["aggregate_recall_point"] <= cfg.prediction_grid_range[1],
        "delta_in_range": cfg.prediction_delta_range[0] <= delta_point <= cfg.prediction_delta_range[1],
        "control_pass_count_in_range": cfg.prediction_control_pass_low <= control["holdout_pass_count"] <= cfg.prediction_control_pass_high,
        "grid_pass_count_in_range": cfg.prediction_grid_pass_low <= grid["holdout_pass_count"] <= cfg.prediction_grid_pass_high,
        "both_fpr_robust": bool(control["fpr_robust"] and grid["fpr_robust"]),
        "latent_identification_below_gate": nearest_lower < cfg.latent_identification_minimum_lower_one_sided_95,
        "overall_verdict_confirmed": verdict == "INCONCLUSIVE_M38B_LATENT_GRID_BANK",
    }
    prediction["fully_confirmed"] = bool(all(prediction.values()))
    return {
        "verdict": verdict,
        "control_valid": control_valid,
        "method_details": method_details,
        "paired_difference": {
            "grid_minus_control_point": delta_point,
            "grid_minus_control_lower_one_sided_95": delta_lower,
            "grid_minus_control_upper_one_sided_95": delta_upper,
        },
        "latent_identification": {
            "primary_hit_n": hit_n,
            "nearest_cell_correct": nearest_correct,
            "nearest_cell_accuracy": nearest_accuracy,
            "nearest_cell_accuracy_lower_one_sided_95": nearest_lower,
            "nearest_cell_accuracy_upper_one_sided_95": nearest_upper,
            "within_half_spacing_correct": half_correct,
            "within_half_spacing_accuracy": half_correct / hit_n if hit_n else 0.0,
            "within_quarter_correct": quarter_correct,
            "within_quarter_accuracy": quarter_correct / hit_n if hit_n else 0.0,
            "duration_exact_correct": duration_exact,
            "duration_exact_accuracy": duration_exact / hit_n if hit_n else 0.0,
            "shape_correct": shape_correct,
            "shape_accuracy": shape_correct / hit_n if hit_n else 0.0,
            "holdout_pass_count": identification_pass_count,
            "identification_pass": latent_identification_pass,
        },
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(bootstrap_frames, ignore_index=True),
        "delta_bootstrap": delta_bootstrap,
    }


def write_environment(path: Path) -> None:
    import scipy
    import sklearn
    path.write_text(
        json.dumps(
            {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scipy": scipy.__version__,
                "scikit_learn": sklearn.__version__,
                "m37r_dependency_sha256": sha256_file(ROOT / "arara_m37r_dependency.py"),
                "m37_dependency_sha256": sha256_file(ROOT / "arara_m37_dependency.py"),
                "m38a_grid_sha256": sha256_file(ROOT / "FROZEN_LATENT_GRID_M38A.json"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
