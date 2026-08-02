
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
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
LENGTH_LABELS = ("8", "16", "24", "full")
FIXED_LENGTHS = {"8": 8, "16": 16, "24": 24}


@dataclass(frozen=True)
class Config:
    version: str = "28.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    length_labels: tuple[str, ...] = LENGTH_LABELS

    calibration_seed: int = 2026082301
    holdout_root_seed: int = 2026082302
    aggregate_bootstrap_root_seed: int = 2026082303

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
    bootstrap_replicates: int = 10_000

    prediction_ranges: tuple[tuple[str, float, float], ...] = (
        ("8", 0.24, 0.34),
        ("16", 0.12, 0.22),
        ("24", 0.07, 0.18),
        ("full", 0.05, 0.25),
    )

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
            holdout_positive_per_stratum_total=self.holdout_positive_per_stratum_total,
            holdout_negative_per_family_total=self.holdout_negative_per_family_total,
            holdout_batches=self.holdout_batches,
            holdout_positive_per_stratum_per_batch=self.holdout_positive_per_stratum_per_batch,
            holdout_negative_per_family_per_batch=self.holdout_negative_per_family_per_batch,
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
    calibration_children = np.random.SeedSequence(cfg.calibration_seed).spawn(
        len(NEGATIVE_FAMILIES)
    )
    calibration = {
        family: {
            "integer_seed": _integer_seed(child),
            "entropy": child.entropy,
            "spawn_key": list(child.spawn_key),
        }
        for family, child in zip(NEGATIVE_FAMILIES, calibration_children)
    }

    holdout_children = np.random.SeedSequence(cfg.holdout_root_seed).spawn(
        cfg.holdout_count
    )
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


