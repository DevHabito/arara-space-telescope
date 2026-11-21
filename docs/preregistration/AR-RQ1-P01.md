# AR-RQ1-P01 — A frozen synthetic calibration stress test

**Date:** 20 November 2026  
**Stage:** Prospective protocol only; implementation, execution and results must follow in separate commits.  
**Repository scope:** ARARA computational research archive. This is not a telescope or detector validation.

## Research question

Can correction from independent reference light curves reduce shared instrumental drift without removing a short event in a target light curve? Under which deliberately adverse conditions does that separation fail?

This is a bounded instructional and diagnostic test of established ideas. It is **not** a proposed new method, a reproduction of Kepler PDC, or a comparison with the full methods in the literature. In particular, the experiment does not implement the Bayesian cotrending of PDC-MAP, wavelet msMAP, Gaussian processes, ZOGY, or TRANSLIENT.

## Model and reproducibility contract

- Generator: Python 3.12 and NumPy 2.x; no external observations.
- Run 64 independent deterministic trial seeds `20261120 + i`, for `i=0,...,63`, with `numpy.random.default_rng`.
- Time grid: 256 integer epochs, `t=0,...,255`; each observation is a dimensionless, normalized flux deviation around 1.
- Reference stars: exactly 31, each with baseline 1. One separate target light curve is never included in reference estimators.
- Per-trial shared instrumental drift: `g(t)=0.018 sin(2*pi*t/96 + phase)+0.007*t/256`; draw `phase` uniformly in `[0,2*pi)`.
- Reference and target noise: independent zero-mean Gaussian draws, standard deviation `0.003` per point, with a fixed generation order (phase, reference-noise array, target-noise array, contaminated-reference indices).
- Event amplitude `-0.020`, exactly on epochs `128:136` (Python half-open slice). A paired no-event curve uses **identical** drift, noise, and instrumental artifacts. This pairing is for outcome evaluation only; the estimator must not see the paired oracle.
- Contaminated reference indices: sample 12 distinct integers from `0,...,30` for each trial, after noise generation, using the same seeded RNG. Contaminated sources receive an artificial `-0.040` change over `128:136`.

Three predeclared scenarios use the same trial draws:

1. **SHARED:** shared drift and independent noise; no additional artifact.
2. **REF_CONTAM:** SHARED plus a simultaneous negative excursion in 12 of the 31 reference sources.
3. **TARGET_ARTIFACT:** SHARED plus a `-0.020` instrumental excursion affecting **only the target** over the event window. For the negative control no astrophysical event exists, despite the apparent dip.

The TARGET_ARTIFACT condition deliberately makes an astronomical event and a source-specific instrumental dip observationally indistinguishable in this simplified model. It is an identifiability counterexample, not an expected capability of a telescope.

## Frozen estimators and measurement

Apply each estimator independently at each epoch, without time-domain smoothing or target fitting:

- `RAW`: corrected target = target - 1.
- `MEAN_REF`: corrected target = target - mean(reference fluxes).
- `MEDIAN_REF`: corrected target = target - median(reference fluxes).

The reference-only estimators never read target values to estimate drift. Their response to an injected additive target-only event should therefore be exactly linear in this generator. That property is a program sanity check, **not** an astrophysical discovery.

Compute the signed window contrast:

`D(z) = mean(z[128:136]) - (mean(z[104:112]) + mean(z[152:160]))/2`.

For each scenario, trial and estimator, report:

- `null_depth` = D(corrected target with no injected astrophysical event).
- `event_depth` = D(corrected target with the event).
- `retention` = (event_depth - null_depth)/(-0.020). The paired null curve is used here only for evaluation; never as a fitted correction.
- `median_abs_null` = median across 64 trials of `abs(null_depth)`.
- `false_dip_rate` = fraction of 64 **no-event** trials where `null_depth <= -0.010`.

No statistical p-values, confidence intervals or out-of-sample observational claims will be inferred from this finite synthetic seed set.

## Frozen decision gates

- **G1 (shared-drift benefit):** in SHARED, MEDIAN_REF `median_abs_null` is at most 50% of RAW.
- **G2 (reference-outlier resistance):** in REF_CONTAM, MEDIAN_REF `median_abs_null` is at most 40% of MEAN_REF.
- **G3 (identifiability failure):** in TARGET_ARTIFACT, MEDIAN_REF `false_dip_rate` is at least 90%. A successful G3 is evidence of a **failure mode**, not a useful detection capability.
- **G4 (paired-injection sanity):** for each estimator in each scenario the maximum absolute `retention - 1` over the 64 trials is at most `1e-10`.

Report PASS/FAIL against all gates even when contrary to expectations, and do not change the thresholds or trial seeds after inspecting outcomes. Save compact aggregate results as JSON including implementation version, NumPy version, and an SHA-256 digest of the canonical JSON output. If execution fails, preserve the failure and repair code separately from the frozen protocol.

## Interpretation limits

A fixed, known event time makes this a matched-window diagnostic, not a blind transient search. The reference-contamination scenario is contrived and tests a median's resistance to a minority of synchronous outliers; the experiment says nothing about general detector color effects, spacecraft systematics, domain shift, correlated noise, star variability, or physical telescope telemetry. Inferences cannot be transferred to ZOGY image subtraction or real observational false-positive rates.

If these synthetic gates pass, the next step is **not** a new-physics claim. It is a separate preregistered test including variable references, spatial or color-dependent drift, independent held-out event positions, realistic noise, and stronger standard baselines. No private correspondence or external association is documented here.

## Background sources

- Stumpe et al. (2012), *Kepler Presearch Data Conditioning I*, https://doi.org/10.1086/667698
- Smith et al. (2012), *Kepler Presearch Data Conditioning II*, https://doi.org/10.1086/667697
- Stumpe et al. (2014), *Multiscale Systematic Error Correction*, https://doi.org/10.1086/674989

The protocol documents a pre-existing methodological idea and its limitations. The researcher is responsible for interpretation and independent verification.
