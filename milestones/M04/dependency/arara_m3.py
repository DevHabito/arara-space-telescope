
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


M2_DIR = Path(__file__).resolve().parents[1] / "m2"
if str(M2_DIR) not in sys.path:
    sys.path.insert(0, str(M2_DIR))

import arara_m2 as m2


POSITIVE_SHAPES = m2.POSITIVE_SHAPES
POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "3.0"
    development_root_seed: int = 2026072901
    holdout_root_seed: int = 2026072902
    bootstrap_seed: int = 2026072903

    development_n_per_stratum: int = 2000
    holdout_total_n_per_stratum: int = 5000
    holdout_batches: int = 20
    holdout_n_per_stratum_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_sbw_recall_lower_ci: float = 0.20
    minimum_delta_lower_ci: float = 0.10
    clean_noninferiority_margin: float = -0.03
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


def normalize_sbw(
    y: np.ndarray,
    data_cfg: m2.Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Subtract common mode before AR(1) whitening.

    Returns:
      residual_whitened: shape (n, time)
      q_raw:             shape (n, time)
      beta_hat:          shape (n,)
    """
    base = y[:, :, :data_cfg.baseline_n]
    mu = np.median(base, axis=2)
    scale = 1.4826 * np.median(
        np.abs(base - mu[:, :, None]), axis=2
    )
    scale = np.maximum(scale, 1e-8)

    x = (y - mu[:, :, None]) / scale[:, :, None]
    q = np.median(x[:, 1:, :], axis=1)

    xb = x[:, 0, :data_cfg.baseline_n]
    qb = q[:, :data_cfg.baseline_n]
    xc = xb - xb.mean(axis=1, keepdims=True)
    qc = qb - qb.mean(axis=1, keepdims=True)

    denom = np.sum(qc**2, axis=1)
    numer = np.sum(xc * qc, axis=1)
    beta_hat = np.divide(
        numer,
        denom,
        out=np.zeros_like(numer),
        where=denom > 1e-12,
    )
    beta_hat = np.clip(beta_hat, 0.0, 3.0)

    e = x[:, 0, :] - beta_hat[:, None] * q

    e_base = e[:, :data_cfg.baseline_n]
    e_mu = np.median(e_base, axis=1)
    e_scale = 1.4826 * np.median(
        np.abs(e_base - e_mu[:, None]), axis=1
    )
    e_scale = np.maximum(e_scale, 1e-8)

    centered = e_base - e_mu[:, None]
    phi_denom = np.sum(centered[:, :-1] ** 2, axis=1)
    phi_numer = np.sum(
        centered[:, 1:] * centered[:, :-1], axis=1
    )
    phi_hat = np.divide(
        phi_numer,
        phi_denom,
        out=np.zeros_like(phi_numer),
        where=phi_denom > 1e-12,
    )
    phi_hat = np.clip(phi_hat, 0.0, 0.8)

    all_centered = e - e_mu[:, None]
    residual = np.empty_like(e, dtype=np.float64)
    residual[:, 0] = all_centered[:, 0] / e_scale
    residual[:, 1:] = (
        all_centered[:, 1:]
        - phi_hat[:, None] * all_centered[:, :-1]
    ) / e_scale[:, None]

    return residual, q, beta_hat


def _paired_stratified_bootstrap(
    sbw_hits: Dict[str, np.ndarray],
    wbs_hits: Dict[str, np.ndarray],
    strata: tuple[str, ...],
    replicates: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    sbw_boot = np.zeros(replicates)
    wbs_boot = np.zeros(replicates)

    for stratum in strata:
        a = np.asarray(sbw_hits[stratum], dtype=np.int8)
        b = np.asarray(wbs_hits[stratum], dtype=np.int8)
        if a.shape != b.shape:
            raise ValueError("Paired arrays differ in shape.")
        n = a.size
        codes = a * 2 + b
        counts = np.bincount(codes, minlength=4)
        probs = counts / n
        draws = rng.multinomial(n, probs, size=replicates)
        sbw_mean = (draws[:, 2] + draws[:, 3]) / n
        wbs_mean = (draws[:, 1] + draws[:, 3]) / n
        sbw_boot += sbw_mean / len(strata)
        wbs_boot += wbs_mean / len(strata)

    return pd.DataFrame(
        {
            "sbw_recall": sbw_boot,
            "wbs_recall": wbs_boot,
            "delta": sbw_boot - wbs_boot,
        }
    )


def evaluate_development(
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    data_cfg = cfg.data_config()
    seed_seq = np.random.SeedSequence(cfg.development_root_seed)
    child_count = len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    children = seed_seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    positive = {}
    negative = {}

    for stratum, rng in zip(
        POSITIVE_STRATA, rngs[:len(POSITIVE_STRATA)]
    ):
        shape, context = stratum.split("__")
        data = m2.generate_positive_stratum(
            shape,
            context,
            cfg.development_n_per_stratum,
            rng,
            data_cfg,
        )
        _, wbs_residual, _, wbs_beta = m2.normalize_field(
            data.y, data_cfg
        )
        sbw_residual, _, sbw_beta = normalize_sbw(
            data.y, data_cfg
        )
        positive[stratum] = {
            "onset": data.onset,
            "t25": data.t25,
            "wbs": m2.rolling_slope_t_score(
                wbs_residual, data_cfg.detector_windows
            ).astype(np.float32),
            "sbw": m2.rolling_slope_t_score(
                sbw_residual, data_cfg.detector_windows
            ).astype(np.float32),
            "wbs_beta": wbs_beta,
            "sbw_beta": sbw_beta,
        }

    for family, rng in zip(
        NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]
    ):
        data = m2.generate_negative_family(
            family,
            cfg.development_n_per_stratum,
            rng,
            data_cfg,
        )
        _, wbs_residual, _, wbs_beta = m2.normalize_field(
            data.y, data_cfg
        )
        sbw_residual, _, sbw_beta = normalize_sbw(
            data.y, data_cfg
        )
        negative[family] = {
            "wbs": m2.rolling_slope_t_score(
                wbs_residual, data_cfg.detector_windows
            ).astype(np.float32),
            "sbw": m2.rolling_slope_t_score(
                sbw_residual, data_cfg.detector_windows
            ).astype(np.float32),
            "wbs_beta": wbs_beta,
            "sbw_beta": sbw_beta,
        }

    thresholds = {}
    rows = []

    for detector in ("wbs", "sbw"):
        maxima = {
            family: m2.curve_max(
                negative[family][detector],
                data_cfg.eval_start,
            )
            for family in NEGATIVE_FAMILIES
        }
        threshold, family_thresholds, allowed = (
            m2.conservative_threshold(
                maxima, cfg.development_fpr_target
            )
        )
        thresholds[detector] = threshold

        for family in NEGATIVE_FAMILIES:
            x = int(np.sum(maxima[family] >= threshold))
            rows.append(
                {
                    "detector": detector,
                    "kind": "negative",
                    "stratum": family,
                    "successes": x,
                    "n": len(maxima[family]),
                    "rate": x / len(maxima[family]),
                    "threshold": threshold,
                    "family_specific_threshold": (
                        family_thresholds[family]
                    ),
                    "allowed": allowed[family],
                }
            )

        for stratum in POSITIVE_STRATA:
            hits, _ = m2.early_hits(
                positive[stratum][detector],
                threshold,
                positive[stratum]["onset"],
                positive[stratum]["t25"],
                data_cfg.eval_start,
            )
            rows.append(
                {
                    "detector": detector,
                    "kind": "positive",
                    "stratum": stratum,
                    "successes": int(hits.sum()),
                    "n": len(hits),
                    "rate": float(hits.mean()),
                    "threshold": threshold,
                    "family_specific_threshold": np.nan,
                    "allowed": np.nan,
                }
            )

    details = {
        "thresholds": thresholds,
        "development_seed_children": [
            {
                "entropy": s.entropy,
                "spawn_key": list(s.spawn_key),
            }
            for s in children
        ],
    }
    return details, pd.DataFrame(rows)


def _evaluate_holdout_batch(
    batch: int,
    seq: np.random.SeedSequence,
    thresholds: dict,
    cfg: Config,
) -> tuple[list, list, list]:
    data_cfg = cfg.data_config()
    child_count = len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    children = seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    positive_records = []
    negative_records = []
    score_records = []

    for stratum, rng in zip(
        POSITIVE_STRATA, rngs[:len(POSITIVE_STRATA)]
    ):
        shape, context = stratum.split("__")
        data = m2.generate_positive_stratum(
            shape,
            context,
            cfg.holdout_n_per_stratum_per_batch,
            rng,
            data_cfg,
        )
        _, wbs_residual, _, wbs_beta = m2.normalize_field(
            data.y, data_cfg
        )
        sbw_residual, _, sbw_beta = normalize_sbw(
            data.y, data_cfg
        )

        score_map = {
            "wbs": m2.rolling_slope_t_score(
                wbs_residual, data_cfg.detector_windows
            ),
            "sbw": m2.rolling_slope_t_score(
                sbw_residual, data_cfg.detector_windows
            ),
        }
        maxima = {
            d: m2.curve_max(s, data_cfg.eval_start)
            for d, s in score_map.items()
        }
        beta_map = {"wbs": wbs_beta, "sbw": sbw_beta}

        for detector, score in score_map.items():
            hits, first = m2.early_hits(
                score,
                thresholds[detector],
                data.onset,
                data.t25,
                data_cfg.eval_start,
            )
            for i in range(len(hits)):
                positive_records.append(
                    {
                        "batch": batch,
                        "stratum": stratum,
                        "shape": shape,
                        "context": context,
                        "curve": i,
                        "detector": detector,
                        "hit": bool(hits[i]),
                        "first_crossing": int(first[i]),
                        "onset": int(data.onset[i]),
                        "t25": int(data.t25[i]),
                        "max_score": float(maxima[detector][i]),
                        "beta_hat": float(beta_map[detector][i]),
                        "beta_truth_proxy": float(
                            data.beta_truth_proxy[i]
                        ),
                        "artifact_family": str(
                            data.artifact_family[i]
                        ),
                    }
                )

        for i in range(cfg.holdout_n_per_stratum_per_batch):
            score_records.append(
                {
                    "batch": batch,
                    "stratum": stratum,
                    "label": 1,
                    "curve": i,
                    "wbs_max": float(maxima["wbs"][i]),
                    "sbw_max": float(maxima["sbw"][i]),
                }
            )

    for family, rng in zip(
        NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]
    ):
        data = m2.generate_negative_family(
            family,
            cfg.holdout_n_per_stratum_per_batch,
            rng,
            data_cfg,
        )
        _, wbs_residual, _, wbs_beta = m2.normalize_field(
            data.y, data_cfg
        )
        sbw_residual, _, sbw_beta = normalize_sbw(
            data.y, data_cfg
        )

        score_map = {
            "wbs": m2.rolling_slope_t_score(
                wbs_residual, data_cfg.detector_windows
            ),
            "sbw": m2.rolling_slope_t_score(
                sbw_residual, data_cfg.detector_windows
            ),
        }
        maxima = {
            d: m2.curve_max(s, data_cfg.eval_start)
            for d, s in score_map.items()
        }
        beta_map = {"wbs": wbs_beta, "sbw": sbw_beta}

        for detector, score in score_map.items():
            first = m2.first_crossing(
                score,
                thresholds[detector],
                data_cfg.eval_start,
            )
            alerts = first >= 0
            for i in range(len(alerts)):
                negative_records.append(
                    {
                        "batch": batch,
                        "family": family,
                        "curve": i,
                        "detector": detector,
                        "alert": bool(alerts[i]),
                        "first_crossing": int(first[i]),
                        "max_score": float(maxima[detector][i]),
                        "beta_hat": float(beta_map[detector][i]),
                        "beta_truth_proxy": float(
                            data.beta_truth_proxy[i]
                        ),
                    }
                )

        for i in range(cfg.holdout_n_per_stratum_per_batch):
            score_records.append(
                {
                    "batch": batch,
                    "stratum": family,
                    "label": 0,
                    "curve": i,
                    "wbs_max": float(maxima["wbs"][i]),
                    "sbw_max": float(maxima["sbw"][i]),
                }
            )

    return positive_records, negative_records, score_records


def evaluate_holdout(
    thresholds: dict,
    cfg: Config,
) -> dict:
    root_seq = np.random.SeedSequence(cfg.holdout_root_seed)
    batch_seqs = root_seq.spawn(cfg.holdout_batches)

    pos_all = []
    neg_all = []
    score_all = []
    seed_records = []

    for batch, seq in enumerate(batch_seqs):
        pos, neg, score = _evaluate_holdout_batch(
            batch, seq, thresholds, cfg
        )
        pos_all.extend(pos)
        neg_all.extend(neg)
        score_all.extend(score)
        seed_records.append(
            {
                "batch": batch,
                "entropy": seq.entropy,
                "spawn_key": list(seq.spawn_key),
            }
        )

    pos_df = pd.DataFrame(pos_all)
    neg_df = pd.DataFrame(neg_all)
    score_df = pd.DataFrame(score_all)

    summary_rows = []
    for detector in ("wbs", "sbw"):
        for stratum in POSITIVE_STRATA:
            s = pos_df[
                (pos_df.detector == detector)
                & (pos_df.stratum == stratum)
            ]
            summary_rows.append(
                {
                    "detector": detector,
                    "kind": "positive",
                    "stratum": stratum,
                    "successes": int(s.hit.sum()),
                    "n": len(s),
                    "rate": float(s.hit.mean()),
                    "cp_upper_95": np.nan,
                }
            )

        for family in NEGATIVE_FAMILIES:
            s = neg_df[
                (neg_df.detector == detector)
                & (neg_df.family == family)
            ]
            x = int(s.alert.sum())
            summary_rows.append(
                {
                    "detector": detector,
                    "kind": "negative",
                    "stratum": family,
                    "successes": x,
                    "n": len(s),
                    "rate": x / len(s),
                    "cp_upper_95": m2.clopper_pearson_upper(
                        x, len(s)
                    ),
                }
            )

    summary_df = pd.DataFrame(summary_rows)

    sbw_hits = {}
    wbs_hits = {}
    for stratum in POSITIVE_STRATA:
        sbw_hits[stratum] = (
            pos_df[
                (pos_df.detector == "sbw")
                & (pos_df.stratum == stratum)
            ]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )
        wbs_hits[stratum] = (
            pos_df[
                (pos_df.detector == "wbs")
                & (pos_df.stratum == stratum)
            ]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )

    global_boot = _paired_stratified_bootstrap(
        sbw_hits,
        wbs_hits,
        POSITIVE_STRATA,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed,
    )
    clean_strata = tuple(
        f"{shape}__clean" for shape in POSITIVE_SHAPES
    )
    clean_boot = _paired_stratified_bootstrap(
        sbw_hits,
        wbs_hits,
        clean_strata,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed + 1,
    )

    sbw_global = float(
        np.mean([sbw_hits[s].mean() for s in POSITIVE_STRATA])
    )
    wbs_global = float(
        np.mean([wbs_hits[s].mean() for s in POSITIVE_STRATA])
    )
    sbw_clean = float(
        np.mean([sbw_hits[s].mean() for s in clean_strata])
    )
    wbs_clean = float(
        np.mean([wbs_hits[s].mean() for s in clean_strata])
    )

    ci = {
        "sbw_recall_point": sbw_global,
        "wbs_recall_point": wbs_global,
        "delta_point": sbw_global - wbs_global,
        "sbw_recall_lower_95": float(
            np.quantile(global_boot.sbw_recall, 0.05)
        ),
        "sbw_recall_upper_95": float(
            np.quantile(global_boot.sbw_recall, 0.95)
        ),
        "delta_lower_95": float(
            np.quantile(global_boot.delta, 0.05)
        ),
        "delta_upper_95": float(
            np.quantile(global_boot.delta, 0.95)
        ),
        "sbw_clean_recall_point": sbw_clean,
        "wbs_clean_recall_point": wbs_clean,
        "clean_delta_point": sbw_clean - wbs_clean,
        "clean_delta_lower_95": float(
            np.quantile(clean_boot.delta, 0.05)
        ),
        "clean_delta_upper_95": float(
            np.quantile(clean_boot.delta, 0.95)
        ),
    }

    stratum_delta = {
        s: float(sbw_hits[s].mean() - wbs_hits[s].mean())
        for s in POSITIVE_STRATA
    }

    batch_rows = []
    for batch in range(cfg.holdout_batches):
        for detector in ("wbs", "sbw"):
            s = pos_df[
                (pos_df.batch == batch)
                & (pos_df.detector == detector)
            ]
            batch_rows.append(
                {
                    "batch": batch,
                    "detector": detector,
                    "early_recall": float(s.hit.mean()),
                    "hits": int(s.hit.sum()),
                    "n": len(s),
                }
            )
    batch_df = pd.DataFrame(batch_rows)
    batch_pivot = batch_df.pivot(
        index="batch", columns="detector", values="early_recall"
    )
    batch_pivot["delta_sbw_minus_wbs"] = (
        batch_pivot["sbw"] - batch_pivot["wbs"]
    )
    positive_batches = int(
        np.sum(batch_pivot.delta_sbw_minus_wbs > 0)
    )

    secondary_rows = []
    y_true = score_df.label.to_numpy()
    for detector, col in (
        ("wbs", "wbs_max"),
        ("sbw", "sbw_max"),
    ):
        values = score_df[col].to_numpy()
        secondary_rows.append(
            {
                "detector": detector,
                "auroc": float(roc_auc_score(y_true, values)),
                "average_precision": float(
                    average_precision_score(y_true, values)
                ),
            }
        )
    secondary_df = pd.DataFrame(secondary_rows)

    fpr_passes = []
    for family in NEGATIVE_FAMILIES:
        row = summary_df[
            (summary_df.detector == "sbw")
            & (summary_df.kind == "negative")
            & (summary_df.stratum == family)
        ].iloc[0]
        fpr_passes.append(
            float(row.cp_upper_95)
            <= cfg.holdout_fpr_upper_limit
        )

    criterion_1 = bool(all(fpr_passes))
    criterion_2 = (
        ci["sbw_recall_lower_95"]
        >= cfg.minimum_sbw_recall_lower_ci
    )
    criterion_3 = (
        ci["delta_lower_95"]
        >= cfg.minimum_delta_lower_ci
    )
    criterion_4 = (
        ci["clean_delta_lower_95"]
        >= cfg.clean_noninferiority_margin
    )
    criterion_5 = (
        sum(v >= 0 for v in stratum_delta.values()) >= 7
    )
    criterion_6 = positive_batches >= 15
    criterion_7 = thresholds["sbw"] < thresholds["wbs"]

    victory = all(
        [
            criterion_1,
            criterion_2,
            criterion_3,
            criterion_4,
            criterion_5,
            criterion_6,
            criterion_7,
        ]
    )
    strong_failure = (
        (not criterion_1)
        or (ci["delta_upper_95"] <= 0.0)
        or (
            ci["clean_delta_upper_95"]
            < cfg.clean_noninferiority_margin
        )
    )
    verdict = (
        "PASS"
        if victory
        else ("STRONG_FAIL" if strong_failure else "INCONCLUSIVE")
    )

    verdict_details = {
        "verdict": verdict,
        "criterion_1_sbw_fpr_control": criterion_1,
        "criterion_2_sbw_recall_lower_ge_0_20": criterion_2,
        "criterion_3_delta_lower_ge_0_10": criterion_3,
        "criterion_4_clean_noninferiority": criterion_4,
        "criterion_5_at_least_7_of_8_strata_nonnegative": criterion_5,
        "criterion_6_at_least_15_of_20_batches_positive": criterion_6,
        "criterion_7_sbw_threshold_lower_than_wbs": criterion_7,
        "positive_batches": positive_batches,
        "stratum_delta": stratum_delta,
        "thresholds": thresholds,
        **ci,
    }

    return {
        "positive_df": pos_df,
        "negative_df": neg_df,
        "score_df": score_df,
        "summary_df": summary_df,
        "global_bootstrap_df": global_boot,
        "clean_bootstrap_df": clean_boot,
        "batch_df": batch_df,
        "batch_pivot_df": batch_pivot.reset_index(),
        "secondary_df": secondary_df,
        "seed_records": seed_records,
        "verdict": verdict_details,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_environment(path: Path) -> None:
    import numpy
    import pandas
    import scipy
    import sklearn

    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "m2_dependency_sha256": sha256_file(
            M2_DIR / "arara_m2.py"
        ),
    }
    path.write_text(json.dumps(env, indent=2), encoding="utf-8")
