
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import platform
import sys
from typing import Dict

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
M2_DIR = ROOT / "m2"
M5_DIR = ROOT / "m5"
M9_DIR = ROOT / "m9"
for dependency in (M2_DIR, M5_DIR, M9_DIR):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

import arara_m2 as m2
import arara_m5 as m5
import arara_m9 as m9


POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "16.0"
    fixed_snr: float = 12.0
    target_fraction: float = 0.50

    calibration_sizes: tuple[int, ...] = (
        2_000, 10_000, 50_000
    )
    world_count: int = 3
    resamples_per_size: int = 100

    world_root_seed: int = 2026081101
    resampling_root_seed: int = 2026081102
    recall_bootstrap_root_seed: int = 2026081103

    calibration_superpool_per_family: int = 50_000
    calibration_generation_batch_size: int = 1_000

    holdout_positive_per_stratum_total: int = 2_500
    holdout_negative_per_family_total: int = 5_000
    holdout_batches: int = 20
    holdout_positive_per_stratum_per_batch: int = 125
    holdout_negative_per_family_per_batch: int = 250

    calibration_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    bootstrap_replicates_per_calibration: int = 10_000

    primary_width_ratio_limit: float = 0.50
    predicted_width_ratio_limit: float = 0.40
    primary_50k_world_pass_rate: float = 0.80
    primary_50k_aggregate_lower_pass_rate: float = 0.70
    primary_2k_aggregate_max_pass_rate: float = 0.40
    strong_fail_50k_max_pass_rate: float = 0.20
    strong_fail_50k_recall_lower_q90: float = 0.60

    def core_config(
        self,
        holdout_seed: int = 1,
        bootstrap_seed: int = 2,
    ) -> m9.Config:
        return m9.Config(
            version=self.version,
            snr_levels=(self.fixed_snr,),
            target_fraction=self.target_fraction,
            development_root_seed=1,
            holdout_root_seed=holdout_seed,
            bootstrap_seed=bootstrap_seed,
            development_base_fields_per_shape_context=1_000,
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
            development_fpr_target=self.calibration_fpr_target,
            holdout_fpr_upper_limit=self.holdout_fpr_upper_limit,
            minimum_global_recall_lower_ci=(
                self.minimum_global_recall_lower_ci
            ),
            minimum_stratum_recall_lower_ci=(
                self.minimum_stratum_recall_lower_ci
            ),
            minimum_good_strata=self.minimum_good_strata,
            minimum_good_batches=self.minimum_good_batches,
            batch_recall_threshold=self.batch_recall_threshold,
            maximum_adjacent_point_drop=0.02,
            strong_fail_snr12_recall_upper=0.50,
            bootstrap_replicates=10_000,
            predicted_first_passing_snr=self.fixed_snr,
        )


def _integer_seed(sequence: np.random.SeedSequence) -> int:
    return int(
        sequence.generate_state(1, dtype=np.uint32)[0]
    )


def build_seed_plan(cfg: Config) -> list[dict]:
    world_sequences = np.random.SeedSequence(
        cfg.world_root_seed
    ).spawn(cfg.world_count)
    resampling_sequences = np.random.SeedSequence(
        cfg.resampling_root_seed
    ).spawn(cfg.world_count)
    bootstrap_sequences = np.random.SeedSequence(
        cfg.recall_bootstrap_root_seed
    ).spawn(cfg.world_count)

    records = []
    for world in range(cfg.world_count):
        generation_children = world_sequences[world].spawn(
            len(NEGATIVE_FAMILIES) + 1
        )
        family_children = generation_children[
            :len(NEGATIVE_FAMILIES)
        ]
        holdout_child = generation_children[-1]

        resampling_children = resampling_sequences[
            world
        ].spawn(len(cfg.calibration_sizes))
        bootstrap_children = bootstrap_sequences[
            world
        ].spawn(len(cfg.calibration_sizes))

        family_records = {}
        for family, child in zip(
            NEGATIVE_FAMILIES, family_children
        ):
            family_records[family] = {
                "integer_seed": _integer_seed(child),
                "entropy": child.entropy,
                "spawn_key": list(child.spawn_key),
            }

        size_records = {}
        for size, resample_child, bootstrap_child in zip(
            cfg.calibration_sizes,
            resampling_children,
            bootstrap_children,
        ):
            size_records[str(size)] = {
                "resampling": {
                    "integer_seed": _integer_seed(
                        resample_child
                    ),
                    "entropy": resample_child.entropy,
                    "spawn_key": list(
                        resample_child.spawn_key
                    ),
                },
                "recall_bootstrap": {
                    "integer_seed": _integer_seed(
                        bootstrap_child
                    ),
                    "entropy": bootstrap_child.entropy,
                    "spawn_key": list(
                        bootstrap_child.spawn_key
                    ),
                },
            }

        records.append(
            {
                "world": world,
                "calibration_families": family_records,
                "holdout": {
                    "integer_seed": _integer_seed(
                        holdout_child
                    ),
                    "entropy": holdout_child.entropy,
                    "spawn_key": list(
                        holdout_child.spawn_key
                    ),
                },
                "sizes": size_records,
            }
        )
    return records


