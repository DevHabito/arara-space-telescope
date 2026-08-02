
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
    version: str = "23.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    onset_offsets: tuple[int, ...] = (0, 1, 2)

    calibration_seed: int = 2026081801
    holdout_root_seed: int = 2026081802
    aggregate_bootstrap_root_seed: int = 2026081803

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
    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    bootstrap_replicates: int = 10_000

    prediction_ranges: tuple[tuple[int, float, float], ...] = (
        (0, 0.64, 0.70),
        (1, 0.62, 0.68),
        (2, 0.58, 0.63),
    )

    def analysis_config(self) -> m22.Config:
        return m22.Config(
            version=self.version,
            fixed_snr=self.fixed_snr,
            target_fraction=self.target_fraction,
            onset_offsets=self.onset_offsets,
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
            minimum_replication_passes=self.minimum_holdout_passes,
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
            prediction_ranges=self.prediction_ranges,
        )


def _integer_seed(sequence: np.random.SeedSequence) -> int:
    return int(
        sequence.generate_state(1, dtype=np.uint32)[0]
    )


def build_seed_plan(cfg: Config) -> dict:
    calibration_children = np.random.SeedSequence(
        cfg.calibration_seed
    ).spawn(len(NEGATIVE_FAMILIES))

    calibration = {}
    for family, child in zip(
        NEGATIVE_FAMILIES, calibration_children
    ):
        calibration[family] = {
            "integer_seed": _integer_seed(child),
            "entropy": child.entropy,
            "spawn_key": list(child.spawn_key),
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


def calibration_core(
    cfg: Config,
) -> m22.m9.Config:
    analysis = cfg.analysis_config()
    seed_record = {
        "replication": 0,
        "seeds": {
            "development": cfg.calibration_seed,
            "holdout": cfg.calibration_seed + 1,
            "bootstrap": cfg.calibration_seed + 2,
        },
    }
    return analysis.core_config(seed_record)


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> Dict[int, np.ndarray]:
    if family not in NEGATIVE_FAMILIES:
        raise ValueError(family)

    seed = seed_plan["calibration"][family][
        "integer_seed"
    ]
    rng = np.random.default_rng(seed)
    analysis = cfg.analysis_config()
    core = calibration_core(cfg)

    parts = {
        offset: [] for offset in cfg.onset_offsets
    }
    remaining = cfg.calibration_negatives_per_family

    while remaining > 0:
        n = min(cfg.calibration_batch_size, remaining)
        score_map = m22.score_negative_offsets(
            family,
            n,
            rng,
            analysis,
            core,
        )
        for offset in cfg.onset_offsets:
            values = np.asarray(
                score_map[offset], dtype=np.float32
            )
            if not np.isfinite(values).all():
                raise RuntimeError(
                    f"Non-finite score in {family}, "
                    f"offset {offset}."
                )
            parts[offset].append(values)
        remaining -= n

    output = {
        offset: np.concatenate(parts[offset])
        for offset in cfg.onset_offsets
    }
    for offset, values in output.items():
        if (
            len(values)
            != cfg.calibration_negatives_per_family
        ):
            raise RuntimeError(
                f"Wrong calibration size in {family}, "
                f"offset {offset}."
            )
    return output


def freeze_thresholds(
    cfg: Config,
    family_score_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame]:
    loaded = {}
    for family in NEGATIVE_FAMILIES:
        path = family_score_paths[family]
        with np.load(path) as data:
            loaded[family] = {
                offset: data[f"offset_{offset}"].copy()
                for offset in cfg.onset_offsets
            }

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []

    for offset in cfg.onset_offsets:
        by_family = {
            family: loaded[family][offset]
            for family in NEGATIVE_FAMILIES
        }
        threshold, specific, allowed = (
            m22.m2.conservative_threshold(
                by_family,
                cfg.development_fpr_target,
            )
        )
        thresholds[str(offset)] = float(threshold)
        family_thresholds[str(offset)] = specific
        allowed_counts[str(offset)] = allowed

        for family in NEGATIVE_FAMILIES:
            values = by_family[family]
            alerts = int(np.sum(values >= threshold))
            if alerts > allowed[family]:
                raise RuntimeError(
                    f"Calibration FPR violation: "
                    f"{family}, offset {offset}."
                )
            rows.append(
                {
                    "offset": offset,
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

    details = {
        "thresholds": thresholds,
        "family_thresholds": family_thresholds,
        "allowed_counts": allowed_counts,
        "calibration_negatives_per_family": (
            cfg.calibration_negatives_per_family
        ),
    }
    return details, pd.DataFrame(rows)


def run_holdout(
    cfg: Config,
    holdout_seed_record: dict,
    thresholds: dict,
) -> dict:
    analysis = cfg.analysis_config()
    return m22.evaluate_holdout(
        analysis,
        holdout_seed_record,
        thresholds,
    )


def aggregate_results(
    cfg: Config,
    holdout_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
) -> dict:
    offset_details = {}
    bootstrap_frames = []
    prediction_ranges = {
        offset: (low, high)
        for offset, low, high in cfg.prediction_ranges
    }
    sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(len(cfg.onset_offsets))

    for offset_index, offset in enumerate(
        cfg.onset_offsets
    ):
        rep = holdout_summary[
            holdout_summary.offset == offset
        ].sort_values("replication")

        if len(rep) != cfg.holdout_count:
            raise RuntimeError(
                f"Expected {cfg.holdout_count} "
                f"holdouts for offset {offset}."
            )

        counts = []
        ns = []
        for holdout in range(cfg.holdout_count):
            subset = stratum_summary[
                (stratum_summary.offset == offset)
                & (
                    stratum_summary.replication
                    == holdout
                )
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

        seed = _integer_seed(sequences[offset_index])
        boot = m22.m15.hierarchical_bootstrap(
            np.asarray(counts),
            np.asarray(ns),
            cfg.bootstrap_replicates,
            seed,
        )
        bootstrap_frames.append(
            pd.DataFrame(
                {
                    "offset": offset,
                    "replicate": np.arange(
                        cfg.bootstrap_replicates
                    ),
                    "recall": boot,
                }
            )
        )

        point = float(rep.recall_point.mean())
        lower = float(np.quantile(boot, 0.05))
        upper = float(np.quantile(boot, 0.95))
        pass_count = int(rep["pass"].sum())
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
            pass_count >= cfg.minimum_holdout_passes
            and lower
            >= cfg.minimum_global_recall_lower_ci
            and fpr_robust
        )
        strong_fail = bool(
            pass_count <= 2
            or upper
            <= cfg.minimum_global_recall_lower_ci
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
        low, high = prediction_ranges[offset]
        offset_details[str(offset)] = {
            "offset": offset,
            "verdict": verdict,
            "aggregate_recall_point": point,
            "aggregate_recall_lower_95": lower,
            "aggregate_recall_upper_95": upper,
            "holdout_pass_count": pass_count,
            "fpr_pass_holdout_count": fpr_pass_count,
            "extreme_fpr_violation": extreme,
            "fpr_robust": fpr_robust,
            "prediction_recall_in_range": bool(
                low <= point <= high
            ),
        }

    verdicts = {
        offset: offset_details[str(offset)]["verdict"]
        for offset in cfg.onset_offsets
    }

    if all(
        verdicts[offset] == "PASS"
        for offset in cfg.onset_offsets
    ):
        overall = "PASS_LATE_ONSET_PLUS2"
    elif (
        verdicts[0] == "PASS"
        and verdicts[1] == "PASS"
    ):
        overall = "PASS_LATE_ONSET_PLUS1"
    elif (
        verdicts[0] == "STRONG_FAIL"
        or verdicts[1] == "STRONG_FAIL"
    ):
        overall = "STRONG_FAIL_STABLE_ONSET"
    else:
        overall = "INCONCLUSIVE"

    recalls = [
        offset_details[str(offset)][
            "aggregate_recall_point"
        ]
        for offset in cfg.onset_offsets
    ]
    monotonic = bool(
        recalls[0] > recalls[1] > recalls[2]
    )

    prediction = {
        "zero_pass": verdicts[0] == "PASS",
        "plus1_pass": verdicts[1] == "PASS",
        "plus2_inconclusive": (
            verdicts[2] == "INCONCLUSIVE"
        ),
        "all_fpr_robust": bool(
            all(
                offset_details[str(offset)][
                    "fpr_robust"
                ]
                for offset in cfg.onset_offsets
            )
        ),
        "strictly_decreasing_recall": monotonic,
        "overall_verdict_confirmed": (
            overall == "PASS_LATE_ONSET_PLUS1"
        ),
        "all_recall_ranges_confirmed": bool(
            all(
                offset_details[str(offset)][
                    "prediction_recall_in_range"
                ]
                for offset in cfg.onset_offsets
            )
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": overall,
        "offset_details": offset_details,
        "prediction": prediction,
        "bootstrap_df": pd.concat(
            bootstrap_frames, ignore_index=True
        ),
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
