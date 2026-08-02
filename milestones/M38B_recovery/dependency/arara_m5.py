
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


ROOT = Path(__file__).resolve().parents[1]
M2_DIR = ROOT / "m2"
if str(M2_DIR) not in sys.path:
    sys.path.insert(0, str(M2_DIR))

import arara_m2 as m2


POSITIVE_SHAPES = m2.POSITIVE_SHAPES
POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "5.0"
    development_root_seed: int = 2026073101
    holdout_root_seed: int = 2026073102
    bootstrap_seed: int = 2026073103

    development_n_per_stratum: int = 2000
    holdout_total_n_per_stratum: int = 5000
    holdout_batches: int = 20
    holdout_n_per_stratum_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    strong_fail_global_recall_upper: float = 0.30
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


def sbw_with_signal_operator(
    y: np.ndarray,
    raw_signal: np.ndarray,
    cfg: m2.Config,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Returns:
      residual: processed observed target
      processed_signal: exact linear contribution of raw_signal
      params: selected baseline parameters
    """
    if y.ndim != 3:
        raise ValueError("y must have shape (n, stars, time).")
    if raw_signal.shape != (y.shape[0], y.shape[2]):
        raise ValueError("raw_signal shape must match target time series.")

    base = y[:, :, :cfg.baseline_n]
    mu = np.median(base, axis=2)
    scale = 1.4826 * np.median(
        np.abs(base - mu[:, :, None]),
        axis=2,
    )
    scale = np.maximum(scale, 1e-8)

    x = (y - mu[:, :, None]) / scale[:, :, None]
    q = np.median(x[:, 1:, :], axis=1)

    xb = x[:, 0, :cfg.baseline_n]
    qb = q[:, :cfg.baseline_n]
    xc = xb - xb.mean(axis=1, keepdims=True)
    qc = qb - qb.mean(axis=1, keepdims=True)

    beta_denom = np.sum(qc**2, axis=1)
    beta_numer = np.sum(xc * qc, axis=1)
    beta_hat = np.divide(
        beta_numer,
        beta_denom,
        out=np.zeros_like(beta_numer),
        where=beta_denom > 1e-12,
    )
    beta_hat = np.clip(beta_hat, 0.0, 3.0)

    e = x[:, 0, :] - beta_hat[:, None] * q
    e_base = e[:, :cfg.baseline_n]
    e_mu = np.median(e_base, axis=1)
    e_scale = 1.4826 * np.median(
        np.abs(e_base - e_mu[:, None]),
        axis=1,
    )
    e_scale = np.maximum(e_scale, 1e-8)

    centered = e_base - e_mu[:, None]
    phi_denom = np.sum(centered[:, :-1] ** 2, axis=1)
    phi_numer = np.sum(
        centered[:, 1:] * centered[:, :-1],
        axis=1,
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

    signal_x = raw_signal / scale[:, 0, None]
    processed_signal = np.empty_like(signal_x)
    processed_signal[:, 0] = signal_x[:, 0] / e_scale
    processed_signal[:, 1:] = (
        signal_x[:, 1:]
        - phi_hat[:, None] * signal_x[:, :-1]
    ) / e_scale[:, None]

    params = {
        "target_scale": scale[:, 0],
        "beta_hat": beta_hat,
        "residual_scale": e_scale,
        "residual_phi": phi_hat,
    }
    return residual, processed_signal, params


def generate_virtual_hypotheses(
    n: int,
    rng: np.random.Generator,
    cfg: m2.Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates one independent unit-amplitude virtual event per negative curve.
    """
    shape_index = rng.integers(0, len(POSITIVE_SHAPES), size=n)
    onset = rng.integers(
        cfg.onset_low,
        cfg.onset_high + 1,
        size=n,
    )
    duration = rng.integers(
        cfg.duration_low,
        cfg.duration_high + 1,
        size=n,
    )
    k = np.arange(cfg.n_time)[None, :]
    signal = np.zeros((n, cfg.n_time), dtype=np.float64)
    shape_names = np.empty(n, dtype=object)

    for idx, shape in enumerate(POSITIVE_SHAPES):
        mask = shape_index == idx
        if not np.any(mask):
            continue
        values = m2._event_shape(
            shape,
            k,
            onset[mask],
            duration[mask],
            rng,
        )
        signal[mask] = values
        shape_names[mask] = shape

    reached = signal >= 0.25
    t25 = np.argmax(reached, axis=1)
    if not np.all(reached[np.arange(n), t25]):
        raise RuntimeError("Every virtual event must reach 25%.")

    return (
        signal,
        onset.astype(np.int16),
        t25.astype(np.int16),
        shape_names,
    )


def aligned_t_score(
    residual: np.ndarray,
    processed_template: np.ndarray,
    onset: np.ndarray,
    t25: np.ndarray,
) -> np.ndarray:
    n = residual.shape[0]
    if processed_template.shape != residual.shape:
        raise ValueError("Template and residual shapes differ.")
    scores = np.zeros(n, dtype=np.float64)

    for i in range(n):
        start = int(onset[i])
        stop = int(t25[i]) + 1
        if stop - start < 3:
            continue

        y = residual[i, start:stop]
        h = processed_template[i, start:stop]
        yc = y - y.mean()
        hc = h - h.mean()
        yn = float(np.linalg.norm(yc))
        hn = float(np.linalg.norm(hc))
        if yn <= 1e-12 or hn <= 1e-12:
            continue

        corr = float(np.dot(yc, hc) / (yn * hn))
        corr = min(1.0, max(-1.0, corr))
        if corr <= 0.0:
            continue
        if corr >= 1.0 - 1e-15:
            scores[i] = np.inf
            continue

        length = stop - start
        scores[i] = corr * np.sqrt(
            (length - 2.0) / (1.0 - corr * corr)
        )

    return scores


def clopper_pearson_lower(
    x: int,
    n: int,
    confidence: float = 0.95,
) -> float:
    from scipy.stats import beta as beta_dist

    if not (0 <= x <= n):
        raise ValueError("x must satisfy 0 <= x <= n.")
    if n <= 0:
        raise ValueError("n must be positive.")
    if x == 0:
        return 0.0
    alpha = 1.0 - confidence
    return float(beta_dist.ppf(alpha, x, n - x + 1))


def stratified_bootstrap_recall(
    hits_by_stratum: Dict[str, np.ndarray],
    replicates: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.zeros(replicates, dtype=np.float64)

    for stratum in POSITIVE_STRATA:
        hits = np.asarray(hits_by_stratum[stratum], dtype=np.int8)
        n = len(hits)
        count = int(hits.sum())
        draws = rng.multinomial(
            n,
            [1.0 - count / n, count / n],
            size=replicates,
        )
        out += (draws[:, 1] / n) / len(POSITIVE_STRATA)

    return out


def evaluate_development(
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    data_cfg = cfg.data_config()
    seed_seq = np.random.SeedSequence(
        cfg.development_root_seed
    )
    child_count = len(POSITIVE_STRATA) + len(
        NEGATIVE_FAMILIES
    )
    children = seed_seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    positive_scores = {}
    negative_scores = {}
    rows = []

    for stratum, rng in zip(
        POSITIVE_STRATA,
        rngs[:len(POSITIVE_STRATA)],
    ):
        shape, context = stratum.split("__")
        data = m2.generate_positive_stratum(
            shape,
            context,
            cfg.development_n_per_stratum,
            rng,
            data_cfg,
        )
        residual, processed_signal, _ = sbw_with_signal_operator(
            data.y,
            data.target_signal,
            data_cfg,
        )
        score = aligned_t_score(
            residual,
            processed_signal,
            data.onset,
            data.t25,
        ).astype(np.float32)
        positive_scores[stratum] = score

    for family, rng in zip(
        NEGATIVE_FAMILIES,
        rngs[len(POSITIVE_STRATA):],
    ):
        data = m2.generate_negative_family(
            family,
            cfg.development_n_per_stratum,
            rng,
            data_cfg,
        )
        virtual_signal, onset, t25, shape_names = (
            generate_virtual_hypotheses(
                cfg.development_n_per_stratum,
                rng,
                data_cfg,
            )
        )
        residual, processed_signal, _ = sbw_with_signal_operator(
            data.y,
            virtual_signal,
            data_cfg,
        )
        score = aligned_t_score(
            residual,
            processed_signal,
            onset,
            t25,
        ).astype(np.float32)
        negative_scores[family] = score

    threshold, family_thresholds, allowed = (
        m2.conservative_threshold(
            negative_scores,
            cfg.development_fpr_target,
        )
    )

    for family in NEGATIVE_FAMILIES:
        scores = negative_scores[family]
        alerts = int(np.sum(scores >= threshold))
        rows.append(
            {
                "kind": "negative",
                "stratum": family,
                "successes": alerts,
                "n": len(scores),
                "rate": alerts / len(scores),
                "threshold": threshold,
                "family_specific_threshold": (
                    family_thresholds[family]
                ),
                "allowed": allowed[family],
            }
        )

    for stratum in POSITIVE_STRATA:
        scores = positive_scores[stratum]
        hits = scores >= threshold
        rows.append(
            {
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
        "threshold": float(threshold),
        "family_thresholds": family_thresholds,
        "allowed_counts": allowed,
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
    threshold: float,
    cfg: Config,
) -> tuple[list, list, list]:
    data_cfg = cfg.data_config()
    child_count = len(POSITIVE_STRATA) + len(
        NEGATIVE_FAMILIES
    )
    children = seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    positive_records = []
    negative_records = []
    score_records = []

    for stratum, rng in zip(
        POSITIVE_STRATA,
        rngs[:len(POSITIVE_STRATA)],
    ):
        shape, context = stratum.split("__")
        data = m2.generate_positive_stratum(
            shape,
            context,
            cfg.holdout_n_per_stratum_per_batch,
            rng,
            data_cfg,
        )
        residual, processed_signal, params = (
            sbw_with_signal_operator(
                data.y,
                data.target_signal,
                data_cfg,
            )
        )
        scores = aligned_t_score(
            residual,
            processed_signal,
            data.onset,
            data.t25,
        )
        hits = scores >= threshold

        for i in range(len(scores)):
            positive_records.append(
                {
                    "batch": batch,
                    "stratum": stratum,
                    "shape": shape,
                    "context": context,
                    "curve": i,
                    "score": float(scores[i]),
                    "hit": bool(hits[i]),
                    "onset": int(data.onset[i]),
                    "t25": int(data.t25[i]),
                    "segment_length": int(
                        data.t25[i] - data.onset[i] + 1
                    ),
                    "residual_phi": float(
                        params["residual_phi"][i]
                    ),
                }
            )
            score_records.append(
                {
                    "batch": batch,
                    "stratum": stratum,
                    "label": 1,
                    "curve": i,
                    "score": float(scores[i]),
                }
            )

    for family, rng in zip(
        NEGATIVE_FAMILIES,
        rngs[len(POSITIVE_STRATA):],
    ):
        data = m2.generate_negative_family(
            family,
            cfg.holdout_n_per_stratum_per_batch,
            rng,
            data_cfg,
        )
        virtual_signal, onset, t25, shape_names = (
            generate_virtual_hypotheses(
                cfg.holdout_n_per_stratum_per_batch,
                rng,
                data_cfg,
            )
        )
        residual, processed_signal, params = (
            sbw_with_signal_operator(
                data.y,
                virtual_signal,
                data_cfg,
            )
        )
        scores = aligned_t_score(
            residual,
            processed_signal,
            onset,
            t25,
        )
        alerts = scores >= threshold

        for i in range(len(scores)):
            negative_records.append(
                {
                    "batch": batch,
                    "family": family,
                    "curve": i,
                    "score": float(scores[i]),
                    "alert": bool(alerts[i]),
                    "pseudo_shape": str(shape_names[i]),
                    "pseudo_onset": int(onset[i]),
                    "pseudo_t25": int(t25[i]),
                    "segment_length": int(
                        t25[i] - onset[i] + 1
                    ),
                    "residual_phi": float(
                        params["residual_phi"][i]
                    ),
                }
            )
            score_records.append(
                {
                    "batch": batch,
                    "stratum": family,
                    "label": 0,
                    "curve": i,
                    "score": float(scores[i]),
                }
            )

    return positive_records, negative_records, score_records


def evaluate_holdout(
    threshold: float,
    cfg: Config,
) -> dict:
    root_seq = np.random.SeedSequence(
        cfg.holdout_root_seed
    )
    batch_seqs = root_seq.spawn(cfg.holdout_batches)

    pos_all = []
    neg_all = []
    score_all = []
    seed_records = []

    for batch, seq in enumerate(batch_seqs):
        pos, neg, scores = _evaluate_holdout_batch(
            batch,
            seq,
            threshold,
            cfg,
        )
        pos_all.extend(pos)
        neg_all.extend(neg)
        score_all.extend(scores)
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
    hits_by_stratum = {}

    for stratum in POSITIVE_STRATA:
        s = pos_df[pos_df.stratum == stratum]
        hits = s.hit.to_numpy(dtype=bool)
        hits_by_stratum[stratum] = hits
        x = int(hits.sum())
        summary_rows.append(
            {
                "kind": "positive",
                "stratum": stratum,
                "successes": x,
                "n": len(hits),
                "rate": x / len(hits),
                "cp_lower_95": clopper_pearson_lower(
                    x, len(hits)
                ),
                "cp_upper_95": np.nan,
            }
        )

    for family in NEGATIVE_FAMILIES:
        s = neg_df[neg_df.family == family]
        x = int(s.alert.sum())
        summary_rows.append(
            {
                "kind": "negative",
                "stratum": family,
                "successes": x,
                "n": len(s),
                "rate": x / len(s),
                "cp_lower_95": np.nan,
                "cp_upper_95": (
                    m2.clopper_pearson_upper(
                        x, len(s)
                    )
                ),
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    boot = stratified_bootstrap_recall(
        hits_by_stratum,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed,
    )
    point = float(
        np.mean(
            [
                hits_by_stratum[s].mean()
                for s in POSITIVE_STRATA
            ]
        )
    )
    ci = {
        "oracle_recall_point": point,
        "oracle_recall_lower_95": float(
            np.quantile(boot, 0.05)
        ),
        "oracle_recall_upper_95": float(
            np.quantile(boot, 0.95)
        ),
    }

    batch_rows = []
    for batch in range(cfg.holdout_batches):
        s = pos_df[pos_df.batch == batch]
        batch_rows.append(
            {
                "batch": batch,
                "recall": float(s.hit.mean()),
                "hits": int(s.hit.sum()),
                "n": len(s),
            }
        )
    batch_df = pd.DataFrame(batch_rows)
    good_batches = int(
        np.sum(
            batch_df.recall
            >= cfg.batch_recall_threshold
        )
    )

    y_true = score_df.label.to_numpy()
    scores = score_df.score.to_numpy()
    secondary_df = pd.DataFrame(
        [
            {
                "auroc": float(
                    roc_auc_score(y_true, scores)
                ),
                "average_precision": float(
                    average_precision_score(
                        y_true, scores
                    )
                ),
            }
        ]
    )

    negative_summary = summary_df[
        summary_df.kind == "negative"
    ]
    criterion_1 = bool(
        np.all(
            negative_summary.cp_upper_95
            <= cfg.holdout_fpr_upper_limit
        )
    )
    criterion_2 = (
        ci["oracle_recall_lower_95"]
        >= cfg.minimum_global_recall_lower_ci
    )

    positive_summary = summary_df[
        summary_df.kind == "positive"
    ]
    good_strata = int(
        np.sum(
            positive_summary.cp_lower_95
            >= cfg.minimum_stratum_recall_lower_ci
        )
    )
    criterion_3 = good_strata >= cfg.minimum_good_strata
    criterion_4 = good_batches >= cfg.minimum_good_batches

    victory = all(
        [
            criterion_1,
            criterion_2,
            criterion_3,
            criterion_4,
        ]
    )
    strong_failure = (
        (not criterion_1)
        or (
            ci["oracle_recall_upper_95"]
            <= cfg.strong_fail_global_recall_upper
        )
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

    verdict_details = {
        "verdict": verdict,
        "criterion_1_fpr_control": criterion_1,
        "criterion_2_global_recall_lower_ge_0_60": (
            criterion_2
        ),
        "criterion_3_six_strata_lower_ge_0_50": (
            criterion_3
        ),
        "criterion_4_fifteen_batches_recall_ge_0_55": (
            criterion_4
        ),
        "good_strata": good_strata,
        "good_batches": good_batches,
        "threshold": float(threshold),
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
        "seed_records": seed_records,
        "verdict": verdict_details,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024), b""
        ):
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
    path.write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )
