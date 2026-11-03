# Independent onset estimation — pre-outcome audit

**Scope:** mathematical and software diagnostics only. No M38B-R calibration,
holdouts, detection rates, thresholds or astronomy are evaluated here.

The archived `m34.estimate_onset_grid` uses cumulative sums to evaluate a
positive hinge-correlation statistic on each endpoint's past selection interval.
`independent_onset.estimate_direct_hinge` independently computes centered
sample vectors and ordinary inner products. It does not import archived ARARA
code or simulated truth. The comparison tests alone import the archive.

## Explicit test targets

- Compare direct and cumulative-sum onset estimates and objective scores on
  fixed, unlabelled numerical noise and curved fixtures.
- Audit exact zero observations: every candidate has nonpositive correlation,
  so the score remains `-inf`. The archived argmax convention can nevertheless
  return the first candidate (70), which is not evidence of an identified onset.
- Verify early endpoints are invariant when only future observations change,
  holding the supplied already-processed residual fixed.
- Reject nonfinite inputs at the independent reference boundary.
- Verify the candidate eligibility arithmetic in Lean 4. This does not prove
  a Python algorithm, floating-point equivalence, or astrophysical validity.

## Interpretation and remaining work

Agreement on fixtures is not global equivalence or proof of causal preprocessing.
Near-constant data, extreme magnitudes, template boundaries, tie conditions and
numerical ill-conditioning still require adversarial controls. Any estimator
with no finite admissible objective must be treated as an **undefined alignment**
in subsequent scientific analysis; no empirical frequency of this condition is
asserted here. The historical implementation is left unchanged.

M38B-R stays uncalibrated and `approved_for_calibration: false`.
