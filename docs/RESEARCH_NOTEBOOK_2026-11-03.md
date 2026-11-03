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

### P0.3 — independent full-bank diagnostic (3 November 2026)

I fixed the numerical comparison rules *before* implementing the second bank.
The criteria are in [INDEPENDENT_BANK_COMPARISON_POLICY.md](../experiments/M38B-R/INDEPENDENT_BANK_COMPARISON_POLICY.md), committed separately at `8c621f137f87882c614478dfbbcae7cf0a64426a`.
I set a stable-fixture maximum-score comparison of `rtol=atol=1e-9`,
an index agreement check only for leading-score margins above `1e-7`,
and special treatment for undefined onset and near-parallel projections.
I did not change these criteria in response to later test results.

I then implemented [independent_bank.py](../experiments/M38B-R/independent_bank.py).
It independently generates linear, power-law, exponential and logistic shapes;
AR(1)-filters nine raw template samples into eight confirmation samples;
uses the direct-sum onset estimator and explicit reference projection; and
selects the winning hypothesis in the specified tie order. It imports no
historical milestone scorer or simulator oracle. The complete 99-endpoint
diagnostic fixture covers 58,608 computed template combinations per curve,
without invoking a scientific positive/negative generator, calibration or
holdout. The independent observation-level entrypoint takes star observations
only, fits the needed preprocessing parameters, and returns an **uncalibrated**
score and diagnostics.

