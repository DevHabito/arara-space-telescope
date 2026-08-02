
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


ROOT = Path(__file__).resolve().parents[1]
M2_DIR = ROOT / "m2"
M5_DIR = ROOT / "m5"
M9_DIR = ROOT / "m9"
M15_DIR = ROOT / "m15"
for dependency in (M2_DIR, M5_DIR, M9_DIR, M15_DIR):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

import arara_m2 as m2
import arara_m5 as m5
import arara_m9 as m9
import arara_m15 as m15


POSITIVE_STRATA = m2.POSITIVE_STRATA
NEGATIVE_FAMILIES = m2.NEGATIVE_FAMILIES


@dataclass(frozen=True)
class Config:
    version: str = "22.0"
    fixed_snr: float = 13.75
    target_fraction: float = 0.50
    onset_offsets: tuple[int, ...] = (-4, -2, 0, 2, 4)

    replication_count: int = 10
    replication_root_seed: int = 2026081701
    aggregate_bootstrap_root_seed: int = 2026081702

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

    prediction_ranges: tuple[tuple[int, float, float], ...] = (
        (-4, 0.50, 0.64),
        (-2, 0.60, 0.68),
        (0, 0.64, 0.70),
        (2, 0.60, 0.68),
        (4, 0.50, 0.64),
    )

    def core_config(self, seed_record: dict) -> m9.Config:
        seeds = seed_record["seeds"]
        return m9.Config(
            version=f"{self.version}-r{seed_record['replication']:02d}",
            snr_levels=(self.fixed_snr,),
            target_fraction=self.target_fraction,
            development_root_seed=seeds["development"],
            holdout_root_seed=seeds["holdout"],
            bootstrap_seed=seeds["bootstrap"],
            development_base_fields_per_shape_context=1000,
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
            development_fpr_target=self.development_fpr_target,
            holdout_fpr_upper_limit=self.holdout_fpr_upper_limit,
            minimum_global_recall_lower_ci=(
                self.minimum_global_recall_lower_ci
            ),
            minimum_stratum_recall_lower_ci=(
                self.minimum_stratum_recall_lower_ci
            ),
            minimum_good_strata=self.minimum_good_strata,
            minimum_good_batches=self.minimum_good_batches,
            batch_recall_threshold=self.batch_recall_threshold,
            maximum_adjacent_point_drop=0.02,
            strong_fail_snr12_recall_upper=0.50,
            bootstrap_replicates=self.bootstrap_replicates,
            predicted_first_passing_snr=self.fixed_snr,
        )


def build_seed_plan(cfg: Config) -> list[dict]:
    return m15.build_seed_plan(cfg)


def shift_signal(signal: np.ndarray, offset: int) -> np.ndarray:
    values = np.asarray(signal)
    if values.ndim != 2:
        raise ValueError("signal must be 2D.")
    out = np.zeros_like(values)
    if offset == 0:
        out[:] = values
    elif offset > 0:
        if offset < values.shape[1]:
            out[:, offset:] = values[:, :-offset]
    else:
        amount = -offset
        if amount < values.shape[1]:
            out[:, :-amount] = values[:, amount:]
    return out


def apply_signal_operator(
    raw_signal: np.ndarray,
    params: dict,
) -> np.ndarray:
    raw = np.asarray(raw_signal, dtype=np.float64)
    target_scale = np.asarray(
        params["target_scale"], dtype=np.float64
    )
    residual_scale = np.asarray(
        params["residual_scale"], dtype=np.float64
    )
    phi = np.asarray(
        params["residual_phi"], dtype=np.float64
    )

    if raw.ndim != 2:
        raise ValueError("raw_signal must be 2D.")
    if raw.shape[0] != len(target_scale):
        raise ValueError("row count differs from params.")

    signal_x = raw / target_scale[:, None]
    processed = np.empty_like(signal_x)
    processed[:, 0] = signal_x[:, 0] / residual_scale
    processed[:, 1:] = (
        signal_x[:, 1:]
        - phi[:, None] * signal_x[:, :-1]
    ) / residual_scale[:, None]
    return processed


