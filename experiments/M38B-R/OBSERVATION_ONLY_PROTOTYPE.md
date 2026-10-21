# Observation-only candidate prototype — mathematical and execution boundary

**Status:** Experimental software prototype; no scientific outcome, no recalibration, no calibrated threshold, no operational verdict. Do not merge this code into the archived milestone tree.

## Scientific question

Can the fixed latent-grid candidate be scored without receiving any simulated true onset, duration, shape, latent parameter, or injected signal?

The historical `score_latent_grid_bank` uses `absolute_source = positions + true_onset` to mask its raw confirmation templates. The difference is causally inappropriate for an operational candidate, and a frozen-observation counterfactual changed the historical score from `4.419417382415921` to `0.0` solely by changing the hidden onset.

## Candidate function

`observable_candidate.score_observation_only(residual, processed_reference, params, cfg)`

The public inputs contain only the residual and reference after observed-data preprocessing, the estimated residual AR(1) coefficient, and a frozen configuration. The causal anchor comes from the archived residual-based estimator. A nine-sample raw template is formed at measured times `endpoint-8 ... endpoint`, from which eight AR(1) differences are scored. All endpoints are validated against the observed time span **before** scoring. No true-onset-dependent source mask is used.

The implementation retains the four archived template families, 37 durations, and five latent points. It reuses the archived causal onset estimator, window extraction, and reference projection as dependencies. It therefore does **not** constitute an independent reimplementation of the entire detector, nor does it establish that those dependencies are free of all observational leakage.

## Expected validation behavior

- Match archived candidate scores in fixtures where the historical mask is all valid, modulo floating-point tolerance.
- Differ from the archived candidate where the true onset changes the historical mask.
- Reject malformed/nonfinite observations and invalid endpoint windows.
- Produce a score grid when the genuine residual-based onset estimator is used.
- Require a prospective calibration and holdout design **even if all tests pass**.

## Anti-leakage boundary and threats

The candidate accepts no explicit hidden truth parameters. This is a necessary, not sufficient, condition: upstream `residual`, `processed_reference`, `params`, or `cfg` may still be contaminated if prepared using hidden truth. The archived `sbw_with_reference_nuisance` function accepts `raw_signal` but its returned residual and reference computations appear not to use that parameter; this needs a separate dataflow audit, not a presumption.

The policy that every measured window is valid changes the historical M38B candidate statistic at late endpoints. **Historical M37R/M38B thresholds, sample gates, projected energy, or recall cannot be transferred to this method.** A corrected and frozen prospective experiment is required.

## Engineering checks

`python -m unittest discover -s tests -p "test_m38br_observable.py" -v`

The corresponding GitHub Actions workflow runs on a clean cloud runner. Lean 4 checks only the discrete boundary policy; it does not prove this NumPy code.

## Current decision

M38B-R remains `approved_for_calibration: false`. The implementation is a hypothesis to be falsified, not a scientific result.

Further work: independent score implementation, preprocessing invariance, property-based stress tests, resource benchmarking, and immutable separate preregistration before calibration.
