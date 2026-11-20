# Research questions: separating astrophysical signals from measurement artifacts

**Date:** 20 November 2026  
**Record type:** Research reasoning and prospective questions; not an experiment, preregistration, validation, or collaboration record.

## Scope

An observed change may arise from the sky, the instrument, the image-processing pipeline, or several of these together. Removing noise is not sufficient: a correction can also remove the event we are trying to detect.

The current repository is a computational research archive. M37R simulator results and M38A structural eligibility do not establish astronomical detection performance; M38B calibration and holdout remain incomplete. See [Scientific Status](SCIENTIFIC_STATUS.md). Nothing in this note changes those claims.

## Q1 — Shared and non-shared instrumental changes

Repeated observations of reference sources may reveal systematic changes common to many stars, whereas an intrinsic change may be confined to a particular source. But common-mode separation is only a starting hypothesis. Instrument response can vary by detector region, source brightness, wavelength, color, and time; reference objects may themselves vary.

**Question:** under which departures from a shared response does calibration preserve an injected astrophysical event?

**Candidate controls:** constant sources under shared drift; one known transient plus shared drift; spatially dependent drift; color-dependent response; a contaminated set of variable reference stars; and events at the same timescale as drift.

**Measurements to predefine:** event-amplitude retention, completeness, false-positive rate, residual correlation, and uncertainty calibration. Reference selection and tuning must not use the final held-out outcomes.

## Q2 — Model flexibility and signal preservation

When instrument physics does not provide an adequate forward model, statistical surrogates such as Gaussian processes may represent residual trends and uncertainty. A flexible model may also explain away a real event.

**Question:** how does true-event recovery change with model flexibility, reference availability, and the similarity of instrumental and astrophysical timescales?

Compare simple detrending, common-mode methods, multiscale corrections, and a well-specified Gaussian-process baseline. Freeze hyperparameter-selection rules without inspecting the final test cases. Preserve failures and report uncertainty, not only detection scores.

## Q3 — False transients in image subtraction

Registration error, point-spread-function mismatch, source noise, astrometric effects, and correlated residuals may resemble a new source in a difference image. A significance score is trustworthy only to the extent that its noise and image-formation assumptions hold.

**Question:** which artifact classes survive an established image-subtraction baseline, and can independent motion-sensitive diagnostics distinguish them from stationary transient events?

Test blank fields, constant sources, injected stationary events, apparent source motion, registration offsets, PSF mismatch, multiple source flux levels, and correlated noise. Report artifact-specific false positives, completeness, position error, and confidence calibration. Do not use a deliberately weak comparator.

Atmospheric scintillation is a ground-observation mechanism. Any proposed transfer to a space instrument requires separate assumptions and evidence; ground-based artifacts are not automatically spacecraft artifacts.

## Q4 — Generalization beyond a simulated survey

A detection model may learn simulation or survey-specific characteristics rather than astronomical structure.

**Question:** do its conclusions survive held-out observing conditions, detector configurations, source populations, and noise distributions?

Use separate evaluation regimes, relevant negative controls, and subgroup error reports. Do not treat multiple correlated detections as independent examples.

## Experimental decision gate

1. Examine the established methods and document which assumptions apply.
2. Define the signal, noise mechanisms, measurement contract, baselines, and falsification threshold.
3. Freeze a new prospective protocol before evaluating test outcomes.
4. Start with reproducible synthetic cases and retain negative results.
5. Progress to independently obtained observational data only with provenance, permissions, and distribution-shift analysis.
6. Do not claim superior performance, operational telescope capability, originality, or independent validation based on this research note.

## Public literature: initial reading list

These are public works to study, not evidence of any external research relationship or approval of ARARA.

- Stumpe et al. (2012). *Kepler Presearch Data Conditioning I: Architecture and Algorithms for Error Correction in Kepler Light Curves*. https://doi.org/10.1086/667698
- Smith et al. (2012). *Kepler Presearch Data Conditioning II: A Bayesian Approach to Systematic Error Correction*. https://doi.org/10.1086/667697
- Stumpe et al. (2014). *Multiscale Systematic Error Correction via Wavelet-Based Bandsplitting in Kepler Data*. https://doi.org/10.1086/674989
- Zackay, Ofek, and Gal-Yam (2016). *Proper Image Subtraction: Optimal Transient Detection, Photometry, and Hypothesis Testing*. https://doi.org/10.3847/0004-637X/830/1/27
- Springer et al. (2024). *TRANSLIENT: Detecting Transients Resulting from Point Source Motion or Astrometric Errors*. https://arxiv.org/abs/2403.09771

**Status:** no new simulations, observational tests, algorithm validation, or performance comparisons were conducted for this note. It records directions to investigate, not findings.
