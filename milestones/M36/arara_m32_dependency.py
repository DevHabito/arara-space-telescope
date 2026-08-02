
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
import arara_m24_dependency as m24
import arara_m25_dependency as m25
import arara_m30_dependency as m30
import arara_m31_dependency as m31


POSITIVE_STRATA = m22.POSITIVE_STRATA
NEGATIVE_FAMILIES = m22.NEGATIVE_FAMILIES
METHODS = (
    "exact_reference_projected8",
    "split_onset_reference_projected8",
)


@dataclass(frozen=True)
class Config(m31.Config):
    version: str = "32.0"
    methods: tuple[str, ...] = METHODS

    candidate_onset_low: int = 70
    candidate_onset_high: int = 120
    selection_start: int = 50
    guard_length: int = 1
    confirmation_length: int = 8

    onset_error_low: int = -2
    onset_error_high: int = 1
    minimum_onset_accuracy_lower_one_sided_95: float = 0.90
    minimum_onset_pass_holdouts: int = 8

    calibration_seed: int = 2026082701
    holdout_root_seed: int = 2026082702
    aggregate_bootstrap_root_seed: int = 2026082703
    paired_difference_bootstrap_seed: int = 2026082704

    prediction_exact_range: tuple[float, float] = (0.75, 0.85)
    prediction_candidate_range: tuple[float, float] = (0.45, 0.70)
    prediction_delta_range: tuple[float, float] = (-0.35, -0.10)
    prediction_onset_accuracy_range: tuple[float, float] = (0.20, 0.45)
    prediction_detection_pass_low: int = 3
    prediction_detection_pass_high: int = 8

    def hinge_config(self) -> m24.Config:
        return m24.Config(
            candidate_onset_low=self.candidate_onset_low,
            candidate_onset_high=self.candidate_onset_high,
            hinge_interval_start=self.selection_start,
        )


build_seed_plan = m30.build_seed_plan
calibration_core = m30.calibration_core
sha256_file = m30.sha256_file


