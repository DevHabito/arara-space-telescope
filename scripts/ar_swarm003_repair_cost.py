"""Exact cost of acting on the frozen AR-SWARM002 peer audit."""

import json
from fractions import Fraction as F

from scripts.ar_swarm002_peer_provenance import SCENARIOS, joint_mass, nominal_table


def score(policy, rows, sky_cost):
    repairs = {"sky": F(0), "fault": F(0)}
    totals = repairs.copy()
    for label, bit, tag, mass in rows:
        totals[label] += mass
        if policy(bit, tag):
            repairs[label] += mass
    if set(totals.values()) != {F(1, 2)}:
        raise ValueError("Each truth class must have probability 1/2")
    missed_faults = totals["fault"] - repairs["fault"]
    return {
        "cost": sky_cost * repairs["sky"] + repairs["fault"] / 10 + missed_faults,
        "repair_given_sky": 2 * repairs["sky"],
        "defer_given_fault": 2 * missed_faults,
        "repair": sum(repairs.values()),
    }


def nominal_repair_table(sky_cost):
    masses = {}
    for label, bit, tag, mass in joint_mass(*SCENARIOS["nominal"]):
        by_label = masses.setdefault((bit, tag), {"sky": F(0), "fault": F(0)})
        by_label[label] += mass
    return {
        key: sky_cost * values["sky"] < F(9, 10) * values["fault"]
        for key, values in masses.items()
    }


def regime(sky_cost):
    bit_only = nominal_table(use_tag=False)
    provenance = nominal_table(use_tag=True)
    direct = nominal_repair_table(sky_cost)
    policies = {
        "defer_all": lambda bit, tag: False,
        "repair_all": lambda bit, tag: True,
        "literal_agreement": lambda bit, tag: bit is False,
        "bit_only": lambda bit, tag: bit_only[bit, None] == "fault",
        "bit_and_provenance": lambda bit, tag: provenance[bit, tag] == "fault",
        "direct_nominal_bayes": lambda bit, tag: direct[bit, tag],
    }
    scenarios = {}
    for name, parameters in SCENARIOS.items():
        rows = tuple(joint_mass(*parameters))
        scenarios[name] = {name: score(rule, rows, sky_cost) for name, rule in policies.items()}

    coverage, report_error, _ = SCENARIOS["nominal"]
    sweep = []
    for index in range(101):
        tag_error = F(index, 100)
        rows = tuple(joint_mass(coverage, report_error, tag_error))
        delta = (score(policies["bit_and_provenance"], rows, sky_cost)["cost"]
                 - score(policies["bit_only"], rows, sky_cost)["cost"])
        sweep.append({"tag_error": tag_error, "provenance_minus_bit_only_cost": delta})
    return {
        "scenarios": scenarios,
        "direct_nominal_actions": [
            {"bit": bit, "shared_tag": tag, "repair": action}
            for (bit, tag), action in direct.items()
        ],
        "sweep": sweep,
    }


def benchmark():
    costs = {str(cost): regime(F(cost)) for cost in (1, 4)}
    primary = costs["1"]["scenarios"]
    nominal, inverted = primary["nominal"], primary["inverted_tag"]
    return {
        "protocol": "AR-SWARM003-P01",
        "unnecessary_repair_costs": costs,
        "hypotheses": {
            "H1": nominal["bit_and_provenance"]["cost"] < nominal["bit_only"]["cost"],
            "H2": inverted["bit_and_provenance"]["cost"] > inverted["bit_only"]["cost"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(benchmark(), default=str, indent=2, sort_keys=True))
