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
import arara_m25_dependency as m25

POSITIVE_STRATA = m22.POSITIVE_STRATA
NEGATIVE_FAMILIES = m22.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "27.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    selection_start: int = 50
    guard_length: int = 1
    confirmation_length: int = 16

    calibration_seed: int = 2026082201
    holdout_root_seed: int = 2026082202
    aggregate_bootstrap_root_seed: int = 2026082203

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

    prediction_threshold_low: float = 20.0
    prediction_threshold_high: float = 26.0
    prediction_recall_low: float = 0.45
    prediction_recall_high: float = 0.62
    prediction_pass_count_low: int = 2
    prediction_pass_count_high: int = 6

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
            minimum_global_recall_lower_ci=self.minimum_global_recall_lower_ci,
            minimum_stratum_recall_lower_ci=self.minimum_stratum_recall_lower_ci,
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


def evaluate_positive_panel(
    panel: m22.m9.PositivePanel,
    cfg: Config,
    core: m22.m9.Config,
) -> np.ndarray:
    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    y = panel.base_y.copy()
    y[:, 0, :] += raw_signal
    residual, processed_signal, _ = m22.m5.sbw_with_signal_operator(
        y, raw_signal, core.data_config()
    )
    return m25.confirmation_matched_filter(
        residual, processed_signal, panel.t100, cfg
    )


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m22.m9.Config,
) -> tuple[np.ndarray, np.ndarray]:
    data_cfg = core.data_config()
    data = m22.m2.generate_negative_family(family, n, rng, data_cfg)
    virtual_signal, _, _, _ = m22.m5.generate_virtual_hypotheses(
        n, rng, data_cfg
    )
    endpoint = m22.m9.time_at_fraction(virtual_signal, cfg.target_fraction)
    residual, processed_template, _ = m22.m5.sbw_with_signal_operator(
        data.y, virtual_signal, data_cfg
    )
    score = m25.confirmation_matched_filter(
        residual, processed_template, endpoint, cfg
    )
    return score, endpoint


def generate_calibration_family(
    family: str,
    cfg: Config,
    seed_plan: dict,
) -> dict:
    seed = seed_plan["calibration"][family]["integer_seed"]
    rng = np.random.default_rng(seed)
    core = calibration_core(cfg)
    score_parts, endpoint_parts = [], []
    remaining = cfg.calibration_negatives_per_family

    while remaining > 0:
        n = min(cfg.calibration_batch_size, remaining)
        score, endpoint = evaluate_negative_family(family, n, rng, cfg, core)
        score_parts.append(np.asarray(score, dtype=np.float32))
        endpoint_parts.append(np.asarray(endpoint, dtype=np.int16))
        remaining -= n

    output = {
        "score": np.concatenate(score_parts),
        "endpoint": np.concatenate(endpoint_parts),
    }
    if any(
        len(values) != cfg.calibration_negatives_per_family
        for values in output.values()
    ):
        raise RuntimeError(f"Wrong calibration size for {family}.")
    if not np.isfinite(output["score"]).all():
        raise RuntimeError(f"Non-finite calibration score: {family}.")
    return output