def generate_calibration_superpool(
    cfg: Config,
    world_seed_record: dict,
) -> Dict[str, np.ndarray]:
    core = cfg.core_config()
    output = {}

    for family in NEGATIVE_FAMILIES:
        seed = world_seed_record[
            "calibration_families"
        ][family]["integer_seed"]
        rng = np.random.default_rng(seed)
        parts = []
        remaining = cfg.calibration_superpool_per_family

        while remaining > 0:
            n = min(
                cfg.calibration_generation_batch_size,
                remaining,
            )
            scores, _, _ = m9.evaluate_negative_family(
                family, n, rng, core
            )
            parts.append(
                np.asarray(scores, dtype=np.float32)
            )
            remaining -= n

        values = np.concatenate(parts)
        if len(values) != cfg.calibration_superpool_per_family:
            raise RuntimeError(
                f"Wrong superpool size for {family}."
            )
        if not np.isfinite(values).all():
            raise RuntimeError(
                f"Non-finite calibration score in {family}."
            )
        output[family] = values

    return output


def generate_holdout_scores(
    cfg: Config,
    world_seed_record: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    holdout_seed = world_seed_record[
        "holdout"
    ]["integer_seed"]
    core = cfg.core_config(
        holdout_seed=holdout_seed
    )
    sequences = np.random.SeedSequence(
        holdout_seed
    ).spawn(cfg.holdout_batches)

    positive_records = []
    negative_records = []

    for batch, sequence in enumerate(sequences):
        positive, negative, _ = m9._evaluate_holdout_batch(
            batch,
            sequence,
            np.inf,
            core,
        )
        positive_records.extend(positive)
        negative_records.extend(negative)

    positive_df = pd.DataFrame(positive_records)
    negative_df = pd.DataFrame(negative_records)

    expected_positive = (
        len(POSITIVE_STRATA)
        * cfg.holdout_positive_per_stratum_total
    )
    expected_negative = (
        len(NEGATIVE_FAMILIES)
        * cfg.holdout_negative_per_family_total
    )
    if len(positive_df) != expected_positive:
        raise RuntimeError(
            f"Expected {expected_positive} positives, "
            f"got {len(positive_df)}."
        )
    if len(negative_df) != expected_negative:
        raise RuntimeError(
            f"Expected {expected_negative} negatives, "
            f"got {len(negative_df)}."
        )

    return positive_df, negative_df


def conservative_threshold_partition(
    sample_by_family: Dict[str, np.ndarray],
    target_fpr: float,
) -> tuple[float, dict, dict]:
    family_thresholds = {}
    allowed_counts = {}

    for family, sample in sample_by_family.items():
        values = np.asarray(sample)
        if not np.issubdtype(
            values.dtype, np.floating
        ):
            values = values.astype(np.float64)
        n = values.size
        allowed = int(
            math.floor(target_fpr * n + 1e-12)
        )
        if allowed >= n:
            threshold = -np.inf
        else:
            ascending_index = n - allowed - 1
            reference = np.partition(
                values, ascending_index
            )[ascending_index]
            threshold = np.nextafter(
                reference,
                np.array(np.inf, dtype=values.dtype),
                dtype=values.dtype,
            )
        family_thresholds[family] = float(threshold)
        allowed_counts[family] = allowed

    return (
        float(max(family_thresholds.values())),
        family_thresholds,
        allowed_counts,
    )


def _global_recall_bootstrap(
    successes: np.ndarray,
    ns: np.ndarray,
    replicates: int,
    seed: int,
) -> tuple[float, float]:
    successes = np.asarray(successes, dtype=np.int64)
    ns = np.asarray(ns, dtype=np.int64)
    probabilities = successes / ns
    rng = np.random.default_rng(seed)
    draws = rng.binomial(
        ns[None, :],
        probabilities[None, :],
        size=(replicates, len(ns)),
    )
    recall = np.mean(draws / ns[None, :], axis=1)
    return (
        float(np.quantile(recall, 0.05)),
        float(np.quantile(recall, 0.95)),
    )


def prepare_holdout_arrays(
    positive_df: pd.DataFrame,
    negative_df: pd.DataFrame,
) -> dict:
    positive_scores = {}
    positive_batches = {}
    for stratum in POSITIVE_STRATA:
        subset = positive_df[
            positive_df.stratum == stratum
        ].sort_values(["batch", "curve"])
        positive_scores[stratum] = (
            subset.score.to_numpy(dtype=np.float64)
        )
        positive_batches[stratum] = (
            subset.batch.to_numpy(dtype=np.int16)
        )

    negative_scores = {}
    for family in NEGATIVE_FAMILIES:
        subset = negative_df[
            negative_df.family == family
        ].sort_values(["batch", "curve"])
        negative_scores[family] = (
            subset.score.to_numpy(dtype=np.float64)
        )

    return {
        "positive_scores": positive_scores,
        "positive_batches": positive_batches,
        "negative_scores": negative_scores,
    }


def evaluate_threshold(
    threshold: float,
    holdout_arrays: dict,
    cfg: Config,
    bootstrap_seed: int,
) -> dict:
    fpr_details = {}
    fpr_control = True

    for family in NEGATIVE_FAMILIES:
        scores = holdout_arrays[
            "negative_scores"
        ][family]
        alerts = int(np.sum(scores >= threshold))
        upper = m2.clopper_pearson_upper(
            alerts, len(scores)
        )
        fpr_details[family] = {
            "alerts": alerts,
            "n": int(len(scores)),
            "rate": alerts / len(scores),
            "upper_95": upper,
        }
        if upper > cfg.holdout_fpr_upper_limit:
            fpr_control = False

    successes = []
    ns = []
    stratum_details = {}
    batch_successes = np.zeros(
        cfg.holdout_batches, dtype=np.int64
    )
    batch_ns = np.zeros(
        cfg.holdout_batches, dtype=np.int64
    )

    for stratum in POSITIVE_STRATA:
        scores = holdout_arrays[
            "positive_scores"
        ][stratum]
        batches = holdout_arrays[
            "positive_batches"
        ][stratum]
        hits = scores >= threshold
        x = int(hits.sum())
        n = int(len(hits))
        lower = m5.clopper_pearson_lower(x, n)
        successes.append(x)
        ns.append(n)
        stratum_details[stratum] = {
            "hits": x,
            "n": n,
            "rate": x / n,
            "lower_95": lower,
        }
        batch_successes += np.bincount(
            batches,
            weights=hits.astype(np.int64),
            minlength=cfg.holdout_batches,
        ).astype(np.int64)
        batch_ns += np.bincount(
            batches,
            minlength=cfg.holdout_batches,
        ).astype(np.int64)

    successes_array = np.asarray(successes)
    ns_array = np.asarray(ns)
    recall_point = float(
        np.mean(successes_array / ns_array)
    )
    recall_lower, recall_upper = (
        _global_recall_bootstrap(
            successes_array,
            ns_array,
            cfg.bootstrap_replicates_per_calibration,
            bootstrap_seed,
        )
    )
    good_strata = int(
        np.sum(
            [
                detail["lower_95"]
                >= cfg.minimum_stratum_recall_lower_ci
                for detail in stratum_details.values()
            ]
        )
    )
    batch_recall = batch_successes / batch_ns
    good_batches = int(
        np.sum(
            batch_recall
            >= cfg.batch_recall_threshold
        )
    )

    passed = bool(
        fpr_control
        and recall_lower
        >= cfg.minimum_global_recall_lower_ci
        and good_strata >= cfg.minimum_good_strata
        and good_batches >= cfg.minimum_good_batches
    )

    return {
        "threshold": float(threshold),
        "fpr_control": bool(fpr_control),
        "recall_point": recall_point,
        "recall_lower_95": recall_lower,
        "recall_upper_95": recall_upper,
        "good_strata": good_strata,
        "good_batches": good_batches,
        "pass": passed,
        "fpr_details": fpr_details,
        "stratum_details": stratum_details,
    }


def run_calibration_resamples(
    cfg: Config,
    world_seed_record: dict,
    superpool: Dict[str, np.ndarray],
    holdout_arrays: dict,
) -> pd.DataFrame:
    rows = []

    for size in cfg.calibration_sizes:
        resampling_seed = world_seed_record[
            "sizes"
        ][str(size)]["resampling"]["integer_seed"]
        bootstrap_seed_root = world_seed_record[
            "sizes"
        ][str(size)]["recall_bootstrap"][
            "integer_seed"
        ]
        rng = np.random.default_rng(resampling_seed)
        bootstrap_sequences = np.random.SeedSequence(
            bootstrap_seed_root
        ).spawn(cfg.resamples_per_size)

        for resample in range(cfg.resamples_per_size):
            sampled = {}
            for family in NEGATIVE_FAMILIES:
                pool = superpool[family]
                indices = rng.integers(
                    0, len(pool), size=size
                )
                sampled[family] = pool[indices]

            threshold, family_thresholds, _ = (
                conservative_threshold_partition(
                    sampled,
                    cfg.calibration_fpr_target,
                )
            )
            evaluation = evaluate_threshold(
                threshold,
                holdout_arrays,
                cfg,
                _integer_seed(
                    bootstrap_sequences[resample]
                ),
            )

            driver = max(
                family_thresholds,
                key=family_thresholds.get,
            )
            rows.append(
                {
                    "world": world_seed_record["world"],
                    "calibration_size": size,
                    "resample": resample,
                    "threshold": threshold,
                    "threshold_driver": driver,
                    "fpr_control": evaluation[
                        "fpr_control"
                    ],
                    "recall_point": evaluation[
                        "recall_point"
                    ],
                    "recall_lower_95": evaluation[
                        "recall_lower_95"
                    ],
                    "recall_upper_95": evaluation[
                        "recall_upper_95"
                    ],
                    "good_strata": evaluation[
                        "good_strata"
                    ],
                    "good_batches": evaluation[
                        "good_batches"
                    ],
                    "pass": evaluation["pass"],
                }
            )

    return pd.DataFrame(rows)


def summarize_results(
    cfg: Config,
    calibration_results: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    summary_rows = []

    for world in range(cfg.world_count):
        for size in cfg.calibration_sizes:
            subset = calibration_results[
                (calibration_results.world == world)
                & (
                    calibration_results.calibration_size
                    == size
                )
            ]
            q05 = float(
                subset.threshold.quantile(0.05)
            )
            q95 = float(
                subset.threshold.quantile(0.95)
            )
            summary_rows.append(
                {
                    "world": world,
                    "calibration_size": size,
                    "threshold_median": float(
                        subset.threshold.median()
                    ),
                    "threshold_q05": q05,
                    "threshold_q95": q95,
                    "threshold_width_90": q95 - q05,
                    "pass_count": int(
                        subset["pass"].sum()
                    ),
                    "pass_rate": float(
                        subset["pass"].mean()
                    ),
                    "fpr_pass_rate": float(
                        subset.fpr_control.mean()
                    ),
                    "recall_median": float(
                        subset.recall_point.median()
                    ),
                    "recall_lower_median": float(
                        subset.recall_lower_95.median()
                    ),
                    "recall_lower_q90": float(
                        subset.recall_lower_95.quantile(
                            0.90
                        )
                    ),
                }
            )

    summary_df = pd.DataFrame(summary_rows)

    width_ratios = []
    for world in range(cfg.world_count):
        w2 = float(
            summary_df[
                (summary_df.world == world)
                & (
                    summary_df.calibration_size
                    == 2_000
                )
            ].threshold_width_90.iloc[0]
        )
        w50 = float(
            summary_df[
                (summary_df.world == world)
                & (
                    summary_df.calibration_size
                    == 50_000
                )
            ].threshold_width_90.iloc[0]
        )
        ratio = (
            w50 / w2
            if w2 > 0.0
            else (0.0 if w50 == 0.0 else np.inf)
        )
        width_ratios.append(ratio)

    median_width_ratio = float(
        np.median(width_ratios)
    )

    pooled = {}
    for size in cfg.calibration_sizes:
        subset = calibration_results[
            calibration_results.calibration_size
            == size
        ]
        passes = int(subset["pass"].sum())
        n = int(len(subset))
        pooled[str(size)] = {
            "pass_count": passes,
            "n": n,
            "pass_rate": passes / n,
            "pass_rate_lower_95": (
                m5.clopper_pearson_lower(
                    passes, n
                )
            ),
            "pass_rate_upper_95": (
                m2.clopper_pearson_upper(
                    passes, n
                )
            ),
            "fpr_pass_rate": float(
                subset.fpr_control.mean()
            ),
            "threshold_median": float(
                subset.threshold.median()
            ),
            "recall_median": float(
                subset.recall_point.median()
            ),
            "recall_lower_q90": float(
                subset.recall_lower_95.quantile(
                    0.90
                )
            ),
        }

    worlds_50k_high_pass = int(
        np.sum(
            summary_df[
                summary_df.calibration_size == 50_000
            ].pass_rate
            >= cfg.primary_50k_world_pass_rate
        )
    )

    calibration_primary = bool(
        median_width_ratio
        <= cfg.primary_width_ratio_limit
        and worlds_50k_high_pass >= 2
        and pooled["50000"][
            "pass_rate_lower_95"
        ]
        >= cfg.primary_50k_aggregate_lower_pass_rate
        and pooled["2000"]["pass_rate"]
        <= cfg.primary_2k_aggregate_max_pass_rate
    )

    strong_fail = bool(
        median_width_ratio
        <= cfg.primary_width_ratio_limit
        and pooled["50000"]["pass_rate"]
        <= cfg.strong_fail_50k_max_pass_rate
        and pooled["50000"]["recall_lower_q90"]
        < cfg.strong_fail_50k_recall_lower_q90
    )

    if calibration_primary:
        verdict = "PASS_CALIBRATION_PRIMARY"
    elif strong_fail:
        verdict = (
            "STRONG_FAIL_CALIBRATION_NOT_PRIMARY"
        )
    else:
        verdict = "INCONCLUSIVE"

    prediction = {
        "width_ratio_confirmed": bool(
            median_width_ratio
            <= cfg.predicted_width_ratio_limit
        ),
        "all_pass_rates_le_0_20": bool(
            all(
                pooled[str(size)]["pass_rate"]
                <= 0.20
                for size in cfg.calibration_sizes
            )
        ),
        "median_50k_recall_in_range": bool(
            0.50
            <= pooled["50000"]["recall_median"]
            <= 0.56
        ),
        "verdict_confirmed": (
            verdict
            == "STRONG_FAIL_CALIBRATION_NOT_PRIMARY"
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    verdict_details = {
        "verdict": verdict,
        "median_width_ratio_50k_to_2k": (
            median_width_ratio
        ),
        "width_ratios_by_world": width_ratios,
        "worlds_50k_pass_rate_ge_0_80": (
            worlds_50k_high_pass
        ),
        "pooled": pooled,
        "prediction": prediction,
    }
    return summary_df, verdict_details


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)
    return digest.hexdigest()


def write_environment(path: Path) -> None:
    import numpy
    import pandas
    import scipy
    import sklearn

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m2_dependency_sha256": sha256_file(
            M2_DIR / "arara_m2.py"
        ),
        "m5_dependency_sha256": sha256_file(
            M5_DIR / "arara_m5.py"
        ),
        "m9_dependency_sha256": sha256_file(
            M9_DIR / "arara_m9.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
