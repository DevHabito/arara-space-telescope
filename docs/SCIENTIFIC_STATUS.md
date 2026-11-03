# Scientific Status

This repository is a historical computational research archive for the ARARA
Space Telescope program. It preserves milestone-level code, tests,
preregistrations, result summaries, and SHA-256 provenance from reconstruction
v0.1 through M38B recovery.

## Established Archive-Level Claims

- The packaged repository contains the available source code, tests,
  preregistrations, and metadata needed to inspect the historical ARARA From
  Zero milestone sequence.
- The packaged validation report records 278 passing tests across
  reconstruction v0.1, M1-M37, M37R, M38A, and M38B recovery.
- M37R passed the complete duration-bank simulator protocol preserved in this
  archive.
- M38A identified the latent grid `[0, 0.25, 0.5, 0.75, 1.0]` as structurally
  eligible.
- M38B recovery preserves code and protocol material, but does not contain a
  completed calibration-and-holdout validation.

## Explicit Nonclaims

This repository does not establish that ARARA is:

- an operational space telescope;
- a validated astronomical detector;
- a confirmed observatory instrument;
- a real transient-discovery pipeline;
- superior to established astronomical detection methods;
- validated on physical telescope telemetry or independent sky-survey data.

## Current separate audit — 3 November 2026

A dedicated, unmerged [draft pull request #9](https://github.com/DevHabito/arara-space-telescope/pull/9) records observation-only P0.1/P0.2 engineering diagnostics, additional tests, and limited Lean 4 claims. The exact audit commit, CI logs, failures and open questions are indexed in [RESEARCH_INDEX.md](RESEARCH_INDEX.md). This audit does not supersede historical milestones or change M38B-R from design-only to an authorized calibration experiment.

## Citation Boundary

Future citations should describe this repository as a historical computational
research archive and reproducibility package. Claims about operational
astronomy, telescope hardware, astrophysical discovery, or validated detection
performance require evidence beyond the material preserved here.

## Search Keywords

ARARA Space Telescope, ARARA From Zero, astronomical transients, computational
astronomy, signal processing, preregistered simulation, reproducibility,
research archive, Python, SHA-256 provenance.
