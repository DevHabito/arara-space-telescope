# AR-SWARM001-P01 — Prospective operational-stability forecasting under controlled failures

**Registration date:** 23 November 2026 (America/Sao_Paulo).  
**Status:** Protocol only. The generator, tests and outcomes must be committed **after** this registration.  
**Stage:** First of three proposed research stages: (1) per-observer operational stability; (2) sectorized swarm repair; (3) integrated community auditing. Only stage 1 is under test here.

## Primary sources and exact claim boundary

- Felipe Gianini Romero (February 2026), *The Romero Law of Relational Stability (RZS): A Closed-Form Statement, Cross-Domain Operationalization, and Computational Verification*, https://philarchive.org/archive/ROMTRL. Equations (1)–(3) specify `sigma=k*B/(I*tau)`, its relative form at `k=1`, and a bounded transform. Section 2.1 defines sustainable update throughput, informational noise and event-to-effective-update latency; Section 3.1 requires frozen proxy definitions and independent outcome checks. The article's algebraic consistency test is **not** empirical fault prediction.
- Felipe Gianini Romero (May 2026), *Adaptive Relational Repair in Weighted Sectorized Networks*, https://philarchive.org/archive/ROMRSA. Equations (4)–(6) define the directed transition matrix, sector autonomy and exchange; Eq. (29) is a **post-damage repair-policy decision**. Neither this first-stage experiment nor the original article validates a telescope swarm, and **sector exchange is not identical to observational agreement**.

Existing aerospace work includes NASA's spacecraft diagnostics/prognostics and conventional fault detection, isolation and recovery (FDIR). Any result here is a bounded demonstration, not a new law or production-spacecraft superiority. References: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/diagnostics-and-prognostics-group/ and https://science.nasa.gov/science-research/science-enabling-technology/technology-highlights/integrating-model-based-systems-engineering-and-fault-management-to-enable-autonomous-space-missions/.

## Research question

Does the article's **unfitted relative index** `sigma_rel = B/(I*tau)` provide **better advance warning** of degraded external service quality than already available single-variable and simple normalized-combination baselines, when all proxy values are observed **before** the outcome? Does the index acknowledge its blind spot when output corruption is invisible to internal telemetry?

This is a **synthetic, discrete-window processing/service simulator**, not NASA or ARARA hardware telemetry, and not the original paper's log-space perturbation generator. Inference is explicitly restricted to this simulation.

## Frozen source generator

Use Python 3.12, NumPy 2.x, no external network or time-of-day inputs. Each independently reset episode has **48 one-second windows**. Five scenarios:

1. `NOMINAL`: normal capacity, with occasional demand bursts.
2. `CAPACITY`: service-rate suppression during one contiguous shock.
3. `VISIBLE_CORRUPTION`: detected output corruption during one shock.
4. `LATENCY`: delayed effective updates during one shock.
5. `HIDDEN_CORRUPTION`: output corruption during one shock that the *internal sensor does not record*.

For each of the first four scenarios, use 50 independent episodes: **indices 0–29 train**, **30–49 held out**. For `HIDDEN_CORRUPTION`, use **50 held-out episodes only**, never used to select any comparator, threshold or feature normalization. The episode seed for scenario index `s=0..4` and episode index `j=0..49` is `20261123 + 1000*s + j`. Never share a random generator between episodes.

For non-nominal scenarios, draw shock onset uniformly from integers `[12,18]` inclusive, length uniformly `[14,20]` inclusive, and severity uniformly `[0.65,0.85]`. The shock is a fixed contiguous window; there is no change to these distributions after results. No shock in nominal episodes.

Each one-second window generates demand `Poisson(48)` plus a burst of 20 requests with probability 0.08, and offered capacity `Poisson(56 * factor)`, with `factor=1-0.70*severity` only for `CAPACITY` during its shock and 1 otherwise. A FIFO-backlog *count* (no per-job age records) is carried across windows and capped at 300; processed count is `min(backlog_before + demand, offered_capacity)`. Record the number dropped beyond the backlog cap. A binomial-like per-completed-job independent random draw assigns **visible corruption** probability `0.015 + 0.55*severity` during a visible-corruption shock and 0.015 otherwise; **hidden corruption** probability `0.01 + 0.55*severity` during a hidden-corruption shock and 0.01 otherwise. A completed job is externally correct iff it has neither defect. An internally detected defect affects reported `B` and `I`; a hidden defect does neither.

Every completed job has simulated event-to-effective-output delay `0.025 + 0.45*(backlog_before / max(offered_capacity,1)) + Exponential(scale=0.055)` seconds, plus `1.35*severity` seconds during a latency shock. The **externally measured service-adequacy fraction** in the window is `min(1, correct_and_delay_at_most_0.65_seconds / max(demand,1))`. It is a *synthetic output-adequacy metric*, **not** a per-request deadline guarantee because detailed FIFO ages are not modeled. The external observer sees hidden defects and all delays; internal telemetry does not see hidden defects.

## Frozen internal proxy dictionary and time direction

At time `t`, measure the current and three immediately preceding complete windows, `t-3..t`. Define:

