
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
import arara_m29_dependency as m29


POSITIVE_STRATA = m22.POSITIVE_STRATA
NEGATIVE_FAMILIES = m22.NEGATIVE_FAMILIES
METHODS = ("baseline8", "reference_projected8")


@dataclass(frozen=True)
class Config:
    version: str = "30.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    window_length: int = 8
    methods: tuple[str, ...] = METHODS

    calibration_seed: int = 2026082501
    holdout_root_seed: int = 2026082502
    aggregate_bootstrap_root_seed: int = 2026082503
    paired_difference_bootstrap_seed: int = 2026082504

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

    projection_tolerance: float = 1e-12
    norm_tolerance: float = 1e-12
    bootstrap_replicates: int = 10_000

    prediction_baseline_range: tuple[float, float] = (0.27, 0.34)
    prediction_candidate_range: tuple[float, float] = (0.48, 0.68)
    prediction_delta_range: tuple[float, float] = (0.18, 0.38)
    prediction_min_median_energy_retention: float = 0.70
    prediction_candidate_pass_low: int = 3
    prediction_candidate_pass_high: int = 10

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


def reference_projected_score(
    residual: np.ndarray,
    processed_template: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, dict]:
    residual_window = m29.extract_last_window(
        residual,
        endpoint,
        cfg.window_length,
    )
    template_window = m29.extract_last_window(
        processed_template,
        endpoint,
        cfg.window_length,
    )
    reference_window = m29.extract_last_window(
        processed_reference,
        endpoint,
        cfg.window_length,
    )

    reference_energy = np.sum(
        reference_window**2,
        axis=1,
    )
    reference_valid = (
        reference_energy
        > cfg.projection_tolerance
    )

    residual_coefficient = np.divide(
        np.sum(
            reference_window
            * residual_window,
            axis=1,
        ),
        reference_energy,
        out=np.zeros(
            residual_window.shape[0],
            dtype=np.float64,
        ),
        where=reference_valid,
    )
    template_coefficient = np.divide(
        np.sum(
            reference_window
            * template_window,
            axis=1,
        ),
        reference_energy,
        out=np.zeros(
            template_window.shape[0],
            dtype=np.float64,
        ),
        where=reference_valid,
    )

    residual_projected = (
        residual_window
        - residual_coefficient[:, None]
        * reference_window
    )
    template_projected = (
        template_window
        - template_coefficient[:, None]
        * reference_window
    )

    original_template_energy = np.sum(
        template_window**2,
        axis=1,
    )
    projected_template_energy = np.sum(
        template_projected**2,
        axis=1,
    )
    template_valid = (
        projected_template_energy
        > cfg.norm_tolerance
    )

    numerator = np.sum(
        residual_projected
        * template_projected,
        axis=1,
    )
    denominator = np.sqrt(
        projected_template_energy
    )
    score = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=template_valid,
    )

    energy_retention = np.divide(
        projected_template_energy,
        original_template_energy,
        out=np.zeros_like(
            projected_template_energy
        ),
        where=(
            original_template_energy
            > cfg.norm_tolerance
        ),
    )
    energy_retention = np.clip(
        energy_retention,
        0.0,
        1.0,
    )

    diagnostics = {
        "reference_degenerate": (
            ~reference_valid
        ),
        "template_degenerate": (
            ~template_valid
        ),
        "energy_retention": energy_retention,
    }
    return score, diagnostics


