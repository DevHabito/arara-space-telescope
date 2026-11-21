# AR-OBS007-P02 — Photometric correction and idealized transit-dip preservation

**Recorded:** 21 November 2026 (America/Sao_Paulo).  
**Study class:** Real archived TESS photometry with **synthetic common-mode pixel injections**, not a detection of real exoplanet transits or true instrument-fault labels.  
**Protocol frozen before code and outcomes:** [AR-OBS007-P02](../preregistration/AR-OBS007-P02.md), commit `6635ead84515ba243e7c104c944bc188dcc393d3`.  
**Implementation:** [scripts/ar_obs007_injection_preservation.py](../../scripts/ar_obs007_injection_preservation.py).  
**Unit tests:** [tests/test_ar_obs007_injection_preservation.py](../../tests/test_ar_obs007_injection_preservation.py): **13 PASS** on Python 3.12.  
**Real-source execution:** [GitHub Actions run #44901988014](https://github.com/DevHabito/arara-space-telescope/actions/runs/44901988014); compact original artifact [#14706198105](https://github.com/DevHabito/arara-space-telescope/actions/runs/44901988014/artifacts/14706198105).  
**Permanent complete numerical output:** [AR-OBS007-P02.json](AR-OBS007-P02.json).

## Why a second benchmark was necessary

AR-OBS007-P01 found that quaternions can improve prediction of **photocenter displacement** beyond a two-lag motion baseline, on a chronological holdout. This is evidence of incremental *instrumental-motion information*, but it does not prove those regressors improve a light curve or preserve transit-like variations.

P02 tests those two necessary conditions separately, with the outcome **SAP photometry** rather than the pixel centroid. It compares **first-order PLD** (21 normalized aperture-pixel fractions) with the same simple ridge corrector augmented by three contemporaneous engineering quaternion medians, under the same 240-example temporal embargo. The published algorithms PLD, EVEREST and QLP already use related ideas: none of the P02 approximations is claimed to be a new method or a complete reproduction of the published pipelines.

## Source and reproducibility

All three archival products are identical to the fixed inputs of AR-OBS007-P01: TESS **L 98-59, TIC 307210830, Sector 5, Camera 4, CCD 4**, SPOC TPF/LC and NASA HEASARC TESSVectors camera-4 CSV. Their original SHA-256 digests and byte lengths are preserved in [the compact result JSON](AR-OBS007-P02.json). FITS/CSV bytes, pixel time series and individual injection vectors were not added to GitHub.

- Python **3.12.16**, NumPy **2.5.5**, Astropy **7.2.4**.
- The original workflow JSON payload digest, independently verified from its downloaded artifact: SHA-256 `be68c1ee73e750fb5f0560b27487d19727cad7574b12508b5da4b4e53b7549f7`.
- The original TPF aperture of **21 optimal pixels** reconstructed LC SAP with maximum relative difference **1.2027552×10⁻⁷**, below the frozen 0.001 tolerance.
- **17,025** source cadences met the fixed quality-zero, pixel, SAP, timing and engineering eligibility rules.
- **10,095** training cadences; **240** embargo cadences; **6,690** untouched held-out cadences; **6,684** consecutive valid held-out pairs for the short-timescale scatter proxy.

All **five integrity gates G1–G5 passed**, separately from the scientific hypothesis decisions.

## H1 — does adding quaternions measurably improve the photometry?

The frozen reference is a deliberately **simple first-order PLD ridge model (PLD1)**, *not* full EVEREST or SPOC. For each method we computed the RMS of first differences of corrected, normalized SAP on the same held-out consecutive cadences, with no clipping or event selection.

| Corrector | Held-out point-to-point RMS of normalized SAP differences |
|---|---:|
| RAW / no correction | **0.00113989956** |
| PLD1 only | 0.00114120800 |
| PLD1 + quaternion medians | **0.00113145193** |
| PLD1 + quaternion medians shifted 97 entries | 0.00113491284 |

Adding quaternion information lowered the *squared* point-to-point RMS by **1.7025% relative to PLD1**, versus **1.1002%** for the deliberately shifted control. The additional margin over the shifted control was therefore only about **0.6023 percentage points**, below the preregistered **3-percentage-point** requirement. The total incremental gain was also below the preregistered **5%** minimum.

**H1 = NOT_SUPPORTED_IN_SELECTED_PRODUCTS**. We did **not** change the thresholds, shift amount, target or model after observing this negative result.

The simple PLD1 comparator, on these data and settings, also performed **slightly worse than the raw SAP** according to this particular point-to-point metric. This cannot be extrapolated to production PLD, EVEREST or SPOC pipelines, whose training, trend modeling and model selection are much more sophisticated.

**H3 = SUPPORTED_IN_SELECTED_PRODUCTS**, as the +97 shifted control produced less than 2% squared-RMS improvement relative to PLD1. However, the shifted model also produced a small improvement. The single circular shift is not a valid statistical null distribution and cannot establish the physical origin of the observed variance.

## H2 — are our injected astrophysical-like dips retained?

The frozen challenge multiplies **all 21 selected background-subtracted aperture pixels** by `1 − 0.005` over 12 uninterrupted cadences in each selected window. This is an **idealized all-pixel common-mode dimming**, not a full stellar PSF transit forward model.

- **16** injection windows in training; **12** untouched held-out injection windows, chosen without inspecting flux extrema.
- Depth: **0.5%**; duration: **12 cadences**; 12 flanking cadences on each side.
- Original and injected worlds are fitted separately, with the **same unmodified training median** as their normalization anchor.
- The normalized first-order PLD pixel fractions change by at most **8.3267×10⁻¹⁷** under the idealized injection — effectively **invariant by construction**.
- Recovery is a difference-of-differences of corrected injected versus corrected original flux, normalized by the known injected depth. This cancels preexisting real-star variability rather than assuming the field is event-free.

| Method | Median recovered depth fraction over 12 test events |
|---|---:|
| RAW | 1.00000000 |
| PLD1 | **0.99991081** |
| PLD1 + quaternions | **0.99998260** |
| Shifted-quaternion control | **1.00006083** |

The PLD1+quaternion median recovery was **99.99826%** of the synthetic injected depth and did not fall below the frozen 95% or noninferiority-to-PLD1 conditions.

**H2 = SUPPORTED_IN_SELECTED_PRODUCTS.**

The result's **strength is narrow**: a uniform scaling of every selected pixel leaves PLD fractions unchanged algebraically. This injection design therefore makes transit-like recovery **easy by construction**, and the high score is *not* evidence that these correctors will preserve real transits from a source whose PSF is blended, nonuniform, displaced, or otherwise different from a common-mode aperture attenuation.

A more realistic star-specific forward model and independently documented transits are necessary before applying that claim to nature.

## An important identifiability limitation

In the same simplified observation model, a **local detector throughput loss** that multiplies exactly the same selected pixels by 0.995 and leaves the engineering records unchanged produces **exactly the same observable arrays** as the artificial astrophysical common-mode dimming. No classifier seeing only these arrays can distinguish those two physical labels. This is an elementary model-level ambiguity, **not** a new theorem or evidence that real detector faults necessarily imitate real transits so exactly.

The logical obstruction must be resolved through different calibrated signatures or genuinely independently informative measurements; adding more processing of the same indistinguishable input cannot solve it.

## Combined P01 + P02 scientific verdict

- **P01:** Quaternion features showed a **positive incremental improvement in held-out centroid displacement** beyond a stronger AR2 history baseline, in one sector.
- **P02:** Adding the same general engineering data family to a simple pixel-based flux corrector **did not meet our predeclared improvement criterion** for held-out short-timescale variability, despite preserving an idealized synthetic common-mode dip.

**Therefore, incremental motion information does not currently imply demonstrated, scientifically useful photometric improvement or reliable physical event attribution.** The result makes this limitation empirically concrete and preserves the original claim boundary.

## Required future evidence

A real origin-discrimination study must:
1. Use physical-event labels established **outside** the light-curve/quality metrics used by the candidate detector, including credible astrophysical events and documented instrumental anomalies.
2. Use a **target/source-specific pixel-level injection model** (not uniform aperture dimming) and compare with full published correction pipelines rather than only first-order PLD.
3. Freeze multiple targets and sectors **before** examining their held-out outcomes, with instrument and source configuration differences represented.
4. Measure separate astrophysical-signal retention, false instrumental-attribution rates, missed artifacts and calibrated abstention rates.

No current P02 result establishes a new detector, validated spacecraft fault attribution, superiority over the state of the art, or closure of the historical M38B independent-calibration gap.

## Established literature context

- [Luger et al. (2016), EVEREST](https://doi.org/10.3847/0004-6256/152/4/100): pixel-level decorrelation, cross-validation, injection/recovery and astrophysical signal preservation considerations.
- [NASA TESS PLD overview](https://heasarc.gsfc.nasa.gov/docs/tess/NoiseRemovalv2.html): first-order pixel decorrelation and systematics.
- [QLP Data Release Notes 002 (2022)](https://arxiv.org/abs/2211.04387): quaternion-assisted TESS photometric detrending.
- [MAST TESS data products](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview): recorded quality flags and their non-independent processing meaning.

Private scientific correspondence is neither quoted nor attributed. No outside scientist is represented as a contributor or reviewer of this work.
