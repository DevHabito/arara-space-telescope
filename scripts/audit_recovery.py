"""Read-only structural audit of the archived M38B recovery protocol.

Do not infer an experimental verdict from the existence of source files,
a passing unit-test suite, or a recovered random-seed plan.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RECOVERY_PATH = Path("milestones/M38B_recovery")
REQUIRED_RESULTS = (
    "results/FROZEN_THRESHOLDS.json",
    "results/PRE_HOLDOUT_RECOVERY_FREEZE_SHA256.json",
    "results/VERDICT.json",
)


def verify_manifest(root: Path, manifest: dict[str, str]) -> list[str]:
    """Return discrepancies without following paths outside the archive."""
    issues: list[str] = []
    base = root.resolve()
    for name, expected_digest in sorted(manifest.items()):
        path = (base / name).resolve()
        if not path.is_relative_to(base):
            issues.append(f"UNSAFE_MANIFEST_PATH:{name}")
        elif not path.is_file():
            issues.append(f"MISSING_FROZEN_FILE:{name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_digest:
            issues.append(f"FROZEN_HASH_MISMATCH:{name}")
    return issues


def audit(root: Path = REPOSITORY_ROOT) -> dict[str, object]:
    """Report structural evidence only, without simulating observations."""
    package = root / RECOVERY_PATH
    spec = json.loads((package / "ARARA_M38B_SPEC.json").read_text(encoding="utf-8"))
    seed_plan = json.loads(
        (package / "FROZEN_SEEDS_RECOVERY.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (package / "results/PRE_CALIBRATION_RECOVERY_FREEZE_SHA256.json").read_text(
            encoding="utf-8"
        )
    )
    findings = verify_manifest(package, manifest)

    endpoints = spec["endpoint_stop"] - spec["endpoint_start"] + 1
    durations = len(spec["durations"])
    latent_points = len(spec["latent_grid"])
    # The four shapes are specified in the original M38B preregistration.
    control_count = endpoints * 4 * durations
    candidate_count = control_count * latent_points
    if (control_count, candidate_count) != (
        spec["control_hypothesis_count"], spec["candidate_hypothesis_count"]
    ):
        findings.append("HYPOTHESIS_COUNT_MISMATCH")

    recovered_seed = seed_plan["calibration_blocks"]["0"]["quiet"]["entropy"]
    if recovered_seed != spec["calibration_seed"]:
        findings.append("SPEC_RECOVERY_SEED_DIVERGENCE")

    source_files = sorted(
        path.relative_to(package).as_posix()
        for path in package.rglob("*.py")
        if path.is_file()
    )
    unprotected = sorted(set(source_files) - set(manifest))
    if unprotected:
        findings.append("UNCOVERED_EXECUTABLE_SOURCES")

    runner = (package / "run_full_recovery.py").read_text(encoding="utf-8")
    if "Path('/mnt/data/ARARA_M38B')" in runner:
        findings.append("ABSOLUTE_EXECUTION_PATH")

    missing_results = [
        name for name in REQUIRED_RESULTS if not (package / name).is_file()
    ]
    missing_holdouts = [
        index
        for index in range(spec["holdout_count"])
        if not (
            package / f"results/holdouts/holdout_{index:02d}_method_summary.csv"
        ).is_file()
    ]
    if missing_results or missing_holdouts:
        findings.append("INCOMPLETE_OPERATIONAL_EVIDENCE")

    integrity_failure = any(
        item.startswith(
            ("UNSAFE_MANIFEST_PATH:", "MISSING_FROZEN_FILE:", "FROZEN_HASH_MISMATCH:")
        )
        for item in findings
    )
    if integrity_failure:
        status = "INTEGRITY_FAILURE"
    elif "INCOMPLETE_OPERATIONAL_EVIDENCE" in findings:
        status = "NO_OPERATIONAL_VERDICT"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "status": status,
        "scope": "archived M38B recovery; structural checks only",
        "control_hypotheses": control_count,
        "candidate_hypotheses": candidate_count,
        "original_calibration_seed": spec["calibration_seed"],
        "recovered_calibration_seed": recovered_seed,
        "unprotected_executable_files": unprotected,
        "missing_required_results": missing_results,
        "missing_holdouts": missing_holdouts,
        "findings": sorted(set(findings)),
    }


def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    # Incomplete archived results are expected. Corrupted protected evidence
    # or an incorrect bank size is a separate, actionable regression.
    if result["status"] == "INTEGRITY_FAILURE":
        return 1
    if "HYPOTHESIS_COUNT_MISMATCH" in result["findings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
