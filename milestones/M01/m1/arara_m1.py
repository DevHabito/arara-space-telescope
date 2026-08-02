
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple
import hashlib
import json
import math
import platform
import sys
import time

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import beta as beta_dist
from sklearn.metrics import average_precision_score, roc_auc_score


POSITIVE_FAMILIES = ("linear", "power_law", "exponential", "logistic")
NEGATIVE_FAMILIES = (
    "quiet",
    "positive_impulse",
    "symmetric_bump",
    "sinusoid",
    "negative_dip_recovery",
)


@dataclass(frozen=True)
class Config:
    version: str = "1.0"
    development_root_seed: int = 2026072701
    holdout_root_seed: int = 2026072702
    bootstrap_seed: int = 2026072703

    n_time: int = 160
    burn_in: int = 200
    baseline_n: int = 40
    eval_start: int = 40

    onset_low: int = 60
    onset_high: int = 90
    duration_low: int = 24
    duration_high: int = 60
    snr_low: float = 2.0
    snr_high: float = 5.0
    phi_low: float = 0.0
    phi_high: float = 0.6

    m1_windows: Tuple[int, ...] = (8, 16, 32)
    cusum_kappas: Tuple[float, ...] = (0.25, 0.50, 0.75, 1.00)

    development_n_per_family: int = 2000
    holdout_total_n_per_family: int = 5000
    holdout_batches: int = 20
    holdout_n_per_family_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_recall_lower_ci: float = 0.30
    minimum_delta_lower_ci: float = 0.10
    bootstrap_replicates: int = 10_000


@dataclass
class FamilyData:
    y: np.ndarray
    signal: np.ndarray
    onset: np.ndarray
    t25: np.ndarray
    phi: np.ndarray
    noise_kind: np.ndarray


