# ARARA-M38A — Execution audit after freeze

## Scientific execution

- No positive curves were generated.
- No negative curves were generated.
- No FPR calibration was performed.
- No holdout was opened.
- Candidate grids were tested in the preregistered order.
- K=2 failed the full-curve gate.
- K=3 passed the full-curve gate but failed the local confirmation-window gate.
- K=5 was the first grid to pass every gate.
- Larger grids were not locally audited because the protocol freezes the first eligible grid.

## Numerical execution

- All calculations used float64.
- The local exhaustive audit covered 1,491,090,084 structural combinations.
- The 512 preregistered worst mesh cells were continuously refined.
- All 512 differential-evolution runs reported success.

## Reporting notation

Section 8 of the frozen preregistration contains the typographical string `phi in [0,0,8]`.
The machine-readable specification and Section 9 define the intended frozen range unambiguously as `0.0 <= phi <= 0.8` with step `0.025`.
No computational parameter was changed.
