# Test Report

**Date:** 2026-08-01  
**Result:** 278 tests passed; zero failures in the available packaged suites.

The tests were executed in separate milestone processes, with each milestone
directory and its local `dependency/` directory placed on `PYTHONPATH`. This
avoids collisions between historical modules that reuse similar names.

| Milestone | Tests | Result |
|---|---:|---|
| `M00_reconstruction_v0_1` | 9 | PASS |
| `M01` | 11 | PASS |
| `M02` | 13 | PASS |
| `M03` | 8 | PASS |
| `M04` | 10 | PASS |
| `M05` | 8 | PASS |
| `M06` | 6 | PASS |
| `M07` | 6 | PASS |
| `M08` | 6 | PASS |
| `M09` | 8 | PASS |
| `M10` | 7 | PASS |
| `M11` | 4 | PASS |
| `M12` | 5 | PASS |
| `M13` | 4 | PASS |
| `M14` | 4 | PASS |
| `M15` | 5 | PASS |
| `M16` | 5 | PASS |
| `M17` | 5 | PASS |
| `M18` | 6 | PASS |
| `M19` | 6 | PASS |
| `M20` | 6 | PASS |
| `M21` | 6 | PASS |
| `M22` | 5 | PASS |
| `M23` | 6 | PASS |
| `M24` | 6 | PASS |
| `M25` | 7 | PASS |
| `M26` | 6 | PASS |
| `M27` | 7 | PASS |
| `M28` | 6 | PASS |
| `M29` | 8 | PASS |
| `M30` | 9 | PASS |
| `M31` | 5 | PASS |
| `M32` | 6 | PASS |
| `M33` | 7 | PASS |
| `M34` | 8 | PASS |
| `M35` | 5 | PASS |
| `M36` | 8 | PASS |
| `M37` | 8 | PASS |
| `M37R` | 7 | PASS |
| `M38A` | 7 | PASS |
| `M38B_recovery` | 9 | PASS |

## Commands

```bash
python scripts/run_all_tests.py
```

Because the packaging environment limited single-command duration, validation
was also run in milestone groups. Every suite listed above exited successfully.

## M38B Recovery Note

The recovered M38B archive did not contain its original test directory. The nine
M38B recovery tests were reconstructed from the implementation record and are
identified as recovered tests, not as files present in the original M38B
package. They check:

- frozen latent grid;
- hypothesis counts of 14,652 and 73,260;
- latent-parameter tie rule;
- control identity with M37R;
- control inclusion when `u_true` is on the grid;
- seed uniqueness;
- block concatenation;
- invalid-control veto;
- detection label with non-identifiable latent parameter.

These tests passed, but M38B remains a recovery-stage package without completed
calibration and holdout validation.
