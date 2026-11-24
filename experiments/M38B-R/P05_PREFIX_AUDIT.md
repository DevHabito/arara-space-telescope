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

## Execution record — exact first P0.5 implementation commit

At commit `07b9f3226dbae5f273da26d63b84f4f0a4aded44`, the
[GitHub Actions research-audit run 41721601276](https://github.com/DevHabito/arara-space-telescope/actions/runs/41721601276)
reported **102/102 Python audit tests passing**, including all **11 new
observed-prefix tests**. The Lean 4 `lake build` completed in nine jobs;
`verify_manifest.py` reported `Manifest verified: all hashes match`;
the historical M38B status remained `NO_OPERATIONAL_VERDICT`.

The checks included exact output equality for early/late prefix endpoints,
future-only nonfinite values in the separate full-series input, rejection
of missing *measured* samples, rejection of longer/shorter inputs, invalid
endpoints and shapes, defined fail-closed behavior on constant data, curve
permutations, immutable caller arrays, and absence of archive imports.

These counts come from the GitHub job logs, not from the presence of a test
file. The 278 historical tests are executed by a **separate** workflow and
must be checked on the final documentation commit before reporting their
result as passed. The final head's CI should also be read back separately.

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
