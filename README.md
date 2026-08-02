# ARARA Space Telescope

Historical computational research archive for the ARARA From Zero program.

This repository preserves source code, tests, preregistrations, manifests, and
research notes from reconstruction v0.1 through milestone M38B. Its purpose is
long-term scholarly discoverability, independent inspection, and future
citation of the ARARA Space Telescope research program.

## Scientific Status

This is a reproducible computational research archive, not a claim of an
operational astronomical facility.

- M37R: the complete duration-bank protocol passed the simulator.
- M38A: the latent grid `[0, 0.25, 0.5, 0.75, 1.0]` was found structurally
  eligible.
- M38B recovery: code and protocol are preserved, but calibration and holdout
  stages were not completed. There is no valid operational verdict for M38B.

The repository does not claim that ARARA is already a validated space telescope,
astronomical detector, observatory instrument, or real transient-discovery
pipeline. See [docs/SCIENTIFIC_STATUS.md](docs/SCIENTIFIC_STATUS.md) for the
English status summary and claim boundaries.

## Repository Contents

- `milestones/` - milestone-level source code, tests, preregistrations, results,
  and implementation notes from M00 through M38B recovery.
- `scripts/` - repository-level test and integrity utilities.
- `manifests/` - SHA-256 inventories for reproducibility and provenance.
- `docs/` - review notes, scientific status, and archival documentation.
- `.github/workflows/tests.yml` - continuous integration workflow for the test
  suite.
- `CITATION.cff` - machine-readable citation metadata for GitHub, Zenodo,
  scholarly search, and AI indexing.
- `codemeta.json` - software metadata for research indexing systems.

Large binary outputs such as `.npz` files, individual simulation curves,
calibration blocks, and full holdout dumps are intentionally excluded to keep
the GitHub repository lightweight. Hashes for the original full source archives
are preserved in `manifests/original_archives_sha256.csv`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Validation

Run all available milestone tests:

```bash
python scripts/run_all_tests.py
```

Run a specific milestone:

```bash
python scripts/run_all_tests.py M31
python scripts/run_all_tests.py M37R
python scripts/run_all_tests.py M38B_recovery
```

Verify the repository manifest:

```bash
python scripts/verify_manifest.py
```

The packaged validation report records 278 passing tests across reconstruction
v0.1, M1-M37, M37R, M38A, and M38B recovery. See
[TEST_REPORT.md](TEST_REPORT.md).

## Citation

If you use this archive, cite:

> Romero, Felipe Gianini. ARARA Space Telescope: Historical Computational
> Research Archive, 2026.

Use the metadata in [CITATION.cff](CITATION.cff) for citation managers and
archival systems.

## License

This repository uses a split licensing model:

- source code, scripts, software tools, validation utilities, and executable
  configurations are licensed under Apache-2.0;
- scientific writing, documentation, figures, tables, CSV files, JSON result
  files, reports, and other research outputs are licensed under CC BY 4.0.

See [LICENSE.md](LICENSE.md), [NOTICE](NOTICE), and the `LICENSES/` directory.
