# P0.3 — independent complete-bank engineering audit

This is a pre-outcome evaluation against the historical uncalibrated
`observable_candidate.py` on **constructed unlabelled numerical arrays**.
The [comparison criteria](INDEPENDENT_BANK_COMPARISON_POLICY.md) were saved in
an earlier commit, before this code was authored.

## Independent calculation

`independent_bank.py` builds its own four shape equations and loops through
the sorted latent-index/duration/shape-index hypothesis order. It uses the
source-independent `estimate_direct_hinge` and `score_projected` numerical
routines, rather than imports from the archived M34/M37/M38B estimators or
the earlier `observable_candidate.py`. Its observation-level entrypoint
uses `observed_preprocessing.py` and does not accept simulated truth.

Each endpoint is scored from nine phase samples, converted into eight
AR(1)-filtered template samples, and projected against an observed reference
window. The code evaluates 592 distinct shape/duration/latent combinations
per endpoint: 37 linear (latent-invariant) plus 555 nonlinear combinations.
The full 99-endpoint run has 58,608 computed template scores per curve.
The historical paper protocol lists 73,260 **nominal** slots because its
Cartesian product repeats the latent-invariant linear entries. Neither count
is the statistical number of independent trials.

The independent implementation is intentionally not a production runner.
It returns per-endpoint diagnostics and fitted labels. It does not create
a threshold, report detection, generate signals for calibrated outcomes, or
open holdouts.

## Scientific comparison and explicit incompatibility

The stable numerical fixture comparisons use `rtol = atol = 1e-9` and only
compare selected parameter indices when the leading score exceeds the
second-highest by more than `1e-7`. An exact tie follows sorted
latent-index/duration/shape-index order.

The independent bank deliberately **fails closed** when there is no
admissible positive onset objective: `alignment_defined_grid = false`,
`grid_score_grid = -inf`, and winning labels `-1`. The earlier prototype
still calculates a template score using the first candidate returned by
`argmax`. These two outputs must not be declared universally equivalent;
the difference is an explicit unresolved scientific-design gate.

Near-parallel templates can also differ numerically because the independent
projector forms the orthogonal vector explicitly, while the archived code
subtracts nearly equal energies. This is why no global floating-point
equivalence theorem is claimed.

## Recorded execution results (3 November 2026)

The first implementation at commit `467e803df3ea4431312d72841a3ba0588c308fbc`
had two failed tests out of the nine added cases:
the undefined-onset guard rejected `-inf` before fail-closed reporting.
The [failed run 41717127226](https://github.com/DevHabito/arara-space-telescope/actions/runs/41717127226)
is retained. The policy's tolerances were not relaxed.

After correcting that guard at commit
`ee439a1992175624652ee8228690e0f0d2f25f37`,
the [research-audit run 41717275635](https://github.com/DevHabito/arara-space-telescope/actions/runs/41717275635)
reported 81 passed Python tests, completed Lean 4 compilation and verified
the unchanged source manifest. The nine P0.3 cases include a 99-endpoint
unlabelled one-curve score comparison, a short stable score/index comparison,
future-only data perturbations, invalid/overflow inputs, an undefined-onset
failure state, complete bank counts, and interface/source checks.
No scientific detection performance was measured.

## Verification required

Run the P0.3 unit tests in cloud CI and inspect their actual logs, including
an unlabelled 99-endpoint bank check, a fixed-observation comparison, undefined
onset, future noninterference, malformed input and integer bank counts.
Do not promote a claimed result to PASS until the corresponding commit's
GitHub Actions runs complete.

No new astrophysical literature or discovery claim is introduced. Prior
orthogonal projection, conditioning and template-search methods are listed
in [the bibliography](../../docs/LITERATURE_AND_ORIGINALITY.md).

**M38B:** `NO_OPERATIONAL_VERDICT`.
**M38B-R:** `approved_for_calibration: false`, `execution_permission: not_authorized`.
