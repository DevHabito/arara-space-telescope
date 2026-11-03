# ARARA research notebook — 3 November 2026

**Research voice:** first-person research record. **Scope:** source inspection, software experiments, mathematical witnesses, and observed GitHub Actions execution. This is not a telescope commissioning report.

## Why I keep this record

I want ARARA to withstand a skeptical reading. That means keeping failed attempts next to successful ones, separating an implementation check from a scientific result, and refusing to treat an impressive test count as evidence of an astronomical discovery. I will not change a threshold or redefine a hypothesis after looking at an outcome and then describe the result as prospective.

This entry records what I can substantiate from the repository and the GitHub Actions logs inspected on 3 November 2026. It does not claim that I personally ran the cloud jobs on a local workstation or that I re-examined every older milestone from first principles.

## What the archive says, and what I checked

The repository's [scientific status](SCIENTIFIC_STATUS.md) describes reconstructed computational milestones through M38B recovery. It reports that M37R passed its **synthetic simulator protocol**, that M38A passed a structural five-point-grid eligibility check, and that M38B lacks completed calibration and holdout validation. Those are distinct statements. My current audit does not independently repeat the full M37R experiment and does not turn the M38A structural check into evidence of detection performance.

The packaged [TEST_REPORT.md](../TEST_REPORT.md) reports 278 tests across 41 historical suites. I subsequently inspected a fresh GitHub Actions `tests` execution on the audit branch: the log itself records 278 passing tests in 41 suites. This confirms that the available regression suites ran in that cloud environment. It does **not** imply that 278 independent astronomical experiments were performed.

### Evidence ledger — confirmed cloud runs

