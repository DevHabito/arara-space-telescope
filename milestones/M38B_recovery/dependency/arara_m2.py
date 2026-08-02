
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


POSITIVE_SHAPES = ("linear", "power_law", "exponential", "logistic")
POSITIVE_CONTEXTS = ("clean", "concurrent")
POSITIVE_STRATA = tuple(
    f"{shape}__{context}"
    for shape in POSITIVE_SHAPES
    for context in POSITIVE_CONTEXTS
)
NEGATIVE_FAMILIES = (
    "quiet",
    "shared_ramp",
    "shared_step",
    "shared_bump",
    "shared_oscillation",
)
SHARED_ARTIFACT_FAMILIES = (
    "shared_ramp",
    "shared_step",
    "shared_bump",
    "shared_oscillation",
)


@dataclass(frozen=True)
class Config:
    version: str = "2.0"
    development_root_seed: int = 2026072801
    holdout_root_seed: int = 2026072802
    bootstrap_seed: int = 2026072803

    n_time: int = 180
    burn_in: int = 200
    baseline_n: int = 50
    eval_start: int = 50
    n_references: int = 8

    onset_low: int = 80
    onset_high: int = 110
    duration_low: int = 24
    duration_high: int = 60
    event_snr_low: float = 3.0
    event_snr_high: float = 7.0
    artifact_snr_low: float = 3.0
    artifact_snr_high: float = 7.0

    common_phi_low: float = 0.2
    common_phi_high: float = 0.8
    common_innovation_sd: float = 0.5

    star_phi_low: float = 0.0
    star_phi_high: float = 0.5
    star_innovation_sd_low: float = 0.8
    star_innovation_sd_high: float = 1.2

    coupling_low: float = 0.7
    coupling_high: float = 1.3
    coupling_multiplier_low: float = 0.9
    coupling_multiplier_high: float = 1.1

    reference_impulse_probability: float = 0.30

    detector_windows: Tuple[int, ...] = (8, 16, 32)

    development_n_per_stratum: int = 2000
    holdout_total_n_per_stratum: int = 5000
    holdout_batches: int = 20
    holdout_n_per_stratum_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_cm_recall_lower_ci: float = 0.30
    minimum_delta_lower_ci: float = 0.15
    clean_noninferiority_margin: float = -0.05
    bootstrap_replicates: int = 10_000


@dataclass
class FieldData:
    y: np.ndarray
    target_signal: np.ndarray
    onset: np.ndarray
    t25: np.ndarray
    beta_truth_proxy: np.ndarray
    artifact_family: np.ndarray


def _ar1_process(
    rng: np.random.Generator,
    phi: np.ndarray,
    innovation_sd: np.ndarray,
    n_time: int,
    burn_in: int,
    student_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    phi and innovation_sd have shape (...). Returns shape (..., n_time).
    """
    shape = phi.shape
    total = n_time + burn_in
    innovations = rng.standard_normal((*shape, total))

    if student_mask is not None and np.any(student_mask):
        count = int(np.sum(student_mask))
        innovations[student_mask] = (
            rng.standard_t(df=5, size=(count, total)) * math.sqrt(3.0 / 5.0)
        )
    innovations *= innovation_sd[..., None]

    out = np.zeros_like(innovations, dtype=np.float64)
    out[..., 0] = innovations[..., 0]
    for k in range(1, total):
        out[..., k] = phi * out[..., k - 1] + innovations[..., k]
    return out[..., burn_in:]


def _normalized_logistic(x: np.ndarray, q: np.ndarray) -> np.ndarray:
    g = 1.0 / (1.0 + np.exp(-q[:, None] * (x - 0.5)))
    g0 = 1.0 / (1.0 + np.exp(q / 2.0))
    g1 = 1.0 / (1.0 + np.exp(-q / 2.0))
    return (g - g0[:, None]) / (g1 - g0)[:, None]


def _event_shape(
    shape: str,
    k: np.ndarray,
    onset: np.ndarray,
    duration: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    x = np.clip((k - onset[:, None]) / duration[:, None], 0.0, 1.0)
    if shape == "linear":
        return x
    if shape == "power_law":
        gamma = rng.uniform(1.5, 3.0, size=len(onset))
        return x ** gamma[:, None]
    if shape == "exponential":
        beta = rng.uniform(1.0, 4.0, size=len(onset))
        return (np.exp(beta[:, None] * x) - 1.0) / (
            np.exp(beta) - 1.0
        )[:, None]
    if shape == "logistic":
        q = rng.uniform(6.0, 12.0, size=len(onset))
        return _normalized_logistic(x, q)
    raise ValueError(f"Unknown event shape: {shape}")


def _shared_artifact_shape(
    family: str,
    k: np.ndarray,
    onset: np.ndarray,
    duration: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    n = len(onset)
    if family == "shared_ramp":
        u = np.clip((k - onset[:, None]) / duration[:, None], 0.0, 1.0)
        return u
    if family == "shared_step":
        return (k >= onset[:, None]).astype(np.float64)
    if family == "shared_bump":
        u = (k - onset[:, None]) / duration[:, None]
        active = (u >= 0.0) & (u <= 1.0)
        return np.where(active, np.sin(np.pi * u), 0.0)
    if family == "shared_oscillation":
        period = rng.integers(16, 49, size=n)
        active = k >= onset[:, None]
        return np.where(
            active,
            np.sin(2.0 * np.pi * (k - onset[:, None]) / period[:, None]),
            0.0,
        )
    raise ValueError(f"Unknown shared artifact family: {family}")


def _generate_base_field(
    n: int, rng: np.random.Generator, cfg: Config
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_stars = 1 + cfg.n_references

    common_phi = rng.uniform(cfg.common_phi_low, cfg.common_phi_high, size=n)
    common_sd = np.full(n, cfg.common_innovation_sd, dtype=np.float64)
    common = _ar1_process(
        rng,
        common_phi,
        common_sd,
        cfg.n_time,
        cfg.burn_in,
        student_mask=None,
    )

    star_phi = rng.uniform(
        cfg.star_phi_low, cfg.star_phi_high, size=(n, n_stars)
    )
    star_innov_sd = rng.uniform(
        cfg.star_innovation_sd_low,
        cfg.star_innovation_sd_high,
        size=(n, n_stars),
    )
    student_mask = rng.random((n, n_stars)) < 0.5
    individual = _ar1_process(
        rng,
        star_phi,
        star_innov_sd,
        cfg.n_time,
        cfg.burn_in,
        student_mask=student_mask,
    )

    coupling = rng.uniform(
        cfg.coupling_low, cfg.coupling_high, size=(n, n_stars)
    )
    y = coupling[:, :, None] * common[:, None, :] + individual

    stationary_sd = star_innov_sd / np.sqrt(1.0 - star_phi**2)

    # A rough truth proxy only for diagnostics; the actual residualization
    # estimates beta from baseline data.
    ref_mean_coupling = np.median(coupling[:, 1:], axis=1)
    beta_proxy = coupling[:, 0] / ref_mean_coupling

    return y, stationary_sd, coupling, common, beta_proxy


def _inject_reference_impulse(
    y: np.ndarray,
    stationary_sd: np.ndarray,
    rng: np.random.Generator,
    cfg: Config,
) -> None:
    n = y.shape[0]
    contaminated = rng.random(n) < cfg.reference_impulse_probability
    indices = np.flatnonzero(contaminated)
    if len(indices) == 0:
        return

    chosen_ref = rng.integers(1, cfg.n_references + 1, size=len(indices))
    starts = rng.integers(60, 179, size=len(indices))
    lengths = rng.integers(1, 3, size=len(indices))
    amp_factor = rng.uniform(
        cfg.artifact_snr_low, cfg.artifact_snr_high, size=len(indices)
    )

    for row, ref, start, length, factor in zip(
        indices, chosen_ref, starts, lengths, amp_factor
    ):
        stop = min(cfg.n_time, int(start + length))
        y[row, ref, start:stop] += factor * stationary_sd[row, ref]


def _inject_shared_artifact(
    y: np.ndarray,
    stationary_sd: np.ndarray,
    coupling: np.ndarray,
    family: str,
    onset: np.ndarray,
    duration: np.ndarray,
    rng: np.random.Generator,
    cfg: Config,
) -> None:
    n, n_stars, _ = y.shape
    k = np.arange(cfg.n_time)[None, :]
    shape = _shared_artifact_shape(family, k, onset, duration, rng)

    amplitude = rng.uniform(
        cfg.artifact_snr_low, cfg.artifact_snr_high, size=n
    ) * stationary_sd[:, 0]

    multiplier = rng.uniform(
        cfg.coupling_multiplier_low,
        cfg.coupling_multiplier_high,
        size=(n, n_stars),
    )
    star_amp = coupling * multiplier * amplitude[:, None]
    y += star_amp[:, :, None] * shape[:, None, :]


def generate_positive_stratum(
    shape: str,
    context: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> FieldData:
    if shape not in POSITIVE_SHAPES:
        raise ValueError(shape)
    if context not in POSITIVE_CONTEXTS:
        raise ValueError(context)

    y, stationary_sd, coupling, common, beta_proxy = _generate_base_field(
        n, rng, cfg
    )
    _inject_reference_impulse(y, stationary_sd, rng, cfg)

    onset = rng.integers(cfg.onset_low, cfg.onset_high + 1, size=n)
    duration = rng.integers(cfg.duration_low, cfg.duration_high + 1, size=n)
    amplitude = rng.uniform(
        cfg.event_snr_low, cfg.event_snr_high, size=n
    ) * stationary_sd[:, 0]

    k = np.arange(cfg.n_time)[None, :]
    shape_values = _event_shape(shape, k, onset, duration, rng)
    target_signal = amplitude[:, None] * shape_values
    y[:, 0, :] += target_signal

    artifact_family = np.full(n, "none", dtype=object)
    if context == "concurrent":
        selected = rng.integers(0, len(SHARED_ARTIFACT_FAMILIES), size=n)
        delta = rng.integers(-10, 11, size=n)
        art_onset = np.clip(onset + delta, 60, 120)
        art_duration = rng.integers(
            cfg.duration_low, cfg.duration_high + 1, size=n
        )
        for idx, family in enumerate(SHARED_ARTIFACT_FAMILIES):
            mask = selected == idx
            if not np.any(mask):
                continue
            # Boolean indexing returns a copy. Inject into an explicit
            # temporary block and assign it back so the concurrent artifact
            # is actually present in the original field.
            y_block = y[mask].copy()
            _inject_shared_artifact(
                y_block,
                stationary_sd[mask],
                coupling[mask],
                family,
                art_onset[mask],
                art_duration[mask],
                rng,
                cfg,
            )
            y[mask] = y_block
            artifact_family[mask] = family

    reached = target_signal >= (0.25 * amplitude)[:, None]
    t25 = np.argmax(reached, axis=1)
    if not np.all(reached[np.arange(n), t25]):
        raise RuntimeError("All positive events must reach 25% amplitude.")

    return FieldData(
        y=y,
        target_signal=target_signal,
        onset=onset.astype(np.int16),
        t25=t25.astype(np.int16),
        beta_truth_proxy=beta_proxy,
        artifact_family=artifact_family,
    )


def generate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> FieldData:
    if family not in NEGATIVE_FAMILIES:
        raise ValueError(family)

    y, stationary_sd, coupling, common, beta_proxy = _generate_base_field(
        n, rng, cfg
    )
    _inject_reference_impulse(y, stationary_sd, rng, cfg)

    artifact_family = np.full(n, family, dtype=object)
    if family != "quiet":
        onset = rng.integers(cfg.onset_low, cfg.onset_high + 1, size=n)
        duration = rng.integers(
            cfg.duration_low, cfg.duration_high + 1, size=n
        )
        _inject_shared_artifact(
            y,
            stationary_sd,
            coupling,
            family,
            onset,
            duration,
            rng,
            cfg,
        )

    no_time = np.full(n, -1, dtype=np.int16)
    return FieldData(
        y=y,
        target_signal=np.zeros((n, cfg.n_time), dtype=np.float64),
        onset=no_time,
        t25=no_time,
        beta_truth_proxy=beta_proxy,
        artifact_family=artifact_family,
    )


def normalize_field(
    y: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    base = y[:, :, :cfg.baseline_n]
    mu = np.median(base, axis=2)
    mad = 1.4826 * np.median(np.abs(base - mu[:, :, None]), axis=2)
    mad = np.maximum(mad, 1e-8)

    centered_base = base - mu[:, :, None]
    denom = np.sum(centered_base[:, :, :-1] ** 2, axis=2)
    numer = np.sum(
        centered_base[:, :, 1:] * centered_base[:, :, :-1], axis=2
    )
    phi_hat = np.divide(
        numer,
        denom,
        out=np.zeros_like(numer),
        where=denom > 1e-12,
    )
    phi_hat = np.clip(phi_hat, 0.0, 0.8)

    centered = y - mu[:, :, None]
    z = np.empty_like(y, dtype=np.float64)
    z[:, :, 0] = centered[:, :, 0] / mad
    z[:, :, 1:] = (
        centered[:, :, 1:]
        - phi_hat[:, :, None] * centered[:, :, :-1]
    ) / mad[:, :, None]

    q = np.median(z[:, 1:, :], axis=1)
    qb = q[:, 1:cfg.baseline_n]
    zb = z[:, 0, 1:cfg.baseline_n]
    qc = qb - qb.mean(axis=1, keepdims=True)
    zc = zb - zb.mean(axis=1, keepdims=True)
    beta_denom = np.sum(qc**2, axis=1)
    beta_numer = np.sum(qc * zc, axis=1)
    beta_hat = np.divide(
        beta_numer,
        beta_denom,
        out=np.zeros_like(beta_numer),
        where=beta_denom > 1e-12,
    )
    beta_hat = np.clip(beta_hat, 0.0, 3.0)

    residual = z[:, 0, :] - beta_hat[:, None] * q
    return z[:, 0, :], residual, q, beta_hat


def rolling_slope_t_score(
    z: np.ndarray, windows: Iterable[int]
) -> np.ndarray:
    n, t = z.shape
    out = np.zeros((n, t), dtype=np.float64)

    for w in windows:
        if w < 3 or w > t:
            raise ValueError("Invalid regression window.")
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
        tstat = np.divide(
            slope, se, out=np.zeros_like(slope), where=regular
        )
        tstat = np.where((~regular) & (slope > 0.0), np.inf, tstat)
        tstat = np.maximum(tstat, 0.0)
        out[:, w - 1:] = np.maximum(out[:, w - 1:], tstat)
    return out


def first_crossing(
    scores: np.ndarray, threshold: float, start: int
) -> np.ndarray:
    crossed = scores[:, start:] >= threshold
    any_cross = crossed.any(axis=1)
    first = np.argmax(crossed, axis=1) + start
    return np.where(any_cross, first, -1).astype(np.int16)


def curve_max(scores: np.ndarray, start: int) -> np.ndarray:
    return np.max(scores[:, start:], axis=1)


def early_hits(
    scores: np.ndarray,
    threshold: float,
    onset: np.ndarray,
    t25: np.ndarray,
    start: int,
) -> tuple[np.ndarray, np.ndarray]:
    first = first_crossing(scores, threshold, start)
    hit = (first >= onset) & (first <= t25)
    return hit, first


def conservative_threshold(
    maxima_by_family: Dict[str, np.ndarray],
    target_fpr: float,
) -> tuple[float, dict, dict]:
    family_thresholds = {}
    allowed_counts = {}
    for family, maxima in maxima_by_family.items():
        values = np.asarray(maxima)
        if not np.issubdtype(values.dtype, np.floating):
            values = values.astype(np.float64)
        n = values.size
        allowed = int(math.floor(target_fpr * n + 1e-12))
        desc = np.sort(values)[::-1]
        if allowed >= n:
            threshold = -np.inf
        else:
            reference = desc[allowed]
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


def clopper_pearson_upper(
    x: int, n: int, confidence: float = 0.95
) -> float:
    if not (0 <= x <= n):
        raise ValueError("x must satisfy 0 <= x <= n")
    if n <= 0:
        raise ValueError("n must be positive")
    if x == n:
        return 1.0
    return float(beta_dist.ppf(confidence, x + 1, n - x))


def _paired_stratified_bootstrap(
    cm_hits: Dict[str, np.ndarray],
    to_hits: Dict[str, np.ndarray],
    strata: tuple[str, ...],
    replicates: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cm_boot = np.zeros(replicates)
    to_boot = np.zeros(replicates)

    for stratum in strata:
        a = np.asarray(cm_hits[stratum], dtype=np.int8)
        b = np.asarray(to_hits[stratum], dtype=np.int8)
        if a.shape != b.shape:
            raise ValueError("Paired arrays differ in shape.")
        n = a.size
        codes = a * 2 + b
        counts = np.bincount(codes, minlength=4)
        probs = counts / n
        draws = rng.multinomial(n, probs, size=replicates)
        cm_mean = (draws[:, 2] + draws[:, 3]) / n
        to_mean = (draws[:, 1] + draws[:, 3]) / n
        cm_boot += cm_mean / len(strata)
        to_boot += to_mean / len(strata)

    return pd.DataFrame(
        {
            "cm_recall": cm_boot,
            "target_only_recall": to_boot,
            "delta": cm_boot - to_boot,
        }
    )


def evaluate_development(cfg: Config) -> tuple[dict, pd.DataFrame]:
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
        data = generate_positive_stratum(
            shape, context, cfg.development_n_per_stratum, rng, cfg
        )
        target, residual, q, beta_hat = normalize_field(data.y, cfg)
        positive[stratum] = {
            "onset": data.onset,
            "t25": data.t25,
            "target_only": rolling_slope_t_score(
                target, cfg.detector_windows
            ).astype(np.float32),
            "common_mode": rolling_slope_t_score(
                residual, cfg.detector_windows
            ).astype(np.float32),
            "beta_hat": beta_hat,
        }

    for family, rng in zip(
        NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]
    ):
        data = generate_negative_family(
            family, cfg.development_n_per_stratum, rng, cfg
        )
        target, residual, q, beta_hat = normalize_field(data.y, cfg)
        negative[family] = {
            "target_only": rolling_slope_t_score(
                target, cfg.detector_windows
            ).astype(np.float32),
            "common_mode": rolling_slope_t_score(
                residual, cfg.detector_windows
            ).astype(np.float32),
            "beta_hat": beta_hat,
        }

    thresholds = {}
    rows = []

    for detector in ("target_only", "common_mode"):
        maxima = {
            family: curve_max(negative[family][detector], cfg.eval_start)
            for family in NEGATIVE_FAMILIES
        }
        threshold, family_thresholds, allowed = conservative_threshold(
            maxima, cfg.development_fpr_target
        )
        thresholds[detector] = threshold

        for family in NEGATIVE_FAMILIES:
            x = int(np.sum(maxima[family] >= threshold))
            rows.append(
                {
                    "detector": detector,
                    "kind": "negative",
                    "stratum": family,
                    "threshold": threshold,
                    "family_specific_threshold": family_thresholds[family],
                    "successes": x,
                    "n": len(maxima[family]),
                    "rate": x / len(maxima[family]),
                    "allowed": allowed[family],
                }
            )

        for stratum in POSITIVE_STRATA:
            hits, _ = early_hits(
                positive[stratum][detector],
                threshold,
                positive[stratum]["onset"],
                positive[stratum]["t25"],
                cfg.eval_start,
            )
            rows.append(
                {
                    "detector": detector,
                    "kind": "positive",
                    "stratum": stratum,
                    "threshold": threshold,
                    "family_specific_threshold": np.nan,
                    "successes": int(hits.sum()),
                    "n": len(hits),
                    "rate": float(hits.mean()),
                    "allowed": np.nan,
                }
            )

    details = {
        "thresholds": thresholds,
        "development_seed_children": [
            {"entropy": s.entropy, "spawn_key": list(s.spawn_key)}
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
        data = generate_positive_stratum(
            shape,
            context,
            cfg.holdout_n_per_stratum_per_batch,
            rng,
            cfg,
        )
        target, residual, q, beta_hat = normalize_field(data.y, cfg)
        score_map = {
            "target_only": rolling_slope_t_score(
                target, cfg.detector_windows
            ),
            "common_mode": rolling_slope_t_score(
                residual, cfg.detector_windows
            ),
        }

        maxima = {
            detector: curve_max(score, cfg.eval_start)
            for detector, score in score_map.items()
        }

        for detector, score in score_map.items():
            hits, first = early_hits(
                score,
                thresholds[detector],
                data.onset,
                data.t25,
                cfg.eval_start,
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
                        "beta_hat": float(beta_hat[i]),
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
                    "target_only_max": float(
                        maxima["target_only"][i]
                    ),
                    "common_mode_max": float(
                        maxima["common_mode"][i]
                    ),
                }
            )

    for family, rng in zip(
        NEGATIVE_FAMILIES, rngs[len(POSITIVE_STRATA):]
    ):
        data = generate_negative_family(
            family,
            cfg.holdout_n_per_stratum_per_batch,
            rng,
            cfg,
        )
        target, residual, q, beta_hat = normalize_field(data.y, cfg)
        score_map = {
            "target_only": rolling_slope_t_score(
                target, cfg.detector_windows
            ),
            "common_mode": rolling_slope_t_score(
                residual, cfg.detector_windows
            ),
        }
        maxima = {
            detector: curve_max(score, cfg.eval_start)
            for detector, score in score_map.items()
        }

        for detector, score in score_map.items():
            first = first_crossing(
                score, thresholds[detector], cfg.eval_start
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
                        "beta_hat": float(beta_hat[i]),
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
                    "target_only_max": float(
                        maxima["target_only"][i]
                    ),
                    "common_mode_max": float(
                        maxima["common_mode"][i]
                    ),
                }
            )

    return positive_records, negative_records, score_records


def evaluate_holdout(thresholds: dict, cfg: Config) -> dict:
    root_seq = np.random.SeedSequence(cfg.holdout_root_seed)
    batch_seqs = root_seq.spawn(cfg.holdout_batches)

    positive_all = []
    negative_all = []
    score_all = []
    seed_records = []

    for batch, seq in enumerate(batch_seqs):
        pos, neg, scores = _evaluate_holdout_batch(
            batch, seq, thresholds, cfg
        )
        positive_all.extend(pos)
        negative_all.extend(neg)
        score_all.extend(scores)
        seed_records.append(
            {
                "batch": batch,
                "entropy": seq.entropy,
                "spawn_key": list(seq.spawn_key),
            }
        )

    pos_df = pd.DataFrame(positive_all)
    neg_df = pd.DataFrame(negative_all)
    score_df = pd.DataFrame(score_all)

    summary_rows = []
    for detector in ("target_only", "common_mode"):
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
                    "cp_upper_95": clopper_pearson_upper(x, len(s)),
                }
            )

    summary_df = pd.DataFrame(summary_rows)

    cm_hits = {}
    to_hits = {}
    for stratum in POSITIVE_STRATA:
        cm_hits[stratum] = (
            pos_df[
                (pos_df.detector == "common_mode")
                & (pos_df.stratum == stratum)
            ]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )
        to_hits[stratum] = (
            pos_df[
                (pos_df.detector == "target_only")
                & (pos_df.stratum == stratum)
            ]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )

    global_boot = _paired_stratified_bootstrap(
        cm_hits,
        to_hits,
        POSITIVE_STRATA,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed,
    )
    clean_strata = tuple(
        f"{shape}__clean" for shape in POSITIVE_SHAPES
    )
    clean_boot = _paired_stratified_bootstrap(
        cm_hits,
        to_hits,
        clean_strata,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed + 1,
    )

    cm_global = float(
        np.mean([cm_hits[s].mean() for s in POSITIVE_STRATA])
    )
    to_global = float(
        np.mean([to_hits[s].mean() for s in POSITIVE_STRATA])
    )
    cm_clean = float(
        np.mean([cm_hits[s].mean() for s in clean_strata])
    )
    to_clean = float(
        np.mean([to_hits[s].mean() for s in clean_strata])
    )

    ci = {
        "cm_recall_point": cm_global,
        "target_only_recall_point": to_global,
        "delta_point": cm_global - to_global,
        "cm_recall_lower_95": float(
            np.quantile(global_boot.cm_recall, 0.05)
        ),
        "cm_recall_upper_95": float(
            np.quantile(global_boot.cm_recall, 0.95)
        ),
        "delta_lower_95": float(
            np.quantile(global_boot.delta, 0.05)
        ),
        "delta_upper_95": float(
            np.quantile(global_boot.delta, 0.95)
        ),
        "cm_clean_recall_point": cm_clean,
        "target_only_clean_recall_point": to_clean,
        "clean_delta_point": cm_clean - to_clean,
        "clean_delta_lower_95": float(
            np.quantile(clean_boot.delta, 0.05)
        ),
        "clean_delta_upper_95": float(
            np.quantile(clean_boot.delta, 0.95)
        ),
    }

    stratum_delta = {
        s: float(cm_hits[s].mean() - to_hits[s].mean())
        for s in POSITIVE_STRATA
    }

    batch_rows = []
    for batch in range(cfg.holdout_batches):
        for detector in ("target_only", "common_mode"):
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
    batch_pivot["delta_common_minus_target"] = (
        batch_pivot["common_mode"] - batch_pivot["target_only"]
    )
    positive_batches = int(
        np.sum(batch_pivot.delta_common_minus_target > 0)
    )

    secondary_rows = []
    y_true = score_df.label.to_numpy()
    for detector, column in (
        ("target_only", "target_only_max"),
        ("common_mode", "common_mode_max"),
    ):
        values = score_df[column].to_numpy()
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
            (summary_df.detector == "common_mode")
            & (summary_df.kind == "negative")
            & (summary_df.stratum == family)
        ].iloc[0]
        fpr_passes.append(
            float(row.cp_upper_95)
            <= cfg.holdout_fpr_upper_limit
        )

    criterion_1 = bool(all(fpr_passes))
    criterion_2 = (
        ci["cm_recall_lower_95"]
        >= cfg.minimum_cm_recall_lower_ci
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

    victory = all(
        [
            criterion_1,
            criterion_2,
            criterion_3,
            criterion_4,
            criterion_5,
            criterion_6,
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
        "criterion_1_common_mode_fpr_control": criterion_1,
        "criterion_2_common_mode_recall_lower_ge_0_30": criterion_2,
        "criterion_3_delta_lower_ge_0_15": criterion_3,
        "criterion_4_clean_noninferiority": criterion_4,
        "criterion_5_at_least_7_of_8_strata_nonnegative": criterion_5,
        "criterion_6_at_least_15_of_20_batches_positive": criterion_6,
        "positive_batches": positive_batches,
        "stratum_delta": stratum_delta,
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
    }
    path.write_text(json.dumps(env, indent=2), encoding="utf-8")
