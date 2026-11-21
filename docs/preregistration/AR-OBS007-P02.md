# AR-OBS007-P02 — Do quaternion-assisted pixel detrenders preserve injected astrophysical dips?

**Prospective registration:** 21 November 2026 (America/Sao_Paulo).  
**Status at registration:** No AR-OBS007-P02 corrected light curves, injection scores or performance outcomes inspected.  
**Scientific scope:** *Necessary-condition synthetic injection/recovery stress test on real TESS photometry*. It is **not** a test of a real astrophysical label or of an instrument-fault classifier. It is separate from P01's centroid-motion prediction.

## Question and competing methods

Can adding **engineering quaternion covariates** to a basic pixel-level decorrelation model reduce held-out short-timescale photometric variability, **without measurably reducing the depth of a fixed, injected dimming signal**? A stronger method should satisfy *both* conditions, not simply produce a smoother curve.

The methods are bounded, simple approximations — **not** full implementations of the SPOC, QLP or EVEREST pipelines:

1. **RAW:** original calibrated TESS `SAP_FLUX`, normalized to a fixed training-sample median, with no correction.
2. **PLD1:** fixed-penalty ridge linear regression of normalized SAP flux against the 21 aperture-pixel fractions `FLUX[p] / sum(FLUX[aperture])` (a basic first-order pixel-level decorrelation reference).
3. **PLD1_Q:** the same model plus the `Quat1_Med`, `Quat2_Med`, `Quat3_Med` from camera-4 TESSVectors.
4. **PLD1_Q_SHIFT97:** identical PLD fractions plus quaternion feature rows circularly shifted by +97 within training and test blocks **separately**; a limited negative control, not a formal null.

The model is neither a production pipeline nor a novel decorrelator. The PLD regressors are derived from the same science pixels, and quaternion medians may share upstream camera guidance. Engineering covariates are **contemporaneous**, not a causal future forecast.

## Frozen public sources

