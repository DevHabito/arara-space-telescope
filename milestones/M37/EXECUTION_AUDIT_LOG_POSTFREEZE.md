# ARARA-M37 — Execution audit after preregistration

The scientific code, seeds and frozen batch size of 50 were not changed. The execution environment terminated long single-process jobs before completion. Calibration was therefore checkpointed into sequential chunks while preserving one continuous NumPy RNG state per family and calling the frozen evaluator in batches of exactly 50.

Verification: the first 1,000 records of the checkpointed `quiet` calibration were compared bit-for-bit against a direct run of the frozen generator for all stored arrays; every array matched exactly. Each family contains exactly 50,000 records. This is an execution-orchestration change only, not a protocol or data-generation change.
