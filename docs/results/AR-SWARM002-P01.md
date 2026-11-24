# AR-SWARM002-P01 — Exact peer-provenance results

24 November 2026 · Exact finite benchmark · Python 3.12.14

The [protocol](../preregistration/AR-SWARM002-P01.md) was published at [`1003275`](https://github.com/DevHabito/arara-space-telescope/commit/100327544a731e1c6664243b03d0e4135392124d) before implementation or execution. [Full exact results](AR-SWARM002-P01.json) retain nominal action tables, per-label outcomes, decision coverage, conditional error, and all 101 tag-error settings. No protocol or decision thresholds were changed after execution.

## Results

Risk is the expected loss under the registered weights: 1 for a wrong decision and 1/4 for abstention. Percentages in the risk columns are percentages of this loss scale. The false confirmations column is the percentage of actual fault cases called sky after conditioning on an initial candidate from A. All policies use their nominal decision tables in every row.

| Scenario | A alone risk | Literal agreement risk | Bit-only risk | Bit + provenance risk | False confirmations, bit + provenance |
|---|---:|---:|---:|---:|---:|
| Nominal | 25.000% | 28.750% | 23.125% | 20.875% | 6.750% |
| Perfect tag | 25.000% | 28.750% | 23.125% | 19.375% | 3.750% |
| Uninformative tag | 25.000% | 28.750% | 23.125% | 26.875% | 18.750% |
| Inverted tag | 25.000% | 28.750% | 23.125% | 34.375% | 33.750% |
| No coverage | 25.000% | 25.000% | 25.000% | 25.000% | 0% |
| Uninformative report | 25.000% | 43.750% | 34.375% | 34.375% | 18.750% |

**H1 supported in the nominal model.** The provenance rule lowers expected loss by 2.25 percentage points versus bit only and by 4.125 points versus A alone. It makes definitive decisions in 37.5% of cases, versus 22.5% for bit only. The nominal bit-only rule never confirms sky because its posterior error for a positive report exceeds the registered abstention cost. Thus nominal provenance adds both sky confirmations and false sky confirmations. Literal agreement makes definitive decisions in 75% of cases and falsely confirms 37.5% of fault cases.

**H2 supported as an adverse result.** With inverted tags the provenance rule costs 11.25 percentage points more than bit only. With uninformative tags it costs 3.75 points more. The stress grid shows an advantage through 24% tag error, a tie at 25%, and a disadvantage from 26% through 100%. These are grid findings for fixed rules and registered assumptions. They do not estimate a mission requirement or apply to a recalibrated policy.

When the report itself becomes uninformative, both frozen Bayes rules have equal loss and the always-abstain rule performs better. Their action distributions still differ. With no coverage, all rules abstain and the error rate among definitive decisions is undefined.

## Reproduction and failures

Run from the repository root:

```sh
python -m unittest discover -s tests -p 'test_ar_swarm002*.py' -v
python -m scripts.ar_swarm002_peer_provenance
```

Local checks passed for all four protocol integrity tests and all four prior feasibility tests, including the 5,151-point rational grid. The 12 AR-SWARM001-P01 regression tests also passed locally. The complete decision-table test compares the nominal posterior decisions against all 27 bit-only and 243 bit-and-tag tables. Two independent command invocations must reproduce the saved bytes in CI. The adverse controls and the increase in false confirmations relative to bit-only are retained. Lean 4 verification was not run.

## Scope

The truth classes are balanced by construction. Coverage, reporting noise, the provenance tag and their error rates are stipulated. The result depends on the loss assigned to abstention, the reliability of the reported tag and the coverage model. It evaluates a two-node audit link after an initial candidate. The original sectorized repair policy, repair costs, larger network and physical data remain outside this benchmark. A subsequent protocol should vary the cost of abstention, allow a common error in the provenance service itself and test whether better audit decisions reduce harmful interventions before recommending any repair.