- `B(t)`: **mean internally accepted processed output jobs/second** in that four-window block. A deliberately short, operational *sustainable-throughput proxy*, not the true long-run throughput.
- `I(t)`: `0.01 + (total detected corrupt jobs / max(1,total processed jobs))` over the same block. The **0.01 fixed additive measurement floor** prevents singular denominators and must not be tuned; this is an operational noise proxy, not Shannon entropy and not undetected true error rate.
- `tau(t)`: arithmetic mean of the **per-window p95 measured job delays** for the same four windows, in seconds. If a window processed zero jobs, its p95 proxy is `0.025 + 0.45*(backlog_before/max(offered_capacity,1))`; this is a documented fallback, not a fitted estimator.
- `sigma_rel(t) = B(t)/(I(t)*tau(t))`, `k=1`, with higher `sigma_rel` treated as healthier. It is not interpreted as a probability. Neither the multiplicative formula nor a calibrated constant is altered.

Forecast target is defined **only after t**: `Y(t)=1` (degradation) when the **mean external adequacy during t+1..t+3 is <0.80**. For each 48-window episode, use exactly `t=3..44` inclusive (**42 forecasts**), with all label windows strictly in the future. The external observer's ground truth is generated by the declared simulation, not by applying a sigma threshold to the same inputs.

Report positive/negative counts, by split and scenario, before any performance interpretation.

## Frozen comparators, selection and metrics

Define risk direction (higher means more likely failure):

- `RZS = -sigma_rel` (no fitted transformation).
- `B_ONLY = -B`.
- `I_ONLY = I`.
- `TAU_ONLY = tau`.
- `LINEAR = -z(B)+z(I)+z(tau)`, using the **training-only** means and population standard deviations of each proxy.
- `MAX = max(-z(B), z(I), z(tau))`, with the same training-only normalization.

If a training feature has zero standard deviation, its standardized column is zero. No logistic-model tuning or supervised weight fitting is permitted.

On the **train episodes from observable scenarios only**, compute the tie-aware empirical ROC-AUC and choose one **champion baseline** among `B_ONLY, I_ONLY, TAU_ONLY, LINEAR, MAX` according to the highest **training ROC-AUC** (fixed tie order is that listed order). No test outcome may affect this choice. Independently set **one alert threshold per risk score** to the 90th percentile of its **negative training** scores, using NumPy's default linear quantile; alarm is `score > threshold`.

On the held-out observable episodes and separately the hidden-corruption episodes, report for every method: ROC-AUC (if both classes exist), confusion counts (TP, FP, TN, FN), sensitivity, false-positive rate, precision, and alarm coverage. Report per-scenario counts/ROC-AUC; pooled windows are **correlated within episodes** and **not independent samples**.

Report an optional 95% percentile *episode-block bootstrap* CI of `AUC_RZS − AUC_champion` on the observable test episodes: **400** resamples, RNG seed `20261201`, sampling 80 episodes with replacement, skipping resamples without both classes and reporting the retained count. This interval is only descriptive for the declared simulator, not a population-wide significance statement.

## Frozen falsifiable decisions

- **H1 — Added ranking information:** on pooled observable held-out episodes, `AUC_RZS>=0.70` **and** `AUC_RZS−AUC_champion>=0.02`; otherwise `NOT_SUPPORTED_IN_SIMULATION`.
- **H2 — Useful advance warnings:** on observable holdout, the training-calibrated RZS alarm must achieve sensitivity `>=0.60` and false-positive rate `<=0.20`; otherwise `NOT_SUPPORTED_IN_SIMULATION`.
- **H3 — Hidden-error limitation:** on hidden-corruption-only holdout, RZS alarm sensitivity `<=0.30`; if this holds label `BLIND_SPOT_EXPOSED_IN_SIMULATION`, otherwise `BLIND_SPOT_NOT_ESTABLISHED`. This H3 verdict **is not a positive performance claim**. It verifies whether internally invisible errors lead to substantial missed detections under the frozen alarm.
- If class variation is absent or integrity fails, use `NOT_EVALUABLE` or `INCONCLUSIVE_IMPLEMENTATION`, not an invented success.

**Integrity gates G1–G5**, distinct from scientific outcomes:
- **G1** exact seeds and splits by episode, no repeated seeds;
- **G2** finite nonnegative telemetry, strictly positive `I/tau`, future-only oracle time;
- **G3** frozen formula, training-only z-scores, baseline selection and alarm quantiles;
- **G4** per-scenario and total confusion/count conservation, no hidden test fitting;
- **G5** canonical SHA-256 of a compact JSON payload including runtime, proxy definitions, scientific verdicts, counts and aggregate metrics; save no raw per-window streams in the repository.

Every failure, rejected hypothesis and blind spot must remain visible; no cherry-picked reruns or change of proxy, scenario, shock or success thresholds after executing the actual experiment.

## Limitations and next study

The external outcome is only externally *visible within the simulator*. It is not actual optical data or independent hardware instrumentation. The fault mechanisms and time persistence were chosen before running to probe the index, not discovered from nature. An algebraically expected monotonic fall in `B/(I*tau)` during a fault is **not proof of early-warning accuracy**, which requires the separate future-outcome comparison.

The original papers are not modified. The second stage, to be separately preregistered, will construct a directed weighted telescope **network** and apply *the original article's* sector definitions `P_ij, A_m, E_m` and policies without conflating `B` (throughput here) with `B_x(p)` (a within-case repair score in the second paper). No claim of telescope swarms, autonomous correction, scientific originality or real astrophysical event recognition follows from P01.
