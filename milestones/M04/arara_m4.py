
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable
import hashlib
import json
import math
import platform
import sys

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import beta as beta_dist
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
M2_DIR = ROOT / "m2"
M3_DIR = ROOT / "m3"
for dependency in (M2_DIR, M3_DIR):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

import arara_m2 as m2
import arara_m3 as m3


POSITIVE_SHAPES = m2.POSITIVE_SHAPES
POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "4.0"
    development_root_seed: int = 2026073001
    holdout_root_seed: int = 2026073002
    bootstrap_seed: int = 2026073003

    durations: tuple[int, ...] = (24, 36, 48, 60)
    prefix_levels: tuple[float, ...] = (0.10, 0.15, 0.20, 0.25)
    power_gammas: tuple[float, ...] = (1.5, 2.25, 3.0)
    exponential_betas: tuple[float, ...] = (1.0, 2.5, 4.0)
    logistic_qs: tuple[float, ...] = (6.0, 9.0, 12.0)
    minimum_template_length: int = 6

    development_n_per_stratum: int = 2000
    holdout_total_n_per_stratum: int = 5000
    holdout_batches: int = 20
    holdout_n_per_stratum_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01
    minimum_global_recall_lower_ci: float = 0.50
    minimum_stratum_recall_lower_ci: float = 0.30
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.45
    minimum_delta_vs_sbw_lower_ci: float = 0.20
    strong_fail_global_recall_upper: float = 0.20
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


def _shape_value(
    shape: str,
    x: np.ndarray | float,
    parameter: float | None,
) -> np.ndarray | float:
    x_arr = np.asarray(x, dtype=np.float64)
    if shape == "linear":
        out = x_arr
    elif shape == "power_law":
        if parameter is None:
            raise ValueError("Power-law requires gamma.")
        out = x_arr ** parameter
    elif shape == "exponential":
        if parameter is None:
            raise ValueError("Exponential requires beta.")
        out = np.expm1(parameter * x_arr) / np.expm1(parameter)
    elif shape == "logistic":
        if parameter is None:
            raise ValueError("Logistic requires q.")
        q = parameter
        g = 1.0 / (1.0 + np.exp(-q * (x_arr - 0.5)))
        g0 = 1.0 / (1.0 + np.exp(q / 2.0))
        g1 = 1.0 / (1.0 + np.exp(-q / 2.0))
        out = (g - g0) / (g1 - g0)
    else:
        raise ValueError(f"Unknown shape: {shape}")

    if np.isscalar(x):
        return float(out)
    return out


def _x_for_level(
    shape: str,
    level: float,
    parameter: float | None,
) -> float:
    if not (0.0 < level < 1.0):
        raise ValueError("Template level must be between zero and one.")

    if shape == "linear":
        return float(level)
    if shape == "power_law":
        if parameter is None:
            raise ValueError("Power-law requires gamma.")
        return float(level ** (1.0 / parameter))
    if shape == "exponential":
        if parameter is None:
            raise ValueError("Exponential requires beta.")
        return float(
            np.log1p(level * np.expm1(parameter)) / parameter
        )
    if shape == "logistic":
        if parameter is None:
            raise ValueError("Logistic requires q.")
        return float(
            brentq(
                lambda x: _shape_value(
                    "logistic", x, parameter
                )
                - level,
                0.0,
                1.0,
            )
        )
    raise ValueError(shape)


