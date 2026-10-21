# Source-level audit: true onset in the M38B candidate boundary mask

**Status:** demonstrated mask-level dependency; effect on complete scores,
recall, and false-positive rate remains unmeasured.

## Exact source and purpose

Historical source: `milestones/M38B_recovery/arara_m38b.py`,
`score_latent_grid_bank`. The candidate computes `estimated_onset` from the
residual, but also receives `onset`, the true simulated onset (or a virtual
onset assigned to negative curves). It constructs:

```python
positions = endpoints + offsets - estimated_onset
absolute_source = positions + onset
source_valid = (absolute_source >= 0.0) & (absolute_source < n_time)
```

It then multiplies its linear and nonlinear raw templates by `source_valid`.

## Explicit counterfactual

Hold the endpoint at 179, the residual's estimated onset at 80, the window
offsets at -8 through 0, and the curve length at 180. Change **only** the hidden
truth argument.

| True onset | Absolute source indices | Valid mask |
|---|---|---|
| 80 | 171–179 | 9/9 valid |
| 110 | 201–209 | 0/9 valid |

This is a counterexample to the independence of the template mask from the true
onset. It is checked by `tests/test_m38br_oracle_boundary.py`. A narrower
counterexample for the last sample is also proved in
`formal/AraraFormal/OracleBoundary.lean`.

## What the example does not prove

It does **not** establish that this combination occurs often in the generator,
that particular saved M37R or M38B scores are wrong, or the direction/magnitude
of any detection-rate bias. It also does not establish that all use of the true
onset is inappropriate: controls deliberately measure oracle performance.
The candidate, however, is meant to operate without true onset.

## Required next falsification test

Keep the observed residual, reference, estimated onset, whitening parameters,
other hidden inputs, and frozen template bank identical. Vary only the
`true_onset` argument in the real scoring path and compare **candidate**
template masks, scores and first-crossing decisions at all endpoints. Include
late endpoints and out-of-range boundary cases. Use a separate experiment
identity for any corrected statistic; do not reinterpret historical holdouts or
transplant their calibrated thresholds.

Until the independent scorer test and a formally specified causal replacement
are complete, `M38B-R` stays **not authorized** to calibrate. Related: issue #4.

## Originality and methodological distinction

Counterfactual invariance testing and oracle/label leakage audits are standard
methodological checks. This specific dependency and witness concern ARARA's
archived implementation, not a novel mathematical theorem.
