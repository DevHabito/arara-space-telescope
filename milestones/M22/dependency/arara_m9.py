
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
M2_DIR = ROOT / "m2"
M5_DIR = ROOT / "m5"
for dependency in (M2_DIR, M5_DIR):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

import arara_m2 as m2
import arara_m5 as m5


POSITIVE_SHAPES = m2.POSITIVE_SHAPES
POSITIVE_CONTEXTS = m2.POSITIVE_CONTEXTS
POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES
SHARED_ARTIFACT_FAMILIES = m2.SHARED_ARTIFACT_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "9.0"
    snr_levels: tuple[float, ...] = (4.0, 6.0, 8.0, 10.0, 12.0)
    target_fraction: float = 1.0

    development_root_seed: int = 2026080401
    holdout_root_seed: int = 2026080402
    bootstrap_seed: int = 2026080403

    development_base_fields_per_shape_context: int = 1000
    development_negatives_per_family: int = 2000

    holdout_positive_per_stratum_total: int = 2500
    holdout_negative_per_family_total: int = 5000
    holdout_batches: int = 20
    holdout_positive_per_stratum_per_batch: int = 125
    holdout_negative_per_family_per_batch: int = 250

    development_fpr_target: float = 0.005
    holdout_fpr_upper_limit: float = 0.01

    minimum_global_recall_lower_ci: float = 0.60
    minimum_stratum_recall_lower_ci: float = 0.50
    minimum_good_strata: int = 6
    minimum_good_batches: int = 15
    batch_recall_threshold: float = 0.55
    maximum_adjacent_point_drop: float = 0.02
    strong_fail_snr12_recall_upper: float = 0.50
    bootstrap_replicates: int = 10_000
    predicted_first_passing_snr: float = 8.0

    def data_config(self) -> m2.Config:
        return m2.Config(
            development_root_seed=self.development_root_seed,
            holdout_root_seed=self.holdout_root_seed,
            bootstrap_seed=self.bootstrap_seed,
            development_n_per_stratum=self.development_base_fields_per_shape_context,
            holdout_total_n_per_stratum=self.holdout_positive_per_stratum_total,
            holdout_batches=self.holdout_batches,
            holdout_n_per_stratum_per_batch=self.holdout_positive_per_stratum_per_batch,
        )


@dataclass
class PositivePanel:
    base_y: np.ndarray
    shape_values: np.ndarray
    stationary_target_sd: np.ndarray
    onset: np.ndarray
    t100: np.ndarray
    artifact_family: np.ndarray


def time_at_fraction(signal: np.ndarray, fraction: float) -> np.ndarray:
    if signal.ndim != 2:
        raise ValueError("signal must be 2D.")
    if not (0.0 < fraction <= 1.0):
        raise ValueError("fraction must lie in (0, 1].")
    amplitude = np.max(signal, axis=1)
    if np.any(amplitude <= 0.0):
        raise ValueError("Every signal must have positive amplitude.")
    reached = signal >= (fraction * amplitude)[:, None]
    times = np.argmax(reached, axis=1)
    if not np.all(reached[np.arange(len(signal)), times]):
        raise RuntimeError("Every signal must reach the requested fraction.")
    return times.astype(np.int16)