def score_positive_offsets(
    panel: m9.PositivePanel,
    cfg: Config,
) -> Dict[int, np.ndarray]:
    data_cfg = cfg.core_config(
        {
            "replication": 0,
            "seeds": {
                "development": 1,
                "holdout": 2,
                "bootstrap": 3,
            },
        }
    ).data_config()

    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    y = panel.base_y.copy()
    y[:, 0, :] += raw_signal

    residual, _, params = m5.sbw_with_signal_operator(
        y, raw_signal, data_cfg
    )

    scores = {}
    for offset in cfg.onset_offsets:
        shifted = shift_signal(raw_signal, offset)
        template = apply_signal_operator(shifted, params)
        estimated_onset = (
            panel.onset.astype(np.int32) + offset
        ).astype(np.int16)
        scores[offset] = m5.aligned_t_score(
            residual,
            template,
            estimated_onset,
            panel.t100,
        )
    return scores


def score_negative_offsets(
    family: str,
    n: int,
    rng: np.random.Generator,
    cfg: Config,
    core: m9.Config,
) -> Dict[int, np.ndarray]:
    data_cfg = core.data_config()
    data = m2.generate_negative_family(
        family, n, rng, data_cfg
    )
    virtual_signal, onset, _, _ = (
        m5.generate_virtual_hypotheses(
            n, rng, data_cfg
        )
    )
    endpoint = m9.time_at_fraction(
        virtual_signal, cfg.target_fraction
    )
    residual, _, params = m5.sbw_with_signal_operator(
        data.y, virtual_signal, data_cfg
    )

    scores = {}
    for offset in cfg.onset_offsets:
        shifted = shift_signal(virtual_signal, offset)
        template = apply_signal_operator(shifted, params)
        estimated_onset = (
            onset.astype(np.int32) + offset
        ).astype(np.int16)
        scores[offset] = m5.aligned_t_score(
            residual,
            template,
            estimated_onset,
            endpoint,
        )
    return scores


def calibrate_thresholds(
    cfg: Config,
    seed_record: dict,
) -> tuple[dict, pd.DataFrame]:
    core = cfg.core_config(seed_record)
    seed_sequence = np.random.SeedSequence(
        seed_record["seeds"]["development"]
    )
    children = seed_sequence.spawn(
        len(NEGATIVE_FAMILIES)
    )

    negative_scores = {
        offset: {} for offset in cfg.onset_offsets
    }

    for family, child in zip(
        NEGATIVE_FAMILIES, children
    ):
        rng = np.random.default_rng(child)
        score_map = score_negative_offsets(
            family,
            cfg.development_negatives_per_family,
            rng,
            cfg,
            core,
        )
        for offset in cfg.onset_offsets:
            negative_scores[offset][family] = (
                score_map[offset].astype(np.float32)
            )

    thresholds = {}
    family_thresholds = {}
    allowed_counts = {}
    rows = []

    for offset in cfg.onset_offsets:
        threshold, family_specific, allowed = (
            m2.conservative_threshold(
                negative_scores[offset],
                cfg.development_fpr_target,
            )
        )
        thresholds[str(offset)] = float(threshold)
        family_thresholds[str(offset)] = (
            family_specific
        )
        allowed_counts[str(offset)] = allowed

        for family in NEGATIVE_FAMILIES:
            values = negative_scores[offset][family]
            alerts = int(np.sum(values >= threshold))
            rows.append(
                {
                    "offset": offset,
                    "family": family,
                    "threshold": threshold,
                    "family_specific_threshold": (
                        family_specific[family]
                    ),
                    "alerts": alerts,
                    "n": len(values),
                    "allowed": allowed[family],
                    "rate": alerts / len(values),
                }
            )

    details = {
        "thresholds": thresholds,
        "family_thresholds": family_thresholds,
        "allowed_counts": allowed_counts,
        "development_seed_children": [
            {
                "entropy": child.entropy,
                "spawn_key": list(child.spawn_key),
            }
            for child in children
        ],
    }
    return details, pd.DataFrame(rows)


