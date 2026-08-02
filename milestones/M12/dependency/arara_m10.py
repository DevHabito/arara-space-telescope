
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
M9_DIR = ROOT / "m9"
for dependency in (M2_DIR, M5_DIR, M9_DIR):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

import arara_m2 as m2
import arara_m5 as m5
import arara_m9 as m9


POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "10.0"
    fixed_snr: float = 8.0
    fractions: tuple[float, ...] = (0.25, 0.50, 0.75, 1.0)

    development_root_seed: int = 2026080501
    holdout_root_seed: int = 2026080502
    bootstrap_seed: int = 2026080503

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
    predicted_first_passing_fraction: float = 0.75
    bootstrap_replicates: int = 10_000

    def panel_config(self) -> m9.Config:
        return m9.Config(
            snr_levels=(self.fixed_snr,),
            development_root_seed=self.development_root_seed,
            holdout_root_seed=self.holdout_root_seed,
            bootstrap_seed=self.bootstrap_seed,
            development_base_fields_per_shape_context=(
                self.development_base_fields_per_shape_context
            ),
            development_negatives_per_family=(
                self.development_negatives_per_family
            ),
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
        )


def evaluate_positive_panel(
    panel: m9.PositivePanel,
    cfg: Config,
) -> tuple[dict[float, np.ndarray], dict[float, np.ndarray]]:
    panel_cfg = cfg.panel_config()
    signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    y = panel.base_y.copy()
    y[:, 0, :] += signal

    residual, processed_signal, _ = m5.sbw_with_signal_operator(
        y, signal, panel_cfg.data_config()
    )

    scores = {}
    times = {}
    for fraction in cfg.fractions:
        tf = m9.time_at_fraction(signal, fraction)
        score = m5.aligned_t_score(
            residual,
            processed_signal,
            panel.onset,
            tf,
        )
        scores[fraction] = score
        times[fraction] = tf
    return scores, times


def evaluate_negative_family(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
) -> tuple[dict[float, np.ndarray], dict[float, np.ndarray], np.ndarray]:
    panel_cfg = cfg.panel_config()
    data_cfg = panel_cfg.data_config()
    data = m2.generate_negative_family(
        family, n, rng, data_cfg
    )
    virtual_signal, onset, _, _ = m5.generate_virtual_hypotheses(
        n, rng, data_cfg
    )
    residual, processed_signal, _ = m5.sbw_with_signal_operator(
        data.y, virtual_signal, data_cfg
    )

    scores = {}
    times = {}
    for fraction in cfg.fractions:
        tf = m9.time_at_fraction(
            virtual_signal, fraction
        )
        scores[fraction] = m5.aligned_t_score(
            residual,
            processed_signal,
            onset,
            tf,
        )
        times[fraction] = tf
    return scores, times, onset


