
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

import arara_m35_dependency as m35


m34 = m35.m34
m32 = m34.m32
m22 = m32.m22
m2 = m22.m2
m9 = m22.m9

SHAPES = (
    "linear",
    "power_law",
    "exponential",
    "logistic",
)
SHAPE_TO_INDEX = {
    shape: index
    for index, shape in enumerate(SHAPES)
}
POSITIVE_STRATA = tuple(
    f"{shape}__{context}"
    for shape in SHAPES
    for context in ("clean", "concurrent")
)
NEGATIVE_FAMILIES = m34.NEGATIVE_FAMILIES
METHODS = (
    "rolling_exact_shape_latency4",
    "rolling_four_shape_bank_latency4",
)


@dataclass(frozen=True)
class Config(m35.Config):
    version: str = "36.0"
    methods: tuple[str, ...] = METHODS

    shape_accuracy_minimum_lower_one_sided_95: float = 0.70
    minimum_shape_accuracy_holdouts: int = 8

    calibration_seed: int = 2026090101
    holdout_root_seed: int = 2026090102
    aggregate_bootstrap_root_seed: int = 2026090103
    paired_difference_bootstrap_seed: int = 2026090104

    prediction_exact_range: tuple[float, float] = (
        0.73,
        0.79,
    )
    prediction_bank_range: tuple[float, float] = (
        0.66,
        0.75,
    )
    prediction_delta_range: tuple[float, float] = (
        -0.10,
        0.00,
    )
    prediction_bank_threshold_range: tuple[float, float] = (
        7.2,
        8.6,
    )
    prediction_bank_pass_low: int = 3
    prediction_bank_pass_high: int = 8
    prediction_shape_accuracy_range: tuple[float, float] = (
        0.45,
        0.75,
    )


@dataclass
class PositivePanel:
    base_y: np.ndarray
    true_shape_values: np.ndarray
    shape_bank_values: np.ndarray
    stationary_target_sd: np.ndarray
    onset: np.ndarray
    duration: np.ndarray
    latent_u: np.ndarray
    true_shape_index: np.ndarray
    true_t50: np.ndarray
    artifact_family: np.ndarray


build_seed_plan = m35.build_seed_plan
calibration_core = m35.calibration_core
sha256_file = m35.sha256_file


def event_shape_from_latent(
    shape: str,
    k: np.ndarray,
    onset: np.ndarray,
    duration: np.ndarray,
    latent_u: np.ndarray,
) -> np.ndarray:
    x = np.clip(
        (
            k
            - np.asarray(onset)[:, None]
        )
        / np.asarray(duration)[:, None],
        0.0,
        1.0,
    )
    u = np.asarray(
        latent_u,
        dtype=np.float64,
    )
    if shape == "linear":
        return x
    if shape == "power_law":
        gamma = 1.5 + 1.5 * u
        return x ** gamma[:, None]
    if shape == "exponential":
        beta = 1.0 + 3.0 * u
        return (
            np.exp(beta[:, None] * x)
            - 1.0
        ) / (
            np.exp(beta) - 1.0
        )[:, None]
    if shape == "logistic":
        q = 6.0 + 6.0 * u
        return m2._normalized_logistic(
            x,
            q,
        )
    raise ValueError(
        f"Unknown shape: {shape}"
    )


def build_shape_bank(
    onset: np.ndarray,
    duration: np.ndarray,
    latent_u: np.ndarray,
    n_time: int,
) -> np.ndarray:
    k = np.arange(
        n_time,
        dtype=np.float64,
    )[None, :]
    return np.stack(
        [
            event_shape_from_latent(
                shape,
                k,
                onset,
                duration,
                latent_u,
            )
            for shape in SHAPES
        ],
        axis=0,
    )


