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

## Usage

```bash
python -m unittest discover -s tests -p 'test_m38br_preflight.py' -v
python scripts/m38br_preflight.py
```

Both commands use only the standard library and generate no observational data.

## Literature and originality

Matched filtering, linear projections, SHA-256, threshold calibration and held-out evaluation precede ARARA. The particular generator, bank configurations and detector decisions are ARARA-specific implementations. See `docs/LITERATURE_AND_ORIGINALITY.md` and `docs/RESEARCH_GLOSSARY.md`.