def evaluate_development(
    cfg: Config,
) -> tuple[dict, pd.DataFrame]:
    child_count = (
        len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    )
    seed_sequence = np.random.SeedSequence(
        cfg.development_root_seed
    )
    children = seed_sequence.spawn(child_count)
    rngs = [np.random.default_rng(seed) for seed in children]

    positive_scores = {
        fraction: {} for fraction in cfg.fractions
    }
    negative_scores = {
        fraction: {} for fraction in cfg.fractions
    }

    panel_cfg = cfg.panel_config()

    for stratum, rng in zip(
        POSITIVE_STRATA,
        rngs[:len(POSITIVE_STRATA)],
    ):
        shape, context = stratum.split("__")
        panel = m9.generate_positive_panel(
            shape,
            context,
            cfg.development_base_fields_per_shape_context,
            rng,
            panel_cfg,
        )
        score_map, _ = evaluate_positive_panel(
            panel, cfg
        )
        for fraction in cfg.fractions:
            positive_scores[fraction][stratum] = (
                score_map[fraction].astype(np.float32)
            )

    for family, rng in zip(
        NEGATIVE_FAMILIES,
        rngs[len(POSITIVE_STRATA):],
    ):
        score_map, _, _ = evaluate_negative_family(
            family,
            cfg.development_negatives_per_family,
            rng,
            cfg,
        )
        for fraction in cfg.fractions:
            negative_scores[fraction][family] = (
                score_map[fraction].astype(np.float32)
            )

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []

    for fraction in cfg.fractions:
        threshold, family_specific, allowed = (
            m2.conservative_threshold(
                negative_scores[fraction],
                cfg.development_fpr_target,
            )
        )
        thresholds[str(fraction)] = float(threshold)
        family_thresholds[str(fraction)] = (
            family_specific
        )
        allowed_counts[str(fraction)] = allowed

        for family in NEGATIVE_FAMILIES:
            scores = negative_scores[fraction][family]
            alerts = int(
                np.sum(scores >= threshold)
            )
            rows.append(
                {
                    "kind": "negative",
                    "fraction": fraction,
                    "stratum": family,
                    "successes": alerts,
                    "n": len(scores),
                    "rate": alerts / len(scores),
                    "threshold": threshold,
                    "family_specific_threshold": (
                        family_specific[family]
                    ),
                    "allowed": allowed[family],
                }
            )

        for stratum in POSITIVE_STRATA:
            scores = positive_scores[fraction][stratum]
            hits = scores >= threshold
            rows.append(
                {
                    "kind": "positive",
                    "fraction": fraction,
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
        "family_thresholds": family_thresholds,
        "allowed_counts": allowed_counts,
        "development_seed_children": [
            {
                "entropy": seed.entropy,
                "spawn_key": list(seed.spawn_key),
            }
            for seed in children
        ],
    }
    return details, pd.DataFrame(rows)


def _evaluate_holdout_batch(
    batch: int,
    seed: np.random.SeedSequence,
    thresholds: dict,
    cfg: Config,
) -> tuple[list, list, list]:
    child_count = (
        len(POSITIVE_STRATA) + len(NEGATIVE_FAMILIES)
    )
    children = seed.spawn(child_count)
    rngs = [np.random.default_rng(child) for child in children]

    positive_records = []
    negative_records = []
    score_records = []
    panel_cfg = cfg.panel_config()

    for stratum, rng in zip(
        POSITIVE_STRATA,
        rngs[:len(POSITIVE_STRATA)],
    ):
        shape, context = stratum.split("__")
        panel = m9.generate_positive_panel(
            shape,
            context,
            cfg.holdout_positive_per_stratum_per_batch,
            rng,
            panel_cfg,
        )
        score_map, time_map = evaluate_positive_panel(
            panel, cfg
        )

        for fraction in cfg.fractions:
            scores = score_map[fraction]
            threshold = thresholds[str(fraction)]
            hits = scores >= threshold
            times = time_map[fraction]

            for i in range(len(scores)):
                positive_records.append(
                    {
                        "batch": batch,
                        "fraction": float(fraction),
                        "stratum": stratum,
                        "shape": shape,
                        "context": context,
                        "curve": i,
                        "score": float(scores[i]),
                        "hit": bool(hits[i]),
                        "onset": int(panel.onset[i]),
                        "tf": int(times[i]),
                        "segment_length": int(
                            times[i] - panel.onset[i] + 1
                        ),
                    }
                )
                score_records.append(
                    {
                        "batch": batch,
                        "fraction": float(fraction),
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
        score_map, time_map, onset = (
            evaluate_negative_family(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
            )
        )

        for fraction in cfg.fractions:
            scores = score_map[fraction]
            threshold = thresholds[str(fraction)]
            alerts = scores >= threshold
            times = time_map[fraction]

            for i in range(len(scores)):
                negative_records.append(
                    {
                        "batch": batch,
                        "fraction": float(fraction),
                        "family": family,
                        "curve": i,
                        "score": float(scores[i]),
                        "alert": bool(alerts[i]),
                        "pseudo_onset": int(onset[i]),
                        "pseudo_tf": int(times[i]),
                    }
                )
                score_records.append(
                    {
                        "batch": batch,
                        "fraction": float(fraction),
                        "stratum": family,
                        "label": 0,
                        "curve": i,
                        "score": float(scores[i]),
                    }
                )

    return positive_records, negative_records, score_records


def evaluate_holdout(
    thresholds: dict,
    cfg: Config,
) -> dict:
    root_sequence = np.random.SeedSequence(
        cfg.holdout_root_seed
    )
    batch_sequences = root_sequence.spawn(
        cfg.holdout_batches
    )

    positive_all = []
    negative_all = []
    score_all = []
    seed_records = []

    for batch, seed in enumerate(batch_sequences):
        positive, negative, scores = (
            _evaluate_holdout_batch(
                batch,
                seed,
                thresholds,
                cfg,
            )
        )
        positive_all.extend(positive)
        negative_all.extend(negative)
        score_all.extend(scores)
        seed_records.append(
            {
                "batch": batch,
                "entropy": seed.entropy,
                "spawn_key": list(seed.spawn_key),
            }
        )

    pos_df = pd.DataFrame(positive_all)
    neg_df = pd.DataFrame(negative_all)
    score_df = pd.DataFrame(score_all)

    summary_rows = []
    bootstrap_frames = []
    fraction_details = {}

    for index, fraction in enumerate(cfg.fractions):
        negative_rows = []
        for family in NEGATIVE_FAMILIES:
            subset = neg_df[
                (neg_df.fraction == fraction)
                & (neg_df.family == family)
            ]
            alerts = int(subset.alert.sum())
            row = {
                "kind": "negative",
                "fraction": float(fraction),
                "stratum": family,
                "successes": alerts,
                "n": len(subset),
                "rate": alerts / len(subset),
                "cp_lower_95": np.nan,
                "cp_upper_95": (
                    m2.clopper_pearson_upper(
                        alerts, len(subset)
                    )
                ),
            }
            negative_rows.append(row)
            summary_rows.append(row)

        fpr_control = bool(
            all(
                row["cp_upper_95"]
                <= cfg.holdout_fpr_upper_limit
                for row in negative_rows
            )
        )

        hits_by_stratum = {}
        positive_rows = []
        for stratum in POSITIVE_STRATA:
            subset = pos_df[
                (pos_df.fraction == fraction)
                & (pos_df.stratum == stratum)
            ]
            hits = subset.hit.to_numpy(dtype=bool)
            hits_by_stratum[stratum] = hits
            successes = int(hits.sum())
            row = {
                "kind": "positive",
                "fraction": float(fraction),
                "stratum": stratum,
                "successes": successes,
                "n": len(hits),
                "rate": successes / len(hits),
                "cp_lower_95": (
                    m5.clopper_pearson_lower(
                        successes, len(hits)
                    )
                ),
                "cp_upper_95": np.nan,
            }
            positive_rows.append(row)
            summary_rows.append(row)

        bootstrap = m5.stratified_bootstrap_recall(
            hits_by_stratum,
            cfg.bootstrap_replicates,
            cfg.bootstrap_seed + index,
        )
        bootstrap_frames.append(
            pd.DataFrame(
                {
                    "fraction": float(fraction),
                    "replicate": np.arange(
                        cfg.bootstrap_replicates
                    ),
                    "recall": bootstrap,
                }
            )
        )

        point = float(
            np.mean(
                [
                    hits_by_stratum[stratum].mean()
                    for stratum in POSITIVE_STRATA
                ]
            )
        )
        lower = float(np.quantile(bootstrap, 0.05))
        upper = float(np.quantile(bootstrap, 0.95))
        good_strata = int(
            np.sum(
                [
                    row["cp_lower_95"]
                    >= cfg.minimum_stratum_recall_lower_ci
                    for row in positive_rows
                ]
            )
        )

        batch_rows = []
        for batch in range(cfg.holdout_batches):
            subset = pos_df[
                (pos_df.batch == batch)
                & (pos_df.fraction == fraction)
            ]
            batch_rows.append(
                {
                    "batch": batch,
                    "fraction": float(fraction),
                    "recall": float(subset.hit.mean()),
                    "hits": int(subset.hit.sum()),
                    "n": len(subset),
                }
            )
        batch_df_fraction = pd.DataFrame(batch_rows)
        good_batches = int(
            np.sum(
                batch_df_fraction.recall
                >= cfg.batch_recall_threshold
            )
        )

        fraction_pass = bool(
            fpr_control
            and lower >= cfg.minimum_global_recall_lower_ci
            and good_strata >= cfg.minimum_good_strata
            and good_batches >= cfg.minimum_good_batches
        )

        fraction_details[str(fraction)] = {
            "fraction": float(fraction),
            "fpr_control": fpr_control,
            "recall_point": point,
            "recall_lower_95": lower,
            "recall_upper_95": upper,
            "good_strata": good_strata,
            "good_batches": good_batches,
            "pass": fraction_pass,
        }

    summary_df = pd.DataFrame(summary_rows)
    bootstrap_df = pd.concat(
        bootstrap_frames, ignore_index=True
    )

    batch_rows_all = []
    for fraction in cfg.fractions:
        for batch in range(cfg.holdout_batches):
            subset = pos_df[
                (pos_df.batch == batch)
                & (pos_df.fraction == fraction)
            ]
            batch_rows_all.append(
                {
                    "batch": batch,
                    "fraction": float(fraction),
                    "recall": float(subset.hit.mean()),
                    "hits": int(subset.hit.sum()),
                    "n": len(subset),
                }
            )
    batch_df = pd.DataFrame(batch_rows_all)

    secondary_rows = []
    for fraction in cfg.fractions:
        positive_scores = pos_df[
            pos_df.fraction == fraction
        ].score.to_numpy()
        negative_scores = neg_df[
            neg_df.fraction == fraction
        ].score.to_numpy()
        labels = np.concatenate(
            [
                np.ones(len(positive_scores), dtype=int),
                np.zeros(len(negative_scores), dtype=int),
            ]
        )
        values = np.concatenate(
            [positive_scores, negative_scores]
        )
        secondary_rows.append(
            {
                "fraction": float(fraction),
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
            fraction_details[str(fraction)][
                "recall_point"
            ]
            for fraction in cfg.fractions
        ]
    )
    differences = np.diff(recalls)
    monotonicity_pass = bool(
        np.all(
            differences
            >= -cfg.maximum_adjacent_point_drop
        )
    )

    passing_fractions = [
        fraction
        for fraction in cfg.fractions
        if fraction_details[str(fraction)]["pass"]
    ]
    earliest = (
        float(min(passing_fractions))
        if passing_fractions
        else None
    )

    mapping_pass = bool(
        passing_fractions and monotonicity_pass
    )
    early_window_success = bool(
        mapping_pass and earliest <= 0.75
    )

    if mapping_pass and early_window_success:
        verdict = "PASS"
    elif mapping_pass:
        verdict = "PASS_MAPPING_ONLY"
    else:
        verdict = "STRONG_FAIL"

    verdict_details = {
        "verdict": verdict,
        "mapping_pass": mapping_pass,
        "early_window_success": early_window_success,
        "monotonicity_pass": monotonicity_pass,
        "adjacent_recall_differences": (
            differences.tolist()
        ),
        "passing_fractions": [
            float(value) for value in passing_fractions
        ],
        "earliest_passing_fraction": earliest,
        "predicted_first_passing_fraction": (
            cfg.predicted_first_passing_fraction
        ),
        "prediction_confirmed": bool(
            earliest
            == cfg.predicted_first_passing_fraction
        ),
        "thresholds": thresholds,
        "fraction_details": fraction_details,
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
        "m2_dependency_sha256": sha256_file(
            M2_DIR / "arara_m2.py"
        ),
        "m5_dependency_sha256": sha256_file(
            M5_DIR / "arara_m5.py"
        ),
        "m9_dependency_sha256": sha256_file(
            M9_DIR / "arara_m9.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
