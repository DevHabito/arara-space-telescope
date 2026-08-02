# ARARA-M1 — Implementation audit log

## Incident 001 — Zero residual variance in an exact linear rise

- Found by: unit test before development data generation.
- Original behavior: slope standard error below numerical tolerance caused the t-statistic to be written as zero.
- Mathematical behavior: for a strictly positive slope with zero residual variance, the one-sided t-statistic is unbounded.
- Correction: return `+inf` only for positive slope and zero numerical standard error; return zero for flat or negative slope.
- Scope: numerical edge case in `rolling_slope_t_score`.
- Protocol impact: none.
- Data impact: none; no development or holdout data had been generated.

## Incident 002 — Equality collision between float32 scores and float64 threshold

- Found by: development sanity check before holdout generation.
- Symptom: 11 alerts in 2.000 curves despite a maximum permitted count of 10.
- Cause: the threshold was moved upward by one `float64` ULP after the reference score had already been quantized to `float32`; scalar promotion during comparison could collapse it back onto the reference value.
- Correction: move the threshold upward by one representable value in the score array's own dtype.
- Additional test: explicit `float32` tie/precision test.
- Protocol impact: none.
- Holdout impact: none; holdout remained unopened.
- Freeze impact: the first threshold file and pre-holdout hash manifest are invalid and must be regenerated.
