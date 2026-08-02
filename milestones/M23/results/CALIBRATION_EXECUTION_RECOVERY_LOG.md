# M23 calibration execution recovery log

The first calibration call reached the notebook's 60-second execution limit while generating the second negative family.

No code, seed, threshold rule, sample size, offset, family, or criterion changed.

The completed `quiet.npz` file was explicitly reopened and verified to contain 50,000 finite scores for each frozen offset.

The remaining families will be generated deterministically in blocks. After each block, the exact NumPy bit-generator state and accumulated score arrays will be saved. Resumption uses that saved state, preserving the same random stream that a single uninterrupted execution would use.