def freeze_threshold(
    cfg: Config,
    family_paths: Dict[str, Path],
) -> tuple[dict, pd.DataFrame]:
    scores = {}
    for family in NEGATIVE_FAMILIES:
        with np.load(family_paths[family]) as data:
            scores[family] = data["score"].copy()

    threshold, family_specific, allowed = m22.m2.conservative_threshold(
        scores, cfg.development_fpr_target
    )
    rows = []
    for family in NEGATIVE_FAMILIES:
        values = scores[family]
        alerts = int(np.sum(values >= threshold))
        if alerts > allowed[family]:
            raise RuntimeError(f"Calibration count exceeded: {family}.")
        rows.append(
            {
                "family": family,
                "threshold": threshold,
                "family_specific_threshold": family_specific[family],
                "alerts": alerts,
                "n": len(values),
                "allowed": allowed[family],
                "rate": alerts / len(values),
            }
        )
    return (
        {
            "threshold": float(threshold),
            "family_thresholds": family_specific,
            "allowed_counts": allowed,
            "calibration_negatives_per_family": cfg.calibration_negatives_per_family,
        },
        pd.DataFrame(rows),
    )


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
        s: np.zeros(cfg.holdout_batches, dtype=np.int64)
        for s in POSITIVE_STRATA
    }
    positive_ns = {
        s: np.zeros(cfg.holdout_batches, dtype=np.int64)
        for s in POSITIVE_STRATA
    }
    negative_counts = {f: 0 for f in NEGATIVE_FAMILIES}
    negative_ns = {f: 0 for f in NEGATIVE_FAMILIES}
    positive_score_parts, negative_score_parts = [], []

    for batch, sequence in enumerate(batch_sequences):
        children = sequence.spawn(len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES))
        rngs = [np.random.default_rng(child) for child in children]

        for stratum, rng in zip(POSITIVE_STRATA, rngs[: len(POSITIVE_STRATA)]):
            shape, context = stratum.split("__")
            panel = m22.m9.generate_positive_panel(
                shape,
                context,
                cfg.holdout_positive_per_stratum_per_batch,
                rng,
                core,
            )
            score = evaluate_positive_panel(panel, cfg, core)
            hits = score >= threshold
            positive_counts[stratum][batch] += int(hits.sum())
            positive_ns[stratum][batch] += len(hits)
            positive_score_parts.append(score.astype(np.float32))

        for family, rng in zip(
            NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA) :]
        ):
            score, endpoint = evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            alerts = score >= threshold
            negative_counts[family] += int(alerts.sum())
            negative_ns[family] += len(alerts)
            negative_score_parts.append(score.astype(np.float32))

    negative_rows = []
    fpr_pass = True
    maximum_fpr_upper = 0.0
    for family in NEGATIVE_FAMILIES:
        x, n = negative_counts[family], negative_ns[family]
        upper = m22.m2.clopper_pearson_upper(x, n)
        maximum_fpr_upper = max(maximum_fpr_upper, upper)
        fpr_pass &= upper <= cfg.holdout_fpr_upper_limit
        negative_rows.append(
            {
                "family": family,
                "alerts": x,
                "n": n,
                "rate": x / n,
                "cp_upper_95": upper,
            }
        )

    stratum_rows, batch_rows = [], []
    successes, ns = [], []
    good_strata = 0
    hits_by_stratum = {}

    for stratum in POSITIVE_STRATA:
        x = int(positive_counts[stratum].sum())
        n = int(positive_ns[stratum].sum())
        lower = m22.m5.clopper_pearson_lower(x, n)
        good_strata += int(lower >= cfg.minimum_stratum_recall_lower_ci)
        successes.append(x)
        ns.append(n)
        hits = np.zeros(n, dtype=bool)
        hits[:x] = True
        hits_by_stratum[stratum] = hits
        stratum_rows.append(
            {
                "stratum": stratum,
                "hits": x,
                "n": n,
                "recall": x / n,
                "recall_cp_lower_95": lower,
            }
        )

    boot = m22.m5.stratified_bootstrap_recall(
        hits_by_stratum,
        cfg.bootstrap_replicates,
        seed_record["seeds"]["bootstrap"],
    )
    recall_point = float(np.mean(np.asarray(successes) / np.asarray(ns)))
    recall_lower = float(np.quantile(boot, 0.05))
    recall_upper = float(np.quantile(boot, 0.95))

    good_batches = 0
    for batch in range(cfg.holdout_batches):
        hits = sum(positive_counts[s][batch] for s in POSITIVE_STRATA)
        n = sum(positive_ns[s][batch] for s in POSITIVE_STRATA)
        recall = hits / n
        good_batches += int(recall >= cfg.batch_recall_threshold)
        batch_rows.append(
            {"batch": batch, "hits": hits, "n": n, "recall": recall}
        )

    passed = bool(
        fpr_pass
        and recall_lower >= cfg.minimum_global_recall_lower_ci
        and good_strata >= cfg.minimum_good_strata
        and good_batches >= cfg.minimum_good_batches
    )

    positive_scores = np.concatenate(positive_score_parts)
    negative_scores = np.concatenate(negative_score_parts)
    labels = np.concatenate(
        [
            np.ones(len(positive_scores), dtype=int),
            np.zeros(len(negative_scores), dtype=int),
        ]
    )
    values = np.concatenate([positive_scores, negative_scores])

    summary = {
        "replication": seed_record["replication"],
        "threshold": threshold,
        "recall_point": recall_point,
        "recall_lower_95": recall_lower,
        "recall_upper_95": recall_upper,
        "good_strata": good_strata,
        "good_batches": good_batches,
        "fpr_pass": bool(fpr_pass),
        "maximum_fpr_upper_95": maximum_fpr_upper,
        "pass": passed,
        "auroc": float(roc_auc_score(labels, values)),
        "average_precision": float(average_precision_score(labels, values)),
    }
    return {
        "summary": summary,
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
    }


