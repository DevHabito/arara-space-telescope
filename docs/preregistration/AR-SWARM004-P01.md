# AR-SWARM004-P01 — Sector spillovers under local repair

24 November 2026. Registered before implementation and enumeration.

## Network and outcome

Use a directed, weighted graph with two fixed sectors, A = {A0,A1}, B = {B0,B1}. Nodes A0 and B0 issue jobs; A1 and B1 provide service. Outgoing weights are A0→A1=3, A0→B1=1, B0→A1=1, B0→B1=3, A1→A0=1 and B1→B0=1. No other edges. All rows are active. Follow Romero, *Adaptive Relational Repair in Weighted Sectorized Networks*, §3.1, equations (4)–(7), for row normalization, mean within-sector autonomy, per-sector exchange and unweighted mean exchange. The service outcome follows one routing step only from each source. The service nodes' outgoing edges close the directed graph for the structural metrics, and carry no further service jobs in this epoch.

Each job is externally scored as correct with probability equal to the availability of its chosen service node. Baseline availability is 1/2 at A1 and 1 at B1. Each repaired condition restores A1 to availability 1. A shared-resource effect reduces B1 availability to 1−g, where g is a prescribed coefficient, not an inferred quantity or a law of resource conservation. No re-estimation or random sampling is used.

## Policies and scenarios

- Defer: keep the baseline graph and availabilities.
- Repair only: restore A1, apply the B1 availability reduction, and keep all weights.
- Repair and reroute: apply the same availability changes, then set the A0 row weights to 7 (A1) and 1 (B1). A0's total offered jobs remain fixed.

Enumerate g=k/100 for k=0 through 100. For each point report each source sector's expected correctness and change from defer, and demand-weighted network correctness and change for A demand shares 1/4, 1/2, 3/4. Retain autonomy and exchange for all policies. Compare policies on matched cases at each g and demand share. Include g=0 (isolated repair control) and g=1 (extreme resource coupling). Run a label-swap metamorphic check, including reversal of demand weights. Check row normalization, probability bounds, mass accounting and deterministic replay.

H1: at least one registered repair-only point with balanced demand improves A and worsens B and the network simultaneously. H2: under balanced demand there exists a point where the rerouted repair improves the network while repair only causes a network loss. H3: exchange alone cannot distinguish two opposite network effects when repair only preserves weights; demonstrate with the same baseline and repaired graph at g=0 and g=1. Report all sign changes and ties on the grid for per-sector and network deltas. No policy is selected on held-out data; these are exact finite cases.

Lean 4 targets: prove exact sign boundaries for balanced-demand changes and supply matched-weight witnesses. Check scaled expressions against direct graph enumeration in Python. This tests a necessary measurement distinction before trying the paper's multi-step internalization/relaxation policies. The paper's selection threshold and repair dynamics are outside the experiment.