def evaluate_holdout(
    cfg: Config,
    seed_record: dict,
    thresholds: dict,
) -> dict:
    core = cfg.core_config(seed_record)
    batch_sequences = np.random.SeedSequence(
        seed_record["seeds"]["holdout"]
    ).spawn(cfg.holdout_batches)

    positive_counts = {
        offset: {
            stratum: np.zeros(
                cfg.holdout_batches, dtype=np.int64
            )
            for stratum in POSITIVE_STRATA
        }
        for offset in cfg.onset_offsets
    }
    positive_ns = {
        offset: {
            stratum: np.zeros(
                cfg.holdout_batches, dtype=np.int64
            )
            for stratum in POSITIVE_STRATA
        }
        for offset in cfg.onset_offsets
    }
    negative_counts = {
        offset: {
            family: 0 for family in NEGATIVE_FAMILIES
        }
        for offset in cfg.onset_offsets
    }
    negative_ns = {
        offset: {
            family: 0 for family in NEGATIVE_FAMILIES
        }
        for offset in cfg.onset_offsets
    }
    positive_score_parts = {
        offset: [] for offset in cfg.onset_offsets
    }
    negative_score_parts = {
        offset: [] for offset in cfg.onset_offsets
    }

    for batch, sequence in enumerate(batch_sequences):
        children = sequence.spawn(
            len(POSITIVE_STRATA)
            + len(NEGATIVE_FAMILIES)
        )
        rngs = [
            np.random.default_rng(child)
            for child in children
        ]

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
                core,
            )
            score_map = score_positive_offsets(
                panel, cfg
            )
            for offset in cfg.onset_offsets:
                values = score_map[offset]
                threshold = thresholds[str(offset)]
                hits = values >= threshold
                positive_counts[offset][stratum][
                    batch
                ] += int(hits.sum())
                positive_ns[offset][stratum][
                    batch
                ] += len(hits)
                positive_score_parts[offset].append(
                    values.astype(np.float32)
                )

        for family, rng in zip(
            NEGATIVE_FAMILIES,
            rngs[len(POSITIVE_STRATA):],
        ):
            score_map = score_negative_offsets(
                family,
                cfg.holdout_negative_per_family_per_batch,
                rng,
                cfg,
                core,
            )
            for offset in cfg.onset_offsets:
                values = score_map[offset]
                threshold = thresholds[str(offset)]
                alerts = values >= threshold
                negative_counts[offset][family] += (
                    int(alerts.sum())
                )
                negative_ns[offset][family] += len(
                    alerts
                )
                negative_score_parts[offset].append(
                    values.astype(np.float32)
                )

    offset_rows = []
    stratum_rows = []
    negative_rows = []
    batch_rows = []
    secondary_rows = []

    for offset_index, offset in enumerate(
        cfg.onset_offsets
    ):
        fpr_pass = True
        maximum_fpr_upper = 0.0

        for family in NEGATIVE_FAMILIES:
            x = negative_counts[offset][family]
            n = negative_ns[offset][family]
            upper = m2.clopper_pearson_upper(x, n)
            maximum_fpr_upper = max(
                maximum_fpr_upper, upper
            )
            if upper > cfg.holdout_fpr_upper_limit:
                fpr_pass = False
            negative_rows.append(
                {
                    "offset": offset,
                    "family": family,
                    "alerts": x,
                    "n": n,
                    "rate": x / n,
                    "cp_upper_95": upper,
                }
            )

        hits_by_stratum = {}
        good_strata = 0
        total_successes = []
        total_ns = []

        for stratum in POSITIVE_STRATA:
            batch_counts = positive_counts[offset][
                stratum
            ]
            batch_ns = positive_ns[offset][stratum]
            x = int(batch_counts.sum())
            n = int(batch_ns.sum())
            lower = m5.clopper_pearson_lower(x, n)
            if (
                lower
                >= cfg.minimum_stratum_recall_lower_ci
            ):
                good_strata += 1
            hits = np.zeros(n, dtype=bool)
            hits[:x] = True
            hits_by_stratum[stratum] = hits
            total_successes.append(x)
            total_ns.append(n)
            stratum_rows.append(
                {
                    "offset": offset,
                    "stratum": stratum,
                    "hits": x,
                    "n": n,
                    "rate": x / n,
                    "cp_lower_95": lower,
                }
            )

        boot = m5.stratified_bootstrap_recall(
            hits_by_stratum,
            cfg.bootstrap_replicates,
            seed_record["seeds"]["bootstrap"]
            + offset_index,
        )
        recall_point = float(
            np.mean(
                np.asarray(total_successes)
                / np.asarray(total_ns)
            )
        )
        recall_lower = float(
            np.quantile(boot, 0.05)
        )
        recall_upper = float(
            np.quantile(boot, 0.95)
        )

        batch_recall_values = []
        for batch in range(cfg.holdout_batches):
            hits = sum(
                positive_counts[offset][stratum][
                    batch
                ]
                for stratum in POSITIVE_STRATA
            )
            n = sum(
                positive_ns[offset][stratum][batch]
                for stratum in POSITIVE_STRATA
            )
            recall = hits / n
            batch_recall_values.append(recall)
            batch_rows.append(
                {
                    "offset": offset,
                    "batch": batch,
                    "hits": hits,
                    "n": n,
                    "recall": recall,
                }
            )
        good_batches = int(
            np.sum(
                np.asarray(batch_recall_values)
                >= cfg.batch_recall_threshold
            )
        )

        passed = bool(
            fpr_pass
            and recall_lower
            >= cfg.minimum_global_recall_lower_ci
            and good_strata >= cfg.minimum_good_strata
            and good_batches >= cfg.minimum_good_batches
        )

        positive_scores = np.concatenate(
            positive_score_parts[offset]
        )
        negative_scores = np.concatenate(
            negative_score_parts[offset]
        )
        labels = np.concatenate(
            [
                np.ones(
                    len(positive_scores), dtype=int
                ),
                np.zeros(
                    len(negative_scores), dtype=int
                ),
            ]
        )
        values = np.concatenate(
            [positive_scores, negative_scores]
        )
        secondary_rows.append(
            {
                "offset": offset,
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

        offset_rows.append(
            {
                "replication": seed_record[
                    "replication"
                ],
                "offset": offset,
                "threshold": thresholds[str(offset)],
                "recall_point": recall_point,
                "recall_lower_95": recall_lower,
                "recall_upper_95": recall_upper,
                "good_strata": good_strata,
                "good_batches": good_batches,
                "fpr_pass": fpr_pass,
                "maximum_fpr_upper_95": (
                    maximum_fpr_upper
                ),
                "pass": passed,
            }
        )

    return {
        "offset_summary": pd.DataFrame(offset_rows),
        "stratum_summary": pd.DataFrame(stratum_rows),
        "negative_summary": pd.DataFrame(negative_rows),
        "batch_summary": pd.DataFrame(batch_rows),
        "secondary_metrics": pd.DataFrame(
            secondary_rows
        ),
    }


def run_replication(
    cfg: Config,
    seed_record: dict,
) -> dict:
    development_details, development_df = (
        calibrate_thresholds(cfg, seed_record)
    )
    holdout = evaluate_holdout(
        cfg,
        seed_record,
        development_details["thresholds"],
    )
    return {
        "replication": seed_record["replication"],
        "development_details": development_details,
        "development_df": development_df,
        **holdout,
    }


def aggregate_results(
    cfg: Config,
    replication_summary: pd.DataFrame,
    stratum_summary: pd.DataFrame,
) -> dict:
    offset_details = {}
    bootstrap_frames = []
    prediction_ranges = {
        offset: (low, high)
        for offset, low, high in cfg.prediction_ranges
    }
    aggregate_sequences = np.random.SeedSequence(
        cfg.aggregate_bootstrap_root_seed
    ).spawn(len(cfg.onset_offsets))

    for offset_index, offset in enumerate(
        cfg.onset_offsets
    ):
        rep = replication_summary[
            replication_summary.offset == offset
        ].sort_values("replication")

        counts = []
        ns = []
        for replication in range(
            cfg.replication_count
        ):
            subset = stratum_summary[
                (stratum_summary.offset == offset)
                & (
                    stratum_summary.replication
                    == replication
                )
            ].set_index("stratum")
            counts.append(
                [
                    int(subset.loc[s, "hits"])
                    for s in POSITIVE_STRATA
                ]
            )
            ns.append(
                [
                    int(subset.loc[s, "n"])
                    for s in POSITIVE_STRATA
                ]
            )

        boot_seed = int(
            aggregate_sequences[offset_index]
            .generate_state(
                1, dtype=np.uint32
            )[0]
        )
        boot = m15.hierarchical_bootstrap(
            np.asarray(counts),
            np.asarray(ns),
            cfg.bootstrap_replicates,
            boot_seed,
        )
        bootstrap_frames.append(
            pd.DataFrame(
                {
                    "offset": offset,
                    "replicate": np.arange(
                        cfg.bootstrap_replicates
                    ),
                    "recall": boot,
                }
            )
        )

        point = float(rep.recall_point.mean())
        lower = float(np.quantile(boot, 0.05))
        upper = float(np.quantile(boot, 0.95))
        pass_count = int(rep["pass"].sum())
        fpr_pass_count = int(rep.fpr_pass.sum())
        extreme = bool(
            np.any(
                rep.maximum_fpr_upper_95
                > cfg.extreme_fpr_upper_limit
            )
        )
        fpr_robust = bool(
            fpr_pass_count
            >= cfg.minimum_fpr_pass_replications
            and not extreme
        )
        passed = bool(
            pass_count
            >= cfg.minimum_replication_passes
            and lower
            >= cfg.minimum_global_recall_lower_ci
            and fpr_robust
        )
        strong_fail = bool(
            pass_count <= 2
            or upper
            <= cfg.minimum_global_recall_lower_ci
            or extreme
        )
        verdict = (
            "PASS"
            if passed
            else (
                "STRONG_FAIL"
                if strong_fail
                else "INCONCLUSIVE"
            )
        )
        low, high = prediction_ranges[offset]
        offset_details[str(offset)] = {
            "offset": offset,
            "verdict": verdict,
            "aggregate_recall_point": point,
            "aggregate_recall_lower_95": lower,
            "aggregate_recall_upper_95": upper,
            "replication_pass_count": pass_count,
            "fpr_pass_replication_count": (
                fpr_pass_count
            ),
            "extreme_fpr_violation": extreme,
            "fpr_robust": fpr_robust,
            "prediction_recall_in_range": bool(
                low <= point <= high
            ),
        }

    required = [
        offset_details["-2"]["verdict"],
        offset_details["0"]["verdict"],
        offset_details["2"]["verdict"],
    ]
    if all(value == "PASS" for value in required):
        overall = "PASS_ONSET_TOLERANCE_PM2"
    elif (
        offset_details["0"]["verdict"]
        == "STRONG_FAIL"
        or (
            offset_details["-2"]["verdict"]
            == "STRONG_FAIL"
            and offset_details["2"]["verdict"]
            == "STRONG_FAIL"
        )
    ):
        overall = "STRONG_FAIL_ONSET_TOLERANCE"
    else:
        overall = "INCONCLUSIVE"

    at_least_one_pm4_not_pass = bool(
        offset_details["-4"]["verdict"] != "PASS"
        or offset_details["4"]["verdict"] != "PASS"
    )
    zero_is_max = bool(
        offset_details["0"][
            "aggregate_recall_point"
        ]
        >= max(
            detail["aggregate_recall_point"]
            for detail in offset_details.values()
        )
        - 1e-15
    )
    prediction = {
        "zero_pass": (
            offset_details["0"]["verdict"]
            == "PASS"
        ),
        "minus2_pass": (
            offset_details["-2"]["verdict"]
            == "PASS"
        ),
        "plus2_pass": (
            offset_details["2"]["verdict"]
            == "PASS"
        ),
        "at_least_one_pm4_not_pass": (
            at_least_one_pm4_not_pass
        ),
        "zero_has_maximum_recall": zero_is_max,
        "overall_verdict_confirmed": (
            overall
            == "PASS_ONSET_TOLERANCE_PM2"
        ),
        "all_recall_ranges_confirmed": bool(
            all(
                detail[
                    "prediction_recall_in_range"
                ]
                for detail in offset_details.values()
            )
        ),
    }
    prediction["fully_confirmed"] = bool(
        all(prediction.values())
    )

    return {
        "verdict": overall,
        "offset_details": offset_details,
        "prediction": prediction,
        "bootstrap_df": pd.concat(
            bootstrap_frames, ignore_index=True
        ),
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
        "m15_dependency_sha256": sha256_file(
            M15_DIR / "arara_m15.py"
        ),
    }
    path.write_text(
        json.dumps(environment, indent=2),
        encoding="utf-8",
    )
