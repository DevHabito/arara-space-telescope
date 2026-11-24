# AR-SWARM004-P01 — Local repair and sector spillovers

24 November 2026 · Exact one-step service model · Python 3.12.14

The [protocol](../preregistration/AR-SWARM004-P01.md) was published at [`777b590`](https://github.com/DevHabito/arara-space-telescope/commit/777b59097cc8bcf67e67e8e631594f602de4f556) before implementation and enumeration. The [exact archive](AR-SWARM004-P01.json) stores all 303 policy-by-spillover rows and all registered demand shares. Its column names specify the order of the fractions.

Structural measures follow Felipe Gianini Romero, *Adaptive Relational Repair in Weighted Sectorized Networks* (May 2026), §3.1, Eqs. (4)–(7). The independent service endpoint is the expected fraction of source jobs completed correctly after one routing step. The model stipulates the reduction g in B1 service availability after the repair of A1. The symbol g does not refer to a graph weight, exchange probability or observed hardware quantity.

## Main outcomes

Baseline correctness is 62.5% for A and 87.5% for B, so equal demand gives 75% network correctness.

| Scenario | Change for A | Change for B | Network change, equal demand | Mean exchange |
|---|---:|---:|---:|---:|
| Repair only, g=0 | +37.50 pp | +12.50 pp | +25.00 pp | 1/8 |
| Repair only, g=55% | +23.75 pp | −28.75 pp | −2.50 pp | 1/8 |
| Repair and reroute, g=55% | +30.625 pp | −28.75 pp | +0.9375 pp | 3/32 |
| Repair only, g=100% | +12.50 pp | −62.50 pp | −25.00 pp | 1/8 |

H1 is supported in the model for every registered g from 51% through 100%. Improving A is compatible with harming B and the network. H2 is supported from 51% through 57%. Rerouting A's traffic can recover the balanced aggregate in that interval, while B receives no extra benefit from rerouting. H3 is supported by the isolated and extreme controls: the same transition matrix and mean exchange produce balanced changes of +25 and −25 percentage points. This establishes insufficiency of exchange alone for this new service endpoint under the stated model. It leaves the paper's role for exchange in selecting repair protocols under its own outcome definitions open.

## All sign changes on the registered grid

Entries are percent values of g. Empty ranges are marked “none.” Defer is a tie everywhere.

| Policy | Outcome | Positive | Tie | Negative |
|---|---|---:|---:|---:|
| Both repair policies | Sector A | 0–100 | none | none |
| Both repair policies | Sector B | 0–16 | none | 17–100 |
| Repair only | Network, A share 1/4 | 0–29 | 30 | 31–100 |
| Repair only | Network, A share 1/2 | 0–49 | 50 | 51–100 |
| Repair only | Network, A share 3/4 | 0–83 | none | 84–100 |
| Repair and reroute | Network, A share 1/4 | 0–31 | none | 32–100 |
| Repair and reroute | Network, A share 1/2 | 0–57 | none | 58–100 |
| Repair and reroute | Network, A share 3/4 | 0–100 | none | none |

At high A demand the weighted network metric can remain positive even when B loses up to 62.5 points. Both sector outcomes should be retained when comparing policies.

## Proof and reproducibility

Write k=100g on the registered grid. In units of 1/1600, simple repair changes A by 600−4k and B by 200−12k. With balanced demand the network change is 400−8k. Rerouting raises the A-only change by k/800 without moving B, giving a balanced change of (400−7k)/1600. The Lean module checks the balanced accounting identity, sign conditions, rescue interval and fixed-exchange counterexample. The Python suite compares these expressions to direct weighted graph enumeration for all 101 settings. It checks sector relabeling with reversed demand shares, row mass, probability bounds and exact output replay. All four new tests and 24 upstream tests passed locally.

```sh
python -m unittest discover -s tests -p 'test_ar_swarm*.py' -v
python -m scripts.ar_swarm004_sector_spillovers
lake build
```

The study keeps a single repair epoch, one shared-resource effect and routes with fixed offered demand. It does not implement the paper's multistep internalization or relaxation dynamics. Quantifying a real shared resource and following harm over multiple epochs remain separate experiments.
