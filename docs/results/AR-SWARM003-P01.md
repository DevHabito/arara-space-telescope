# AR-SWARM003-P01 — When should a peer audit trigger repair?

24 November 2026. Exact two-node benchmark. The [protocol](../preregistration/AR-SWARM003-P01.md) was published at [`f221119`](https://github.com/DevHabito/arara-space-telescope/commit/f22111987e347997ad953a5a2d197b351c5fca6a) before implementation and execution. [Exact output](AR-SWARM003-P01.json) contains all scenarios, both cost regimes and both 101-point sweeps.

## Nominal conditions

| Policy | Expected cost, unnecessary repair costs 1 | Expected cost, unnecessary repair costs 4 | Unnecessary repair among sky cases, cost 1 | Faults deferred, cost 1 |
|---|---:|---:|---:|---:|
| Defer all | 0.500000 | 0.500000 | 0% | 100% |
| Repair all | 0.550000 | 2.050000 | 100% | 0% |
| Literal agreement | 0.368750 | 0.481250 | 7.50% | 62.50% |
| Frozen bit only | 0.368750 | 0.481250 | 7.50% | 62.50% |
| Frozen bit and provenance | 0.380375 | 0.436625 | 3.75% | 69.25% |
| Direct nominal cost minimizer | 0.368750 | 0.436625 | 7.50% | 62.50% |

**H1 unsupported.** At unnecessary-repair cost 1, the provenance-based audit cuts unnecessary repair by 3.75 percentage points. It defers an additional 6.75 points of actual faults and increases expected cost by 0.011625. Quadrupling the unnecessary-repair cost reverses the comparison and reduces nominal expected cost by 0.044625. The direct nominal decision rule matches bit only in the first regime and bit with provenance in the second. The relative cost of acting incorrectly matters for routing an audit verdict to repair.

**H2 supported as an adverse control.** With inverted tags and repair cost 1, the provenance-based rule costs 0.501875, compared with 0.368750 for the bit-only rule and 0.500000 for always deferring. When the report itself is uninformative, always deferring beats every frozen rule at both registered costs. Without coverage, the audit-based rules and direct nominal rule defer all actions; repair-all still acts.

The grid favors the frozen provenance-to-repair rule below 2% tag error at cost 1 and through 43% tag error at cost 4. The opposite result begins at 2% and 44%, respectively, with no ties on either grid. These are exact consequences of the stipulated model and loss weights. They are not empirical mission tolerances.

## Lean 4 and the evidence boundary

The [Lean module](../../formal/AraraFormal/PeerRepair.lean) represents exact joint masses on a common integer scale. Its first theorem states the decision inequality for arbitrary integer inputs on that scale. Its next results characterize the SWARM002 audit crossover and the SWARM003 repair crossovers and verify nominal and inverted-tag witnesses. The Python bridge checks every point on all three registered grids against the scaled expressions. The simulation generator and its correspondence to the Lean expressions are checked on the specified grids by the Python test suite. They are not Lean theorems. GitHub Actions builds the module using the repository's pinned Lean toolchain.

The crossover expressions follow by comparing the cases where bit only repairs and the provenance rule defers. On the 8000-mass scale these cases have sky mass 150 and fault mass 150 + 12k, where k is the integer tag-error percentage. Deferring saves the unnecessary sky action and loses 9/10 of the benefit on faults, so the provenance-minus-bit-only cost has numerator 9(150 + 12k) − 1500w over 80000, with w the unnecessary repair cost.

## Reproduction

```sh
python -m unittest discover -s tests -p 'test_ar_swarm*.py' -v
python -m scripts.ar_swarm003_repair_cost
lake build
```

All 24 relevant Python tests passed locally, including 20 upstream and feasibility checks. The current model applies one intervention with no feedback. A sectorized repair study must explicitly define propagation, action latency and changes in sector exchange before comparing against the published adaptive-repair policy.
