# M24 calibration execution recovery log

A call that attempted two calibration families reached the notebook's 60-second limit while generating the second family in that call.

Because interrupted tool calls cannot be trusted implicitly, the filesystem was inspected afterward. Both previously completed files, `quiet.npz` and `shared_ramp.npz`, were reopened independently and verified to contain exactly 50,000 finite values for `score`, `estimated_onset`, and `endpoint`.

No code, seed, family order, threshold rule, sample size, candidate onset, or criterion changed.

The remaining families are executed one at a time. Verified completed files are not regenerated.
