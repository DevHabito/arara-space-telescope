# P0.5 — strict observed-prefix input boundary

The [acceptance policy](P05_PREFIX_CONTRACT_POLICY.md) was committed on
3 November 2026 before this implementation or its test outcomes.

## What I changed

The experimental `score_observed_prefix(stars, *, endpoint)` accepts
**exactly** samples 0..endpoint (inclusive). The star axis includes one
target and at least one reference. I deliberately do not accept a full
180-sample array when asking for endpoint 83, pad unavailable future
samples with arbitrary values, inspect hidden simulator information or
change the 50-sample preprocessing baseline.

The independent bank's minimum-length check now depends on its configured
last endpoint, not on a hard-coded 180. With the default 99-endpoint
configuration, the same 180-sample minimum still applies. Its onset,
four shape equations, five-point latent grid, 37 durations, AR(1) filtering,
projection and tie order remain untouched.

I did not change the previous `score_independent_observed_stars` batch
function. It still rejects a nonfinite value anywhere in the supplied
180-sample series. The prefix function receives less data rather than
silently suppressing validation failures in the batch path.

## Comparison and failure conditions

The precommitted tests compare *every returned field* with the corresponding
column from the independent full-bank batch diagnostic on a deterministic,
unlabelled, finite star cube, at endpoints **81, 83, 110, 179**. Equality
means `np.testing.assert_array_equal` on a single GitHub Actions runtime;
it does **not** establish a universal floating-point theorem.

The tests also require rejection of an incomplete measured prefix; reject
additional unseen future samples, even when finite; disallow bad endpoints,
invalid star dimensions and malformed reference-star axes; preserve input
arrays; preserve per-curve isolation; and fail closed when the hinge onset
is undefined. A later `NaN` in a **separately supplied full array** must
continue to fail old batch validation, while the accepted finite prefix
0..83 can still be scored independently.

## Execution record

This section must be updated only after reading the actual GitHub Actions
logs for the exact implementation commit, recording any failed attempts
and the final verified head. An unexecuted test file is not evidence of a
pass.

## Scientific boundary

This is a *prefix-bounded numerical API*, not a telescope acquisition
system, photometric noise model, missing-data imputer, live alert stream,
FPR calibration, or an operational detector. At an endpoint where observed
samples are themselves nonfinite, the prefix function rejects the input
rather than guessing their values. It remains sensitive to the numerical
conditioning and absolute energy cutoff issues F17–F18.

Archived M38B: `NO_OPERATIONAL_VERDICT`.
Prospective M38B-R: `approved_for_calibration: false`,
`execution_permission: not_authorized`.
