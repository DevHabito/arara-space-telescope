
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


POSITIVE_STRATA = m22.POSITIVE_STRATA
NEGATIVE_FAMILIES = m22.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "24.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50

    candidate_onset_low: int = 70
    candidate_onset_high: int = 120
    hinge_interval_start: int = 50

    calibration_seed: int = 2026081901
    holdout_root_seed: int = 2026081902
    aggregate_bootstrap_root_seed: int = 2026081903

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
    minimum_complete_holdout_passes: int = 8
    minimum_fpr_pass_holdouts: int = 9
    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55

    onset_error_low: int = -2
    onset_error_high: int = 1
    minimum_onset_accuracy_lower_ci: float = 0.90
    strong_fail_onset_accuracy_upper: float = 0.75

    bootstrap_replicates: int = 10_000

    prediction_recall_low: float = 0.48
    prediction_recall_high: float = 0.60
    prediction_accuracy_low: float = 0.25
    prediction_accuracy_high: float = 0.60
    prediction_max_complete_passes: int = 2

    @property
    def candidates(self) -> np.ndarray:
        return np.arange(
            self.candidate_onset_low,
            self.candidate_onset_high + 1,
            dtype=np.int16,
        )

    def analysis_config(self) -> m22.Config:
        return m22.Config(
            version=self.version,
            fixed_snr=self.fixed_snr,
            target_fraction=self.target_fraction,
            onset_offsets=(0,),
            replication_count=self.holdout_count,
            replication_root_seed=self.holdout_root_seed,
            aggregate_bootstrap_root_seed=(
                self.aggregate_bootstrap_root_seed
            ),
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
            minimum_replication_passes=(
                self.minimum_complete_holdout_passes
            ),
            minimum_fpr_pass_replications=(
                self.minimum_fpr_pass_holdouts
            ),
            minimum_global_recall_lower_ci=(
                self.minimum_global_recall_lower_ci
            ),
            minimum_stratum_recall_lower_ci=(
                self.minimum_stratum_recall_lower_ci
            ),
            minimum_good_strata=self.minimum_good_strata,
            minimum_good_batches=self.minimum_good_batches,
            batch_recall_threshold=self.batch_recall_threshold,
            bootstrap_replicates=self.bootstrap_replicates,
            prediction_ranges=((0, 0.0, 1.0),),
        )


def _integer_seed(sequence: np.random.SeedSequence) -> int:
    return int(
        sequence.generate_state(1, dtype=np.uint32)[0]
    )


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
            NEGATIVE_FAMILIES, calibration_children
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
                "children": {
                    label: {
                        "integer_seed": seeds[label],
                        "entropy": sequence.entropy,
                        "spawn_key": list(
                            sequence.spawn_key
                        ),
                    }
                    for label, sequence in zip(
                        labels, subchildren
                    )
                },
            }
        )
    return {
        "calibration": calibration,
        "holdouts": holdouts,
    }


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


def shift_rows(
    signal: np.ndarray,
    offsets: np.ndarray,
) -> np.ndarray:
    values = np.asarray(signal)
    offsets = np.asarray(offsets, dtype=np.int32)
    if values.ndim != 2:
        raise ValueError("signal must be 2D.")
    if offsets.shape != (values.shape[0],):
        raise ValueError("offsets shape mismatch.")

    n, t = values.shape
    destination = np.arange(t)[None, :]
    source = destination - offsets[:, None]
    valid = (source >= 0) & (source < t)
    clipped = np.clip(source, 0, t - 1)
    gathered = np.take_along_axis(
        values, clipped, axis=1
    )
    return np.where(valid, gathered, 0.0)


