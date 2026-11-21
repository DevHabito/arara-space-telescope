# AR-OBS004-P01 — Pixel morphology, pointing proxies, and flagged background

**Registered:** 20 November 2026 (America/Sao_Paulo)  
**Stage:** Prospective observational protocol. The implementation and outcomes must be committed after this document.  
**Parent evidence:** AR-OBS003-P01, which reconstructed the published SAP light curve from the same calibrated target pixels. The parent is a provenance check, **not** a physical event classification.

## Research question

When the apparent spatial distribution of light changes within the fixed TESS aperture, do its *frame-to-frame* displacement measurements co-vary with the archive's position-correction columns? Does the archive's scattered-light quality flag select different reported background levels?

We test descriptive consistency of **dependent pipeline measurements**, not whether a specific dimming is instrumental or astrophysical. Neither source classification nor physical event recovery is attempted. The quality annotations are not independent ground-truth labels.

## Frozen source, prior to reading new metrics

Use exactly the SPOC two-minute **TIC 307210830 / L 98-59**, **Sector 5** products already audited:

- `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits`
- `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`
- Directory: `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/`
- Frozen TPF SHA-256: `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b`
- Frozen LC SHA-256: `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`

Use the bounded STScI HTTPS download logic from AR-OBS003 (128 MiB per product, per-read 120 s), temporary FITS storage, Python 3.12, NumPy 2.x and Astropy 6.x/7.x. Verify both file checksums, target/sector header identity, exactly matching TPF/LC cadence IDs, nonnegative integer quality bits, and the expected `FLUX`, `FLUX_BKG`, `POS_CORR1`, `POS_CORR2`, `TIME`, `CADENCENO`, `QUALITY` and 2-D `APERTURE` fields. Do **not** substitute a different star, sector, aperture, file revision or event.

For orientation: MAST's target-pixel file description explains that `FLUX_BKG` is an estimated per-pixel background, while `POS_CORR1/2` are local motion corrections from pipeline motion polynomials; see [MAST TESS pixel tutorial](https://spacetelescope.github.io/mast_notebooks/notebooks/TESS/beginner_tour_lc_tp/beginner_tour_lc_tp.html) and [TESS Science Data Products Description](https://ntrs.nasa.gov/api/citations/20205008729/downloads/EXP-TESS-ARC-ICD-TM-0014-Rev-F_v2.pdf). Quality bit 6 refers to a reaction-wheel desaturation event, while bit 13 is a scattered-light exclusion; see [TESS quality bits](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview). Neither flag proves an astrophysical cause. Bit 13 can itself be set based on background estimates: an association of this flag with background is **selection by construction**, not independent confirmation.

## Frozen measurement rules

**Photocenter from pixels (descriptive only).** Take only the `APERTURE & 2 != 0` pixels selected by the SPOC photometric mask. At each cadence require every selected `FLUX` value finite. Define per-pixel nonnegative weights `w = max(FLUX,0)`; require `sum(w)>0`. Use local integer pixel coordinates `(x,y)` with image origin `(0,0)` and compute:

`c_x = sum(w*x)/sum(w)`; `c_y = sum(w*y)/sum(w)`.

Record the number of finite/positive-weight photocenters; do not equate this positive-clipped photocenter with the SPOC's exact `MOM_CENTR` algorithm. The centroid depends on the same photons as the aperture flux. A centering method with signed or background-adjusted weights would be a **different experiment**, not a post hoc adjustment here.

**Pointing-proxy sample.** Align records by exact integer `CADENCENO`. Define usable rows as `QUALITY == 0`, finite `TIME`, finite `POS_CORR1` and `POS_CORR2`, and valid `c_x,c_y`. Form differences **only** when two successive source rows both meet all those conditions and their integer cadence numbers differ by exactly one. For each consecutive pair, compute `dc_x,dc_y,dPOS_CORR1,dPOS_CORR2`. Do not smooth, detrend, threshold large excursions, regress on the target's flux, or remove outliers.

Compute Pearson correlation `r0_x = corr(dc_x,dPOS_CORR1)`, `r0_y = corr(dc_y,dPOS_CORR2)` across the exact eligible pair set. A correlation is undefined if a series has zero variance or there are fewer than 100 pairs; record `NOT_EVALUABLE` in that case. Compute a **fixed, nonphysical negative control** by pairing the same `dc` differences with the *24-position cyclically shifted* `dPOS_CORR` sequence in the eligible-pair order (`np.roll(...,24)`). This shift is not a realistic null distribution and does not correct for autocorrelation; it tests whether a same-position co-variation exceeds a deliberately misaligned comparison.

**Estimated-background sample.** Select the pixels marked by `APERTURE & 4 != 0` (a separate pixel-mask role); require at least one such pixel. Per cadence require all of their `FLUX_BKG` values finite, then take the per-cadence **median** (e-/s). Compare this estimated-background distribution for **all** rows with `QUALITY==0` against rows with **bit 13 set** (regardless of other flags). Report group sizes, medians, median difference, and the fraction of each group with finite background. Also record usable counts for **bit 6** as a descriptive reference. Because flag groups may overlap and are not independent samples, do not claim a p-value, uncertainty interval, or causal effect.

## Frozen hypotheses and verdict rules

- **H1 — x displacement consistency:** at least **100** eligible consecutive pairs, `abs(r0_x)>=0.20`, and `abs(r0_x)-abs(rshift24_x)>=0.10`.
- **H2 — y displacement consistency:** same criteria on `dc_y` versus `dPOS_CORR2`.
- **H3 — flagged-background selection check:** at least **30** finite `FLUX_BKG` measurements among bit-13 rows and at least **100** among `QUALITY==0` rows, with the bit-13 median background **greater than** the zero-flag median.

Each hypothesis is `SUPPORTED_IN_SELECTED_PRODUCT`, `NOT_SUPPORTED_IN_SELECTED_PRODUCT`, or `NOT_EVALUABLE` if required values are absent. Failure is a valid result, not a reason to modify thresholds or select a better-looking sample. H3 is a **pipeline selection sanity check**, explicitly not independent scientific discovery.

**G1–G5 integrity gates**, distinct from hypotheses: two pinned source hashes and identity pass; schema and pixel-mask checks pass; cadence alignment and eligible-pair accounting conserve all counts; correlations and background medians are computed only from the frozen masks and finite values; compact JSON includes versions, counts, hypotheses, complete SHA-256 provenance and a canonical-payload digest. If a gate fails, preserve the error and mark all hypotheses `INCONCLUSIVE_ACCESS_OR_SCHEMA`.

## Scientific scope and follow-up

The derived pixel photocenter and POS_CORR estimates may share instrumental information and processing assumptions. Correlation cannot show that POS_CORR is an independent sensor. Neither does association of bit 13 and background imply new knowledge when bit 13 is defined using background. No per-cadence light curves, pixel data, private correspondence or identifiable scientist contacts are committed.

The next distinct gate, after reviewing this audit, would require **external event provenance** and a separately frozen evaluation: e.g. known spacecraft pointing events from mission operations and known astronomical variations from independently justified catalogs, with source/instrument confounds controlled. Repeating this correlation on the same object does not create ground truth.

**Status at freeze:** no new AR-OBS004 measurements have been inspected or executed.
