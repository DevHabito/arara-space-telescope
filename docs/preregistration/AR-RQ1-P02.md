# AR-RQ1-P02 — Does an independent diagnostic resolve a photometric ambiguity?

**Registered:** 20 November 2026  
**Status:** Prospective protocol; implementation and outcomes are not part of this commit.  
**Relationship:** Follow-up question to AR-RQ1-P01, independently defined and not a validation of a telescope.

## Question

When an instrumental dip and an astrophysical dimming have identical observed light curves, can an **independently measured**, imperfect auxiliary diagnostic help distinguish them? What happens when the diagnostic becomes non-informative or its relationship to the event changes?

This experiment tests an elementary identifiability principle under a declared probabilistic model. It is not a novel astronomical detection technique, a simulator of physical spacecraft telemetry, or a replacement for established image- and pixel-level validation.

## Fixed observational experiment

Generate 512 **paired examples**, indexed `i=0..511`, with NumPy `default_rng(20261121+i)`. Each pair contains two possible explanations, A and I, with exactly the **same observed photometry**, reference-star observations, and sampled noise:

- **A (astrophysical):** a real `-0.020` dimming over epochs `128:136`.
- **I (instrumental):** no astrophysical event, but a target-local instrument artifact of `-0.020` over the same epochs.

In both cases, the measured target samples are exactly equal; the physical labels are different. No method receiving only these samples and the common references can distinguish the pair. This is a construction, not an inference from real data.

Each pair has 256 epochs `t=0..255`, 31 reference stars, baseline flux 1 and dimensionless deviations:

`g(t) = 0.018 sin(2*pi*t/96 + phase) + 0.007*t/256`,

where `phase ~ Uniform(0,2*pi)`. Draw the 31-by-256 reference noise array and a 256-point target noise vector independently from `Normal(0,0.003)`. References are `1+g(t)+reference_noise`; the measured target under *both* labels is `1+g(t)+target_noise-0.020*1_[128:136](t)`.

After generating the flux data, draw **two independent standard-normal values** `z_A` and `z_I` from that pair's RNG. Reuse those same draws across the three scenarios below, changing only their means. This deliberately pairs scenario comparisons; do not interpret all scenario outcomes as independent experimental samples.

A hypothetical external diagnostic `x` is defined as:

| Scenario | A: x | I: x |
|---|---|---|
| ALIGNED | `0 + z_A` | `1.5 + z_I` |
| UNINFORMATIVE | `0.75 + z_A` | `0.75 + z_I` |
| INVERTED | `1.5 + z_A` | `0 + z_I` |

The standard deviation is always 1. The diagnostic distribution is imposed by the simulator. We do **not** assume that any real spacecraft sensor has this behavior.

## Frozen decision rules

1. **Photometry-only baseline:** subtract the epochwise median of the 31 reference fluxes, then compute
   `D(z)=mean(z[128:136])-(mean(z[104:112])+mean(z[152:160]))/2`.
   Predict label **I** if `D(z)>-0.010`, otherwise predict **A**. The rule is deliberately fixed and has no access to the diagnostic. Since each pair has identical photometry across labels, the balanced accuracy must be exactly 0.5, irrespective of the threshold.
2. **Independent-diagnostic rule:** predict label **I** iff `x > 0.75`; otherwise predict **A**. No fitting, feature selection, or threshold optimization is permitted. Apply the *same threshold* to all three scenarios.

No final-test outcomes will be used to tune either rule.

## Outcomes and predefined gates

There are 512 A and 512 I examples per scenario, with shared flux curves within each pair. Report the following for each rule and scenario:

- `astro_retention`: fraction of A correctly classified A.
- `artifact_rejection`: fraction of I correctly classified I.
- `balanced_accuracy = (astro_retention + artifact_rejection)/2`.
- `artifact_miss_rate = 1 - artifact_rejection`, the fraction of instrumental events mistaken for astronomy.
- Counts, not only percentages; also the number of pairs whose photometric observations are bytewise identical.

The known Gaussian reference for a correctly specified ALIGNED sensor with midpoint threshold 0.75 is `Phi(0.75)` (approximately 0.7734), where `Phi` is the standard-normal CDF. UNINFORMATIVE is 0.5 and INVERTED is `1-Phi(0.75)` (approximately 0.2266). Finite samples may deviate.

The gates are frozen now:

- **G1:** all 512 paired flux curves and 31-star reference matrices match exactly between A and I; photometry-only balanced accuracy is exactly 0.5 in every scenario.
- **G2:** ALIGNED diagnostic balanced accuracy >= 0.70 and within 0.06 of `Phi(0.75)`.
- **G3:** UNINFORMATIVE diagnostic balanced accuracy within 0.06 of 0.5.
- **G4:** INVERTED diagnostic balanced accuracy <= 0.33 and within 0.06 of `1-Phi(0.75)`.
- **G5:** every reported count is an integer between 0 and 512, the A/I sample counts remain balanced, and the four metrics agree with the archived counts to numerical tolerance `1e-12`.

A PASS on G4 records failure under a miscalibrated sensor; it is **not** a successful detection result. All gates must be reported even if contrary to expectation.

## Reproducibility and stop conditions

- Target runtime: Python 3.12, NumPy 2.x. A different local interpreter may be used for preliminary debugging only, identified explicitly.
- Implementation and regression tests must be committed after this file.
- Record a deterministic JSON output with seed range, software versions, aggregate confusion counts and SHA-256 of the canonical payload excluding the digest field.
- Do not silently change means, threshold, number of examples, feature formula or failure gates after inspecting results.
- Do not infer a significance level, a confidence claim about astrophysical populations, or performance of real telemetry from simulator outcomes.
- The demonstrated diagnostic advantage is **built into the conditional distributions**. It illustrates a prerequisite for identification, not evidence that a specific new sensor will provide such information.

## Scientific limitations

This protocol gives the competing physical explanations identical flux data by design. Neither an event-time search nor a probabilistic model of real spacecraft instrumental anomalies is evaluated. Telemetry values are synthetic Gaussian scores with stipulated label-dependent means; they are **not measured** motion, housekeeping, detector, or pixel data. In real applications the calibration itself can shift, diagnostic measurements may be correlated with the flux error, and astrophysical signals may affect some diagnostics.

For relevant established practice, consult the Kepler data processing handbook and TESS target-pixel and validation documentation rather than presenting this experiment as novel:
- NASA, *Kepler Data Processing Handbook*, https://archive.stsci.edu/kepler/manuals/KSCI-19081-003-KDPH.pdf
- NASA TESS data products and pipeline, https://heasarc.gsfc.nasa.gov/docs/tess/data_pipeline.html

**Evidence status at registration:** no outcomes, validations or observations from AR-RQ1-P02 have been examined.
