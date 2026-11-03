# M38B-R — prospective protocol design (not an experiment result)

This directory prepares a separately identified reconstruction of ARARA's uncompleted M38B latent-grid bank. **No calibration or holdout has been run for M38B-R.** The archived M38B status remains `NO_OPERATIONAL_VERDICT`.

## Why a separate experiment?

The historical M38B specification used random roots 2026090501–2026090504; the recovered script uses 2026090601–2026090604. Changing random roots means a different execution. Neither historical code nor results are edited here.

## Read-only preflight scope

- Check all 33 archived M38B-recovery files against `SOURCE_FREEZE.json`, using the repository's historical SHA-256 inventory.
- Flag unlisted executable, configuration or report files. Do not overwrite hashes, generate scores, create curves, or open holdouts.
- Check the fixed five-point latent grid, endpoint/duration dimensions, synthetic SNR, latency, original sample sizes, and root-seed separation.
- Always return `approved_for_calibration: false`; integrity is a prerequisite, not permission for a scientific run.

The manifest anchors the archived implementation to Git commit `840ac58cb9be1b5e99726bfdd45549ef0a7f5ae7`, but it **does not** freeze any new M38B-R runner or its environment.

## Counts and interpretation

The candidate has 73,260 nominal slots (99 endpoints × 4 shapes × 37 durations × 5 grid points), but the linear shape is independent of u. The archived implementation therefore computes 58,608 candidate template scores per curve and 14,652 control scores per curve. These counts describe work units, **not** equivalent independent trials or scientific detection power.

## Blocking conditions

1. Freeze an exact Python runtime and dependency hashes; verify installation in the intended cloud runner.
2. Benchmark CPU time and peak RAM with synthetic benchmark fixtures, without examining prospective scientific outcomes. Keep all sample sizes unchanged.
3. Build separate output-only-once checkpoint, seed, threshold, count, and holdout-verdict validators. No resumed job may alter a frozen input or replace an existing result.
4. Independently verify that the source and runner agree on the gates, positive strata, negative families, seed derivation, confidence intervals and veto decisions.
5. Publish a **separate prospective M38B-R preregistration** freezing the full runner, seed plan, implementation, environment, and gates before any scientific calibration or holdout.
6. Preserve negative findings and invalid runs. A passing preflight cannot be called an operational detector pass.

The proposed random roots in `PROTOCOL_DRAFT.json` are not yet authorized for execution.

## Current audit notes — 3 November 2026

The source-independent onset reference, observation-only baseline processor, historical-geometry checker, and Lean 4 causality witnesses are recorded under [the research index](../../docs/RESEARCH_INDEX.md). Read the [research notebook](../../docs/RESEARCH_NOTEBOOK_2026-11-03.md) alongside the [failure register](../../docs/FAILURE_AND_LIMITATIONS_REGISTER.md). These are pre-outcome software and mathematical audits only. They do not authorize calibration, thresholds, holdouts, physical astronomy claims, or retroactive changes to this draft protocol.

## Independent full-bank numerical reference — P0.3

The new [complete-bank audit](INDEPENDENT_BANK_AUDIT.md) and
[precommitted comparison policy](INDEPENDENT_BANK_COMPARISON_POLICY.md)
document the source-independent diagnostic scorer, its 99-endpoint
unlabelled fixture, numerical equivalence bounds and the explicit divergence
when the hinge onset is undefined. A first implementation error was preserved
as [F14](../../docs/FAILURE_AND_LIMITATIONS_REGISTER.md) and subsequently
corrected in CI. This does not freeze an experiment runner or authorize
calibration or holdouts. Do not reuse any historical thresholds.

## Conditioning and missing-sample audit — P0.4

I recorded the [P0.4 numerical criteria](P04_NUMERICAL_AUDIT_POLICY.md)
before constructing the new tests. The
[P0.4 evidence report](P04_NUMERICAL_AUDIT.md) contains the actual
near-parallel computed scores, an analytic reference, the absolute
energy-gate counterexample and the missing-sample classification limits.
The read-only `numerical_quality.py` module marks invalid observed prefixes
versus future-only missing samples; it does **not** replace preprocessing,
repair data, or authorize a change in operational detector behavior.
The conditions F16–F18 remain unresolved scientific-design limits.

## Strict observed-prefix numerical diagnostics — P0.5

I added a [precommitted prefix policy](P05_PREFIX_CONTRACT_POLICY.md)
and [P0.5 verification report](P05_PREFIX_AUDIT.md). The new experimental
`observed_prefix.py` accepts only measured observations through its
requested endpoint; its finite-prefix outputs matched the independent
batch calculation exactly in the four unlabelled endpoints tested.
The old batch interface still rejects future nonfinite samples and the
low-level scorer remains a numerical diagnostic rather than a live
instrument. These distinctions are recorded as [F16 and F19](../../docs/FAILURE_AND_LIMITATIONS_REGISTER.md).
No thresholds, holdouts or calibration inputs were read.

## Sequential cadence and time-label audit — P0.6

I fixed the [P0.6 order and gap policy](P06_SEQUENTIAL_CADENCE_POLICY.md)
before implementing the [sequential ledger](sequential_cadence.py).
The [P0.6 audit report](P06_SEQUENTIAL_CADENCE_AUDIT.md) records
the initially passing tests, a later ragged-input failure, the
source correction and the separate successful rerun. The ledger
rejects non-consecutive sample indices and invalid frames without
silently filling gaps. The timestamps are **unverified metadata**;
physical clock calibration and actual continuous hardware acquisition
remain unresolved in [F21](../../docs/FAILURE_AND_LIMITATIONS_REGISTER.md).
No scientific experiment, calibration, threshold or holdout was run.

## Usage

```bash
python -m unittest discover -s tests -p 'test_m38br_preflight.py' -v
python scripts/m38br_preflight.py
```

Both commands use only the standard library and generate no observational data.

## Literature and originality

Matched filtering, linear projections, SHA-256, threshold calibration and held-out evaluation precede ARARA. The particular generator, bank configurations and detector decisions are ARARA-specific implementations. See `docs/LITERATURE_AND_ORIGINALITY.md` and `docs/RESEARCH_GLOSSARY.md`.
