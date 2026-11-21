# AR-OBS003-P01 — TESS pixel/aperture provenance and photometry reconstruction audit

**Registered:** 20 November 2026, America/Sao_Paulo.  
**Status:** Prospective protocol. Data inspection and outcomes must follow in later commits.  
**Parent studies:** AR-OBS001-P01 (single-file access) and AR-OBS002-P01 (two-sector row-wise missingness). Neither result is reclassified here.

## Question

For one publicly identified TESS target and observing sector, do the target-pixel product and its pipeline light-curve product align at the cadence level? Can the simple aperture photometry (SAP) reported in the light-curve table be reconstructed by summing calibrated pixels in the aperture marked by the FITS image?

This is a **pipeline consistency** question. TPF flux and light-curve SAP flux originate from the same detector observations and are not independent astronomical confirmations. Pixel-derived centroid positions are also not automatically independent of photometry, and the quality flags are pipeline annotations, not astrophysical truth labels.

## Frozen public sources

Target **TIC 307210830 (L 98-59)**, **TESS sector 5**, **SPOC** 2-minute products:

- Target Pixel File: `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits`.
- Light Curve File: `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`.
- Both archival URLs use the directory: `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/`.
- Frozen independent source identity check for the previously audited LC: SHA-256 `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
- The original TPF SHA-256 is **unknown at preregistration** and must be measured, not guessed.

The specific product name is in the official [NASA TESS Target Pixel File tutorial](https://heasarc.gsfc.nasa.gov/docs/tess/Target-Pixel-File-Tutorial.html). FITS table and aperture-mask semantics are described in the [MAST TESS notebook](https://spacetelescope.github.io/mast_notebooks/notebooks/TESS/beginner_tour_lc_tp/beginner_tour_lc_tp.html) and [MAST archive documentation](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview).

This exact pair was selected **before** inspecting target-pixel measurements; do not change source, product revision, aperture choice, target or sector because of an unfavorable outcome.

## Ingest and identity contract

- Python 3.12, NumPy 2.x, Astropy 6.x/7.x.
- Download over HTTPS from `archive.stsci.edu` or redirected HTTPS STScI hosts only, with 120-second per-read timeout and at most **128 MiB per FITS**. Temporary downloads must be deleted after the run. No FITS file may be committed or uploaded as a workflow artifact.
- Record the URL, final URL, byte count, SHA-256 and software versions. Recheck the LC against its frozen SHA-256.
- Both FITS products must have consistent `TICID=307210830` and `SECTOR=5` headers, without contradictory extension values.
- TPF must have exactly one binary table extension named `PIXELS`, with 1-D `TIME`, `CADENCENO`, `QUALITY` and a 3-D `FLUX` column of shape (cadences, height, width). Require one 2-D integer `APERTURE` image with the same image-plane dimensions and **at least one optimal-aperture pixel** selected by the second aperture-mask bit (`mask & 2 != 0`). Record image dimensions, column names and units, and counts of bits 1 through 9 in the aperture image.
- LC must have a nonempty `LIGHTCURVE` table with 1-D `TIME`, `CADENCENO`, `QUALITY`, `SAP_FLUX`, `PDCSAP_FLUX`. Require nonnegative integral flags and unique integral `CADENCENO` within each file.
- If any essential source, identity or schema check fails, retain the error and return `INCONCLUSIVE_ACCESS_OR_SCHEMA` for hypotheses. Never substitute simulated values for FITS measurements.

## Predefined measurements

**Cadence pairing:** match on *exact integer* `CADENCENO`, never by row index or nearest timestamp. Record each file's cadence count, intersection size and unmatched counts. On matching cadences record (i) number of unequal `QUALITY` values, (ii) number with both `TIME` values finite, and (iii) maximum and median absolute `TIME` difference in days. Unpaired rows cannot be used to support H1 or H2.

**SAP reconstruction:** for each matched cadence with `QUALITY=0` in both products, finite positive LC `SAP_FLUX`, and **all** TPF `FLUX` values finite inside the frozen optimal aperture, compute

`R_i = sum(TPF.FLUX[i, aperture_bit_2])`;

`delta_i = |R_i - LC.SAP_FLUX[i]| / max(|LC.SAP_FLUX[i]|, 1)`.

Do not subtract `FLUX_BKG` again: the archived `FLUX` is documented as calibrated, background-subtracted pixel flux. Record number of eligible rows, skipped rows by reason, median and maximum `delta_i`, and count/fraction with `delta_i <= 0.001`. Report median signed (R−SAP) in flux units as well. Do not introduce an additional per-sector calibration factor, offset, event mask or fitted parameter.

Also record: TPF pixel-flux array shape; selected and background-mask pixel counts; number of matched cadences with at least one finite selected pixel; number with all selected pixels finite; and uncorrected `SAP_FLUX` missingness relative to quality. We do not compute a transit or anomaly statistic.

## Frozen hypotheses and verdicts

- **H1 — matched-product consistency:** At least one matched cadence with finite times; **every matched pair has identical `QUALITY`**, and all pairwise finite `TIME` differences are <= `1e-6` day. `SUPPORTED_IN_SELECTED_PRODUCT_PAIR` if all conditions hold; otherwise `NOT_SUPPORTED_IN_SELECTED_PRODUCT_PAIR`.
- **H2 — SAP aperture reconstruction:** At least **100 eligible** cadences, median relative discrepancy `<= 0.0001`, and at least **95%** of eligible cadences with `delta_i <= 0.001`. Report `SUPPORTED_IN_SELECTED_PRODUCT_PAIR` or `NOT_SUPPORTED_IN_SELECTED_PRODUCT_PAIR` exactly; an H2 rejection is an acceptable scientific result. These tolerances are fixed engineering checks for this one pipeline product, not universal accuracy thresholds.

The integrity gates are:
- **G1:** both verified HTTPS products downloaded within fixed limits, complete source hashes stored, and the pinned LC SHA matched.
- **G2:** selected TIC, sector, FITS structure, pixel/aperture dimensions and compulsory columns verified.
- **G3:** cadence IDs are unique and matched by explicit identity, with accounting of unmatched cadences.
- **G4:** aperture bit and eligibility counts are internally consistent; all relative errors are finite, count constraints hold, no result is silently imputed.
- **G5:** deterministic aggregate JSON includes software versions, source hashes, counts, hypotheses and a SHA-256 of its canonical payload (excluding its own digest). No individual pixel images or light curves are preserved.

A hypothesis can fail while all five integrity gates pass. A gate failure must not be disguised as a scientific negative.

## Strict scope of any conclusion

- Do **not** treat SAP reconstruction as independent evidence of a true astronomical source or event.
- Do **not** label quality-flagged cadences as instrumental faults, nor `QUALITY=0` as guaranteed clean astronomy.
- Do **not** interpret a matching `CADENCENO` as proof that source images are independent.
- Do **not** search for transits or threshold unusual cadences based on the observed pixel series.
- Do **not** tune acceptance thresholds after seeing discrepancies.
- Do **not** promote this archival product audit to ARARA performance validation or claim a novel astronomical detection method.

A separate future preregistration may investigate pixel-space morphology, background trends and centroid shifts, after examining whether independently sourced diagnostics or catalog labels are available. The present task only tests **traceability of measurements**, not causal event attribution.

**Evidence status at freeze:** TPF not yet read in this research branch. Both hypotheses are open.
