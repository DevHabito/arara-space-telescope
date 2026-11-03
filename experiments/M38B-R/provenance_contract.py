"""Read-only historical-geometry checks for M38B-R research provenance.

This describes the archived candidate's mathematical input geometry. It does
NOT freeze the new experimental identity, approve calibration, or modify code.
Small diagnostic fixtures intentionally fail the complete historical geometry.
"""
from __future__ import annotations

# Checked directly against archived M32/M34 defaults and M38B protocol metadata.
HISTORICAL_GEOMETRY = {
    "endpoint_start": 81,
    "endpoint_stop": 179,
    "window_length": 8,
    "selection_start": 50,
    "guard_length": 1,
    "confirmation_length": 8,
    "candidate_onset_low": 70,
    "candidate_onset_high": 120,
}

HISTORICAL_BASELINE_LENGTH = 50


def historical_geometry_findings(cfg: object, *, baseline_n: int = 50) -> tuple[str, ...]:
    """Identify geometry departures; never silently repair or authorize them."""
    findings: list[str] = []
    for field, expected in HISTORICAL_GEOMETRY.items():
        value = getattr(cfg, field, None)
        if type(value) is not int or value != expected:
            findings.append(f"GEOMETRY_DRIFT:{field}:expected={expected}:actual={value!r}")
    if type(baseline_n) is not int or baseline_n != HISTORICAL_BASELINE_LENGTH:
        findings.append(
            f"BASELINE_DRIFT:expected={HISTORICAL_BASELINE_LENGTH}:actual={baseline_n!r}"
        )
    return tuple(findings)
