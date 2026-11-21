# AR-RQ1-P02 — hosted Python 3.12 verification

**Recorded:** 20 November 2026  
**Scope:** A separate verification note. The preregistration and preliminary local result are preserved without amendment.

## GitHub Actions evidence

- Pull Request: https://github.com/DevHabito/arara-space-telescope/pull/11
- Workflow run: https://github.com/DevHabito/arara-space-telescope/actions/runs/44846334208
- Job: `recovery-provenance`, job ID `136666847325`
- Runner: Python `3.12.16`
- Outcome: **54 unittest cases passed**, including seven checks from `tests/test_ar_rq1_p02.py`.
- The regression evaluating all five preregistered gates passed under this interpreter.
- The historical recovery-audit step completed.
- `python scripts/verify_manifest.py` reported: `Manifest verified: all hashes match.`
- The same workflow's Lean-protocol job completed successfully, but it is **not** a Lean formalization of this identifiability experiment.

The test suite checks deterministic generation, shape and bounds, independent fixed-window contrast, class-count bookkeeping, the paired-photometry identifiability condition, the five frozen decision gates, and result SHA-256 consistency.

The precise numerical table in [the preliminary result](AR-RQ1-P02.md) was produced locally on Python 3.13.5 and NumPy 2.3.5. The hosted test independently reran the generator and checked the gates on Python 3.12.16; it did **not** archive a second full JSON payload. Do not claim byte-for-byte cross-version identity of the two output files without comparing those files.

## Scientific boundary

This verification establishes only that the stated synthetic program and checks execute on the registered interpreter. It does not validate a physical telescope, real sensor calibration, probabilistic model for astrophysical artifacts, or out-of-distribution generalization. The simulated label-dependent diagnostic distributions still determine the conditional result by construction.

Existing historical M38B calibration and holdout gaps are unchanged.