def build_template_bank(cfg: Config) -> dict:
    """
    Returns:
      metadata: list of retained template metadata, indexed by stable ID
      groups: {length: {"matrix": centered unit templates, "ids": IDs}}
    """
    candidates = []
    order = 0

    parameter_grid = {
        "linear": [(None, None)],
        "power_law": [
            ("gamma", value) for value in cfg.power_gammas
        ],
        "exponential": [
            ("beta", value) for value in cfg.exponential_betas
        ],
        "logistic": [
            ("q", value) for value in cfg.logistic_qs
        ],
    }

    for shape in (
        "linear",
        "power_law",
        "exponential",
        "logistic",
    ):
        for parameter_name, parameter in parameter_grid[shape]:
            for duration in cfg.durations:
                for level in cfg.prefix_levels:
                    x_end = _x_for_level(
                        shape, level, parameter
                    )
                    length = max(
                        cfg.minimum_template_length,
                        int(math.ceil(duration * x_end)) + 1,
                    )
                    x = np.linspace(0.0, x_end, length)
                    raw = np.asarray(
                        _shape_value(shape, x, parameter),
                        dtype=np.float64,
                    )
                    centered = raw - raw.mean()
                    norm = float(np.linalg.norm(centered))
                    if norm <= 1e-12:
                        raise RuntimeError(
                            "Degenerate matched-filter template."
                        )
                    unit = centered / norm
                    candidates.append(
                        {
                            "candidate_order": order,
                            "shape": shape,
                            "parameter_name": parameter_name,
                            "parameter": parameter,
                            "duration": int(duration),
                            "level": float(level),
                            "x_end": float(x_end),
                            "length": int(length),
                            "end_value": float(raw[-1]),
                            "unit": unit,
                        }
                    )
                    order += 1

    retained = []
    seen = set()
    groups_raw: dict[int, list[tuple[int, np.ndarray]]] = {}

    for candidate in candidates:
        key = (
            candidate["length"],
            tuple(np.round(candidate["unit"], 12)),
        )
        if key in seen:
            continue
        seen.add(key)

        template_id = len(retained)
        metadata = {
            key: value
            for key, value in candidate.items()
            if key != "unit"
        }
        metadata["template_id"] = template_id
        retained.append(metadata)
        groups_raw.setdefault(
            candidate["length"], []
        ).append((template_id, candidate["unit"]))

    groups = {}
    for length, entries in sorted(groups_raw.items()):
        groups[length] = {
            "ids": np.array(
                [entry[0] for entry in entries],
                dtype=np.int32,
            ),
            "matrix": np.stack(
                [entry[1] for entry in entries],
                axis=0,
            ).astype(np.float64),
        }

    return {
        "candidate_count": len(candidates),
        "retained_count": len(retained),
        "metadata": retained,
        "groups": groups,
    }


def serializable_bank(bank: dict) -> dict:
    return {
        "candidate_count": bank["candidate_count"],
        "retained_count": bank["retained_count"],
        "metadata": bank["metadata"],
        "groups": {
            str(length): {
                "template_ids": group["ids"].tolist(),
                "template_count": int(len(group["ids"])),
            }
            for length, group in bank["groups"].items()
        },
    }


