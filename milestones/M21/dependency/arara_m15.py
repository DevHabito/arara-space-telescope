
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
M9_DIR = ROOT / "m9"
if str(M9_DIR) not in sys.path:
    sys.path.insert(0, str(M9_DIR))

import arara_m9 as m9


@dataclass(frozen=True)
class Config:
    version: str = "15.0"
    fixed_snr: float = 12.0
    target_fraction: float = 0.50
    replication_count: int = 10
    replication_root_seed: int = 2026081001
    aggregate_bootstrap_seed: int = 2026081002

    development_base_fields_per_shape_context: int = 1000
    development_negatives_per_family: int = 2000
    holdout_positive_per_stratum_total: int = 2500
    holdout_negative_per_family_total: int = 5000
    holdout_batches: int = 20
    holdout_positive_per_stratum_per_batch: int = 125
    holdout_negative_per_family_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    extreme_fpr_upper_limit: float = 0.015
    minimum_replication_passes: int = 8
    minimum_fpr_pass_replications: int = 9

    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    bootstrap_replicates: int = 10_000


def build_seed_plan(cfg: Config) -> list[dict]:
    root = np.random.SeedSequence(cfg.replication_root_seed)
    replication_sequences = root.spawn(cfg.replication_count)
    records = []

    for index, replication_sequence in enumerate(
        replication_sequences
    ):
        children = replication_sequence.spawn(3)
        labels = ("development", "holdout", "bootstrap")
        seeds = {}
        child_records = {}

        for label, child in zip(labels, children):
            integer = int(
                child.generate_state(
                    1, dtype=np.uint32
                )[0]
            )
            seeds[label] = integer
            child_records[label] = {
                "integer_seed": integer,
                "entropy": child.entropy,
                "spawn_key": list(child.spawn_key),
            }

        records.append(
            {
                "replication": index,
                "replication_entropy": (
                    replication_sequence.entropy
                ),
                "replication_spawn_key": list(
                    replication_sequence.spawn_key
                ),
                "seeds": seeds,
                "children": child_records,
            }
        )

    return records


def core_config(
    cfg: Config,
    seed_record: dict,
) -> m9.Config:
    seeds = seed_record["seeds"]
    return m9.Config(
        version=f"{cfg.version}-r{seed_record['replication']:02d}",
        snr_levels=(cfg.fixed_snr,),
        target_fraction=cfg.target_fraction,
        development_root_seed=seeds["development"],
        holdout_root_seed=seeds["holdout"],
        bootstrap_seed=seeds["bootstrap"],
        development_base_fields_per_shape_context=(
            cfg.development_base_fields_per_shape_context
        ),
        development_negatives_per_family=(
            cfg.development_negatives_per_family
        ),
        holdout_positive_per_stratum_total=(
            cfg.holdout_positive_per_stratum_total
        ),
        holdout_negative_per_family_total=(
            cfg.holdout_negative_per_family_total
        ),
        holdout_batches=cfg.holdout_batches,
        holdout_positive_per_stratum_per_batch=(
            cfg.holdout_positive_per_stratum_per_batch
        ),
        holdout_negative_per_family_per_batch=(
            cfg.holdout_negative_per_family_per_batch
        ),
        development_fpr_target=(
            cfg.development_fpr_target
        ),
        holdout_fpr_upper_limit=(
            cfg.holdout_fpr_upper_limit
        ),
        minimum_global_recall_lower_ci=(
            cfg.minimum_global_recall_lower_ci
        ),
        minimum_stratum_recall_lower_ci=(
            cfg.minimum_stratum_recall_lower_ci
        ),
        minimum_good_strata=cfg.minimum_good_strata,
        minimum_good_batches=cfg.minimum_good_batches,
        batch_recall_threshold=(
            cfg.batch_recall_threshold
        ),
        maximum_adjacent_point_drop=0.02,
        strong_fail_snr12_recall_upper=0.50,
        bootstrap_replicates=cfg.bootstrap_replicates,
        predicted_first_passing_snr=cfg.fixed_snr,
    )


def run_replication(
    cfg: Config,
    seed_record: dict,
) -> dict:
    core = core_config(cfg, seed_record)
    development_details, development_df = (
        m9.evaluate_development(core)
    )
    threshold = float(development_details["threshold"])
    holdout = m9.evaluate_holdout(threshold, core)

    level = holdout["verdict"]["level_details"][
        str(cfg.fixed_snr)
    ]
    negative_summary = holdout["summary_df"][
        holdout["summary_df"].kind == "negative"
    ].copy()
    maximum_fpr_upper = float(
        negative_summary.cp_upper_95.max()
    )
    fpr_pass = bool(
        np.all(
            negative_summary.cp_upper_95
            <= cfg.holdout_fpr_upper_limit
        )
    )
    replication_pass = bool(level["pass"])

    stratum_summary = holdout["summary_df"][
        holdout["summary_df"].kind == "positive"
    ].copy()

    record = {
        "replication": seed_record["replication"],
        "threshold": threshold,
        "recall_point": float(level["recall_point"]),
        "recall_lower_95": float(
            level["recall_lower_95"]
        ),
        "recall_upper_95": float(
            level["recall_upper_95"]
        ),
        "good_strata": int(level["good_strata"]),
        "good_batches": int(level["good_batches"]),
        "fpr_pass": fpr_pass,
        "maximum_fpr_upper_95": maximum_fpr_upper,
        "pass": replication_pass,
        "development_details": development_details,
        "development_df": development_df,
        "summary_df": holdout["summary_df"],
        "batch_df": holdout["batch_df"],
        "secondary_df": holdout["secondary_df"],
        "stratum_summary": stratum_summary,
        "verdict": holdout["verdict"],
    }
    return record


def hierarchical_bootstrap(
    replication_stratum_counts: np.ndarray,
    replication_stratum_ns: np.ndarray,
    replicates: int,
    seed: int,
) -> np.ndarray:
    counts = np.asarray(
        replication_stratum_counts, dtype=np.int64
    )
    ns = np.asarray(
        replication_stratum_ns, dtype=np.int64
    )
    if counts.shape != ns.shape:
        raise ValueError("Count and n matrices differ.")
    if counts.ndim != 2:
        raise ValueError(
            "Matrices must have shape (replications, strata)."
        )
    if np.any(counts < 0) or np.any(counts > ns):
        raise ValueError("Invalid binomial counts.")
    if np.any(ns <= 0):
        raise ValueError("All n values must be positive.")

    rng = np.random.default_rng(seed)
    replication_count, stratum_count = counts.shape
    probabilities = counts / ns
    output = np.empty(replicates, dtype=np.float64)

    for b in range(replicates):
        selected = rng.integers(
            0,
            replication_count,
            size=replication_count,
        )
        total = 0.0
        for index in selected:
            draws = rng.binomial(
                ns[index],
                probabilities[index],
            )
            total += np.mean(draws / ns[index])
        output[b] = total / replication_count

    return output


def aggregate_results(
    cfg: Config,
    replication_summaries: pd.DataFrame,
    stratum_counts: np.ndarray,
    stratum_ns: np.ndarray,
) -> dict:
    boot = hierarchical_bootstrap(
        stratum_counts,
        stratum_ns,
        cfg.bootstrap_replicates,
        cfg.aggregate_bootstrap_seed,
    )
    point = float(
        replication_summaries.recall_point.mean()
    )
    lower = float(np.quantile(boot, 0.05))
    upper = float(np.quantile(boot, 0.95))

    pass_count = int(
        replication_summaries["pass"].sum()
    )
    fpr_pass_count = int(
        replication_summaries.fpr_pass.sum()
    )
    extreme_fpr_violation = bool(
        np.any(
            replication_summaries.maximum_fpr_upper_95
            > cfg.extreme_fpr_upper_limit
        )
    )
    fpr_robust = bool(
        fpr_pass_count
        >= cfg.minimum_fpr_pass_replications
        and not extreme_fpr_violation
    )

    victory = bool(
        pass_count >= cfg.minimum_replication_passes
        and lower >= cfg.minimum_global_recall_lower_ci
        and fpr_robust
    )
    strong_failure = bool(
        pass_count <= 2
        or upper <= cfg.minimum_global_recall_lower_ci
        or extreme_fpr_violation
    )
    verdict = (
        "PASS"
        if victory
        else (
            "STRONG_FAIL"
            if strong_failure
            else "INCONCLUSIVE"
        )
    )

    prediction_pass_count = 5 <= pass_count <= 7
    prediction_recall = 0.59 <= point <= 0.63
    prediction_verdict = verdict == "INCONCLUSIVE"

    return {
        "verdict": verdict,
        "aggregate_recall_point": point,
        "aggregate_recall_lower_95": lower,
        "aggregate_recall_upper_95": upper,
        "replication_pass_count": pass_count,
        "fpr_pass_replication_count": fpr_pass_count,
        "extreme_fpr_violation": extreme_fpr_violation,
        "fpr_robust": fpr_robust,
        "minimum_replication_passes": (
            cfg.minimum_replication_passes
        ),
        "prediction_pass_count_confirmed": (
            prediction_pass_count
        ),
        "prediction_recall_confirmed": (
            prediction_recall
        ),
        "prediction_verdict_confirmed": (
            prediction_verdict
        ),
        "prediction_fully_confirmed": bool(
            prediction_pass_count
            and prediction_recall
            and prediction_verdict
        ),
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
        "m9_dependency_sha256": sha256_file(
            M9_DIR / "arara_m9.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
