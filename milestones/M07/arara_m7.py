
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

ROOT = Path(__file__).resolve().parents[1]
M2_DIR = ROOT / "m2"
M5_DIR = ROOT / "m5"
for d in (M2_DIR, M5_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

import arara_m2 as m2
import arara_m5 as m5

POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "7.0"
    target_fraction: float = 0.75
    development_root_seed: int = 2026080201
    holdout_root_seed: int = 2026080202
    bootstrap_seed: int = 2026080203

    development_n_per_stratum: int = 2000
    holdout_total_n_per_stratum: int = 5000
    holdout_batches: int = 20
    holdout_n_per_stratum_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_global_recall_lower_ci: float = 0.30
    minimum_stratum_recall_lower_ci: float = 0.20
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.25
    strong_fail_global_recall_upper: float = 0.10
    bootstrap_replicates: int = 10_000

    def data_config(self) -> m2.Config:
        return m2.Config(
            development_root_seed=self.development_root_seed,
            holdout_root_seed=self.holdout_root_seed,
            bootstrap_seed=self.bootstrap_seed,
            development_n_per_stratum=self.development_n_per_stratum,
            holdout_total_n_per_stratum=self.holdout_total_n_per_stratum,
            holdout_batches=self.holdout_batches,
            holdout_n_per_stratum_per_batch=self.holdout_n_per_stratum_per_batch,
        )


def time_at_fraction(signal: np.ndarray, fraction: float) -> np.ndarray:
    if signal.ndim != 2:
        raise ValueError("signal must be 2D.")
    if not (0 < fraction <= 1):
        raise ValueError("fraction must lie in (0,1].")
    amplitude = np.max(signal, axis=1)
    if np.any(amplitude <= 0):
        raise ValueError("Every signal must have positive amplitude.")
    reached = signal >= (fraction * amplitude)[:, None]
    times = np.argmax(reached, axis=1)
    if not np.all(reached[np.arange(len(signal)), times]):
        raise RuntimeError("Every signal must reach the requested fraction.")
    return times.astype(np.int16)


def _evaluate_positive(
    shape: str,
    context: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> tuple[m2.FieldData, np.ndarray, np.ndarray]:
    data_cfg = cfg.data_config()
    data = m2.generate_positive_stratum(shape, context, n, rng, data_cfg)
    tf = time_at_fraction(data.target_signal, cfg.target_fraction)
    residual, processed_signal, _ = m5.sbw_with_signal_operator(
        data.y, data.target_signal, data_cfg
    )
    scores = m5.aligned_t_score(
        residual, processed_signal, data.onset, tf
    )
    return data, tf, scores


def _evaluate_negative(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> tuple[m2.FieldData, np.ndarray, np.ndarray, np.ndarray]:
    data_cfg = cfg.data_config()
    data = m2.generate_negative_family(family, n, rng, data_cfg)
    virtual_signal, onset, _, shapes = m5.generate_virtual_hypotheses(
        n, rng, data_cfg
    )
    tf = time_at_fraction(virtual_signal, cfg.target_fraction)
    residual, processed_signal, _ = m5.sbw_with_signal_operator(
        data.y, virtual_signal, data_cfg
    )
    scores = m5.aligned_t_score(
        residual, processed_signal, onset, tf
    )
    return data, onset, tf, scores


def evaluate_development(cfg: Config) -> tuple[dict, pd.DataFrame]:
    seed_seq = np.random.SeedSequence(cfg.development_root_seed)
    child_count = len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    children = seed_seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    pos_scores = {}
    neg_scores = {}

    for stratum, rng in zip(POSITIVE_STRATA, rngs[:len(POSITIVE_STRATA)]):
        shape, context = stratum.split("__")
        _, _, score = _evaluate_positive(
            shape, context, cfg.development_n_per_stratum, rng, cfg
        )
        pos_scores[stratum] = score.astype(np.float32)

    for family, rng in zip(
        NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]
    ):
        _, _, _, score = _evaluate_negative(
            family, cfg.development_n_per_stratum, rng, cfg
        )
        neg_scores[family] = score.astype(np.float32)

    threshold, family_thresholds, allowed = m2.conservative_threshold(
        neg_scores, cfg.development_fpr_target
    )

    rows = []
    for family in NEGATIVE_FAMILIES:
        score = neg_scores[family]
        alerts = int(np.sum(score >= threshold))
        rows.append({
            "kind": "negative",
            "stratum": family,
            "successes": alerts,
            "n": len(score),
            "rate": alerts / len(score),
            "threshold": threshold,
            "family_specific_threshold": family_thresholds[family],
            "allowed": allowed[family],
        })
    for stratum in POSITIVE_STRATA:
        score = pos_scores[stratum]
        hits = score >= threshold
        rows.append({
            "kind": "positive",
            "stratum": stratum,
            "successes": int(hits.sum()),
            "n": len(hits),
            "rate": float(hits.mean()),
            "threshold": threshold,
            "family_specific_threshold": np.nan,
            "allowed": np.nan,
        })

    details = {
        "threshold": float(threshold),
        "family_thresholds": family_thresholds,
        "allowed_counts": allowed,
        "development_seed_children": [
            {"entropy": s.entropy, "spawn_key": list(s.spawn_key)}
            for s in children
        ],
    }
    return details, pd.DataFrame(rows)


def _evaluate_holdout_batch(
    batch: int,
    seq: np.random.SeedSequence,
    threshold: float,
    cfg: Config,
) -> tuple[list, list, list]:
    child_count = len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    children = seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    pos_records, neg_records, score_records = [], [], []

    for stratum, rng in zip(POSITIVE_STRATA, rngs[:len(POSITIVE_STRATA)]):
        shape, context = stratum.split("__")
        data, tf, scores = _evaluate_positive(
            shape, context, cfg.holdout_n_per_stratum_per_batch, rng, cfg
        )
        hits = scores >= threshold
        for i in range(len(scores)):
            pos_records.append({
                "batch": batch,
                "stratum": stratum,
                "shape": shape,
                "context": context,
                "curve": i,
                "score": float(scores[i]),
                "hit": bool(hits[i]),
                "onset": int(data.onset[i]),
                "tf": int(tf[i]),
                "segment_length": int(tf[i] - data.onset[i] + 1),
            })
            score_records.append({
                "batch": batch,
                "stratum": stratum,
                "label": 1,
                "curve": i,
                "score": float(scores[i]),
            })

    for family, rng in zip(
        NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]
    ):
        data, onset, tf, scores = _evaluate_negative(
            family, cfg.holdout_n_per_stratum_per_batch, rng, cfg
        )
        alerts = scores >= threshold
        for i in range(len(scores)):
            neg_records.append({
                "batch": batch,
                "family": family,
                "curve": i,
                "score": float(scores[i]),
                "alert": bool(alerts[i]),
                "pseudo_onset": int(onset[i]),
                "pseudo_tf": int(tf[i]),
                "segment_length": int(tf[i] - onset[i] + 1),
            })
            score_records.append({
                "batch": batch,
                "stratum": family,
                "label": 0,
                "curve": i,
                "score": float(scores[i]),
            })

    return pos_records, neg_records, score_records


def evaluate_holdout(threshold: float, cfg: Config) -> dict:
    root_seq = np.random.SeedSequence(cfg.holdout_root_seed)
    batch_seqs = root_seq.spawn(cfg.holdout_batches)
    pos_all, neg_all, score_all, seeds = [], [], [], []

    for batch, seq in enumerate(batch_seqs):
        p, n, s = _evaluate_holdout_batch(batch, seq, threshold, cfg)
        pos_all.extend(p)
        neg_all.extend(n)
        score_all.extend(s)
        seeds.append({
            "batch": batch,
            "entropy": seq.entropy,
            "spawn_key": list(seq.spawn_key),
        })

    pos_df = pd.DataFrame(pos_all)
    neg_df = pd.DataFrame(neg_all)
    score_df = pd.DataFrame(score_all)

    summary_rows = []
    hits_by_stratum = {}
    for stratum in POSITIVE_STRATA:
        s = pos_df[pos_df.stratum == stratum]
        hits = s.hit.to_numpy(dtype=bool)
        hits_by_stratum[stratum] = hits
        x = int(hits.sum())
        summary_rows.append({
            "kind": "positive",
            "stratum": stratum,
            "successes": x,
            "n": len(hits),
            "rate": x / len(hits),
            "cp_lower_95": m5.clopper_pearson_lower(x, len(hits)),
            "cp_upper_95": np.nan,
        })
    for family in NEGATIVE_FAMILIES:
        s = neg_df[neg_df.family == family]
        x = int(s.alert.sum())
        summary_rows.append({
            "kind": "negative",
            "stratum": family,
            "successes": x,
            "n": len(s),
            "rate": x / len(s),
            "cp_lower_95": np.nan,
            "cp_upper_95": m2.clopper_pearson_upper(x, len(s)),
        })
    summary_df = pd.DataFrame(summary_rows)

    boot = m5.stratified_bootstrap_recall(
        hits_by_stratum, cfg.bootstrap_replicates, cfg.bootstrap_seed
    )
    point = float(np.mean([
        hits_by_stratum[s].mean() for s in POSITIVE_STRATA
    ]))
    ci = {
        "recall_point": point,
        "recall_lower_95": float(np.quantile(boot, 0.05)),
        "recall_upper_95": float(np.quantile(boot, 0.95)),
    }

    batch_rows = []
    for batch in range(cfg.holdout_batches):
        s = pos_df[pos_df.batch == batch]
        batch_rows.append({
            "batch": batch,
            "recall": float(s.hit.mean()),
            "hits": int(s.hit.sum()),
            "n": len(s),
        })
    batch_df = pd.DataFrame(batch_rows)
    good_batches = int(np.sum(
        batch_df.recall >= cfg.batch_recall_threshold
    ))

    y_true = score_df.label.to_numpy()
    score_values = score_df.score.to_numpy()
    secondary_df = pd.DataFrame([{
        "auroc": float(roc_auc_score(y_true, score_values)),
        "average_precision": float(
            average_precision_score(y_true, score_values)
        ),
    }])

    neg_summary = summary_df[summary_df.kind == "negative"]
    criterion_1 = bool(np.all(
        neg_summary.cp_upper_95 <= cfg.holdout_fpr_upper_limit
    ))
    criterion_2 = ci["recall_lower_95"] >= cfg.minimum_global_recall_lower_ci
    pos_summary = summary_df[summary_df.kind == "positive"]
    good_strata = int(np.sum(
        pos_summary.cp_lower_95 >= cfg.minimum_stratum_recall_lower_ci
    ))
    criterion_3 = good_strata >= cfg.minimum_good_strata
    criterion_4 = good_batches >= cfg.minimum_good_batches

    victory = all([criterion_1, criterion_2, criterion_3, criterion_4])
    strong_failure = (
        (not criterion_1)
        or (ci["recall_upper_95"] <= cfg.strong_fail_global_recall_upper)
    )
    verdict_name = (
        "PASS" if victory else ("STRONG_FAIL" if strong_failure else "INCONCLUSIVE")
    )
    verdict = {
        "verdict": verdict_name,
        "criterion_1_fpr_control": criterion_1,
        "criterion_2_global_recall_lower_ge_0_30": criterion_2,
        "criterion_3_six_strata_lower_ge_0_20": criterion_3,
        "criterion_4_fifteen_batches_recall_ge_0_25": criterion_4,
        "good_strata": good_strata,
        "good_batches": good_batches,
        "threshold": float(threshold),
        "target_fraction": cfg.target_fraction,
        **ci,
    }

    return {
        "positive_df": pos_df,
        "negative_df": neg_df,
        "score_df": score_df,
        "summary_df": summary_df,
        "bootstrap": boot,
        "batch_df": batch_df,
        "secondary_df": secondary_df,
        "seed_records": seeds,
        "verdict": verdict,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_environment(path: Path) -> None:
    import numpy, pandas, scipy, sklearn
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m2_dependency_sha256": sha256_file(M2_DIR / "arara_m2.py"),
        "m5_dependency_sha256": sha256_file(M5_DIR / "arara_m5.py"),
    }
    path.write_text(json.dumps(env, indent=2), encoding="utf-8")
