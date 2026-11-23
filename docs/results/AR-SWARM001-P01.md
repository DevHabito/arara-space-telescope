# AR-SWARM001-P01 — Operational self-audit and hidden-failure stress test

**Completed:** 23 November 2026 (America/Sao_Paulo).  
**Evidence type:** Reproducible, deterministic **synthetic observer-processing simulator**. **No actual TESS, ARARA hardware, telescope fleet, optical sensor or independent astronomical event was observed in this phase.**  
**Authoritative preregistration:** [AR-SWARM001-P01](../preregistration/AR-SWARM001-P01.md), committed *before* implementation as `6d7be731d0c68941d723a28c41b9d661ff60f405`.  
**Code:** [ar_swarm001_operational_stability.py](../../scripts/ar_swarm001_operational_stability.py).  
**Tests:** [test_ar_swarm001_operational_stability.py](../../tests/test_ar_swarm001_operational_stability.py), 12 passing unit tests in the hosted Python 3.12 run.  
**Hosted execution:** [GitHub Actions run #45152307189](https://github.com/DevHabito/arara-space-telescope/actions/runs/45152307189) — **SUCCESS**, 12 tests passed and five internal integrity gates passed.  
**Original complete JSON artifact:** [#14805574950](https://github.com/DevHabito/arara-space-telescope/actions/runs/45152307189/artifacts/14805574950), subject to GitHub's artifact retention policy.  
**Permanent compact aggregate:** [AR-SWARM001-P01-aggregate.json](AR-SWARM001-P01-aggregate.json).

The original hosted JSON's canonical payload SHA-256, **independently recomputed from the downloaded workflow artifact**, is `0d589fac6c4db752e76eddfc52881256af35c06c22d5423e26263b81fe3c1bc6`. The aggregate JSON is a *human-readable subset of the original record* and **does not have the same digest**. The executable source, fixed seeds and full preregistration can regenerate the complete JSON.

## Why this experiment was needed

Romero's February 2026 paper, [*The Romero Law of Relational Stability*](https://philarchive.org/archive/ROMTRL), gives the relative stability index

`sigma_rel(t) = B(t)/(I(t)*tau(t))`

with `k=1` for comparative use. It specifies that capacity, informational noise and latency require domain-specific, preselected operational measurements, and that stability should be confronted with an external outcome. Its earlier algebraic simulation cannot itself show that sigma forecasts real faults.

Romero's May 2026 paper, [*Adaptive Relational Repair in Weighted Sectorized Networks*](https://philarchive.org/archive/ROMRSA), tests choosing among repair policies in a weighted sectorized graph, based on damaged boundary exchange. The present P01 **does not** implement that network, graph, sector exchange or repair policy. It tests a prerequisite: could each observer provide a useful *self-audit*, and what happens when its sensors cannot see the true fault?

Similar spacecraft fault detection and prognostics already exist at NASA and elsewhere. Neither the present index nor the concept of internal monitoring can be described as a new instrument-health architecture based on this first simulation.

## Frozen simulator and internal-to-external separation

Every episode has 48 simulated one-second processing windows and produces 42 strictly *future*-directed forecasts. At each time `t`, internal proxies use **only** `t−3..t`; the external fault label is computed from downstream adequacy at **`t+1..t+3`**.

- **B:** mean rate of internally accepted processing jobs, across the current four-window block.
- **I:** 0.01 plus the fraction of *internally detected* corrupted jobs in that block; hidden corruption is excluded by the internal sensor model.
- **tau:** average modeled p95 effective-output delay from completed jobs across the same four windows. This **is not** the CCD timing offset measured in earlier TESS studies.
- **External target:** mean future proportion of on-time and actually correct simulated outputs relative to offered demand below **0.80**. The simulator carries only a FIFO-backlog count, so this is a *throughput-adequacy proxy*, **not** a per-request SLA guarantee.

Five seeded regimes were frozen: NOMINAL, CAPACITY, VISIBLE_CORRUPTION, LATENCY and HIDDEN_CORRUPTION. The latter deliberately introduces future incorrect outputs invisible to internal B, I and tau. It is therefore an **identifiability/observability stress test**, not a surprising newly discovered detector failure.

The study used **120 whole training episodes**, **80 entirely different held-out observable episodes**, and **50 held-out hidden-corruption episodes** never used for calibration. Each episode's random generator has a frozen seed; no individual forecast windows were randomly mixed between training and holdout.

Comparators were throughput alone, detected-error fraction alone, latency alone, a fixed training-normalized linear sum, and a maximum of the normalized risk components. The **MAX** baseline was chosen based **only** on its training AUC. All method alert thresholds were fixed from the 90th percentile of *negative training* risk scores, before held-out evaluation.

## H1 — Is the ratio superior to a strong comparator?

| Pooled observable held-out result | Romero relative index | Train-selected MAX baseline |
|---|---:|---:|
| Episodes | 80 | 80 |
| Future-fault forecast examples | 3,360 | 3,360 |
| ROC-AUC | **0.895014** | **0.892678** |
| True positives | 1,180 | 1,123 |
| False negatives | 218 | 275 |
| False positives | 205 | 199 |
| True negatives | 1,757 | 1,763 |
| Sensitivity | 84.406% | 80.329% |
| False-positive rate | 10.449% | 10.143% |

The index improved held-out **AUC by only 0.002336**, far short of the preregistered **0.02** incremental-advantage requirement. Its descriptive 95% episode-resampled AUC-difference interval (400 fixed-seed samples, resampling entire episodes) was **[−0.009113, +0.013984]**. This interval is not an astronomy-population confidence statement, nor is it a license to infer a p-value from correlated forecast windows.

**H1: NOT_SUPPORTED_IN_SIMULATION.** The ratio did *not* demonstrate the minimum advantage over a simple rival.

## H2 — Can the self-audit warn before an observable fault?

The frozen RZS alarm detected **1,180 of 1,398** future degradations in the observable test pool, at a **10.45%** false-positive rate among 1,962 negative forecasts. This passed the predeclared sensitivity (>=60%) and FPR (<=20%) limits.

**H2: SUPPORTED_IN_SIMULATION.** This is a forecast about the next three *simulated* windows under the chosen generator, not a real on-board early-warning result.

Performance was heterogeneous, and this matters:

| Regime | Future faults / no faults | AUC (RZS) | RZS sensitivity | RZS FPR |
|---|---:|---:|---:|---:|
| NOMINAL | 11 / 829 | 0.739 | 9.1% | 2.2% |
| CAPACITY | 639 / 201 | 0.951 | 87.2% | 1.5% |
| VISIBLE_CORRUPTION | 371 / 469 | 0.869 | 87.1% | **23.7%** |
| LATENCY | 377 / 463 | 0.849 | 79.3% | 15.8% |

In particular, the **visible-corruption subset exceeds the pooled false-alarm target**. One should not claim uniform performance across operating regimes. The very low nominal-fault base rate makes that subset's sensitivity especially unstable.

## H3 — Does the internal observer miss failures it cannot measure?

There were **901 positive** hidden-corruption future windows and **1,199 negative** windows in the 50 completely unseen episodes.

The RZS alarm detected **11 of 901** positive cases (sensitivity **1.22%**), missed **890** positives, and produced **33** false alarms among the negative observations. Its AUC was **0.4891** — essentially chance for this particular concealed-fault construction.

**H3: BLIND_SPOT_EXPOSED_IN_SIMULATION.** This is deliberately a *failure of internal self-awareness*, not an indicator of a successfully working universal self-audit. It is exactly the kind of failure the later community architecture must confront without treating simple consensus as ground truth.

Because the hidden-corruption state is designed not to enter any internal proxy, one cannot honestly conclude that a different algebraic combination of these **same observables** would necessarily recover it. The follow-up needs **additional provenance with different failure dependence**, not just a new formula on the same inputs.

## Audit and interpretation

All five G1–G5 software-integrity gates and 12 network-free tests passed in a separate hosted Python 3.12 environment. H1 was nonetheless **scientifically negative**. Pass/fail software checks are not evidence of predictive superiority.

The experiment distinguishes:
- **Arithmetic correctness:** the proposed ratio is calculated exactly from frozen operational proxies.
- **Simulated advance warning:** present for measured disturbances under the declared generator, but without the stipulated incremental AUC margin.
- **Physical/epistemic observability:** absent for deliberately hidden downstream corruption.

The generator has controlled persistence and shared mechanisms linking throughput, latency and output adequacy. Its results cannot validate any natural physical law; the external label is external only **to the simulated internal telemetry**, not to the simulation's assumptions. Windows within an episode are correlated, and both the binary target and the chosen comparators are domain-specific.

**No observational astronomy, telescope hardware, external peer review, spacecraft deployment or published-article validation has occurred in this first stage.**

## Consequences for the two papers and the next stage

For the first paper, P01 is a **new, refutable operationalization and negative/positive simulation record**. It confirms neither uniqueness nor cross-domain validity; H1 in particular warns against citing the ratio as a demonstrably superior forecasting instrument.

For the repair paper, P01 creates a well-defined reason to test network intervention: when an individual sensor has a blind spot, **independently failing or differently positioned observers** may provide an observable discrepancy. However, if all observers use the same faulty calibration or share the same hidden error, more nodes or higher agreement will not solve identifiability.

The second stage should have its own *new* prospective registration. It must explicitly instantiate the May article's **directed, weighted** graph, supplied sector labels, row-normalized transition matrix, sector autonomy `A_m`, exchange `E_m=1−A_m`, and its two repair sequences. The original learned threshold **0.683746** must not be reused as a physical parameter without new training or a truly blind transfer test. Compare `no repair`, fixed repair, article's exchange-only policy and a proposed external-audit-informed policy, with **independent output truth** and a shared-failure counterexample.

No changes were made to the two PhilArchive articles or to the main branch.