def aggregate_results(
    cfg: Config,
    holdout_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
    frozen_threshold: float,
) -> dict:
    rep = holdout_summary.sort_values("replication")
    if len(rep) != cfg.holdout_count:
        raise RuntimeError("Wrong number of holdouts.")

    counts, ns = [], []
    for holdout in range(cfg.holdout_count):
        subset = stratum_summary[
            stratum_summary.replication == holdout
        ].set_index("stratum")
        counts.append([int(subset.loc[s, "hits"]) for s in POSITIVE_STRATA])
        ns.append([int(subset.loc[s, "n"]) for s in POSITIVE_STRATA])

    boot = m22.m15.hierarchical_bootstrap(
        np.asarray(counts),
        np.asarray(ns),
        cfg.bootstrap_replicates,
        cfg.aggregate_bootstrap_root_seed,
    )
    recall_point = float(rep.recall_point.mean())
    recall_lower = float(np.quantile(boot, 0.05))
    recall_upper = float(np.quantile(boot, 0.95))
    pass_count = int(rep["pass"].sum())
    fpr_pass_count = int(rep.fpr_pass.sum())
    extreme = bool(
        np.any(rep.maximum_fpr_upper_95 > cfg.extreme_fpr_upper_limit)
    )
    fpr_robust = bool(
        fpr_pass_count >= cfg.minimum_fpr_pass_holdouts and not extreme
    )

    passed = bool(
        pass_count >= cfg.minimum_holdout_passes
        and recall_lower >= cfg.minimum_global_recall_lower_ci
        and fpr_robust
    )
    strong_fail = bool(
        pass_count <= 2
        or recall_upper <= cfg.minimum_global_recall_lower_ci
        or extreme
    )
    verdict = (
        "PASS_EXACT_ONSET_16_CONFIRMATION"
        if passed
        else (
            "STRONG_FAIL_EXACT_ONSET_16_CONFIRMATION"
            if strong_fail
            else "INCONCLUSIVE"
        )
    )

    prediction = {
        "threshold_in_range": bool(
            cfg.prediction_threshold_low
            <= frozen_threshold
            <= cfg.prediction_threshold_high
        ),
        "recall_in_range": bool(
            cfg.prediction_recall_low
            <= recall_point
            <= cfg.prediction_recall_high
        ),
        "pass_count_in_range": bool(
            cfg.prediction_pass_count_low
            <= pass_count
            <= cfg.prediction_pass_count_high
        ),
        "verdict_confirmed": verdict == "INCONCLUSIVE",
    }
    prediction["fully_confirmed"] = bool(all(prediction.values()))

    return {
        "verdict": verdict,
        "frozen_threshold": frozen_threshold,
        "aggregate_recall_point": recall_point,
        "aggregate_recall_lower_95": recall_lower,
        "aggregate_recall_upper_95": recall_upper,
        "holdout_pass_count": pass_count,
        "fpr_pass_holdout_count": fpr_pass_count,
        "fpr_robust": fpr_robust,
        "extreme_fpr_violation": extreme,
        "prediction": prediction,
        "bootstrap": boot,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
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
        "m22_dependency_sha256": sha256_file(ROOT / "arara_m22_dependency.py"),
        "m25_dependency_sha256": sha256_file(ROOT / "arara_m25_dependency.py"),
    }
    path.write_text(json.dumps(environment, indent=2), encoding="utf-8")
