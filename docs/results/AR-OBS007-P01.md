# AR-OBS007-P01 — Incremental quaternion information beyond recent pixel motion

**Recorded:** 21 November 2026 (America/Sao_Paulo).  
**Status:** Completed single-target observational benchmark; *not* an astrophysical classification experiment or independent instrument validation.  
**Preregistered protocol:** [AR-OBS007-P01](../preregistration/AR-OBS007-P01.md), frozen in commit `3856e8cf0091c5f0cd741f0ec9c34608b9175dfd`, **before** implementation or inspection of outcomes.  
**Executed source:** [GitHub Actions run #44901558890](https://github.com/DevHabito/arara-space-telescope/actions/runs/44901558890), 10 unit tests and five integrity gates passed; [original JSON artifact #14706425783](https://github.com/DevHabito/arara-space-telescope/actions/runs/44901558890/artifacts/14706425783).  
**Permanent output:** [AR-OBS007-P01.json](AR-OBS007-P01.json).  
**Implementation:** [scripts/ar_obs007_incremental_telemetry.py](../../scripts/ar_obs007_incremental_telemetry.py).  

## Why this benchmark is different from AR-OBS006

AR-OBS006 showed that a fixed three-feature quaternion ridge model explained a nonzero fraction of contemporaneous photocenter displacement relative to a **constant mean** prediction. That comparison was too weak to show the telemetry adds information beyond the measured image-motion history.

Here, the predeclared comparator knows the **two immediately preceding valid 2-minute photocenter displacement vectors**. The candidate adds three same-interval quaternion differences. Each model is fitted only on the training block and judged on identical, withheld chronological observations.

The comparison addresses a narrow necessary condition for instrumental diagnostics: **whether engineering data add predictive information beyond target-image movement**. It does not classify an event as astrophysical or instrumental.

## Sources, masks and held-out sample

The inputs are the exact same TESS Sector 5 / L 98-59 products pinned by SHA-256 in AR-OBS006: the MAST SPOC 11×11 TPF, SPOC LC and NASA HEASARC 120-second camera-4 TESSVectors CSV. Their original SHA-256s and byte counts are retained in the permanent JSON.

| Predeclared population | Count |
|---|---:|
| Original TPF/LC cadences | 18,944 |
| Engineering vectors with matching cadence identifiers | 17,971 |
| Individually eligible, quality-zero cadences | 17,025 |
| Eligible consecutive displacement pairs | 16,925 |
| Motion examples with two uninterrupted previous displacement pairs | **16,761** |
| Training examples, chronologically first | **9,936** |
| Embargoed examples around the split | **240** |
| Untouched test examples, chronologically last | **6,585** |

The final training example ends at cadence **163149** and the first test example at **163390**. The embargo prevents directly adjacent source cadences crossing the split; it is not a proof of full statistical independence.

Every model uses training-only feature scaling, the same ridge penalty (λ=10) and the same two output axes. The fixed shifted-quaternion control rotates quaternion rows 97 positions inside *each separate block*, without moving AR lag features or using test labels for fitting. This is only a sanity control and does not constitute a statistical null distribution.

## Observational verdicts

| Unseen-test score | X axis | Y axis |
|---|---:|---:|
| R² for AR2 motion baseline vs constant mean | 0.528070 | 0.523476 |
| R² for quaternion-only model vs mean | 0.339531 | 0.283643 |
| R² for **AR2 + quaternions** vs mean | **0.602247** | **0.574308** |
| Held-out AR2 sum of squared error | 0.0668310 | 0.1312083 |
| Held-out AR2+Q sum of squared error | **0.0563267** | **0.1172121** |
| **Incremental SSE gain over AR2** | **+15.7177%** | **+10.6672%** |
| Shifted-Q incremental SSE gain over AR2 | −0.6304% | −0.6733% |
| AR2 mean absolute error (pixels) | 0.0024744 | 0.0034164 |
| AR2+Q mean absolute error (pixels) | **0.0022984** | **0.0032746** |

The predeclared H1 and H2 required **at least 5% reduction of squared error beyond AR2** and a margin of at least 3 percentage points over the shifted telemetry control. **Both were supported in this selected sector.** The predeclared H3 required the shifted control not to improve either axis by more than 2%; this was also supported (it worsened both).

The authoritative original JSON payload has SHA-256 `b73a826b3ff9da673914044ae7a7201311476466e2ec400020c78dd79cbbcdfa`. The workflow artifact was downloaded and this canonical SHA-256 independently recalculated. All five G1–G5 gates passed. Failure cases and no-information conditions are tested by the included synthetic regression suite.

## Interpretation and novelty boundary

This provides **stronger observational evidence for incremental descriptive information from quaternions** than AR-OBS006: the features improved upon a model that already used recent target-image movement. The improvement is a held-out result with a frozen comparison, not a post hoc selected statistic.

Still, it does **not** establish a scientifically new method. Existing [QLP documentation (2022)](https://arxiv.org/abs/2211.04387) already describes quaternion-assisted TESS detrending. Existing [EVEREST / Luger et al. (2016)](https://doi.org/10.3847/0004-6256/152/4/100) explores instrument-noise removal and transit injection/recovery, and NASA provides [PLD methods](https://heasarc.gsfc.nasa.gov/docs/tess/NoiseRemovalv2.html).

Especially important limitations:

- These outcomes are **pixel photocenter changes**, not photometric errors, planet/transient detections or recovered transit depths.
- Engineering features are **contemporaneous**. The model does not predict a new pointing displacement before the engineering measurements occur.
- TESS guide stars may contribute to attitude measurements, so the two measurements can share physical and processing provenance.
- This is **one star, one sector, one CCD** and a quality-zero subset. It has not been tested across targets, sectors, pointing changes, flares or corrupted intervals.
- AR2 uses only two prior motion vectors. We did not benchmark against a production TESS pipeline, a state-space model, a nonlinear autoregressive predictor, or a physically calibrated attitude-to-pixel transformation.
- The holdout and embargo reduce direct contamination; they do not eliminate time correlation or sector-specific transfer issues.
- The 97-example circular shift is one control, not a null distribution or a statistically calibrated test.
- We have **not measured whether a photometric correction using these features preserves injected astrophysical transits**. A separate frozen experiment, AR-OBS007-P02, must address this before discussing scientific usefulness as a light-curve corrector.
- Neither the result nor the archived M38B synthetic experiments constitute a validated real-world fault classifier.

**Research direction:** Continue with an injection/recovery *necessary-condition* benchmark comparing a known pixel-based baseline with and without quaternion covariates, preserving both positive and negative outcomes; only subsequently introduce genuine, externally documented physical-event labels to test origin discrimination.

No private email correspondence, names of contacts, or implied collaborations appear here.
