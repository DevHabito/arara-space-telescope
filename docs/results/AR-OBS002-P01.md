# AR-OBS002-P01 — quality and missingness across two archived TESS sectors

**Recorded:** 20 November 2026 (America/Sao_Paulo).  
**Evidence level:** Direct audit of two real archived SPOC FITS light-curve products. **No event classification was performed.**  
**Protocol:** [AR-OBS002-P01](../preregistration/AR-OBS002-P01.md), frozen first at commit `a319d6f5b6e8b6b7175301e8ee57f379696d7996`.  
**Permanent tabulation:** [AR-OBS002-P01-aggregate.json](AR-OBS002-P01-aggregate.json).  
**Authoritative original execution:** [GitHub Actions #44849436001](https://github.com/DevHabito/arara-space-telescope/actions/runs/44849436001), [full JSON artifact #14684887210](https://github.com/DevHabito/arara-space-telescope/actions/runs/44849436001/artifacts/14684887210).

## Source selection and provenance

The source pair was selected by **target and product name before inspecting the Sector 2 data**, using the published [NASA light-curve tutorial](https://heasarc.gsfc.nasa.gov/docs/tess/LightCurveFile-Object-Tutorial.html) and [MAST archive conventions](https://archive.stsci.edu/missions-and-data/tess/data-products.html).

| Field | Sector 2 | Sector 5 |
|---|---|---|
| Target | TIC 307210830 (L 98-59) | Same target |
| FITS filename | `tess2018234235059-s0002-0000000307210830-0121-s_lc.fits` | `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits` |
| Original FITS bytes | 2,004,480 | 1,923,840 |
| Pipeline header `PROCVER` | `spoc-5.0.11-20200915` | `spoc-5.0.20-20201120` |
| SHA-256 | `516d3ee2210ba33214026ac1255d06e112723c6053f5a33872f457b0526ba8d4` | `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae` |

The Sector 5 SHA matches the one independently archived in AR-OBS001, and both FITS headers confirm the selected TIC and sector. The run used Python **3.12.16**, NumPy **2.5.5**, and Astropy **7.2.4**. The full canonical result payload (without its digest field) has SHA-256 `e4b8460f900d3e61b787598a42d8cced42115adf15d1a1a045a7d09c9c35c9c6`.

The original FITS bytes remain at the public STScI archive and were not committed. The full JSON workflow artifact is subject to GitHub retention; the repository holds a permanent aggregate, source hashes, protocol and executable code for repeatability.

## Prior execution failure preserved

[First execution #44849327441](https://github.com/DevHabito/arara-space-telescope/actions/runs/44849327441) **FAILED for a software reason**: a previously defined identity validator assumed Sector 5 for every FITS product and rejected the correct Sector 2 header. It was not a rejected scientific hypothesis or source-access failure.

The validator was made sector-specific in commit `221f8ff` and a regression test covering both sectors was added in commit `d8d1ae1`. The original protocol, source choices and thresholds were **not** changed. The corrected hosted run passed the ten unit tests and all five verification gates.

## Row-wise result: the two frozen hypotheses

Let `Q` be `QUALITY=0`, and `P` be finite and strictly positive `PDCSAP_FLUX` at the **same cadence**. The full paired 2-by-2 tables are:

| P versus Q | Sector 2 | Sector 5 |
|---|---:|---:|
| `Q and P` | 17,578 | 17,025 |
| `Q and not P` | **0** | **0** |
| `not Q and P` | **0** | **0** |
| `not Q and not P` | 2,159 | 1,919 |

Thus **H1 (Sector 5)** and **H2 (Sector 2)** are both `SUPPORTED_IN_SELECTED_FILE`. This is exact row-wise equivalence for the **two named archived products**, not merely equality of totals. It says nothing about all TESS sectors, other pipeline releases, or the correct physical interpretation of events.

## Other availability differs

| Descriptive quantity | Sector 2 | Sector 5 |
|---|---:|---:|
| Total cadences | 19,737 | 18,944 |
| `QUALITY=0` rows | 17,578 (89.06%) | 17,025 (89.87%) |
| `QUALITY!=0` with finite TIME | 1,121 | 946 |
| `QUALITY!=0` with finite positive SAP flux | 1,043 | 832 |
| `QUALITY!=0` with **paired** finite moment centroids | 1,043 | 832 |
| `QUALITY!=0` with **paired** finite `POS_CORR` columns | 1,043 | 631 |
| Finite PSF centroid rows (each column) | 0 | 0 |

The fraction of zero-flag cadences differs by approximately **0.81 percentage points**. This is a descriptive difference between two observational epochs and pipeline builds, not an estimated effect of a particular instrument failure. Cadences are time-correlated, so treating these counts as independent statistical trials would be incorrect.

The important distinction is that **valid SAP flux and finite centroid observations can still occur when the quality flag is nonzero**, whereas a valid PDCSAP entry did not occur in any nonzero-flagged cadence in either selected product. Using PDCSAP without considering missingness or quality-selection therefore changes the sample available to downstream analysis.

Both products contain PSF centroid column names, but **none** of their values are finite. Availability must be measured rather than assumed from column presence.

The observed quality-bit combinations and their overlaps are archived in the original JSON and the compact aggregate. Flags are not disjoint event categories, and their counts cannot be added to infer a number of distinct physical incidents.

## Interpretation and explicit nonclaims

This audit concerns the **representation and availability of processed TESS measurements**. A strong association between quality masks and PDCSAP availability can arise from pipeline processing. We did **not** infer that quality flags provide independent ground truth for whether a light-curve dip is astrophysical or instrumental.

The source is real TESS data, but this test is not a demonstration of:

- a detected transit, stellar flare, or novel astronomical transient;
- a statistically independent effect of any particular flag;
- the validity of a target-specific instrument diagnostic;
- a new image-subtraction method or improved pipeline;
- ARARA as an operational telescope or validated detector.

The two sectors differ in observing time and `PROCVER`. No cause for the difference in available centroids or quality-bit frequencies was identified in this audit. We did not inspect the target-pixel arrays or fit a time-domain detector.

## Next scientific gate

A future preregistration should retrieve the **public target-pixel file** for one selected sector, verify its SHA and observation alignment, and investigate whether pixel-level information and quality annotations can rule out some **specific** photometric artifacts. Pixel-derived centroids remain statistically dependent on the same photons. A true independent diagnostic, if needed, requires external spacecraft engineering telemetry or a separately justified source.

A class label based solely on the `QUALITY` flag would be circular for assessing astrophysical false positives. Genuine event labels must be established by independently sourced catalog evidence and careful exclusions.

**Final verdict:** H1 and H2 supported in the two selected files; five integrity gates passed. The result documents selection behavior of archived pipeline products and guides the next prospective observation study without making a new-physics or detector-performance claim.
