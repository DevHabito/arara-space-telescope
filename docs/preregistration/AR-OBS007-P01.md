# AR-OBS007-P01 — Does attitude telemetry add information beyond recent pixel motion?

**Prospective registration:** 21 November 2026 (America/Sao_Paulo).  
**Status at registration:** No AR-OBS007 outputs or models inspected.  
**Purpose:** A **necessary-condition benchmark**, not a physical classification or astrophysical signal preservation result. P02 must evaluate preservation separately.

## Falsifiable question

Does contemporaneous TESS attitude information improve out-of-sample prediction of **pixel-photocenter displacements** beyond a stronger, readily available **autoregressive motion baseline**? The preceding AR-OBS006 compared quaternion predictors only with the constant training-mean displacement, which was insufficient to demonstrate incremental utility.

A failure here would substantially weaken the motivation to add these engineering features to ARARA. A success would not prove fault-vs-astrophysical source identification: spacecraft guidance and pixel position share physical and processing dependencies.

## Fixed observational products and hashes

The three public, already audited products of **TIC 307210830 / L 98-59**, TESS **Sector 5**, Camera **4**, CCD **4**:

- `tess2018319095959-s0005-0000000307210830-0125-s_tp.fits` (STScI MAST): SHA-256 `c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b`.
- `tess2018319095959-s0005-0000000307210830-0125-s_lc.fits` (STScI MAST): SHA-256 `a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae`.
- `TessVectors_S005_C4_120.csv` (NASA HEASARC): SHA-256 `2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8`.

Use exact URLs and bounded HTTPS retrieval from AR-OBS003/005. Abort on hash, FITS identity, schema, duplicate cadence or provenance failure. No archive files, cadence-level data or target photon series are committed. Runtime Python 3.12, NumPy 2.x, Astropy 6.x/7.x.

## Fixed measurements and eligibility

Reconstruct per-cadence optimal-aperture photocenters using `APERTURE & 2` and weights `max(FLUX,0)`, exactly as in AR-OBS004/006. Join LC and engineering vectors by **integer CADENCENO**. Require:
- LC and TPF QUALITY=0 with exact quality agreement;
- valid finite TPF/LC TIME and engineering MidTime;
- TESSVectors Quat_NBinned>0; all Quat[1–4]_StdDev finite and nonnegative;
- Quat1_Med, Quat2_Med, Quat3_Med finite;
- valid positive-weight photocenter with all selected pixels finite.

As in AR-OBS006, form Y=(Δcx,Δcy) and Q=(ΔQuat1_Med,ΔQuat2_Med,ΔQuat3_Med) only when source cadence identifiers differ by exactly 1. Then retain a **lagged-motion example** only when that pair and the **two preceding pairs** have consecutive endpoint cadence IDs (so all three differences represent adjacent unbroken intervals). Define A=(Y_(t−1), Y_(t−2)), four autoregressive features; Q remains the three contemporaneous quaternion differences.

Exclude observations with missing source fields; document counts and the **nonrandom QUALITY=0 selection**.

## Split and embargo (no holdout tuning)

Sort eligible lagged-motion examples by actual ending CADENCENO. Compute boundary index `floor(0.60 * N)`; define training examples `[0, boundary−120)`, discard `[boundary−120, boundary+120)` (exactly **240 chronological examples** when enough exist), and test only on `[boundary+120, N)`. The embargo protects against direct sharing of the neighboring cadence/pair at the split and is not a full cure for correlated time series. Require at least **500** training and **500** test examples for any evaluable claim.

No shuffling, hyperparameter tuning, alternative boundaries or seeing the test when choosing features.

## Frozen models and references

Train each using only its training block. For each feature column, use training mean and population standard deviation; zero-variance columns become all zero. Unpenalized intercept is the training outcome mean; fixed ridge penalty **λ=10** on slopes.

Evaluate exactly the same test examples and outcome array for:

1. **MEAN:** constant two-component training-mean displacement.
2. **AR2:** four lagged displacement components, no quaternion.
3. **Q:** three contemporaneous quaternion differences, no autoregression (AR-OBS006-style).
4. **AR2+Q:** combined seven-feature candidate.
5. **AR2+Q_SHIFT97:** identical AR2 features, but quaternion difference rows circularly shifted by **+97 eligible examples**, separately in training and test, preserving block boundaries. Fit a fresh fixed-ridge model on shifted training features; this is a **sanity check only**, not a formal null distribution.

For X and Y separately record test SSE, MAE, R² versus MEAN, and the **incremental gain** `gain_Q = 1−SSE_AR2+Q/SSE_AR2`. Negative gain must be preserved. For shifted control compute `gain_shift = 1−SSE_AR2+Q_SHIFT97/SSE_AR2`. Zero SSE_AR2 or insufficient split size means `NOT_EVALUABLE`.

## Frozen decisions

- **H1 (X incremental value):** `gain_Q_x>=0.05` **and** `gain_Q_x−gain_shift_x>=0.03`.
- **H2 (Y incremental value):** same conditions on Y.
- **H3 (shift sanity):** both `gain_shift_x<=0.02` and `gain_shift_y<=0.02`.

Return `SUPPORTED_IN_SELECTED_PRODUCTS`, `NOT_SUPPORTED_IN_SELECTED_PRODUCTS`, `NOT_EVALUABLE` or, if an integrity gate fails, `INCONCLUSIVE_ACCESS_OR_SCHEMA`. All outcomes, including negative gains, are scientific results; no threshold changes after the run.

## Integrity gates and interpretation

**G1** verified original hashes; **G2** FITS/CSV identity and schema; **G3** valid exact joins, lag eligibility accounting and chronological embargo; **G4** no test-derived normalization/fitting, fixed model and correct SSE/gain accounting; **G5** deterministic compact JSON with runtime, hashes, counts, outcomes and canonical SHA-256 (excluding digest field). A failed gate is **not** a negative scientific finding.

**Scope boundaries:** This is one target and sector, selected `QUALITY=0` cadences, and **contemporaneous** engineering information, not a prediction made before it is observed. An R², even on holdout, is not proof of sensor independence, cause attribution, event discrimination, novel method or signal preservation. The relevant next protocol, **AR-OBS007-P02**, must measure astrophysical-signal recovery with a fixed synthetic-injection challenge grounded in real photometry, and must state the assumption that injected events are not independently observed astronomical detections.

Relevant prior public methods:
- [EVEREST / Luger et al. (2016)](https://doi.org/10.3847/0004-6256/152/4/100) — pixel decorrelation and injection/recovery.
- [QLP Data Release Notes 002 (2022)](https://arxiv.org/abs/2211.04387) — quaternion-assisted TESS detrending.
- [NASA TESS noise removal overview](https://heasarc.gsfc.nasa.gov/docs/tess/NoiseRemovalv2.html).

**Registration boundary:** No P01 observational values have been computed yet.
