# AR-OBS006-P01 — chronological holdout of engineering-to-pixel photocenter prediction

**Recorded:** 20 November 2026 (America/Sao_Paulo).  
**Evidence type:** Direct analysis of **real archived TESS data**, with a predetermined linear model and a chronological holdout. This is a **within-sector predictive association**, not a physical-event detection, causal inference or independent telescope validation.

**Preregistered before inspecting the AR-OBS006 outcomes:** [AR-OBS006-P01](../preregistration/AR-OBS006-P01.md), commit `84244f1eb28ee0e6a902a0e9d9847a92906b8a28`.  
**Implementation:** [scripts/ar_obs006_quaternion_holdout.py](../../scripts/ar_obs006_quaternion_holdout.py).  
**Ten synthetic regression tests:** [tests/test_ar_obs006_quaternion_holdout.py](../../tests/test_ar_obs006_quaternion_holdout.py), all **PASS** on Python 3.12.16.  
**Original execution:** [GitHub Actions run #44853140664](https://github.com/DevHabito/arara-space-telescope/actions/runs/44853140664), artifact [#14685389828](https://github.com/DevHabito/arara-space-telescope/actions/runs/44853140664/artifacts/14685389828).  
**Permanent original numerical report:** [AR-OBS006-P01.json](AR-OBS006-P01.json).

## Sources and verification

The experiment uses **exactly** the three previously audited TESS Sector 5 / TIC 307210830 / Camera 4 products and preserves their original checksums:

| Input | SHA-256 | Bytes |
|---|---|---:|
| SPOC Target Pixel File `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits` | `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b` | 46,414,080 |
| SPOC light curve `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits` | `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae` | 1,923,840 |
| TESSVectors `TessVectors_S005_C4_120.csv` | `2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8` | 9,386,675 |

The FITS files were accessed from STScI and the vectors from NASA HEASARC; no raw source, images, engineering time series or per-cadence results were committed.

The hosted run used **Python 3.12.16**, **NumPy 2.5.5**, **Astropy 7.2.4**. The SHA-256 of the canonical original result payload (excluding its self-digest field) is `7661b50f87b96c27b5f7c65017d500bb431965ff0bd7db3d594fb4dd68eab050`. This digest was recomputed independently from the downloaded workflow artifact and matched. All five G1–G5 integrity gates passed.

## Eligibility and immutable chronological split

The positive-weight TPF photocenter used only **21 optimal-aperture pixels**. The three fixed predictors were first differences of `Quat1_Med`, `Quat2_Med` and `Quat3_Med`. Both differences were computed across consecutive **integer cadence IDs**, with complete positive-flux photocenters, finite times, quality-zero TPF and LC rows, and usable engineering quaternions. No event selection, outlier clipping or data-dependent feature choice was applied.

| Population | Count |
|---|---:|
| TPF/LC source cadences | 18,944 |
| Matched TESSVectors cadences | 17,971 |
| Individual eligible cadences | 17,025 |
| Consecutive eligible cadence pairs | **16,925** |
| Training pairs, first 60% | **10,155** |
| Untouched chronological test pairs, final 40% | **6,770** |
| Ineligible or nonconsecutive adjacent source-row pairs | 2,018 |

Exclusion tallies **overlap** and must not be summed as disjoint groups. The source includes 1,919 nonzero-quality rows; 973 missing engineering rows, 973 nonfinite LC and TPF times, and one unusable engineering-quaternion row among matched rows. `QUALITY=0` selection excludes many explicitly flagged instrumental intervals, so these results cannot describe behavior precisely during the most problematic events.

### Method and baselines

Training-only standardized engineering predictors were fitted by a fixed three-feature ridge regression (`lambda=10`) to two simultaneous first-difference outcomes: local pixel-photocenter steps `dc_x,dc_y`. The baseline was the **constant training-mean displacement**. A separate negative control used the same model with predictor rows cyclically shifted by 97 positions **within each of the train and holdout blocks**. No holdout outcome was used in fitting.

Importantly, the test's features describe **the same contemporaneous cadence transition** as the outcomes. This is a held-out explanatory prediction, **not a causal or operational forecast of future pointing before engineering measurements exist**.

## Frozen outcome results

The predeclared measure `R2 = 1 - SSE_model/SSE_constant_baseline` was evaluated solely on the final 6,770 chronological pairs. Negative scores are preserved.

| Held-out measure | X photocenter | Y photocenter |
|---|---:|---:|
| `R2_ridge` | **0.335352** | **0.273929** |
| `R2_shift97` | **−0.001879** | **−0.002071** |
| Baseline mean absolute error, pixels | 0.00360354 | 0.00495411 |
| Ridge mean absolute error, pixels | **0.00296555** | **0.00428833** |
| Shift-control mean absolute error, pixels | 0.00360712 | 0.00496258 |
| Baseline sum of squared error | 0.14554950 | 0.28457555 |
| Ridge sum of squared error | 0.09673920 | 0.20662201 |
| Shift-control sum of squared error | 0.14582304 | 0.28516485 |

Relative to the constant baseline, the frozen ridge model reduced held-out mean absolute displacement error by approximately **17.7% on X** and **13.4% on Y**. It surpassed the fixed shifted-data comparison on both axes.

The hypothesis decisions were, exactly as registered:

- **H1 X holdout association — SUPPORTED_IN_SELECTED_PRODUCTS**: R² exceeds 0.10 and improves over the shifted control by more than 0.05.
- **H2 Y holdout association — SUPPORTED_IN_SELECTED_PRODUCTS**: same thresholds.
- **H3 limited shifted-control specificity — SUPPORTED_IN_SELECTED_PRODUCTS**: shifted R² was at most 0.05 in both axes.

The unit tests include deliberately uninformative predictors, chronological split-size failure, missing engineering data, unequal LC/TPF quality flags, out-of-order source rows and constant predictors. They establish internal code behavior, not astrophysical validity.

## Scientific and computational limitations

This result is **not a new physical law**, novel pointing algorithm, detector performance measurement, or reliable classification of an astronomy-versus-instrument candidate. The existing TESS literature already recognizes that pointing jitter and fine guidance depend on science-camera information. Predictability here can arise from **shared physical and processing provenance**, not independent corroboration.

The experiment must be interpreted under all of these limitations:

1. **One target, one camera, one sector.** There is no cross-sector, cross-star, cross-CCD, or different instrument evaluation. Chronological separation is not distributional independence.
2. **Contemporaneous predictors.** The model uses quaternion changes occurring during the target displacement interval. It does not predict future behavior from prior telemetry alone.
3. **A deliberately weak constant baseline.** Beating the training mean does not establish superiority over autoregressive pointing models, a simple per-axis persistence baseline, SPOC `POS_CORR`, physically calibrated quaternion-to-pixel transformations or established detrending methods.
4. **Dependence and temporal autocorrelation.** The 97-position circular shift is a single sanity check, not a null distribution or statistical significance test. Consecutive differences remain dependent, and adjacent training/test **pairs may share one boundary cadence**, even though no test labels were used to fit the model. A new study should apply a preregistered temporal embargo at split boundaries.
5. **Selection bias.** Only `QUALITY=0` and fully measured engineering/pixel cadences are used. Detector or spacecraft faults can disproportionately fall outside this sample.
6. **Reprocessing and pointing history.** Official [Sector 5 notes](https://heasarc.gsfc.nasa.gov/docs/tess/sector5_summary.html) document a guiding configuration change near the end of the sector and subsequent reprocessing of timestamp and calibration products. No stratification around that incident was attempted here; it could influence a chronological holdout.
7. **No event truth labels.** Neither quaternion availability, FITS `QUALITY` flags nor a photometric centroid drift proves whether an observed source variation is astrophysical.

The result is valuable as a reproducible within-sector demonstration that a simple, frozen relationship between quaternion median changes and measured photocenter movement survives a chronological holdout. It does **not** close the earlier M38B observational calibration and independent holdout limitations.

## Next prospective scientific gate

A genuinely stronger experiment should freeze **before evaluation**: an embargo between training and test blocks; multiple unrelated TESS stars and sectors; a time-series or physics-based pointing baseline; comparison of same-camera and other-camera quaternion information with an explicit shared-source causal diagram; and quality-flagged intervals where enough measurements exist. Only independently documented physical-event provenance could justify a fault-versus-astronomy classification protocol.

No private correspondence, names of scientific contacts, or claims of external collaboration appear here.

## Public-method context

- [TESSVectors public processing and data semantics](https://github.com/tessgi/tessvectors).
- [NASA TESS fine-pointing and science-camera guidance](https://heasarc.gsfc.nasa.gov/docs/tess/telescope_information.html).
- [NASA TESS Sector 5 notes and reprocessing information](https://heasarc.gsfc.nasa.gov/docs/tess/sector5_summary.html).
