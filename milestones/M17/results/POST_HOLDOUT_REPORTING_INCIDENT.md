# M17 post-holdout reporting incident

The reused M15 aggregate function returned four legacy prediction-check fields based on the M15 forecast (5–7 passes, aggregate recall 0.59–0.63, INCONCLUSIVE).

Those fields were not used in:
- threshold calibration;
- holdout generation;
- per-replication gates;
- hierarchical bootstrap;
- FPR robustness;
- PASS/INCONCLUSIVE/STRONG_FAIL decision.

The correct M17 prediction checks were computed separately from the preregistered M17 ranges and were already stored under `m17_prediction`.

Actions:
1. preserved the untouched aggregate output as `VERDICT_RAW_CORE.json`;
2. rewrote `VERDICT.json` as a cleaned reporting view containing the scientific metrics, decision, and M17-specific prediction assessment;
3. changed no data, seed, threshold, bootstrap draw, gate, or verdict.

Classification: reporting-label inheritance defect; no scientific-result impact.
