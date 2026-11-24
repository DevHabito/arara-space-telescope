"""Integrity gates for the preregistered AR-SWARM002-P01 benchmark."""

from fractions import Fraction as F
from itertools import product
import unittest

from scripts.ar_swarm002_peer_provenance import (
    ACTIONS, LABELS, SCENARIOS, benchmark, joint_mass, nominal_table, score,
)


class ProvenanceBenchmarkTests(unittest.TestCase):
    def test_conservation(self):
        for name, parameters in SCENARIOS.items():
            with self.subTest(scenario=name):
                rows = tuple(joint_mass(*parameters))
                self.assertTrue(all(0 <= mass <= 1 for _, _, _, mass in rows))
                for label in LABELS:
                    self.assertEqual(
                        sum(mass for truth, _, _, mass in rows if truth == label), F(1, 2),
                    )

    def test_nominal_decisions_against_all_tables(self):
        rows = tuple(joint_mass(*SCENARIOS["nominal"]))
        for use_tag in (False, True):
            def observation(bit, tag):
                return bit, tag if use_tag else None

            fitted = nominal_table(use_tag)
            keys = tuple(fitted)
            actual = score(lambda bit, tag: fitted[observation(bit, tag)], rows)["risk"]
            all_risks = []
            for actions in product(ACTIONS, repeat=len(keys)):
                candidate = dict(zip(keys, actions))
                all_risks.append(
                    score(lambda bit, tag: candidate[observation(bit, tag)], rows)["risk"]
                )
            self.assertEqual(actual, min(all_risks))

    def test_no_coverage(self):
        results = benchmark()["scenarios"]["no_coverage"]
        for policy in results.values():
            self.assertEqual(policy, results["a_alone"])
            self.assertEqual(policy["risk"], F(1, 4))
            self.assertEqual(policy["coverage"], 0)
            self.assertIsNone(policy["error_given_decision"])

    def test_determinism_and_sweep_completeness(self):
        first = benchmark()
        self.assertEqual(first, benchmark())
        self.assertEqual(
            [point["tag_error"] for point in first["tag_stress_sweep"]],
            [F(k, 100) for k in range(101)],
        )
        for scenario in first["scenarios"].values():
            for policy in scenario.values():
                for masses in policy["action_given_label"].values():
                    self.assertEqual(sum(masses.values()), 1)


if __name__ == "__main__":
    unittest.main()
