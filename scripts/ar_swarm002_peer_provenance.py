"""Exact two-observer audit benchmark specified in AR-SWARM002-P01."""

import json
from fractions import Fraction as F
from itertools import product


LABELS = ("fault", "sky")
ACTIONS = ("abstain", *LABELS)
SCENARIOS = {
    "nominal": (F(3, 4), F(1, 10), F(1, 10)),
    "perfect_tag": (F(3, 4), F(1, 10), F(0)),
    "uninformative_tag": (F(3, 4), F(1, 10), F(1, 2)),
    "inverted_tag": (F(3, 4), F(1, 10), F(1)),
    "no_coverage": (F(0), F(1, 10), F(1, 10)),
    "uninformative_report": (F(3, 4), F(1, 2), F(1, 10)),
}


def joint_mass(coverage, report_error, tag_error):
    """Yield truth and permitted observations with exact joint weights."""
    for label in LABELS:
        yield label, None, None, (1 - coverage) / 2
        for shared, report_flip, tag_flip in product((False, True), repeat=3):
            bit = (label == "sky" or shared) ^ report_flip
            tag = shared ^ tag_flip
            report_mass = report_error if report_flip else 1 - report_error
            tag_mass = tag_error if tag_flip else 1 - tag_error
            yield label, bit, tag, coverage * report_mass * tag_mass / 4


def loss(action, label):
    return F(1, 4) if action == "abstain" else F(action != label)


def nominal_table(use_tag):
    """Minimize nominal loss separately for each available observation."""
    risks = {}
    for label, bit, tag, mass in joint_mass(*SCENARIOS["nominal"]):
        key = (bit, tag if use_tag else None)
        costs = risks.setdefault(key, dict.fromkeys(ACTIONS, F(0)))
        for action in ACTIONS:
            costs[action] += mass * loss(action, label)
    return {key: min(costs, key=costs.get) for key, costs in risks.items()}


def score(policy, rows):
    masses = {label: dict.fromkeys(ACTIONS, F(0)) for label in LABELS}
    for label, bit, tag, mass in rows:
        masses[label][policy(bit, tag)] += mass
    if any(sum(actions.values()) != F(1, 2) for actions in masses.values()):
        raise ValueError("Expected conserved joint mass with equal truth priors")
    abstained = sum(actions["abstain"] for actions in masses.values())
    wrong = masses["fault"]["sky"] + masses["sky"]["fault"]
    coverage = 1 - abstained
    return {
        "risk": wrong + abstained / 4,
        "coverage": coverage,
        "error_given_decision": wrong / coverage if coverage else None,
        "action_given_label": {
            label: {action: 2 * mass for action, mass in actions.items()}
            for label, actions in masses.items()
        },
    }


def benchmark():
    bit_only = nominal_table(use_tag=False)
    provenance = nominal_table(use_tag=True)
    policies = {
        "a_alone": lambda bit, tag: "abstain",
        "literal_agreement": lambda bit, tag: {None: "abstain", True: "sky", False: "fault"}[bit],
        "bit_only": lambda bit, tag: bit_only[bit, None],
        "bit_and_provenance": lambda bit, tag: provenance[bit, tag],
    }
    scenarios = {
        name: {policy: score(rule, tuple(joint_mass(*parameters)))
               for policy, rule in policies.items()}
        for name, parameters in SCENARIOS.items()
    }
    nominal = scenarios["nominal"]
    inverted = scenarios["inverted_tag"]
    nominal_risk = nominal["bit_and_provenance"]["risk"]
    coverage, report_error, _ = SCENARIOS["nominal"]
    sweep = []
    for k in range(101):
        tag_error = F(k, 100)
        rows = tuple(joint_mass(coverage, report_error, tag_error))
        delta = (score(policies["bit_and_provenance"], rows)["risk"]
                 - score(policies["bit_only"], rows)["risk"])
        sweep.append({"tag_error": tag_error, "provenance_minus_bit_only_risk": delta})
    return {
        "protocol": "AR-SWARM002-P01",
        "parameters": SCENARIOS,
        "nominal_decisions": {
            name: [{"bit": bit, "shared_tag": tag, "action": action}
                   for (bit, tag), action in table.items()]
            for name, table in (("bit_only", bit_only), ("bit_and_provenance", provenance))
        },
        "scenarios": scenarios,
        "tag_stress_sweep": sweep,
        "hypotheses": {
            "H1": nominal_risk < min(nominal["bit_only"]["risk"], nominal["a_alone"]["risk"]),
            "H2": inverted["bit_and_provenance"]["risk"] > inverted["bit_only"]["risk"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(benchmark(), default=str, indent=2, sort_keys=True))
