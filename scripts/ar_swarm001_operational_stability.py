"""AR-SWARM001-P01: preregistered operational-stability forecast.

Protocol frozen first: docs/preregistration/AR-SWARM001-P01.md,
commit 6d7be731d0c68941d723a28c41b9d661ff60f405.
Synthetic processing service only; not measured telescope hardware.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PROTOCOL = "AR-SWARM001-P01"
VERSION = "1.0.0"
START_SEED = 20261123
WINDOWS_PER_EPISODE = 48
PAST_WINDOWS = 4
FUTURE_WINDOWS = 3
SCENARIOS = (
    "NOMINAL", "CAPACITY", "VISIBLE_CORRUPTION", "LATENCY", "HIDDEN_CORRUPTION"
)
OBSERVABLE_SCENARIOS = SCENARIOS[:4]
TRAIN_EPISODES_PER_OBSERVABLE_SCENARIO = 30
HOLDOUT_EPISODES_PER_SCENARIO = 20
HIDDEN_HOLDOUT_EPISODES = 50
SCORES = ("RZS", "B_ONLY", "I_ONLY", "TAU_ONLY", "LINEAR", "MAX")
CHAMPION_OPTIONS = SCORES[1:]
BOOTSTRAP_SEED = 20261201
BOOTSTRAP_REPLICATES = 400
TARGET_EXTERNAL_ADEQUACY = .80
DEADLINE_SECONDS = .65


@dataclass(frozen=True)
class ForecastBlock:
    """Telemetry available at t and an external oracle computed only after t."""

    regime: str
    episode: int
    seed: int
    telemetry: np.ndarray  # B, I, tau; no truth labels
    labels: np.ndarray     # future external degradation


def episode_seed(scenario_index: int, episode_index: int) -> int:
    if not (0 <= scenario_index < len(SCENARIOS) and 0 <= episode_index < 50):
        raise ValueError("Unregistered scenario or episode")
    return START_SEED + 1000 * scenario_index + episode_index


def generate_episode(regime: str, episode: int) -> ForecastBlock:
    """Simulate processing count, detectable errors, hidden faults and delays.

    The queue is count-based; the external adequacy ratio is a synthetic
    throughput-quality proxy, NOT per-request SLA compliance.
    """
    if regime not in SCENARIOS:
        raise ValueError("Unknown scenario")
    seed = episode_seed(SCENARIOS.index(regime), episode)
    rng = np.random.default_rng(seed)
    if regime == "NOMINAL":
        shock_start, shock_len, severity = -1, 0, 0.0
    else:
        shock_start = int(rng.integers(12, 19))
        shock_len = int(rng.integers(14, 21))
        severity = float(rng.uniform(.65, .85))

    accepted = np.zeros(WINDOWS_PER_EPISODE)
    detected = np.zeros(WINDOWS_PER_EPISODE)
    processed = np.zeros(WINDOWS_PER_EPISODE)
    p95 = np.zeros(WINDOWS_PER_EPISODE)
    adequacy = np.zeros(WINDOWS_PER_EPISODE)
    backlog = 0

    for t in range(WINDOWS_PER_EPISODE):
        fault = shock_start <= t < shock_start + shock_len
        demand = int(rng.poisson(48)) + (20 if rng.random() < .08 else 0)
        factor = (1. - .70 * severity) if fault and regime == "CAPACITY" else 1.
        offered = int(rng.poisson(56. * factor))
        queue_before = backlog
        completed = min(queue_before + demand, offered)
        backlog = min(300, queue_before + demand - completed)
        visible_p = .015 + (.55 * severity if fault and regime == "VISIBLE_CORRUPTION" else 0.)
        hidden_p = .01 + (.55 * severity if fault and regime == "HIDDEN_CORRUPTION" else 0.)
        delay_base = (.025 + .45 * queue_before / max(offered, 1)
                      + (1.35 * severity if fault and regime == "LATENCY" else 0.))
        if completed:
            visible = rng.random(completed) < visible_p
            hidden = rng.random(completed) < hidden_p
            delay = delay_base + rng.exponential(scale=.055, size=completed)
            detected_count = int(np.count_nonzero(visible))
            externally_valid = int(np.count_nonzero(
                (~visible) & (~hidden) & (delay <= DEADLINE_SECONDS)
            ))
            p95[t] = float(np.quantile(delay, .95))
        else:
            detected_count = externally_valid = 0
            p95[t] = delay_base
        processed[t] = completed
        detected[t] = detected_count
        accepted[t] = completed - detected_count
        adequacy[t] = min(1., externally_valid / max(demand, 1))

    telemetry, labels = [], []
    for t in range(PAST_WINDOWS - 1, WINDOWS_PER_EPISODE - FUTURE_WINDOWS):
        past = slice(t - PAST_WINDOWS + 1, t + 1)
        future = slice(t + 1, t + FUTURE_WINDOWS + 1)
        telemetry.append([
            float(np.mean(accepted[past])),
            float(.01 + np.sum(detected[past]) / max(1., float(np.sum(processed[past])))),
            float(np.mean(p95[past])),
        ])
        labels.append(int(np.mean(adequacy[future]) < TARGET_EXTERNAL_ADEQUACY))
    x, y = np.asarray(telemetry), np.asarray(labels, dtype=np.int8)
    if x.shape != (42, 3) or y.shape != (42,):
        raise AssertionError("Past/future episode sample count mismatch")
    if not np.isfinite(x).all() or np.any(x[:, 0] < 0) or np.any(x[:, 1:] <= 0):
        raise AssertionError("Impossible operational proxies")
    return ForecastBlock(regime, episode, seed, x, y)


def generate_cohorts() -> tuple[list[ForecastBlock], list[ForecastBlock], list[ForecastBlock]]:
    train, obs_test, hidden = [], [], []
    for regime in SCENARIOS:
        for episode in range(50):
            example = generate_episode(regime, episode)
            if regime == "HIDDEN_CORRUPTION":
                hidden.append(example)
            elif episode < TRAIN_EPISODES_PER_OBSERVABLE_SCENARIO:
                train.append(example)
            else:
                obs_test.append(example)
    if (len(train), len(obs_test), len(hidden)) != (120, 80, 50):
        raise AssertionError("Episode split mismatch")
    ids = [b.seed for b in [*train, *obs_test, *hidden]]
    if len(set(ids)) != len(ids):
        raise AssertionError("Duplicate seed")
    return train, obs_test, hidden


def aggregate(blocks: list[ForecastBlock]) -> tuple[np.ndarray, np.ndarray]:
    if not blocks:
        raise ValueError("Empty cohort")
    return (np.concatenate([b.telemetry for b in blocks]),
            np.concatenate([b.labels for b in blocks]))


def trained_normalization(train_telemetry: np.ndarray) -> dict:
    if train_telemetry.ndim != 2 or train_telemetry.shape[1] != 3 or not len(train_telemetry):
        raise ValueError("Bad training telemetry")
    return {"means": np.mean(train_telemetry, axis=0),
            "stddev": np.std(train_telemetry, axis=0)}


def score_telemetry(telemetry: np.ndarray, normalization: dict) -> dict[str, np.ndarray]:
    x = np.asarray(telemetry, dtype=np.float64)
    if (x.ndim != 2 or x.shape[1] != 3 or not np.isfinite(x).all()
            or np.any(x[:, 0] < 0) or np.any(x[:, 1:] <= 0)):
        raise ValueError("Invalid operational telemetry")
    scale = np.where(normalization["stddev"] == 0, 1., normalization["stddev"])
    z = (x - normalization["means"]) / scale
    z[:, normalization["stddev"] == 0] = 0.
    return {
        "RZS": -x[:, 0] / (x[:, 1] * x[:, 2]),
        "B_ONLY": -x[:, 0],
        "I_ONLY": x[:, 1],
        "TAU_ONLY": x[:, 2],
        "LINEAR": -z[:, 0] + z[:, 1] + z[:, 2],
        "MAX": np.maximum.reduce([-z[:, 0], z[:, 1], z[:, 2]]),
    }


def tie_aware_auc(labels: np.ndarray, scores: np.ndarray) -> float | None:
    y = np.asarray(labels)
    values = np.asarray(scores, dtype=np.float64)
    if y.ndim != 1 or y.shape != values.shape or not np.isin(y, [0, 1]).all():
        raise ValueError("Bad binary labels")
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite scores")
    positives = int(np.count_nonzero(y == 1))
    negatives = len(y) - positives
    if not positives or not negatives:
        return None
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    ranks = np.empty(len(y))
    start = 0
    while start < len(y):
        end = start + 1
        while end < len(y) and sorted_values[start] == sorted_values[end]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.
        start = end
    return float((np.sum(ranks[y == 1]) - positives * (positives + 1) / 2)
                 / (positives * negatives))


def confusion(labels: np.ndarray, risks: np.ndarray, threshold: float) -> dict:
    y = np.asarray(labels, dtype=np.int8)
    alert = np.asarray(risks) > threshold
    tp = int(np.count_nonzero(alert & (y == 1)))
    fn = int(np.count_nonzero(~alert & (y == 1)))
    fp = int(np.count_nonzero(alert & (y == 0)))
    tn = int(np.count_nonzero(~alert & (y == 0)))
    if tp + fn + fp + tn != len(y):
        raise AssertionError("Confusion counts inconsistent")
    return {
        "TP": tp, "FN": fn, "FP": fp, "TN": tn,
        "recall": tp / (tp + fn) if tp + fn else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "alarm_coverage": (tp + fp) / len(y) if len(y) else None,
    }


def evaluate(y: np.ndarray, score: dict, thresholds: dict) -> dict:
    return {name: {
        "roc_auc": tie_aware_auc(y, score[name]),
        **confusion(y, score[name], thresholds[name]),
    } for name in SCORES}


def bootstrap_auc_delta(blocks: list[ForecastBlock], norm: dict, champion: str) -> dict:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    grouped = []
    for block in blocks:
        scores = score_telemetry(block.telemetry, norm)
        grouped.append((block.labels, scores["RZS"], scores[champion]))
    differences = []
    for _ in range(BOOTSTRAP_REPLICATES):
        picks = rng.integers(0, len(grouped), size=len(grouped))
        y = np.concatenate([grouped[i][0] for i in picks])
        rz = np.concatenate([grouped[i][1] for i in picks])
        ch = np.concatenate([grouped[i][2] for i in picks])
        auc_rz = tie_aware_auc(y, rz)
        auc_ch = tie_aware_auc(y, ch)
        if auc_rz is not None and auc_ch is not None:
            differences.append(auc_rz - auc_ch)
    return {
        "seed": BOOTSTRAP_SEED,
        "resamples_requested": BOOTSTRAP_REPLICATES,
        "resamples_with_both_classes": len(differences),
        "percentile_95_CI": [float(np.percentile(differences, p)) for p in (2.5, 97.5)]
        if differences else None,
    }


def hypothesis_verdicts(observable: dict, hidden: dict, champion: str) -> dict:
    rz = observable["RZS"]
    best = observable[champion]
    blind = hidden["RZS"]
    if rz["roc_auc"] is None or best["roc_auc"] is None:
        h1 = "NOT_EVALUABLE"
    elif rz["roc_auc"] >= .70 and rz["roc_auc"] - best["roc_auc"] >= .02:
        h1 = "SUPPORTED_IN_SIMULATION"
    else:
        h1 = "NOT_SUPPORTED_IN_SIMULATION"
    if rz["recall"] is None or rz["false_positive_rate"] is None:
        h2 = "NOT_EVALUABLE"
    elif rz["recall"] >= .60 and rz["false_positive_rate"] <= .20:
        h2 = "SUPPORTED_IN_SIMULATION"
    else:
        h2 = "NOT_SUPPORTED_IN_SIMULATION"
    if blind["recall"] is None:
        h3 = "NOT_EVALUABLE"
    elif blind["recall"] <= .30:
        h3 = "BLIND_SPOT_EXPOSED_IN_SIMULATION"
    else:
        h3 = "BLIND_SPOT_NOT_ESTABLISHED"
    return {
        "H1_added_ranking_information": h1,
        "H2_advance_alarm": h2,
        "H3_hidden_corruption_limit": h3,
    }


def canonical_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run() -> dict:
    report = {
        "protocol": PROTOCOL,
        "version": VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "source": {
            "kind": "SYNTHETIC_PROCESSING_SERVICE_ONLY",
            "seed_start": START_SEED,
            "stability_paper": "https://philarchive.org/archive/ROMTRL",
            "repair_paper": "https://philarchive.org/archive/ROMRSA",
        },
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
        "hypotheses": {name: "INCONCLUSIVE_IMPLEMENTATION" for name in (
            "H1_added_ranking_information", "H2_advance_alarm",
            "H3_hidden_corruption_limit",
        )},
    }
    try:
        train, observable_blocks, hidden_blocks = generate_cohorts()
        report["gates"]["G1"] = "PASS"
        x_train, y_train = aggregate(train)
        x_obs, y_obs = aggregate(observable_blocks)
        x_hidden, y_hidden = aggregate(hidden_blocks)
        if not all(np.isfinite(v).all() for v in (x_train, x_obs, x_hidden)):
            raise ValueError("Bad telemetry")
        if any(len(b.labels) != 42 for b in [*train, *observable_blocks, *hidden_blocks]):
            raise ValueError("Episode length mismatch")
        report["gates"]["G2"] = "PASS"
        norm = trained_normalization(x_train)
        train_scores = score_telemetry(x_train, norm)
        training_auc = {name: tie_aware_auc(y_train, train_scores[name]) for name in SCORES}
        if not np.any(y_train == 0) or any(v is None for v in training_auc.values()):
            raise ValueError("Training sample has only one outcome class")
        # Comparator and thresholds are trained on observable episodes ONLY.
        champion = max(CHAMPION_OPTIONS, key=lambda name: training_auc[name])
        thresholds = {
            name: float(np.quantile(train_scores[name][y_train == 0], .90))
            for name in SCORES
        }
        report["gates"]["G3"] = "PASS"
        obs = evaluate(y_obs, score_telemetry(x_obs, norm), thresholds)
        hidden = evaluate(y_hidden, score_telemetry(x_hidden, norm), thresholds)
        by_scenario = {}
        for regime in SCENARIOS:
            cohort = [
                b for b in (hidden_blocks if regime == "HIDDEN_CORRUPTION"
                            else observable_blocks) if b.regime == regime
            ]
            xs, ys = aggregate(cohort)
            by_scenario[regime] = {
                "episodes": len(cohort),
                "forecasts": len(ys),
                "positives": int(np.sum(ys)),
                "negatives": int(len(ys) - np.sum(ys)),
                "methods": evaluate(ys, score_telemetry(xs, norm), thresholds),
            }
        if (len(y_train), len(y_obs), len(y_hidden)) != (5040, 3360, 2100):
            raise AssertionError("Unexpected split and forecast counts")
        if sum(v["forecasts"] for v in by_scenario.values()) != len(y_obs) + len(y_hidden):
            raise AssertionError("Scenario conservation failed")
        report["gates"]["G4"] = "PASS"
        report["calibration"] = {
            "observable_training_episode_count": len(train),
            "observable_training_forecasts": len(y_train),
            "train_positive_count": int(np.sum(y_train)),
            "train_negative_count": int(len(y_train) - np.sum(y_train)),
            "train_roc_auc": training_auc,
            "frozen_baseline_selection_order": list(CHAMPION_OPTIONS),
            "champion": champion,
            "training_feature_mean": [float(v) for v in norm["means"]],
            "training_feature_stddev": [float(v) for v in norm["stddev"]],
            "alert_thresholds": thresholds,
        }
        report["holdout"] = {
            "observable": {
                "episodes": len(observable_blocks),
                "forecasts": len(y_obs),
                "positives": int(np.sum(y_obs)),
                "negatives": int(len(y_obs) - np.sum(y_obs)),
                "methods": obs,
            },
            "hidden_corruption": {
                "episodes": len(hidden_blocks),
                "forecasts": len(y_hidden),
                "positives": int(np.sum(y_hidden)),
                "negatives": int(len(y_hidden) - np.sum(y_hidden)),
                "methods": hidden,
            },
            "by_scenario": by_scenario,
            "episode_bootstrap_auc_difference": bootstrap_auc_delta(
                observable_blocks, norm, champion
            ),
        }
        report["hypotheses"] = hypothesis_verdicts(obs, hidden, champion)
        report["gates"]["G5"] = "PASS"
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error_type"] = type(error).__name__
        report["error_detail"] = str(error)[:500]
    report["payload_sha256"] = canonical_hash(report)
    return report


def main() -> int:
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_swarm001_p01.json")
    result = run()
    path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "gates": result["gates"],
        "hypotheses": result["hypotheses"],
        "champion": result.get("calibration", {}).get("champion"),
        "observable_auc": result.get("holdout", {}).get("observable", {}).get(
            "methods", {}).get("RZS", {}).get("roc_auc"),
        "error": result.get("error_detail"),
        "payload_sha256": result["payload_sha256"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