def generate_positive_panel(
    shape: str,
    context: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> PositivePanel:
    if shape not in POSITIVE_SHAPES:
        raise ValueError(shape)
    if context not in POSITIVE_CONTEXTS:
        raise ValueError(context)

    data_cfg = cfg.data_config()
    y, stationary_sd, coupling, _, _ = m2._generate_base_field(
        n, rng, data_cfg
    )
    m2._inject_reference_impulse(y, stationary_sd, rng, data_cfg)

    onset = rng.integers(
        data_cfg.onset_low,
        data_cfg.onset_high + 1,
        size=n,
    )
    duration = rng.integers(
        data_cfg.duration_low,
        data_cfg.duration_high + 1,
        size=n,
    )
    k = np.arange(data_cfg.n_time)[None, :]
    shape_values = m2._event_shape(
        shape, k, onset, duration, rng
    )

    artifact_family = np.full(n, "none", dtype=object)
    if context == "concurrent":
        selected = rng.integers(
            0, len(SHARED_ARTIFACT_FAMILIES), size=n
        )
        delta = rng.integers(-10, 11, size=n)
        artifact_onset = np.clip(onset + delta, 60, 120)
        artifact_duration = rng.integers(
            data_cfg.duration_low,
            data_cfg.duration_high + 1,
            size=n,
        )

        for index, family in enumerate(SHARED_ARTIFACT_FAMILIES):
            mask = selected == index
            if not np.any(mask):
                continue
            block = y[mask].copy()
            m2._inject_shared_artifact(
                block,
                stationary_sd[mask],
                coupling[mask],
                family,
                artifact_onset[mask],
                artifact_duration[mask],
                rng,
                data_cfg,
            )
            y[mask] = block
            artifact_family[mask] = family

    t100 = time_at_fraction(shape_values, cfg.target_fraction)
    return PositivePanel(
        base_y=y,
        shape_values=shape_values,
        stationary_target_sd=stationary_sd[:, 0],
        onset=onset.astype(np.int16),
        t100=t100,
        artifact_family=artifact_family,
    )


def evaluate_positive_panel(
    panel: PositivePanel,
    snr: float,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    data_cfg = cfg.data_config()
    signal = (
        float(snr)
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    y = panel.base_y.copy()
    y[:, 0, :] += signal

    residual, processed_signal, _ = m5.sbw_with_signal_operator(
        y, signal, data_cfg
    )
    scores = m5.aligned_t_score(
        residual,
        processed_signal,
        panel.onset,
        panel.t100,
    )
    return scores, signal


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data_cfg = cfg.data_config()
    data = m2.generate_negative_family(
        family, n, rng, data_cfg
    )
    virtual_signal, onset, _, _ = m5.generate_virtual_hypotheses(
        n, rng, data_cfg
    )
    t100 = time_at_fraction(
        virtual_signal, cfg.target_fraction
    )
    residual, processed_signal, _ = m5.sbw_with_signal_operator(
        data.y, virtual_signal, data_cfg
    )
    scores = m5.aligned_t_score(
        residual, processed_signal, onset, t100
    )
    return scores, onset, t100


def evaluate_development(
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    child_count = (
        len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    )
    seed_seq = np.random.SeedSequence(
        cfg.development_root_seed
    )
    children = seed_seq.spawn(child_count)
    rngs = [np.random.default_rng(s) for s in children]

    positive_scores: dict[float, dict[str, np.ndarray]] = {
        snr: {} for snr in cfg.snr_levels
    }
    negative_scores: dict[str, np.ndarray] = {}

    for stratum, rng in zip(
        POSITIVE_STRATA,
        rngs[:len(POSITIVE_STRATA)],
    ):
        shape, context = stratum.split("__")
        panel = generate_positive_panel(
            shape,
            context,
            cfg.development_base_fields_per_shape_context,
            rng,
            cfg,
        )
        for snr in cfg.snr_levels:
            scores, _ = evaluate_positive_panel(
                panel, snr, cfg
            )
            positive_scores[snr][stratum] = (
                scores.astype(np.float32)
            )

    for family, rng in zip(
        NEGATIVE_FAMILIES,
        rngs[len(POSITIVE_STRATA):],
    ):
        scores, _, _ = evaluate_negative_family(
            family,
            cfg.development_negatives_per_family,
            rng,
            cfg,
        )
        negative_scores[family] = scores.astype(np.float32)

    threshold, family_thresholds, allowed = (
        m2.conservative_threshold(
            negative_scores,
            cfg.development_fpr_target,
        )
    )

    rows = []
    for family in NEGATIVE_FAMILIES:
        scores = negative_scores[family]
        alerts = int(np.sum(scores >= threshold))
        rows.append(
            {
                "kind": "negative",
                "snr": np.nan,
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

    for snr in cfg.snr_levels:
        for stratum in POSITIVE_STRATA:
            scores = positive_scores[snr][stratum]
            hits = scores >= threshold
            rows.append(
                {
                    "kind": "positive",
                    "snr": snr,
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
    child_count = (
        len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
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
        panel = generate_positive_panel(
            shape,
            context,
            cfg.holdout_positive_per_stratum_per_batch,
            rng,
            cfg,
        )

        for snr in cfg.snr_levels:
            scores, _ = evaluate_positive_panel(
                panel, snr, cfg
            )
            hits = scores >= threshold

            for i in range(len(scores)):
                positive_records.append(
                    {
                        "batch": batch,
                        "snr": float(snr),
                        "stratum": stratum,
                        "shape": shape,
                        "context": context,
                        "curve": i,
                        "score": float(scores[i]),
                        "hit": bool(hits[i]),
                        "onset": int(panel.onset[i]),
                        "t100": int(panel.t100[i]),
                        "segment_length": int(
                            panel.t100[i] - panel.onset[i] + 1
                        ),
                        "artifact_family": str(
                            panel.artifact_family[i]
                        ),
                    }
                )
                score_records.append(
                    {
                        "batch": batch,
                        "snr": float(snr),
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
        scores, onset, t100 = evaluate_negative_family(
            family,
            cfg.holdout_negative_per_family_per_batch,
            rng,
            cfg,
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
                    "pseudo_onset": int(onset[i]),
                    "pseudo_t100": int(t100[i]),
                }
            )
            score_records.append(
                {
                    "batch": batch,
                    "snr": np.nan,
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

    positive_all = []
    negative_all = []
    score_all = []
    seed_records = []

    for batch, seq in enumerate(batch_seqs):
        pos, neg, score = _evaluate_holdout_batch(
            batch, seq, threshold, cfg
        )
        positive_all.extend(pos)
        negative_all.extend(neg)
        score_all.extend(score)
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
    level_details = {}
    bootstrap_frames = []

    negative_summary_rows = []
    for family in NEGATIVE_FAMILIES:
        subset = neg_df[neg_df.family == family]
        x = int(subset.alert.sum())
        negative_summary_rows.append(
            {
                "kind": "negative",
                "snr": np.nan,
                "stratum": family,
                "successes": x,
                "n": len(subset),
                "rate": x / len(subset),
                "cp_lower_95": np.nan,
                "cp_upper_95": m2.clopper_pearson_upper(
                    x, len(subset)
                ),
            }
        )

    fpr_control = bool(
        all(
            row["cp_upper_95"]
            <= cfg.holdout_fpr_upper_limit
            for row in negative_summary_rows
        )
    )
    summary_rows.extend(negative_summary_rows)

    for level_index, snr in enumerate(cfg.snr_levels):
        hits_by_stratum = {}
        stratum_rows = []

        for stratum in POSITIVE_STRATA:
            subset = pos_df[
                (pos_df.snr == snr)
                & (pos_df.stratum == stratum)
            ]
            hits = subset.hit.to_numpy(dtype=bool)
            hits_by_stratum[stratum] = hits
            x = int(hits.sum())
            row = {
                "kind": "positive",
                "snr": float(snr),
                "stratum": stratum,
                "successes": x,
                "n": len(hits),
                "rate": x / len(hits),
                "cp_lower_95": m5.clopper_pearson_lower(
                    x, len(hits)
                ),
                "cp_upper_95": np.nan,
            }
            stratum_rows.append(row)
            summary_rows.append(row)

        boot = m5.stratified_bootstrap_recall(
            hits_by_stratum,
            cfg.bootstrap_replicates,
            cfg.bootstrap_seed + level_index,
        )
        bootstrap_frames.append(
            pd.DataFrame(
                {
                    "snr": float(snr),
                    "replicate": np.arange(
                        cfg.bootstrap_replicates
                    ),
                    "recall": boot,
                }
            )
        )

        point = float(
            np.mean(
                [
                    hits_by_stratum[s].mean()
                    for s in POSITIVE_STRATA
                ]
            )
        )
        lower = float(np.quantile(boot, 0.05))
        upper = float(np.quantile(boot, 0.95))
        good_strata = int(
            np.sum(
                [
                    row["cp_lower_95"]
                    >= cfg.minimum_stratum_recall_lower_ci
                    for row in stratum_rows
                ]
            )
        )

        batch_rows = []
        for batch in range(cfg.holdout_batches):
            subset = pos_df[
                (pos_df.batch == batch)
                & (pos_df.snr == snr)
            ]
            batch_rows.append(
                {
                    "batch": batch,
                    "snr": float(snr),
                    "recall": float(subset.hit.mean()),
                    "hits": int(subset.hit.sum()),
                    "n": len(subset),
                }
            )
        batch_df_level = pd.DataFrame(batch_rows)
        good_batches = int(
            np.sum(
                batch_df_level.recall
                >= cfg.batch_recall_threshold
            )
        )

        level_pass = bool(
            fpr_control
            and lower >= cfg.minimum_global_recall_lower_ci
            and good_strata >= cfg.minimum_good_strata
            and good_batches >= cfg.minimum_good_batches
        )
        level_details[str(snr)] = {
            "snr": float(snr),
            "recall_point": point,
            "recall_lower_95": lower,
            "recall_upper_95": upper,
            "good_strata": good_strata,
            "good_batches": good_batches,
            "pass": level_pass,
        }

    summary_df = pd.DataFrame(summary_rows)
    bootstrap_df = pd.concat(
        bootstrap_frames, ignore_index=True
    )

    batch_rows_all = []
    for snr in cfg.snr_levels:
        for batch in range(cfg.holdout_batches):
            subset = pos_df[
                (pos_df.batch == batch)
                & (pos_df.snr == snr)
            ]
            batch_rows_all.append(
                {
                    "batch": batch,
                    "snr": float(snr),
                    "recall": float(subset.hit.mean()),
                    "hits": int(subset.hit.sum()),
                    "n": len(subset),
                }
            )
    batch_df = pd.DataFrame(batch_rows_all)

    secondary_rows = []
    negative_scores = neg_df.score.to_numpy()
    for snr in cfg.snr_levels:
        positive_scores = pos_df[
            pos_df.snr == snr
        ].score.to_numpy()
        values = np.concatenate(
            [positive_scores, negative_scores]
        )
        labels = np.concatenate(
            [
                np.ones(len(positive_scores), dtype=int),
                np.zeros(len(negative_scores), dtype=int),
            ]
        )
        secondary_rows.append(
            {
                "snr": float(snr),
                "auroc": float(
                    roc_auc_score(labels, values)
                ),
                "average_precision": float(
                    average_precision_score(
                        labels, values
                    )
                ),
            }
        )
    secondary_df = pd.DataFrame(secondary_rows)

    recalls = np.array(
        [
            level_details[str(snr)]["recall_point"]
            for snr in cfg.snr_levels
        ]
    )
    adjacent_differences = np.diff(recalls)
    monotonicity_pass = bool(
        np.all(
            adjacent_differences
            >= -cfg.maximum_adjacent_point_drop
        )
    )

    passing_levels = [
        snr
        for snr in cfg.snr_levels
        if level_details[str(snr)]["pass"]
    ]
    minimum_passing_snr = (
        float(min(passing_levels))
        if passing_levels
        else None
    )

    victory = bool(
        fpr_control
        and bool(passing_levels)
        and monotonicity_pass
    )
    highest = level_details[str(cfg.snr_levels[-1])]
    strong_failure = bool(
        (not fpr_control)
        or (
            not passing_levels
            and highest["recall_upper_95"]
            <= cfg.strong_fail_snr12_recall_upper
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

    prediction_confirmed = (
        minimum_passing_snr
        == cfg.predicted_first_passing_snr
    )

    verdict_details = {
        "verdict": verdict,
        "fpr_control": fpr_control,
        "monotonicity_pass": monotonicity_pass,
        "adjacent_recall_differences": (
            adjacent_differences.tolist()
        ),
        "passing_levels": [
            float(x) for x in passing_levels
        ],
        "minimum_passing_snr": minimum_passing_snr,
        "predicted_first_passing_snr": (
            cfg.predicted_first_passing_snr
        ),
        "prediction_confirmed": bool(
            prediction_confirmed
        ),
        "threshold": float(threshold),
        "level_details": level_details,
    }

    return {
        "positive_df": pos_df,
        "negative_df": neg_df,
        "score_df": score_df,
        "summary_df": summary_df,
        "bootstrap_df": bootstrap_df,
        "batch_df": batch_df,
        "secondary_df": secondary_df,
        "seed_records": seed_records,
        "verdict": verdict_details,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            h.update(block)
    return h.hexdigest()


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
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