def matched_filter_score(
    series: np.ndarray,
    bank: dict,
    template_chunk_size: int = 16,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Causal maximum t statistic and stable winning template ID.

    series shape: (n_curves, n_time)
    """
    z = np.asarray(series, dtype=np.float64)
    if z.ndim != 2:
        raise ValueError("series must be a 2D array.")
    n, t = z.shape

    out = np.zeros((n, t), dtype=np.float64)
    winner = np.full((n, t), -1, dtype=np.int32)

    csum = np.concatenate(
        [np.zeros((n, 1)), np.cumsum(z, axis=1)],
        axis=1,
    )
    csum2 = np.concatenate(
        [np.zeros((n, 1)), np.cumsum(z * z, axis=1)],
        axis=1,
    )

    for length, group in bank["groups"].items():
        if length > t:
            continue

        windows = np.lib.stride_tricks.sliding_window_view(
            z, window_shape=length, axis=1
        )
        sums = csum[:, length:] - csum[:, :-length]
        sums2 = csum2[:, length:] - csum2[:, :-length]
        centered_ss = np.maximum(
            sums2 - (sums * sums) / length,
            0.0,
        )
        y_norm = np.sqrt(centered_ss)

        matrices = group["matrix"]
        ids = group["ids"]
        current = out[:, length - 1:]
        current_winner = winner[:, length - 1:]

        for start in range(0, len(ids), template_chunk_size):
            stop = min(start + template_chunk_size, len(ids))
            matrix = matrices[start:stop]
            chunk_ids = ids[start:stop]

            # Templates are centered, so dot(window, template)
            # equals dot(centered_window, template).
            dots = np.einsum(
                "ntl,ml->ntm",
                windows,
                matrix,
                optimize=True,
            )
            corr = np.divide(
                dots,
                y_norm[:, :, None],
                out=np.zeros_like(dots),
                where=y_norm[:, :, None] > 1e-12,
            )
            corr = np.clip(corr, -1.0, 1.0)

            positive = corr > 0.0
            near_one = corr >= (1.0 - 1e-15)
            denom = np.maximum(1.0 - corr * corr, 1e-300)
            tscore = np.where(
                positive,
                corr * np.sqrt((length - 2.0) / denom),
                0.0,
            )
            tscore = np.where(near_one, np.inf, tscore)

            chunk_arg = np.argmax(tscore, axis=2)
            chunk_max = np.take_along_axis(
                tscore,
                chunk_arg[:, :, None],
                axis=2,
            )[:, :, 0]
            chunk_winner = chunk_ids[chunk_arg]

            better = chunk_max > current
            equal_better_id = (
                (chunk_max == current)
                & (chunk_max > 0.0)
                & (
                    (current_winner < 0)
                    | (chunk_winner < current_winner)
                )
            )
            update = better | equal_better_id
            current[update] = chunk_max[update]
            current_winner[update] = chunk_winner[update]

    return out, winner


def _winner_at_first_crossing(
    winner: np.ndarray,
    first: np.ndarray,
) -> np.ndarray:
    result = np.full(len(first), -1, dtype=np.int32)
    valid = first >= 0
    rows = np.flatnonzero(valid)
    result[valid] = winner[rows, first[valid]]
    return result


def clopper_pearson_lower(
    x: int,
    n: int,
    confidence: float = 0.95,
) -> float:
    if not (0 <= x <= n):
        raise ValueError("x must satisfy 0 <= x <= n.")
    if n <= 0:
        raise ValueError("n must be positive.")
    if x == 0:
        return 0.0
    alpha = 1.0 - confidence
    return float(beta_dist.ppf(alpha, x, n - x + 1))


def _paired_stratified_bootstrap(
    mf_hits: Dict[str, np.ndarray],
    sbw_hits: Dict[str, np.ndarray],
    replicates: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mf_boot = np.zeros(replicates)
    sbw_boot = np.zeros(replicates)

    for stratum in POSITIVE_STRATA:
        a = np.asarray(mf_hits[stratum], dtype=np.int8)
        b = np.asarray(sbw_hits[stratum], dtype=np.int8)
        if a.shape != b.shape:
            raise ValueError("Paired arrays differ in shape.")
        n = len(a)
        codes = a * 2 + b
        counts = np.bincount(codes, minlength=4)
        draws = rng.multinomial(
            n, counts / n, size=replicates
        )
        mf_mean = (draws[:, 2] + draws[:, 3]) / n
        sbw_mean = (draws[:, 1] + draws[:, 3]) / n
        mf_boot += mf_mean / len(POSITIVE_STRATA)
        sbw_boot += sbw_mean / len(POSITIVE_STRATA)

    return pd.DataFrame(
        {
            "mf_recall": mf_boot,
            "sbw_recall": sbw_boot,
            "delta": mf_boot - sbw_boot,
        }
    )


def evaluate_development(
    cfg: Config,
    bank: dict,
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

    positive = {}
    negative = {}

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
        residual, _, _ = m3.normalize_sbw(
            data.y, data_cfg
        )
        mf_score, _ = matched_filter_score(
            residual, bank
        )
        sbw_score = m2.rolling_slope_t_score(
            residual, data_cfg.detector_windows
        )
        positive[stratum] = {
            "onset": data.onset,
            "t25": data.t25,
            "matched_filter": mf_score.astype(np.float32),
            "sbw_slope": sbw_score.astype(np.float32),
        }

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
        residual, _, _ = m3.normalize_sbw(
            data.y, data_cfg
        )
        mf_score, _ = matched_filter_score(
            residual, bank
        )
        sbw_score = m2.rolling_slope_t_score(
            residual, data_cfg.detector_windows
        )
        negative[family] = {
            "matched_filter": mf_score.astype(np.float32),
            "sbw_slope": sbw_score.astype(np.float32),
        }

    thresholds = {}
    rows = []

    for detector in ("matched_filter", "sbw_slope"):
        maxima = {
            family: m2.curve_max(
                negative[family][detector],
                data_cfg.eval_start,
            )
            for family in NEGATIVE_FAMILIES
        }
        threshold, family_thresholds, allowed = (
            m2.conservative_threshold(
                maxima,
                cfg.development_fpr_target,
            )
        )
        thresholds[detector] = threshold

        for family in NEGATIVE_FAMILIES:
            alerts = int(
                np.sum(maxima[family] >= threshold)
            )
            rows.append(
                {
                    "detector": detector,
                    "kind": "negative",
                    "stratum": family,
                    "successes": alerts,
                    "n": len(maxima[family]),
                    "rate": alerts / len(maxima[family]),
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
        "template_bank": serializable_bank(bank),
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
    bank: dict,
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
        residual, _, _ = m3.normalize_sbw(
            data.y, data_cfg
        )
        mf_score, mf_winner = matched_filter_score(
            residual, bank
        )
        sbw_score = m2.rolling_slope_t_score(
            residual, data_cfg.detector_windows
        )
        score_map = {
            "matched_filter": mf_score,
            "sbw_slope": sbw_score,
        }
        maxima = {
            detector: m2.curve_max(
                score, data_cfg.eval_start
            )
            for detector, score in score_map.items()
        }

        for detector, score in score_map.items():
            hits, first = m2.early_hits(
                score,
                thresholds[detector],
                data.onset,
                data.t25,
                data_cfg.eval_start,
            )
            if detector == "matched_filter":
                winner_first = _winner_at_first_crossing(
                    mf_winner, first
                )
            else:
                winner_first = np.full(
                    len(first), -1, dtype=np.int32
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
                        "max_score": float(
                            maxima[detector][i]
                        ),
                        "winner_template_id": int(
                            winner_first[i]
                        ),
                        "artifact_family": str(
                            data.artifact_family[i]
                        ),
                    }
                )

        for i in range(
            cfg.holdout_n_per_stratum_per_batch
        ):
            score_records.append(
                {
                    "batch": batch,
                    "stratum": stratum,
                    "label": 1,
                    "curve": i,
                    "matched_filter_max": float(
                        maxima["matched_filter"][i]
                    ),
                    "sbw_slope_max": float(
                        maxima["sbw_slope"][i]
                    ),
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
        residual, _, _ = m3.normalize_sbw(
            data.y, data_cfg
        )
        mf_score, mf_winner = matched_filter_score(
            residual, bank
        )
        sbw_score = m2.rolling_slope_t_score(
            residual, data_cfg.detector_windows
        )
        score_map = {
            "matched_filter": mf_score,
            "sbw_slope": sbw_score,
        }
        maxima = {
            detector: m2.curve_max(
                score, data_cfg.eval_start
            )
            for detector, score in score_map.items()
        }

        for detector, score in score_map.items():
            first = m2.first_crossing(
                score,
                thresholds[detector],
                data_cfg.eval_start,
            )
            alerts = first >= 0
            if detector == "matched_filter":
                winner_first = _winner_at_first_crossing(
                    mf_winner, first
                )
            else:
                winner_first = np.full(
                    len(first), -1, dtype=np.int32
                )

            for i in range(len(alerts)):
                negative_records.append(
                    {
                        "batch": batch,
                        "family": family,
                        "curve": i,
                        "detector": detector,
                        "alert": bool(alerts[i]),
                        "first_crossing": int(first[i]),
                        "max_score": float(
                            maxima[detector][i]
                        ),
                        "winner_template_id": int(
                            winner_first[i]
                        ),
                    }
                )

        for i in range(
            cfg.holdout_n_per_stratum_per_batch
        ):
            score_records.append(
                {
                    "batch": batch,
                    "stratum": family,
                    "label": 0,
                    "curve": i,
                    "matched_filter_max": float(
                        maxima["matched_filter"][i]
                    ),
                    "sbw_slope_max": float(
                        maxima["sbw_slope"][i]
                    ),
                }
            )

    return positive_records, negative_records, score_records


def evaluate_holdout(
    thresholds: dict,
    cfg: Config,
    bank: dict,
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
            thresholds,
            cfg,
            bank,
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
    for detector in ("matched_filter", "sbw_slope"):
        for stratum in POSITIVE_STRATA:
            s = pos_df[
                (pos_df.detector == detector)
                & (pos_df.stratum == stratum)
            ]
            x = int(s.hit.sum())
            summary_rows.append(
                {
                    "detector": detector,
                    "kind": "positive",
                    "stratum": stratum,
                    "successes": x,
                    "n": len(s),
                    "rate": x / len(s),
                    "cp_lower_95": clopper_pearson_lower(
                        x, len(s)
                    ),
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
                    "cp_lower_95": np.nan,
                    "cp_upper_95": (
                        m2.clopper_pearson_upper(
                            x, len(s)
                        )
                    ),
                }
            )

    summary_df = pd.DataFrame(summary_rows)

    mf_hits = {}
    sbw_hits = {}
    for stratum in POSITIVE_STRATA:
        mf_hits[stratum] = (
            pos_df[
                (pos_df.detector == "matched_filter")
                & (pos_df.stratum == stratum)
            ]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )
        sbw_hits[stratum] = (
            pos_df[
                (pos_df.detector == "sbw_slope")
                & (pos_df.stratum == stratum)
            ]
            .sort_values(["batch", "curve"])
            .hit.to_numpy(dtype=bool)
        )

    boot = _paired_stratified_bootstrap(
        mf_hits,
        sbw_hits,
        cfg.bootstrap_replicates,
        cfg.bootstrap_seed,
    )

    mf_global = float(
        np.mean(
            [mf_hits[s].mean() for s in POSITIVE_STRATA]
        )
    )
    sbw_global = float(
        np.mean(
            [sbw_hits[s].mean() for s in POSITIVE_STRATA]
        )
    )

    ci = {
        "mf_recall_point": mf_global,
        "sbw_recall_point": sbw_global,
        "delta_point": mf_global - sbw_global,
        "mf_recall_lower_95": float(
            np.quantile(boot.mf_recall, 0.05)
        ),
        "mf_recall_upper_95": float(
            np.quantile(boot.mf_recall, 0.95)
        ),
        "delta_lower_95": float(
            np.quantile(boot.delta, 0.05)
        ),
        "delta_upper_95": float(
            np.quantile(boot.delta, 0.95)
        ),
    }

    batch_rows = []
    for batch in range(cfg.holdout_batches):
        for detector in (
            "matched_filter",
            "sbw_slope",
        ):
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
        index="batch",
        columns="detector",
        values="early_recall",
    )
    batch_pivot["delta_mf_minus_sbw"] = (
        batch_pivot["matched_filter"]
        - batch_pivot["sbw_slope"]
    )
    good_batches = int(
        np.sum(
            batch_pivot["matched_filter"]
            >= cfg.batch_recall_threshold
        )
    )

    secondary_rows = []
    y_true = score_df.label.to_numpy()
    for detector, column in (
        ("matched_filter", "matched_filter_max"),
        ("sbw_slope", "sbw_slope_max"),
    ):
        values = score_df[column].to_numpy()
        secondary_rows.append(
            {
                "detector": detector,
                "auroc": float(
                    roc_auc_score(y_true, values)
                ),
                "average_precision": float(
                    average_precision_score(
                        y_true, values
                    )
                ),
            }
        )
    secondary_df = pd.DataFrame(secondary_rows)

    mf_negative = summary_df[
        (summary_df.detector == "matched_filter")
        & (summary_df.kind == "negative")
    ]
    criterion_1 = bool(
        np.all(
            mf_negative.cp_upper_95
            <= cfg.holdout_fpr_upper_limit
        )
    )
    criterion_2 = (
        ci["mf_recall_lower_95"]
        >= cfg.minimum_global_recall_lower_ci
    )

    mf_positive = summary_df[
        (summary_df.detector == "matched_filter")
        & (summary_df.kind == "positive")
    ]
    good_strata = int(
        np.sum(
            mf_positive.cp_lower_95
            >= cfg.minimum_stratum_recall_lower_ci
        )
    )
    criterion_3 = good_strata >= cfg.minimum_good_strata
    criterion_4 = good_batches >= cfg.minimum_good_batches
    criterion_5 = (
        ci["delta_lower_95"]
        >= cfg.minimum_delta_vs_sbw_lower_ci
    )

    victory = all(
        [
            criterion_1,
            criterion_2,
            criterion_3,
            criterion_4,
            criterion_5,
        ]
    )
    strong_failure = (
        (not criterion_1)
        or (
            ci["mf_recall_upper_95"]
            <= cfg.strong_fail_global_recall_upper
        )
        or (ci["delta_upper_95"] <= 0.0)
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
        "criterion_2_global_recall_lower_ge_0_50": (
            criterion_2
        ),
        "criterion_3_six_strata_lower_ge_0_30": (
            criterion_3
        ),
        "criterion_4_fifteen_batches_recall_ge_0_45": (
            criterion_4
        ),
        "criterion_5_delta_vs_sbw_lower_ge_0_20": (
            criterion_5
        ),
        "good_strata": good_strata,
        "good_batches": good_batches,
        "thresholds": thresholds,
        "template_candidate_count": (
            bank["candidate_count"]
        ),
        "template_retained_count": bank["retained_count"],
        **ci,
    }

    return {
        "positive_df": pos_df,
        "negative_df": neg_df,
        "score_df": score_df,
        "summary_df": summary_df,
        "bootstrap_df": boot,
        "batch_df": batch_df,
        "batch_pivot_df": batch_pivot.reset_index(),
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
        "m3_dependency_sha256": sha256_file(
            M3_DIR / "arara_m3.py"
        ),
    }
    path.write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )
