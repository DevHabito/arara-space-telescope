# M38B-R independent projection and computational benchmark

**Scope:** Read-only numerical comparison; no scientific outcomes, thresholds, calibration or holdouts. This audit tests a second implementation of **only the reference projection and matched-filter score**. The rest of the observation-only candidate still uses archived onset estimation and template-bank infrastructure. Do not call this an independent end-to-end detector.

## Mathematics (existing literature, not an ARARA discovery)

For a residual vector `y`, template `t`, and reference `r`:

```text
if ||r||² > epsilon:
    y_perp = y - <y,r> r / ||r||²
    t_perp = t - <t,r> r / ||r||²
else:
    y_perp = y; t_perp = t

score = <t_perp, y_perp> / ||t_perp|| if ||t_perp||² > epsilon else 0
```

Here `epsilon = 1e-12` is inherited from the archived implementation. It is **not** a universal conditioning rule. The archive computes projected template energy as `||t||² - <t,r>²/||r||²`, a difference susceptible to cancellation when `t` and `r` are nearly parallel. The new module independently forms `t_perp` and computes its squared norm directly. This is another numerical algorithm for the same real-valued expression, not proof that either floating-point implementation is always accurate.

## Tests that must not be interpreted as detection performance

- Random, well-conditioned score and retention comparison against the **actual archived** `projected_scores_hypotheses`.
- Reference identically zero, reference energy below cutoff, template identically zero, exactly parallel template, nonfinite/empty/misaligned inputs, target scaling and projected orthogonality.
- A near-parallel synthetic numerical witness where each result must remain finite and differences are recorded rather than hidden or declared successful detection.
- Running the observation-only candidate once with the archival scorer and once with the independent scorer as a substituted calculation, holding all observed inputs fixed.

The fixed integer examples in `formal/AraraFormal/ProjectionWitness.lean` are Lean-checked illustrations of projection geometry in two dimensions. They do **not** prove numerical floating-point stability, quantify calibration, or verify Python automatically.

## Resource benchmark

`python scripts/m38br_projection_benchmark.py` generates a small, unlabelled numerical array with a fixed RNG seed. It measures median wall time for five scored repetitions, Python-traced peak allocations, and the runner process's high-water RSS. The two scoring implementations use the same input. The JSON is saved as a GitHub Actions artifact for inspection.

This is a **projection-only microbenchmark**. The final full bank has a different array size, causal-estimator cost, calibration workload, and memory profile. Extrapolation to 1,000,000 synthetic calibration negatives, mission CPU, or cloud cost is not justified.

## Scientific blockers

The observation-only candidate and independent projector remain uncalibrated. A rigorous prospective M38B-R experiment additionally needs source-independent generator/estimator tests, explicit IEEE numerical policy, full-run benchmark, frozen environment and seeds, veto controls, fresh calibration and untouched holdouts. Issues #4 and #7 remain open.

## References

Classical orthogonal projection, Euclidean inner product, Gram–Schmidt orthogonalization, and conditioning analysis are established numerical linear algebra. See Golub and Van Loan, *Matrix Computations* (4th ed., Johns Hopkins University Press, 2013), and Higham, *Accuracy and Stability of Numerical Algorithms* (2nd ed., SIAM, 2002). No claim is made that these methods originated in ARARA.

## Analytic near-parallel witness and full-bank resource diagnostic

For `r=(1,1,1,1,1,1,1,1)`, `y=(1,-1,1,-1,1,-1,1,-1)`, and `t=r+1.2e-6*(1,0,0,0,0,0,0,0)`, the exact real-valued normalized projected score is `sqrt(8/7)`. The new test checks that the explicit projection implementation reproduces this analytic value (with tolerance), and the runner stores both the archived and independent results and their respective absolute errors. This evaluates **numerical precision**, not signal detection.

The benchmark also runs the uncalibrated observation-only candidate across all 99 nominal endpoints for a **single, arbitrarily generated unlabelled curve** using each projector in turn. It records elapsed seconds and Python-traced peak allocations, and compares their score grids. This is an engineering fixture only: neither calibration sample sizes nor model-derived positives/negatives are run; no FPR, recall, PPV, thresholds, or holdouts are produced. The measurements should not be scaled linearly into a mission or a million-curve budget.
