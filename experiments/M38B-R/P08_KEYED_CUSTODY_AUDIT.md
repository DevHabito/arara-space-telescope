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

## Executed checks — including the negative run

I used the [P0.8 policy](P08_KEYED_CUSTODY_POLICY.md) fixed at
`7185997425ca4ab788c79a741d23d858707a54c7` before implementing
the code or observing any P0.8 outcomes.

At implementation commit `2249883f02818ea38e6853e86085b649748f987f`,
[research-audit run 41727981482](https://github.com/DevHabito/arara-space-telescope/actions/runs/41727981482)
confirmed **145/145 Python tests**, including **15 new P0.8 tests**.
The Lean 4 build completed in **10 jobs** and the manifest verifier
reported `Manifest verified: all hashes match`. In particular, the
predeclared negative controls both **passed**: a sender possessing the
key can sign arbitrary fabricated numerical values, and a complete
previously valid transcript can be replayed in a fresh verifier with
the same key/session identity. These are documented limitations, not
claims of real-world authentication.

I strengthened the exact-equality check to compare each output
array's **raw bytes**, not just `np.testing.assert_array_equal`;
two arrays can compare numerically equal while encoding a
difference such as `+0.0` versus `-0.0`. Those byte comparisons
passed on the deterministic constructed fixture at **endpoints
81, 83 and 179**.

I also added a white-box adversarial case: someone who knows the
**public test key** replaces an already accepted packet's stored
bytes with a malformed length, then recomputes a valid MAC. The
[negative run 41728262117](https://github.com/DevHabito/arara-space-telescope/actions/runs/41728262117)
ran **146 Python tests, with one real failure**:
`test_validly_retagged_invalid_stored_bytes_block_custody`
confirmed the invalid buffer raised a `ValueError`, but left
`verifier.blocked == False`. The P0.8 fail-closed requirement was
not met. I did not remove this test or change the policy.

Commit `96809479c956c3f108e3acdf89600b4e97d654d4`
added a strict stored-byte-length guard and caught NumPy decoding
errors within the session-blocking path. The subsequent
[research-audit run 41728450100](https://github.com/DevHabito/arara-space-telescope/actions/runs/41728450100)
records **146/146 Python tests passing**, a successful **10-job Lean
build**, and the unchanged source-manifest hashes. The original
failure and correction are recorded as **F27**.

All three runs concern deterministic, **unlabelled numerical test
arrays**. The trusted key is deliberately a published test value, not
a secret credential. The RFC 4231 known-answer check verifies only
the standard-library HMAC-SHA-256 primitive; packet framing and the
custody contract are checked by separate tests. Neither result
establishes instrument provenance, protected key provisioning,
physical timestamp accuracy, transport security or authenticity
of an astronomical observation.

The historical regression workflow is independent; check its
**final documentation commit** before claiming that 278 historical
tests passed at that specific SHA.

**Scientific status:** archived M38B `NO_OPERATIONAL_VERDICT`;
M38B-R `approved_for_calibration: false`,
`execution_permission: not_authorized`.