The first [research-audit run 41717127226](https://github.com/DevHabito/arara-space-telescope/actions/runs/41717127226)
failed two of the nine new P0.3 tests. I had written a condition that
mistakenly classified the `-inf` objective of an undefined onset as a
malformed number. The seven other tests passed, including the stable
full-grid comparison. This was my implementation error, not a failed
astronomical detection hypothesis.

I corrected only the faulty guard in commit
`ee439a1992175624652ee8228690e0f0d2f25f37`; the original tests and
frozen numerical criteria remained unchanged. The subsequent
[research-audit run 41717275635](https://github.com/DevHabito/arara-space-telescope/actions/runs/41717275635)
reported **81/81 passing Python audit tests**, a successful Lean 4 build
and matching manifest hashes. It retains the archived M38B
`NO_OPERATIONAL_VERDICT`. These numerical fixtures confirm only specific
software properties; they do not establish astronomical sensitivity.

There is also an important limitation in the word *causal*: while finite
future perturbations do not change earlier scores, the current **offline**
input validation checks all 180 samples before returning. A later missing
or nonfinite measurement therefore rejects even an unchanged early prefix.
I added a negative regression for this behavior, F16. Strict online
causality, streaming quality control and handling of missing data are not
yet established.

The new scorer *deliberately differs* from the earlier observation-only
prototype when no positive hinge objective exists: it sets the score to
`-inf` and the parameter labels to `-1`. The earlier prototype can still
score a template at a first-candidate default. That difference is explicit
and remains a design choice requiring a prospective policy. Neither
implementation has a calibrated threshold. See
[P0.3 audit](../experiments/M38B-R/INDEPENDENT_BANK_AUDIT.md)
and [failure entries F14–F15](FAILURE_AND_LIMITATIONS_REGISTER.md).

### P0.4 — near-singular projection and missing-data position (3 November 2026)

I wrote the [P0.4 diagnostic policy](../experiments/M38B-R/P04_NUMERICAL_AUDIT_POLICY.md)
before implementing the tests. It fixes the analytic eight-element witness,
scale factors `0.1` and `2.0`, the `1e-12` inherited energy floor and
the numerical acceptance bounds. I did not reinterpret a disagreement
as agreement.

The [cloud audit run 41720056181](https://github.com/DevHabito/arara-space-telescope/actions/runs/41720056181)
at commit `e63da1c168341014ff87bdea495f3c5151163851` reported
nine new P0.4 tests passing, **91 passing audit tests in total**,
a successful Lean build, matching historical manifest hashes and the
unchanged `NO_OPERATIONAL_VERDICT`.

The near-parallel comparison is especially informative. An eight-element
constructed vector has an exact expected normalized projected score
`sqrt(8/7) = 1.0690449676496976`. The independently constructed
projection returned that value to the precision shown in the CI log.
The older subtractive-energy calculation returned `1.0685306041827185`,
an absolute difference from the analytic reference of
`0.0005143634669790842`. Both calculations used the same fixed input.
I am not interpreting this engineering witness as evidence of a new
physical signal or as a global proof that one implementation is superior.
The numerical conditioning problem and these observations are recorded
in [the P0.4 report](../experiments/M38B-R/P04_NUMERICAL_AUDIT.md).

Another test found a discontinuity caused by the existing absolute
energy cutoff: multiplying a near-parallel template and reference by
`0.1` makes its reported score zero when the projected energy falls
below `1e-12`. The same mathematical normalized score should be
scale-invariant in exact arithmetic away from such gating. I have not
changed the cutoff or invented a physically justified replacement.
This question is F17; the archived near-singular discrepancy is F18.

For missing values, I added
[`numerical_quality.py`](../experiments/M38B-R/numerical_quality.py),
a read-only time-position classifier. It distinguishes a nonfinite
measured prefix from an invalid sample that lies only in the future
of the requested endpoint. It neither imputes data nor bypasses the
existing batch scorer's whole-series rejection. F16 therefore remains
open: the implementation does not yet have a streaming or missing-data
policy I could fairly call operational.

### P0.5 — observed-prefix scoring without future-sample inputs (3 November 2026)

I formalized the acceptance tests in
[P05_PREFIX_CONTRACT_POLICY.md](../experiments/M38B-R/P05_PREFIX_CONTRACT_POLICY.md)
at commit `72d241d00293138f5499a78c0d5d566eb1d6ad5a` before
implementing the new interface. I rejected the tempting shortcut of
padding short input series with zeros: a detector claiming to depend only
on what has been observed should not need fabricated future measurements.

The experimental [`observed_prefix.py`](../experiments/M38B-R/observed_prefix.py)
now accepts precisely samples `0..endpoint` for an endpoint in the
historical range `81..179`. It uses the 50-sample baseline processor,
the independent causal onset reference and the complete independent
template bank. I changed the latter's required minimum input length to
the final requested endpoint, not a hard-coded 180. The existing batch
entrypoint remains unchanged, including its whole-series finiteness check.

In [research-audit run 41721601276](https://github.com/DevHabito/arara-space-telescope/actions/runs/41721601276)
at commit `07b9f3226dbae5f273da26d63b84f4f0a4aded44`, **102 Python audit
tests passed**, including eleven P0.5 tests, and Lean 4 and manifest
verification succeeded. On a constructed, finite, unlabelled nine-star
fixture, every prefix output at endpoints 81, 83, 110 and 179 matched the
corresponding full-batch output **exactly**, not just within a tolerance.
A future NaN made the separate full-batch scorer reject its series, but
the unchanged valid prefix for endpoint 83 scored identically to the clean
case. A NaN inside that measured prefix was rejected as required.

This is a meaningful improvement in **input-level causal isolation**.
It is not evidence that the old batch entrypoint has changed; the
low-level bank can still accept a supplied array longer than a requested
diagnostic endpoint. The strict contract exists on the new high-level
prefix entrypoint only. I cannot claim that a static prefix function
implements a production streaming telescope, low-latency acquisition,
clock synchronization or recovery from missing past observations.
These boundaries remain open in F16 and F19. See the full
[P0.5 audit](../experiments/M38B-R/P05_PREFIX_AUDIT.md).

### P0.6 — declared cadence order, missing-past policy and an adversarial failure

I wrote [the cadence policy](../experiments/M38B-R/P06_SEQUENTIAL_CADENCE_POLICY.md)
at commit `6815ce4dc937f0ac7360db658113c9e688ad8465`
before implementing a sequential ledger. The new
[`sequential_cadence.py`](../experiments/M38B-R/sequential_cadence.py)
takes explicit zero-based consecutive cadence numbers and declared
monotonically increasing time labels, copies finite measured frames,
and scores only the latest prefix through P0.5. It permanently blocks
a segment on a malformed or missing frame instead of filling data
that were never observed.

The first [research-audit run 41723252836](https://github.com/DevHabito/arara-space-telescope/actions/runs/41723252836)
passed 114 tests, including twelve new P0.6 tests. Scoring at cadences
81, 83 and 179 matched the direct prefix computation exactly in
those deterministic unlabelled fixtures. The data contain no
astronomical detection labels.

I added a separate adversarial case for an irregular nested input
whose NumPy conversion fails before normal shape checking. That test
caught a real defect: [run 41723477963](https://github.com/DevHabito/arara-space-telescope/actions/runs/41723477963)
recorded **one failure among 115 tests** because the input raised
`ValueError` but left the ledger unblocked. I kept the test and fixed
the conversion boundary without weakening the earlier contract.
The [corrected run 41723628328](https://github.com/DevHabito/arara-space-telescope/actions/runs/41723628328)
reported **115 passing audit tests**, Lean 4 compilation and intact
historical hashes. This mistake and its correction are F20 in the
[failure register](FAILURE_AND_LIMITATIONS_REGISTER.md).

A declared timestamp is still just metadata from the caller. It is
not authenticated UTC, exposure time, observatory telemetry or
proof that a camera really captured a sample when the number says
it did. That unsolved provenance question is F21. The ledger has no
instrument source, transport, retries, persistence or physical
timing-error budget. This is a stronger input-order audit, not a
space telescope running in real time. See the full
[P0.6 engineering report](../experiments/M38B-R/P06_SEQUENTIAL_CADENCE_AUDIT.md).

### P0.7 — declared exposure envelopes and an in-memory integrity chain (3 November 2026)

I committed [the P0.7 acceptance policy](../experiments/M38B-R/P07_EXPOSURE_PROVENANCE_POLICY.md)
at `4689a513e7eef4b4eba09ccbc6a2ddbcc88248a9`, *before*
implementing any test. Its purpose is limited: check whether
producer-declared exposure intervals are internally consistent after
including producer-declared absolute uncertainty bounds, and whether
accepted numerical frames remain consistent with their metadata.

The new [exposure provenance wrapper](../experiments/M38B-R/exposure_provenance.py)
checks fixed labels for session, instrument, target and clock, positive
exposure duration under declared error bounds, definite separation
between neighboring exposures, and consecutive frame order through
the P0.6 ledger. It computes a versioned SHA-256 chain over each
accepted binary64 frame and the canonical representation of its
declared time/identity metadata. A mismatch blocks subsequent
scoring. No scientific threshold or telescope source is consulted.

In the first [research-audit run 41725557607](https://github.com/DevHabito/arara-space-telescope/actions/runs/41725557607),
all **130 Python audit tests passed**, including fifteen P0.7 cases.
However, **Lean 4 failed to compile** the two integer witnesses written
with `decide`; the compiler could not synthesize their decidability.
The change to explicit arithmetic tactics fixed the build without
changing its statement. The [corrected run 41725739124](https://github.com/DevHabito/arara-space-telescope/actions/runs/41725739124)
then passed all 130 Python audit tests, a **ten-job Lean build**, and
the unchanged source-manifest check. The failed and corrected versions
are both recorded as F22, not silently collapsed into a green result.

This is a traceable internal consistency check, **not authenticated
provenance**. An untrusted source can invent an instrument name, time
bounds, error bounds and sample values and then hash all of them.
The code cannot establish their truth. Nor do its `<` comparisons
prove a general IEEE-754 interval-arithmetic theorem; the Lean result
is deliberately restricted to exact natural-number arithmetic.
The unresolved questions F23–F24 and the prior F21 must remain open.
See the [P0.7 report](../experiments/M38B-R/P07_EXPOSURE_PROVENANCE_AUDIT.md)
and the separate [literature review](LITERATURE_AND_ORIGINALITY.md)
for the preexisting scientific and engineering methods.

## What did not work

I am keeping the failed checks in a separate [failure and limitation register](FAILURE_AND_LIMITATIONS_REGISTER.md). They include a Lean syntax failure involving the reserved identifier `at`, an initial overflow test that overflowed **before** entering the function under test, the unresolved degeneracy of an onset statistic, the existing oracle leakage in the historical M38B scorer, and numerical sensitivity of a near-parallel projection.

The Lean syntax error is visible in [failed research-audit run 41711129381](https://github.com/DevHabito/arara-space-telescope/actions/runs/41711129381). The corrected Lean source and corrected finite-input overflow regression were subsequently verified in the successful audit runs. I do not hide the failed run merely because the latest build is green.

### Documentation integrity correction

During this same documentation pass, I made a change that the archive's checksum policy does not allow: I added navigation links to the root `README.md` and `docs/SCIENTIFIC_STATUS.md`. The [research-audit run 41714898482](https://github.com/DevHabito/arara-space-telescope/actions/runs/41714898482) reported two hash mismatches. This is a legitimate integrity failure, not a defect in the scientific equations. I restored those two protected files from the unchanged `main` without editing or regenerating the source manifest. The new research pages remain accessible from this index, the M38B-R experimental README, and the draft PR. The restored source was subsequently checked at commit `7aa2619ce32f00b531c4cb7e4a2cff98d2d95cf9`: [research-audit run 41715319051](https://github.com/DevHabito/arara-space-telescope/actions/runs/41715319051) passed its 72 Python tests, nine-job Lean build and manifest verification; [tests run 41715319012](https://github.com/DevHabito/arara-space-telescope/actions/runs/41715319012) passed the 278 historical tests in 41 suites. I record both the failing and successful runs.

## What remains unproven

- M38B has no completed, source-verified operational calibration and holdout verdict in this archive.
- M38B-R has **not** run calibration, holdouts or a prospective detection-power study. Its `PROTOCOL_DRAFT.json` says `execution_permission: not_authorized`.
- A source-independent complete-bank **diagnostic** and a strictly prefix-bounded experimental entrypoint now exist, with fixed-fixture comparisons checked in CI. There is still no prospectively frozen production runner, continuous acquisition system, quality-masked missing-data policy, general floating-point proof, instrument observation pipeline or calibrated end-to-end detector; the earlier observation-only prototype continues to import archival components.
- The full prototype configuration, executable runner, statistical stopping rules, seeds, exact environment and artifact verification are not yet jointly frozen for a prospective run.
- No real-sky false-alert rate, completeness, precision, photometric noise budget, telescope pointing response, read noise, dark noise, detector hardware or flight readiness is established.
- Passing software tests does not establish the scientific validity of the simulator's distributional assumptions.

## The work order I will follow

1. **P0.3 implementation checked on unlabelled fixtures; further adversarial review remains.** I reconstructed the bank, filtering, projection and tie-breaking independently and compared both shortened and full 99-endpoint numerical fixtures. Next I must audit ill-conditioned cases, tie transitions, independent parameter provenance and IEEE error behavior without changing the already recorded criteria.
2. **P0.4 numerical diagnosis completed for declared fixtures; broader policy remains open.** I now have an analytic near-parallel counterexample, a scale-gate test and a read-only missing-position classifier. I have not established global IEEE error bounds, the physical meaning of the fixed cutoff, or a missing-data strategy.
3. **P0.7 declared exposure and integrity checks tested; physical provenance remains open.** The in-memory wrapper checks consecutive samples, declared time-error envelopes and a versioned hash chain. I still lack an authenticated hardware clock, a verified uncertainty budget, raw instrument/target identity, transport integrity and independently examined observations.
4. **Prospective freeze.** Freeze the new runner, environment, source dependencies, seeds, sample counts, acceptance gates and independent verification scripts in a distinct M38B-R preregistration. Keep failed attempts visible.
5. **Only after those gates:** consider authorization for calibration, then untouched holdouts, followed by genuinely independent instrument/real-data validation. No stage inherits permission from a passing software CI run.

I will keep [existing literature and ARARA-specific constructions](LITERATURE_AND_ORIGINALITY.md) separate. A mathematical technique that existed before this project is not a new physical law merely because I have implemented it.

**Research decision, 3 November 2026:** M38B remains `NO_OPERATIONAL_VERDICT`. M38B-R remains design/audit only, `approved_for_calibration: false`. No astrophysical discovery or operational telescope capability is claimed.
