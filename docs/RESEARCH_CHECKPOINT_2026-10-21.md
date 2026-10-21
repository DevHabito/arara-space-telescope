# ARARA research checkpoint — 2026-10-21

Base commit: 6ad883dbd171e0e7eece5a9f9267552e5297435c.

## Archived evidence

The repository preserves M00 through M38B recovery. TEST_REPORT.md records 278 historical passing tests, which are not independent reruns performed by this checkpoint. M37R's recorded operational synthetic pass and its prediction-mismatch flags must both remain visible. M38A is an outcome-free structural grid check, not an operational detector confirmation.

## M38B blockers

1. The archived M38B specification freezes calibration seed 2026090501, whereas the recovery plan records 2026090601. Recovery discloses the change but needs its own experimental identity.
2. The recovery freeze covers only six central files, omitting executable dependency modules, runner, and test suite. This audit does not rewrite the historical manifest.
3. The recovered runner hard-codes /mnt/data/ARARA_M38B and regenerates freeze-related files during execution. It is not a portable, read-only preflight.
4. No complete frozen thresholds, ten holdouts, and final verdict were found in the archived package. M38B is NO_OPERATIONAL_VERDICT, not passed and not failed.

## Negative tests and regressions

The new Python tests exercise valid/invalid checksums, tampering, absent files, directory escape, incorrect bank size, missing data, changed random seeds, and the logical distinction between raw score improvement and detection after recalibration. The audit CLI exits nonzero on archive integrity or hypothesis-count regressions. Expected missing historical outcomes remain prominently flagged but do not turn into false CI failures.

The Lean 4 module proposes proofs only of arithmetic cardinalities, control-veto logic, and a discrete recalibration counterexample. Formal checking must be confirmed from GitHub Actions logs; no mathematical or physical result is considered verified until then.

## Next scientific gate

Prepare a distinct prospective M38B-R preregistration (not a retroactive edit) with complete dependency hashes, reproducible environment, source-independent controls, exact stop/failure gates, and immutable seed plan. Calibrate negatives before opening any holdout. Preserve every unsuccessful outcome. Do not claim operational astronomy until independent real-data validation and false-alert estimates in target-hour/field-hour units.

## Nominal templates versus actual candidate evaluations

The M38B preregistration declares 99 endpoints × 4 shapes × 37 durations × 5 latent values = 73,260 nominal grid slots. Inspection of score_latent_grid_bank shows that the linear shape is independent of the latent parameter and is evaluated only once per duration; the power-law, exponential and logistic shapes each use all five latent values. Thus the candidate's implemented per-curve template score evaluations are 99 × 37 × (1 + 3 × 5) = 58,608 (not counting the separately scored exact-latent control). These are evaluation counts, not a proof that every resulting statistic is distinct. Do not alter the frozen protocol or infer FPR from nominal template counts; empirical calibration already uses the bank's maximum. This distinction matters for computational-resource estimates and accurate reporting.
