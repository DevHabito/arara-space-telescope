# P0.6 — sequential cadence provenance and missing-past-data contract

**Recorded:** 3 November 2026, before the P0.6 implementation or test execution. This is an engineering audit of constructed numerical observations, not a preregistered astronomical detection study.

## Question

P0.5 proves only that a numerical scoring entrypoint receives the exact prefix supplied to it. That does not establish where those samples originated, whether a producer skipped a cadence, whether samples were received in chronological order, or whether the supplied time labels correspond to any real instrument clock. I will not conflate sequence validation with authenticated astrophysical timekeeping.

## Proposed isolated implementation

Create an experimental `CadenceLedger` (in `sequential_cadence.py`) with fixed `curves` and `stars_per_curve` constructor arguments, where curves >= 1 and stars per curve >= 2.

The only accepted frame sequence is a series of explicit **zero-based consecutive integer cadence indices** `0, 1, 2, ... 179` with a fixed two-dimensional `(curve, star)` numeric array at each cadence. Every frame is copied as float64 and must be finite before acceptance. The caller also supplies a finite **strictly increasing numeric declared timestamp** in seconds. This is an *ordering check only*: the timestamps are untrusted caller declarations, not verified UTC, exposure start/stop times, barycentric times or calibrated cadence intervals.

The ledger has no reordering queue, buffering of gaps, interpolation, extrapolation, synthetic missing values, replay, disk persistence, network IO or trusted sensor protocol. An invalid `append` request (gap, duplicate, reversed index, non-monotonic/invalid timestamp, invalid frame, wrong shape, index outside the historical horizon) makes that ledger **irreversibly blocked**. It cannot subsequently score, snapshot, or resume the segment; a new ledger would have to be created for a separately identified segment under a future, currently unspecified policy. Existing accepted frames remain in memory but cannot be used to produce a score after an integrity failure.

Expose `snapshot()` only for the **latest accepted prefix** and return a copy. Expose `score_latest()` only at endpoints `81..179`, by passing that snapshot to the already validated `score_observed_prefix` path. In particular, never pass a longer array to score an earlier endpoint. Do not modify `observed_prefix.py` or its numerical bank and never use simulator truth.

## Acceptance tests fixed before implementation

1. Given a deterministic finite constructed observation cube `(2, 9, 180)` (not labeled scientific positives or negatives), append cadences 0..83 with timestamps `1000 + 0.5 * index`. At endpoints **81 and 83**, require every output field to agree **exactly** (`np.testing.assert_array_equal`) with `score_observed_prefix(cube[:, :, :endpoint+1], endpoint=endpoint)`.
2. Continue the same admissible sequence through **179**; compare the final diagnostic outputs exactly and verify the ledger's frame count, last index, and recorded declared times.
3. Append index 0, then index 2: the missing index 1 must block the ledger. The offending frame must never be committed. Scoring/snapshot after block must fail, and an attempted late repair at index 1 must also fail.
4. Test duplicates or reversed indices, equal or decreasing declared timestamps, nonfinite timestamps, a bool index, and a cadence 180, each against a separate ledger to ensure no state contamination. Every invalid append must block the ledger.
5. Reject a NaN or Inf in an *observed frame*, wrong frame shape, and nonnumeric input before a score can be produced. No imputation or masking is permitted.
6. After a successful append, mutating the caller's frame or an exported snapshot must not affect subsequent snapshots or the calculated prefix score. State must own copies of accepted frames.
7. Before 81 accepted cadences, `score_latest()` fails with a documented eligibility error; it must not claim a false detection or manufacture 180 samples.
8. No negative family, calibration, holdout, physical timestamp source, network stream, threshold or FPR/recall test. A later invalid time stamp must not retroactively create a valid score after the ledger becomes blocked. A source inspection test should confirm no import of the archived scorer.

## Failure bookkeeping and limits

The results are diagnostic and should be read from the actual GitHub Actions logs on the exact commit. Any failure, including an invalid assumption in these criteria, must be recorded without changing tolerances after results are seen. No new Lean theorem is claimed unless one is independently written and compiled.

The terms *cadence*, *declared timestamp* and *blocked segment* are audit-specific conventions. A physically trustworthy telescope timebase would additionally need provenance of exposure boundaries, calibrated clocks, target identity, cadence losses/recovery, sampling uncertainty, sensor quality flags, transport integrity and replay policy. The baseline preprocessing and matched filter remain unchanged and retain the P0.4 conditioning limits.

Relevant prior measurement-process context: C. M. Croarkin (2003), *NIST/SEMATECH Engineering Statistics Handbook, Chapter 2: Measurement Process Characterization*; see the project's [literature review](../../docs/LITERATURE_AND_ORIGINALITY.md). I do not claim that publication verifies this prototype.

**Scientific boundary:** archived M38B `NO_OPERATIONAL_VERDICT`. M38B-R `approved_for_calibration: false`; `execution_permission: not_authorized`. No calibration, scientific outcomes or holdouts are accessible in this procedure.
