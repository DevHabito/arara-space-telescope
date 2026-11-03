# M38B-R observed-data provenance audit — 2026-11-03

**Classification:** Pre-outcome engineering verification, not a detector validation.
The historical `milestones/` files and scientific thresholds are unchanged.

## Source-based dataflow finding

The archived M38B positive evaluator builds an observed target from a simulated
injection and passes `raw_true` to the archived M29 preprocessor. The archived
negative evaluator passes a *virtual* `true_signal` to the same preprocessor.
In `arara_m29_dependency.py::sbw_with_reference_nuisance`, that second input
is shape-checked and then used to compute `processed_signal`, a diagnostic
value. The operational outputs `residual`, `processed_reference`, and
`parameters` are computed from measured `y`. The archival M38B **scorer**
separately accepts simulated onset and other oracle arguments; this is a
distinct, documented leakage problem (issue #4).

`observed_preprocessing.preprocess_observations` independently expresses the
M29 operational preprocessing directly from an observed star cube, accepting
no truth, label, onset, injection or synthetic signal input. The function checks
shape, baseline, finite inputs and finite outputs. It is numerically compared
with the actual archive, with deliberately different supplied truth. The
integration function `score_observed_stars` feeds the existing uncalibrated
`observable_candidate.score_observation_only` entrypoint, and hence does **not**
claim source independence of its archived estimator, template bank or projection.

## Preconditions and causal meaning

For the frozen fixture, the first star is the target and the remaining
observed stars are references, baseline length is 50 samples, and endpoint
measurements are at or after 81. Baseline statistics depend on the first 50
observations, AR(1) filtering uses the previous sample, and reference median
uses only stars observed at the same time. The software tests change only
future samples **after** the measured endpoint, while leaving measured past
and labels unrelated. This establishes a bounded fixture-level noninterference
test, not a proof for every possible observation stream or external telemetry.

A fixed-observation counterfactual varying a supplied `raw_signal` is
meaningful as a leakage test. It is **not** a claim that simulated `raw_true`
could be varied independently of its physical injection while still referring
to the same synthetic event. The test intentionally holds observed `y` fixed.

## Important unresolved boundaries

- No complete independent M38B-R end-to-end detection implementation exists.
- Undefined/degenerate hinge objectives can return the first candidate with
  `-inf`; this must not be interpreted as an identified physical onset.
- The candidate's `cfg` object, upstream data acquisition, simulation
  generation, quality flags and downstream decision rules still need
  end-to-end provenance and causality auditing.
- Finite NumPy arrays do not establish floating-point stability under all
  possible physical input magnitudes.
- No new calibration, holdout, FPR, recall, astronomical detection or
  physical instrument feasibility is established here.

## Execution gate

Run `python -m unittest discover -s tests -p 'test_m38br_observed_preprocessing.py' -v`
and full `research-audit` CI; inspect execution logs before recording test
results. The existing Lean 4 library should also continue to build; Lean
does not automatically verify this NumPy implementation.

**Scientific gate:** M38B-R remains `approved_for_calibration: false`.
