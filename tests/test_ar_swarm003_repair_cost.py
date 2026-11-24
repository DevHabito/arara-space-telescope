"""Check the registered repair benchmark and its Lean scaling bridge."""

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import unittest

from scripts.ar_swarm002_peer_provenance import SCENARIOS, benchmark as audit, joint_mass
from scripts.ar_swarm003_repair_cost import benchmark, nominal_repair_table, score


class RepairCostTests(unittest.TestCase):
    def test_direct_rule_against_every_nominal_action_table(self):
        rows = tuple(joint_mass(*SCENARIOS["nominal"]))
        for sky_cost in (1, 4):
            direct = nominal_repair_table(F(sky_cost))
            best = score(lambda bit, tag: direct[bit, tag], rows, sky_cost)["cost"]
            for actions in product((False, True), repeat=len(direct)):
                table = dict(zip(direct, actions))
                self.assertLessEqual(
                    best, score(lambda bit, tag: table[bit, tag], rows, sky_cost)["cost"],
                )

    def test_no_coverage_and_probability_bounds(self):
        for regime in benchmark()["unnecessary_repair_costs"].values():
            absent = regime["scenarios"]["no_coverage"]
            for policy, result in absent.items():
                if policy != "repair_all":
                    self.assertEqual(result, absent["defer_all"])
            for policies in regime["scenarios"].values():
                for result in policies.values():
                    on_sky, on_fault = result["repair_given_sky"], 1 - result["defer_given_fault"]
                    self.assertTrue(0 <= on_sky <= 1 and 0 <= on_fault <= 1)
                    self.assertEqual(result["repair"], (on_sky + on_fault) / 2)

    def test_lean_scaled_formulas_on_registered_grid(self):
        results = benchmark()
        for index, point in enumerate(audit()["tag_stress_sweep"]):
            self.assertEqual(point["tag_error"], F(index, 100))
            self.assertEqual(point["provenance_minus_bit_only_risk"], F(3100 + 24 * index - 3700, 16000))
        for sky_cost, data in results["unnecessary_repair_costs"].items():
            self.assertEqual(len(data["sweep"]), 101)
            for index, point in enumerate(data["sweep"]):
                self.assertEqual(point["tag_error"], F(index, 100))
                scaled = 9 * (150 + 12 * index) - 1500 * int(sky_cost)
                self.assertEqual(point["provenance_minus_bit_only_cost"], F(scaled, 80000))

    def test_deterministic_archived_result(self):
        archived = Path(__file__).resolve().parents[1] / "docs/results/AR-SWARM003-P01.json"
        expected = json.dumps(benchmark(), default=str, indent=2, sort_keys=True) + "\n"
        self.assertEqual(archived.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