def generate_positive_panel(
    shape: str,
    context: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    data_cfg=None,
) -> PositivePanel:
    if shape not in SHAPES:
        raise ValueError(shape)
    if context not in (
        "clean",
        "concurrent",
    ):
        raise ValueError(context)

    if data_cfg is None:
        data_cfg = calibration_core(
            cfg
        ).data_config()
    (
        y,
        stationary_sd,
        coupling,
        _,
        _,
    ) = m2._generate_base_field(
        n,
        rng,
        data_cfg,
    )
    m2._inject_reference_impulse(
        y,
        stationary_sd,
        rng,
        data_cfg,
    )

    onset = rng.integers(
        data_cfg.onset_low,
        data_cfg.onset_high + 1,
        size=n,
    )
    duration = rng.integers(
        data_cfg.duration_low,
        data_cfg.duration_high + 1,
        size=n,
    )
    latent_u = rng.uniform(
        0.0,
        1.0,
        size=n,
    )
    bank = build_shape_bank(
        onset,
        duration,
        latent_u,
        data_cfg.n_time,
    )
    true_index = np.full(
        n,
        SHAPE_TO_INDEX[shape],
        dtype=np.int8,
    )
    true_values = bank[
        SHAPE_TO_INDEX[shape]
    ]

    artifact_family = np.full(
        n,
        "none",
        dtype=object,
    )
    if context == "concurrent":
        families = m9.SHARED_ARTIFACT_FAMILIES
        selected = rng.integers(
            0,
            len(families),
            size=n,
        )
        delta = rng.integers(
            -10,
            11,
            size=n,
        )
        artifact_onset = np.clip(
            onset + delta,
            60,
            120,
        )
        artifact_duration = rng.integers(
            data_cfg.duration_low,
            data_cfg.duration_high + 1,
            size=n,
        )

        for index, family in enumerate(
            families
        ):
            mask = selected == index
            if not np.any(mask):
                continue
            block = y[mask].copy()
            m2._inject_shared_artifact(
                block,
                stationary_sd[mask],
                coupling[mask],
                family,
                artifact_onset[mask],
                artifact_duration[mask],
                rng,
                data_cfg,
            )
            y[mask] = block
            artifact_family[mask] = family

    true_t50 = m9.time_at_fraction(
        true_values,
        cfg.target_fraction,
    )
    return PositivePanel(
        base_y=y,
        true_shape_values=true_values,
        shape_bank_values=bank,
        stationary_target_sd=stationary_sd[:, 0],
        onset=onset.astype(np.int16),
        duration=duration.astype(np.int16),
        latent_u=latent_u,
        true_shape_index=true_index,
        true_t50=true_t50,
        artifact_family=artifact_family,
    )


def generate_virtual_shape_bank(
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    data_cfg=None,
) -> dict:
    if data_cfg is None:
        data_cfg = calibration_core(
            cfg
        ).data_config()
    true_shape_index = rng.integers(
        0,
        len(SHAPES),
        size=n,
        dtype=np.int8,
    )
    onset = rng.integers(
        data_cfg.onset_low,
        data_cfg.onset_high + 1,
        size=n,
    )
    duration = rng.integers(
        data_cfg.duration_low,
        data_cfg.duration_high + 1,
        size=n,
    )
    latent_u = rng.uniform(
        0.0,
        1.0,
        size=n,
    )
    bank = build_shape_bank(
        onset,
        duration,
        latent_u,
        data_cfg.n_time,
    )
    row = np.arange(n)
    true_signal = bank[
        true_shape_index,
        row,
    ]
    true_t50 = m9.time_at_fraction(
        true_signal,
        cfg.target_fraction,
    )
    return {
        "shape_bank": bank,
        "true_signal": true_signal,
        "true_shape_index": true_shape_index,
        "onset": onset.astype(np.int16),
        "duration": duration.astype(np.int16),
        "latent_u": latent_u,
        "true_t50": true_t50,
    }


def score_shape_bank(
    residual: np.ndarray,
    raw_shape_bank: np.ndarray,
    reference_onset: np.ndarray,
    true_shape_index: np.ndarray,
    processed_reference: np.ndarray,
    params: dict,
    cfg: Config,
) -> dict:
    endpoints = cfg.endpoint_grid
    estimated_onset, hinge_objective = (
        m34.estimate_onset_grid(
            residual,
            endpoints,
            cfg,
        )
    )
    residual_window = (
        m34.fixed_endpoint_windows(
            residual,
            endpoints,
            cfg.window_length,
        )
    )
    reference_window = (
        m34.fixed_endpoint_windows(
            processed_reference,
            endpoints,
            cfg.window_length,
        )
    )

    n = residual.shape[0]
    endpoint_count = len(endpoints)
    shape_scores = np.empty(
        (
            n,
            len(SHAPES),
            endpoint_count,
        ),
        dtype=np.float64,
    )
    shape_energy = np.empty_like(
        shape_scores
    )
    shape_degenerate = np.empty(
        shape_scores.shape,
        dtype=bool,
    )

    for shape_index, _ in enumerate(
        SHAPES
    ):
        template_window = (
            m34.processed_template_grid_windows(
                raw_shape_bank[shape_index],
                reference_onset,
                estimated_onset,
                endpoints,
                params,
                cfg,
            )
        )
        score, diagnostics = (
            m34.projected_window_score(
                residual_window,
                template_window,
                reference_window,
            )
        )
        shape_scores[
            :,
            shape_index,
            :,
        ] = score
        shape_energy[
            :,
            shape_index,
            :,
        ] = diagnostics[
            "energy_retention"
        ]
        shape_degenerate[
            :,
            shape_index,
            :,
        ] = diagnostics[
            "template_degenerate"
        ]

    row = np.arange(n)
    exact_score_grid = shape_scores[
        row,
        np.asarray(
            true_shape_index,
            dtype=np.int64,
        ),
        :,
    ]
    exact_energy_grid = shape_energy[
        row,
        np.asarray(
            true_shape_index,
            dtype=np.int64,
        ),
        :,
    ]
    exact_degenerate_grid = (
        shape_degenerate[
            row,
            np.asarray(
                true_shape_index,
                dtype=np.int64,
            ),
            :,
        ]
    )

    bank_shape_index_grid = np.argmax(
        shape_scores,
        axis=1,
    ).astype(np.int8)
    bank_score_grid = np.max(
        shape_scores,
        axis=1,
    )
    bank_energy_grid = np.take_along_axis(
        shape_energy,
        bank_shape_index_grid[
            :,
            None,
            :,
        ],
        axis=1,
    )[:, 0, :]
    bank_degenerate_grid = (
        np.take_along_axis(
            shape_degenerate,
            bank_shape_index_grid[
                :,
                None,
                :,
            ],
            axis=1,
        )[:, 0, :]
    )

    return {
        "exact_score_grid": exact_score_grid,
        "bank_score_grid": bank_score_grid,
        "bank_shape_index_grid": (
            bank_shape_index_grid
        ),
        "estimated_onset_grid": (
            estimated_onset
        ),
        "hinge_objective_grid": (
            hinge_objective
        ),
        "exact_energy_grid": (
            exact_energy_grid
        ),
        "bank_energy_grid": (
            bank_energy_grid
        ),
        "exact_degenerate_grid": (
            exact_degenerate_grid
        ),
        "bank_degenerate_grid": (
            bank_degenerate_grid
        ),
        "shape_scores": shape_scores,
    }


