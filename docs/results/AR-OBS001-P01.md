# AR-OBS001-P01 — first public TESS file provenance audit

**Recorded:** 20 November 2026 (Brazil time).  
**Evidence type:** Observational **data access and schema audit**, not a transient or astrophysical detection experiment.  
**Protocol frozen first:** [AR-OBS001-P01](../preregistration/AR-OBS001-P01.md), commit `4193fc74fd349d50ef81dfaea41d433ffb20b4fb`.  
**Hosted run:** [GitHub Actions #44847535996](https://github.com/DevHabito/arara-space-telescope/actions/runs/44847535996), job `source-provenance` (successful).  
**Persisted aggregate:** [AR-OBS001-P01.json](AR-OBS001-P01.json).  
**Original workflow artifact:** [Public FITS provenance report, artifact #14684365327](https://github.com/DevHabito/arara-space-telescope/actions/runs/44847535996/artifacts/14684365327) (GitHub retention applies).

## What was actually downloaded

The program retrieved one SPOC light-curve FITS product **from the official STScI archive** using the file name and path frozen before retrieval:

- Object: L 98-59, `TICID=307210830`.
- TESS sector: `5`; Camera `4`, CCD `4`.
- Filename: `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`.
- Source: `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`.
- Downloaded size: **1,923,840 bytes**.
- Original FITS SHA-256: `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
- Header identifies `TELESCOP=TESS`, `INSTRUME=TESS Photometer`, `TIMESYS=TDB`, `PROCVER=spoc-5.0.20-20201120`.
- Runtime: Python `3.12.16`, NumPy `2.5.5`, Astropy `7.2.4`.
- Canonical JSON payload SHA-256: `2d8011f576107810da102d85d58c4e587b67eb799e3ff2e607cf302c1c1fac18` (independently recalculated from the stored workflow artifact).

This is **real archived observational data**. Its availability does not supply true/false labels for any event, and no original FITS data has been committed to the repository.

## Frozen gate results

| Gate | Outcome |
|---|---|
| Download bounded public HTTPS file | PASS |
| Parse FITS as an astronomical data product | PASS |
| Verify archived target and sector identity | PASS |
| Verify required schema: TIME, SAP_FLUX, PDCSAP_FLUX, QUALITY | PASS |

The generated output was inspected and its canonical JSON digest independently recomputed. A failing access attempt would have been recorded as an access failure, not an astrophysical result.

## Observational availability, without event selection

The LIGHTCURVE table contains **18,944 cadences**, including **17,971 finite TIME values**.

| Property | Row count |
|---|---:|
| `QUALITY=0` | 17,025 |
| `QUALITY!=0` | 1,919 |
| Positive finite `SAP_FLUX`, all rows | 17,857 |
| Positive finite `SAP_FLUX`, `QUALITY=0` | 17,025 |
| Positive finite `PDCSAP_FLUX`, all rows | 17,025 |
| Positive finite `PDCSAP_FLUX`, `QUALITY=0` | 17,025 |
| Finite `MOM_CENTR1` and `MOM_CENTR2`, individually | 17,857 each |
| Finite `POS_CORR1` and `POS_CORR2`, individually | 17,656 each |
| Finite `PSF_CENTR1` and `PSF_CENTR2`, individually | **0 each** |

The **counts** of positive finite PDCSAP_FLUX and QUALITY=0 cadences agree; the present audit did **not** calculate a row-by-row equivalence test, so that stronger statement remains unverified. The overlap of centroid availability with quality flags was also not measured.

Select nonzero quality-bit counts (these are **overlapping annotations**, not disjoint event classes):

- Bit 4: 974 rows (Earth-point flag).
- Bit 13: 550 rows (scattered-light exclusion).
- Bit 8: 216 rows (manual exclusion).
- Bit 16: 115 rows (insufficient targets for error correction).
- Bit 6: 60 rows (reaction-wheel desaturation).
- Bit 5: 54 rows (Argabrightening event).

Flag definitions are taken from [MAST's quality-bit table](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview). Their presence documents pipeline annotations; it does not by itself establish the physical origin of individual brightness variations. Not all nonzero flags mean an unusable cadence.

## What this changes in our research direction

1. **Quality-dependent missingness must be audited explicitly.** Analyses using only PDCSAP flux or only quality-zero cadences could have different sample selection from those using SAP flux.
2. **Available column names are not enough.** PSF centroid columns exist but all their entries lack finite values in this product. A plan that silently assumes these measurements exist would be invalid.
3. **Moment centroids are not independent telemetry.** Flux-derived positions may help diagnose spatial effects but share data with the photometric measurements; using them cannot resolve causal ambiguity by fiat.
4. **Reprocessing must be accounted for.** SAP and PDCSAP are not interchangeable measurements; PDCSAP has undergone correction for common systematic trends, and that processing can suppress astrophysical variability in some regimes.

## Questions still open

The next protocol should separately test quality/flux availability **row by row**, investigate whether these descriptive relationships persist in an untouched public comparison sector, and inspect which position metrics are usable without treating them as independent physical ground truth. A subsequent **pixel-level** study must obtain and verify an official TPF for the same target and sector before proposing any event attribution.

No telescope performance benchmark, known-transit recovery, controlled falsification of a detector, or new astrophysical finding has been established here. The archived M38B calibration-and-holdout gap is unchanged.

The work uses NASA/MAST published data products and public scientific documentation. No private scientific correspondence or external collaboration claim is included.
