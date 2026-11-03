# P0.4 — numerical conditioning and missing-sample diagnostics

**Scope:** mathematical and software checks on fixed analytic vectors and constructed observation-quality masks. The comparisons were specified in [P04_NUMERICAL_AUDIT_POLICY.md](P04_NUMERICAL_AUDIT_POLICY.md) and committed *before* implementing the P0.4 checks. No archived scorer code, M38B source manifest or detection threshold is changed.

## Why this investigation matters

ARARA uses an absolute `1e-12` energy cutoff in its reference projection and template normalization. The cutoff is a computational rule, not a demonstrated telescope-noise model. Near a reference/template singular direction, the archived subtractive energy formula and the source-independent direct-vector projection need not agree to tight floating-point tolerances. The numerical limit follows standard analysis of loss of significance in nearly equal floating-point quantities (Higham, 2002; Golub and Van Loan, 2013); publication metadata and publisher links are in [the bibliography](../../docs/LITERATURE_AND_ORIGINALITY.md).

In exact arithmetic, for reference `r = (1,...,1)` (eight elements), `y = (1,-1,...,1,-1)` and template `t = r + δ e₀`, `δ > 0`, the score after projecting away the reference direction is `sqrt(8/7)`, while the projected energy is `7δ²/8`. These are identities for this constructed example, not physical detections. The independent projection computes the orthogonal vector before its norm; the archived projection subtracts two energies and can lose precision near parallelism. Neither method is declared globally superior.

## Input quality and prospective missing-data policy

`numerical_quality.classify_nonfinite_positions` labels nonfinite values relative to the inclusive observed prefix `0..endpoint` versus future-only positions, separately for each curve. It is a **read-only classifier**, not an imputer, quality-weighted detector or authorization to ignore nonfinite future measurements. The current batch preprocessor and independent scorer still reject any series containing nonfinite samples, including after the requested endpoint. The pending scientific design decision is whether to provide a separate strict prefix-only/streaming implementation and how to freeze missing-data handling before calibration.

The new tests use explicitly defined positions of `NaN` or `Inf`: a baseline value before all endpoints, an invalid sample between two requested endpoints, and a later invalid sample after earlier requested endpoints. The classifier does not alter the raw array or mix curves. This distinguishes *invalid measured evidence* from *unavailable future data* for review, without assigning a scientific verdict.

## Verified numerical results — 3 November 2026

The nine new P0.4 tests **all passed** in the exact cloud
[research-audit run 41720056181](https://github.com/DevHabito/arara-space-telescope/actions/runs/41720056181)
at commit `e63da1c168341014ff87bdea495f3c5151163851`. The job log
records **91/91 passing Python audit tests**, a successful Lean 4 build
and `Manifest verified: all hashes match`; the archived scientific status
is still `NO_OPERATIONAL_VERDICT`. The archived tests workflow is a
separate check and should not be inferred from these audit tests.

The project does not need to approximate this example from observations.
The independent analytic prediction and both actual computed values
were printed by the unit test itself:

| Quantity | Value from CI log |
| --- | ---: |
| Analytic projected template energy for the binary64 fixture | `1.2600000000724642e-12` |
| Analytic normalized score `sqrt(8/7)` | `1.0690449676496976` |
| Independent explicit-projection score | `1.0690449676496976` |
| Historical subtractive-energy score | `1.0685306041827185` |
| Independent absolute error at displayed precision | `0.0` |
| Archived absolute error | `0.0005143634669790842` |

The witness was fixed in
[P04_NUMERICAL_AUDIT_POLICY.md](P04_NUMERICAL_AUDIT_POLICY.md) at an
earlier commit, `19c404829c3d0ee754813fcf1b7880e79f345011`.
The observed difference is evidence of floating-point sensitivity in
this **one near-parallel constructed example**; it is not an empirical
estimate of ARARA's physical accuracy or a blanket comparison of algorithms.

The predeclared scale test also passed: the independent score is nonzero
with the unscaled near-parallel vectors, becomes **zero** when the
reference and template are both multiplied by `0.1` (projected energy
falls below the fixed absolute floor), and agrees again after multiplying
both by `2.0`, within the fixed `1e-9` absolute tolerance. This is
a direct counterexample to unit/scale invariance near the numerical
cutoff. It does not demonstrate whether this cutoff is suitable for
a real detector.

The reference-cutoff test passed too: a very weak parallel reference
is disregarded below the fixed floor; the stronger parallel reference
is projected out. Finite inputs with extreme energy are rejected instead
of being promoted to finite scores.

The new [observation-quality classifier](numerical_quality.py) passed
the positional checks: a missing baseline sample taints the observed
prefix, while a missing later sample can be marked future-only with
respect to an earlier endpoint. It does **not** change the existing
whole-series finite-data rejection rule, authorize imputation or prove
streaming causality. I have kept this limitation open as F16.



The audit only becomes an executed finding when the exact P0.4 commit's GitHub Actions logs show results. Check [tests/test_m38br_numerical_quality.py](../../tests/test_m38br_numerical_quality.py), the separate archived-vs-independent numerical witness in the CI log, and the manifest verification before recording PASS/FAIL. Keep negative observations visible rather than loosening the predeclared absolute bounds.

## What this does not solve

- No IEEE error-bound theorem for all data, scale transformations or operating systems.
- No proof that `1e-12` is appropriate for astronomical photometry or invariant to units.
- No streaming detector, real instrument data, missing-data imputation or quality-control policy.
- No M38B-R calibration, untouched holdouts, FPR, recall, alert rate or astrophysical discovery.

The prior status remains: M38B `NO_OPERATIONAL_VERDICT`; M38B-R `approved_for_calibration: false`.