def evaluate_positive_panel(
    panel: PositivePanel,
    cfg: Config,
    core,
) -> dict:
    amplitude = (
        cfg.fixed_snr
        * panel.stationary_target_sd
    )
    raw_bank = (
        panel.shape_bank_values
        * amplitude[
            None,
            :,
            None,
        ]
    )
    row = np.arange(
        len(panel.onset)
    )
    raw_true = raw_bank[
        panel.true_shape_index,
        row,
    ]

    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_true

    (
        residual,
        _,
        processed_reference,
        params,
    ) = m32.m30.m29.sbw_with_reference_nuisance(
        observed,
        raw_true,
        core.data_config(),
    )
    scores = score_shape_bank(
        residual,
        raw_bank,
        panel.onset,
        panel.true_shape_index,
        processed_reference,
        params,
        cfg,
    )
    scores.update(
        {
            "true_shape_index": (
                panel.true_shape_index
            ),
            "true_onset": panel.onset,
            "true_t50": panel.true_t50,
            "duration": panel.duration,
            "latent_u": panel.latent_u,
        }
    )
    return scores


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core,
) -> dict:
    data_cfg = core.data_config()
    data = m2.generate_negative_family(
        family,
        n,
        rng,
        data_cfg,
    )
    virtual = generate_virtual_shape_bank(
        n,
        rng,
        cfg,
        data_cfg=data_cfg,
    )
    (
        residual,
        _,
        processed_reference,
        params,
    ) = m32.m30.m29.sbw_with_reference_nuisance(
        data.y,
        virtual["true_signal"],
        data_cfg,
    )
    scores = score_shape_bank(
        residual,
        virtual["shape_bank"],
        virtual["onset"],
        virtual["true_shape_index"],
        processed_reference,
        params,
        cfg,
    )
    scores.update(virtual)
    return scores


