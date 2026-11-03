# P0.6 — sequential cadence provenance and missing-past-data audit

I committed the [P0.6 acceptance policy](P06_SEQUENTIAL_CADENCE_POLICY.md)
**before** writing or running the following code and checks. This remains an
engineering investigation, not a calibrated astronomy experiment.

## The interface being investigated

`sequential_cadence.CadenceLedger` receives one explicit frame at a time,
with a declared zero-based cadence index and a caller-supplied timestamp.
The ledger accepts only consecutive indices, finite frame values of the
declared target/reference shape, and strictly increasing finite time labels.
It owns copies of accepted frames and returns copies of the latest accepted
prefix. It can call the already tested `score_observed_prefix` only when
cadences 0..81 (or later) have been received, without passing any future
samples.

On the first invalid append, the ledger becomes permanently blocked for
that session. This is a deliberately strict **missing-past policy** for
numerical research: it neither fills a gap with zeros nor pretends a
later sample belongs to an earlier cadence. Its accepted frames are retained
internally but scoring and snapshots are unavailable after blocking.
No data-repair, retransmission or continuation protocol has been authorized.

The declared timestamps are **unverified producer metadata**. Strict order
does not prove their correctness, precision, synchronization to UTC or any
astronomical time standard. The tests deliberately accept wildly irregular
time intervals to make this limitation visible.

## Executed checks and the failure I kept

I checked the actual GitHub Actions logs, not just the test definitions.

The first P0.6 implementation at commit
`51609e911e7fa949abe78d4cb9471f1f3a53694d` passed its
**12 new cadence-ledger cases**. [Research-audit run 41723252836](https://github.com/DevHabito/arara-space-telescope/actions/runs/41723252836)
records **114 passing Python audit tests**, a successful nine-job Lean build
and verified historical manifest hashes. The cadence 81, 83 and 179
diagnostic fields matched the pre-existing prefix scorer exactly on the
fixed numerical fixture. The ledger also blocked declared missing,
duplicate or reversed indices, invalid timestamps and invalid measured
sample arrays in the exercised tests.

I then added one more adversarial check for a ragged nested frame.
[Run 41723477963](https://github.com/DevHabito/arara-space-telescope/actions/runs/41723477963)
reported **115 Python tests run, one failure**. `np.asarray(frame)`
raised a `ValueError` before the original append guard marked the ledger
as blocked. The new test observed `ledger.blocked == False`, contrary to
the previously recorded P0.6 fail-closed contract. That is an
implementation error, not a statistical detection outcome.

I corrected the conversion boundary in
commit `e32cbb08569215a2a8f3a4843425dc58708afd8e`.
The frame inspection and float64 conversion are now guarded separately,
and both malformed shapes and conversion errors block the ledger.
[Research-audit run 41723628328](https://github.com/DevHabito/arara-space-telescope/actions/runs/41723628328)
records **115/115 passing Python audit tests**, including
`test_ragged_frame_rejection_blocks_segment`; Lean 4 completed
successfully in nine jobs and `Manifest verified: all hashes match`.
The archive still reports `NO_OPERATIONAL_VERDICT`. I did not
change the temporal acceptance policy after observing the failed run.

The separate historical regression workflow must be checked on the
final documentation commit before reporting its result for that
commit. The audit tests and a compiled Lean module do not verify
actual instrument timestamps or scientific significance.

## What I cannot establish yet

The timestamp field is a producer declaration. The ledger checks
monotonicity and shape but cannot authenticate clock origin, exposure
integration time, sampling jitter, absolute epoch or synchronization.
The test deliberately accepted time gaps of very different sizes.
This means P0.6 has a reproducible **software order contract**, not a
verified physical timebase. It does not implement retries or data
repair when an actual frame is lost. A blocked segment currently requires
an entirely new ledger; segment reconciliation and independent target
identity are not specified.

## Boundaries still open

A real acquisition pipeline requires authenticated hardware and target
identity, exposure integration timing, drop/retry policy, timing uncertainty,
calibrated cadence intervals, transport integrity, data persistence,
instrumental calibration and validation on independent observations.
The ledger cannot establish any of these. It also does not resolve the
absolute energy floor and projection conditioning findings F17–F18.

The archived M38B state is `NO_OPERATIONAL_VERDICT`.
M38B-R remains `approved_for_calibration: false` and
`execution_permission: not_authorized`.
