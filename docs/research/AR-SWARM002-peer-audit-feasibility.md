# ARARA peer audit under shared failures

24 November 2026 · Exploratory mathematical note and reproducibility check

## Starting point

[AR-SWARM001-P01](https://github.com/DevHabito/arara-space-telescope/pull/19) observed 11 true alarms among 901 positive windows in its hidden-corruption cohort. The simulator withheld that corruption from the internal telemetry by construction. The question here is whether a second observer can distinguish a real event from a fault that produced the first observer's candidate.

The P01 source and suite were retrieved at [PR head `47137d0`](https://github.com/DevHabito/arara-space-telescope/tree/47137d068a77a70354c324b6fbfbff87da7cf9af) and rerun locally. All 12 tests passed. The full calibration and holdout objects, including per-scenario results and the bootstrap, matched the recorded workflow JSON exactly. The local Python 3.12.14 and NumPy 2.3.5 versions differ from the recorded Python 3.12.16 and NumPy 2.5.5. The canonical digests therefore differ because the runtime versions are part of the payload.

## Observation contract

Condition on a candidate already raised by observer A. A reports the same positive candidate under both hypotheses. Under S it is a real event visible to both observers. Under F it is a fault originating in A's measurement or processing path. The fault contaminates observer B's ideal report with conditional probability q. B's reported bit is independently flipped with probability e after this step; the same e applies to both hypotheses. We take 0 ≤ q ≤ 1 and 0 ≤ e ≤ 1/2. There are two labels, equal hypothesis weights and equal error costs. Real candidates can involve additional causes, unequal rates, out-of-band or unsynchronized observations, and uncertainty about B's coverage.

| Term | Meaning in this note |
|---|---|
| Positive peer report | B also reports a candidate for the matched observation. |
| Shared-failure probability q | Conditional probability under F that the fault reaches B's ideal report, among candidates already raised by A. It is a model parameter, not an estimated mission rate. |
| Report error e | Symmetric post-propagation bit-flip probability for B. |
| Provenance | The sensor, calibration, software and timing dependencies needed to assess what failures two reports might share. |
| Identifiability in this model | The two hypotheses induce different distributions on available reports. This permits statistical separation in principle and may still leave individual cases ambiguous. |

## Derivation

Under S, B's ideal bit is 1, so P(B=1 | S) = 1−e. Under F, B's ideal bit is 1 with probability q and 0 otherwise; therefore P(B=1 | F) = q(1−e)+(1−q)e. Their difference is (1−q)(1−2e), which is nonnegative on the declared domain. Total variation for two Bernoulli distributions is the absolute difference of their success probabilities. The equal-weight Bayes error is therefore

**E(q,e) = [1−(1−q)(1−2e)]/2 = e + q(1/2−e).**

Equivalently, a rule choosing S when B=1 and F when B=0 has false-sky probability q(1−e)+(1−q)e and missed-sky probability e. Its average error equals the expression above. Choosing a constant label costs 1/2; reversing the decision costs 1−E. These exhaust deterministic binary rules. A randomized decision is an average of deterministic rules and cannot lower the minimum.

| Shared-failure probability q | Minimum equal-weight error for e = 10% |
|---:|---:|
| 0% | 10% |
| 50% | 30% |
| 90% | 46% |
| 100% | 50% |

The probabilities in this table are illustrative inputs. With q=1 and e=0, both observers always report the candidate under both hypotheses. Even perfect agreement gives the same observable pair (1,1) in both cases. With e=1/2, B's report is identically distributed under both hypotheses for any q. Otherwise B supplies information under this specific observation model. This is a result about classification after A raises a candidate. It leaves lead time, detection completeness across all targets, and the efficacy of repair policies open.

## Checks and limits

The Python check below uses exact rational arithmetic. It enumerates both latent propagation states, both report flips and all four deterministic decisions for each of 5,151 grid points in the declared domain. Four tests passed, covering the grid, exact observational equivalence with perfect agreement, the perfect independent peer, and the table. The derivation above covers the continuum. Lean 4 was unavailable in the execution environment; no machine-checked Lean result is claimed.

The testing identity is standard. See [Pradeep Ravikumar, CMU 10-716, Lecture 15, 2019, §15.1](https://www.cs.cmu.edu/~pradeepr/courses/716/2019-spring/notes/lec15.pdf). The spacecraft fault-management precedent is [NASA, Guidance, Navigation, and Control Engineering Best Practices, best practice 5](https://ntrs.nasa.gov/citations/20230005922). This note applies those ideas to a deliberately small ARARA observation model. It supplies no empirical estimate of q or e and makes no originality claim for the underlying statistical identity or the principle of independent fault diagnosis.

## Consequence for the next registration

Before comparing repair policies in the directed, weighted network from [Adaptive Relational Repair in Weighted Sectorized Networks](https://philarchive.org/archive/ROMRSA), give each simulated report explicit provenance and an externally scored outcome. Include the same matched sky event in two processing paths, a local fault confined to one path, and a shared fault that replicates the appearance of that event in both paths. Include a valid missing-coverage case, where B cannot audit A. Keep shared calibration and software dependencies observable as metadata while withholding the injected cause from the audit algorithms.

Measure false sky confirmations, missed sky events and abstentions separately. Compare A alone with agreement-only and provenance-aware decisions on fresh whole episodes. Then test whether any better identification translates to lower repair cost and fewer harmful interventions against no repair, fixed repair and the paper's exchange-based policy. Freeze numerical gates and seeds prospectively; this exploratory note does not register that experiment or reuse the P01 holdout to tune it.

## Reproduction code

Save the following as `verify_arara_peer_audit.py` and run `python3 verify_arara_peer_audit.py`. It uses the standard library.

```python
"""Exhaustive, exact checks for the two-observer audit model."""

from fractions import Fraction
from itertools import product
import unittest


def report_distribution(sky_event, shared_failure, report_error):
    """Enumerate latent failure propagation and binary report error."""
    masses = [Fraction(0), Fraction(0)]
    for copied, flipped in product((False, True), repeat=2):
        copy_mass = shared_failure if copied else 1 - shared_failure
        flip_mass = report_error if flipped else 1 - report_error
        ideal_report = sky_event or copied
        masses[int(ideal_report ^ flipped)] += copy_mass * flip_mass
    return masses


def minimum_error(sky, fault):
    """Evaluate all four deterministic policies with equal class weights."""
    return min(
        sum((fault if pick_sky else sky)[report]
            for report, pick_sky in enumerate(policy)) / 2
        for policy in product((False, True), repeat=2)
    )


class PeerAuditChecks(unittest.TestCase):
    def test_all_rational_grid_cases(self):
        for error_index, common_index in product(range(51), range(101)):
            error = Fraction(error_index, 100)
            common = Fraction(common_index, 100)
            sky = report_distribution(True, common, error)
            fault = report_distribution(False, common, error)
            self.assertEqual(sum(sky), 1)
            self.assertEqual(sum(fault), 1)
            self.assertTrue(all(0 <= mass <= 1 for mass in sky + fault))
            self.assertEqual(
                minimum_error(sky, fault),
                (1 - (1 - common) * (1 - 2 * error)) / 2,
                (error, common),
            )
            self.assertEqual(sky == fault, common == 1 or error == Fraction(1, 2))

    def test_perfect_peer_without_shared_fault(self):
        sky = report_distribution(True, Fraction(0), Fraction(0))
        fault = report_distribution(False, Fraction(0), Fraction(0))
        self.assertEqual(minimum_error(sky, fault), 0)

    def test_complete_agreement_can_be_uninformative(self):
        sky = report_distribution(True, Fraction(1), Fraction(0))
        fault = report_distribution(False, Fraction(1), Fraction(0))
        self.assertEqual(sky, [0, 1])
        self.assertEqual(sky, fault)
        self.assertEqual(minimum_error(sky, fault), Fraction(1, 2))

    def test_architecture_examples(self):
        error = Fraction(1, 10)
        for common, expected in (
            (Fraction(0), Fraction(1, 10)),
            (Fraction(1, 2), Fraction(3, 10)),
            (Fraction(9, 10), Fraction(23, 50)),
            (Fraction(1), Fraction(1, 2)),
        ):
            sky = report_distribution(True, common, error)
            fault = report_distribution(False, common, error)
            self.assertEqual(minimum_error(sky, fault), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
```
