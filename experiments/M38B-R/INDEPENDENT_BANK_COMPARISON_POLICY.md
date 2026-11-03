# P0.3 independent complete-bank comparison — protocol fixed before implementation

**Recorded:** 3 November 2026. **Scope:** pre-outcome software and numerical checks on constructed unlabelled arrays only. No calibration, holdouts, synthetic detection-performance study, astronomical data or physical inference.

I am recording comparison criteria before creating a new bank implementation or observing its discrepancies. I will preserve unexpected failures and numerical differences in this audit rather than relaxing a bound after the fact.

## Independent implementation contract

- The new `independent_bank.py` must not import historical `milestones/` or `observable_candidate.py`. It can call only the new `independent_onset.py` and `independent_projection.py`, NumPy and standard-library modules; a separate observation-only entrypoint may use `observed_preprocessing.py`.
- The reference must calculate the four template shapes from their equations, then apply the fixed AR(1) filter and explicit reference projection. It must preserve the historically declared latent points `0, .25, .5, .75, 1`, durations `24..60`, onset candidates `70..120`, nine template samples (eight filtered samples), endpoint grid `81..179` and measured past-only onset selection `50..endpoint-9`.
- Linear templates are latent-invariant, so each endpoint performs `37 * (1 + 3 * 5) = 592` template calculations. For 99 endpoints that is 58,608 actual evaluations per curve. Nominal slots are 73,260; neither number counts independent trials.
- Resolve equal scores by ascending **latent index, duration, shape index**, following the actual prototype's tie logic. Return the chosen label as a diagnostic, not a proven true physical parameter.
- If the onset objective is `-inf`, do **not** interpret the default chosen onset as meaningful. Report `alignment_defined_grid = false` and fail-closed at that endpoint (`score = -inf`, labels `-1`); make any departure from the historical prototype explicit rather than claiming numerical equivalence.
- The default configuration is the full historical geometry. For fast isolated unit tests, a shortened endpoint tuple may be used *only* when the test and report declare the fixture diagnostic and not protocol-equivalent.

## Comparison criteria (frozen in this document)

1. **Stable reference fixtures:** arrays drawn from a fixed, stated NumPy RNG seed, with finite residual and reference values, finite `residual_phi`, no deliberately near-parallel template/reference geometry and a defined onset. Compare independent bank maxima against `observable_candidate.score_observation_only` with `rtol=1e-9` and `atol=1e-9`; compare chosen shape/duration/latent indexes only where their computed leading-score margin exceeds `1e-7` and the numeric agreement condition is satisfied. An unexplained score divergence fails the test; it does not authorize a tolerance change.
2. **Causal future-only perturbation:** change all measured star curves *strictly after* the final tested endpoint. Earlier score, onset and alignment-defined outputs must be bitwise identical for a fixed program and runtime.
3. **Oracle-counterfactual:** independent bank API must not accept true onset, injection signal, simulated duration/shape, hidden label, or latent truth. Changing extra truth-looking fields at the low-level prototype's existing parameter boundary must not change its output; that separate P0.2 property is not by itself proof of source independence.
4. **Invalid and degenerate fixtures:** reject nonfinite measurements, nonfinite phi, malformed endpoints and missing dimensions. Exact-zero observed residuals produce an undefined hinge objective and fail-closed independent-bank score; do not compare this forced `-inf` with the current prototype's still-computed score.
5. **Near-parallel projection:** record the known numerical sensitivity as a separate adversarial diagnostic. Do not require both algebraically equivalent floating-point algorithms to have equal outputs in ill-conditioned cases, and do not select a winner post hoc.
6. **Complete geometry:** run at least one unlabelled one-curve check over all 99 frozen endpoints. This is a software enumeration test, never a scientific calibration or a detector benchmark.

## What this procedure cannot establish

This audit can establish fixture-level independence of code paths, reproducible regressions and known numeric disagreements. It cannot prove equality for all floating-point inputs, measure FPR, justify a threshold, predict compute cost for millions of calibrations, validate telescope data or authorize an experiment. Lean 4 checks only statements expressed in its mathematical models, not this NumPy implementation.

Evidence must be read back from the **exact** GitHub Actions commit. The original research archive and its protected checksum manifest are not altered. The scientific gate remains `NO_OPERATIONAL_VERDICT` for the historical M38B and `approved_for_calibration: false` for M38B-R.
