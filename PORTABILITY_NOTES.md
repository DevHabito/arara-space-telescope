# Portability Notes

The milestones are preserved separately so their historical dependency layouts
remain inspectable. Some older scripts assume that the current working
directory is the milestone directory itself.

Large binary result files, individual curves, calibration chunks, and full
holdout dumps are excluded from the GitHub archive. Hashes for the original
complete archives are preserved in `manifests/original_archives_sha256.csv`.
