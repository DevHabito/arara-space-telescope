"""AR-RQ1-P01: synthetic calibration stress test, with no telescope observations.

The protocol was committed before implementation:
docs/preregistration/AR-RQ1-P01.md
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

PROTOCOL_ID = "AR-RQ1-P01"
SEED_START = 20261120
TRIAL_COUNT = 64
EPOCH_COUNT = 256
REFERENCE_COUNT = 31
EVENT_SLICE = slice(128, 136)
EVENT_DEPTH = -0.020
SCENARIOS = ("SHARED", "REF_CONTAM", "TARGET_ARTIFACT")
ESTIMATORS = ("RAW", "MEAN_REF", "MEDIAN_REF")


def generate_trial(trial: int, scenario: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return target with event, paired null target, and reference curves."""
    if not 0 <= trial < TRIAL_COUNT:
        raise ValueError("Trial index out of protocol bounds")
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")

    rng = np.random.default_rng(SEED_START + trial)
    epochs = np.arange(EPOCH_COUNT)
    phase = rng.uniform(0.0, 2.0 * np.pi)
    drift = 0.018 * np.sin(2.0 * np.pi * epochs / 96.0 + phase)
    drift += 0.007 * epochs / 256.0

    reference_noise = rng.normal(0.0, 0.003, (REFERENCE_COUNT, EPOCH_COUNT))
    target_noise = rng.normal(0.0, 0.003, EPOCH_COUNT)
    corrupted_indices = rng.choice(REFERENCE_COUNT, size=12, replace=False)

    references = 1.0 + drift[None, :] + reference_noise
    target_null = 1.0 + drift + target_noise
    if scenario == "REF_CONTAM":
        references[corrupted_indices, EVENT_SLICE] -= 0.040
    elif scenario == "TARGET_ARTIFACT":
        target_null[EVENT_SLICE] -= 0.020

    target_event = target_null.copy()
    target_event[EVENT_SLICE] += EVENT_DEPTH
    return target_event, target_null, references


def correct(target: np.ndarray, references: np.ndarray, estimator: str) -> np.ndarray:
    """Use only independent references to estimate shared instrumental change."""
    if target.shape != (EPOCH_COUNT,) or references.shape != (REFERENCE_COUNT, EPOCH_COUNT):
        raise ValueError("Unexpected curve shapes")
    if estimator == "RAW":
        return target - 1.0
    if estimator == "MEAN_REF":
        return target - references.mean(axis=0)
    if estimator == "MEDIAN_REF":
        return target - np.median(references, axis=0)
    raise ValueError("Unknown estimator")


def window_depth(corrected: np.ndarray) -> float:
    """Signed fixed-window contrast: negative is a dimming."""
    event = float(np.mean(corrected[128:136]))
    sidebands = (
        float(np.mean(corrected[104:112]))
        + float(np.mean(corrected[152:160]))
    ) / 2.0
    return event - sidebands


def evaluate() -> dict:
    results: dict[str, dict[str, dict[str, float]]] = {}
    for scenario in SCENARIOS:
        trial_data = {est: {"null": [], "retention": []} for est in ESTIMATORS}
        for trial in range(TRIAL_COUNT):
            target_event, target_null, references = generate_trial(trial, scenario)
            for estimator in ESTIMATORS:
                null_depth = window_depth(correct(target_null, references, estimator))
                event_depth = window_depth(correct(target_event, references, estimator))
                trial_data[estimator]["null"].append(null_depth)
                trial_data[estimator]["retention"].append(
                    (event_depth - null_depth) / EVENT_DEPTH
                )
        results[scenario] = {}
        for estimator in ESTIMATORS:
            null_values = np.asarray(trial_data[estimator]["null"])
            retentions = np.asarray(trial_data[estimator]["retention"])
            results[scenario][estimator] = {
                "median_abs_null": round(float(np.median(np.abs(null_values))), 12),
                "false_dip_rate": round(float(np.mean(null_values <= -0.010)), 12),
                "max_abs_retention_error": round(float(np.max(np.abs(retentions - 1.0))), 12),
            }

    gates = {
        "G1_shared_drift_benefit": (
            results["SHARED"]["MEDIAN_REF"]["median_abs_null"]
            <= 0.5 * results["SHARED"]["RAW"]["median_abs_null"]
        ),
        "G2_reference_outlier_resistance": (
            results["REF_CONTAM"]["MEDIAN_REF"]["median_abs_null"]
            <= 0.4 * results["REF_CONTAM"]["MEAN_REF"]["median_abs_null"]
        ),
        "G3_target_local_artifact_failure": (
            results["TARGET_ARTIFACT"]["MEDIAN_REF"]["false_dip_rate"] >= 0.9
        ),
        "G4_paired_injection_sanity": all(
            results[scenario][estimator]["max_abs_retention_error"] <= 1e-10
            for scenario in SCENARIOS
            for estimator in ESTIMATORS
        ),
    }
    payload = {
        "protocol": PROTOCOL_ID,
        "numpy_version": np.__version__,
        "seed_start": SEED_START,
        "trials_per_scenario": TRIAL_COUNT,
        "results": results,
        "gates": {name: "PASS" if passed else "FAIL" for name, passed in gates.items()},
    }
    serialized = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    return {
        **payload,
        "payload_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
    }


def main() -> None:
    print(json.dumps(evaluate(), indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
