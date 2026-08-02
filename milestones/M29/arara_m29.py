
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import platform
import sys
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parent
DEPENDENCY_DIR = ROOT / "dependency"
for directory in (DEPENDENCY_DIR, ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import arara_m22_dependency as m22
import arara_m28_dependency as m28


POSITIVE_STRATA = m22.POSITIVE_STRATA
NEGATIVE_FAMILIES = m22.NEGATIVE_FAMILIES
METHODS = ("baseline8", "projected_t8")


@dataclass(frozen=True)
class Config:
    version: str = "29.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    window_length: int = 8
    methods: tuple[str, ...] = METHODS

    calibration_seed: int = 2026082401
    holdout_root_seed: int = 2026082402
    aggregate_bootstrap_root_seed: int = 2026082403
    paired_difference_bootstrap_seed: int = 2026082404

    calibration_negatives_per_family: int = 50_000
    calibration_batch_size: int = 1_000

    holdout_count: int = 10
    holdout_positive_per_stratum_total: int = 2_500
    holdout_negative_per_family_total: int = 5_000
    holdout_batches: int = 20
    holdout_positive_per_stratum_per_batch: int = 125
    holdout_negative_per_family_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    extreme_fpr_upper_limit: float = 0.015
    minimum_holdout_passes: int = 8
    minimum_fpr_pass_holdouts: int = 9
    minimum_global_recall_lower_one_sided_95: float = 0.60
    minimum_stratum_recall_lower_one_sided_95: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55

    minimum_paired_delta_lower_one_sided_95: float = 0.10
    minimum_holdout_delta: float = 0.08
    minimum_holdouts_with_delta: int = 8
    strong_fail_candidate_recall_upper: float = 0.30

    rank_tolerance: float = 1e-10
    norm_tolerance: float = 1e-12
    bootstrap_replicates: int = 10_000

    prediction_baseline_range: tuple[float, float] = (0.27, 0.34)
    prediction_projected_range: tuple[float, float] = (0.45, 0.60)
    prediction_delta_range: tuple[float, float] = (0.15, 0.30)

    def analysis_config(self) -> m22.Config:
        return m22.Config(
            version=self.version,
            fixed_snr=self.fixed_snr,
            target_fraction=self.target_fraction,
            onset_offsets=(0,),
            replication_count=self.holdout_count,
            replication_root_seed=self.holdout_root_seed,
            aggregate_bootstrap_root_seed=self.aggregate_bootstrap_root_seed,
            development_negatives_per_family=2_000,
            holdout_positive_per_stratum_total=(
                self.holdout_positive_per_stratum_total
            ),
            holdout_negative_per_family_total=(
                self.holdout_negative_per_family_total
            ),
            holdout_batches=self.holdout_batches,
            holdout_positive_per_stratum_per_batch=(
                self.holdout_positive_per_stratum_per_batch
            ),
            holdout_negative_per_family_per_batch=(
                self.holdout_negative_per_family_per_batch
            ),
            development_fpr_target=self.development_fpr_target,
            holdout_fpr_upper_limit=self.holdout_fpr_upper_limit,
            extreme_fpr_upper_limit=self.extreme_fpr_upper_limit,
            minimum_replication_passes=self.minimum_holdout_passes,
            minimum_fpr_pass_replications=self.minimum_fpr_pass_holdouts,
            minimum_global_recall_lower_ci=(
                self.minimum_global_recall_lower_one_sided_95
            ),
            minimum_stratum_recall_lower_ci=(
                self.minimum_stratum_recall_lower_one_sided_95
            ),
            minimum_good_strata=self.minimum_good_strata,
            minimum_good_batches=self.minimum_good_batches,
            batch_recall_threshold=self.batch_recall_threshold,
            bootstrap_replicates=self.bootstrap_replicates,
            prediction_ranges=((0, 0.0, 1.0),),
        )


def _integer_seed(sequence: np.random.SeedSequence) -> int:
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def build_seed_plan(cfg: Config) -> dict:
    calibration_children = np.random.SeedSequence(
        cfg.calibration_seed
    ).spawn(len(NEGATIVE_FAMILIES))
    calibration = {
        family: {
            "integer_seed": _integer_seed(child),
            "entropy": child.entropy,
            "spawn_key": list(child.spawn_key),
        }
        for family, child in zip(
            NEGATIVE_FAMILIES,
            calibration_children,
        )
    }

    holdout_children = np.random.SeedSequence(
        cfg.holdout_root_seed
    ).spawn(cfg.holdout_count)
    holdouts = []
    for index, child in enumerate(holdout_children):
        subchildren = child.spawn(3)
        labels = ("development", "holdout", "bootstrap")
        seeds = {
            label: _integer_seed(sequence)
            for label, sequence in zip(labels, subchildren)
        }
        holdouts.append(
            {
                "replication": index,
                "seeds": seeds,
                "entropy": child.entropy,
                "spawn_key": list(child.spawn_key),
            }
        )
    return {"calibration": calibration, "holdouts": holdouts}


def calibration_core(cfg: Config) -> m22.m9.Config:
    analysis = cfg.analysis_config()
    record = {
        "replication": 0,
        "seeds": {
            "development": cfg.calibration_seed,
            "holdout": cfg.calibration_seed + 1,
            "bootstrap": cfg.calibration_seed + 2,
        },
    }
    return analysis.core_config(record)


def sbw_with_reference_nuisance(
    y: np.ndarray,
    raw_signal: np.ndarray,
    cfg: m22.m2.Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    if y.ndim != 3:
        raise ValueError("y must have shape (n, stars, time).")
    if raw_signal.shape != (y.shape[0], y.shape[2]):
        raise ValueError("raw_signal shape mismatch.")

    base = y[:, :, :cfg.baseline_n]
    mu = np.median(base, axis=2)
    scale = 1.4826 * np.median(
        np.abs(base - mu[:, :, None]),
        axis=2,
    )
    scale = np.maximum(scale, 1e-8)

    x = (y - mu[:, :, None]) / scale[:, :, None]
    reference_common = np.median(x[:, 1:, :], axis=1)

    target_base = x[:, 0, :cfg.baseline_n]
    reference_base = reference_common[:, :cfg.baseline_n]
    target_centered = (
        target_base
        - target_base.mean(axis=1, keepdims=True)
    )
    reference_centered = (
        reference_base
        - reference_base.mean(axis=1, keepdims=True)
    )

    beta_denominator = np.sum(
        reference_centered**2,
        axis=1,
    )
    beta_numerator = np.sum(
        target_centered * reference_centered,
        axis=1,
    )
    beta_hat = np.divide(
        beta_numerator,
        beta_denominator,
        out=np.zeros_like(beta_numerator),
        where=beta_denominator > 1e-12,
    )
    beta_hat = np.clip(beta_hat, 0.0, 3.0)

    common_subtracted = (
        x[:, 0, :]
        - beta_hat[:, None] * reference_common
    )
    residual_base = common_subtracted[:, :cfg.baseline_n]
    residual_median = np.median(
        residual_base,
        axis=1,
    )
    residual_scale = 1.4826 * np.median(
        np.abs(
            residual_base
            - residual_median[:, None]
        ),
        axis=1,
    )
    residual_scale = np.maximum(
        residual_scale,
        1e-8,
    )

    centered_base = (
        residual_base
        - residual_median[:, None]
    )
    phi_denominator = np.sum(
        centered_base[:, :-1] ** 2,
        axis=1,
    )
    phi_numerator = np.sum(
        centered_base[:, 1:]
        * centered_base[:, :-1],
        axis=1,
    )
    phi_hat = np.divide(
        phi_numerator,
        phi_denominator,
        out=np.zeros_like(phi_numerator),
        where=phi_denominator > 1e-12,
    )
    phi_hat = np.clip(phi_hat, 0.0, 0.8)

    all_centered = (
        common_subtracted
        - residual_median[:, None]
    )
    residual = np.empty_like(
        common_subtracted,
        dtype=np.float64,
    )
    residual[:, 0] = (
        all_centered[:, 0]
        / residual_scale
    )
    residual[:, 1:] = (
        all_centered[:, 1:]
        - phi_hat[:, None]
        * all_centered[:, :-1]
    ) / residual_scale[:, None]

    signal_normalized = (
        raw_signal
        / scale[:, 0, None]
    )
    processed_signal = np.empty_like(
        signal_normalized,
        dtype=np.float64,
    )
    processed_signal[:, 0] = (
        signal_normalized[:, 0]
        / residual_scale
    )
    processed_signal[:, 1:] = (
        signal_normalized[:, 1:]
        - phi_hat[:, None]
        * signal_normalized[:, :-1]
    ) / residual_scale[:, None]

    reference_median = np.median(
        reference_base,
        axis=1,
    )
    reference_centered_all = (
        reference_common
        - reference_median[:, None]
    )
    processed_reference = np.empty_like(
        reference_centered_all,
        dtype=np.float64,
    )
    processed_reference[:, 0] = (
        reference_centered_all[:, 0]
        / residual_scale
    )
    processed_reference[:, 1:] = (
        reference_centered_all[:, 1:]
        - phi_hat[:, None]
        * reference_centered_all[:, :-1]
    ) / residual_scale[:, None]

    parameters = {
        "target_scale": scale[:, 0],
        "beta_hat": beta_hat,
        "residual_scale": residual_scale,
        "residual_phi": phi_hat,
        "reference_baseline_median": reference_median,
    }
    return (
        residual,
        processed_signal,
        processed_reference,
        parameters,
    )


def extract_last_window(
    values: np.ndarray,
    endpoint: np.ndarray,
    length: int,
) -> np.ndarray:
    values = np.asarray(values)
    endpoint = np.asarray(endpoint, dtype=np.int32)
    if values.ndim != 2:
        raise ValueError("values must be 2D.")
    if endpoint.shape != (values.shape[0],):
        raise ValueError("endpoint shape mismatch.")

    starts = endpoint - length + 1
    if np.any(starts < 0):
        raise ValueError("Window begins before time zero.")

    indices = (
        starts[:, None]
        + np.arange(length)[None, :]
    )
    return np.take_along_axis(
        values,
        indices,
        axis=1,
    )


def baseline_score(
    residual: np.ndarray,
    processed_template: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> np.ndarray:
    residual_window = extract_last_window(
        residual,
        endpoint,
        cfg.window_length,
    )
    template_window = extract_last_window(
        processed_template,
        endpoint,
        cfg.window_length,
    )
    numerator = np.sum(
        residual_window * template_window,
        axis=1,
    )
    denominator = np.sqrt(
        np.sum(template_window**2, axis=1)
    )
    return np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=denominator > cfg.norm_tolerance,
    )


def projected_partial_t_score(
    residual: np.ndarray,
    processed_template: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, dict]:
    residual_window = extract_last_window(
        residual,
        endpoint,
        cfg.window_length,
    )
    template_window = extract_last_window(
        processed_template,
        endpoint,
        cfg.window_length,
    )
    reference_window = extract_last_window(
        processed_reference,
        endpoint,
        cfg.window_length,
    )

    n = residual_window.shape[0]
    constant = np.ones(
        (n, cfg.window_length),
        dtype=np.float64,
    )
    ramp = np.broadcast_to(
        np.linspace(
            -1.0,
            1.0,
            cfg.window_length,
            dtype=np.float64,
        ),
        (n, cfg.window_length),
    )
    nuisance = np.stack(
        [
            constant,
            ramp,
            reference_window,
        ],
        axis=2,
    )

    pseudo_inverse = np.linalg.pinv(
        nuisance,
        rcond=cfg.rank_tolerance,
    )
    residual_coefficients = np.matmul(
        pseudo_inverse,
        residual_window[:, :, None],
    )
    template_coefficients = np.matmul(
        pseudo_inverse,
        template_window[:, :, None],
    )
    residual_projected = (
        residual_window
        - np.matmul(
            nuisance,
            residual_coefficients,
        )[:, :, 0]
    )
    template_projected = (
        template_window
        - np.matmul(
            nuisance,
            template_coefficients,
        )[:, :, 0]
    )

    ranks = np.linalg.matrix_rank(
        nuisance,
        tol=cfg.rank_tolerance,
    )
    degrees = (
        cfg.window_length
        - ranks
        - 1
    ).astype(np.int16)

    residual_norm = np.linalg.norm(
        residual_projected,
        axis=1,
    )
    template_norm = np.linalg.norm(
        template_projected,
        axis=1,
    )
    denominator = (
        residual_norm * template_norm
    )
    correlation = np.divide(
        np.sum(
            residual_projected
            * template_projected,
            axis=1,
        ),
        denominator,
        out=np.zeros(n, dtype=np.float64),
        where=denominator > cfg.norm_tolerance,
    )
    correlation = np.clip(
        correlation,
        -1.0,
        1.0,
    )

    valid = (
        (degrees >= 1)
        & (residual_norm > cfg.norm_tolerance)
        & (template_norm > cfg.norm_tolerance)
        & (correlation > 0.0)
    )
    scores = np.zeros(n, dtype=np.float64)
    finite = valid & (
        correlation
        < 1.0 - 1e-15
    )
    scores[finite] = (
        correlation[finite]
        * np.sqrt(
            degrees[finite]
            / (
                1.0
                - correlation[finite] ** 2
            )
        )
    )
    scores[
        valid
        & (
            correlation
            >= 1.0 - 1e-15
        )
    ] = np.inf

    diagnostics = {
        "rank": ranks.astype(np.int16),
        "degrees_of_freedom": degrees,
        "template_degenerate": (
            template_norm
            <= cfg.norm_tolerance
        ),
        "residual_degenerate": (
            residual_norm
            <= cfg.norm_tolerance
        ),
    }
    return scores, diagnostics


def paired_scores_from_processed(
    residual: np.ndarray,
    processed_template: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    baseline = baseline_score(
        residual,
        processed_template,
        endpoint,
        cfg,
    )
    projected, diagnostics = (
        projected_partial_t_score(
            residual,
            processed_template,
            processed_reference,
            endpoint,
            cfg,
        )
    )
    return (
        {
            "baseline8": baseline,
            "projected_t8": projected,
        },
        diagnostics,
    )


def evaluate_positive_panel(
    panel: m22.m9.PositivePanel,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_signal

    (
        residual,
        processed_signal,
        processed_reference,
        parameters,
    ) = sbw_with_reference_nuisance(
        observed,
        raw_signal,
        core.data_config(),
    )
    return paired_scores_from_processed(
        residual,
        processed_signal,
        processed_reference,
        panel.t100,
        cfg,
    )


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    data_cfg = core.data_config()
    data = m22.m2.generate_negative_family(
        family,
        n,
        rng,
        data_cfg,
    )
    virtual_signal, virtual_onset, _, _ = (
        m22.m5.generate_virtual_hypotheses(
            n,
            rng,
            data_cfg,
        )
    )
    endpoint = m22.m9.time_at_fraction(
        virtual_signal,
        cfg.target_fraction,
    )
    (
        residual,
        processed_template,
        processed_reference,
        parameters,
    ) = sbw_with_reference_nuisance(
        data.y,
        virtual_signal,
        data_cfg,
    )
    return paired_scores_from_processed(
        residual,
        processed_template,
        processed_reference,
        endpoint,
        cfg,
    )


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> dict:
    seed = seed_plan["calibration"][family][
        "integer_seed"
    ]
    rng = np.random.default_rng(seed)
    core = calibration_core(cfg)

    score_parts = {
        method: [] for method in cfg.methods
    }
    rank_parts = []
    template_degenerate_parts = []
    residual_degenerate_parts = []
    remaining = cfg.calibration_negatives_per_family

    while remaining > 0:
        n = min(
            cfg.calibration_batch_size,
            remaining,
        )
        scores, diagnostics = evaluate_negative_family(
            family,
            n,
            rng,
            cfg,
            core,
        )
        for method in cfg.methods:
            score_parts[method].append(
                np.asarray(
                    scores[method],
                    dtype=np.float32,
                )
            )
        rank_parts.append(diagnostics["rank"])
        template_degenerate_parts.append(
            diagnostics["template_degenerate"]
        )
        residual_degenerate_parts.append(
            diagnostics["residual_degenerate"]
        )
        remaining -= n

    output = {
        f"score_{method}": np.concatenate(
            score_parts[method]
        )
        for method in cfg.methods
    }
    output["rank"] = np.concatenate(
        rank_parts
    ).astype(np.int16)
    output["template_degenerate"] = np.concatenate(
        template_degenerate_parts
    ).astype(np.int8)
    output["residual_degenerate"] = np.concatenate(
        residual_degenerate_parts
    ).astype(np.int8)

    for key, values in output.items():
        if (
            len(values)
            != cfg.calibration_negatives_per_family
        ):
            raise RuntimeError(
                f"Wrong calibration size: "
                f"{family}, {key}."
            )
    for method in cfg.methods:
        values = output[f"score_{method}"]
        if not np.isfinite(values).all():
            raise RuntimeError(
                f"Non-finite calibration score: "
                f"{family}, {method}."
            )
    return output


def freeze_thresholds(
    cfg: Config,
    family_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    loaded = {}
    diagnostic_rows = []

    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            loaded[family] = {
                method: data[
                    f"score_{method}"
                ].copy()
                for method in cfg.methods
            }
            ranks = data["rank"]
            template_degenerate = data[
                "template_degenerate"
            ]
            residual_degenerate = data[
                "residual_degenerate"
            ]
            for rank in sorted(
                np.unique(ranks)
            ):
                diagnostic_rows.append(
                    {
                        "family": family,
                        "rank": int(rank),
                        "count": int(
                            np.sum(ranks == rank)
                        ),
                        "n": len(ranks),
                        "fraction": float(
                            np.mean(ranks == rank)
                        ),
                        "template_degenerate_fraction": float(
                            np.mean(
                                template_degenerate
                            )
                        ),
                        "residual_degenerate_fraction": float(
                            np.mean(
                                residual_degenerate
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
            m22.m2.conservative_threshold(
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
        },
        pd.DataFrame(rows),
        pd.DataFrame(diagnostic_rows),
    )


def paired_stratified_bootstrap(
    pair_counts: dict[str, np.ndarray],
    replicates: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    baseline = np.zeros(
        replicates,
        dtype=np.float64,
    )
    projected = np.zeros(
        replicates,
        dtype=np.float64,
    )

    for stratum in POSITIVE_STRATA:
        counts = np.asarray(
            pair_counts[stratum],
            dtype=np.int64,
        )
        if counts.shape != (4,):
            raise ValueError(
                "Pair counts must have four categories."
            )
        n = int(counts.sum())
        probabilities = counts / n
        draws = rng.multinomial(
            n,
            probabilities,
            size=replicates,
        )
        baseline += (
            (
                draws[:, 2]
                + draws[:, 3]
            )
            / n
            / len(POSITIVE_STRATA)
        )
        projected += (
            (
                draws[:, 1]
                + draws[:, 3]
            )
            / n
            / len(POSITIVE_STRATA)
        )

    return pd.DataFrame(
        {
            "baseline_recall": baseline,
            "projected_recall": projected,
            "delta": projected - baseline,
        }
    )


def hierarchical_paired_bootstrap(
    pair_count_array: np.ndarray,
    replicates: int,
    seed: int,
) -> np.ndarray:
    counts = np.asarray(
        pair_count_array,
        dtype=np.int64,
    )
    expected_shape = (
        counts.shape[0],
        len(POSITIVE_STRATA),
        4,
    )
    if counts.shape != expected_shape:
        raise ValueError(
            "pair_count_array must be H x S x 4."
        )

    holdout_count = counts.shape[0]
    rng = np.random.default_rng(seed)
    sampled_holdouts = rng.integers(
        0,
        holdout_count,
        size=(replicates, holdout_count),
    )
    output = np.zeros(
        replicates,
        dtype=np.float64,
    )

    for position in range(holdout_count):
        selected = sampled_holdouts[:, position]
        position_delta = np.zeros(
            replicates,
            dtype=np.float64,
        )

        for holdout in range(holdout_count):
            mask = selected == holdout
            draw_count = int(mask.sum())
            if draw_count == 0:
                continue

            selected_delta = np.zeros(
                draw_count,
                dtype=np.float64,
            )
            for stratum_index in range(
                len(POSITIVE_STRATA)
            ):
                category_counts = counts[
                    holdout,
                    stratum_index,
                ]
                n = int(category_counts.sum())
                probabilities = (
                    category_counts / n
                )
                draws = rng.multinomial(
                    n,
                    probabilities,
                    size=draw_count,
                )
                baseline = (
                    draws[:, 2]
                    + draws[:, 3]
                ) / n
                projected = (
                    draws[:, 1]
                    + draws[:, 3]
                ) / n
                selected_delta += (
                    projected - baseline
                ) / len(POSITIVE_STRATA)

            position_delta[mask] = selected_delta

        output += position_delta / holdout_count

    return output


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

    positive_score_parts = {
        method: [] for method in cfg.methods
    }
    negative_score_parts = {
        method: [] for method in cfg.methods
    }

    rank_rows = []

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
            panel = m22.m9.generate_positive_panel(
                shape,
                context,
                cfg.holdout_positive_per_stratum_per_batch,
                rng,
                core,
            )
            scores, diagnostics = evaluate_positive_panel(
                panel,
                cfg,
                core,
            )
            for method in cfg.methods:
                values = scores[method]
                hits = (
                    values
                    >= thresholds[method]
                )
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

            ranks = diagnostics["rank"]
            for rank in np.unique(ranks):
                rank_rows.append(
                    {
                        "replication": seed_record[
                            "replication"
                        ],
                        "population": "positive",
                        "group": stratum,
                        "rank": int(rank),
                        "count": int(
                            np.sum(ranks == rank)
                        ),
                        "n": len(ranks),
                        "template_degenerate": int(
                            np.sum(
                                diagnostics[
                                    "template_degenerate"
                                ]
                            )
                        ),
                        "residual_degenerate": int(
                            np.sum(
                                diagnostics[
                                    "residual_degenerate"
                                ]
                            )
                        ),
                    }
                )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[len(POSITIVE_STRATA):],
        ):
            scores, diagnostics = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            for method in cfg.methods:
                values = scores[method]
                alerts = (
                    values
                    >= thresholds[method]
                )
                negative_counts[method][family] += int(
                    alerts.sum()
                )
                negative_ns[method][family] += len(
                    alerts
                )
                negative_score_parts[method].append(
                    values.astype(np.float32)
                )

            ranks = diagnostics["rank"]
            for rank in np.unique(ranks):
                rank_rows.append(
                    {
                        "replication": seed_record[
                            "replication"
                        ],
                        "population": "negative",
                        "group": family,
                        "rank": int(rank),
                        "count": int(
                            np.sum(ranks == rank)
                        ),
                        "n": len(ranks),
                        "template_degenerate": int(
                            np.sum(
                                diagnostics[
                                    "template_degenerate"
                                ]
                            )
                        ),
                        "residual_degenerate": int(
                            np.sum(
                                diagnostics[
                                    "residual_degenerate"
                                ]
                            )
                        ),
                    }
                )

    method_rows = []
    stratum_rows = []
    negative_rows = []
    batch_rows = []

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

    pair_counts = {}
    for stratum in POSITIVE_STRATA:
        baseline_hits = np.concatenate(
            positive_hits["baseline8"][stratum]
        )
        projected_hits = np.concatenate(
            positive_hits["projected_t8"][stratum]
        )
        codes = (
            baseline_hits.astype(np.int8) * 2
            + projected_hits.astype(np.int8)
        )
        pair_counts[stratum] = np.bincount(
            codes,
            minlength=4,
        )

    for method_index, method in enumerate(
        cfg.methods
    ):
        fpr_pass = True
        maximum_fpr_upper = 0.0

        for family in NEGATIVE_FAMILIES:
            x = negative_counts[method][family]
            n = negative_ns[method][family]
            upper = m22.m2.clopper_pearson_upper(
                x,
                n,
            )
            maximum_fpr_upper = max(
                maximum_fpr_upper,
                upper,
            )
            if upper > cfg.holdout_fpr_upper_limit:
                fpr_pass = False

            negative_rows.append(
                {
                    "replication": seed_record[
                        "replication"
                    ],
                    "method": method,
                    "family": family,
                    "alerts": x,
                    "n": n,
                    "rate": x / n,
                    "fpr_upper_one_sided_95": upper,
                }
            )

        hits_by_stratum = {}
        good_strata = 0
        stratum_rates = []

        for stratum in POSITIVE_STRATA:
            hits = np.concatenate(
                positive_hits[method][stratum]
            )
            x = int(hits.sum())
            n = len(hits)
            lower = m22.m5.clopper_pearson_lower(
                x,
                n,
            )
            good_strata += int(
                lower
                >= cfg.minimum_stratum_recall_lower_one_sided_95
            )
            hits_by_stratum[stratum] = hits
            stratum_rates.append(x / n)
            stratum_rows.append(
                {
                    "replication": seed_record[
                        "replication"
                    ],
                    "method": method,
                    "stratum": stratum,
                    "hits": x,
                    "n": n,
                    "recall": x / n,
                    "recall_lower_one_sided_95": lower,
                }
            )

        bootstrap = m22.m5.stratified_bootstrap_recall(
            hits_by_stratum,
            cfg.bootstrap_replicates,
            seed_record["seeds"]["bootstrap"]
            + method_index,
        )
        recall_point = float(
            np.mean(stratum_rates)
        )
        recall_lower = float(
            np.quantile(bootstrap, 0.05)
        )
        recall_upper = float(
            np.quantile(bootstrap, 0.95)
        )

        good_batches = 0
        for batch in range(cfg.holdout_batches):
            hits = sum(
                positive_batch_counts[
                    method
                ][stratum][batch]
                for stratum in POSITIVE_STRATA
            )
            n = sum(
                positive_batch_ns[
                    method
                ][stratum][batch]
                for stratum in POSITIVE_STRATA
            )
            recall = hits / n
            good_batches += int(
                recall
                >= cfg.batch_recall_threshold
            )
            batch_rows.append(
                {
                    "replication": seed_record[
                        "replication"
                    ],
                    "method": method,
                    "batch": batch,
                    "hits": hits,
                    "n": n,
                    "recall": recall,
                }
            )

        passed = bool(
            fpr_pass
            and recall_lower
            >= cfg.minimum_global_recall_lower_one_sided_95
            and good_strata
            >= cfg.minimum_good_strata
            and good_batches
            >= cfg.minimum_good_batches
        )

        positive_values = positive_scores_all[method]
        negative_values = negative_scores_all[method]
        labels = np.concatenate(
            [
                np.ones(
                    len(positive_values),
                    dtype=int,
                ),
                np.zeros(
                    len(negative_values),
                    dtype=int,
                ),
            ]
        )
        combined_values = np.concatenate(
            [positive_values, negative_values]
        )

        method_rows.append(
            {
                "replication": seed_record[
                    "replication"
                ],
                "method": method,
                "threshold": thresholds[method],
                "recall_point": recall_point,
                "recall_lower_one_sided_95": recall_lower,
                "recall_upper_one_sided_95": recall_upper,
                "good_strata": good_strata,
                "good_batches": good_batches,
                "fpr_pass": fpr_pass,
                "maximum_fpr_upper_one_sided_95": (
                    maximum_fpr_upper
                ),
                "pass": passed,
                "auroc": float(
                    roc_auc_score(
                        labels,
                        combined_values,
                    )
                ),
                "average_precision": float(
                    average_precision_score(
                        labels,
                        combined_values,
                    )
                ),
            }
        )

    paired_bootstrap = paired_stratified_bootstrap(
        pair_counts,
        cfg.bootstrap_replicates,
        seed_record["seeds"]["bootstrap"]
        + 100,
    )
    baseline_point = float(
        paired_bootstrap[
            "baseline_recall"
        ].mean()
    )
    projected_point = float(
        paired_bootstrap[
            "projected_recall"
        ].mean()
    )
    delta_point = (
        projected_point - baseline_point
    )

    baseline_positive = positive_scores_all[
        "baseline8"
    ]
    projected_positive = positive_scores_all[
        "projected_t8"
    ]
    baseline_negative = negative_scores_all[
        "baseline8"
    ]
    projected_negative = negative_scores_all[
        "projected_t8"
    ]

    paired_row = {
        "replication": seed_record["replication"],
        "baseline_recall_point": baseline_point,
        "projected_recall_point": projected_point,
        "delta_point": delta_point,
        "delta_lower_one_sided_95": float(
            np.quantile(
                paired_bootstrap["delta"],
                0.05,
            )
        ),
        "delta_upper_one_sided_95": float(
            np.quantile(
                paired_bootstrap["delta"],
                0.95,
            )
        ),
        "positive_score_correlation": float(
            np.corrcoef(
                baseline_positive,
                projected_positive,
            )[0, 1]
        ),
        "negative_score_correlation": float(
            np.corrcoef(
                baseline_negative,
                projected_negative,
            )[0, 1]
        ),
        "neither_detected": int(
            sum(
                counts[0]
                for counts in pair_counts.values()
            )
        ),
        "projected_only_detected": int(
            sum(
                counts[1]
                for counts in pair_counts.values()
            )
        ),
        "baseline_only_detected": int(
            sum(
                counts[2]
                for counts in pair_counts.values()
            )
        ),
        "both_detected": int(
            sum(
                counts[3]
                for counts in pair_counts.values()
            )
        ),
    }

    pair_rows = []
    for stratum_index, stratum in enumerate(
        POSITIVE_STRATA
    ):
        counts = pair_counts[stratum]
        pair_rows.append(
            {
                "replication": seed_record[
                    "replication"
                ],
                "stratum_index": stratum_index,
                "stratum": stratum,
                "neither": int(counts[0]),
                "projected_only": int(counts[1]),
                "baseline_only": int(counts[2]),
                "both": int(counts[3]),
                "n": int(counts.sum()),
            }
        )

    return {
        "method_summary": pd.DataFrame(method_rows),
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
        "paired_summary": pd.DataFrame([paired_row]),
        "pair_counts": pd.DataFrame(pair_rows),
        "rank_diagnostics": pd.DataFrame(rank_rows),
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
        if len(rep) != cfg.holdout_count:
            raise RuntimeError(
                f"Wrong holdout count for {method}."
            )

        counts = []
        ns = []
        for holdout in range(
            cfg.holdout_count
        ):
            subset = stratum_summary[
                (
                    stratum_summary.method
                    == method
                )
                & (
                    stratum_summary.replication
                    == holdout
                )
            ].set_index("stratum")
            counts.append(
                [
                    int(
                        subset.loc[
                            stratum,
                            "hits",
                        ]
                    )
                    for stratum in POSITIVE_STRATA
                ]
            )
            ns.append(
                [
                    int(
                        subset.loc[
                            stratum,
                            "n",
                        ]
                    )
                    for stratum in POSITIVE_STRATA
                ]
            )

        bootstrap_seed = _integer_seed(
            sequences[method_index]
        )
        bootstrap = m22.m15.hierarchical_bootstrap(
            np.asarray(counts),
            np.asarray(ns),
            cfg.bootstrap_replicates,
            bootstrap_seed,
        )
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
            "threshold": thresholds[method],
            "threshold_driver": (
                threshold_drivers[method]
            ),
            "aggregate_recall_point": point,
            "aggregate_recall_lower_one_sided_95": lower,
            "aggregate_recall_upper_one_sided_95": upper,
            "holdout_pass_count": pass_count,
            "fpr_pass_holdout_count": fpr_pass_count,
            "fpr_robust": fpr_robust,
            "extreme_fpr_violation": extreme,
            "operational_pass": operational_pass,
            "auroc_mean": float(
                rep.auroc.mean()
            ),
            "average_precision_mean": float(
                rep.average_precision.mean()
            ),
        }

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
            int(row.projected_only),
            int(row.baseline_only),
            int(row.both),
        ]

    delta_bootstrap = hierarchical_paired_bootstrap(
        pair_array,
        cfg.bootstrap_replicates,
        cfg.paired_difference_bootstrap_seed,
    )
    delta_point = (
        method_details[
            "projected_t8"
        ][
            "aggregate_recall_point"
        ]
        - method_details[
            "baseline8"
        ][
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

    pivot = method_summary.pivot(
        index="replication",
        columns="method",
        values="recall_point",
    )
    holdout_deltas = (
        pivot["projected_t8"]
        - pivot["baseline8"]
    )
    holdouts_with_material_delta = int(
        np.sum(
            holdout_deltas
            >= cfg.minimum_holdout_delta
        )
    )
    superiority_pass = bool(
        delta_lower
        >= cfg.minimum_paired_delta_lower_one_sided_95
        and holdouts_with_material_delta
        >= cfg.minimum_holdouts_with_delta
    )

    candidate = method_details[
        "projected_t8"
    ]
    extreme_any = bool(
        candidate[
            "extreme_fpr_violation"
        ]
        or method_details[
            "baseline8"
        ][
            "extreme_fpr_violation"
        ]
    )

    if (
        candidate["operational_pass"]
        and superiority_pass
    ):
        overall = (
            "PASS_NUISANCE_PROJECTED_CANDIDATE"
        )
    elif (
        delta_lower
        >= cfg.minimum_paired_delta_lower_one_sided_95
        and not candidate[
            "operational_pass"
        ]
    ):
        overall = (
            "PARTIAL_GAIN_NOT_OPERATIONAL"
        )
    elif (
        delta_upper <= 0.0
        or candidate[
            "aggregate_recall_upper_one_sided_95"
        ]
        <= cfg.strong_fail_candidate_recall_upper
        or extreme_any
    ):
        overall = (
            "STRONG_FAIL_NUISANCE_PROJECTION"
        )
    else:
        overall = (
            "INCONCLUSIVE_NUISANCE_PROJECTION"
        )

    baseline_range = (
        cfg.prediction_baseline_range
    )
    projected_range = (
        cfg.prediction_projected_range
    )
    delta_range = cfg.prediction_delta_range

    prediction = {
        "baseline_recall_in_range": bool(
            baseline_range[0]
            <= method_details[
                "baseline8"
            ][
                "aggregate_recall_point"
            ]
            <= baseline_range[1]
        ),
        "projected_recall_in_range": bool(
            projected_range[0]
            <= candidate[
                "aggregate_recall_point"
            ]
            <= projected_range[1]
        ),
        "delta_in_range": bool(
            delta_range[0]
            <= delta_point
            <= delta_range[1]
        ),
        "both_fpr_robust": bool(
            method_details[
                "baseline8"
            ]["fpr_robust"]
            and candidate["fpr_robust"]
        ),
        "material_paired_gain": superiority_pass,
        "candidate_holdout_passes_0_to_5": bool(
            0
            <= candidate[
                "holdout_pass_count"
            ]
            <= 5
        ),
        "overall_verdict_confirmed": bool(
            overall
            == "PARTIAL_GAIN_NOT_OPERATIONAL"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": overall,
        "method_details": method_details,
        "paired_superiority": {
            "delta_point": delta_point,
            "delta_lower_one_sided_95": (
                delta_lower
            ),
            "delta_upper_one_sided_95": (
                delta_upper
            ),
            "holdout_deltas": {
                str(int(index)): float(value)
                for index, value in holdout_deltas.items()
            },
            "holdouts_with_delta_at_least_0_08": (
                holdouts_with_material_delta
            ),
            "superiority_pass": superiority_pass,
        },
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(
            bootstrap_frames,
            ignore_index=True,
        ),
        "delta_bootstrap": delta_bootstrap,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


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
        "m22_dependency_sha256": sha256_file(
            ROOT / "arara_m22_dependency.py"
        ),
        "m28_dependency_sha256": sha256_file(
            ROOT / "arara_m28_dependency.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
