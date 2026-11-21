# AR-OBS004-P01 — pixel morphology, pointing proxy, and background selection

**Recorded:** 20 November 2026 (America/Sao_Paulo).  
**Evidence class:** Direct observational audit of one public TESS SPOC product pair. The experiment is **descriptive**, not a detector benchmark or a physical-cause identification.  
**Protocol preregistered before implementation and inspection:** [AR-OBS004-P01](../preregistration/AR-OBS004-P01.md), commit `eddd1a2ead43c9c78a66c0fc1de47af69e76a13c`.  
**Code:** [scripts/ar_obs004_pixel_morphology.py](../../scripts/ar_obs004_pixel_morphology.py).  
**Synthetic regression tests:** [tests/test_ar_obs004_pixel_morphology.py](../../tests/test_ar_obs004_pixel_morphology.py).  
**Original successful GitHub Actions execution:** [Run #44851579170](https://github.com/DevHabito/arara-space-telescope/actions/runs/44851579170).  
**Permanent output:** [AR-OBS004-P01.json](AR-OBS004-P01.json); original short-lived workflow artifact [#14685477158](https://github.com/DevHabito/arara-space-telescope/actions/runs/44851579170/artifacts/14685477158).

## Identity, program, and provenance

The same public Sector 5 target and products were used throughout; no star, mask, time interval, pipeline file, hypothesis or threshold was selected after looking at the new measurements.

- Target: TIC **307210830** (L 98-59), TESS **Sector 5**, SPOC.
- TPF: `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits`, **46,414,080 bytes**, SHA-256 `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b`.
- LC: `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`, **1,923,840 bytes**, SHA-256 `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
- Both official FITS sources: `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/`.
- Runtime: Python **3.12.16**, NumPy **2.5.5**, Astropy **7.2.4**.
- The original canonical JSON payload (excluding its self-digest field) was independently hash-checked after downloading the workflow artifact. SHA-256: `c577df950c8802650d2874c5aff32c83dee5caf17efd94ff56a9d8f3a49aaa18`.

The TPF pixel cube is **18,944 × 11 × 11**. All **18,944** cadence IDs matched the LC, as in the earlier provenance study. The published mask uses **21** optimal-aperture pixels (bit 2) and **32** background-role pixels (bit 3). These mask roles can overlap. Original FITS bytes, images and per-cadence time series were not committed.

## H1 and H2 — descriptive pixel/position co-variation

At each usable cadence, the analysis used the **positive part** of the calibrated pixel flux in the frozen 21-pixel aperture to calculate a local photocenter. It then computed first differences only for pairs of consecutive `CADENCENO` values with `QUALITY=0`, finite time, photocenter and both `POS_CORR` fields. No event positions, outliers or astrophysical labels were selected.

- Positive-weight photocenters measurable on **17,971** cadences.
- All quality, time, photocenter and position conditions met on **17,025** individual cadences.
- **16,925 consecutive pairs** eligible for the fixed first-difference comparison; 2,018 adjacent source-row pairs did not satisfy the complete eligibility and adjacency rule.

| Predeclared comparison | Observed Pearson correlation |
|---|---:|
| `Δc_x` against `ΔPOS_CORR1` at matched cadence steps | **+0.983548** |
| `Δc_y` against `ΔPOS_CORR2` at matched cadence steps | **+0.989465** |
| `Δc_x` against the same POS_CORR differences shifted 24 pair positions | −0.019822 |
| `Δc_y` against the same POS_CORR differences shifted 24 pair positions | −0.029424 |

**H1 and H2 = SUPPORTED_IN_SELECTED_PRODUCT** against the frozen requirements `|r0| >= 0.20` and `|r0| - |rshift24| >= 0.10`, with at least 100 eligible pairs.

These numerical correlations are strong **inside this source product**. They are not astrophysical accuracy scores or an estimate of how often instrumental artifacts can be distinguished. Both measures involve the same spacecraft imaging and its processing pipeline. The 24-position cyclic shift is only a fixed comparison; temporal autocorrelation and nonstationarity mean it is **not** a principled statistical null distribution. No p-value or independent validation is claimed.

## H3 — flagged estimated-background selection

The TPF reports an estimated per-pixel `FLUX_BKG`. Using the frozen median over the **32 background-mask pixels** on each cadence:

| Predeclared group | Total cadences | Finite background estimates | Median estimated background, e⁻/s per pixel |
|---|---:|---:|---:|
| `QUALITY=0` | 17,025 | **17,025** | **90.108513** |
| Quality **bit 13** (scattered-light exclusion) | 550 | **550** | **764.526245** |
| Quality **bit 6** (reaction-wheel desaturation) | 60 | **0** | Not measurable |

The difference in observed medians between the bit-13 and quality-zero groups was **+674.417732 e⁻/s per pixel**. **H3 = SUPPORTED_IN_SELECTED_PRODUCT** according to the frozen count and signed-median rule.

This does **not** independently confirm an instrumental cause: the scattered-light flag can itself be set using background estimates. The result can therefore be largely or entirely a **pipeline selection effect by construction**, and the two sets of cadences have different processing status. It would be circular to treat the flag as the true physical label in a classifier.

The bit-6 subgroup is an important **negative measurement result**: all **60** such cadences lacked a finite background estimate under the preregistered completeness rule. We cannot evaluate the background distribution of reaction-wheel-desaturation events from this proxy in this product. Do not fill those missing data with values from nearby cadences.

## Test and audit history, including the failed run

The first hosted run [#44851516067](https://github.com/DevHabito/arara-space-telescope/actions/runs/44851516067) stopped **before** observational analysis because one synthetic test counted overlapping flag cohorts incorrectly (the fixture contained 70 bit-13 rows, not 50). The failure was in the **test oracle**, not the method's observational output or the source data.

That regression expectation was corrected in commit `fde5fbc` without changing any frozen research question, threshold or input FITS file. The second hosted run **#44851579170** passed all **10 synthetic checks** and all five G1–G5 gates, then performed the actual TESS analysis. Both runs remain visible as provenance. The historical repository-wide CI should be reported separately from this dedicated observational run.

## Scientific interpretation and future constraints

The new observation is an extremely strong **within-product association** between pixel photocenter steps and the archive's position-correction steps. It is a useful reproducibility and diagnostic-consistency finding but not an independent sensor or a physical diagnosis of an event. By itself it cannot establish an ARARA-specific algorithmic novelty.

The background comparison confirms a distinction in the **selected** pipeline data, not independent identification of sky-scattered light. The missing bit-6 background readings explicitly constrain any attempted physical analysis.

A next, genuinely different, prospectively registered experiment should investigate whether a physical event label exists **outside these same processed flux/pixel/flag estimates**. Potential examples include verified spacecraft event logs or independently documented astronomical objects, with careful alignment, calibration, domain controls, and prospective evaluation. A TESS quality flag alone is not such ground truth.

No transient was detected or labeled here, no survey-level false-positive rate was estimated, no causal mechanism was proven, and the historical M38B calibration/holdout gap remains open.

## Public sources and attribution

- MAST, [TESS Data Product Overview](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview).
- NASA, [TESS Science Data Products Description](https://ntrs.nasa.gov/api/citations/20205008729/downloads/EXP-TESS-ARC-ICD-TM-0014-Rev-F_v2.pdf).
- STScI, [Tour of TESS 2-minute Target Pixel Products](https://spacetelescope.github.io/mast_notebooks/notebooks/TESS/beginner_tour_lc_tp/beginner_tour_lc_tp.html).

No private scientific correspondence, personal email addresses or implied external collaborations appear in this report.
