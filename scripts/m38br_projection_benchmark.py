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

    recorded = {
        "scope": "unlabeled numerical microbenchmark only",
        "git_sha": os.environ.get("GITHUB_SHA", "local-untracked"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "fixture_shape": list(templates.shape),
        "max_absolute_score_difference": float(np.max(np.abs(actual - expected))),
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
