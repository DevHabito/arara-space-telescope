# AR-OBS001-P01 — Public TESS light-curve access and provenance audit

**Frozen date:** 20 November 2026  
**Stage:** Prospective data-access protocol; no outcome analysis at registration.  
**Scope:** Observational source audit only; not a transient detection experiment.

## Selection, before inspecting the data

Use a target appearing in an official NASA TESS educational tutorial rather than selecting a star on the basis of an interesting light-curve feature. The fixed source is:

- Mission: TESS; archival provider: MAST/STScI; pipeline product: SPOC.
- Target: **TIC 307210830 (L 98-59)**.
- Sector: **5**; 2-minute cadence light-curve product.
- Officially documented product filename:
  `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`
- Candidate canonical archive path:
  `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`.

The filename is shown in NASA's public [Light Curve File tutorial](https://heasarc.gsfc.nasa.gov/docs/tess/LightCurveFile-Object-Tutorial.html). The path is derived from the official [MAST naming and directory convention](https://archive.stsci.edu/missions-and-data/tess/data-products); **its accessibility must be verified at execution time**, not assumed from the documentation.

The associated target-pixel filename documented by NASA is `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits`. Its retrieval and pixel-level analysis are **out of scope** for this first audit. Pixel-derived centroid fields in the light-curve file are not logically independent of the pixel observations.

## Data gate, fixed before execution

One remote file is downloaded to a temporary folder. Verify HTTPS; prohibit redirection to unrelated hosts; enforce a 32 MiB maximum and a 60-second read timeout. After download, record the byte count and SHA-256 checksum. Do not commit the FITS bytes or distribute a modified copy.

Read the FITS headers and binary-table columns with Astropy; require:
- `TICID=307210830` and `SECTOR=5` in an authoritative header, with explicit failure if the values disagree or are absent.
- A light-curve binary table with `TIME`, `SAP_FLUX`, `PDCSAP_FLUX`, and `QUALITY`.
- Equal column lengths, nonempty rows, finite timestamps for at least one cadence, and nonnegative integer quality flags.

Report `PASS`, `FAIL`, or `INCONCLUSIVE` for download, FITS parsing, identity, and required schema. Failure to connect is a **source-access failure**, not a scientific conclusion.

## Descriptive quantities allowed in this audit

Record the file hash, byte length, header values, column names and units, total cadences, count of finite timestamps, number with `QUALITY=0`, bitwise quality-flag counts for bits 1–16, and the finite-positive fraction of SAP and PDCSAP flux, in both all rows and unflagged rows. If the centroid columns exist, record their availability and finite-row fraction, **not** an event association or independent evidence claim.

The following are explicitly forbidden at this stage:

- Searching the time series for interesting dips or selecting intervals based on the data.
- Changing the target, sector or pipeline version after encountering an unexpected result.
- Treating `QUALITY=0` as proof that all remaining observations are artifact-free.
- Treating `PDCSAP_FLUX`, `MOM_CENTR1/2`, or `POS_CORR1/2` as physically independent of the pixels or pipeline.
- Fitting, training, selecting events, measuring transit recovery, or assigning astrophysical versus artifact labels.
- Reinterpreting the old synthetic trials as tests on real telescope observations.

The archive's quality flags are **pipeline annotations**, not an independent ground truth for astrophysical origin. The meanings of individual flags must come from the official MAST product documentation, and the fact that some flags represent corrections rather than irreparable data loss must be preserved.

## Reproducibility contract

- Python 3.12, NumPy 2.x, Astropy and HTTPS standard library.
- Report a deterministic JSON document with a schema version, software/runtime versions, stable target and product identifier, SHA-256 digest of the remote FITS file, observed column/header metadata, gate statuses and counts.
- Include a SHA-256 digest of the canonical JSON payload excluding its own digest field.
- A GitHub Actions run may upload the JSON audit as a workflow artifact. Temporary FITS is deleted after the run; no FITS or personal information is committed to the repository.
- Unit tests must use synthetic in-memory arrays and test schema/quality accounting, without claiming independent observational validation.
- Never create a successful-looking report by filling missing fields with simulated or guessed data.
- When the endpoint is unreachable, preserve a clear error and stop; a separate protocol amendment is required before changing the selected data source.

## What follows if data access succeeds

Inspect whether the available observables can support a **new**, prospectively frozen quality-flag and centroid-dependence audit. A pixel-level causal classification or a true astronomical false-positive-rate claim would require an independently justified label source and noncircular validation. No such labels are established by this protocol.

## References

- NASA TESS Science Support Center, [Light Curve File tutorial](https://heasarc.gsfc.nasa.gov/docs/tess/LightCurveFile-Object-Tutorial.html).
- MAST, [TESS product schema and archive structure](https://archive.stsci.edu/missions-and-data/tess/data-products).
- MAST, [TESS data product overview and quality-flag meanings](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview).
- MAST, [Levels of data processing](https://outerspace.stsci.edu/spaces/TESS/pages/16712852/2.1%2BLevels%2Bof%2Bdata%2Bprocessing).

**Claim boundary:** a successful audit would establish that a named public file was accessed and its schema inspected. It would not demonstrate astronomical detection accuracy or any original scientific result.
