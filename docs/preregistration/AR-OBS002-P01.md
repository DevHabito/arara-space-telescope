# AR-OBS002-P01 — Paired-sector TESS missingness and quality-mask audit

**Registered:** 20 November 2026 (America/Sao_Paulo).
**Stage:** Prospective protocol. No data analysis or results are included in this commit.
**Relationship:** Follow-up to AR-OBS001-P01; the previous protocol and its archived source remain unchanged.

## Scientific question and limits

Is the observed alignment between the TESS SPOC `QUALITY=0` mask and the availability of positive, finite `PDCSAP_FLUX` a **row-level equivalence** in the archived Sector 5 product, and does the same relation hold for a *preselected* different observing sector of the **same target**?

This is a study of **pipeline selection and measurement availability**, not of the physical origin of individual flux dips. A quality flag is a processing annotation rather than an independent astrophysical label. Missingness may be produced by the pipeline, and a different sector may have different pointing, systematics, reduction version, and observing conditions.

## Fixed sources, selected before seeing the second-sector results

Two publicly documented, 2-minute SPOC light-curve FITS files for **TIC 307210830 (L 98-59)**:

| Role | TESS sector | File name |
|---|---:|---|
| First, previously audited source | 5 | `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits` |
| New comparison source | 2 | `tess2018234235059-s0002-0000000307210830-0121-s_lc.fits` |

The full HTTPS URL for each is `https://archive.stsci.edu/missions/tess/tid/sNNNN/0000/0003/0721/0830/<file_name>` with sector padded to four digits. This directory scheme and both filenames are specified by NASA and MAST:

- [NASA TESS LightCurveFile tutorial](https://heasarc.gsfc.nasa.gov/docs/tess/LightCurveFile-Object-Tutorial.html) (lists both exact product names).
- [MAST TESS file naming and directory convention](https://archive.stsci.edu/missions-and-data/tess/data-products.html).

The observed Sector 5 byte hash from AR-OBS001 is **frozen as a source-consistency check**, not an outcome criterion: `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`. Sector 2's hash is unknown at registration.

Do not substitute another sector, star, file version, or provider if a download fails. Report the access failure without inferring the research hypothesis.

## Fixed ingest and evidence checks

- Python 3.12, NumPy 2.x, Astropy 6.x or 7.x.
- Download each file over HTTPS from an STScI host, rejecting off-host redirects; 32 MiB maximum per file and 60-second timeout per remote read.
- Keep the FITS files in temporary storage and do not commit the FITS bytes.
- Require valid FITS headers with unique `TICID=307210830` and the expected `SECTOR` on each file.
- Require exactly one nonempty light-curve table with 1-D, equal-length `TIME`, `SAP_FLUX`, `PDCSAP_FLUX`, `QUALITY`, `MOM_CENTR1`, `MOM_CENTR2`, `POS_CORR1`, and `POS_CORR2`. Record when `PSF_CENTR1/2` exist and whether their samples are finite; if columns are absent, report that, not a fabricated count.
- `QUALITY` must be nonnegative integral and `TIME` must contain finite timestamps.
- Store file size, original SHA-256, identifier/header information, column units and availability, Python/NumPy/Astropy versions, run-selection metadata, and SHA-256 of the canonical JSON payload (without its digest field).

The first source should be verified against the preserved Sector 5 SHA. A changed file fails the source-consistency gate; do not quietly replace its identity.

## Frozen row-wise measurements

For each sector, define masks independently for **each cadence**:

- `Q`: `QUALITY == 0`.
- `T`: finite `TIME`.
- `S`: finite, strictly positive `SAP_FLUX`.
- `P`: finite, strictly positive `PDCSAP_FLUX`.
- `M`: both `MOM_CENTR1` and `MOM_CENTR2` finite.
- `C`: both `POS_CORR1` and `POS_CORR2` finite.

For `T`, `S`, `P`, `M`, and `C`, record total true rows and the complete four-cell contingency table relative to `Q`:
`Q_and_valid`, `Q_and_invalid`, `flagged_and_valid`, `flagged_and_invalid`.
The sum of the four cells **must equal total rows**.

Record whether `Q` and `P` are *exactly equivalent*, i.e. whether the combined count `Q_and_invalid + flagged_and_valid` equals zero; also report the individual mismatch counts. Do not infer row-wise equivalence merely because overall counts match.

For each quality bit 1–16, record how many cadences carry the bit (overlapping flags are allowed) and, in that subset, how many have valid `PDCSAP_FLUX` and valid moment-centroid pairs. Do not sum bit counts as if flags were mutually exclusive.

Across the two sectors, report these counts and the fractions of valid `PDCSAP_FLUX` for `QUALITY=0` and `QUALITY!=0` when the denominator is nonzero. No test of statistical independence, time-series detection, or significance will be performed.

## Prospective hypotheses and verdict rule

**H1 (row-level Sector 5 alignment):** the pre-audited Sector 5 product satisfies `Q == P` for **every** cadence.

**H2 (cross-sector alignment):** the preselected Sector 2 product independently satisfies `Q == P` for every cadence.

Each H is `SUPPORTED_IN_SELECTED_FILE` only if both mismatch cells are zero; otherwise `NOT_SUPPORTED_IN_SELECTED_FILE`. If data are unavailable, return `INCONCLUSIVE_SOURCE_ACCESS`, never a supportive result. These are **exact descriptive claims about archived pipeline output**, not hypotheses about telescope physics or general SPOC behavior.

**G1–G5 validation gates** require only trustworthy execution:
- G1: both files downloaded within the fixed limits and source hashes recorded.
- G2: both FITS headers confirm the fixed identity, and Sector 5 hash matches the archival value.
- G3: required columns and row shapes valid, quality flags integral/nonnegative, and timestamps present.
- G4: all five contingency tables conserve total rows and quality-bit subset counts do not exceed their flagged subsets.
- G5: canonical JSON checksum and run versions recorded, with no individual light curves, pixels, event times or private data in the persisted report.

An H1/H2 rejection is a valid scientific outcome **even if all validation gates pass**.

## Forbidden inference and next gate

- Do not search for, fit, or label transit events.
- Do not read `QUALITY` as a physical ground truth for instrumental versus astrophysical origins.
- Do not interpret `PDCSAP_FLUX` and `SAP_FLUX` as independent measurements; the former is corrected from the latter.
- Do not treat moment centroid information as independent of the flux-bearing pixels.
- Do not publish FITS bytes, claim a new detector, or promote descriptive correlations into astrophysical discovery.

A follow-up, separately preregistered **target-pixel** investigation is allowed only after reviewing this audit and verifying pixel file provenance and the causal dependencies between the measurements.

**At registration:** no Sector 2 FITS measurements or outcomes had been read; the hypotheses and gates were frozen before implementation.
