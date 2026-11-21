# AR-OBS005-P01 — Camera-level engineering-vector provenance and cadence alignment

**Registration date:** 20 November 2026 (America/Sao_Paulo).  
**Status:** Prospective protocol. No AR-OBS005 observations or outcomes have been inspected in the source file before this registration.
**Parent:** AR-OBS004; this protocol adds a *different data-product family*, not a new detector.

## Research question

Can a public, camera-level TESS engineering-vector product be linked by cadence identity and exposure time to the already audited Sector 5 target light curve? Are quaternion-derived engineering measurements sufficiently populated for a future, separately preregistered instrumental analysis?

A separate file and processing lineage **do not guarantee statistical or physical independence**. In particular, spacecraft fine pointing may use the science cameras, and the selected vectors were themselves resampled to 120-second science cadence. A successful join establishes traceability, not truth labels or an improvement in discrimination of astrophysical events.

## Frozen source identities, chosen without inspecting the new vector rows

- Target **TIC 307210830 (L 98-59)**; TESS **Sector 5**, **Camera 4**, CCD 4; two-minute cadence.
- Fixed original SPOC LC: `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`, from `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/`. Its verified SHA-256 is `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
- Fixed **TESSVectors** engineering product: `TessVectors_S005_C4_120.csv` at `https://heasarc.gsfc.nasa.gov/docs/tess/data/TESSVectors/Vectors/120_Cadence/TessVectors_S005_C4_120.csv`.
- The engineering CSV hash is **unknown at registration** and will be measured.
- The public directory itself lists the exact Sector 5/Camera 4 file: https://heasarc.gsfc.nasa.gov/docs/tess/data/TESSVectors/Vectors/120_Cadence/.
- The official source project explains that `Cadence` is the mission cadence index, `MidTime` is a spacecraft-frame exposure midpoint *without* barycentric correction, and component vectors derive from MAST quaternion and Earth–Moon engineering products: https://github.com/tessgi/tessvectors.

This is an early-stage, publicly distributed reprocessed engineering product (not the original quaternion FITS). No other sector, camera, filename, calibration release or mirror may be substituted after inspecting outcomes. Inaccessibility must be preserved as an access failure. A future direct-quaternion study would require a separate source and protocol.

## Frozen access and schema gates

- Python 3.12, NumPy 2.x, Astropy 6/7. Use standard-library CSV; do not install or execute the upstream project package.
- Download CSV over HTTPS from the exact `heasarc.gsfc.nasa.gov` host, reject cross-host and non-HTTPS redirects, cap at 24 MiB with a 90-second per-read timeout; record final URL, byte length and SHA-256.
- Download LC with the existing bounded HTTPS helper; demand its frozen SHA-256 and `TICID=307210830`, `SECTOR=5`, `CAMERA=4`, `CCD=4` from noncontradictory FITS headers.
- Because examples of TESSVectors have human-readable comment preambles, the reader must locate exactly one CSV header containing the documented `Cadence` and `MidTime` fields and parse only the following tabular section; it must not silently reinterpret a preamble line as observations.
- Require `Cadence`, `MidTime`, `Quat_NBinned`, `Quat1_StdDev`, `Quat2_StdDev`, `Quat3_StdDev`, `Quat4_StdDev`. Record additional columns, without silently using them as evidence.
- Require one unique integral `Cadence` per row, finite `MidTime` for at least one row, no contradictory `Sector` or `Camera` values **if such columns exist**, and no more than 100,000 rows. Negative quaternion counts are invalid. The LC must have unique integral `CADENCENO` and equal-length `TIME`, `TIMECORR`, `QUALITY`.
- Missing or nonfinite individual quaternion standard deviations are **missing data**, not zero jitter. They must not be filled from adjacent cadences.

## Frozen cadence join and metrics

Join the CSV `Cadence` and LC `CADENCENO` on their *exact integer values*; no nearest-time matching or arbitrary shift in cadence numbers is permitted. Count each file's rows, matched/unmatched rows, finite-time matches and quality-zero/flagged matches.

For every matched row where `TIME`, `TIMECORR`, and engineering `MidTime` are all finite:

`time_delta_seconds = ((LC.TIME - LC.TIMECORR) - Vector.MidTime) * 86400`.

Report the count, median and 95th percentile of `abs(time_delta_seconds)`, the maximum, and signed median. Do not fit or subtract a constant offset. TESSVectors documents that its camera-level time is benchmarked to **CCD1**, while this target was observed on **CCD4**, with a potential staggered-read time offset around 0.2–1 second; this is a compatibility study, not a timing calibration.

On matched rows, define engineering availability `E` iff `Quat_NBinned > 0` and all four `Quat[1-4]_StdDev` values are finite and nonnegative. Report the four-cell contingency of `E` against `QUALITY=0`; do not call the quality flag a physical failure label. Describe the finite `Quat_NBinned` count and median for matched E rows. The quaternion standard deviations have no claimed direct conversion to the AR-OBS004 pixel-center displacement at this stage.

## Prospective hypotheses

- **H1 — cadence coverage:** at least **95%** of LC cadences with finite `TIME` match an engineering row with a finite `MidTime`.
- **H2 — time-frame compatibility:** at least **100** finite-time matches, median absolute time difference **<= 2 seconds**, and 95th percentile absolute difference **<= 5 seconds**.
- **H3 — engineering availability:** at least **50%** of matched LC `QUALITY=0` rows satisfy `E`, with at least 100 matched zero-quality rows.

Verdicts are `SUPPORTED_IN_SELECTED_PRODUCTS`, `NOT_SUPPORTED_IN_SELECTED_PRODUCTS`, or `NOT_EVALUABLE` when required denominators or values are absent. A rejection is scientifically valid. No thresholds, source choice or offset correction may be adapted after inspecting results.

**G1–G5 engineering-integrity gates:** bounded and hashed sources; validated FITS/CSV identity and schema; unique keys and conserved join accounting; metrics without nonfinite imputation and with count consistency; compact reproducible JSON including source digests, runtime versions, hypothesis outcomes and SHA-256 of canonical payload excluding its own digest. If a gate fails, mark hypotheses `INCONCLUSIVE_ACCESS_OR_SCHEMA` and preserve error category.

## Scope and stop conditions

- Neither engineering vectors nor `QUALITY` are independent ground truth for physical events.
- No target anomaly, transit, spacecraft fault, or photometric change may be searched or labeled in this protocol.
- Do not compute correlations with pixel brightness until a new protocol reviews overlap, guide-camera usage, cadences, and leakage.
- Never distribute CSV science rows, original FITS or the target's light curve as GitHub artifacts. Preserve **counts, distributions, headers and digests only**.
- No discovery claim, classifier accuracy, novel telescope instrument or closure of historical M38B calibration gaps is supported by these access and alignment checks.

## Public references

- TESS Guest Investigator Program, [TESSVectors repository](https://github.com/tessgi/tessvectors) and [120-second file index](https://heasarc.gsfc.nasa.gov/docs/tess/data/TESSVectors/Vectors/120_Cadence/).
- MAST, [Engineering Data product locations](https://archive.stsci.edu/missions-and-data/tess/data-products).
- NASA, [TESS Instrument Handbook](https://archive.stsci.edu/missions-and-data/tess) for camera-guidance and clock-frame considerations.

**Evidence status at registration:** no AR-OBS005 engineering rows have been analyzed.