| Question | Evidence at audit commit | Narrow result |
| --- | --- | --- |
| Did the historical regression suites execute? | [GitHub Actions: tests, run 41712840362](https://github.com/DevHabito/arara-space-telescope/actions/runs/41712840362) | 278 passing tests, 41 suites; runner completed successfully |
| Did the new scientific-engineering audit tests execute? | [GitHub Actions: research-audit, run 41712840089](https://github.com/DevHabito/arara-space-telescope/actions/runs/41712840089) | 72 Python tests passed, including ten P0.2 tests |
| Did the Lean 4 modules compile? | Same research-audit run, `lean-protocol` job | `lake build` completed successfully, nine build jobs |
| Did integrity verification complete? | Same research-audit run, `recovery-provenance` job | Manifest hashes matched; status remained `NO_OPERATIONAL_VERDICT` |
| Did all workflows on this exact commit pass? | [Commit `afea7fe56e09f98a8dd45cc5a3431883cd2679c9`](https://github.com/DevHabito/arara-space-telescope/commit/afea7fe56e09f98a8dd45cc5a3431883cd2679c9) | Six of six push workflows concluded successfully |

The audit was made on branch `audit/m38br-independent-onset-20261103`, tracked by [draft pull request #9](https://github.com/DevHabito/arara-space-telescope/pull/9). The historical `milestones/` files were not edited in this audit. The last checked `main` commit was `08d1daea5b3f5c4c8d9df8be340a96ab4786c0ad`. Dates and run IDs refer to observed repository evidence, not to a newly completed M38B-R scientific experiment.

## What I learned by following the data

**Historical implementation.** In `milestones/M38B_recovery/arara_m38b.py`, `evaluate_positive_panel` builds observed target data with a simulated injection. Both positive and negative evaluators supply simulated onset, shape, duration and latent information to the historical scorer. In the negative case, some of these values come from a virtual shape bank rather than the negative star observations. The historical template boundary also depends on true onset. This is a genuine evaluation-design problem, described in [issue #4](https://github.com/DevHabito/arara-space-telescope/issues/4); I will not call that historical candidate observation-only.

**Observed-data preprocessing (P0.1).** I added `experiments/M38B-R/observed_preprocessing.py`, which takes observed target and reference series and calculates baseline normalization, shared-reference subtraction, a residual, a fitted AR(1) coefficient, and a processed reference. It does not request a simulated true signal. Its outputs agreed numerically with the operational outputs of the archived M29 preprocessor on the specific unlabeled fixtures tested. When I changed the archival `raw_signal` input while keeping the observations fixed, the archival diagnostic `processed_signal` changed but its residual, processed reference and fitted parameters did not. This is a source and unit-test result, not a proof for arbitrary physical inputs.

**Onset estimator (P0.1).** The independent direct-sum hinge estimator in `independent_onset.py` agreed with the archived prefix-sum implementation on the tested inputs. A zero residual produced an undefined maximum objective of `-inf`, although the tie convention still selected candidate 70. That index must not be mistaken for a physically identified onset. [Read the onset audit](../experiments/M38B-R/INDEPENDENT_ONSET_AUDIT.md).

**Projection.** `independent_projection.py` computes an explicit vector projection rather than relying solely on the archived subtractive energy expression. An adversarial near-parallel fixture exposed sensitivity to floating-point cancellation. This is a numerical warning, not evidence of better astronomical sensitivity. [Read the projection audit](../experiments/M38B-R/INDEPENDENT_PROJECTION_AUDIT.md).

**Configuration and parameter provenance (P0.2).** A scorer may take only observed curves and yet still be influenced by information supplied indirectly in `cfg` or `params`. In the current numerical tests, adding truth-named dictionary keys did not change the low-level scorer's output. Changing the required `residual_phi` value, however, changed the generated template arrays. The frontend fits `residual_phi` from the observed baseline, whereas the low-level scorer cannot authenticate a caller-supplied coefficient. The separate `provenance_contract.py` reports changes to historically specified geometry. This checker is diagnostic; it does not make the entire prospective experiment immutable. [Read the P0.2 dataflow audit](../experiments/M38B-R/PROTOCOL_DATAFLOW_AUDIT.md).

**Formal mathematics.** Lean 4 checked the exact-integer or discrete claims currently expressed in the library: hinge eligibility, a fixed-coefficient one-step AR(1) prefix invariant, and a counterexample when the coefficient changes. I do not infer a proof about the NumPy implementation, IEEE floating-point arithmetic, or physical light curves from those theorems.

## What did not work

I am keeping the failed checks in a separate [failure and limitation register](FAILURE_AND_LIMITATIONS_REGISTER.md). They include a Lean syntax failure involving the reserved identifier `at`, an initial overflow test that overflowed **before** entering the function under test, the unresolved degeneracy of an onset statistic, the existing oracle leakage in the historical M38B scorer, and numerical sensitivity of a near-parallel projection.

The Lean syntax error is visible in [failed research-audit run 41711129381](https://github.com/DevHabito/arara-space-telescope/actions/runs/41711129381). The corrected Lean source and corrected finite-input overflow regression were subsequently verified in the successful audit runs. I do not hide the failed run merely because the latest build is green.

### Documentation integrity correction

During this same documentation pass, I made a change that the archive's checksum policy does not allow: I added navigation links to the root `README.md` and `docs/SCIENTIFIC_STATUS.md`. The [research-audit run 41714898482](https://github.com/DevHabito/arara-space-telescope/actions/runs/41714898482) reported two hash mismatches. This is a legitimate integrity failure, not a defect in the scientific equations. I restored those two protected files from the unchanged `main` without editing or regenerating the source manifest. The new research pages remain accessible from this index, the M38B-R experimental README, and the draft PR. The restored source was subsequently checked at commit `7aa2619ce32f00b531c4cb7e4a2cff98d2d95cf9`: [research-audit run 41715319051](https://github.com/DevHabito/arara-space-telescope/actions/runs/41715319051) passed its 72 Python tests, nine-job Lean build and manifest verification; [tests run 41715319012](https://github.com/DevHabito/arara-space-telescope/actions/runs/41715319012) passed the 278 historical tests in 41 suites. I record both the failing and successful runs.

## What remains unproven

- M38B has no completed, source-verified operational calibration and holdout verdict in this archive.
- M38B-R has **not** run calibration, holdouts or a prospective detection-power study. Its `PROTOCOL_DRAFT.json` says `execution_permission: not_authorized`.
- There is no independently reconstructed full-bank, end-to-end causal detector. The observation-only prototype still imports archived estimation/projection components.
- The full prototype configuration, executable runner, statistical stopping rules, seeds, exact environment and artifact verification are not yet jointly frozen for a prospective run.
- No real-sky false-alert rate, completeness, precision, photometric noise budget, telescope pointing response, read noise, dark noise, detector hardware or flight readiness is established.
- Passing software tests does not establish the scientific validity of the simulator's distributional assumptions.

## The work order I will follow

1. **P0.3 — source-independent complete-bank audit.** Rebuild template generation, filtering, projection and tie-breaking independently. Fix numerical acceptance criteria *before* examining discrepancy outputs. Compare ordinary and adversarial unlabelled fixtures.
2. **Numerical policy.** State exact IEEE assumptions, conditioning thresholds and failure classifications. Treat near-parallel templates, undefined onset objectives, constant baselines and extreme finite magnitudes explicitly.
3. **Provenance closure.** Trace raw measurement identity, baseline quality, parameter estimation, configuration, negative/positive generator separation and every statistic reaching the final decision.
4. **Prospective freeze.** Freeze the new runner, environment, source dependencies, seeds, sample counts, acceptance gates and independent verification scripts in a distinct M38B-R preregistration. Keep failed attempts visible.
5. **Only after those gates:** consider authorization for calibration, then untouched holdouts, followed by genuinely independent instrument/real-data validation. No stage inherits permission from a passing software CI run.

I will keep [existing literature and ARARA-specific constructions](LITERATURE_AND_ORIGINALITY.md) separate. A mathematical technique that existed before this project is not a new physical law merely because I have implemented it.

**Research decision, 3 November 2026:** M38B remains `NO_OPERATIONAL_VERDICT`. M38B-R remains design/audit only, `approved_for_calibration: false`. No astrophysical discovery or operational telescope capability is claimed.
