# P0.2 — Runtime provenance boundary and protocol geometry audit

**Status:** Engineering-only, read-only scientific diagnostics. No calibration,
holdout access, new scientific threshold, or astronomical performance estimate.

## Code-path audit

1. `M38B_recovery/arara_m38b.py::evaluate_positive_panel` constructs
   measured `observed` from a simulator injection, then sends `panel.onset`,
   `panel.latent_u`, `panel.true_shape_index`, and `panel.duration` to the
   archived scorer. This is the *historical* implementation, not the new
   observation-only frontend.
2. `evaluate_negative_family` uses `generate_negative_family` for measured
   `data.y`, then `generate_virtual_shape_bank` to obtain simulated
   metadata. The historical scorer receives the virtual onset/latent/duration.
   Changing these while holding `data.y` fixed is a valid **code** leakage
   counterfactual, not a physical redefinition of the same simulated event.
3. The experimental `observed_preprocessing.preprocess_observations` receives
   only observed star data and baseline size; fitted `residual_phi` is a
   function of measured baseline observations.
4. `observable_candidate.score_observation_only` directly accepts a
   caller-supplied `params["residual_phi"]` and a configurable `cfg`. It
   ignores extraneous truth-named keys in the parameter dict, but this is not
   proof that the required `residual_phi` was estimated without labels.
5. The low-level scorer checks endpoint bounds and eight-sample window size,
   but permits shortened endpoint grids used for small numerical fixtures.
   An accepted fixture is not the complete M38B historical search over 99
   endpoints; use of it for scientific calibration would change experiment
   identity and effective maximum-search multiplicity.

## Newly isolated reference geometry

`provenance_contract.historical_geometry_findings` records departures from
specific, opened historical source definitions: M32 candidate-onset/split
settings, M34 endpoints, M29/M2 baseline, and the eight-sample window. This
checker is deliberately read-only and does not call the detector, recalculate
scores, set thresholds, approve calibration or retroactively freeze M38B-R.
It is **not** a complete prospective protocol verifier. Additional dimensions,
seed identities, environments, checksums and statistical gates remain
outstanding.

## Adversarial checks (unit tests, not science)

- Hidden truth metadata appended as *extra* `params` keys has no effect on the
  current low-level scorer for unchanged operational inputs.
- Holding measured residual/reference fixed, varying only caller-supplied
  `residual_phi` can change actual generated template arrays. This
  establishes a parameter-provenance requirement, not simulator-oracle leakage
  in the observation-only frontend.
- Changing the time grid, selection split, onset candidate limits or baseline
  length is detected by the audit checker.
- Batch permutation should permute output curve order without cross-contamination.
- A missing required `residual_phi` does not receive an arbitrary default.

## Scientific decision

The observation-only frontend is a candidate preprocessing boundary, but the
experimental statistic remains uncalibrated and not independently reconstructed
end-to-end. An operational run must use an immutable, separately preregistered
configuration with independently checked parameter provenance. Do not reuse
thresholds from M37R or M38B.

**M38B-R remains `approved_for_calibration: false`.**
