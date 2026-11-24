"""Exact one-step service outcomes on a weighted, two-sector network."""

import json
from fractions import Fraction


SECTORS = {"A0": "A", "A1": "A", "B0": "B", "B1": "B"}
SOURCES = {"A": "A0", "B": "B0"}
WEIGHTS = {"A0": {"A1": 3, "B1": 1}, "A1": {"A0": 1},
           "B0": {"A1": 1, "B1": 3}, "B1": {"B0": 1}}
REROUTED = {**WEIGHTS, "A0": {"A1": 7, "B1": 1}}
DEMAND_SHARES = tuple(Fraction(n, 4) for n in (1, 2, 3))


def transition_rows(weights):
    """Normalize active rows and retain zero rows as all zero."""
    rows = {}
    for source, edges in weights.items():
        total = sum(edges.values())
        rows[source] = {
            target: Fraction(weight, total) if total else Fraction(0)
            for target, weight in edges.items()
        }
    return rows


def structure(rows, sectors):
    result = {}
    for sector in sorted(set(sectors.values())):
        members = [node for node, label in sectors.items() if label == sector]
        autonomy = sum(
            probability
            for member in members
            for target, probability in rows[member].items()
            if sectors[target] == sector
        ) / Fraction(len(members))
        result[sector] = {"autonomy": autonomy, "exchange": 1 - autonomy}
    return {
        "sectors": result,
        "mean_exchange": sum(value["exchange"] for value in result.values()) / len(result),
    }


def source_correctness(rows, sources, availability):
    return {
        sector: sum(probability * availability[service]
                    for service, probability in rows[source].items())
        for sector, source in sources.items()
    }


def network_correctness(outcomes, a_demand):
    return a_demand * outcomes["A"] + (1 - a_demand) * outcomes["B"]


def evaluate():
    standard, rerouted = transition_rows(WEIGHTS), transition_rows(REROUTED)
    policies = {"defer": standard, "repair_only": standard, "repair_and_reroute": rerouted}
    baseline = source_correctness(standard, SOURCES, {"A1": Fraction(1, 2), "B1": 1})
    grid = []
    for index in range(101):
        spillover = Fraction(index, 100)
        repaired = {"A1": 1, "B1": 1 - spillover}
        policy_results = {}
        for name, rows in policies.items():
            outcomes = baseline if name == "defer" else source_correctness(rows, SOURCES, repaired)
            delta = {sector: value - baseline[sector] for sector, value in outcomes.items()}
            policy_results[name] = {
                "correctness_by_sector": outcomes,
                "delta_by_sector": delta,
                "network": [
                    {"a_demand_share": share, "correctness": network_correctness(outcomes, share),
                     "delta": network_correctness(delta, share)}
                    for share in DEMAND_SHARES
                ],
            }
        grid.append({"spillover": spillover, "policies": policy_results})

    def balanced_delta(point, policy):
        return point["policies"][policy]["network"][1]["delta"]

    return {
        "protocol": "AR-SWARM004-P01",
        "structure": {name: structure(rows, SECTORS) for name, rows in policies.items()},
        "grid": grid,
        "hypotheses": {
            "H1": any(p["policies"]["repair_only"]["delta_by_sector"]["A"] > 0
                      > p["policies"]["repair_only"]["delta_by_sector"]["B"]
                      and balanced_delta(p, "repair_only") < 0 for p in grid),
            "H2": any(balanced_delta(p, "repair_and_reroute") > 0
                      > balanced_delta(p, "repair_only") for p in grid),
            "H3": balanced_delta(grid[0], "repair_only") > 0
                  > balanced_delta(grid[-1], "repair_only"),
        },
    }


def archive():
    """Keep all results with a single shared column definition."""
    result = evaluate()
    rows = []
    for point in result.pop("grid"):
        for name, policy in point["policies"].items():
            rows.append([
                point["spillover"], name,
                *(policy["correctness_by_sector"][sector] for sector in ("A", "B")),
                *(policy["delta_by_sector"][sector] for sector in ("A", "B")),
                *(item["correctness"] for item in policy["network"]),
                *(item["delta"] for item in policy["network"]),
            ])
    result["columns"] = [
        "spillover", "policy", "correct_A", "correct_B", "delta_A", "delta_B",
        "network_correct_A_share_1/4", "network_correct_A_share_1/2", "network_correct_A_share_3/4",
        "network_delta_A_share_1/4", "network_delta_A_share_1/2", "network_delta_A_share_3/4",
    ]
    header = json.dumps(result, indent=2, sort_keys=True, default=str)
    contents = ",\n".join("    " + json.dumps(row, default=str) for row in rows)
    return header[:-2] + ',\n  "rows": [\n' + contents + "\n  ]\n}\n"


if __name__ == "__main__":
    print(archive(), end="")