def estimate_onset_hinge(
    residual: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(residual, dtype=np.float64)
    endpoint = np.asarray(endpoint, dtype=np.int32)
    if y.ndim != 2:
        raise ValueError("residual must be 2D.")
    if endpoint.shape != (y.shape[0],):
        raise ValueError("endpoint shape mismatch.")

    n, t = y.shape
    candidates = cfg.candidates.astype(np.int32)
    time = np.arange(t, dtype=np.float64)
    hinge = np.maximum(
        0.0,
        time[None, :] - candidates[:, None],
    )

    interval_mask = (
        np.arange(t)[None, :]
        >= cfg.hinge_interval_start
    ) & (
        np.arange(t)[None, :]
        <= endpoint[:, None]
    )
    y_masked = np.where(interval_mask, y, 0.0)

    count = (
        endpoint - cfg.hinge_interval_start + 1
    ).astype(np.float64)
    if np.any(count < 3):
        raise ValueError("Endpoint leaves too few samples.")

    sum_y = y_masked.sum(axis=1)
    sum_y2 = np.square(y_masked).sum(axis=1)
    sum_yh = y_masked @ hinge.T

    hinge_cumsum = np.cumsum(hinge, axis=1)
    hinge2_cumsum = np.cumsum(
        np.square(hinge), axis=1
    )
    sum_h = hinge_cumsum[:, endpoint].T
    sum_h2 = hinge2_cumsum[:, endpoint].T

    covariance = (
        sum_yh
        - sum_y[:, None] * sum_h / count[:, None]
    )
    variance_y = (
        sum_y2
        - np.square(sum_y) / count
    )[:, None]
    variance_h = (
        sum_h2
        - np.square(sum_h) / count[:, None]
    )

    denominator = np.sqrt(
        np.maximum(variance_y, 0.0)
        * np.maximum(variance_h, 0.0)
    )
    correlation = np.divide(
        covariance,
        denominator,
        out=np.zeros_like(covariance),
        where=denominator > 1e-12,
    )
    correlation = np.clip(correlation, -1.0, 1.0)

    valid = (
        endpoint[:, None]
        - candidates[None, :]
        + 1
        >= 3
    )
    positive = (correlation > 0.0) & valid
    score = np.full_like(correlation, -np.inf)
    safe = positive & (
        correlation < 1.0 - 1e-15
    )
    degrees = np.broadcast_to(
        count[:, None] - 2.0,
        correlation.shape,
    )
    score[safe] = correlation[safe] * np.sqrt(
        degrees[safe]
        / (
            1.0
            - np.square(correlation[safe])
        )
    )
    score[
        positive
        & (correlation >= 1.0 - 1e-15)
    ] = np.inf

    index = np.argmax(score, axis=1)
    estimated = candidates[index].astype(np.int16)
    maximum = score[np.arange(n), index]
    return estimated, maximum


def final_score_from_estimated_onset(
    residual: np.ndarray,
    raw_template_reference: np.ndarray,
    reference_onset: np.ndarray,
    estimated_onset: np.ndarray,
    endpoint: np.ndarray,
    params: dict,
) -> np.ndarray:
    offsets = (
        np.asarray(estimated_onset, dtype=np.int32)
        - np.asarray(reference_onset, dtype=np.int32)
    )
    shifted = shift_rows(
        raw_template_reference, offsets
    )
    processed = m22.apply_signal_operator(
        shifted, params
    )
    return m22.m5.aligned_t_score(
        residual,
        processed,
        np.asarray(estimated_onset, dtype=np.int16),
        np.asarray(endpoint, dtype=np.int16),
    )


def evaluate_positive_panel(
    panel: m22.m9.PositivePanel,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    y = panel.base_y.copy()
    y[:, 0, :] += raw_signal

    residual, _, params = (
        m22.m5.sbw_with_signal_operator(
            y, raw_signal, core.data_config()
        )
    )
    estimated, hinge_score = estimate_onset_hinge(
        residual, panel.t100, cfg
    )
    final_score = final_score_from_estimated_onset(
        residual,
        raw_signal,
        panel.onset,
        estimated,
        panel.t100,
        params,
    )
    error = (
        estimated.astype(np.int32)
        - panel.onset.astype(np.int32)
    )
    return final_score, estimated, error


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data_cfg = core.data_config()
    data = m22.m2.generate_negative_family(
        family, n, rng, data_cfg
    )
    virtual_signal, reference_onset, _, _ = (
        m22.m5.generate_virtual_hypotheses(
            n, rng, data_cfg
        )
    )
    endpoint = m22.m9.time_at_fraction(
        virtual_signal, cfg.target_fraction
    )
    residual, _, params = (
        m22.m5.sbw_with_signal_operator(
            data.y, virtual_signal, data_cfg
        )
    )
    estimated, hinge_score = estimate_onset_hinge(
        residual, endpoint, cfg
    )
    final_score = final_score_from_estimated_onset(
        residual,
        virtual_signal,
        reference_onset,
        estimated,
        endpoint,
        params,
    )
    return final_score, estimated, endpoint


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

    score_parts = []
    onset_parts = []
    endpoint_parts = []
    remaining = cfg.calibration_negatives_per_family

    while remaining > 0:
        n = min(cfg.calibration_batch_size, remaining)
        score, onset, endpoint = (
            evaluate_negative_family(
                family, n, rng, cfg, core
            )
        )
        score_parts.append(
            np.asarray(score, dtype=np.float32)
        )
        onset_parts.append(
            np.asarray(onset, dtype=np.int16)
        )
        endpoint_parts.append(
            np.asarray(endpoint, dtype=np.int16)
        )
        remaining -= n

    output = {
        "score": np.concatenate(score_parts),
        "estimated_onset": np.concatenate(
            onset_parts
        ),
        "endpoint": np.concatenate(endpoint_parts),
    }
    for key, values in output.items():
        if (
            len(values)
            != cfg.calibration_negatives_per_family
        ):
            raise RuntimeError(
                f"Wrong calibration size for {family}: "
                f"{key}."
            )
    if not np.isfinite(output["score"]).all():
        raise RuntimeError(
            f"Non-finite calibration score: {family}."
        )
    return output


def freeze_threshold(
    cfg: Config,
    family_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame]:
    scores = {}
    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            scores[family] = data["score"].copy()

    threshold, family_specific, allowed = (
        m22.m2.conservative_threshold(
            scores,
            cfg.development_fpr_target,
        )
    )
    rows = []
    for family in NEGATIVE_FAMILIES:
        values = scores[family]
        alerts = int(np.sum(values >= threshold))
        if alerts > allowed[family]:
            raise RuntimeError(
                f"Calibration count exceeded for {family}."
            )
        rows.append(
            {
                "family": family,
                "threshold": threshold,
                "family_specific_threshold": (
                    family_specific[family]
                ),
                "alerts": alerts,
                "n": len(values),
                "allowed": allowed[family],
                "rate": alerts / len(values),
            }
        )
    details = {
        "threshold": float(threshold),
        "family_thresholds": family_specific,
        "allowed_counts": allowed,
        "calibration_negatives_per_family": (
            cfg.calibration_negatives_per_family
        ),
    }
    return details, pd.DataFrame(rows)


def evaluate_holdout(
    cfg: Config,
    seed_record: dict,
    threshold: float,
) -> dict:
    analysis = cfg.analysis_config()
    core = analysis.core_config(seed_record)
    batch_sequences = np.random.SeedSequence(
        seed_record["seeds"]["holdout"]
    ).spawn(cfg.holdout_batches)

    positive_counts = {
        stratum: np.zeros(
            cfg.holdout_batches, dtype=np.int64
        )
        for stratum in POSITIVE_STRATA
    }
    positive_ns = {
        stratum: np.zeros(
            cfg.holdout_batches, dtype=np.int64
        )
        for stratum in POSITIVE_STRATA
    }
    onset_good_counts = {
        stratum: np.zeros(
            cfg.holdout_batches, dtype=np.int64
        )
        for stratum in POSITIVE_STRATA
    }
    detected_errors = {
        stratum: [] for stratum in POSITIVE_STRATA
    }

    negative_counts = {
        family: 0 for family in NEGATIVE_FAMILIES
    }
    negative_ns = {
        family: 0 for family in NEGATIVE_FAMILIES
    }
    positive_score_parts = []
    negative_score_parts = []

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
            score, estimated, error = (
                evaluate_positive_panel(
                    panel, cfg, core
                )
            )
            hits = score >= threshold
            good = (
                hits
                & (error >= cfg.onset_error_low)
                & (error <= cfg.onset_error_high)
            )

            positive_counts[stratum][batch] += int(
                hits.sum()
            )
            positive_ns[stratum][batch] += len(hits)
            onset_good_counts[stratum][batch] += int(
                good.sum()
            )
            detected_errors[stratum].append(
                error[hits].astype(np.int16)
            )
            positive_score_parts.append(
                score.astype(np.float32)
            )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[len(POSITIVE_STRATA):],
        ):
            score, estimated, endpoint = (
                evaluate_negative_family(
                    family,
                    cfg.holdout_negative_per_family_per_batch,
                    rng,
                    cfg,
                    core,
                )
            )
            alerts = score >= threshold
            negative_counts[family] += int(
                alerts.sum()
            )
            negative_ns[family] += len(alerts)
            negative_score_parts.append(
                score.astype(np.float32)
            )

    negative_rows = []
    fpr_pass = True
    maximum_fpr_upper = 0.0
    for family in NEGATIVE_FAMILIES:
        x = negative_counts[family]
        n = negative_ns[family]
        upper = m22.m2.clopper_pearson_upper(
            x, n
        )
        maximum_fpr_upper = max(
            maximum_fpr_upper, upper
        )
        if upper > cfg.holdout_fpr_upper_limit:
            fpr_pass = False
        negative_rows.append(
            {
                "family": family,
                "alerts": x,
                "n": n,
                "rate": x / n,
                "cp_upper_95": upper,
            }
        )

    stratum_rows = []
    batch_rows = []
    successes = []
    ns = []
    good_strata = 0
    hits_by_stratum = {}

    total_detected = 0
    total_onset_good = 0
    total_early = 0
    total_late = 0
    all_detected_errors = []

    for stratum in POSITIVE_STRATA:
        batch_hits = positive_counts[stratum]
        batch_ns = positive_ns[stratum]
        x = int(batch_hits.sum())
        n = int(batch_ns.sum())
        lower = m22.m5.clopper_pearson_lower(
            x, n
        )
        if (
            lower
            >= cfg.minimum_stratum_recall_lower_ci
        ):
            good_strata += 1
        successes.append(x)
        ns.append(n)

        hits = np.zeros(n, dtype=bool)
        hits[:x] = True
        hits_by_stratum[stratum] = hits

        errors = (
            np.concatenate(detected_errors[stratum])
            if detected_errors[stratum]
            else np.empty(0, dtype=np.int16)
        )
        good_count = int(
            np.sum(
                (errors >= cfg.onset_error_low)
                & (errors <= cfg.onset_error_high)
            )
        )
        early_count = int(
            np.sum(errors < cfg.onset_error_low)
        )
        late_count = int(
            np.sum(errors > cfg.onset_error_high)
        )
        total_detected += len(errors)
        total_onset_good += good_count
        total_early += early_count
        total_late += late_count
        all_detected_errors.append(errors)

        onset_lower = (
            m22.m5.clopper_pearson_lower(
                good_count, len(errors)
            )
            if len(errors) > 0
            else 0.0
        )
        stratum_rows.append(
            {
                "stratum": stratum,
                "hits": x,
                "n": n,
                "recall": x / n,
                "recall_cp_lower_95": lower,
                "detected_for_onset": len(errors),
                "onset_in_envelope": good_count,
                "onset_accuracy": (
                    good_count / len(errors)
                    if len(errors) > 0
                    else 0.0
                ),
                "onset_accuracy_cp_lower_95": (
                    onset_lower
                ),
                "early_below_minus2": early_count,
                "late_above_plus1": late_count,
                "median_error": (
                    float(np.median(errors))
                    if len(errors) > 0
                    else np.nan
                ),
                "median_absolute_error": (
                    float(
                        np.median(np.abs(errors))
                    )
                    if len(errors) > 0
                    else np.nan
                ),
            }
        )

    boot = m22.m5.stratified_bootstrap_recall(
        hits_by_stratum,
        cfg.bootstrap_replicates,
        seed_record["seeds"]["bootstrap"],
    )
    recall_point = float(
        np.mean(np.asarray(successes) / np.asarray(ns))
    )
    recall_lower = float(np.quantile(boot, 0.05))
    recall_upper = float(np.quantile(boot, 0.95))

    good_batches = 0
    for batch in range(cfg.holdout_batches):
        hits = sum(
            positive_counts[stratum][batch]
            for stratum in POSITIVE_STRATA
        )
        n = sum(
            positive_ns[stratum][batch]
            for stratum in POSITIVE_STRATA
        )
        onset_good = sum(
            onset_good_counts[stratum][batch]
            for stratum in POSITIVE_STRATA
        )
        recall = hits / n
        if recall >= cfg.batch_recall_threshold:
            good_batches += 1
        batch_rows.append(
            {
                "batch": batch,
                "hits": hits,
                "n": n,
                "recall": recall,
                "onset_good": onset_good,
                "onset_accuracy_among_detected": (
                    onset_good / hits
                    if hits > 0
                    else 0.0
                ),
            }
        )

    onset_accuracy = (
        total_onset_good / total_detected
        if total_detected > 0
        else 0.0
    )
    onset_lower = (
        m22.m5.clopper_pearson_lower(
            total_onset_good, total_detected
        )
        if total_detected > 0
        else 0.0
    )
    onset_upper = (
        m22.m2.clopper_pearson_upper(
            total_onset_good, total_detected
        )
        if total_detected > 0
        else 1.0
    )

    detection_pass = bool(
        fpr_pass
        and recall_lower
        >= cfg.minimum_global_recall_lower_ci
        and good_strata >= cfg.minimum_good_strata
        and good_batches >= cfg.minimum_good_batches
    )
    onset_pass = bool(
        onset_lower
        >= cfg.minimum_onset_accuracy_lower_ci
    )
    complete_pass = bool(
        detection_pass and onset_pass
    )

    positive_scores = np.concatenate(
        positive_score_parts
    )
    negative_scores = np.concatenate(
        negative_score_parts
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
    errors_all = np.concatenate(
        all_detected_errors
    ) if all_detected_errors else np.empty(0)

    summary = {
        "replication": seed_record["replication"],
        "threshold": threshold,
        "recall_point": recall_point,
        "recall_lower_95": recall_lower,
        "recall_upper_95": recall_upper,
        "good_strata": good_strata,
        "good_batches": good_batches,
        "fpr_pass": fpr_pass,
        "maximum_fpr_upper_95": (
            maximum_fpr_upper
        ),
        "detection_pass": detection_pass,
        "detected_for_onset": total_detected,
        "onset_in_envelope": total_onset_good,
        "onset_accuracy": onset_accuracy,
        "onset_accuracy_lower_95": onset_lower,
        "onset_accuracy_upper_95": onset_upper,
        "early_below_minus2": total_early,
        "late_above_plus1": total_late,
        "median_error": (
            float(np.median(errors_all))
            if len(errors_all) > 0
            else np.nan
        ),
        "median_absolute_error": (
            float(np.median(np.abs(errors_all)))
            if len(errors_all) > 0
            else np.nan
        ),
        "onset_pass": onset_pass,
        "pass": complete_pass,
        "auroc": float(
            roc_auc_score(labels, values)
        ),
        "average_precision": float(
            average_precision_score(
                labels, values
            )
        ),
    }

    return {
        "summary": summary,
        "stratum_summary": pd.DataFrame(
            stratum_rows
        ),
        "negative_summary": pd.DataFrame(
            negative_rows
        ),
        "batch_summary": pd.DataFrame(batch_rows),
    }


def aggregate_results(
    cfg: Config,
    holdout_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
) -> dict:
    rep = holdout_summary.sort_values(
        "replication"
    )
    if len(rep) != cfg.holdout_count:
        raise RuntimeError(
            "Wrong number of holdouts."
        )

    counts = []
    ns = []
    for holdout in range(cfg.holdout_count):
        subset = stratum_summary[
            stratum_summary.replication == holdout
        ].set_index("stratum")
        counts.append(
            [
                int(subset.loc[s, "hits"])
                for s in POSITIVE_STRATA
            ]
        )
        ns.append(
            [
                int(subset.loc[s, "n"])
                for s in POSITIVE_STRATA
            ]
        )

    boot = m22.m15.hierarchical_bootstrap(
        np.asarray(counts),
        np.asarray(ns),
        cfg.bootstrap_replicates,
        cfg.aggregate_bootstrap_root_seed,
    )
    recall_point = float(rep.recall_point.mean())
    recall_lower = float(np.quantile(boot, 0.05))
    recall_upper = float(np.quantile(boot, 0.95))

    total_detected = int(
        rep.detected_for_onset.sum()
    )
    total_good = int(
        rep.onset_in_envelope.sum()
    )
    accuracy = total_good / total_detected
    accuracy_lower = (
        m22.m5.clopper_pearson_lower(
            total_good, total_detected
        )
    )
    accuracy_upper = (
        m22.m2.clopper_pearson_upper(
            total_good, total_detected
        )
    )

    complete_pass_count = int(rep["pass"].sum())
    detection_pass_count = int(
        rep.detection_pass.sum()
    )
    onset_pass_count = int(
        rep.onset_pass.sum()
    )
    fpr_pass_count = int(rep.fpr_pass.sum())
    extreme = bool(
        np.any(
            rep.maximum_fpr_upper_95
            > cfg.extreme_fpr_upper_limit
        )
    )
    fpr_robust = bool(
        fpr_pass_count
        >= cfg.minimum_fpr_pass_holdouts
        and not extreme
    )

    passed = bool(
        complete_pass_count
        >= cfg.minimum_complete_holdout_passes
        and recall_lower
        >= cfg.minimum_global_recall_lower_ci
        and accuracy_lower
        >= cfg.minimum_onset_accuracy_lower_ci
        and fpr_robust
    )
    strong_fail = bool(
        complete_pass_count <= 2
        or recall_upper
        <= cfg.minimum_global_recall_lower_ci
        or accuracy_upper
        < cfg.strong_fail_onset_accuracy_upper
        or extreme
    )

    verdict = (
        "PASS_CAUSAL_ONSET_ESTIMATOR"
        if passed
        else (
            "STRONG_FAIL_CAUSAL_ONSET_ESTIMATOR"
            if strong_fail
            else "INCONCLUSIVE"
        )
    )

    prediction = {
        "recall_in_range": bool(
            cfg.prediction_recall_low
            <= recall_point
            <= cfg.prediction_recall_high
        ),
        "onset_accuracy_in_range": bool(
            cfg.prediction_accuracy_low
            <= accuracy
            <= cfg.prediction_accuracy_high
        ),
        "complete_passes_le_2": bool(
            complete_pass_count
            <= cfg.prediction_max_complete_passes
        ),
        "verdict_confirmed": (
            verdict
            == "STRONG_FAIL_CAUSAL_ONSET_ESTIMATOR"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": verdict,
        "aggregate_recall_point": recall_point,
        "aggregate_recall_lower_95": recall_lower,
        "aggregate_recall_upper_95": recall_upper,
        "complete_holdout_pass_count": (
            complete_pass_count
        ),
        "detection_holdout_pass_count": (
            detection_pass_count
        ),
        "onset_holdout_pass_count": (
            onset_pass_count
        ),
        "fpr_pass_holdout_count": fpr_pass_count,
        "fpr_robust": fpr_robust,
        "extreme_fpr_violation": extreme,
        "pooled_detected_for_onset": total_detected,
        "pooled_onset_in_envelope": total_good,
        "pooled_onset_accuracy": accuracy,
        "pooled_onset_accuracy_lower_95": (
            accuracy_lower
        ),
        "pooled_onset_accuracy_upper_95": (
            accuracy_upper
        ),
        "pooled_early_below_minus2": int(
            rep.early_below_minus2.sum()
        ),
        "pooled_late_above_plus1": int(
            rep.late_above_plus1.sum()
        ),
        "prediction": prediction,
        "bootstrap": boot,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
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
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
