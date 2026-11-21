# ARARA — Scientific novelty and falsification decision after AR-OBS007

**21 November 2026.** Internal research decision record. Based on the public repo's existing synthetic protocols (AR-RQ1-P01/P02), the observational records AR-OBS001–006, and the new preregistered AR-OBS007-P01/P02 outcomes. Not a peer review or a systematic literature review.

## Decision

**A genuine technical result has been demonstrated: instrument-attitude data provided incremental within-sector information about pixel motion beyond a recent-motion baseline. A corresponding scientifically useful photometric advantage and a reliable physical event-attribution method have not been demonstrated.**

The two new studies were designed to make that distinction refutable rather than treating improved correlation as proof of a detector.

### Evidence ledger

| Claim | Evidence | Scientific status |
|---|---|---|
| Exact archival product access, selected-file hashes and reproducible join of TPF/LC/engineering cadence | AR-OBS001–005 | Verified product-level provenance; established techniques |
| Contemporaneous quaternion differences improve one target's photocenter motion prediction over the constant mean | AR-OBS006 | Positive, selected-sector holdout; weak original baseline |
| Quaternions improve pixel movement prediction **beyond an AR2 recent-motion baseline** with a 240-example temporal embargo | [AR-OBS007-P01](../results/AR-OBS007-P01.md): incremental held-out SSE reduction **15.72% X / 10.67% Y** | Positive **narrow empirical finding**, not demonstrated novelty |
| Quaternions improve a simple first-order PLD correction's held-out short-timescale photometric variance by the prespecified **5%** minimum | [AR-OBS007-P02](../results/AR-OBS007-P02.md): **1.70%** observed; shifted control **1.10%** | **Not supported**; also fails the prespecified 3-percentage-point control margin |
| The same simple PLD+quaternion model preserves a fixed **uniform 0.5% aperture-flux injection** | P02: median recovery **99.998%** across 12 held-out events | Supported in this **idealized, nearly invariant** injection model only |
| These results identify physical instrument failures separately from true astrophysical dimming | No independent physical-event truth labels or physical source-specific injection | **Not tested**; no scientific claim |
| The algorithm improves a published production TESS pipeline or demonstrates a new detection method | No head-to-head production baseline, cross-target/sector transfer or independent holdout | **Not demonstrated** |
| A local throughput change and an equally shaped artificial source dimming are distinguishable if they produce identical pixel+engineering arrays | Elementary paired-observation equivalence in prior AR-RQ1 simulations and current idealized injection | **Impossible in that stipulated model; known identifiability principle, not novel** |

### How the literature constrains originality

- [QLP Data Release Notes 002 (2022)](https://arxiv.org/abs/2211.04387) already documents engineering quaternion-assisted detrending of TESS light curves. Thus *using quaternions* cannot be claimed as a new idea.
- [Luger et al., EVEREST (2016)](https://doi.org/10.3847/0004-6256/152/4/100) already documents pixel-level decorrelation, cross-validation and transit injection/recovery. Thus *recovered idealized transit depth* does not on its own establish a new method.
- [NASA TESS PLD/noise-removal documentation](https://heasarc.gsfc.nasa.gov/docs/tess/NoiseRemovalv2.html) presents pixel-level regressors as an established family. Our **PLD1 is a bounded first-order ridge approximation**, not full EVEREST/QLP/PDC.
- [MAST TESS Data Product Overview](https://outerspace.stsci.edu/spaces/TESS/pages/14563420/2.0%2B-%2BData%2BProduct%2BOverview) documents quality bit semantics and selection. `QUALITY=0` is not a ground-truth astronomical-origin label.
- [Zackay, Ofek & Gal-Yam (2016)](https://arxiv.org/abs/1601.02655) and the [TRANSLIENT literature](https://arxiv.org/abs/2401.16489) are relevant published alternatives for distinguishing moving or shifted image sources from actual transients, and must be included in any claim of source-attribution novelty.

This is a **targeted** prior-art comparison, not proof that no older or unpublished work contains the exact benchmark. Conversely, the exact numeric R² and SSE values on a selected star do not establish original scientific methodology.

## The crucial apparent conflict is real, not an error

The P01 target variable is **photocenter displacement in pixels** and its strong baseline is an AR2 model of previous motion. The P02 target variable is **SAP brightness** and its strong comparator is a basic **pixel-level decorrelation**. The scores use different outcomes, samples, and error objectives, so **15.72% and 1.70% are not directly comparable effects**.

They are entirely compatible findings: quaternion telemetry can add information about pointing while yielding only modest or non-specific improvement to photometric scatter after pixel-based correction. The P02 shifted control also improved the metric slightly; this limits attribution of the small gain to physical quaternion alignment alone.

## Stop conditions and next scientific design

Do **not** claim a new ARARA astrophysical detector based on these results. The next major protocol must satisfy these conditions **before** using words such as *instrumental versus astrophysical classification*:

1. Freeze **external labels** for both known astrophysical events and independently documented instrument anomalies, with catalog/version/time-provenance; labels must not be functions of the same `QUALITY`, `SAP`, `PDCSAP` or model score being evaluated. If independent labels are unavailable, stop the classification claims.
2. Preselect **multiple TESS targets and sectors**, including both the previously studied data and a genuinely unseen source/sector family. Split by **target/sector**, not only adjacent cadences; apply temporal embargoes and do not choose cases after observing performance.
3. Compare with a **full reproducible published pipeline/baseline** and a calibrated abstention/reject-option procedure. Time-only AR2, first-order PLD1 and one +97 shift are *not* sufficient comparators for a state-of-the-art superiority claim.
4. Use physically constrained **source-specific transit injections** (with point-spread function, blends, backgrounds and measured aperture losses) for recovery tests. Do not generalize all-aperture common-mode scaling to planet transits.
5. For event attribution, report confusion matrices, per-class false-positive/false-negative rates, selective risk-versus-coverage, a calibration/uncertainty check, detection power and transit-depth retention. Require preregistered thresholds and an untouched final holdout.
6. Audit the real sensor/feature dependency graph: science cameras can participate in spacecraft guidance, so separate data providers do not guarantee **physical independence**.
7. Preserve all negative tests, access failures, input hashes and precise nonclaims. Do not publish private scientific emails or imply outside collaboration.

A possible narrower scholarly output *today* is a clearly scoped, reproducible **technical benchmark note** that highlights the separation between motion predictability and photometric utility in this one TESS product. It is **not yet** a validated new astronomical method, and generalization/publication value requires independent replication.

## Current claim boundary

**Known science:** pointing-induced photometric systematics; pixel decorrelation; quaternion covariates; synthetic signal injection; identifiability limits.  
**ARARA's own tested evidence:** audited archival joins, positive incremental quaternion information for within-sector motion prediction, rejected 5%-threshold photometric gain on simple PLD1, and very high retention of an idealized multiplicative aperture injection.  
**Not established:** an independently verified astrophysical-vs-instrument discriminator, novel theorem, new physical mechanism, cross-sector generalization, state-of-the-art advantage, or closed M38B calibration/holdout gap.

There is no author endorsement, external validation, or private-correspondence attribution in this record.
