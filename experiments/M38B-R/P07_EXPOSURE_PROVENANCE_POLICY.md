# P0.7 — declared exposure intervals, time bounds, and chained integrity

**Recorded:** 3 November 2026, *before* the P0.7 implementation and test execution. This is a software and mathematical audit, not scientific calibration or independent astronomical observation.

## The question

P0.6 checked consecutively declared cadence indices and increasing producer-supplied timestamps. It did not determine whether consecutive exposures physically overlap, whether stated time uncertainties permit a definite temporal ordering, whether a frame and its declared metadata remain consistent after storage, or whether a producer's identity can be trusted.

I will add a separate audit wrapper rather than alter the previously tested scorer or its P0.6 ledger. This avoids confusing a newly declared metadata contract with a physical detector guarantee.

## Fixed data and checks

An experimental `ExposureProvenanceLedger` accepts a constant, caller-declared `instrument_id`, `target_id`, `clock_id`, `session_id`, number of curves and star channels. Identifiers are nonblank UTF-8 strings of length at most 128; the ledger does **not** independently authenticate them. Only finite real-valued frames of the fixed (curve, star) shape enter the P0.6 ledger, using consecutive zero-based cadence indices `0..179`. There is no gap repair.

Each append declares `start_seconds`, `end_seconds`, `start_uncertainty_seconds`, `end_uncertainty_seconds`. Values are Python `int` or `float` (excluding booleans), finite and nonnegative for uncertainties. Times are abstract seconds within one *unverified* producer time scale. They are **not automatically UTC/TDB/BJD or synchronized hardware measurements**. Uncertainties are declared absolute upper bounds, **not** standard deviations or confidence intervals.

The following strict inequalities are required in binary64 arithmetic, with nonfinite derived bounds rejected:

1. **Definitely positive exposure:** `start + start_uncertainty < end - end_uncertainty`.
2. **Definitely ordered neighboring exposures:** for every subsequent frame, `previous_end + previous_end_uncertainty < next_start - next_start_uncertainty`.
3. The P0.6 ledger also checks that the arithmetic midpoint `start/2 + end/2` is finite, strictly increasing, and that the cadence index is exactly the next one. Computing the midpoint using halves avoids some preventable overflow, but does not establish a bound on floating-point error or clock accuracy.
4. Accepted frame data are **copied**, canonicalized to contiguous little-endian float64 bytes in C order, and hashed together with a versioned canonical JSON encoding of that frame's metadata. A chain uses `SHA-256(domain-separator || previous-digest || metadata-length || metadata || frame-bytes)`, beginning with 32 zero bytes. Verification recomputes the chain from stored copies before exposing score. A mismatch blocks the in-memory session. This checksum is **not a digital signature**, keyed MAC, trusted clock, trusted raw observation, or protected persistent audit log. A malicious producer may forge both data and checksum.

All invalid append requests, including wrong identity, malformed type, clock mismatch, interval ambiguity, missing index, nonfinite frames and unrepresentable floating point values, block the wrapper permanently before scoring. The rejected record is not added. The existing P0.6 ledger and scorer keep their previous behavior.

## Acceptance tests fixed now

- Fixed, unlabeled `(2, 9, 180)` NumPy fixture, seed `20261103`, same deterministic rising numerical ramp used in P0.5; **no simulated astrophysical positives or negatives**.
- Valid example: for cadence `k`, declare start `1000 + 2*k`, end `1000.5 + 2*k` and uncertainties `0.01` seconds at both boundaries. Append 0..83, comparing **every** result at cadence 81 and 83 bitwise to direct `score_observed_prefix`, and continue through 179. Test record counts, identities, checksum lengths and repeat verification.
- Refuse definitely-positive violations, neighboring time intervals that overlap **once uncertainty is included**, NaN/Inf/boolean/non-numeric time values, negative or nonfinite uncertainty, and a finite `1e308` input producing nonfinite derived bounds. Use separate fresh ledgers for independent failure cases.
- Refuse a declared instrument, target or clock change and a wrong cadence index; all rejection paths must permanently block the session and must not commit the offending record.
- Mutate the caller's frame and exported snapshot after append; digest verification and later results must not change. Identical copies of the same valid sequence produce identical SHA-256 digests. A change of one finite sample or one declared interval in a separate valid sequence must change the digest, while keeping chronological constraints satisfied.
- Corrupt a privately stored metadata record in a test (a deliberate white-box adversarial fixture) while leaving the original digest. `verify_integrity` must detect the mismatch, permanently block the wrapper, and refuse subsequent scores.
- No data are sent to a network, written as scientific results, imputed, labeled, calibrated or interpreted as detections.
- Narrow Lean 4 arithmetic witnesses may be added for integer interval bounds; do not portray them as IEEE floating-point or instrument-clock verification.

## Boundaries and evidence

The behavior can validate only **internal consistency of asserted metadata and values**, not authenticity, actual instrument exposure, source identity, timestamp standard, astronomical coordinates, transport security, sampling jitter or long-term archive persistence. No covariance-aware, statistical or interval-verified proof for IEEE arithmetic is established. The inherited `1e-12` projection energy floor is unchanged. An immutable Git commit plus successful CI is source reproducibility, not physical provenance.

Prior art: C. M. Croarkin (2003), NIST/SEMATECH *Measurement Process Characterization* (measurement uncertainty); Gene H. Golub and Charles F. Van Loan (2013), *Matrix Computations*, and Nicholas J. Higham (2002), *Accuracy and Stability of Numerical Algorithms* (arithmetic/conditioning). Verified publication metadata and links are collected in [the literature review](../../docs/LITERATURE_AND_ORIGINALITY.md). None of these publications validates ARARA. SHA-256 is a standard hash and is not a novel ARARA invention.

**Scientific gate:** archived M38B `NO_OPERATIONAL_VERDICT`. M38B-R `approved_for_calibration: false` and `execution_permission: not_authorized`. Archive and protected manifest must remain unchanged.
