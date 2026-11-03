# P0.7 — declared exposure-time bounds and integrity audit

The [P0.7 numerical and metadata acceptance policy](P07_EXPOSURE_PROVENANCE_POLICY.md)
was committed separately **before** this implementation or any test run.

## What this code can check

The new experimental `exposure_provenance.py` wraps the existing P0.6
cadence ledger and the P0.5 prefix scoring path; no original archive,
scientific threshold or template-bank equation was edited. It requires
constant caller-declared session, instrument, target and clock labels,
consecutive cadence indices, finite measured frames and exposure
start/end declarations accompanied by nonnegative finite absolute
uncertainty bounds.

For each exposure, the interval between latest possible start and earliest
possible end must be strictly positive. Neighboring envelopes must be
definitely separated *under the declared upper bounds*, rather than
merely ordered by their center values. A rejection permanently blocks
the session; rejected input cannot be used in a score. This policy
cannot determine whether any declared uncertainty is itself truthful.

A versioned SHA-256 chain covers each accepted, copied binary64 frame
and the canonical JSON encoding of its index, four source labels,
boundaries and uncertainty declarations. Before scoring, the chain is
recomputed from the ledger's currently stored frames and metadata.
That detects certain accidental or unauthorized *in-memory changes* to
one side of the record. It cannot authenticate an upstream producer,
timestamps or acquisition hardware: anyone controlling both data and
metadata can simply hash their own false story. No key, signature,
nonrepudiation or secured persistent log is provided.

## Verification boundary

The tests use constructed, unlabeled mathematical samples, including
the same deterministic numerical ramp employed in earlier P0.5
source checks. They exercise comparison with `score_observed_prefix`
at three endpoints, invalid time envelopes and identities, byte-for-byte
digest determinism, a changed frame/time causing digest changes,
mutation isolation and deliberate stored-record corruption.

The optional `formal/AraraFormal/ExposureOrder.lean` witnesses express
a **narrow exact natural-number implication**: separation after adding
nonnegative bounds implies nominal exposure order. Compilation is
not evidence of correct NumPy operations, real-valued interval
analysis or physical clock calibration.

## Results pending direct CI inspection

I will write the implementation commit, failed or successful cloud run
IDs, exact test counts and any limitations here only after reading the
GitHub Actions logs. The historical manifest must remain byte-for-byte
valid; the PR must stay draft and `main` untouched.

## Open physical and statistical questions

Instrument/source identity, UTC/TDB timestamp scale, calibrated exposure
start and stop, timing uncertainty estimation, noise correlation,
instrument pointing, cryptographic source authentication, transport
and storage integrity, end-to-end online system and real-sky observations
are not established. F17–F18 numerical conditioning and F21 physical
time provenance remain open.

**Scientific decision remains:** archived M38B `NO_OPERATIONAL_VERDICT`;
prospective M38B-R `approved_for_calibration: false`,
`execution_permission: not_authorized`. This exercise is not
calibration or a holdout opening.
