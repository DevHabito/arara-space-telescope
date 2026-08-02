# ARARA independent reconstruction v0.1

This is an independent reconstruction from the surviving ARARA documents. It is **not** a reproduction of the deleted code and does not inherit any old numerical result.

## Run

```bash
python -m arara.run_audit results
pytest -q
```

## Epistemic rules

1. Every undefined legacy implementation detail is treated as unknown.
2. Synthetic, analytic, real-sky, and engineering evidence are kept separate.
3. The same evaluation horizon rule is applied to positives and negatives.
4. Lead time uses the first threshold crossing.
5. Housekeeping is generated independently of astrophysical class.
6. FLOCK requires candidate-level coincidence probabilities; event-window FPR is not silently substituted.
7. No 6U or 12U feasibility verdict is issued without preserved component-level inputs.

See `results/EXECUTION_REPORT.md` after execution.
