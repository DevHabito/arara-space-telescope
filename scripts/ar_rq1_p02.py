"""AR-RQ1-P02: paired photometric ambiguity with a hypothetical diagnostic.

The frozen protocol is docs/preregistration/AR-RQ1-P02.md. These are
simulations, not real detector measurements or a novel classification method.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform

import numpy as np

PROTOCOL = "AR-RQ1-P02"
VERSION = "1.0.0"
SEED = 20261121
PAIRS = 512
EPOCHS = 256
REFERENCE_STARS = 31
THRESHOLD = 0.75
SCENARIOS = {
    "ALIGNED": (0.0, 1.5),
    "UNINFORMATIVE": (0.75, 0.75),
    "INVERTED": (1.5, 0.0),
}
MODELS = ("PHOTOMETRY_ONLY", "AUX_DIAGNOSTIC")


def paired_observation(i: int) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Return identical-label photometry, reference data and two noise draws."""
    if not 0 <= i < PAIRS:
        raise ValueError("Pair index outside frozen protocol")
    rng = np.random.default_rng(SEED + i)
    t = np.arange(EPOCHS)
    phase = rng.uniform(0.0, 2.0 * np.pi)
    drift = 0.018 * np.sin(2.0 * np.pi * t / 96.0 + phase)
    drift += 0.007 * t / 256.0
    ref_noise = rng.normal(0.0, 0.003, (REFERENCE_STARS, EPOCHS))
    target_noise = rng.normal(0.0, 0.003, EPOCHS)
    refs = 1.0 + drift[None, :] + ref_noise
    target = 1.0 + drift + target_noise
    target[128:136] -= 0.020
    z_a, z_i = rng.normal(size=2)
    return target, refs, float(z_a), float(z_i)


def photometry_depth(target: np.ndarray, references: np.ndarray) -> float:
    """A fixed event contrast using independent reference-star median."""
    if target.shape != (EPOCHS,) or references.shape != (REFERENCE_STARS, EPOCHS):
        raise ValueError("Unexpected photometry shape")
    z = target - np.median(references, axis=0)
    return float(np.mean(z[128:136]) - (np.mean(z[104:112]) + np.mean(z[152:160])) / 2.0)


def classification_metrics(a_correct: int, i_correct: int) -> dict:
    """The balanced evaluation includes the same number of each label."""
    retained = a_correct / PAIRS
    rejected = i_correct / PAIRS
    return {
        "astro_correct_count": a_correct,
        "artifact_correct_count": i_correct,
        "astro_retention": retained,
        "artifact_rejection": rejected,
        "artifact_miss_rate": 1.0 - rejected,
        "balanced_accuracy": (retained + rejected) / 2.0,
    }


def evaluate() -> dict:
    counts = {
        scenario: {
            model: {"a_correct": 0, "i_correct": 0}
            for model in MODELS
        } for scenario in SCENARIOS
    }
    identical_pairs = 0
    for i in range(PAIRS):
        target, references, z_a, z_i = paired_observation(i)
        # Reproduce both observations explicitly: labels are *not* observable
        # from the same target and reference array alone.
        target_a, target_i = target.copy(), target.copy()
        reference_a, reference_i = references.copy(), references.copy()
        if (target_a.tobytes() == target_i.tobytes()
                and reference_a.tobytes() == reference_i.tobytes()):
            identical_pairs += 1
        depth_a = photometry_depth(target_a, reference_a)
        depth_i = photometry_depth(target_i, reference_i)
        photo_predict_i_a = depth_a > -0.010
        photo_predict_i_i = depth_i > -0.010
        for scenario, (mu_a, mu_i) in SCENARIOS.items():
            phot = counts[scenario]["PHOTOMETRY_ONLY"]
            phot["a_correct"] += int(not photo_predict_i_a)
            phot["i_correct"] += int(photo_predict_i_i)
            aux = counts[scenario]["AUX_DIAGNOSTIC"]
            aux["a_correct"] += int(mu_a + z_a <= THRESHOLD)
            aux["i_correct"] += int(mu_i + z_i > THRESHOLD)

    results = {
        scenario: {
            model: classification_metrics(c["a_correct"], c["i_correct"])
            for model, c in models.items()
        } for scenario, models in counts.items()
    }
    phi = (1.0 + math.erf(0.75 / math.sqrt(2.0))) / 2.0
    aux = lambda scenario: results[scenario]["AUX_DIAGNOSTIC"]["balanced_accuracy"]
    gates = {
        "G1_photometric_nonidentifiability": identical_pairs == PAIRS and all(
            results[s]["PHOTOMETRY_ONLY"]["balanced_accuracy"] == 0.5
            for s in SCENARIOS
        ),
        "G2_aligned_informativeness": aux("ALIGNED") >= 0.70 and abs(aux("ALIGNED") - phi) <= 0.06,
        "G3_uninformative_diagnostic": abs(aux("UNINFORMATIVE") - 0.5) <= 0.06,
        "G4_inverted_diagnostic_failure": aux("INVERTED") <= 0.33 and abs(aux("INVERTED") - (1.0 - phi)) <= 0.06,
        "G5_count_and_metric_consistency": all(
            all(
                isinstance(m[k], int) and 0 <= m[k] <= PAIRS
                for k in ("astro_correct_count", "artifact_correct_count")
            ) and abs(m["astro_retention"] - m["astro_correct_count"] / PAIRS) <= 1e-12
              and abs(m["artifact_rejection"] - m["artifact_correct_count"] / PAIRS) <= 1e-12
              and abs(m["artifact_miss_rate"] - (1.0 - m["artifact_rejection"])) <= 1e-12
              and abs(m["balanced_accuracy"] - (
                  m["astro_retention"] + m["artifact_rejection"]
              ) / 2.0) <= 1e-12
            for models in results.values() for m in models.values()
        ),
    }
    payload = {
        "protocol": PROTOCOL,
        "implementation_version": VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "seed_start": SEED,
        "pairs": PAIRS,
        "class_examples_per_scenario": {"A": PAIRS, "I": PAIRS},
        "identical_photometry_pairs": identical_pairs,
        "expected_gaussian_balanced_accuracy": {
            "ALIGNED": phi,
            "UNINFORMATIVE": 0.5,
            "INVERTED": 1.0 - phi,
        },
        "results": results,
        "gates": {k: "PASS" if v else "FAIL" for k, v in gates.items()},
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return {**payload, "payload_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, ensure_ascii=False))
