# AR-RQ1-P01 — preliminary synthetic benchmark report

**Date:** 20 November 2026  
**Status:** Local synthetic execution recorded; protocol-runtime verification pending.  
**Protocol frozen before implementation:** [AR-RQ1-P01](../preregistration/AR-RQ1-P01.md), commit `d0bf8fae076f6aaa05b3839eb58a6fff7e361701`.  
**Implementation:** [scripts/ar_rq1_p01.py](../../scripts/ar_rq1_p01.py), version 1.0.1.  
**Regression checks:** 12 passed locally with pytest; see [tests/test_ar_rq1_p01.py](../../tests/test_ar_rq1_p01.py).  
**Archived result:** [AR-RQ1-P01-local-python313.json](AR-RQ1-P01-local-python313.json).

## Execution and provenance

The local run used Python **3.13.5**, NumPy **2.3.5**, 64 declared seeded trials per scenario (`20261120,...,20261183`), 31 reference curves, 256 epochs, and a fixed event window. The prespecified environment is Python **3.12** and NumPy 2.x. As a result, the numbers below are **preliminary until the Python 3.12 run has been independently checked**. The branch CI workflow has been configured to execute the suite and benchmark on Python 3.12, but no claim of a passing hosted run is made here.

The local result JSON records the SHA-256 digest of the canonical *payload without the digest field*: `32d2adcb0a5d8104d43487e77b337046af34fa8e52ef9cf90d7ec6072c9a64b8`. The Python and NumPy versions are part of the hashed payload.

This is a deliberately small **matched-window** simulation. It is not blind source discovery, observational validation, a physical telescope model, or an implementation of the full PDC, ZOGY or TRANSLIENT methods.

## Results

The primary quantity `median_abs_null` is the median absolute **no-event** signed-window contrast across 64 paired synthetic trials. Smaller values mean less apparent event-like contrast when there is no astronomical event. The fixed one-sided false-dip threshold is `-0.010`.

| Scenario | RAW | MEAN_REF | MEDIAN_REF |
|---|---:|---:|---:|
| SHARED: median absolute null contrast | 0.011400615 | 0.000902561 | 0.000906193 |
| REF_CONTAM: median absolute null contrast | 0.011400615 | 0.015668013 | 0.002826700 |
| TARGET_ARTIFACT: median absolute null contrast | 0.016753193 | 0.019815858 | 0.019847707 |
| TARGET_ARTIFACT: false-dip rate | 41/64 (64.06%) | 64/64 (100%) | 64/64 (100%) |

All four gates reported `PASS` in this Python 3.13 local run:

- **G1:** MEDIAN_REF shared-drift null contrast was 7.95% of RAW, below the predeclared 50% bound.
- **G2:** With 12 synchronously contaminated references, MEDIAN_REF contrast was 18.04% of MEAN_REF, below the predeclared 40% bound.
- **G3:** Target-local instrumental dips were falsely identified as dimming candidates in all 64 no-event cases after MEDIAN_REF correction, satisfying the predeclared **failure-mode** threshold of at least 90%.
- **G4:** The maximum paired-injection retention error, rounded to 12 decimals, was 0.0 for every method and scenario. This result is primarily an algebraic sanity check: subtracting a reference-only estimate cannot remove an additive target-only injection if calibration does not use the target. It is not an independently demonstrated property of real photometry.

The results show expected behavior of basic arithmetic estimators under explicitly constructed conditions. They do not demonstrate that MEDIAN_REF outperforms PDC-MAP, Gaussian-process detrending, or any real astronomical pipeline.

## Scientific interpretation

A reference-based estimator can remove a shared temporal trend in this simple additive model. A median resists the chosen minority of contaminated reference curves better than the mean.

The more consequential finding is a limitation: if an unobserved target-specific instrument artifact has exactly the same time profile as a potential astrophysical dip, then the target and reference observations can be the same under two incompatible explanations:

- Real astrophysical dip, no target-specific artifact.
- No astrophysical dip, an identical target-specific instrumental artifact.

Without additional information, the two explanations are not identifiable from these light curves alone. This is an elementary observational equivalence, not a novel theorem, and it cannot be solved by tuning the same reference-only correction more aggressively.

## What has not been established

- No real or independent survey images or light curves have been analyzed.
- No search over unknown event times has been tested.
- The 64 trials are chosen synthetic seeds; three scenarios reuse their random draws and are not 192 independent astronomical observations.
- Noise is independent, additive Gaussian in this toy model. Detector physics, photon-counting, heteroscedastic errors, PSF mismatch, spatial/color effects, and reference-star astrophysical variability remain outside this run.
- No new detection algorithm or improvement over the scientific state of the art has been established.
- Hosted Python 3.12 verification, full repository test-suite status, and any external independent replication are not yet confirmed.

## Next distinct prospective gate

A new, separately frozen protocol should test changing event positions, source- and detector-dependent drifts, heteroscedastic or temporally correlated noise, and a predeclared stronger reference baseline. Real Kepler/TESS photometry or independent image-subtraction observations would require a separate source/data audit before use.

The practical methodological requirement is to identify at least one **independent observable** that could distinguish a target-local instrument artifact from an astrophysical event. More complex modeling of the same insufficient observations may improve a score but cannot resolve exact observational equivalence.

## References and scope

For established Kepler conditioning methods, see Stumpe et al. (2012), Smith et al. (2012), and Stumpe et al. (2014), cited in the frozen protocol. These references motivate a problem already recognized in the literature; they are not endorsements or validations of this experiment. No private communications have been quoted or identified here.