def estimate_onset_split(
    residual: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    return m25.estimate_onset_split(
        residual,
        endpoint,
        cfg,
    )


def process_shifted_template(
    raw_template: np.ndarray,
    reference_onset: np.ndarray,
    estimated_onset: np.ndarray,
    params: dict,
) -> np.ndarray:
    offsets = (
        np.asarray(estimated_onset, dtype=np.int32)
        - np.asarray(reference_onset, dtype=np.int32)
    )
    shifted = m24.shift_rows(
        raw_template,
        offsets,
    )
    return m22.apply_signal_operator(
        shifted,
        params,
    )


def paired_reference_scores(
    residual: np.ndarray,
    exact_processed_template: np.ndarray,
    estimated_processed_template: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    exact_score, exact_diag = (
        m30.reference_projected_score(
            residual,
            exact_processed_template,
            processed_reference,
            endpoint,
            cfg,
        )
    )
    estimated_score, estimated_diag = (
        m30.reference_projected_score(
            residual,
            estimated_processed_template,
            processed_reference,
            endpoint,
            cfg,
        )
    )
    return (
        {
            "exact_reference_projected8": exact_score,
            "split_onset_reference_projected8": estimated_score,
        },
        {
            "exact_energy_retention": exact_diag[
                "energy_retention"
            ],
            "estimated_energy_retention": estimated_diag[
                "energy_retention"
            ],
            "exact_template_degenerate": exact_diag[
                "template_degenerate"
            ],
            "estimated_template_degenerate": estimated_diag[
                "template_degenerate"
            ],
            "reference_degenerate": exact_diag[
                "reference_degenerate"
            ],
        },
    )


def evaluate_positive_panel(
    panel: m22.m9.PositivePanel,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[Dict[str, np.ndarray], np.ndarray, np.ndarray, dict]:
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
    ) = m30.m29.sbw_with_reference_nuisance(
        observed,
        raw_signal,
        core.data_config(),
    )

    estimated_onset, hinge_score = estimate_onset_split(
        residual,
        panel.t100,
        cfg,
    )
    estimated_processed_signal = process_shifted_template(
        raw_signal,
        panel.onset,
        estimated_onset,
        params,
    )
    scores, diagnostics = paired_reference_scores(
        residual,
        exact_processed_signal,
        estimated_processed_signal,
        processed_reference,
        panel.t100,
        cfg,
    )
    error = (
        estimated_onset.astype(np.int32)
        - panel.onset.astype(np.int32)
    )
    diagnostics["hinge_score"] = hinge_score
    return scores, estimated_onset, error, diagnostics


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[Dict[str, np.ndarray], np.ndarray, np.ndarray, np.ndarray, dict]:
    data_cfg = core.data_config()
    data = m22.m2.generate_negative_family(
        family,
        n,
        rng,
        data_cfg,
    )
    virtual_signal, reference_onset, _, _ = (
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
        exact_processed_template,
        processed_reference,
        params,
    ) = m30.m29.sbw_with_reference_nuisance(
        data.y,
        virtual_signal,
        data_cfg,
    )
    estimated_onset, hinge_score = estimate_onset_split(
        residual,
        endpoint,
        cfg,
    )
    estimated_processed_template = process_shifted_template(
        virtual_signal,
        reference_onset,
        estimated_onset,
        params,
    )
    scores, diagnostics = paired_reference_scores(
        residual,
        exact_processed_template,
        estimated_processed_template,
        processed_reference,
        endpoint,
        cfg,
    )
    diagnostics["hinge_score"] = hinge_score
    return (
        scores,
        reference_onset,
        estimated_onset,
        endpoint,
        diagnostics,
    )


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> dict:
    seed = seed_plan["calibration"][family]["integer_seed"]
    rng = np.random.default_rng(seed)
    core = calibration_core(cfg)

    score_parts = {
        method: [] for method in cfg.methods
    }
    reference_onset_parts = []
    estimated_onset_parts = []
    endpoint_parts = []
    diagnostic_parts = {
        "exact_energy_retention": [],
        "estimated_energy_retention": [],
        "exact_template_degenerate": [],
        "estimated_template_degenerate": [],
        "reference_degenerate": [],
    }

    remaining = cfg.calibration_negatives_per_family
    while remaining > 0:
        n = min(
            cfg.calibration_batch_size,
            remaining,
        )
        (
            scores,
            reference_onset,
            estimated_onset,
            endpoint,
            diagnostics,
        ) = evaluate_negative_family(
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
        reference_onset_parts.append(
            np.asarray(reference_onset, dtype=np.int16)
        )
        estimated_onset_parts.append(
            np.asarray(estimated_onset, dtype=np.int16)
        )
        endpoint_parts.append(
            np.asarray(endpoint, dtype=np.int16)
        )
        for key in diagnostic_parts:
            dtype = (
                np.float32
                if "energy" in key
                else np.int8
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
    output["reference_onset"] = np.concatenate(
        reference_onset_parts
    )
    output["estimated_onset"] = np.concatenate(
        estimated_onset_parts
    )
    output["endpoint"] = np.concatenate(
        endpoint_parts
    )
    for key, parts in diagnostic_parts.items():
        output[key] = np.concatenate(parts)

    for key, values in output.items():
        if len(values) != cfg.calibration_negatives_per_family:
            raise RuntimeError(
                f"Wrong calibration size: {family}, {key}."
            )
    for method in cfg.methods:
        if not np.isfinite(output[f"score_{method}"]).all():
            raise RuntimeError(
                f"Non-finite score: {family}, {method}."
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
                method: data[f"score_{method}"].copy()
                for method in cfg.methods
            }
            error = (
                data["estimated_onset"].astype(np.int32)
                - data["reference_onset"].astype(np.int32)
            )
            diagnostic_rows.append(
                {
                    "family": family,
                    "n": len(error),
                    "estimated_onset_mean": float(
                        np.mean(data["estimated_onset"])
                    ),
                    "onset_error_median": float(
                        np.median(error)
                    ),
                    "onset_absolute_error_median": float(
                        np.median(np.abs(error))
                    ),
                    "exact_energy_retention_mean": float(
                        np.mean(data["exact_energy_retention"])
                    ),
                    "estimated_energy_retention_mean": float(
                        np.mean(
                            data["estimated_energy_retention"]
                        )
                    ),
                    "exact_template_degenerate_fraction": float(
                        np.mean(
                            data["exact_template_degenerate"]
                        )
                    ),
                    "estimated_template_degenerate_fraction": float(
                        np.mean(
                            data["estimated_template_degenerate"]
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
        pd.DataFrame(diagnostic_rows),
    )


def _method_holdout_metrics(
    method: str,
    positive_hits: dict,
    positive_batch_counts: dict,
    positive_batch_ns: dict,
    negative_counts: dict,
    negative_ns: dict,
    positive_scores: np.ndarray,
    negative_scores: np.ndarray,
    threshold: float,
    seed_record: dict,
    cfg: Config,
) -> tuple[dict, list[dict], list[dict], list[dict]]:
    negative_rows = []
    fpr_pass = True
    maximum_fpr_upper = 0.0
    for family in NEGATIVE_FAMILIES:
        x = negative_counts[method][family]
        n = negative_ns[method][family]
        upper = m22.m2.clopper_pearson_upper(x, n)
        maximum_fpr_upper = max(
            maximum_fpr_upper,
            upper,
        )
        if upper > cfg.holdout_fpr_upper_limit:
            fpr_pass = False
        negative_rows.append(
            {
                "replication": seed_record["replication"],
                "method": method,
                "family": family,
                "alerts": x,
                "n": n,
                "rate": x / n,
                "fpr_upper_one_sided_95": upper,
            }
        )

    stratum_rows = []
    hits_by_stratum = {}
    good_strata = 0
    stratum_rates = []

    for stratum in POSITIVE_STRATA:
        hits = np.concatenate(
            positive_hits[method][stratum]
        )
        x = int(hits.sum())
        n = len(hits)
        lower = m22.m5.clopper_pearson_lower(x, n)
        good_strata += int(
            lower
            >= cfg.minimum_stratum_recall_lower_one_sided_95
        )
        hits_by_stratum[stratum] = hits
        stratum_rates.append(x / n)
        stratum_rows.append(
            {
                "replication": seed_record["replication"],
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
        + cfg.methods.index(method),
    )
    recall_point = float(np.mean(stratum_rates))
    recall_lower = float(np.quantile(bootstrap, 0.05))
    recall_upper = float(np.quantile(bootstrap, 0.95))

    batch_rows = []
    good_batches = 0
    for batch in range(cfg.holdout_batches):
        hits = sum(
            positive_batch_counts[method][stratum][batch]
            for stratum in POSITIVE_STRATA
        )
        n = sum(
            positive_batch_ns[method][stratum][batch]
            for stratum in POSITIVE_STRATA
        )
        recall = hits / n
        good_batches += int(
            recall >= cfg.batch_recall_threshold
        )
        batch_rows.append(
            {
                "replication": seed_record["replication"],
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
        and good_strata >= cfg.minimum_good_strata
        and good_batches >= cfg.minimum_good_batches
    )

    labels = np.concatenate(
        [
            np.ones(len(positive_scores), dtype=int),
            np.zeros(len(negative_scores), dtype=int),
        ]
    )
    values = np.concatenate(
        [positive_scores, negative_scores]
    )
    summary = {
        "replication": seed_record["replication"],
        "method": method,
        "threshold": threshold,
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
            roc_auc_score(labels, values)
        ),
        "average_precision": float(
            average_precision_score(labels, values)
        ),
    }
    return (
        summary,
        stratum_rows,
        negative_rows,
        batch_rows,
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

    onset_errors_all = {
        stratum: [] for stratum in POSITIVE_STRATA
    }
    onset_errors_detected = {
        stratum: [] for stratum in POSITIVE_STRATA
    }
    diagnostic_rows = []

    for batch, sequence in enumerate(batch_sequences):
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
            (
                scores,
                estimated_onset,
                error,
                diagnostics,
            ) = evaluate_positive_panel(
                panel,
                cfg,
                core,
            )

            candidate_hits = None
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
                if (
                    method
                    == "split_onset_reference_projected8"
                ):
                    candidate_hits = hits

            onset_errors_all[stratum].append(
                error.astype(np.int16)
            )
            onset_errors_detected[stratum].append(
                error[candidate_hits].astype(np.int16)
            )
            diagnostic_rows.append(
                {
                    "replication": seed_record["replication"],
                    "population": "positive",
                    "group": stratum,
                    "n": len(error),
                    "exact_energy_sum": float(
                        np.sum(
                            diagnostics[
                                "exact_energy_retention"
                            ]
                        )
                    ),
                    "estimated_energy_sum": float(
                        np.sum(
                            diagnostics[
                                "estimated_energy_retention"
                            ]
                        )
                    ),
                    "exact_template_degenerate": int(
                        np.sum(
                            diagnostics[
                                "exact_template_degenerate"
                            ]
                        )
                    ),
                    "estimated_template_degenerate": int(
                        np.sum(
                            diagnostics[
                                "estimated_template_degenerate"
                            ]
                        )
                    ),
                }
            )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[len(POSITIVE_STRATA):],
        ):
            (
                scores,
                reference_onset,
                estimated_onset,
                endpoint,
                diagnostics,
            ) = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
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

    for method in cfg.methods:
        (
            summary,
            method_strata,
            method_negative,
            method_batches,
        ) = _method_holdout_metrics(
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
    total_pair_counts = np.zeros(4, dtype=np.int64)
    for stratum_index, stratum in enumerate(
        POSITIVE_STRATA
    ):
        exact_hits = np.concatenate(
            positive_hits[
                "exact_reference_projected8"
            ][stratum]
        )
        candidate_hits = np.concatenate(
            positive_hits[
                "split_onset_reference_projected8"
            ][stratum]
        )
        codes = (
            exact_hits.astype(np.int8) * 2
            + candidate_hits.astype(np.int8)
        )
        counts = np.bincount(codes, minlength=4)
        total_pair_counts += counts
        pair_rows.append(
            {
                "replication": seed_record["replication"],
                "stratum_index": stratum_index,
                "stratum": stratum,
                "neither": int(counts[0]),
                "candidate_only": int(counts[1]),
                "exact_only": int(counts[2]),
                "both": int(counts[3]),
                "n": int(counts.sum()),
            }
        )

    all_errors = np.concatenate(
        [
            np.concatenate(onset_errors_all[stratum])
            for stratum in POSITIVE_STRATA
        ]
    )
    detected_errors = np.concatenate(
        [
            np.concatenate(onset_errors_detected[stratum])
            for stratum in POSITIVE_STRATA
        ]
    )
    detected_good = int(
        np.sum(
            (detected_errors >= cfg.onset_error_low)
            & (detected_errors <= cfg.onset_error_high)
        )
    )
    all_good = int(
        np.sum(
            (all_errors >= cfg.onset_error_low)
            & (all_errors <= cfg.onset_error_high)
        )
    )
    detected_n = len(detected_errors)
    all_n = len(all_errors)

    detected_lower = (
        m22.m5.clopper_pearson_lower(
            detected_good,
            detected_n,
        )
        if detected_n > 0
        else 0.0
    )
    detected_upper = (
        m22.m2.clopper_pearson_upper(
            detected_good,
            detected_n,
        )
        if detected_n > 0
        else 1.0
    )
    all_lower = m22.m5.clopper_pearson_lower(
        all_good,
        all_n,
    )
    all_upper = m22.m2.clopper_pearson_upper(
        all_good,
        all_n,
    )

    onset_summary = {
        "replication": seed_record["replication"],
        "detected_n": detected_n,
        "detected_in_envelope": detected_good,
        "detected_accuracy": (
            detected_good / detected_n
            if detected_n > 0
            else 0.0
        ),
        "detected_accuracy_lower_one_sided_95": (
            detected_lower
        ),
        "detected_accuracy_upper_one_sided_95": (
            detected_upper
        ),
        "all_positive_n": all_n,
        "all_positive_in_envelope": all_good,
        "all_positive_accuracy": all_good / all_n,
        "all_positive_accuracy_lower_one_sided_95": (
            all_lower
        ),
        "all_positive_accuracy_upper_one_sided_95": (
            all_upper
        ),
        "detected_early_below_minus2": int(
            np.sum(detected_errors < cfg.onset_error_low)
        ),
        "detected_late_above_plus1": int(
            np.sum(detected_errors > cfg.onset_error_high)
        ),
        "all_early_below_minus2": int(
            np.sum(all_errors < cfg.onset_error_low)
        ),
        "all_late_above_plus1": int(
            np.sum(all_errors > cfg.onset_error_high)
        ),
        "detected_median_error": (
            float(np.median(detected_errors))
            if detected_n > 0
            else np.nan
        ),
        "detected_median_absolute_error": (
            float(np.median(np.abs(detected_errors)))
            if detected_n > 0
            else np.nan
        ),
        "all_median_error": float(np.median(all_errors)),
        "all_median_absolute_error": float(
            np.median(np.abs(all_errors))
        ),
        "onset_pass": bool(
            detected_lower
            >= cfg.minimum_onset_accuracy_lower_one_sided_95
        ),
    }

    exact_point = next(
        row["recall_point"]
        for row in method_rows
        if row["method"]
        == "exact_reference_projected8"
    )
    candidate_point = next(
        row["recall_point"]
        for row in method_rows
        if row["method"]
        == "split_onset_reference_projected8"
    )
    paired_summary = {
        "replication": seed_record["replication"],
        "exact_recall_point": exact_point,
        "candidate_recall_point": candidate_point,
        "delta_point": candidate_point - exact_point,
        "neither": int(total_pair_counts[0]),
        "candidate_only": int(total_pair_counts[1]),
        "exact_only": int(total_pair_counts[2]),
        "both": int(total_pair_counts[3]),
        "positive_score_correlation": float(
            np.corrcoef(
                positive_scores_all[
                    "exact_reference_projected8"
                ],
                positive_scores_all[
                    "split_onset_reference_projected8"
                ],
            )[0, 1]
        ),
        "negative_score_correlation": float(
            np.corrcoef(
                negative_scores_all[
                    "exact_reference_projected8"
                ],
                negative_scores_all[
                    "split_onset_reference_projected8"
                ],
            )[0, 1]
        ),
    }

    return {
        "method_summary": pd.DataFrame(method_rows),
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
        "onset_summary": pd.DataFrame([onset_summary]),
        "pair_counts": pd.DataFrame(pair_rows),
        "paired_summary": pd.DataFrame([paired_summary]),
        "projection_diagnostics": pd.DataFrame(
            diagnostic_rows
        ),
    }


def _hierarchical_method_bootstrap(
    cfg: Config,
    method: str,
    stratum_summary: pd.DataFrame,
    seed: int,
) -> np.ndarray:
    counts = []
    ns = []
    for holdout in range(cfg.holdout_count):
        subset = stratum_summary[
            (
                stratum_summary.method == method
            )
            & (
                stratum_summary.replication == holdout
            )
        ].set_index("stratum")
        counts.append(
            [
                int(subset.loc[stratum, "hits"])
                for stratum in POSITIVE_STRATA
            ]
        )
        ns.append(
            [
                int(subset.loc[stratum, "n"])
                for stratum in POSITIVE_STRATA
            ]
        )
    return m22.m15.hierarchical_bootstrap(
        np.asarray(counts),
        np.asarray(ns),
        cfg.bootstrap_replicates,
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
    bootstrap_frames = []
    sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(len(cfg.methods))

    for method_index, method in enumerate(cfg.methods):
        rep = method_summary[
            method_summary.method == method
        ].sort_values("replication")
        bootstrap = _hierarchical_method_bootstrap(
            cfg,
            method,
            stratum_summary,
            int(
                sequences[method_index].generate_state(
                    1,
                    dtype=np.uint32,
                )[0]
            ),
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
            int(row.candidate_only),
            int(row.exact_only),
            int(row.both),
        ]
    delta_bootstrap = m30.hierarchical_paired_bootstrap(
        pair_array,
        cfg.bootstrap_replicates,
        cfg.paired_difference_bootstrap_seed,
    )

    exact = method_details[
        "exact_reference_projected8"
    ]
    candidate = method_details[
        "split_onset_reference_projected8"
    ]
    delta_point = (
        candidate["aggregate_recall_point"]
        - exact["aggregate_recall_point"]
    )
    delta_lower = float(
        np.quantile(delta_bootstrap, 0.05)
    )
    delta_upper = float(
        np.quantile(delta_bootstrap, 0.95)
    )

    total_detected = int(onset_summary.detected_n.sum())
    total_detected_good = int(
        onset_summary.detected_in_envelope.sum()
    )
    detected_accuracy = (
        total_detected_good / total_detected
        if total_detected > 0
        else 0.0
    )
    detected_lower = (
        m22.m5.clopper_pearson_lower(
            total_detected_good,
            total_detected,
        )
        if total_detected > 0
        else 0.0
    )
    detected_upper = (
        m22.m2.clopper_pearson_upper(
            total_detected_good,
            total_detected,
        )
        if total_detected > 0
        else 1.0
    )

    total_all = int(onset_summary.all_positive_n.sum())
    total_all_good = int(
        onset_summary.all_positive_in_envelope.sum()
    )
    all_accuracy = total_all_good / total_all
    all_lower = m22.m5.clopper_pearson_lower(
        total_all_good,
        total_all,
    )
    all_upper = m22.m2.clopper_pearson_upper(
        total_all_good,
        total_all,
    )
    onset_pass_count = int(
        onset_summary.onset_pass.sum()
    )
    onset_pass = bool(
        detected_lower
        >= cfg.minimum_onset_accuracy_lower_one_sided_95
        and onset_pass_count
        >= cfg.minimum_onset_pass_holdouts
    )

    control_valid = bool(exact["operational_pass"])

    if not control_valid:
        verdict = "INVALID_EXACT_CONTROL_FAILURE"
    elif (
        candidate["operational_pass"]
        and onset_pass
    ):
        verdict = "PASS_SPLIT_ONSET_CANDIDATE"
    elif candidate["operational_pass"]:
        verdict = "PASS_DETECTION_ONSET_UNRELIABLE"
    elif (
        candidate["holdout_pass_count"] <= 2
        or candidate[
            "aggregate_recall_upper_one_sided_95"
        ]
        <= cfg.minimum_global_recall_lower_one_sided_95
        or candidate["extreme_fpr_violation"]
    ):
        verdict = (
            "STRONG_FAIL_SPLIT_ONSET_WITH_CONFIRMED_DOWNSTREAM"
        )
    else:
        verdict = (
            "INCONCLUSIVE_SPLIT_ONSET_WITH_CONFIRMED_DOWNSTREAM"
        )

    prediction = {
        "exact_recall_in_range": bool(
            cfg.prediction_exact_range[0]
            <= exact["aggregate_recall_point"]
            <= cfg.prediction_exact_range[1]
        ),
        "candidate_recall_in_range": bool(
            cfg.prediction_candidate_range[0]
            <= candidate["aggregate_recall_point"]
            <= cfg.prediction_candidate_range[1]
        ),
        "delta_in_range": bool(
            cfg.prediction_delta_range[0]
            <= delta_point
            <= cfg.prediction_delta_range[1]
        ),
        "control_valid": control_valid,
        "both_fpr_robust": bool(
            exact["fpr_robust"]
            and candidate["fpr_robust"]
        ),
        "onset_accuracy_in_range": bool(
            cfg.prediction_onset_accuracy_range[0]
            <= detected_accuracy
            <= cfg.prediction_onset_accuracy_range[1]
        ),
        "onset_localization_failed": not onset_pass,
        "detection_pass_count_in_range": bool(
            cfg.prediction_detection_pass_low
            <= candidate["holdout_pass_count"]
            <= cfg.prediction_detection_pass_high
        ),
        "overall_verdict_confirmed": bool(
            verdict
            == "INCONCLUSIVE_SPLIT_ONSET_WITH_CONFIRMED_DOWNSTREAM"
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
            "candidate_minus_exact_point": delta_point,
            "candidate_minus_exact_lower_one_sided_95": (
                delta_lower
            ),
            "candidate_minus_exact_upper_one_sided_95": (
                delta_upper
            ),
        },
        "onset_localization": {
            "detected_n": total_detected,
            "detected_in_envelope": total_detected_good,
            "detected_accuracy": detected_accuracy,
            "detected_accuracy_lower_one_sided_95": (
                detected_lower
            ),
            "detected_accuracy_upper_one_sided_95": (
                detected_upper
            ),
            "all_positive_n": total_all,
            "all_positive_in_envelope": total_all_good,
            "all_positive_accuracy": all_accuracy,
            "all_positive_accuracy_lower_one_sided_95": (
                all_lower
            ),
            "all_positive_accuracy_upper_one_sided_95": (
                all_upper
            ),
            "holdout_pass_count": onset_pass_count,
            "localization_pass": onset_pass,
            "detected_early_below_minus2": int(
                onset_summary.detected_early_below_minus2.sum()
            ),
            "detected_late_above_plus1": int(
                onset_summary.detected_late_above_plus1.sum()
            ),
            "all_early_below_minus2": int(
                onset_summary.all_early_below_minus2.sum()
            ),
            "all_late_above_plus1": int(
                onset_summary.all_late_above_plus1.sum()
            ),
        },
        "prediction": prediction,
        "method_bootstrap_df": pd.concat(
            bootstrap_frames,
            ignore_index=True,
        ),
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
        "m25_dependency_sha256": sha256_file(
            ROOT / "arara_m25_dependency.py"
        ),
        "m24_dependency_sha256": sha256_file(
            ROOT / "arara_m24_dependency.py"
        ),
        "m31_dependency_sha256": sha256_file(
            ROOT / "arara_m31_dependency.py"
        ),
        "m30_dependency_sha256": sha256_file(
            ROOT / "arara_m30_dependency.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