Use only previously audited **TIC 307210830 (L 98-59), TESS Sector 5, Camera 4, CCD 4**:
- MAST TPF `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits` SHA-256 `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b`.
- MAST LC `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits` SHA-256 `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
- HEASARC 120-sec TESSVectors CSV `TessVectors_S005_C4_120.csv` SHA-256 `2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8`.

Use source URLs, bounded HTTPS readers, FITS identity checks and unique exact cadence joins already validated in AR-OBS003/005. Keep all FITS, CSV, pixel fractions, source time series and individual injection outcomes ephemeral. Commit only compact aggregate reports, SHA-256s, preregistration and executable code.

## Fixed eligibility and split

Use the published `APERTURE & 2 != 0`, exactly **21** photometric pixels. Include a cadence only if:
- quality flags are exactly zero in TPF and LC, their integer cadence IDs match, and both times are finite;
- all 21 calibrated TPF `FLUX` pixel values finite, their sum positive, and positive finite LC `SAP_FLUX`;
- reconstructed SAP pixel sum differs by at most 0.001 relative from LC SAP;
- the matching engineering row has finite `MidTime`, `Quat_NBinned>0`, all four quaternion standard deviations finite nonnegative, and all three medians finite.

Sort by exact CADENCENO. Compute `boundary=floor(0.60*N)`; training includes indices `[0,boundary-120)`, hold out indices `[boundary+120,N)`, and discard exactly **240** eligible indices around the split. Require at least 500 training and 500 test rows. All models share the exact eligible rows.

Normalize SAP by the **unmodified training** median `S0` and subtract 1. This scalar is fixed in both paired worlds. For every candidate, center and standardize regression features using only its training block (zero-variance features set to zero), fit a ridge linear model with unpenalized intercept and frozen `lambda=10`. No feature selection, transit masking or tuning based on test outcomes.

## Primary held-out noise proxy — no injected data

For each method, subtract its predicted normalized trend from original normalized SAP. On the test block **only**, form first differences of its residuals at pairs with consecutive exact integer cadence IDs, and compute the **root mean square of those first differences**, without outlier rejection or fitting. Report the number of eligible test pairs, each method's point-to-point RMS and the fractional **squared-RMS reduction**

`gain_Q=1−RMS(PLD1_Q)^2/RMS(PLD1)^2`;

`gain_shift=1−RMS(PLD1_Q_SHIFT97)^2/RMS(PLD1)^2`.

This is only a **short-timescale variation proxy**; real stellar variability or transits may contribute to it. A smaller value alone is not proof of improved astronomy or removal of an instrumental signal.

## Frozen synthetic-injection challenge — paired worlds

For training and test **independently**, enumerate candidate starts at block-local index `250 + 500*k` for k≥0, and use only those for which the full **12-cadence event** plus **12 cadences on either side** have exact consecutive source cadence IDs. The event is `[start,start+12)`; fixed multiplicative depth **d=0.005** (0.5%) for all selected calibrated aperture pixels. No injection timing or location is chosen based on measured flux, quaternions or performance.

This deliberately idealized *common-mode aperture dimming* rescales **all 21 selected pixel fluxes** by exactly `1−d`, and therefore also rescales their total SAP flux by `1−d`. The normalized PLD pixel fractions are **algebraically invariant** under this injection, which is an important limitation: in real blended scenes, planet transits do **not** necessarily multiply all observed aperture photons by the same factor. Do not claim this reproduces a physical star/planet PSF perfectly.

Create paired worlds for each method: **original SAP** and **SAP plus these multiplicative synthetic dips**. Fit a separate model on the original training block and on the injected training block, applying the corresponding frozen models to the original or injected holdout respectively. Engineering measurements are unchanged by the synthetic injection. Recompute PLD fractions from rescaled pixels conceptually / verify within numerical tolerance that they remain invariant; do not reuse adjusted source pixels as astrophysical truth.

For each preselected held-out injection, compute the difference `D = residual_injected − residual_original`. Estimate the recovered depth by subtracting the mean D in the 24 flanking cadences from its mean in the 12 event cadences, then dividing the negative difference by `d * mean(original_SAP/S0 within the event)`. This **difference-of-differences** cancels natural source variability without assuming the real star has no transits.

Report every method's **median** recovered fraction and median absolute deviation from 1 over held-out events, and number of eligible injected events in training and test. Do not suppress individual failures or retune locations. Require at least **3 valid test events** and **3 training events** for an evaluable verdict.

## Frozen refutable hypotheses

- **H1 — incremental short-timescale precision:** PLD1_Q reduces *squared* point-to-point RMS by **at least 5%** over PLD1 and improves by at least **3 percentage points** over PLD1_Q_SHIFT97 on the same held-out original observations.
- **H2 — injection preservation:** PLD1_Q median recovered depth is in **[0.95, 1.05]** and is at least `(PLD1 median recovered depth − 0.03)`. This is a **noninferiority check on the idealized injection**, not proof of real-planet signal recovery.
- **H3 — shifted-control sanity:** PLD1_Q_SHIFT97 improves squared-RMS by at most **2%** relative to PLD1.

Every H is `SUPPORTED_IN_SELECTED_PRODUCTS`, `NOT_SUPPORTED_IN_SELECTED_PRODUCTS`, or `NOT_EVALUABLE`. A failure is preserved, not fixed by changing thresholds. No p-values or significance claims.

**Integrity G1–G5:** pinned original archive SHA; verified FITS/CSV identities, schema and positive optimal aperture; exact unique-key join, quality selection and full 240-row embargo; training-only fitting, fixed injection schedule, event/flank accounting and deterministic metrics; compact JSON with input hashes, source/runtime details, all verdicts and canonical payload SHA. Any integrity failure leaves all hypotheses `INCONCLUSIVE_ACCESS_OR_SCHEMA`, not a negative scientific finding.

## A deliberate non-identifiability counterexample

An alternative **target-local throughput loss** modeled as exactly the same 0.5% multiplicative change to all selected pixels, with the same unchanged engineering records, would generate identical observable inputs to this idealized astrophysical dimming. The two different *labels* would be observationally indistinguishable in this simplified setting. This is an **algebraic counterexample**, already familiar in statistical identifiability; no detector-accuracy result or novel theorem is claimed. To distinguish physical causes in real data we need genuinely independent event evidence or distinct calibrated signatures.

## What this test can and cannot establish

It can reject the practical idea that adding the chosen three quaternion medians to a simple PLD correction improves held-out short-timescale precision; it can also reject the proposition that the resulting correction preserves *this specified* artificial dimming.

It **cannot** establish real instrumental fault-versus-astronomical classification, causal independence, novel astrophysical detection, production-pipeline superiority or robust detection of actual planet transits. It uses only quality-zero observations of **one** star in **one** sector, and its injection construction is intentionally easy for first-order PLD. A future study must compare with **real, separately documented instrument events and externally established astrophysical events** across held-out targets/sectors, with physical pixel forward models and stronger established pipelines.

Relevant public predecessors:
- [Luger et al., EVEREST (2016)](https://doi.org/10.3847/0004-6256/152/4/100), pixel decorrelation and transit injection/recovery.
- [NASA TESS PLD/noise removal documentation](https://heasarc.gsfc.nasa.gov/docs/tess/NoiseRemovalv2.html).
- [QLP release notes on quaternion corrections (2022)](https://arxiv.org/abs/2211.04387).

**Status at registration:** no P02 outcomes observed, hypotheses frozen.
