"""Fixed-observation counterfactual demonstrating hidden-onset score dependence.

This is an artificial numerical fixture, not a calibrated experiment or a
measurement of astronomical recall, false positives, or prevalence.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "milestones/M38B_recovery"
sys.path.insert(0, str(ARCHIVE))
import arara_m38b as detector  # noqa: E402


def candidate_score(true_onset: int) -> float:
    """Hold all observed data and the causal anchor fixed; vary true onset."""
    cfg = detector.Config(endpoint_start=179, endpoint_stop=179)
    residual = np.zeros((1, 180), dtype=np.float64)
    residual[0, 171:180] = np.linspace(1.0, 2.0, 9)
    reference = np.zeros_like(residual)
    params = {
        "target_scale": np.ones(1, dtype=np.float64),
        "residual_scale": np.ones(1, dtype=np.float64),
        "residual_phi": np.array([0.2], dtype=np.float64),
    }
    anchor = np.full((1, 1), 80, dtype=np.int16)
    objective = np.zeros((1, 1), dtype=np.float64)
    with patch.object(detector.m34, "estimate_onset_grid", return_value=(anchor, objective)):
        output = detector.score_latent_grid_bank(
            residual=residual,
            onset=np.array([true_onset], dtype=np.int16),
            true_latent_u=np.array([0.5], dtype=np.float64),
            template_scale=np.ones(1, dtype=np.float64),
            true_shape_index=np.zeros(1, dtype=np.int8),
            true_duration=np.array([30], dtype=np.int16),
            processed_reference=reference,
            params=params,
            cfg=cfg,
        )
    return float(output["grid_score_grid"][0, 0])


def main() -> int:
    first = candidate_score(80)
    second = candidate_score(110)
    changed = not np.isclose(first, second, rtol=0.0, atol=1e-12)
    report = {
        "audit": "historical candidate counterfactual score dependence",
        "observed_inputs_changed": False,
        "hidden_true_onset_values": [80, 110],
        "candidate_score_onset_80": first,
        "candidate_score_onset_110": second,
        "candidate_scores_differ": bool(changed),
        "scientific_verdict": None,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not changed:
        raise AssertionError("Boundary-mask witness did not change candidate score")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
