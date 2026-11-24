# P0.5 — observed-prefix contract (criteria recorded before implementation)

**Date:** 3 November 2026. **State:** engineering audit design, not a prospective detection experiment. I will record negative tests and the original code failure if any assertion fails. I will not change numerical acceptance criteria after observing test discrepancies.

## Problem I am testing

P0.4 showed a concrete gap between a computation that uses only past samples in its mathematical score and a *batch interface* that refuses all earlier endpoints when a later sample contains NaN or Inf. The current scorer also insists on a 180-sample array even for endpoint 81. Merely masking future values or padding the array with zeros would conceal rather than fix this boundary.

The contract below deliberately **does not fill or mask future measurements**. The new public function must receive only samples 0..endpoint, inclusive. It must reject longer arrays, so callers cannot accidentally pass future metadata disguised as observations. This is a software-level prefix-input boundary, not telescope timing or flight hardware.

## Fixed implementation contract

1. Add `score_observed_prefix(stars, *, endpoint)` in a new module. `stars` is a finite three-dimensional array `(curve, target+reference stars, sample)`, whose last axis is **exactly endpoint+1**. `endpoint` is a Python integer between **81 and 179**, inclusive. Values outside these conditions raise `ValueError`. Booleans and floating-point endpoints are not silently converted to integers.
2. The path uses the existing source-independent `preprocess_observations` with its **fixed 50-sample baseline**, `IndependentBankConfig(endpoints=(endpoint,))`, and `score_independent_bank`. It does not import the historical scorer or accept true simulated onset, labels, physical shape, or hidden injection data. It performs no new fit on future observations.
3. Permit `score_independent_bank` to evaluate a residual array whose final index is at least its configured maximum endpoint; **do not** require a full 180 measurements when the requested diagnostic endpoint is earlier. Preserve its other shape, finite-data, AR-coefficient, template-family and geometry checks. The default full configuration still requires 180 samples.
4. Keep the existing **batch** `score_independent_observed_stars` unchanged and its whole-series validation explicit. Do not claim that the old interface became streaming-capable.

## Acceptance tests fixed here

- **Full-series equivalence:** for a deterministic, finite, constructed nine-star fixture with baseline noise and a positive numerical ramp (not simulated physical positives), the prefix endpoint scores and all diagnostics must be **bitwise equal** to the matching endpoint columns from the current independent full-batch result, for endpoints 81, 83, 110 and 179. Same Python/NumPy runner; no relaxed numeric tolerance.
- **Missing future:** on the same constructed full series, set a sample strictly after endpoint 83 to NaN, while preserving measured prefix 0..83. The current batch route must reject the full input. The new prefix route receives only the valid 84-sample slice and produces exactly the clean full-batch endpoint-83 outputs. This is *not* imputing the NaN or hiding a missing measurement within the observed prefix.
- **Invalid measured prefix:** a NaN at sample 25 or at the exact requested endpoint must cause prefix rejection. No scores or labels are returned for an incomplete measured prefix.
- **No future arguments:** reject both an input shorter than endpoint+1 and an input longer than endpoint+1, even if its additional values are finite. Disallow invalid endpoint types/ranges, malformed array dimensions and too few reference stars.
- **Undefined onset:** constant finite prefix input must return an explicit undefined-alignment result with score `-inf` and selected labels `-1`, without a false detected event.
- **Isolation and provenance:** permuting curves permutes per-curve output arrays exactly; the public prefix function accepts only `stars` and keyword-only `endpoint`. It does not open or import the simulator or the historical scorer. No data are mutated.
- **Historical regression:** the full 278-test archive suite, research audit suite, Lean 4 build and source manifest must be checked on the final exact commit in GitHub Actions. A green check on a parent commit is not proof of the final head.

## Explicit limits

This endpoint-specific interface can supply a **mathematically prefix-bounded diagnostic** without accessing samples beyond the requested endpoint. It has no sequential acquisition loop, no transport protocol or instrument clock, no missing-data recovery rule, no error bar for astrophysical measurements, no accepted physical noise model and no frozen operational calibration. The 180-sample batch prototype remains unchanged. The independent numerical projection retains the conditioning and absolute-energy floor problems documented in F17–F18. The physical and statistical gates are unchanged.

**M38B:** `NO_OPERATIONAL_VERDICT`. **M38B-R:** `approved_for_calibration: false`; `execution_permission: not_authorized`. No calibration or holdout read is permitted.
