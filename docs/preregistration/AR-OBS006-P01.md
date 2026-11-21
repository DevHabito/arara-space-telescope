# AR-OBS006-P01 — Held-out prediction of pixel photocenter motion from engineering quaternions

**Registered:** 20 November 2026 (America/Sao_Paulo).  
**Status:** Prospective protocol. No AR-OBS006 source values, model fits or outcomes have been inspected before this commit.  
**Scope:** A strictly bounded **within-sector predictive association** test, not astrophysical detection, fault classification, or proof of an independent sensor.

## Scientific question

Can *changes in camera-level pointing quaternions*, recorded in a separately distributed engineering product, predict **consecutive-cadence shifts of the positive-weight pixel photocenter** in an untouched chronological holdout? Does that prediction exceed both a fixed baseline and a deliberately time-misaligned predictor?

Because TESS's camera-derived guide-star measurements help control spacecraft attitude, engineering quaternion estimates and science-image photocenter shifts may share upstream information. A success would show within-product predictive consistency, **not causal identification or independent astrophysical evidence**.

## Frozen source and reproducibility

Use only three previously audited products for TIC 307210830 (L 98-59), TESS Sector 5, Camera 4, CCD 4:

1. SPOC target pixels: `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits`, SHA-256 `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b`.
2. SPOC light curve: `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`, SHA-256 `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
3. TESSVectors 120-second camera-level engineering CSV: `TessVectors_S005_C4_120.csv`, SHA-256 `2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8`.

The files originate from the frozen STScI/HEASARC URLs and bounded download helpers defined in AR-OBS003 and AR-OBS005. Read temporary copies with Python 3.12, NumPy 2.x and Astropy 6/7. Require original hashes, noncontradictory target/sector/camera/CCD headers where supplied, unique exact integer cadence keys and the same TPF-LC cadence/quality alignment as AR-OBS003. The TESSVectors CSV has no independent `Sector`/`Camera` row fields; its provenance follows the source URL, file name and digest.

No other target, sector, vectors, camera, aperture, background subtraction, source release or reference cadence is allowed. Do not commit raw FITS, CSV, feature arrays or target time series.

## Frozen outcomes, features and eligibility

**Outcomes:** on each TPF cadence, use calibrated TPF `FLUX` inside the documented optimal aperture `APERTURE & 2 != 0`. Require all selected pixels finite, use nonnegative weights `w=max(FLUX,0)`, and require `sum(w)>0`. Compute local image photocenters
`cx=sum(w*x)/sum(w)` and `cy=sum(w*y)/sum(w)`,
with local integer pixel coordinates. These are not exact SPOC `MOM_CENTR` outputs.

**Engineering features:** the archived `Quat1_Med`, `Quat2_Med`, `Quat3_Med` from TESSVectors, not fitted from the target flux. `Quat4_Med` is omitted in advance; these components are treated as numerical predictors, not converted into physical displacement units or a derived spacecraft attitude solution.

Join TPF, LC and vector rows on exact integer `CADENCENO`/`Cadence`; reject duplicate keys. At an individual cadence, require:
- `QUALITY=0` in the TPF and matched LC;
- finite TPF `TIME`, finite vector `MidTime` and finite LC `TIME`;
- TESSVectors `Quat_NBinned>0` and all four `Quat[1-4]_StdDev` finite and nonnegative;
- all three selected quaternion medians finite;
- a valid pixel photocenter as above.

Order TPF cadences numerically. A pair is eligible only if **two successive ordered TPF cadence IDs differ by exactly one** and both rows are individually eligible. Define outcome
`Y=(cx[t]-cx[t-1], cy[t]-cy[t-1])`,
and predictor
`X=(Q1_Med[t]-Q1_Med[t-1], Q2_Med[t]-Q2_Med[t-1], Q3_Med[t]-Q3_Med[t-1])`.
No smoothing, detrending, outlier removal, flux regression, or event selection is allowed.

Report total and matched cadences, individual eligible rows, eligible consecutive pairs, and exclusions by missing fields or quality. An eligibility rule may preferentially remove problematic pointing intervals; this must be stated as a selection limitation.

## Train/holdout and fixed model

Chronologically order the eligible pairs by their later `CADENCENO`. The **first 60%** (integer floor) are the training block; the **last 40%** are the untouched test block. Do **not** shuffle or cross-validate over the holdout.

For each X component, subtract its training mean and divide by its training population standard deviation; any exactly zero-variance training feature is set to zero (and the zero training standard deviation is reported). Apply these training parameters unchanged to the holdout.

Use a fixed multi-output **ridge linear model** with:
- an unpenalized intercept equal to the two-component training outcome mean;
- centered X and centered Y in the fit;
- fixed penalty `lambda = 10.0` on the three slope coefficients;
- the analytic NumPy linear solve, no optimizer tuning.

**Baseline:** predict the constant training mean `(mean(dc_x),mean(dc_y))` on each test pair. This is intentionally a simple baseline, not an established high-performance pointing model.

**Time-shift negative control:** independently circularly shift **training X by +97 eligible-pair positions** and **test X by +97 eligible-pair positions**, preserving each block's marginal distribution and within-block order, and fit the same frozen ridge model. The control never uses labels from the holdout for fitting. A cyclic shift is an engineering sanity check, **not** a formal null distribution, and can be misleading for periodic or autocorrelated signals.

## Metrics and frozen verdicts

For each axis separately, report on the untouched chronological holdout:
- `SSE_baseline`, `SSE_ridge`, `SSE_shift97`;
- `R2_ridge = 1 - SSE_ridge/SSE_baseline`;
- `R2_shift97 = 1 - SSE_shift97/SSE_baseline`;
- `MAE_baseline`, `MAE_ridge`, `MAE_shift97`;
- held-out rows; training/holdout sizes; number of constant features.

A zero baseline SSE or fewer than **500 eligible pairs in either split** renders an axis `NOT_EVALUABLE`. Negative R² values **must be retained**. The model is not allowed to learn a sector-to-sector transfer since only one sector is used.

Predeclared decisions:
- **H1 — X holdout association:** `R2_ridge_x >= 0.10` **and** `R2_ridge_x - R2_shift97_x >= 0.05`.
- **H2 — Y holdout association:** same criteria on Y.
- **H3 — temporal-control specificity:** both `R2_shift97_x <= 0.05` and `R2_shift97_y <= 0.05`. This is a limited negative-control check, not evidence of statistical independence.

Each hypothesis is `SUPPORTED_IN_SELECTED_PRODUCTS`, `NOT_SUPPORTED_IN_SELECTED_PRODUCTS`, or `NOT_EVALUABLE`. A rejected hypothesis is a valid study outcome. No p-values, data-derived threshold changes, bootstrap uncertainty claims or detector accuracy metrics.

**G1–G5 integrity gates** require, separately: verified three-source download and hashes; schema and identity consistency; exact unique-key alignment and conserved eligibility counts; train-only normalization and fitting with controlled negative baseline; compact deterministic result JSON with runtime and original hashes plus canonical-payload SHA-256. A gate failure is not a negative scientific finding and leaves all hypotheses `INCONCLUSIVE_ACCESS_OR_SCHEMA`.

## Interpretation boundaries

A strong predictive association would remain **within one target, one sector and selected clean cadences**, and the pointing vectors themselves may be derived from guide-star measurements from the same science cameras. The offset between CCD1 vector midpoints and CCD4 target midpoints was already characterized in AR-OBS005, but this protocol joins by **cadence** instead of fitting timing offsets. No physical fault labels are introduced.

A positive R² or successful negative control **cannot** demonstrate:
- identification of an astrophysical transit versus a target-local instrumental artifact;
- a causal mechanism, an independent sensor, a novel detector, or telescope capability;
- applicability to other targets, sectors, cameras, pixels or distributions;
- closure of the historical M38B calibration and holdout gaps.

For established context, see [TESSVectors](https://github.com/tessgi/tessvectors), [NASA TESS telescope information](https://heasarc.gsfc.nasa.gov/docs/tess/telescope_information.html), and the [MIT fine-pointing-system publication](https://dspace.mit.edu/entities/publication/10c0556f-931a-40e0-8a41-df7d8906c54a).

**At preregistration:** no AR-OBS006 feature arrays, models, trial outcomes or metrics were examined.
