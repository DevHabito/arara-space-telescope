
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

import arara_m32_dependency as m32


POSITIVE_STRATA = m32.POSITIVE_STRATA
NEGATIVE_FAMILIES = m32.NEGATIVE_FAMILIES
METHODS = (
    "exact_reference_projected8",
    "hinge_reference_projected8",
    "permuted_hinge_reference_projected8",
)


@dataclass(frozen=True)
class Config(m32.Config):
    version: str = "33.0"
    methods: tuple[str, ...] = METHODS

    calibration_seed: int = 2026082801
    calibration_permutation_seed: int = 2026082802
    holdout_root_seed: int = 2026082803
    holdout_permutation_seed: int = 2026082804
    aggregate_bootstrap_root_seed: int = 2026082805
    paired_difference_bootstrap_seed: int = 2026082806

    association_margin: float = 0.02
    minimum_holdout_association_delta: float = 0.015
    minimum_holdouts_with_association_delta: int = 8

    prediction_exact_range: tuple[float, float] = (0.75, 0.85)
    prediction_hinge_range: tuple[float, float] = (0.74, 0.79)
    prediction_permuted_range: tuple[float, float] = (0.73, 0.79)
    prediction_association_delta_range: tuple[float, float] = (
        -0.01,
        0.01,
    )
    prediction_permuted_pass_low: int = 8
    prediction_permuted_pass_high: int = 10


def _integer_seed(sequence: np.random.SeedSequence) -> int:
    return int(
        sequence.generate_state(
            1,
            dtype=np.uint32,
        )[0]
    )


def build_seed_plan(cfg: Config) -> dict:
    plan = m32.build_seed_plan(cfg)

    calibration_children = np.random.SeedSequence(
        cfg.calibration_permutation_seed
    ).spawn(len(NEGATIVE_FAMILIES))
    plan["calibration_permutation"] = {
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
        cfg.holdout_permutation_seed
    ).spawn(cfg.holdout_count)
    for record, child in zip(
        plan["holdouts"],
        holdout_children,
    ):
        record["permutation_seed"] = _integer_seed(child)
        record["permutation_entropy"] = child.entropy
        record["permutation_spawn_key"] = list(child.spawn_key)

    return plan


calibration_core = m32.calibration_core
sha256_file = m32.sha256_file


