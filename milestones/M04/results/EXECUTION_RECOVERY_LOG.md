# M4 execution recovery log

The first all-at-once holdout process was interrupted by the notebook environment's 60-second execution limit before any result was returned.

No code, seed, template, threshold, metric, or criterion was changed.

The already-opened holdout was resumed deterministically by regenerating each of the 20 frozen child-seed batches separately. Each batch was saved before aggregate analysis. The holdout opening count remains one.