def paired_confirmation_scores(
    residual: np.ndarray,
    processed_template: np.ndarray,
    onset: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> Dict[str, np.ndarray]:
    residual = np.asarray(residual, dtype=np.float64)
    template = np.asarray(processed_template, dtype=np.float64)
    onset = np.asarray(onset, dtype=np.int32)
    endpoint = np.asarray(endpoint, dtype=np.int32)

    if residual.shape != template.shape:
        raise ValueError("Residual/template shape mismatch.")
    if onset.shape != (residual.shape[0],):
        raise ValueError("Onset shape mismatch.")
    if endpoint.shape != (residual.shape[0],):
        raise ValueError("Endpoint shape mismatch.")
    if np.any(endpoint < onset):
        raise ValueError("Endpoint precedes onset.")

    time = np.arange(residual.shape[1])[None, :]
    scores: Dict[str, np.ndarray] = {}

    for label in cfg.length_labels:
        if label == "full":
            start = onset
        else:
            start = endpoint - FIXED_LENGTHS[label] + 1

        mask = (
            (time >= start[:, None])
            & (time <= endpoint[:, None])
        )
        masked_template = np.where(mask, template, 0.0)
        numerator = np.sum(
            np.where(mask, residual, 0.0) * masked_template,
            axis=1,
        )
        denominator = np.sqrt(
            np.sum(np.square(masked_template), axis=1)
        )
        scores[label] = np.divide(
            numerator,
            denominator,
            out=np.zeros_like(numerator),
            where=denominator > 1e-12,
        )
    return scores


def evaluate_positive_panel(
    panel: m22.m9.PositivePanel,
    cfg: Config,
    core: m22.m9.Config,
) -> Dict[str, np.ndarray]:
    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_signal
    residual, processed_signal, _ = m22.m5.sbw_with_signal_operator(
        observed,
        raw_signal,
        core.data_config(),
    )
    return paired_confirmation_scores(
        residual,
        processed_signal,
        panel.onset,
        panel.t100,
        cfg,
    )


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[Dict[str, np.ndarray], np.ndarray, np.ndarray]:
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
    residual, processed_template, _ = m22.m5.sbw_with_signal_operator(
        data.y,
        virtual_signal,
        data_cfg,
    )
    scores = paired_confirmation_scores(
        residual,
        processed_template,
        virtual_onset,
        endpoint,
        cfg,
    )
    return scores, virtual_onset, endpoint


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> dict:
    seed = seed_plan["calibration"][family]["integer_seed"]
    rng = np.random.default_rng(seed)
    core = calibration_core(cfg)

    score_parts = {
        label: [] for label in cfg.length_labels
    }
    onset_parts = []
    endpoint_parts = []
    remaining = cfg.calibration_negatives_per_family

    while remaining > 0:
        n = min(cfg.calibration_batch_size, remaining)
        scores, onset, endpoint = evaluate_negative_family(
            family,
            n,
            rng,
            cfg,
            core,
        )
        for label in cfg.length_labels:
            score_parts[label].append(
                np.asarray(scores[label], dtype=np.float32)
            )
        onset_parts.append(np.asarray(onset, dtype=np.int16))
        endpoint_parts.append(np.asarray(endpoint, dtype=np.int16))
        remaining -= n

    output = {
        f"score_{label}": np.concatenate(score_parts[label])
        for label in cfg.length_labels
    }
    output["onset"] = np.concatenate(onset_parts)
    output["endpoint"] = np.concatenate(endpoint_parts)

    for key, values in output.items():
        if len(values) != cfg.calibration_negatives_per_family:
            raise RuntimeError(
                f"Wrong calibration size for {family}: {key}."
            )
    for label in cfg.length_labels:
        if not np.isfinite(output[f"score_{label}"]).all():
            raise RuntimeError(
                f"Non-finite calibration score: {family}, {label}."
            )
    return output


def freeze_thresholds(
    cfg: Config,
    family_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame]:
    loaded: dict[str, dict[str, np.ndarray]] = {}
    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            loaded[family] = {
                label: data[f"score_{label}"].copy()
                for label in cfg.length_labels
            }

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []

    for label in cfg.length_labels:
        by_family = {
            family: loaded[family][label]
            for family in NEGATIVE_FAMILIES
        }
        threshold, specific, allowed = (
            m22.m2.conservative_threshold(
                by_family,
                cfg.development_fpr_target,
            )
        )
        thresholds[label] = float(threshold)
        family_thresholds[label] = specific
        allowed_counts[label] = allowed

        for family in NEGATIVE_FAMILIES:
            values = by_family[family]
            alerts = int(np.sum(values >= threshold))
            if alerts > allowed[family]:
                raise RuntimeError(
                    f"Calibration count exceeded: {label}, {family}."
                )
            rows.append(
                {
                    "length": label,
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

    positive_counts = {
        label: {
            stratum: np.zeros(
                cfg.holdout_batches,
                dtype=np.int64,
            )
            for stratum in POSITIVE_STRATA
        }
        for label in cfg.length_labels
    }
    positive_ns = {
        label: {
            stratum: np.zeros(
                cfg.holdout_batches,
                dtype=np.int64,
            )
            for stratum in POSITIVE_STRATA
        }
        for label in cfg.length_labels
    }
    negative_counts = {
        label: {
            family: 0 for family in NEGATIVE_FAMILIES
        }
        for label in cfg.length_labels
    }
    negative_ns = {
        label: {
            family: 0 for family in NEGATIVE_FAMILIES
        }
        for label in cfg.length_labels
    }

    positive_score_parts = {
        label: [] for label in cfg.length_labels
    }
    negative_score_parts = {
        label: [] for label in cfg.length_labels
    }

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
            scores = evaluate_positive_panel(
                panel,
                cfg,
                core,
            )
            for label in cfg.length_labels:
                values = scores[label]
                hits = values >= thresholds[label]
                positive_counts[label][stratum][batch] += int(
                    hits.sum()
                )
                positive_ns[label][stratum][batch] += len(hits)
                positive_score_parts[label].append(
                    values.astype(np.float32)
                )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[len(POSITIVE_STRATA):],
        ):
            scores, onset, endpoint = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            for label in cfg.length_labels:
                values = scores[label]
                alerts = values >= thresholds[label]
                negative_counts[label][family] += int(
                    alerts.sum()
                )
                negative_ns[label][family] += len(alerts)
                negative_score_parts[label].append(
                    values.astype(np.float32)
                )

    summary_rows = []
    stratum_rows = []
    negative_rows = []
    batch_rows = []
    metric_rows = []

    positive_scores_all = {
        label: np.concatenate(positive_score_parts[label])
        for label in cfg.length_labels
    }
    negative_scores_all = {
        label: np.concatenate(negative_score_parts[label])
        for label in cfg.length_labels
    }

    for label_index, label in enumerate(cfg.length_labels):
        fpr_pass = True
        maximum_fpr_upper = 0.0

        for family in NEGATIVE_FAMILIES:
            x = negative_counts[label][family]
            n = negative_ns[label][family]
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
                    "length": label,
                    "family": family,
                    "alerts": x,
                    "n": n,
                    "rate": x / n,
                    "fpr_upper_one_sided_95": upper,
                }
            )

        successes = []
        ns = []
        good_strata = 0
        hits_by_stratum = {}

        for stratum in POSITIVE_STRATA:
            x = int(
                positive_counts[label][stratum].sum()
            )
            n = int(
                positive_ns[label][stratum].sum()
            )
            lower = m22.m5.clopper_pearson_lower(x, n)
            good_strata += int(
                lower
                >= cfg.minimum_stratum_recall_lower_one_sided_95
            )
            successes.append(x)
            ns.append(n)
            hits = np.zeros(n, dtype=bool)
            hits[:x] = True
            hits_by_stratum[stratum] = hits
            stratum_rows.append(
                {
                    "replication": seed_record["replication"],
                    "length": label,
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
            + label_index,
        )
        recall_point = float(
            np.mean(
                np.asarray(successes)
                / np.asarray(ns)
            )
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
                positive_counts[label][stratum][batch]
                for stratum in POSITIVE_STRATA
            )
            n = sum(
                positive_ns[label][stratum][batch]
                for stratum in POSITIVE_STRATA
            )
            recall = hits / n
            good_batches += int(
                recall
                >= cfg.batch_recall_threshold
            )
            batch_rows.append(
                {
                    "replication": seed_record["replication"],
                    "length": label,
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

        positive_values = positive_scores_all[label]
        negative_values = negative_scores_all[label]
        labels = np.concatenate(
            [
                np.ones(len(positive_values), dtype=int),
                np.zeros(len(negative_values), dtype=int),
            ]
        )
        combined_values = np.concatenate(
            [positive_values, negative_values]
        )

        summary_rows.append(
            {
                "replication": seed_record["replication"],
                "length": label,
                "threshold": thresholds[label],
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

    for left, right in combinations(cfg.length_labels, 2):
        left_positive = positive_scores_all[left]
        right_positive = positive_scores_all[right]
        left_negative = negative_scores_all[left]
        right_negative = negative_scores_all[right]
        left_hits = left_positive >= thresholds[left]
        right_hits = right_positive >= thresholds[right]

        metric_rows.append(
            {
                "replication": seed_record["replication"],
                "left_length": left,
                "right_length": right,
                "positive_score_correlation": float(
                    np.corrcoef(
                        left_positive,
                        right_positive,
                    )[0, 1]
                ),
                "negative_score_correlation": float(
                    np.corrcoef(
                        left_negative,
                        right_negative,
                    )[0, 1]
                ),
                "both_detected": int(
                    np.sum(left_hits & right_hits)
                ),
                "left_only_detected": int(
                    np.sum(left_hits & ~right_hits)
                ),
                "right_only_detected": int(
                    np.sum(~left_hits & right_hits)
                ),
                "neither_detected": int(
                    np.sum(~left_hits & ~right_hits)
                ),
            }
        )

    return {
        "length_summary": pd.DataFrame(summary_rows),
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
        "paired_metrics": pd.DataFrame(metric_rows),
    }


def aggregate_results(
    cfg: Config,
    length_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    thresholds: dict[str, float],
    threshold_drivers: dict[str, str],
) -> dict:
    details = {}
    bootstrap_frames = []
    ranges = {
        label: (low, high)
        for label, low, high in cfg.prediction_ranges
    }
    bootstrap_sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(len(cfg.length_labels))

    for index, label in enumerate(cfg.length_labels):
        rep = length_summary[
            length_summary.length.astype(str) == label
        ].sort_values("replication")
        if len(rep) != cfg.holdout_count:
            raise RuntimeError(
                f"Wrong number of holdouts for {label}."
            )

        counts = []
        ns = []
        for holdout in range(cfg.holdout_count):
            subset = stratum_summary[
                (
                    stratum_summary.length.astype(str)
                    == label
                )
                & (
                    stratum_summary.replication
                    == holdout
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

        bootstrap_seed = _integer_seed(
            bootstrap_sequences[index]
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
                    "length": label,
                    "replicate": np.arange(
                        cfg.bootstrap_replicates
                    ),
                    "recall": bootstrap,
                }
            )
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
        passed = bool(
            pass_count
            >= cfg.minimum_holdout_passes
            and lower
            >= cfg.minimum_global_recall_lower_one_sided_95
            and fpr_robust
        )
        strong_fail = bool(
            pass_count <= 2
            or upper
            <= cfg.minimum_global_recall_lower_one_sided_95
            or extreme
        )
        verdict = (
            "PASS"
            if passed
            else (
                "STRONG_FAIL"
                if strong_fail
                else "INCONCLUSIVE"
            )
        )
        low, high = ranges[label]
        details[label] = {
            "length": label,
            "verdict": verdict,
            "threshold": thresholds[label],
            "threshold_driver": threshold_drivers[label],
            "aggregate_recall_point": point,
            "aggregate_recall_lower_one_sided_95": lower,
            "aggregate_recall_upper_one_sided_95": upper,
            "holdout_pass_count": pass_count,
            "fpr_pass_holdout_count": fpr_pass_count,
            "fpr_robust": fpr_robust,
            "extreme_fpr_violation": extreme,
            "prediction_recall_in_range": bool(
                low <= point <= high
            ),
        }

    passing = [
        label
        for label in cfg.length_labels
        if details[label]["verdict"] == "PASS"
    ]
    if passing:
        overall = "PASS_LENGTH_CANDIDATE"
        candidate = passing[0]
    elif all(
        details[label]["verdict"]
        == "STRONG_FAIL"
        for label in cfg.length_labels
    ):
        overall = "STRONG_FAIL_ALL_LENGTHS"
        candidate = None
    else:
        overall = "INCONCLUSIVE_LENGTH_MAP"
        candidate = None

    thresholds_ordered = [
        thresholds[label]
        for label in cfg.length_labels
    ]
    recalls_ordered = [
        details[label]["aggregate_recall_point"]
        for label in cfg.length_labels
    ]

    prediction = {
        "no_length_passed": not passing,
        "all_lengths_strong_fail": all(
            details[label]["verdict"]
            == "STRONG_FAIL"
            for label in cfg.length_labels
        ),
        "thresholds_strictly_increasing": all(
            left < right
            for left, right in zip(
                thresholds_ordered,
                thresholds_ordered[1:],
            )
        ),
        "recall_strictly_decreasing": all(
            left > right
            for left, right in zip(
                recalls_ordered,
                recalls_ordered[1:],
            )
        ),
        "shared_step_drives_16_24_full": all(
            threshold_drivers[label]
            == "shared_step"
            for label in ("16", "24", "full")
        ),
        "all_recall_ranges_confirmed": all(
            details[label][
                "prediction_recall_in_range"
            ]
            for label in cfg.length_labels
        ),
        "overall_verdict_confirmed": (
            overall
            == "STRONG_FAIL_ALL_LENGTHS"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": overall,
        "candidate_length": candidate,
        "length_details": details,
        "prediction": prediction,
        "bootstrap_df": pd.concat(
            bootstrap_frames,
            ignore_index=True,
        ),
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
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
