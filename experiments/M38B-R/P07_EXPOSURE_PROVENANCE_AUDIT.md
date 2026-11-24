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

## Executed findings and original failed build — 3 November 2026

I committed [the P0.7 policy](P07_EXPOSURE_PROVENANCE_POLICY.md)
at `4689a513e7eef4b4eba09ccbc6a2ddbcc88248a9`, before implementing
the source, tests or formal witnesses.

The first implementation at `d37979c2da3df644317cf268edba87444dabe11c`
was checked by [research-audit run 41725557607](https://github.com/DevHabito/arara-space-telescope/actions/runs/41725557607).
Its Python job completed **130/130 passing audit tests**, including
**15 new P0.7 tests**, and the historical source manifest was verified.
The **Lean 4 job failed**: two concrete witnesses used `decide`, and
the Lean compiler could not synthesize the required
`Decidable (boundedExposureBefore ...)` instances. I kept that failed
CI result; it is not a scientific counterexample.

I replaced only those two proof tactics with
`unfold boundedExposureBefore` followed by `omega` in commit
`3827600ae212386840cd2fc2b8a9cbbcf0465427`.
The [corrected research-audit run 41725739124](https://github.com/DevHabito/arara-space-telescope/actions/runs/41725739124)
recorded **130/130 passing Python audit tests**, a successful Lean 4
build (**10 jobs**) and `Manifest verified: all hashes match`.
It reported archived M38B `NO_OPERATIONAL_VERDICT`. No
baseline, numerical tolerance, physical uncertainty model or
archived source file was altered to make the theorem compile.

The checked cases include exactly equal numerical diagnostics for
latest accepted cadences **81, 83 and 179** versus the existing P0.5
prefix path; disjointness checks for bounded exposure envelopes;
identity and cadence mismatch blocking; nonfinite and overflowing
time bounds; malformed frames; in-memory ownership; SHA-256 chain
determinism; changes to frame or time metadata changing the hash;
and detection of deliberate **stored-metadata-only** corruption.
These are software fixtures, not actual telescope measurements.

The correction and its original failed build are tracked as **F22**.
The unverified origin and physical magnitude of time uncertainties
remain open as **F23**; the absence of authenticated origin,
keyed signatures and protected persistent records remains **F24**.

The historical 278-suite regression is a **separate** CI workflow.
It must be checked on the final documentation commit before claiming
a verified final state.

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
