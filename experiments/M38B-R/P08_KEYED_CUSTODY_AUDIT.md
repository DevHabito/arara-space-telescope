# P0.8 — keyed packet custody and partial source-authenticity boundary

This audit uses the precommitted
[P0.8 acceptance policy](P08_KEYED_CUSTODY_POLICY.md). I did not change
an archival scorer, the source manifest, any scientific threshold or
the candidate bank's mathematical operations.

## What the implementation attempts

The new `keyed_custody.py` has two separate conceptual actors:
a test-only packet constructor that signs with a deliberately **public
fixture key**, and a verifier configured with a pinned key ID, a separate
runtime verification key and producer-declared session, instrument,
target and clock labels. The verifier authenticates the entire
versioned metadata/byte payload using Python's standard HMAC-SHA-256,
a constant-time tag comparison and a previous-packet MAC reference
*before* decoding the numerical frame.

The original input frame bytes are retained in each immutable packet
as little-endian binary64 C-order numerical data. They are **not**
actual instrument ADC frames, FITS files or ground-truth timestamps.
The verified decoded frame then enters the unchanged P0.7 exposure
ledger, P0.6 cadence order and P0.5 prefix scoring. An invalid packet
permanently blocks that in-memory verification session without
committing an invalid observation.

The HMAC construction was described by Krawczyk, Bellare and Canetti
in RFC 2104 (1997). The RFC 4231 (M. Nystrom, 2005) HMAC-SHA-256
known-answer vector is independently predeclared and tested.
Both are existing cryptographic references, not an ARARA invention.
See [the literature review](../../docs/LITERATURE_AND_ORIGINALITY.md).

## Adversarial conditions and nonclaims

An untrusted party with *no access to the correct secret* should fail
to change packet frame bytes, timing, labels, predecessor or MAC
without detection, under the standard cryptographic assumptions.
However, the tests cannot demonstrate independence from the signer
because both actors use public fixtures in one software process.

A sender who *does* know the key can sign fabricated measurements.
A complete previously valid transcript can be replayed into a new
verifier with the same key and session identity. Those deliberate
negative-control tests are necessary: HMAC verifies **key possession**,
not a physical telescope, real clock, actual target or factual claim.

Without an independently protected source key, hardware identity,
instrument clock, secure key rotation, external monotonic session
nonce register, persistent append-only storage and independent raw
data custody, neither authenticity nor real-world anti-replay is
established. The P0.7 claimed timing uncertainty and P0.4 numeric
conditioning limitations remain open.

## Execution and failure record

Only the exact CI job logs can justify test/pass claims. I will
record observed outcomes and corrective commits here without
retroactively changing the precommitted criteria. This is not an
observational calibration, holdout evaluation, FPR experiment
or astronautical mission result.

**Scientific status:** archived M38B `NO_OPERATIONAL_VERDICT`;
M38B-R `approved_for_calibration: false`,
`execution_permission: not_authorized`.
