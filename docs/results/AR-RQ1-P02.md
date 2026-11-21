# AR-RQ1-P02 — preliminary paired-observation and auxiliary-diagnostic result

**Date:** 20 November 2026  
**Scientific status:** preliminary **synthetic** result; the registered Python 3.12 run and repository-level CI must be reviewed separately.

## Frozen protocol and execution

The prospective protocol was committed before the generator and its results: [AR-RQ1-P02](../preregistration/AR-RQ1-P02.md), commit `2e4cb3d376fe2bf37302f9586f6bba0f222e8dbb`.

- Implementation: [scripts/ar_rq1_p02.py](../../scripts/ar_rq1_p02.py), version 1.0.0.
- Regression checks: [tests/test_ar_rq1_p02.py](../../tests/test_ar_rq1_p02.py), seven locally passing `unittest` cases.
- Local runtime: Python 3.13.5, NumPy 2.3.5.
- Seed range: `20261121` through `20261632`, 512 matched pairs.
- Archived raw aggregate: [AR-RQ1-P02-local-python313.json](AR-RQ1-P02-local-python313.json).
- Canonical payload SHA-256 (excluding the digest field): `fd8b7c0ed9ce933552297567cf89fbefde7e8c230ef4dc000c89fce2aaadbf79`.

All five frozen gates passed in this local execution. The Python 3.12 target environment remains to be checked; the numerical results must not be promoted to hosted verification on the basis of the local run.

## Why the photometry-only limit is exact

The experiment constructs a pair of physical explanations for every sample: an astrophysical dimming (A) or an equally shaped local instrument dip (I). Their target and reference flux arrays are **bytewise identical**.

If a classifier sees only the same photometric vector `x`, a deterministic rule `f(x)` must issue the same label for both members of a pair. With one A and one I example per pair, exactly **one** prediction can be correct. The balanced accuracy of any such deterministic photometry-only rule is therefore exactly 50% on this paired sample (the expected result is likewise 50% for a label-independent randomized rule). This is an elementary observation-equivalence argument, not an original theorem.

The fixed baseline classified every example as A and achieved `512/512` correct A, `0/512` correct I: 50% balanced accuracy. Class accuracy must be reported; overall accuracy alone conceals the fact that it rejected **no** instrumental artifact.

## Frozen auxiliary diagnostic: results

The diagnostic threshold is `x > 0.75 => I`. It is not fitted to the outcomes. The simulator stipulates the Gaussian score distributions; the observed advantage is therefore conditional on this stipulated information being present.

| Scenario | Correct A | Correct I | Balanced accuracy | Instrumental dips mistaken for A |
|---|---:|---:|---:|---:|
| ALIGNED | 405/512 | 410/512 | **79.59%** | 102/512 (19.92%) |
| UNINFORMATIVE | 251/512 | 273/512 | **51.17%** | 239/512 (46.68%) |
| INVERTED | 117/512 | 135/512 | **24.61%** | 377/512 (73.63%) |

The Gaussian analytic expectations given the fixed score distributions are about 77.34%, 50.00%, and 22.66% balanced accuracy respectively. The observed deviations stay within the registered tolerance of 0.06.

Frozen gates: `G1 PASS` (all 512 matched photometry/reference arrays identical, 50% photometry baseline), `G2 PASS` (aligned sensor), `G3 PASS` (uninformative sensor), `G4 PASS` (misleading inverted sensor), and `G5 PASS` (count and metric accounting).

## Interpretation and negative findings

This is **not** evidence that a physical spacecraft sensor can achieve 79.59% reliability. The diagnostic is a hypothetical Gaussian score constructed with class-dependent means. Under ALIGNED, its positive association with the instrumental explanation is assumed by the generator; under INVERTED, the opposite association is assumed. The experiment tests the logical consequences and sensitivity to that assumption.

The central result is methodological: when two explanations are photometrically indistinguishable, distinctions require a new independently informative measurement or justified prior information, not merely a more elaborate classifier acting on the same observations.

A second important lesson is negative: a sensor can lower reliability below the photometry-only baseline if its calibration or relationship to the target phenomenon changes. Such shifts must be identified and controlled before diagnostic fusion.

## What remains open

- No real detector pixels, centroid time series, temperatures, pointing telemetry, or astronomical labels have been used.
- This is a fixed-window, two-class synthetic diagnostic, not a blind event search.
- No model was trained and no out-of-domain performance was established.
- The score distributions were chosen to express known information regimes; this is an instructional identifiability test, not a discovered physical effect.
- The paired conditions intentionally make photometry identical. Real target-local disturbances and astrophysical events may leave distinguishable pixel-level signatures, but that cannot be assumed.
- The 512 pairs are controlled Monte Carlo examples, not a sample of independent astronomical sources.

## Next verification gate

Before making a stronger scientific claim, audit the provenance and semantics of a **real** independently observed diagnostic, ideally a public target-pixel dataset with quality flags and time-stamped pointing or centroid information. A new prospective protocol must define negative controls, source and instrument confounds, how the diagnostic was calibrated before seeing events, and whether a shift in calibration can be detected from held-out data.

For public methodological context see the [Kepler Data Processing Handbook](https://archive.stsci.edu/kepler/manuals/KSCI-19081-003-KDPH.pdf) and the [NASA TESS pipeline description](https://heasarc.gsfc.nasa.gov/docs/tess/data_pipeline.html). The public literature does not amount to external approval of this work.

**Research boundary:** no operational ARARA telescope, original algorithm, verified observational detector, or novel discovery is established by these synthetic results. No private correspondence or names of external correspondents have been included.