def paired_scores_from_processed(
    residual: np.ndarray,
    processed_template: np.ndarray,
    processed_reference: np.ndarray,
    endpoint: np.ndarray,
    cfg: Config,
) -> tuple[Dict[str, np.ndarray], dict]:
    baseline = m29.baseline_score(
        residual,
        processed_template,
        endpoint,
        cfg,
    )
    candidate, diagnostics = (
        reference_projected_score(
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
            "reference_projected8": candidate,
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
    ) = m29.sbw_with_reference_nuisance(
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
    ) = m29.sbw_with_reference_nuisance(
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
    reference_degenerate_parts = []
    template_degenerate_parts = []
    energy_retention_parts = []
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
        reference_degenerate_parts.append(
            diagnostics[
                "reference_degenerate"
            ]
        )
        template_degenerate_parts.append(
            diagnostics[
                "template_degenerate"
            ]
        )
        energy_retention_parts.append(
            diagnostics[
                "energy_retention"
            ].astype(np.float32)
        )
        remaining -= n

    output = {
        f"score_{method}": np.concatenate(
            score_parts[method]
        )
        for method in cfg.methods
    }
    output["reference_degenerate"] = (
        np.concatenate(
            reference_degenerate_parts
        ).astype(np.int8)
    )
    output["template_degenerate"] = (
        np.concatenate(
            template_degenerate_parts
        ).astype(np.int8)
    )
    output["energy_retention"] = (
        np.concatenate(
            energy_retention_parts
        ).astype(np.float32)
    )

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
                f"Non-finite score: "
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
            reference_degenerate = data[
                "reference_degenerate"
            ]
            template_degenerate = data[
                "template_degenerate"
            ]
            energy_retention = data[
                "energy_retention"
            ]
            diagnostic_rows.append(
                {
                    "family": family,
                    "n": len(energy_retention),
                    "reference_degenerate_fraction": float(
                        np.mean(
                            reference_degenerate
                        )
                    ),
                    "template_degenerate_fraction": float(
                        np.mean(
                            template_degenerate
                        )
                    ),
                    "energy_retention_mean": float(
                        np.mean(
                            energy_retention
                        )
                    ),
                    "energy_retention_median": float(
                        np.median(
                            energy_retention
                        )
                    ),
                    "energy_retention_q05": float(
                        np.quantile(
                            energy_retention,
                            0.05,
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
    diagnostic_rows = []

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

            diagnostic_rows.append(
                {
                    "replication": seed_record[
                        "replication"
                    ],
                    "population": "positive",
                    "group": stratum,
                    "n": len(
                        diagnostics[
                            "energy_retention"
                        ]
                    ),
                    "reference_degenerate": int(
                        np.sum(
                            diagnostics[
                                "reference_degenerate"
                            ]
                        )
                    ),
                    "template_degenerate": int(
                        np.sum(
                            diagnostics[
                                "template_degenerate"
                            ]
                        )
                    ),
                    "energy_retention_sum": float(
                        np.sum(
                            diagnostics[
                                "energy_retention"
                            ]
                        )
                    ),
                    "energy_retention_median": float(
                        np.median(
                            diagnostics[
                                "energy_retention"
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

            diagnostic_rows.append(
                {
                    "replication": seed_record[
                        "replication"
                    ],
                    "population": "negative",
                    "group": family,
                    "n": len(
                        diagnostics[
                            "energy_retention"
                        ]
                    ),
                    "reference_degenerate": int(
                        np.sum(
                            diagnostics[
                                "reference_degenerate"
                            ]
                        )
                    ),
                    "template_degenerate": int(
                        np.sum(
                            diagnostics[
                                "template_degenerate"
                            ]
                        )
                    ),
                    "energy_retention_sum": float(
                        np.sum(
                            diagnostics[
                                "energy_retention"
                            ]
                        )
                    ),
                    "energy_retention_median": float(
                        np.median(
                            diagnostics[
                                "energy_retention"
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
        candidate_hits = np.concatenate(
            positive_hits[
                "reference_projected8"
            ][stratum]
        )
        codes = (
            baseline_hits.astype(np.int8) * 2
            + candidate_hits.astype(np.int8)
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
            np.quantile(
                bootstrap,
                0.05,
            )
        )
        recall_upper = float(
            np.quantile(
                bootstrap,
                0.95,
            )
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

    paired_bootstrap = m29.paired_stratified_bootstrap(
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
    candidate_point = float(
        paired_bootstrap[
            "projected_recall"
        ].mean()
    )
    delta_point = (
        candidate_point - baseline_point
    )

    baseline_positive = positive_scores_all[
        "baseline8"
    ]
    candidate_positive = positive_scores_all[
        "reference_projected8"
    ]
    baseline_negative = negative_scores_all[
        "baseline8"
    ]
    candidate_negative = negative_scores_all[
        "reference_projected8"
    ]

    paired_row = {
        "replication": seed_record["replication"],
        "baseline_recall_point": baseline_point,
        "candidate_recall_point": candidate_point,
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
                candidate_positive,
            )[0, 1]
        ),
        "negative_score_correlation": float(
            np.corrcoef(
                baseline_negative,
                candidate_negative,
            )[0, 1]
        ),
        "neither_detected": int(
            sum(
                counts[0]
                for counts in pair_counts.values()
            )
        ),
        "candidate_only_detected": int(
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
                "candidate_only": int(counts[1]),
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
        "projection_diagnostics": pd.DataFrame(
            diagnostic_rows
        ),
    }


def hierarchical_paired_bootstrap(
    pair_count_array: np.ndarray,
    replicates: int,
    seed: int,
) -> np.ndarray:
    counts = np.asarray(
        pair_count_array,
        dtype=np.int64,
    )
    if (
        counts.ndim != 3
        or counts.shape[1]
        != len(POSITIVE_STRATA)
        or counts.shape[2] != 4
    ):
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
                candidate = (
                    draws[:, 1]
                    + draws[:, 3]
                ) / n
                selected_delta += (
                    candidate - baseline
                ) / len(POSITIVE_STRATA)

            position_delta[mask] = selected_delta

        output += position_delta / holdout_count

    return output


def aggregate_results(
    cfg: Config,
    method_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    pair_counts: pd.DataFrame,
    projection_diagnostics: pd.DataFrame,
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
            int(row.candidate_only),
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
            "reference_projected8"
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
        pivot["reference_projected8"]
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
        "reference_projected8"
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
            "PASS_REFERENCE_PROJECTION_CANDIDATE"
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
            "STRONG_FAIL_REFERENCE_PROJECTION"
        )
    else:
        overall = (
            "INCONCLUSIVE_REFERENCE_PROJECTION"
        )

    positive_diagnostics = projection_diagnostics[
        projection_diagnostics.population
        == "positive"
    ]
    total_positive = float(
        positive_diagnostics.n.sum()
    )
    weighted_energy_mean = float(
        positive_diagnostics[
            "energy_retention_sum"
        ].sum()
        / total_positive
    )
    median_of_batch_medians = float(
        positive_diagnostics[
            "energy_retention_median"
        ].median()
    )
    reference_degenerate_fraction = float(
        positive_diagnostics[
            "reference_degenerate"
        ].sum()
        / total_positive
    )
    template_degenerate_fraction = float(
        positive_diagnostics[
            "template_degenerate"
        ].sum()
        / total_positive
    )

    baseline_range = (
        cfg.prediction_baseline_range
    )
    candidate_range = (
        cfg.prediction_candidate_range
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
        "candidate_recall_in_range": bool(
            candidate_range[0]
            <= candidate[
                "aggregate_recall_point"
            ]
            <= candidate_range[1]
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
        "median_energy_retention_above_0_70": bool(
            median_of_batch_medians
            >= cfg.prediction_min_median_energy_retention
        ),
        "material_paired_gain": superiority_pass,
        "candidate_holdout_passes_in_range": bool(
            cfg.prediction_candidate_pass_low
            <= candidate[
                "holdout_pass_count"
            ]
            <= cfg.prediction_candidate_pass_high
        ),
        "overall_verdict_confirmed": bool(
            overall
            == "INCONCLUSIVE_REFERENCE_PROJECTION"
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
        "projection_diagnostics": {
            "positive_weighted_energy_retention_mean": (
                weighted_energy_mean
            ),
            "positive_median_of_batch_medians": (
                median_of_batch_medians
            ),
            "positive_reference_degenerate_fraction": (
                reference_degenerate_fraction
            ),
            "positive_template_degenerate_fraction": (
                template_degenerate_fraction
            ),
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
        "m29_dependency_sha256": sha256_file(
            ROOT / "arara_m29_dependency.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
