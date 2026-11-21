# AR-OBS005-P01 — TESS engineering-vector cadence and time-frame audit

**Recorded:** 20 November 2026 (America/Sao_Paulo).  
**Evidence type:** Public TESS engineering-product and photometric-product **access, identity, completeness and timing** audit. It does not search for events or identify physical faults.  
**Frozen before engineering data inspection:** [AR-OBS005-P01](../preregistration/AR-OBS005-P01.md), commit `5745e44be8f66eace181cafec62c69b3a0d7f198`.  
**Implementation:** [scripts/ar_obs005_tessvectors_alignment.py](../../scripts/ar_obs005_tessvectors_alignment.py).  
**Unit tests:** [tests/test_ar_obs005_tessvectors_alignment.py](../../tests/test_ar_obs005_tessvectors_alignment.py); **10 passed** on Python 3.12.16.  
**Primary execution:** [GitHub Actions run #44852568159](https://github.com/DevHabito/arara-space-telescope/actions/runs/44852568159).  
**Permanent output:** [AR-OBS005-P01.json](AR-OBS005-P01.json).  
**Original workflow artifact:** [#14685872879](https://github.com/DevHabito/arara-space-telescope/actions/runs/44852568159/artifacts/14685872879), subject to GitHub artifact retention.

## Why this source matters

Earlier work (AR-OBS003/004) reconstructed the SAP flux from the same target pixels and found a strong within-product association between positive-weight pixel-photocenter steps and SPOC `POS_CORR` shifts. Neither comparison supplied independent fault labels.

AR-OBS005 introduces a separate **public engineering-vector product** rather than assuming another TPF/LC column is independent telemetry. The TESSVectors project derives camera-level engineering products by resampling quaternion and Earth–Moon measurements onto science cadences. These vectors have a distinct data-product provenance, but the TESS pointing-control system itself can use science-camera measurements. **Distinct files do not imply independent physical evidence.**

## Frozen source provenance

| Item | Engineering vectors | SPOC light curve |
|---|---|---|
| Selected file | `TessVectors_S005_C4_120.csv` | `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits` |
| Provider | NASA HEASARC TESSVectors archive | STScI MAST TESS archive |
| Byte length | **9,386,675** | **1,923,840** |
| Original SHA-256 | `2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8` | `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae` |

The engineering CSV is at `https://heasarc.gsfc.nasa.gov/docs/tess/data/TESSVectors/Vectors/120_Cadence/TessVectors_S005_C4_120.csv`. The light curve is at `https://archive.stsci.edu/missions/tess/tid/s0005/0000/0003/0721/0830/tess2018319095959-s0005-0000000307210830-0125-s_lc.fits`.

SPOC FITS headers confirm **TIC 307210830**, **Sector 5**, **Camera 4**, **CCD 4**. The vector CSV's source identity is established by the selected provider path and file name; **it does not include independent `Sector` or `Camera` columns** to cross-check row by row. This limitation must be retained rather than fabricating a header check that the CSV cannot support.

Runtime: Python **3.12.16**, NumPy **2.5.5**, Astropy **7.2.4**. The input CSV contained **41 preamble lines** before its actual data header, which the strict parser handled without treating explanatory lines as observations.

The canonical JSON payload's SHA-256 (excluding the self-digest field) is `ac924ec3c5b05010202d7fc60a0e4cb1e41a14ad93d5b01e68e2655c4ad2aa35`; it was recomputed independently from the downloaded workflow artifact and matched.

## H1 — cadence coverage: supported

| Measurement | Observed |
|---|---:|
| SPOC LC rows | **18,944** |
| TESSVectors rows | **17,971** |
| Rows joined by exact integer cadence ID | **17,971** |
| TESSVectors without matching LC cadence | **0** |
| LC rows without engineering cadence match | **973** |
| LC rows with finite `TIME` | **17,971** |
| Matched rows with finite LC and vector time | **17,971** |

All **17,971 LC rows with finite `TIME`** had a corresponding engineering `Cadence` with finite `MidTime`. Thus coverage of the *finite-time LC population* was **100%**, exceeding the frozen 95% criterion.

The 973 unmatched LC rows correspond to the non-finite-time portion of this particular LC, by count conservation. They must **not** be used for a timing comparison or silently filled by interpolation. The 100% figure must never be misrepresented as 100% of all 18,944 source rows.

**H1 = SUPPORTED_IN_SELECTED_PRODUCTS.**

## H2 — clock-frame compatibility: supported

TESSVectors documents `MidTime` as an exposure midpoint without barycentric correction. For every matched finite-time cadence, the frozen protocol computed

`((LC.TIME - LC.TIMECORR) - Vector.MidTime) * 86400` seconds.

| Measure | Difference |
|---|---:|
| Matched finite comparisons | **17,971** |
| Median signed difference | **−0.4400000573 s** |
| Median absolute difference | **0.4400000573 s** |
| 95th-percentile absolute difference | **0.4400000573 s** |
| Maximum absolute difference | **0.4400000573 s** |

No constant offset was fitted or removed, and no timestamps were adjusted after seeing the output. The magnitude is consistent with the documented CCD-readout time staggering: TESSVectors's midpoint is benchmarked to **CCD1**, while this light curve is from **CCD4**. This consistency is an interpretation, **not** an independent calibration or proof of the physical cause of the offset.

The median (<=2 s) and 95th percentile (<=5 s) both meet the fixed tolerances.

**H2 = SUPPORTED_IN_SELECTED_PRODUCTS.**

## H3 — usable engineering quaternions: supported

A row was defined as having engineering availability only when `Quat_NBinned > 0` and all four quaternion standard deviations were finite and nonnegative. They were neither interpolated nor interpreted as physical event labels.

| LC quality / engineering availability | With quaternion measurements | Without |
|---|---:|---:|
| `QUALITY=0` | **17,025** | **0** |
| Nonzero LC quality | **945** | **1** |

Total matched rows with full engineering availability: **17,970 of 17,971**. Median number of quaternion samples binned among available rows: **60**.

All 17,025 matched rows with zero quality flags meet the availability rule, exceeding the predeclared 50% requirement. However, **945 quality-flagged rows also retain available engineering vectors**. Availability is **not** a truthful classifier for good versus bad astronomy, and the one flagged cadence lacking complete engineering information must not be imputed.

**H3 = SUPPORTED_IN_SELECTED_PRODUCTS.**

## Verification and limitations

All **five integrity gates G1–G5 passed** in the hosted Python 3.12 run, together with the **10 synthetic tests**. The ten unit tests separately check provenance constants, CSV preamble parsing, duplicate cadence rejection, invalid quaternion counts, exact integer-key joins despite row shuffling, time offsets, missing-data handling and both supported/rejected verdicts.

This evidence supports only a **traceable join and timing/availability contract** for the selected products. It does not establish that quaternion-derived features can distinguish instrumental glitches from transits or stellar variability. The vectors have been processed and resampled to the science cadence, may share upstream camera measurements, and carry no independently verified astrophysical ground-truth labels.

A meaningful next step would require a **separately registered comparison** of engineering-vector changes with the already defined pixel-motion measurements, with safeguards against shared-source coupling and temporal autocorrelation. Even successful correlations would not be detector validation. A subsequent external-event reference would be needed to evaluate classification or causality.

No private scientific correspondence is quoted or attributed here. No FITS bytes, engineering time series, or raw target photometry were committed. Existing M38B calibration and holdout gaps remain open.

## Public source references

- TESS Guest Investigator Program, [TESSVectors](https://github.com/tessgi/tessvectors) and [Sector 5, camera 4 vector file index](https://heasarc.gsfc.nasa.gov/docs/tess/data/TESSVectors/Vectors/120_Cadence/).
- MAST, [TESS Data Products](https://archive.stsci.edu/missions-and-data/tess/data-products).
- MAST, [TESS Instrument Handbook](https://archive.stsci.edu/missions-and-data/tess), for the fine-pointing camera dependence.

**Scientific boundary:** AR-OBS005 establishes additional observational provenance, not an identified mechanism, novel algorithm or new detection capability.
