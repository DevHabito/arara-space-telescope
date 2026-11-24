"""Invariants and exact correspondence with the scaled Lean model."""

from fractions import Fraction as F
from pathlib import Path
import json
import unittest

from scripts.ar_swarm004_sector_spillovers import (
    DEMAND_SHARES, REROUTED, SECTORS, SOURCES, WEIGHTS, archive, evaluate,
    network_correctness, source_correctness, structure, transition_rows,
)


class SectorSpilloverTests(unittest.TestCase):
    def test_normalization_and_exchange(self):
        expected = ((WEIGHTS, F(1, 8)), (REROUTED, F(3, 32)))
        for weights, exchange in expected:
            rows = transition_rows(weights)
            self.assertTrue(all(sum(row.values()) == 1 for row in rows.values()))
            measured = structure(rows, SECTORS)
            self.assertEqual(measured["mean_exchange"], exchange)
            for values in measured["sectors"].values():
                self.assertEqual(values["autonomy"] + values["exchange"], 1)
        self.assertEqual(transition_rows({"A": {"B": 0}}), {"A": {"B": F(0)}})

    def test_label_swap_and_reversed_demand(self):
        swapped_sources = {"A": SOURCES["B"], "B": SOURCES["A"]}
        swapped_sectors = {node: "A" if label == "B" else "B"
                           for node, label in SECTORS.items()}
        for weights in (WEIGHTS, REROUTED):
            rows = transition_rows(weights)
            original, swapped = structure(rows, SECTORS), structure(rows, swapped_sectors)
            self.assertEqual(original["mean_exchange"], swapped["mean_exchange"])
            self.assertEqual(original["sectors"]["A"], swapped["sectors"]["B"])
            for k in range(101):
                availability = {"A1": 1, "B1": 1 - F(k, 100)}
                original = source_correctness(rows, SOURCES, availability)
                swapped = source_correctness(rows, swapped_sources, availability)
                for share in DEMAND_SHARES:
                    self.assertEqual(network_correctness(original, share),
                                     network_correctness(swapped, 1 - share))

    def test_accounting_and_lean_scaled_grid(self):
        result = evaluate()
        self.assertEqual(len(result["grid"]), 101)
        for k, point in enumerate(result["grid"]):
            self.assertEqual(point["spillover"], F(k, 100))
            policies = point["policies"]
            simple, reroute = policies["repair_only"], policies["repair_and_reroute"]
            self.assertEqual(simple["delta_by_sector"], {"A": F(600 - 4 * k, 1600),
                                                        "B": F(200 - 12 * k, 1600)})
            self.assertEqual(simple["network"][1]["delta"], F(400 - 8 * k, 1600))
            self.assertEqual(reroute["network"][1]["delta"], F(400 - 7 * k, 1600))
            for policy in policies.values():
                for row, baseline in zip(policy["network"], policies["defer"]["network"]):
                    self.assertTrue(0 <= row["correctness"] <= 1)
                    self.assertEqual(row["correctness"] - baseline["correctness"], row["delta"])
                self.assertTrue(all(0 <= v <= 1 for v in policy["correctness_by_sector"].values()))

    def test_deterministic_archive(self):
        expected = Path(__file__).resolve().parents[1] / "docs/results/AR-SWARM004-P01.json"
        text = archive()
        self.assertEqual(text, archive())
        self.assertEqual(text, expected.read_text(encoding="utf-8"))
        rows = json.loads(text)["rows"]
        self.assertEqual(len(rows), 303)
        self.assertTrue(all(len(row) == 12 for row in rows))


if __name__ == "__main__":
    unittest.main()