def random_derangement(
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if n < 2:
        raise ValueError("Derangement requires n >= 2.")
    identity = np.arange(n)
    for _ in range(10_000):
        permutation = rng.permutation(n)
        if np.all(permutation != identity):
            return permutation
    raise RuntimeError("Could not generate derangement.")


def three_reference_scores(
    residual: np.ndarray,
    exact_processed_template: np.ndarray,
    hinge_processed_template: np.ndarray,
    permuted_processed_template: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    exact_score, exact_diag = (
        m32.m30.reference_projected_score(
            residual,
            exact_processed_template,
            processed_reference,
            endpoint,
            cfg,
        )
    )
    hinge_score, hinge_diag = (
        m32.m30.reference_projected_score(
            residual,
            hinge_processed_template,
            processed_reference,
            endpoint,
            cfg,
        )
    )
    permuted_score, permuted_diag = (
        m32.m30.reference_projected_score(
            residual,
            permuted_processed_template,
            processed_reference,
            endpoint,
            cfg,
        )
    )
    return (
        {
            "exact_reference_projected8": exact_score,
            "hinge_reference_projected8": hinge_score,
            "permuted_hinge_reference_projected8": permuted_score,
        },
        {
            "exact_energy_retention": exact_diag[
                "energy_retention"
            ],
            "hinge_energy_retention": hinge_diag[
                "energy_retention"
            ],
            "permuted_energy_retention": permuted_diag[
                "energy_retention"
            ],
            "exact_template_degenerate": exact_diag[
                "template_degenerate"
            ],
            "hinge_template_degenerate": hinge_diag[
                "template_degenerate"
            ],
            "permuted_template_degenerate": permuted_diag[
                "template_degenerate"
            ],
            "reference_degenerate": exact_diag[
                "reference_degenerate"
            ],
        },
    )


def evaluate_positive_panel(
    panel: m32.m22.m9.PositivePanel,
    permutation_rng: np.random.Generator,
    cfg: Config,
    core: m32.m22.m9.Config,
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
        exact_processed_signal,
        processed_reference,
        params,
    ) = m32.m30.m29.sbw_with_reference_nuisance(
        observed,
        raw_signal,
        core.data_config(),
    )

    hinge_onset, hinge_objective = m32.estimate_onset_split(
        residual,
        panel.t100,
        cfg,
    )
    permutation = random_derangement(
        len(hinge_onset),
        permutation_rng,
    )
    permuted_onset = hinge_onset[permutation]

    hinge_processed_signal = m32.process_shifted_template(
        raw_signal,
        panel.onset,
        hinge_onset,
        params,
    )
    permuted_processed_signal = m32.process_shifted_template(
        raw_signal,
        panel.onset,
        permuted_onset,
        params,
    )

    scores, diagnostics = three_reference_scores(
        residual,
        exact_processed_signal,
        hinge_processed_signal,
        permuted_processed_signal,
        processed_reference,
        panel.t100,
        cfg,
    )
    diagnostics.update(
        {
            "hinge_onset": hinge_onset.astype(np.int16),
            "permuted_onset": permuted_onset.astype(np.int16),
            "true_onset": panel.onset.astype(np.int16),
            "hinge_error": (
                hinge_onset.astype(np.int32)
                - panel.onset.astype(np.int32)
            ),
            "permuted_error": (
                permuted_onset.astype(np.int32)
                - panel.onset.astype(np.int32)
            ),
            "hinge_objective": hinge_objective,
            "permutation": permutation.astype(np.int16),
        }
    )
    return scores, diagnostics


def evaluate_negative_family(
    family: str,
    n: int,
    curve_rng: np.random.Generator,
    permutation_rng: np.random.Generator,
    cfg: Config,
    core: m32.m22.m9.Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    data_cfg = core.data_config()
    data = m32.m22.m2.generate_negative_family(
        family,
        n,
        curve_rng,
        data_cfg,
    )
    virtual_signal, reference_onset, _, _ = (
        m32.m22.m5.generate_virtual_hypotheses(
            n,
            curve_rng,
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
    hinge_onset, hinge_objective = m32.estimate_onset_split(
        residual,
        endpoint,
        cfg,
    )
    permutation = random_derangement(
        n,
        permutation_rng,
    )
    permuted_onset = hinge_onset[permutation]

    hinge_processed_template = m32.process_shifted_template(
        virtual_signal,
        reference_onset,
        hinge_onset,
        params,
    )
    permuted_processed_template = m32.process_shifted_template(
        virtual_signal,
        reference_onset,
        permuted_onset,
        params,
    )
    scores, diagnostics = three_reference_scores(
        residual,
        exact_processed_template,
        hinge_processed_template,
        permuted_processed_template,
        processed_reference,
        endpoint,
        cfg,
    )
    diagnostics.update(
        {
            "reference_onset": reference_onset.astype(np.int16),
            "hinge_onset": hinge_onset.astype(np.int16),
            "permuted_onset": permuted_onset.astype(np.int16),
            "endpoint": endpoint.astype(np.int16),
            "hinge_objective": hinge_objective,
            "permutation": permutation.astype(np.int16),
        }
    )
    return scores, diagnostics


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> dict:
    curve_rng = np.random.default_rng(
        seed_plan["calibration"][family]["integer_seed"]
    )
    permutation_rng = np.random.default_rng(
        seed_plan["calibration_permutation"][family][
            "integer_seed"
        ]
    )
    core = calibration_core(cfg)

    score_parts = {
        method: [] for method in cfg.methods
    }
    diagnostic_parts = {
        "reference_onset": [],
        "hinge_onset": [],
        "permuted_onset": [],
        "endpoint": [],
        "exact_energy_retention": [],
        "hinge_energy_retention": [],
        "permuted_energy_retention": [],
        "exact_template_degenerate": [],
        "hinge_template_degenerate": [],
        "permuted_template_degenerate": [],
        "reference_degenerate": [],
        "permutation": [],
    }

    remaining = cfg.calibration_negatives_per_family
    while remaining > 0:
        n = min(
            cfg.calibration_batch_size,
            remaining,
        )
        scores, diagnostics = evaluate_negative_family(
            family,
            n,
            curve_rng,
            permutation_rng,
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
        for key in diagnostic_parts:
            dtype = (
                np.float32
                if "energy" in key
                else (
                    np.int8
                    if "degenerate" in key
                    else np.int16
                )
            )
            diagnostic_parts[key].append(
                np.asarray(
                    diagnostics[key],
                    dtype=dtype,
                )
            )
        remaining -= n

    output = {
        f"score_{method}": np.concatenate(
            score_parts[method]
        )
        for method in cfg.methods
    }
    for key, parts in diagnostic_parts.items():
        output[key] = np.concatenate(parts)

    expected = cfg.calibration_negatives_per_family
    for key, values in output.items():
        if len(values) != expected:
            raise RuntimeError(
                f"Wrong calibration size: {family}, {key}."
            )
    for method in cfg.methods:
        if not np.isfinite(
            output[f"score_{method}"]
        ).all():
            raise RuntimeError(
                f"Non-finite score: {family}, {method}."
            )
    return output


def freeze_thresholds(
    cfg: Config,
    family_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    loaded = {}
    diagnostics_rows = []

    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            loaded[family] = {
                method: data[f"score_{method}"].copy()
                for method in cfg.methods
            }
            hinge_error = (
                data["hinge_onset"].astype(np.int32)
                - data["reference_onset"].astype(np.int32)
            )
            permuted_error = (
                data["permuted_onset"].astype(np.int32)
                - data["reference_onset"].astype(np.int32)
            )
            diagnostics_rows.append(
                {
                    "family": family,
                    "n": len(hinge_error),
                    "hinge_onset_mean": float(
                        np.mean(data["hinge_onset"])
                    ),
                    "permuted_onset_mean": float(
                        np.mean(data["permuted_onset"])
                    ),
                    "same_onset_multiset": bool(
                        np.array_equal(
                            np.sort(data["hinge_onset"]),
                            np.sort(data["permuted_onset"]),
                        )
                    ),
                    "fixed_point_count": int(
                        np.sum(
                            data["permutation"]
                            == (
                                np.arange(
                                    len(data["permutation"])
                                )
                                % cfg.calibration_batch_size
                            )
                        )
                    ),
                    "hinge_error_median": float(
                        np.median(hinge_error)
                    ),
                    "permuted_error_median": float(
                        np.median(permuted_error)
                    ),
                    "hinge_absolute_error_median": float(
                        np.median(np.abs(hinge_error))
                    ),
                    "permuted_absolute_error_median": float(
                        np.median(np.abs(permuted_error))
                    ),
                    "exact_energy_mean": float(
                        np.mean(data["exact_energy_retention"])
                    ),
                    "hinge_energy_mean": float(
                        np.mean(data["hinge_energy_retention"])
                    ),
                    "permuted_energy_mean": float(
                        np.mean(data["permuted_energy_retention"])
                    ),
                    "hinge_template_degenerate_fraction": float(
                        np.mean(
                            data["hinge_template_degenerate"]
                        )
                    ),
                    "permuted_template_degenerate_fraction": float(
                        np.mean(
                            data[
                                "permuted_template_degenerate"
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
            alerts = int(np.sum(values >= threshold))
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
                    "family_specific_threshold": specific[family],
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
        pd.DataFrame(diagnostics_rows),
    )


def _onset_metrics(
    errors: np.ndarray,
    alerts: np.ndarray,
    method: str,
    replication: int,
    cfg: Config,
) -> dict:
    errors = np.asarray(errors, dtype=np.int32)
    alerts = np.asarray(alerts, dtype=bool)
    selected = errors[alerts]
    selected_n = len(selected)
    selected_good = int(
        np.sum(
            (selected >= cfg.onset_error_low)
            & (selected <= cfg.onset_error_high)
        )
    )
    all_good = int(
        np.sum(
            (errors >= cfg.onset_error_low)
            & (errors <= cfg.onset_error_high)
        )
    )
    return {
        "replication": replication,
        "method": method,
        "alert_n": selected_n,
        "alert_in_envelope": selected_good,
        "alert_accuracy": (
            selected_good / selected_n
            if selected_n > 0
            else 0.0
        ),
        "alert_accuracy_lower_one_sided_95": (
            m32.m22.m5.clopper_pearson_lower(
                selected_good,
                selected_n,
            )
            if selected_n > 0
            else 0.0
        ),
        "all_positive_n": len(errors),
        "all_positive_in_envelope": all_good,
        "all_positive_accuracy": (
            all_good / len(errors)
        ),
        "alert_median_error": (
            float(np.median(selected))
            if selected_n > 0
            else np.nan
        ),
        "alert_median_absolute_error": (
            float(np.median(np.abs(selected)))
            if selected_n > 0
            else np.nan
        ),
        "all_median_error": float(np.median(errors)),
        "all_median_absolute_error": float(
            np.median(np.abs(errors))
        ),
        "alert_early_below_minus2": int(
            np.sum(selected < cfg.onset_error_low)
        ),
        "alert_late_above_plus1": int(
            np.sum(selected > cfg.onset_error_high)
        ),
    }


def evaluate_holdout(
    cfg: Config,
    seed_record: dict,
    thresholds: dict[str, float],
) -> dict:
    analysis = cfg.analysis_config()
    core = analysis.core_config(seed_record)
    curve_batches = np.random.SeedSequence(
        seed_record["seeds"]["holdout"]
    ).spawn(cfg.holdout_batches)
    permutation_batches = np.random.SeedSequence(
        seed_record["permutation_seed"]
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
            family: 0 for family in NEGATIVE_FAMILIES
        }
        for method in cfg.methods
    }
    negative_ns = {
        method: {
            family: 0 for family in NEGATIVE_FAMILIES
        }
        for method in cfg.methods
    }

    hinge_errors = {
        stratum: [] for stratum in POSITIVE_STRATA
    }
    permuted_errors = {
        stratum: [] for stratum in POSITIVE_STRATA
    }
    diagnostic_rows = []

    for batch, (curve_sequence, permutation_sequence) in enumerate(
        zip(curve_batches, permutation_batches)
    ):
        curve_children = curve_sequence.spawn(
            len(POSITIVE_STRATA)
            + len(NEGATIVE_FAMILIES)
        )
        permutation_children = permutation_sequence.spawn(
            len(POSITIVE_STRATA)
            + len(NEGATIVE_FAMILIES)
        )
        curve_rngs = [
            np.random.default_rng(child)
            for child in curve_children
        ]
        permutation_rngs = [
            np.random.default_rng(child)
            for child in permutation_children
        ]

        for stratum_index, stratum in enumerate(
            POSITIVE_STRATA
        ):
            shape, context = stratum.split("__")
            panel = m32.m22.m9.generate_positive_panel(
                shape,
                context,
                cfg.holdout_positive_per_stratum_per_batch,
                curve_rngs[stratum_index],
                core,
            )
            scores, diagnostics = evaluate_positive_panel(
                panel,
                permutation_rngs[stratum_index],
                cfg,
                core,
            )

            for method in cfg.methods:
                values = scores[method]
                hits = values >= thresholds[method]
                positive_hits[method][stratum].append(hits)
                positive_batch_counts[
                    method
                ][stratum][batch] += int(hits.sum())
                positive_batch_ns[
                    method
                ][stratum][batch] += len(hits)
                positive_score_parts[method].append(
                    values.astype(np.float32)
                )

            hinge_errors[stratum].append(
                diagnostics["hinge_error"].astype(np.int16)
            )
            permuted_errors[stratum].append(
                diagnostics["permuted_error"].astype(np.int16)
            )
            diagnostic_rows.append(
                {
                    "replication": seed_record["replication"],
                    "population": "positive",
                    "group": stratum,
                    "n": len(diagnostics["hinge_error"]),
                    "fixed_points": int(
                        np.sum(
                            diagnostics["permutation"]
                            == np.arange(
                                len(diagnostics["permutation"])
                            )
                        )
                    ),
                    "same_onset_multiset": bool(
                        np.array_equal(
                            np.sort(diagnostics["hinge_onset"]),
                            np.sort(diagnostics["permuted_onset"]),
                        )
                    ),
                    "exact_energy_sum": float(
                        np.sum(
                            diagnostics[
                                "exact_energy_retention"
                            ]
                        )
                    ),
                    "hinge_energy_sum": float(
                        np.sum(
                            diagnostics[
                                "hinge_energy_retention"
                            ]
                        )
                    ),
                    "permuted_energy_sum": float(
                        np.sum(
                            diagnostics[
                                "permuted_energy_retention"
                            ]
                        )
                    ),
                    "hinge_template_degenerate": int(
                        np.sum(
                            diagnostics[
                                "hinge_template_degenerate"
                            ]
                        )
                    ),
                    "permuted_template_degenerate": int(
                        np.sum(
                            diagnostics[
                                "permuted_template_degenerate"
                            ]
                        )
                    ),
                }
            )

        for family_index, family in enumerate(
            NEGATIVE_FAMILIES,
            start=len(POSITIVE_STRATA),
        ):
            scores, diagnostics = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                curve_rngs[family_index],
                permutation_rngs[family_index],
                cfg,
                core,
            )
            for method in cfg.methods:
                values = scores[method]
                alerts = values >= thresholds[method]
                negative_counts[method][family] += int(
                    alerts.sum()
                )
                negative_ns[method][family] += len(alerts)
                negative_score_parts[method].append(
                    values.astype(np.float32)
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
        stratum_rows.extend(method_strata)
        negative_rows.extend(method_negative)
        batch_rows.extend(method_batches)

    pair_rows = []
    total_counts = np.zeros(4, dtype=np.int64)
    for stratum_index, stratum in enumerate(
        POSITIVE_STRATA
    ):
        hinge_hits = np.concatenate(
            positive_hits[
                "hinge_reference_projected8"
            ][stratum]
        )
        permuted_hits = np.concatenate(
            positive_hits[
                "permuted_hinge_reference_projected8"
            ][stratum]
        )
        codes = (
            permuted_hits.astype(np.int8) * 2
            + hinge_hits.astype(np.int8)
        )
        counts = np.bincount(codes, minlength=4)
        total_counts += counts
        pair_rows.append(
            {
                "replication": seed_record["replication"],
                "stratum_index": stratum_index,
                "stratum": stratum,
                "neither": int(counts[0]),
                "hinge_only": int(counts[1]),
                "permuted_only": int(counts[2]),
                "both": int(counts[3]),
                "n": int(counts.sum()),
            }
        )

    all_hinge_errors = np.concatenate(
        [
            np.concatenate(hinge_errors[stratum])
            for stratum in POSITIVE_STRATA
        ]
    )
    all_permuted_errors = np.concatenate(
        [
            np.concatenate(permuted_errors[stratum])
            for stratum in POSITIVE_STRATA
        ]
    )
    hinge_alerts = np.concatenate(
        [
            np.concatenate(
                positive_hits[
                    "hinge_reference_projected8"
                ][stratum]
            )
            for stratum in POSITIVE_STRATA
        ]
    )
    permuted_alerts = np.concatenate(
        [
            np.concatenate(
                positive_hits[
                    "permuted_hinge_reference_projected8"
                ][stratum]
            )
            for stratum in POSITIVE_STRATA
        ]
    )
    onset_rows = [
        _onset_metrics(
            all_hinge_errors,
            hinge_alerts,
            "hinge_reference_projected8",
            seed_record["replication"],
            cfg,
        ),
        _onset_metrics(
            all_permuted_errors,
            permuted_alerts,
            "permuted_hinge_reference_projected8",
            seed_record["replication"],
            cfg,
        ),
    ]

    method_frame = pd.DataFrame(method_rows).set_index("method")
    hinge_recall = float(
        method_frame.loc[
            "hinge_reference_projected8",
            "recall_point",
        ]
    )
    permuted_recall = float(
        method_frame.loc[
            "permuted_hinge_reference_projected8",
            "recall_point",
        ]
    )
    paired_summary = {
        "replication": seed_record["replication"],
        "hinge_recall": hinge_recall,
        "permuted_recall": permuted_recall,
        "hinge_minus_permuted": (
            hinge_recall - permuted_recall
        ),
        "neither": int(total_counts[0]),
        "hinge_only": int(total_counts[1]),
        "permuted_only": int(total_counts[2]),
        "both": int(total_counts[3]),
        "positive_score_correlation": float(
            np.corrcoef(
                positive_scores_all[
                    "hinge_reference_projected8"
                ],
                positive_scores_all[
                    "permuted_hinge_reference_projected8"
                ],
            )[0, 1]
        ),
        "negative_score_correlation": float(
            np.corrcoef(
                negative_scores_all[
                    "hinge_reference_projected8"
                ],
                negative_scores_all[
                    "permuted_hinge_reference_projected8"
                ],
            )[0, 1]
        ),
    }

    return {
        "method_summary": pd.DataFrame(method_rows),
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
        "onset_summary": pd.DataFrame(onset_rows),
        "pair_counts": pd.DataFrame(pair_rows),
        "paired_summary": pd.DataFrame([paired_summary]),
        "projection_diagnostics": pd.DataFrame(
            diagnostic_rows
        ),
    }


def _method_bootstrap(
    cfg: Config,
    method: str,
    stratum_summary: pd.DataFrame,
    seed: int,
) -> np.ndarray:
    return m32._hierarchical_method_bootstrap(
        cfg,
        method,
        stratum_summary,
        seed,
    )


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    onset_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    method_details = {}
    method_bootstrap_frames = []
    sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(len(cfg.methods))

    for method_index, method in enumerate(cfg.methods):
        rep = method_summary[
            method_summary.method == method
        ].sort_values("replication")
        bootstrap = _method_bootstrap(
            cfg,
            method,
            stratum_summary,
            _integer_seed(sequences[method_index]),
        )
        point = float(rep.recall_point.mean())
        lower = float(np.quantile(bootstrap, 0.05))
        upper = float(np.quantile(bootstrap, 0.95))
        pass_count = int(rep["pass"].sum())
        fpr_pass_count = int(rep.fpr_pass.sum())
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
            pass_count >= cfg.minimum_holdout_passes
            and lower
            >= cfg.minimum_global_recall_lower_one_sided_95
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
            "average_precision_mean": float(
                rep.average_precision.mean()
            ),
        }
        method_bootstrap_frames.append(
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
            int(row.hinge_only),
            int(row.permuted_only),
            int(row.both),
        ]

    association_bootstrap = (
        m32.m30.hierarchical_paired_bootstrap(
            pair_array,
            cfg.bootstrap_replicates,
            cfg.paired_difference_bootstrap_seed,
        )
    )
    hinge = method_details[
        "hinge_reference_projected8"
    ]
    permuted = method_details[
        "permuted_hinge_reference_projected8"
    ]
    exact = method_details[
        "exact_reference_projected8"
    ]
    delta_point = (
        hinge["aggregate_recall_point"]
        - permuted["aggregate_recall_point"]
    )
    delta_lower = float(
        np.quantile(association_bootstrap, 0.05)
    )
    delta_upper = float(
        np.quantile(association_bootstrap, 0.95)
    )

    pivot = method_summary.pivot(
        index="replication",
        columns="method",
        values="recall_point",
    )
    holdout_deltas = (
        pivot["hinge_reference_projected8"]
        - pivot["permuted_hinge_reference_projected8"]
    )
    holdouts_with_material_delta = int(
        np.sum(
            holdout_deltas
            >= cfg.minimum_holdout_association_delta
        )
    )
    association_pass = bool(
        delta_lower >= cfg.association_margin
        and holdouts_with_material_delta
        >= cfg.minimum_holdouts_with_association_delta
    )
    equivalence_pass = bool(
        delta_lower >= -cfg.association_margin
        and delta_upper <= cfg.association_margin
    )

    controls_valid = bool(
        exact["operational_pass"]
        and hinge["operational_pass"]
    )

    if not controls_valid:
        verdict = "INVALID_M33_CONTROL_FAILURE"
    elif association_pass:
        verdict = "PASS_CURVE_SPECIFIC_ONSET_INFORMATION"
    elif (
        permuted["operational_pass"]
        and equivalence_pass
    ):
        verdict = "ONSET_DISTRIBUTION_ONLY"
    elif delta_upper <= 0.0:
        verdict = "STRONG_FAIL_HINGE_ASSOCIATION"
    else:
        verdict = "INCONCLUSIVE_HINGE_ASSOCIATION"

    onset_aggregate = {}
    for method in (
        "hinge_reference_projected8",
        "permuted_hinge_reference_projected8",
    ):
        subset = onset_summary[
            onset_summary.method == method
        ]
        alert_n = int(subset.alert_n.sum())
        alert_good = int(
            subset.alert_in_envelope.sum()
        )
        all_n = int(subset.all_positive_n.sum())
        all_good = int(
            subset.all_positive_in_envelope.sum()
        )
        onset_aggregate[method] = {
            "alert_n": alert_n,
            "alert_in_envelope": alert_good,
            "alert_accuracy": (
                alert_good / alert_n
                if alert_n > 0
                else 0.0
            ),
            "all_positive_n": all_n,
            "all_positive_in_envelope": all_good,
            "all_positive_accuracy": all_good / all_n,
            "alert_early_below_minus2": int(
                subset.alert_early_below_minus2.sum()
            ),
            "alert_late_above_plus1": int(
                subset.alert_late_above_plus1.sum()
            ),
        }

    prediction = {
        "exact_recall_in_range": bool(
            cfg.prediction_exact_range[0]
            <= exact["aggregate_recall_point"]
            <= cfg.prediction_exact_range[1]
        ),
        "hinge_recall_in_range": bool(
            cfg.prediction_hinge_range[0]
            <= hinge["aggregate_recall_point"]
            <= cfg.prediction_hinge_range[1]
        ),
        "permuted_recall_in_range": bool(
            cfg.prediction_permuted_range[0]
            <= permuted["aggregate_recall_point"]
            <= cfg.prediction_permuted_range[1]
        ),
        "association_delta_in_range": bool(
            cfg.prediction_association_delta_range[0]
            <= delta_point
            <= cfg.prediction_association_delta_range[1]
        ),
        "controls_valid": controls_valid,
        "permuted_operational": bool(
            permuted["operational_pass"]
        ),
        "permuted_pass_count_in_range": bool(
            cfg.prediction_permuted_pass_low
            <= permuted["holdout_pass_count"]
            <= cfg.prediction_permuted_pass_high
        ),
        "equivalence_confirmed": equivalence_pass,
        "permuted_onset_accuracy_not_higher": bool(
            onset_aggregate[
                "permuted_hinge_reference_projected8"
            ]["alert_accuracy"]
            <= onset_aggregate[
                "hinge_reference_projected8"
            ]["alert_accuracy"]
        ),
        "overall_verdict_confirmed": bool(
            verdict == "ONSET_DISTRIBUTION_ONLY"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": verdict,
        "controls_valid": controls_valid,
        "method_details": method_details,
        "association_test": {
            "hinge_minus_permuted_point": delta_point,
            "hinge_minus_permuted_lower_one_sided_95": (
                delta_lower
            ),
            "hinge_minus_permuted_upper_one_sided_95": (
                delta_upper
            ),
            "holdout_deltas": {
                str(int(index)): float(value)
                for index, value in holdout_deltas.items()
            },
            "holdouts_with_delta_at_least_0_015": (
                holdouts_with_material_delta
            ),
            "association_pass": association_pass,
            "equivalence_margin": cfg.association_margin,
            "equivalence_pass": equivalence_pass,
        },
        "onset_localization": onset_aggregate,
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(
            method_bootstrap_frames,
            ignore_index=True,
        ),
        "association_bootstrap": association_bootstrap,
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
        "m32_dependency_sha256": sha256_file(
            ROOT / "arara_m32_dependency.py"
        ),
        "m25_dependency_sha256": sha256_file(
            ROOT / "arara_m25_dependency.py"
        ),
        "m30_dependency_sha256": sha256_file(
            ROOT / "arara_m30_dependency.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