def _stationary_ar1_noise(
    rng: np.random.Generator,
    n: int,
    n_time: int,
    burn_in: int,
    phi: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    total = n_time + burn_in
    is_student = rng.random(n) < 0.5

    innovations = rng.standard_normal((n, total))
    if np.any(is_student):
        innovations[is_student] = (
            rng.standard_t(df=5, size=(is_student.sum(), total)) * math.sqrt(3.0 / 5.0)
        )

    eps = np.zeros((n, total), dtype=np.float64)
    eps[:, 0] = innovations[:, 0]
    for k in range(1, total):
        eps[:, k] = phi * eps[:, k - 1] + innovations[:, k]
    return eps[:, burn_in:], is_student.astype(np.int8)


def _sample_common_latents(
    rng: np.random.Generator, n: int, cfg: Config
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    phi = rng.uniform(cfg.phi_low, cfg.phi_high, size=n)
    onset = rng.integers(cfg.onset_low, cfg.onset_high + 1, size=n)
    duration = rng.integers(cfg.duration_low, cfg.duration_high + 1, size=n)
    sigma_marginal = 1.0 / np.sqrt(1.0 - phi**2)
    amplitude = rng.uniform(cfg.snr_low, cfg.snr_high, size=n) * sigma_marginal
    return phi, onset, duration, amplitude


def _normalized_logistic(x: np.ndarray, q: np.ndarray) -> np.ndarray:
    g = 1.0 / (1.0 + np.exp(-q[:, None] * (x - 0.5)))
    g0 = 1.0 / (1.0 + np.exp(q / 2.0))
    g1 = 1.0 / (1.0 + np.exp(-q / 2.0))
    return (g - g0[:, None]) / (g1 - g0)[:, None]


def generate_positive_family(
    family: str, n: int, rng: np.random.Generator, cfg: Config
) -> FamilyData:
    if family not in POSITIVE_FAMILIES:
        raise ValueError(f"Unknown positive family: {family}")

    phi, onset, duration, amplitude = _sample_common_latents(rng, n, cfg)
    noise, noise_kind = _stationary_ar1_noise(rng, n, cfg.n_time, cfg.burn_in, phi)

    k = np.arange(cfg.n_time)[None, :]
    x = np.clip((k - onset[:, None]) / duration[:, None], 0.0, 1.0)

    if family == "linear":
        shape = x
    elif family == "power_law":
        gamma = rng.uniform(1.5, 3.0, size=n)
        shape = x ** gamma[:, None]
    elif family == "exponential":
        beta = rng.uniform(1.0, 4.0, size=n)
        shape = (np.exp(beta[:, None] * x) - 1.0) / (np.exp(beta) - 1.0)[:, None]
    else:
        q = rng.uniform(6.0, 12.0, size=n)
        shape = _normalized_logistic(x, q)

    signal = amplitude[:, None] * shape
    y = noise + signal

    reached = signal >= (0.25 * amplitude)[:, None]
    t25 = np.argmax(reached, axis=1)
    if not np.all(reached[np.arange(n), t25]):
        raise RuntimeError("Every positive curve must reach 25% amplitude.")

    return FamilyData(
        y=y.astype(np.float64),
        signal=signal.astype(np.float64),
        onset=onset.astype(np.int16),
        t25=t25.astype(np.int16),
        phi=phi.astype(np.float64),
        noise_kind=noise_kind,
    )


def generate_negative_family(
    family: str, n: int, rng: np.random.Generator, cfg: Config
) -> FamilyData:
    if family not in NEGATIVE_FAMILIES:
        raise ValueError(f"Unknown negative family: {family}")

    phi, onset, duration, amplitude = _sample_common_latents(rng, n, cfg)
    noise, noise_kind = _stationary_ar1_noise(rng, n, cfg.n_time, cfg.burn_in, phi)
    signal = np.zeros((n, cfg.n_time), dtype=np.float64)
    k = np.arange(cfg.n_time)[None, :]

    if family == "quiet":
        pass
    elif family == "positive_impulse":
        starts = rng.integers(60, 151, size=n)
        lengths = rng.integers(1, 3, size=n)
        for i in range(n):
            stop = min(cfg.n_time, int(starts[i] + lengths[i]))
            signal[i, starts[i]:stop] = amplitude[i]
    elif family == "symmetric_bump":
        x = (k - onset[:, None]) / duration[:, None]
        active = (x >= 0.0) & (x <= 1.0)
        signal = amplitude[:, None] * np.where(active, np.sin(np.pi * x), 0.0)
    elif family == "sinusoid":
        period = rng.integers(12, 49, size=n)
        phase = rng.uniform(0.0, 2.0 * np.pi, size=n)
        signal = amplitude[:, None] * np.sin(
            2.0 * np.pi * k / period[:, None] + phase[:, None]
        )
    elif family == "negative_dip_recovery":
        x = (k - onset[:, None]) / duration[:, None]
        active = (x >= 0.0) & (x <= 1.0)
        signal = -amplitude[:, None] * np.where(active, np.sin(np.pi * x), 0.0)

    y = noise + signal
    no_time = np.full(n, -1, dtype=np.int16)
    return FamilyData(
        y=y.astype(np.float64),
        signal=signal.astype(np.float64),
        onset=no_time,
        t25=no_time,
        phi=phi.astype(np.float64),
        noise_kind=noise_kind,
    )


def causal_normalize(y: np.ndarray, cfg: Config) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    base = y[:, :cfg.baseline_n]
    mu = np.median(base, axis=1)
    mad = 1.4826 * np.median(np.abs(base - mu[:, None]), axis=1)
    mad = np.maximum(mad, 1e-8)

    centered = base - mu[:, None]
    denom = np.sum(centered[:, :-1] ** 2, axis=1)
    numer = np.sum(centered[:, 1:] * centered[:, :-1], axis=1)
    phi_hat = np.divide(numer, denom, out=np.zeros_like(numer), where=denom > 1e-12)
    phi_hat = np.clip(phi_hat, 0.0, 0.8)

    all_centered = y - mu[:, None]
    z = np.empty_like(y, dtype=np.float64)
    z[:, 0] = all_centered[:, 0] / mad
    z[:, 1:] = (
        all_centered[:, 1:] - phi_hat[:, None] * all_centered[:, :-1]
    ) / mad[:, None]
    return z, mu, phi_hat


def rolling_slope_t_score(z: np.ndarray, windows: Iterable[int]) -> np.ndarray:
    n, t = z.shape
    out = np.zeros((n, t), dtype=np.float64)

    for w in windows:
        if w < 3 or w > t:
            raise ValueError("Each regression window must be between 3 and sequence length.")
        view = sliding_window_view(z, window_shape=w, axis=1)
        x = np.arange(w, dtype=np.float64)
        xc = x - x.mean()
        sxx = np.sum(xc**2)

        mean_y = view.mean(axis=2)
        slope = np.sum(view * xc[None, None, :], axis=2) / sxx
        fitted = mean_y[:, :, None] + slope[:, :, None] * xc[None, None, :]
        resid = view - fitted
        sse = np.sum(resid**2, axis=2)
        mse = sse / (w - 2)
        se = np.sqrt(np.maximum(mse, 0.0) / sxx)
        regular = se > 1e-12
        tstat = np.divide(slope, se, out=np.zeros_like(slope), where=regular)
        # If residual variance is numerically zero, a strictly positive slope
        # has an unbounded one-sided t statistic; flat/negative slopes score zero.
        tstat = np.where((~regular) & (slope > 0.0), np.inf, tstat)
        tstat = np.maximum(tstat, 0.0)
        out[:, w - 1:] = np.maximum(out[:, w - 1:], tstat)
    return out


def cusum_score(z: np.ndarray, kappa: float) -> np.ndarray:
    n, t = z.shape
    out = np.zeros((n, t), dtype=np.float64)
    for k in range(1, t):
        out[:, k] = np.maximum(0.0, out[:, k - 1] + z[:, k] - kappa)
    return out


def flux_z_score(z: np.ndarray) -> np.ndarray:
    return np.maximum(z, 0.0)


def first_crossing(scores: np.ndarray, threshold: float, start: int) -> np.ndarray:
    crossed = scores[:, start:] >= threshold
    any_cross = crossed.any(axis=1)
    first = np.argmax(crossed, axis=1) + start
    return np.where(any_cross, first, -1).astype(np.int16)


def curve_max(scores: np.ndarray, start: int) -> np.ndarray:
    return np.max(scores[:, start:], axis=1)


def conservative_threshold(
    maxima_by_family: Dict[str, np.ndarray], target_fpr: float
) -> Tuple[float, Dict[str, float], Dict[str, int]]:
    family_thresholds: Dict[str, float] = {}
    allowed_counts: Dict[str, int] = {}
    for family, maxima in maxima_by_family.items():
        raw_values = np.asarray(maxima)
        if not np.issubdtype(raw_values.dtype, np.floating):
            raw_values = raw_values.astype(np.float64)
        n = raw_values.size
        allowed = int(math.floor(target_fpr * n + 1e-12))
        desc = np.sort(raw_values)[::-1]
        if allowed >= n:
            thr = -np.inf
        else:
            reference = desc[allowed]
            # Move one representable number upward in the score's own dtype.
            # This prevents an equality collision when float32 score arrays are
            # compared with a nominally float64 threshold.
            thr = np.nextafter(
                reference,
                np.array(np.inf, dtype=raw_values.dtype),
                dtype=raw_values.dtype,
            )
        family_thresholds[family] = float(thr)
        allowed_counts[family] = allowed

    threshold = max(family_thresholds.values())
    return float(threshold), family_thresholds, allowed_counts


def early_hits(
    scores: np.ndarray,
    threshold: float,
    onset: np.ndarray,
    t25: np.ndarray,
    start: int,
) -> Tuple[np.ndarray, np.ndarray]:
    first = first_crossing(scores, threshold, start)
    hit = (first >= onset) & (first <= t25)
    return hit, first


def clopper_pearson_upper(x: int, n: int, confidence: float = 0.95) -> float:
    if not (0 <= x <= n):
        raise ValueError("x must satisfy 0 <= x <= n")
    if n <= 0:
        raise ValueError("n must be positive")
    if x == n:
        return 1.0
    return float(beta_dist.ppf(confidence, x + 1, n - x))


def paired_stratified_bootstrap(
    m1_hits_by_family: Dict[str, np.ndarray],
    cusum_hits_by_family: Dict[str, np.ndarray],
    replicates: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    families = list(POSITIVE_FAMILIES)
    m1_boot = np.zeros(replicates, dtype=np.float64)
    cu_boot = np.zeros(replicates, dtype=np.float64)

    for family in families:
        a = np.asarray(m1_hits_by_family[family], dtype=np.int8)
        b = np.asarray(cusum_hits_by_family[family], dtype=np.int8)
        if a.shape != b.shape:
            raise ValueError("Paired outcomes must have equal shape.")
        n = a.size

        codes = a * 2 + b
        counts = np.bincount(codes, minlength=4)
        probs = counts / n
        draws = rng.multinomial(n, probs, size=replicates)

        m1_mean = (draws[:, 2] + draws[:, 3]) / n
        cu_mean = (draws[:, 1] + draws[:, 3]) / n
        m1_boot += m1_mean / len(families)
        cu_boot += cu_mean / len(families)

    return pd.DataFrame(
        {
            "m1_recall": m1_boot,
            "cusum_recall": cu_boot,
            "delta": m1_boot - cu_boot,
        }
    )


def evaluate_development(cfg: Config) -> Tuple[dict, dict]:
    seed_seq = np.random.SeedSequence(cfg.development_root_seed)
    children = seed_seq.spawn(len(POSITIVE_FAMILIES) + len(NEGATIVE_FAMILIES))
    rngs = [np.random.default_rng(s) for s in children]

    positive_scores: Dict[str, dict] = {}
    negative_scores: Dict[str, dict] = {}

    for family, rng in zip(POSITIVE_FAMILIES, rngs[:len(POSITIVE_FAMILIES)]):
        data = generate_positive_family(family, cfg.development_n_per_family, rng, cfg)
        z, _, _ = causal_normalize(data.y, cfg)
        positive_scores[family] = {
            "onset": data.onset,
            "t25": data.t25,
            "m1": rolling_slope_t_score(z, cfg.m1_windows).astype(np.float32),
            "flux_z": flux_z_score(z).astype(np.float32),
            "cusum": {
                str(k): cusum_score(z, k).astype(np.float32)
                for k in cfg.cusum_kappas
            },
        }

    for family, rng in zip(NEGATIVE_FAMILIES, rngs[len(POSITIVE_FAMILIES):]):
        data = generate_negative_family(family, cfg.development_n_per_family, rng, cfg)
        z, _, _ = causal_normalize(data.y, cfg)
        negative_scores[family] = {
            "m1": rolling_slope_t_score(z, cfg.m1_windows).astype(np.float32),
            "flux_z": flux_z_score(z).astype(np.float32),
            "cusum": {
                str(k): cusum_score(z, k).astype(np.float32)
                for k in cfg.cusum_kappas
            },
        }

    thresholds: Dict[str, float] = {}
    dev_rows = []

    for detector in ("m1", "flux_z"):
        maxima = {
            family: curve_max(negative_scores[family][detector], cfg.eval_start)
            for family in NEGATIVE_FAMILIES
        }
        thr, fam_thr, allowed = conservative_threshold(maxima, cfg.development_fpr_target)
        thresholds[detector] = thr

        for family in NEGATIVE_FAMILIES:
            x = int(np.sum(maxima[family] >= thr))
            dev_rows.append(
                {
                    "detector": detector,
                    "variant": "",
                    "family": family,
                    "kind": "negative",
                    "threshold": thr,
                    "alerts": x,
                    "n": len(maxima[family]),
                    "rate": x / len(maxima[family]),
                    "family_specific_threshold": fam_thr[family],
                    "allowed": allowed[family],
                }
            )

        for family in POSITIVE_FAMILIES:
            hits, _ = early_hits(
                positive_scores[family][detector],
                thr,
                positive_scores[family]["onset"],
                positive_scores[family]["t25"],
                cfg.eval_start,
            )
            dev_rows.append(
                {
                    "detector": detector,
                    "variant": "",
                    "family": family,
                    "kind": "positive",
                    "threshold": thr,
                    "alerts": int(hits.sum()),
                    "n": len(hits),
                    "rate": float(hits.mean()),
                    "family_specific_threshold": np.nan,
                    "allowed": np.nan,
                }
            )

    cusum_candidates = []
    for kappa in cfg.cusum_kappas:
        key = str(kappa)
        maxima = {
            family: curve_max(negative_scores[family]["cusum"][key], cfg.eval_start)
            for family in NEGATIVE_FAMILIES
        }
        thr, fam_thr, allowed = conservative_threshold(maxima, cfg.development_fpr_target)
        recalls = {}
        for family in POSITIVE_FAMILIES:
            hits, _ = early_hits(
                positive_scores[family]["cusum"][key],
                thr,
                positive_scores[family]["onset"],
                positive_scores[family]["t25"],
                cfg.eval_start,
            )
            recalls[family] = float(hits.mean())
        worst_fpr = max(float(np.mean(maxima[f] >= thr)) for f in NEGATIVE_FAMILIES)
        cusum_candidates.append(
            {
                "kappa": kappa,
                "threshold": thr,
                "mean_early_recall": float(np.mean(list(recalls.values()))),
                "worst_fpr": worst_fpr,
                "family_recalls": recalls,
                "family_thresholds": fam_thr,
                "allowed": allowed,
            }
        )

    chosen = sorted(
        cusum_candidates,
        key=lambda row: (-row["mean_early_recall"], row["worst_fpr"], row["kappa"]),
    )[0]
    thresholds["cusum"] = float(chosen["threshold"])
    thresholds["cusum_kappa"] = float(chosen["kappa"])

    key = str(chosen["kappa"])
    for family in NEGATIVE_FAMILIES:
        maxima = curve_max(negative_scores[family]["cusum"][key], cfg.eval_start)
        x = int(np.sum(maxima >= chosen["threshold"]))
        dev_rows.append(
            {
                "detector": "cusum",
                "variant": f"kappa={chosen['kappa']}",
                "family": family,
                "kind": "negative",
                "threshold": chosen["threshold"],
                "alerts": x,
                "n": len(maxima),
                "rate": x / len(maxima),
                "family_specific_threshold": chosen["family_thresholds"][family],
                "allowed": chosen["allowed"][family],
            }
        )
    for family in POSITIVE_FAMILIES:
        hits, _ = early_hits(
            positive_scores[family]["cusum"][key],
            chosen["threshold"],
            positive_scores[family]["onset"],
            positive_scores[family]["t25"],
            cfg.eval_start,
        )
        dev_rows.append(
            {
                "detector": "cusum",
                "variant": f"kappa={chosen['kappa']}",
                "family": family,
                "kind": "positive",
                "threshold": chosen["threshold"],
                "alerts": int(hits.sum()),
                "n": len(hits),
                "rate": float(hits.mean()),
                "family_specific_threshold": np.nan,
                "allowed": np.nan,
            }
        )

    details = {
        "thresholds": thresholds,
        "cusum_candidates": cusum_candidates,
        "development_seed_children": [
            {"entropy": s.entropy, "spawn_key": list(s.spawn_key)} for s in children
        ],
    }
    return details, {"rows": dev_rows}


def _evaluate_holdout_batch(
    batch_index: int,
    seed_seq: np.random.SeedSequence,
    thresholds: dict,
    cfg: Config,
) -> Tuple[list, list, list]:
    children = seed_seq.spawn(len(POSITIVE_FAMILIES) + len(NEGATIVE_FAMILIES))
    rngs = [np.random.default_rng(s) for s in children]

    positive_records = []
    negative_records = []
    score_records = []

    for family, rng in zip(POSITIVE_FAMILIES, rngs[:len(POSITIVE_FAMILIES)]):
        data = generate_positive_family(
            family, cfg.holdout_n_per_family_per_batch, rng, cfg
        )
        z, _, _ = causal_normalize(data.y, cfg)
        scores = {
            "m1": rolling_slope_t_score(z, cfg.m1_windows),
            "cusum": cusum_score(z, thresholds["cusum_kappa"]),
            "flux_z": flux_z_score(z),
        }

        detector_hits = {}
        for detector, score in scores.items():
            hits, first = early_hits(
                score,
                thresholds[detector],
                data.onset,
                data.t25,
                cfg.eval_start,
            )
            detector_hits[detector] = hits
            maxima = curve_max(score, cfg.eval_start)

            for i in range(len(hits)):
                positive_records.append(
                    {
                        "batch": batch_index,
                        "family": family,
                        "curve": i,
                        "detector": detector,
                        "hit": bool(hits[i]),
                        "first_crossing": int(first[i]),
                        "onset": int(data.onset[i]),
                        "t25": int(data.t25[i]),
                        "max_score": float(maxima[i]),
                    }
                )

        for i in range(cfg.holdout_n_per_family_per_batch):
            score_records.append(
                {
                    "batch": batch_index,
                    "family": family,
                    "label": 1,
                    "curve": i,
                    "m1_max": float(curve_max(scores["m1"], cfg.eval_start)[i]),
                    "cusum_max": float(curve_max(scores["cusum"], cfg.eval_start)[i]),
                    "flux_z_max": float(curve_max(scores["flux_z"], cfg.eval_start)[i]),
                }
            )

    for family, rng in zip(NEGATIVE_FAMILIES, rngs[len(POSITIVE_FAMILIES):]):
        data = generate_negative_family(
            family, cfg.holdout_n_per_family_per_batch, rng, cfg
        )
        z, _, _ = causal_normalize(data.y, cfg)
        scores = {
            "m1": rolling_slope_t_score(z, cfg.m1_windows),
            "cusum": cusum_score(z, thresholds["cusum_kappa"]),
            "flux_z": flux_z_score(z),
        }

        for detector, score in scores.items():
            first = first_crossing(score, thresholds[detector], cfg.eval_start)
            maxima = curve_max(score, cfg.eval_start)
            alerts = first >= 0
            for i in range(len(alerts)):
                negative_records.append(
                    {
                        "batch": batch_index,
                        "family": family,
                        "curve": i,
                        "detector": detector,
                        "alert": bool(alerts[i]),
                        "first_crossing": int(first[i]),
                        "max_score": float(maxima[i]),
                    }
                )

        maxima_dict = {d: curve_max(s, cfg.eval_start) for d, s in scores.items()}
        for i in range(cfg.holdout_n_per_family_per_batch):
            score_records.append(
                {
                    "batch": batch_index,
                    "family": family,
                    "label": 0,
                    "curve": i,
                    "m1_max": float(maxima_dict["m1"][i]),
                    "cusum_max": float(maxima_dict["cusum"][i]),
                    "flux_z_max": float(maxima_dict["flux_z"][i]),
                }
            )

    return positive_records, negative_records, score_records


def evaluate_holdout(thresholds: dict, cfg: Config) -> dict:
    root_seq = np.random.SeedSequence(cfg.holdout_root_seed)
    batch_seqs = root_seq.spawn(cfg.holdout_batches)
    positive_all = []
    negative_all = []
    score_all = []
    batch_seed_records = []

    for batch_index, seq in enumerate(batch_seqs):
        pos, neg, scr = _evaluate_holdout_batch(batch_index, seq, thresholds, cfg)
        positive_all.extend(pos)
        negative_all.extend(neg)
        score_all.extend(scr)
        batch_seed_records.append(
            {
                "batch": batch_index,
                "entropy": seq.entropy,
                "spawn_key": list(seq.spawn_key),
            }
        )

    pos_df = pd.DataFrame(positive_all)
    neg_df = pd.DataFrame(negative_all)
    score_df = pd.DataFrame(score_all)

    summary_rows = []
    for detector in ("m1", "cusum", "flux_z"):
        subp = pos_df[pos_df.detector == detector]
        for family in POSITIVE_FAMILIES:
            s = subp[subp.family == family]
            summary_rows.append(
                {
                    "detector": detector,
                    "kind": "positive",
                    "family": family,
                    "successes": int(s.hit.sum()),
                    "n": len(s),
                    "rate": float(s.hit.mean()),
                    "cp_upper_95": np.nan,
                }
            )

        subn = neg_df[neg_df.detector == detector]
        for family in NEGATIVE_FAMILIES:
            s = subn[subn.family == family]
            x = int(s.alert.sum())
            summary_rows.append(
                {
                    "detector": detector,
                    "kind": "negative",
                    "family": family,
                    "successes": x,
                    "n": len(s),
                    "rate": x / len(s),
                    "cp_upper_95": clopper_pearson_upper(x, len(s)),
                }
            )

    summary_df = pd.DataFrame(summary_rows)

    m1_hits = {}
    cu_hits = {}
    for family in POSITIVE_FAMILIES:
        m1_hits[family] = (
            pos_df[(pos_df.detector == "m1") & (pos_df.family == family)]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )
        cu_hits[family] = (
            pos_df[(pos_df.detector == "cusum") & (pos_df.family == family)]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )

    boot = paired_stratified_bootstrap(
        m1_hits,
        cu_hits,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed,
    )
    ci = {
        "m1_recall_point": float(np.mean(np.concatenate(list(m1_hits.values())))),
        "cusum_recall_point": float(np.mean(np.concatenate(list(cu_hits.values())))),
        "delta_point": float(
            np.mean(np.concatenate(list(m1_hits.values())))
            - np.mean(np.concatenate(list(cu_hits.values())))
        ),
        "m1_recall_lower_95": float(np.quantile(boot.m1_recall, 0.05)),
        "m1_recall_upper_95": float(np.quantile(boot.m1_recall, 0.95)),
        "cusum_recall_lower_95": float(np.quantile(boot.cusum_recall, 0.05)),
        "cusum_recall_upper_95": float(np.quantile(boot.cusum_recall, 0.95)),
        "delta_lower_95": float(np.quantile(boot.delta, 0.05)),
        "delta_upper_95": float(np.quantile(boot.delta, 0.95)),
    }

    batch_rows = []
    for batch in range(cfg.holdout_batches):
        for detector in ("m1", "cusum", "flux_z"):
            s = pos_df[(pos_df.batch == batch) & (pos_df.detector == detector)]
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
    pivot = batch_df.pivot(index="batch", columns="detector", values="early_recall")
    pivot["delta_m1_minus_cusum"] = pivot["m1"] - pivot["cusum"]
    positive_batches = int(np.sum(pivot["delta_m1_minus_cusum"] > 0))

    family_delta = {}
    for family in POSITIVE_FAMILIES:
        family_delta[family] = float(m1_hits[family].mean() - cu_hits[family].mean())

    secondary_rows = []
    y_true = score_df.label.to_numpy()
    for detector, col in (
        ("m1", "m1_max"),
        ("cusum", "cusum_max"),
        ("flux_z", "flux_z_max"),
    ):
        values = score_df[col].to_numpy()
        secondary_rows.append(
            {
                "detector": detector,
                "auroc": float(roc_auc_score(y_true, values)),
                "average_precision": float(average_precision_score(y_true, values)),
            }
        )
    secondary_df = pd.DataFrame(secondary_rows)

    fpr_passes = []
    for family in NEGATIVE_FAMILIES:
        row = summary_df[
            (summary_df.detector == "m1")
            & (summary_df.kind == "negative")
            & (summary_df.family == family)
        ].iloc[0]
        fpr_passes.append(float(row.cp_upper_95) <= cfg.holdout_fpr_upper_limit)

    criterion_1 = bool(all(fpr_passes))
    criterion_2 = ci["m1_recall_lower_95"] >= cfg.minimum_recall_lower_ci
    criterion_3 = ci["delta_lower_95"] >= cfg.minimum_delta_lower_ci
    criterion_4 = sum(v >= 0 for v in family_delta.values()) >= 3
    criterion_5 = positive_batches >= 15

    victory = all([criterion_1, criterion_2, criterion_3, criterion_4, criterion_5])
    strong_failure = (
        (not criterion_1)
        or (ci["delta_upper_95"] <= 0.0)
    )
    verdict = "PASS" if victory else ("STRONG_FAIL" if strong_failure else "INCONCLUSIVE")

    verdict_details = {
        "verdict": verdict,
        "criterion_1_all_negative_fpr_cp_upper_le_0_01": criterion_1,
        "criterion_2_m1_recall_lower_ci_ge_0_30": criterion_2,
        "criterion_3_delta_lower_ci_ge_0_10": criterion_3,
        "criterion_4_three_of_four_family_deltas_nonnegative": criterion_4,
        "criterion_5_at_least_15_of_20_batches_positive": criterion_5,
        "positive_batches": positive_batches,
        "family_delta": family_delta,
        **ci,
    }

    return {
        "positive_df": pos_df,
        "negative_df": neg_df,
        "score_df": score_df,
        "summary_df": summary_df,
        "bootstrap_df": boot,
        "batch_df": batch_df,
        "batch_pivot_df": pivot.reset_index(),
        "secondary_df": secondary_df,
        "batch_seed_records": batch_seed_records,
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
    }
    path.write_text(json.dumps(env, indent=2), encoding="utf-8")


def run_all(output_dir: Path, cfg: Config | None = None) -> dict:
    cfg = cfg or Config()
    output_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()

    dev_details, dev_table = evaluate_development(cfg)
    thresholds = dev_details["thresholds"]

    (output_dir / "FROZEN_THRESHOLDS.json").write_text(
        json.dumps(dev_details, indent=2), encoding="utf-8"
    )
    pd.DataFrame(dev_table["rows"]).to_csv(
        output_dir / "development_metrics.csv", index=False
    )

    holdout = evaluate_holdout(thresholds, cfg)
    holdout["positive_df"].to_csv(output_dir / "holdout_positive_curves.csv", index=False)
    holdout["negative_df"].to_csv(output_dir / "holdout_negative_curves.csv", index=False)
    holdout["score_df"].to_csv(output_dir / "holdout_discrimination_scores.csv", index=False)
    holdout["summary_df"].to_csv(output_dir / "holdout_summary.csv", index=False)
    holdout["bootstrap_df"].to_csv(output_dir / "bootstrap_10000.csv", index=False)
    holdout["batch_df"].to_csv(output_dir / "holdout_by_batch.csv", index=False)
    holdout["batch_pivot_df"].to_csv(output_dir / "holdout_batch_deltas.csv", index=False)
    holdout["secondary_df"].to_csv(output_dir / "secondary_metrics.csv", index=False)

    (output_dir / "HOLDOUT_SEEDS.json").write_text(
        json.dumps(holdout["batch_seed_records"], indent=2), encoding="utf-8"
    )
    (output_dir / "VERDICT.json").write_text(
        json.dumps(holdout["verdict"], indent=2), encoding="utf-8"
    )
    write_environment(output_dir / "ENVIRONMENT.json")

    elapsed = time.perf_counter() - start
    run_meta = {
        "elapsed_seconds": elapsed,
        "thresholds": thresholds,
        "verdict": holdout["verdict"]["verdict"],
    }
    (output_dir / "RUN_METADATA.json").write_text(
        json.dumps(run_meta, indent=2), encoding="utf-8"
    )

    manifest = {}
    for path in sorted(output_dir.glob("*")):
        if path.is_file():
            manifest[path.name] = sha256_file(path)
    (output_dir / "SHA256SUMS.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return {
        "development": dev_details,
        "holdout": holdout,
        "elapsed_seconds": elapsed,
    }
