"""Non-scientific microbenchmark of two projection implementations.

Never generates positives/negatives, evaluates holdout gates, or computes
recall or false-positive rates. CPU/RAM observations are runner-dependent.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import resource
import statistics
import sys
from time import perf_counter
import tracemalloc

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))
from independent_projection import score_projected  # noqa: E402
import observable_candidate  # noqa: E402


def benchmark(function, residual, templates, reference, repetitions=5):
    """Record median wall time and Python traced peak for fixed arrays."""
    function(residual, templates, reference)  # warmup: no observed labels
    times = []
    tracemalloc.start()
    for _ in range(repetitions):
        started = perf_counter()
        function(residual, templates, reference)
        times.append(perf_counter() - started)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"median_wall_seconds": statistics.median(times),
            "python_traced_peak_bytes": int(peak), "repetitions": repetitions}


def main() -> int:
    rng = np.random.default_rng(20261021)
    # Arbitrary low-cost numerical fixtures; not the M38B-R simulation model.
    target = rng.normal(size=(3, 16, 8))
    reference = rng.normal(size=(3, 16, 8))
    templates = rng.normal(size=(3, 96, 16, 8))
    original = observable_candidate.archived.m37.projected_scores_hypotheses
    new = score_projected
    expected, _ = original(target, templates, reference)
    actual, _ = new(target, templates, reference)
    if not np.allclose(expected, actual, rtol=1e-10, atol=1e-10):
        raise AssertionError("Well-conditioned benchmark fixture disagrees")


    # Explicit diagnostic: nearly parallel template with an exact real-valued
    # target score sqrt(8/7); this is never an astronomical observation.
    ill_target = np.array([[[1., -1., 1., -1., 1., -1., 1., -1.]]])
    ill_reference = np.ones((1, 1, 8))
    ill_template = ill_reference[:, None, :, :].copy()
    ill_template[0, 0, 0, 0] += 1.2e-6
    old_ill, _ = original(ill_target, ill_template, ill_reference)
    new_ill, _ = new(ill_target, ill_template, ill_reference)
    analytic_score = float(np.sqrt(8.0 / 7.0))

    # Full endpoint/shape/duration/grid mechanics on one unlabeled curve.
    # This is a resource benchmark, not a valid synthetic negative or positive.
    full_cfg = observable_candidate.archived.Config()
    full_target = rng.normal(size=(1, 180))
    full_reference = rng.normal(size=(1, 180))
    full_params = {"residual_phi": np.array([0.3])}
    full_candidate = observable_candidate.score_observation_only
    from unittest.mock import patch

    def run_independent_bank():
        with patch.object(
            observable_candidate.archived.m37,
            "projected_scores_hypotheses",
            side_effect=score_projected,
        ):
            return full_candidate(
                full_target, full_reference, full_params, full_cfg
            )

    def run_archived_bank():
        return full_candidate(
            full_target, full_reference, full_params, full_cfg
        )

    def single_run(function):
        tracemalloc.start()
        started = perf_counter()
        scores = function()["grid_score_grid"]
        elapsed = perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return scores, {"wall_seconds": elapsed, "python_traced_peak_bytes": peak}

    old_full, old_full_metrics = single_run(run_archived_bank)
    new_full, new_full_metrics = single_run(run_independent_bank)
    if not np.allclose(old_full, new_full, rtol=1e-9, atol=1e-9):
        raise AssertionError("Unlabeled full-bank scores differ unexpectedly")

    recorded = {
        "scope": "unlabeled numerical microbenchmark only",
        "git_sha": os.environ.get("GITHUB_SHA", "local-untracked"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "fixture_shape": list(templates.shape),
        "max_absolute_score_difference": float(np.max(np.abs(actual - expected))),
        "near_parallel_analytic_score": analytic_score,
        "near_parallel_archived_score": float(old_ill[0, 0, 0]),
        "near_parallel_independent_score": float(new_ill[0, 0, 0]),
        "near_parallel_archived_absolute_error": float(abs(old_ill[0, 0, 0] - analytic_score)),
        "near_parallel_independent_absolute_error": float(abs(new_ill[0, 0, 0] - analytic_score)),
        "full_candidate_fixture_shape": list(full_target.shape),
        "full_candidate_archived_projector": old_full_metrics,
        "full_candidate_independent_projector": new_full_metrics,
        "full_candidate_score_max_abs_difference": float(np.max(np.abs(old_full - new_full))),
        "archived_energy_formula": benchmark(original, target, templates, reference),
        "independent_vector_projection": benchmark(new, target, templates, reference),
        "linux_process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "calibration_executed": False,
        "holdouts_opened": False,
        "scientific_verdict": None,
    }
    output = ROOT / "m38br_projection_benchmark.json"
    output.write_text(json.dumps(recorded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(recorded, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
