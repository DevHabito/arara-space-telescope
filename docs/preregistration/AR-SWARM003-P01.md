# AR-SWARM003-P01 — Cost of acting on a peer audit

24 November 2026. Registered before implementation and evaluation. This is a one-step intervention benchmark for the two-node audit of AR-SWARM002-P01. The directed link, latent truth, coverage, fault dependence, reporting and provenance-tag noise are exactly those of that registered model. Benchmark all six named scenarios and the same 101-point tag-error grid. Keep the nominal audit rules unchanged.

## Fixed actions and downstream outcome

After A raises a candidate, the network can perform one immediate local repair or defer. For a real sky event, repair incurs cost 1 (unnecessary intervention) and defer incurs 0. For a true local processing fault, repair incurs residual cost 1/10 and defer incurs 1. These dimensionless costs model a deliberately asymmetric decision; they are not estimates of actual restoration or hardware damage. Ground truth for scoring is the generator's hidden label, not the audit verdict. This stage has no repair feedback and does not implement the sectorized graph policy.

Compare defer all, repair all, and three frozen audit policies from AR-SWARM002-P01: literal agreement, bit only, bit and provenance. For the three audit policies, repair only on a fault verdict. The baselines can act without B; all three audit policies defer without B. As an informationally matched decision-theoretic comparator, fit a nominal minimum-cost action table using bit and tag, breaking ties in favor of defer, and freeze it across stress cases. Include a second cost regime with unnecessary repair cost 4, keeping the other costs fixed and refitting only the nominal minimum-cost table for that regime. This gives a prespecified consequence test without selecting a favorite cost ratio after seeing outcomes.

## Reporting and tests

Use exact rational enumeration. For each scenario and cost regime retain expected cost, P(repair | sky), P(defer | fault), and P(repair). Record provenance minus bit-only cost deltas for the sweep and every sign transition. Primary H1: at cost 1, frozen provenance-to-repair has lower nominal cost than frozen bit-only-to-repair. H2: at cost 1 it has higher cost under inverted tags. Preserve an unsupported hypothesis. Compare every policy to both fixed baselines even if either baseline wins. Check probability conservation, no-coverage behavior, nominal optimal-table loss against every binary action table, and deterministic replay.

Lean 4 target: check general decision inequalities for scaled integer costs, and separately check concrete exact witnesses for provenance and intervention against the computed tables. State which parts depend on correspondence with the Python model. The next study can implement repair propagation and sector exchange once this one-step tradeoff is explicit.
