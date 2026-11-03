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

## Verification status

A passing check requires inspecting actual logs from the exact implementation
commit. The `tests/test_m38br_sequential_cadence.py` suite exercises
equivalence with static prefix scoring, missing indices, duplicate/reordered
frames, invalid timestamps, malformed/nonfinite frames, owned input copies,
eligibility before cadence 81, and the absence of archived scorer imports.

No scientific positives/negatives, calibration, holdout, detection threshold
or instrument light curve enters these tests. I will record numerical
failures and source changes in this document, the research notebook, and the
failure register as evidence becomes available.

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