def first_crossing(
    score_grid: np.ndarray,
    threshold: float,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    crossings = (
        np.asarray(score_grid)
        >= threshold
    )
    any_crossing = np.any(
        crossings,
        axis=1,
    )
    first_index = np.argmax(
        crossings,
        axis=1,
    )
    first_endpoint = np.where(
        any_crossing,
        cfg.endpoint_grid[
            first_index
        ],
        -1,
    ).astype(np.int16)
    return (
        any_crossing,
        first_index.astype(np.int16),
        first_endpoint,
    )



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

    exact_max_parts = []
    bank_max_parts = []
    exact_argmax_endpoint_parts = []
    bank_argmax_endpoint_parts = []
    bank_argmax_shape_parts = []
    true_shape_parts = []
    exact_energy_parts = []
    bank_energy_parts = []

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

        exact_grid = output[
            "exact_score_grid"
        ]
        bank_grid = output[
            "bank_score_grid"
        ]
        exact_argmax = np.argmax(
            exact_grid,
            axis=1,
        )
        bank_argmax = np.argmax(
            bank_grid,
            axis=1,
        )
        row = np.arange(n)

        exact_max_parts.append(
            exact_grid[
                row,
                exact_argmax,
            ].astype(np.float32)
        )
        bank_max_parts.append(
            bank_grid[
                row,
                bank_argmax,
            ].astype(np.float32)
        )
        exact_argmax_endpoint_parts.append(
            cfg.endpoint_grid[
                exact_argmax
            ].astype(np.int16)
        )
        bank_argmax_endpoint_parts.append(
            cfg.endpoint_grid[
                bank_argmax
            ].astype(np.int16)
        )
        bank_argmax_shape_parts.append(
            output[
                "bank_shape_index_grid"
            ][
                row,
                bank_argmax,
            ].astype(np.int8)
        )
        true_shape_parts.append(
            output[
                "true_shape_index"
            ].astype(np.int8)
        )
        exact_energy_parts.append(
            output[
                "exact_energy_grid"
            ][
                row,
                exact_argmax,
            ].astype(np.float32)
        )
        bank_energy_parts.append(
            output[
                "bank_energy_grid"
            ][
                row,
                bank_argmax,
            ].astype(np.float32)
        )
        remaining -= n

    result = {
        "score_rolling_exact_shape_latency4": (
            np.concatenate(
                exact_max_parts
            )
        ),
        "score_rolling_four_shape_bank_latency4": (
            np.concatenate(
                bank_max_parts
            )
        ),
        "exact_argmax_endpoint": (
            np.concatenate(
                exact_argmax_endpoint_parts
            )
        ),
        "bank_argmax_endpoint": (
            np.concatenate(
                bank_argmax_endpoint_parts
            )
        ),
        "bank_argmax_shape_index": (
            np.concatenate(
                bank_argmax_shape_parts
            )
        ),
        "true_shape_index": np.concatenate(
            true_shape_parts
        ),
        "exact_energy_at_max": np.concatenate(
            exact_energy_parts
        ),
        "bank_energy_at_max": np.concatenate(
            bank_energy_parts
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
        values = result[
            f"score_{method}"
        ]
        if not np.isfinite(
            values
        ).all():
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

            selected = data[
                "bank_argmax_shape_index"
            ]
            counts = np.bincount(
                selected,
                minlength=len(SHAPES),
            )
            row = {
                "family": family,
                "n": len(selected),
                "exact_argmax_endpoint_mean": float(
                    np.mean(
                        data[
                            "exact_argmax_endpoint"
                        ]
                    )
                ),
                "bank_argmax_endpoint_mean": float(
                    np.mean(
                        data[
                            "bank_argmax_endpoint"
                        ]
                    )
                ),
                "exact_energy_at_max_mean": float(
                    np.mean(
                        data[
                            "exact_energy_at_max"
                        ]
                    )
                ),
                "bank_energy_at_max_mean": float(
                    np.mean(
                        data[
                            "bank_energy_at_max"
                        ]
                    )
                ),
            }
            for shape_index, shape in enumerate(
                SHAPES
            ):
                row[
                    f"bank_selected_{shape}_fraction"
                ] = (
                    counts[shape_index]
                    / len(selected)
                )
            diagnostic_rows.append(row)

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []

    for method in cfg.methods:
        by_family = {
            family: loaded[
                family
            ][method]
            for family in NEGATIVE_FAMILIES
        }
        (
            threshold,
            specific,
            allowed,
        ) = m2.conservative_threshold(
            by_family,
            cfg.development_fpr_target,
        )
        thresholds[method] = float(
            threshold
        )
        family_thresholds[
            method
        ] = specific
        allowed_counts[method] = allowed

        for family in NEGATIVE_FAMILIES:
            values = by_family[family]
            alerts = int(
                np.sum(
                    values >= threshold
                )
            )
            if (
                alerts
                > allowed[family]
            ):
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
            "family_thresholds": (
                family_thresholds
            ),
            "allowed_counts": (
                allowed_counts
            ),
            "calibration_negatives_per_family": (
                cfg.calibration_negatives_per_family
            ),
            "exact_hypothesis_count": int(
                len(cfg.endpoint_grid)
            ),
            "bank_hypothesis_count": int(
                len(cfg.endpoint_grid)
                * len(SHAPES)
            ),
        },
        pd.DataFrame(rows),
        pd.DataFrame(
            diagnostic_rows
        ),
    )


def shape_accuracy_row(
    replication: int,
    true_shape_index: np.ndarray,
    selected_shape_index: np.ndarray,
    alert_mask: np.ndarray,
    primary_hit_mask: np.ndarray,
    cfg: Config,
) -> dict:
    true_index = np.asarray(
        true_shape_index,
        dtype=np.int8,
    )
    selected_index = np.asarray(
        selected_shape_index,
        dtype=np.int8,
    )
    alerts = np.asarray(
        alert_mask,
        dtype=bool,
    )
    hits = np.asarray(
        primary_hit_mask,
        dtype=bool,
    )

    alert_n = int(
        alerts.sum()
    )
    hit_n = int(
        hits.sum()
    )
    alert_correct = int(
        np.sum(
            alerts
            & (
                selected_index
                == true_index
            )
        )
    )
    hit_correct = int(
        np.sum(
            hits
            & (
                selected_index
                == true_index
            )
        )
    )

    hit_lower = (
        m22.m5.clopper_pearson_lower(
            hit_correct,
            hit_n,
        )
        if hit_n > 0
        else 0.0
    )
    hit_upper = (
        m2.clopper_pearson_upper(
            hit_correct,
            hit_n,
        )
        if hit_n > 0
        else 1.0
    )
    return {
        "replication": replication,
        "alert_n": alert_n,
        "alert_shape_correct": (
            alert_correct
        ),
        "alert_shape_accuracy": (
            alert_correct / alert_n
            if alert_n > 0
            else 0.0
        ),
        "primary_hit_n": hit_n,
        "primary_hit_shape_correct": (
            hit_correct
        ),
        "primary_hit_shape_accuracy": (
            hit_correct / hit_n
            if hit_n > 0
            else 0.0
        ),
        "primary_hit_shape_accuracy_lower_one_sided_95": (
            hit_lower
        ),
        "primary_hit_shape_accuracy_upper_one_sided_95": (
            hit_upper
        ),
        "shape_identification_pass": bool(
            hit_lower
            >= cfg.shape_accuracy_minimum_lower_one_sided_95
        ),
    }



def evaluate_holdout(
    cfg: Config,
    seed_record: dict,
    thresholds: dict[str, float],
) -> dict:
    analysis = cfg.analysis_config()
    core = analysis.core_config(
        seed_record
    )
    batch_sequences = (
        np.random.SeedSequence(
            seed_record[
                "seeds"
            ]["holdout"]
        ).spawn(
            cfg.holdout_batches
        )
    )

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
        method: []
        for method in cfg.methods
    }
    negative_score_parts = {
        method: []
        for method in cfg.methods
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
    confusion_rows = []
    negative_shape_rows = []
    projection_rows = []

    for batch, sequence in enumerate(
        batch_sequences
    ):
        children = sequence.spawn(
            len(POSITIVE_STRATA)
            + len(NEGATIVE_FAMILIES)
        )
        rngs = [
            np.random.default_rng(
                child
            )
            for child in children
        ]

        for stratum, rng in zip(
            POSITIVE_STRATA,
            rngs[
                :len(POSITIVE_STRATA)
            ],
        ):
            shape, context = (
                stratum.split("__")
            )
            panel = generate_positive_panel(
                shape,
                context,
                cfg.holdout_positive_per_stratum_per_batch,
                rng,
                cfg,
                data_cfg=core.data_config(),
            )
            output = evaluate_positive_panel(
                panel,
                cfg,
                core,
            )

            exact_grid = output[
                "exact_score_grid"
            ]
            bank_grid = output[
                "bank_score_grid"
            ]
            exact_max = np.max(
                exact_grid,
                axis=1,
            )
            bank_max = np.max(
                bank_grid,
                axis=1,
            )

            (
                exact_alert,
                exact_first_index,
                exact_first_endpoint,
            ) = first_crossing(
                exact_grid,
                thresholds[
                    "rolling_exact_shape_latency4"
                ],
                cfg,
            )
            (
                bank_alert,
                bank_first_index,
                bank_first_endpoint,
            ) = first_crossing(
                bank_grid,
                thresholds[
                    "rolling_four_shape_bank_latency4"
                ],
                cfg,
            )

            row = np.arange(
                len(bank_alert)
            )
            bank_selected_shape = np.where(
                bank_alert,
                output[
                    "bank_shape_index_grid"
                ][
                    row,
                    bank_first_index,
                ],
                -1,
            ).astype(np.int8)
            exact_hinge_at_alert = np.where(
                exact_alert,
                output[
                    "estimated_onset_grid"
                ][
                    row,
                    exact_first_index,
                ],
                -1,
            ).astype(np.int16)
            bank_hinge_at_alert = np.where(
                bank_alert,
                output[
                    "estimated_onset_grid"
                ][
                    row,
                    bank_first_index,
                ],
                -1,
            ).astype(np.int16)

            true_onset = output[
                "true_onset"
            ].astype(np.int16)
            true_t50 = output[
                "true_t50"
            ].astype(np.int16)
            true_shape_index = output[
                "true_shape_index"
            ].astype(np.int8)

            exact_hits = (
                exact_alert
                & (
                    exact_first_endpoint
                    >= true_onset
                )
                & (
                    exact_first_endpoint
                    <= (
                        true_t50
                        + cfg.primary_latency
                    )
                )
            )
            bank_hits = (
                bank_alert
                & (
                    bank_first_endpoint
                    >= true_onset
                )
                & (
                    bank_first_endpoint
                    <= (
                        true_t50
                        + cfg.primary_latency
                    )
                )
            )

            hits_by_method = {
                "rolling_exact_shape_latency4": (
                    exact_hits
                ),
                "rolling_four_shape_bank_latency4": (
                    bank_hits
                ),
            }
            scores_by_method = {
                "rolling_exact_shape_latency4": (
                    exact_max
                ),
                "rolling_four_shape_bank_latency4": (
                    bank_max
                ),
            }

            for method in cfg.methods:
                hits = hits_by_method[
                    method
                ]
                values = scores_by_method[
                    method
                ]
                positive_hits[
                    method
                ][stratum].append(
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
                positive_score_parts[
                    method
                ].append(
                    values.astype(
                        np.float32
                    )
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
                        "true_shape_index": (
                            true_shape_index
                        ),
                        "true_shape": np.asarray(
                            [
                                SHAPES[index]
                                for index in (
                                    true_shape_index
                                )
                            ],
                            dtype=object,
                        ),
                        "true_onset": (
                            true_onset
                        ),
                        "true_t50": (
                            true_t50
                        ),
                        "exact_alert": (
                            exact_alert
                        ),
                        "exact_first_endpoint": (
                            exact_first_endpoint
                        ),
                        "exact_primary_hit": (
                            exact_hits
                        ),
                        "bank_alert": (
                            bank_alert
                        ),
                        "bank_first_endpoint": (
                            bank_first_endpoint
                        ),
                        "bank_primary_hit": (
                            bank_hits
                        ),
                        "bank_selected_shape_index": (
                            bank_selected_shape
                        ),
                        "bank_selected_shape": np.asarray(
                            [
                                (
                                    SHAPES[index]
                                    if index >= 0
                                    else "none"
                                )
                                for index in (
                                    bank_selected_shape
                                )
                            ],
                            dtype=object,
                        ),
                        "bank_shape_correct": (
                            bank_alert
                            & (
                                bank_selected_shape
                                == true_shape_index
                            )
                        ),
                        "exact_latency_from_t50": np.where(
                            exact_alert,
                            (
                                exact_first_endpoint
                                - true_t50
                            ),
                            -999,
                        ),
                        "bank_latency_from_t50": np.where(
                            bank_alert,
                            (
                                bank_first_endpoint
                                - true_t50
                            ),
                            -999,
                        ),
                        "exact_hinge_error_at_alert": np.where(
                            exact_alert,
                            (
                                exact_hinge_at_alert
                                - true_onset
                            ),
                            -999,
                        ),
                        "bank_hinge_error_at_alert": np.where(
                            bank_alert,
                            (
                                bank_hinge_at_alert
                                - true_onset
                            ),
                            -999,
                        ),
                    }
                )
            )

            for true_index, true_name in enumerate(
                SHAPES
            ):
                true_mask = (
                    true_shape_index
                    == true_index
                )
                for selected_index, selected_name in enumerate(
                    SHAPES
                ):
                    confusion_rows.append(
                        {
                            "replication": (
                                seed_record[
                                    "replication"
                                ]
                            ),
                            "batch": batch,
                            "stratum": stratum,
                            "population": (
                                "primary_hits"
                            ),
                            "true_shape": (
                                true_name
                            ),
                            "selected_shape": (
                                selected_name
                            ),
                            "count": int(
                                np.sum(
                                    true_mask
                                    & bank_hits
                                    & (
                                        bank_selected_shape
                                        == selected_index
                                    )
                                )
                            ),
                        }
                    )
                    confusion_rows.append(
                        {
                            "replication": (
                                seed_record[
                                    "replication"
                                ]
                            ),
                            "batch": batch,
                            "stratum": stratum,
                            "population": (
                                "all_alerts"
                            ),
                            "true_shape": (
                                true_name
                            ),
                            "selected_shape": (
                                selected_name
                            ),
                            "count": int(
                                np.sum(
                                    true_mask
                                    & bank_alert
                                    & (
                                        bank_selected_shape
                                        == selected_index
                                    )
                                )
                            ),
                        }
                    )

            exact_energy = output[
                "exact_energy_grid"
            ]
            bank_energy = output[
                "bank_energy_grid"
            ]
            exact_energy_at_first = (
                np.where(
                    exact_alert,
                    exact_energy[
                        row,
                        exact_first_index,
                    ],
                    np.nan,
                )
            )
            bank_energy_at_first = (
                np.where(
                    bank_alert,
                    bank_energy[
                        row,
                        bank_first_index,
                    ],
                    np.nan,
                )
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
                    "n": len(
                        true_onset
                    ),
                    "exact_alert_n": int(
                        exact_alert.sum()
                    ),
                    "bank_alert_n": int(
                        bank_alert.sum()
                    ),
                    "exact_energy_at_first_sum": float(
                        np.nansum(
                            exact_energy_at_first
                        )
                    ),
                    "bank_energy_at_first_sum": float(
                        np.nansum(
                            bank_energy_at_first
                        )
                    ),
                }
            )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[
                len(POSITIVE_STRATA):
            ],
        ):
            output = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            exact_grid = output[
                "exact_score_grid"
            ]
            bank_grid = output[
                "bank_score_grid"
            ]
            exact_max = np.max(
                exact_grid,
                axis=1,
            )
            bank_max = np.max(
                bank_grid,
                axis=1,
            )
            (
                exact_alert,
                _,
                _,
            ) = first_crossing(
                exact_grid,
                thresholds[
                    "rolling_exact_shape_latency4"
                ],
                cfg,
            )
            (
                bank_alert,
                bank_first_index,
                bank_first_endpoint,
            ) = first_crossing(
                bank_grid,
                thresholds[
                    "rolling_four_shape_bank_latency4"
                ],
                cfg,
            )
            row = np.arange(
                len(bank_alert)
            )
            selected_shape = np.where(
                bank_alert,
                output[
                    "bank_shape_index_grid"
                ][
                    row,
                    bank_first_index,
                ],
                -1,
            ).astype(np.int8)

            for (
                method,
                values,
                alerts,
            ) in (
                (
                    "rolling_exact_shape_latency4",
                    exact_max,
                    exact_alert,
                ),
                (
                    "rolling_four_shape_bank_latency4",
                    bank_max,
                    bank_alert,
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
                    values.astype(
                        np.float32
                    )
                )

            for shape_index, shape in enumerate(
                SHAPES
            ):
                negative_shape_rows.append(
                    {
                        "replication": (
                            seed_record[
                                "replication"
                            ]
                        ),
                        "batch": batch,
                        "family": family,
                        "selected_shape": shape,
                        "count": int(
                            np.sum(
                                bank_alert
                                & (
                                    selected_shape
                                    == shape_index
                                )
                            )
                        ),
                        "bank_alerts": int(
                            bank_alert.sum()
                        ),
                        "n": len(
                            bank_alert
                        ),
                        "first_endpoint_mean": (
                            float(
                                np.mean(
                                    bank_first_endpoint[
                                        bank_alert
                                        & (
                                            selected_shape
                                            == shape_index
                                        )
                                    ]
                                )
                            )
                            if np.any(
                                bank_alert
                                & (
                                    selected_shape
                                    == shape_index
                                )
                            )
                            else np.nan
                        ),
                    }
                )

    positive_scores_all = {
        method: np.concatenate(
            positive_score_parts[
                method
            ]
        )
        for method in cfg.methods
    }
    negative_scores_all = {
        method: np.concatenate(
            negative_score_parts[
                method
            ]
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
            positive_scores_all[
                method
            ],
            negative_scores_all[
                method
            ],
            thresholds[method],
            seed_record,
            cfg,
        )
        method_rows.append(
            summary
        )
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
                "rolling_exact_shape_latency4"
            ][stratum]
        )
        bank_hits = np.concatenate(
            positive_hits[
                "rolling_four_shape_bank_latency4"
            ][stratum]
        )
        codes = (
            exact_hits.astype(
                np.int8
            )
            * 2
            + bank_hits.astype(
                np.int8
            )
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
                "stratum_index": (
                    stratum_index
                ),
                "stratum": stratum,
                "neither": int(
                    counts[0]
                ),
                "bank_only": int(
                    counts[1]
                ),
                "exact_only": int(
                    counts[2]
                ),
                "both": int(
                    counts[3]
                ),
                "n": int(
                    counts.sum()
                ),
            }
        )

    timing_detail = pd.concat(
        timing_frames,
        ignore_index=True,
    )
    shape_summary = (
        shape_accuracy_row(
            seed_record[
                "replication"
            ],
            timing_detail[
                "true_shape_index"
            ].to_numpy(),
            timing_detail[
                "bank_selected_shape_index"
            ].to_numpy(),
            timing_detail[
                "bank_alert"
            ].to_numpy(),
            timing_detail[
                "bank_primary_hit"
            ].to_numpy(),
            cfg,
        )
    )

    method_frame = pd.DataFrame(
        method_rows
    ).set_index("method")
    paired_summary = {
        "replication": (
            seed_record[
                "replication"
            ]
        ),
        "exact_recall": float(
            method_frame.loc[
                "rolling_exact_shape_latency4",
                "recall_point",
            ]
        ),
        "bank_recall": float(
            method_frame.loc[
                "rolling_four_shape_bank_latency4",
                "recall_point",
            ]
        ),
        "bank_minus_exact": float(
            method_frame.loc[
                "rolling_four_shape_bank_latency4",
                "recall_point",
            ]
            - method_frame.loc[
                "rolling_exact_shape_latency4",
                "recall_point",
            ]
        ),
        "neither": int(
            total_counts[0]
        ),
        "bank_only": int(
            total_counts[1]
        ),
        "exact_only": int(
            total_counts[2]
        ),
        "both": int(
            total_counts[3]
        ),
        "positive_score_correlation": float(
            np.corrcoef(
                positive_scores_all[
                    "rolling_exact_shape_latency4"
                ],
                positive_scores_all[
                    "rolling_four_shape_bank_latency4"
                ],
            )[0, 1]
        ),
        "negative_score_correlation": float(
            np.corrcoef(
                negative_scores_all[
                    "rolling_exact_shape_latency4"
                ],
                negative_scores_all[
                    "rolling_four_shape_bank_latency4"
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
        "shape_summary": pd.DataFrame(
            [shape_summary]
        ),
        "shape_confusion": pd.DataFrame(
            confusion_rows
        ),
        "timing_detail": (
            timing_detail
        ),
        "negative_shape_summary": pd.DataFrame(
            negative_shape_rows
        ),
        "projection_diagnostics": pd.DataFrame(
            projection_rows
        ),
    }



def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    shape_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    method_details = {}
    bootstrap_frames = []
    sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(
        len(cfg.methods)
    )

    for method_index, method in enumerate(
        cfg.methods
    ):
        rep = method_summary[
            method_summary.method
            == method
        ].sort_values(
            "replication"
        )
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
                rep[
                    "maximum_fpr_upper_one_sided_95"
                ]
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
            int(row.bank_only),
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
        "rolling_exact_shape_latency4"
    ]
    bank = method_details[
        "rolling_four_shape_bank_latency4"
    ]
    delta_point = (
        bank[
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

    primary_n = int(
        shape_summary[
            "primary_hit_n"
        ].sum()
    )
    primary_correct = int(
        shape_summary[
            "primary_hit_shape_correct"
        ].sum()
    )
    alert_n = int(
        shape_summary[
            "alert_n"
        ].sum()
    )
    alert_correct = int(
        shape_summary[
            "alert_shape_correct"
        ].sum()
    )
    primary_accuracy = (
        primary_correct
        / primary_n
        if primary_n > 0
        else 0.0
    )
    primary_lower = (
        m22.m5.clopper_pearson_lower(
            primary_correct,
            primary_n,
        )
        if primary_n > 0
        else 0.0
    )
    primary_upper = (
        m2.clopper_pearson_upper(
            primary_correct,
            primary_n,
        )
        if primary_n > 0
        else 1.0
    )
    alert_accuracy = (
        alert_correct / alert_n
        if alert_n > 0
        else 0.0
    )
    shape_pass_count = int(
        shape_summary[
            "shape_identification_pass"
        ].sum()
    )
    shape_identification_pass = bool(
        primary_lower
        >= cfg.shape_accuracy_minimum_lower_one_sided_95
        and shape_pass_count
        >= cfg.minimum_shape_accuracy_holdouts
    )

    control_valid = bool(
        exact["operational_pass"]
    )
    if not control_valid:
        verdict = (
            "INVALID_M36_EXACT_SHAPE_CONTROL"
        )
    elif (
        bank["operational_pass"]
        and shape_identification_pass
    ):
        verdict = (
            "PASS_FOUR_SHAPE_BANK_AND_IDENTIFICATION"
        )
    elif bank[
        "operational_pass"
    ]:
        verdict = (
            "PASS_DETECTION_SHAPE_UNRELIABLE"
        )
    elif (
        bank[
            "holdout_pass_count"
        ]
        <= 2
        or bank[
            "aggregate_recall_upper_one_sided_95"
        ]
        <= cfg.minimum_global_recall_lower_one_sided_95
        or bank[
            "extreme_fpr_violation"
        ]
    ):
        verdict = (
            "STRONG_FAIL_FOUR_SHAPE_BANK"
        )
    else:
        verdict = (
            "INCONCLUSIVE_FOUR_SHAPE_BANK"
        )

    prediction = {
        "exact_recall_in_range": bool(
            cfg.prediction_exact_range[0]
            <= exact[
                "aggregate_recall_point"
            ]
            <= cfg.prediction_exact_range[1]
        ),
        "bank_recall_in_range": bool(
            cfg.prediction_bank_range[0]
            <= bank[
                "aggregate_recall_point"
            ]
            <= cfg.prediction_bank_range[1]
        ),
        "delta_in_range": bool(
            cfg.prediction_delta_range[0]
            <= delta_point
            <= cfg.prediction_delta_range[1]
        ),
        "control_valid": control_valid,
        "both_fpr_robust": bool(
            exact["fpr_robust"]
            and bank["fpr_robust"]
        ),
        "bank_threshold_in_range": bool(
            cfg.prediction_bank_threshold_range[0]
            <= bank["threshold"]
            <= cfg.prediction_bank_threshold_range[1]
        ),
        "bank_pass_count_in_range": bool(
            cfg.prediction_bank_pass_low
            <= bank[
                "holdout_pass_count"
            ]
            <= cfg.prediction_bank_pass_high
        ),
        "shape_accuracy_in_range": bool(
            cfg.prediction_shape_accuracy_range[0]
            <= primary_accuracy
            <= cfg.prediction_shape_accuracy_range[1]
        ),
        "overall_verdict_confirmed": bool(
            verdict
            == "INCONCLUSIVE_FOUR_SHAPE_BANK"
        ),
    }
    prediction[
        "fully_confirmed"
    ] = bool(
        all(
            prediction.values()
        )
    )

    return {
        "verdict": verdict,
        "control_valid": control_valid,
        "method_details": method_details,
        "paired_difference": {
            "bank_minus_exact_point": (
                delta_point
            ),
            "bank_minus_exact_lower_one_sided_95": (
                delta_lower
            ),
            "bank_minus_exact_upper_one_sided_95": (
                delta_upper
            ),
        },
        "shape_identification": {
            "primary_hit_n": (
                primary_n
            ),
            "primary_hit_shape_correct": (
                primary_correct
            ),
            "primary_hit_shape_accuracy": (
                primary_accuracy
            ),
            "primary_hit_shape_accuracy_lower_one_sided_95": (
                primary_lower
            ),
            "primary_hit_shape_accuracy_upper_one_sided_95": (
                primary_upper
            ),
            "alert_n": alert_n,
            "alert_shape_correct": (
                alert_correct
            ),
            "alert_shape_accuracy": (
                alert_accuracy
            ),
            "holdout_pass_count": (
                shape_pass_count
            ),
            "identification_pass": (
                shape_identification_pass
            ),
        },
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(
            bootstrap_frames,
            ignore_index=True,
        ),
        "delta_bootstrap": (
            delta_bootstrap
        ),
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
        "m35_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m35_dependency.py"
            )
        ),
        "m34_dependency_sha256": (
            sha256_file(
                ROOT
                / "arara_m34_dependency.py"
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
