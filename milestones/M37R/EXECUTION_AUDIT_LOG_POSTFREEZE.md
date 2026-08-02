# ARARA-M37R — Execution audit after preregistration

The scientific code, seeds, block sizes and frozen batch size were not changed.

The first orchestration process was paused after completing part of block 1. The remaining independent family×block streams were executed with four workers. Parallelism occurred only across streams with distinct preregistered seeds. Within every stream, chunks were sequential, each chunk restored the prior NumPy RNG state, and the frozen evaluator continued to use batches of exactly 50.

All 100 chunks, 20 blocks and five pooled family files were verified for exact record counts and finite scores. No block was removed or regenerated according to its values.
