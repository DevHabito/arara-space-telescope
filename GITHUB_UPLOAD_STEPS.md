# GitHub Publication Notes

Target public repository:

```text
https://github.com/DevHabito/arara-space-telescope
```

Recommended repository display name:

```text
ARARA Space Telescope
```

Recommended short description:

```text
Historical computational research archive for the ARARA Space Telescope program, including reproducible milestone code, tests, preregistrations, and SHA-256 provenance.
```

Recommended topics:

```text
arara, space-telescope, astronomy, astronomical-transients, signal-processing, computational-research, reproducibility, open-science, python, research-archive
```

The GitHub repository intentionally excludes large binary outputs such as full
calibration blocks, holdout dumps, `.npz` result arrays, and individual curves.
Use GitHub Releases, Zenodo, or another archival storage layer for those binary
artifacts, preserving the SHA-256 hashes listed in
`manifests/original_archives_sha256.csv`.

After publication, cite the repository using `CITATION.cff` and, when possible,
a specific commit hash or archived release DOI.
