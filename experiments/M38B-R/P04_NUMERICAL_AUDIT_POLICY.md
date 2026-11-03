# P0.4 — numerical conditioning and missing-sample audit policy

**Recorded:** 3 November 2026, **before** adding the P0.4 numerical diagnostics or running their tests. This is a pre-outcome engineering plan, not the prospective statistical protocol for M38B-R.

## Question

I want to know precisely where the independent projection and observation-only frontend depend on numerical scale or a whole-series validity check. I will investigate the implementation already in the repository, not change the detector's scientific statistic or re-label a discrepancy as a success.

The prior mathematical references are Nicholas J. Higham, *Accuracy and Stability of Numerical Algorithms*, second edition (2002), and Gene H. Golub and Charles F. Van Loan, *Matrix Computations*, fourth edition (2013), listed with publisher links in [the bibliography](../../docs/LITERATURE_AND_ORIGINALITY.md). They motivate the audit of conditioning and projection, but do not verify this code.

## Fixed analytic witnesses and decisions

The eight-element reference `r = (1,1,1,1,1,1,1,1)` and target `y = (1,-1,1,-1,1,-1,1,-1)` are synthetic vectors for mathematical verification, not astronomical observations.

1. **Near-parallel, just above the energy floor.** Let `t = r + δ e₀`, `δ = 1.2e-6`. In exact real arithmetic, `||t_perp||² = 7δ²/8` and the normalized projected score equals `sqrt(8/7)` for positive δ, provided the template is accepted. Require the independent projector's score to agree with this analytic target within **absolute error 1e-9**. Record the archived formula's value and signed/absolute deviation without imposing a same-score requirement in this ill-conditioned case.
2. **Scale-induced gate transition.** Keep `y` unchanged and multiply *both* `r` and `t` by `0.1`. The ideal real-valued normalized score is unchanged, but `||t_perp||²` drops below the existing absolute cutoff `1e-12`. Test the independently calculated output is **zero** at the scaled fixture while the unscaled fixture remains accepted. This exposes algorithmic non-invariance near a fixed absolute cutoff, not a measured physical effect. For an above-floor rescaling by `2.0`, require score agreement within absolute error **1e-9**.
3. **Reference-cutoff discontinuity.** Fix `t = y = r = ones(8)`. With reference scale `1e-7`, reference energy is below `1e-12`, so the unprojected output must equal `sqrt(8)` within **1e-12**. With reference scale `1e-6`, reference energy is above the floor and the template is projected away, so the output must equal **zero**. Record this branch behavior as a limitation; do not tune the existing floor.
4. **Finite extreme input.** Use an array containing finite `1e200` values; an overflowed reference energy must raise the existing `ValueError`. A warning or exception is evidence about input-domain handling, not performance.
5. **Missing-value position.** On an explicitly constructed `(curve, target-and-references, time)` sample cube, classify nonfinite values *without scoring* into invalid measured prefixes or invalid future-only samples for each requested endpoint. A `NaN` at time 25 invalidates endpoints 81 and 83 as prefix; at time 82 it is future-only to 81 and prefix-invalid to 83; at time 130 it is future-only to both. The classifier must **not** impute, suppress, alter observations or authorize partial scoring. The existing offline scorer still rejects any nonfinite input, including future-only values.
6. **No labels and no outcome selection.** No synthetic positive/negative family generation, threshold choice, calibration, holdout, astronomy data ingestion or FPR/recall calculation is permitted. Any new program must be a diagnostic, not a replacement scoring path.

## Pass/fail bookkeeping

Every condition above is checked exactly as stated. If a numeric example contradicts the analytic prediction, I must investigate and record the failure, not enlarge its tolerance. Differences between the two projection algorithms near singularity are reported as differences, not retrospectively converted into equivalence. A successful unit-test run proves only these specific fixtures on the recorded Python/NumPy runtime.

The source code, mathematical identities, test fixture construction, relevant GitHub Actions run URLs and unresolved implications must be entered in [the P0.4 report](P04_NUMERICAL_AUDIT.md), [research notebook](../../docs/RESEARCH_NOTEBOOK_2026-11-03.md) and [failure ledger](../../docs/FAILURE_AND_LIMITATIONS_REGISTER.md). Preserve the original code and historical source manifest.

**Scientific gate unchanged:** archived M38B `NO_OPERATIONAL_VERDICT`; prospective M38B-R `approved_for_calibration: false` and `execution_permission: not_authorized`.
