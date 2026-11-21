# AR-OBS003-P01 — target-pixel provenance and SAP aperture reconstruction

**Date recorded:** 20 November 2026 (America/Sao_Paulo).  
**Evidence type:** Direct audit of archived **real TESS** pixel and light-curve files, with a preregistered pipeline-consistency comparison. **Not a transient detection test.**  
**Protocol frozen before inspecting TPF:** [AR-OBS003-P01](../preregistration/AR-OBS003-P01.md), commit `add93ad1b071a4138549b6d4428e3b0155c9869c`.  
**Code:** [scripts/ar_obs003_pixel_aperture.py](../../scripts/ar_obs003_pixel_aperture.py).  
**Regression tests:** [tests/test_ar_obs003_pixel_aperture.py](../../tests/test_ar_obs003_pixel_aperture.py), **10 passed** on Python 3.12.  
**Source execution:** [GitHub Actions #44850462411](https://github.com/DevHabito/arara-space-telescope/actions/runs/44850462411), public-archive `pixel-provenance` job.  
**Complete output preserved:** [AR-OBS003-P01.json](AR-OBS003-P01.json).  
**Original short-lived workflow artifact:** [AR-OBS003 provenance ZIP, artifact #14685400495](https://github.com/DevHabito/arara-space-telescope/actions/runs/44850462411/artifacts/14685400495).

## Frozen data selection and original source identities

- **Target:** TIC 307210830 (L 98-59), **TESS Sector 5**, SPOC two-minute data.
- **TPF:** `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits`; 46,414,080 bytes; SHA-256 `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b`.
- **Light curve:** `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`; 1,923,840 bytes; SHA-256 `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae` (agrees with the previously pinned AR-OBS001/002 hash).
- **Source:** `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/` with the two exact file names.
- **Environment:** Python 3.12.16; NumPy 2.5.5; Astropy 7.2.4.
- **Full canonical JSON payload SHA-256:** `efae93cf6c6b687dcea52e31c8072230b154554445228ea966b765088f11c669`. The source workflow artifact's JSON digest was independently checked after download.

The official [NASA TPF tutorial](https://heasarc.gsfc.nasa.gov/docs/tess/Target-Pixel-File-Tutorial.html) identifies this exact target/product. [MAST's data product overview](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview) defines the aperture-image bit semantics.

## H1 — product alignment: supported in this product pair

Both FITS products contain exactly **18,944 cadences**. Matching was performed on integer `CADENCENO`, **not row index**:

| Measurement | Observed |
|---|---:|
| Matched `CADENCENO` values | 18,944 |
| Unmatched TPF / LC cadence numbers | 0 / 0 |
| Disagreements in `QUALITY` on matched cadences | **0** |
| Matched rows with finite times in both files | 17,971 |
| Maximum absolute paired time offset | **0 days** |

Therefore **H1 = SUPPORTED_IN_SELECTED_PRODUCT_PAIR**, under the frozen quality/time consistency conditions. This is a strong source-alignment check, but it does not imply independent physical measurements.

## Aperture geometry: measured rather than inferred

The TPF `FLUX` cube has dimensions **(18,944 cadences, 11 rows, 11 columns)**. The 11×11 FITS aperture image includes:

- 121 pixels marked as collected (mask bit 1).
- **21 pixels in the optimal SAP photometric aperture** (bit 2).
- **32 pixels marked for background calculation** (bit 3).
- 21 pixels marked for the flux-weighted centroid calculation (bit 4).
- No pixels marked for PRF centroid calculation (bit 5).
- The remaining pixel-mask flags are preserved in the JSON output.

These roles can overlap. The individual counts must **not** be added as mutually exclusive categories. The sum of a calibrated, background-subtracted pixel `FLUX` image across the bit-2 optimal aperture is a known method for reproducing SAP; it is not a new photometric algorithm.

## H2 — reproduce SAP from calibrated pixels: supported in this product pair

Only predeclared eligible cadences were used: `QUALITY=0` in both products, positive and finite LC `SAP_FLUX`, and all selected pixel fluxes finite.

| Measurement | Observed |
|---|---:|
| Eligible paired cadences | **17,025** |
| Excluded because at least one quality flag was nonzero | 1,919 |
| Excluded for an invalid positive SAP value after zero-quality selection | 0 |
| Excluded for missing optimal-aperture pixels after previous conditions | 0 |
| Cadences with relative discrepancy <= 0.001 | **17,025 / 17,025** |
| Median absolute relative discrepancy | **3.032639632197059 × 10⁻⁸** |
| Maximum absolute relative discrepancy | **1.2027551989857079 × 10⁻⁷** |
| Median signed difference, reconstructed minus SAP | **−3.814697265625 × 10⁻⁶ e⁻/s** |

Thus **H2 = SUPPORTED_IN_SELECTED_PRODUCT_PAIR** under the prior thresholds (at least 100 eligible rows; median relative error <= 0.0001; >= 95% within 0.001). The achieved discrepancies were small without any fitted correction factor or adjustment of the aperture.

All **five integrity gates G1–G5 passed**. The original source hashes, schema metadata, primary counts and canonical output are preserved. The uploaded workflow artifact contains only aggregate JSON, not the original FITS files or a per-cadence light curve.

## Why this matters — and what it does not prove

The result connects our archival observations with the actual pixels collected for this target: the two FITS products agree on cadence identity and quality masks, and the official SAP values can be reconstructed from the selected pixels to a very small relative discrepancy.

This is **not** independent verification of a star dimming, exoplanet transit, instrument failure or new transient. Both values depend on the **same SPOC-calibrated pixels**, and the archive supplies no independent truth labels. Strong reconstruction is expected from the published TESS processing model; it is a reproducibility and provenance milestone, not scientific novelty.

In particular:
- The test does not evaluate how `PDCSAP_FLUX` is corrected or whether a real astrophysical signal survives cotrending.
- A `QUALITY=0` cadence is not guaranteed to be free of all artifacts.
- The large pixel cube has not been searched for events; the audit only computed aggregate consistency statistics.
- The reconstruction comparison used only 17,025 predeclared eligible rows; the remaining cadences are not claims of erroneous photometry.
- The available pixel data and flux-weighted centroid estimates are **not physically independent sensors**.
- The archived M38B calibration and holdout gap remains unresolved.

## Proposed next distinct gate

A **new, separately frozen protocol** should examine the *spatial* behavior of selected pixels under independently motivated instrumental proxies, with explicit controls for flux-background coupling, pixel-level missingness and known quality-flag semantics. One useful starting point is a **pixel morphology and centroid-consistency audit** on the same fixed source, without any event labeling. It must distinguish what can be computed from the pixel cube from what is genuinely independent of it.

A more demanding future study could then obtain an independently justified set of known instrumental events and true astrophysical events, with source provenance, time-causal eligibility and no tuning on held-out results. No such labels have been established by AR-OBS003.

**Conclusion:** AR-OBS003 successfully tests archival pixel-to-light-curve traceability for a named TESS product. It does not establish an operational ARARA instrument or detector performance.
