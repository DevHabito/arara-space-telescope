"""Read-only provenance and protocol preflight for prospective ARARA M38B-R.

The command never generates scientific observations, changes frozen inputs,
or authorizes opening calibration or holdout outcomes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
DESIGN = Path("experiments/M38B-R")
ARCHIVE = Path("milestones/M38B_recovery")
SOURCE_SUFFIXES = frozenset({".py", ".json", ".md", ".txt"})
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
PRIOR_SEEDS = frozenset(range(2026090501, 2026090505)) | frozenset(
    range(2026090601, 2026090605)
)


def digest_file(path: Path) -> str:
    """Hash files incrementally rather than loading their entire contents."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validated_archive_path(root: Path, name: str) -> Path | None:
    """Reject noncanonical paths, traversal and symlinks outside the archive."""
    if not isinstance(name, str) or not name or "\\" in name:
        return None
    parts = PurePosixPath(name).parts
    if (
        name.startswith("/")
        or "." in parts
        or ".." in parts
        or not name.startswith(f"{ARCHIVE.as_posix()}/")
        or PurePosixPath(name).as_posix() != name
    ):
        return None
    target = root / name
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        return None
    return target


def verify_source_freeze(root: Path, freeze: dict) -> list[str]:
    """Compare bytes and require coverage of the complete historical package."""
    findings: list[str] = []
    expected = freeze.get("files")
    if not isinstance(expected, dict) or not expected:
        return ["INVALID_FREEZE_INVENTORY"]

    frozen_paths: set[str] = set()
    for name, expected_hash in sorted(expected.items()):
        path = validated_archive_path(root, name)
        if path is None:
            findings.append(f"UNSAFE_PATH:{name}")
            continue
        frozen_paths.add(name)
        if not isinstance(expected_hash, str) or not DIGEST_PATTERN.fullmatch(expected_hash):
            findings.append(f"INVALID_DIGEST:{name}")
        elif not path.is_file():
            findings.append(f"MISSING_FILE:{name}")
        elif digest_file(path) != expected_hash:
            findings.append(f"MODIFIED_FILE:{name}")

    archive = root / ARCHIVE
    if not archive.is_dir():
        findings.append("ARCHIVE_DIRECTORY_MISSING")
    else:
        existing = {
            path.relative_to(root).as_posix()
            for path in archive.rglob("*")
            if path.is_file()
            and path.suffix in SOURCE_SUFFIXES
            and "__pycache__" not in path.parts
        }
        for name in sorted(existing - frozen_paths):
            findings.append(f"UNFROZEN_ARCHIVE_FILE:{name}")
    if len(expected) != freeze.get("frozen_file_count"):
        findings.append("FROZEN_FILE_COUNT_MISMATCH")
    return findings


def verify_protocol(spec: dict, frozen_grid: dict, recovery: dict, design: dict) -> list[str]:
    """Check experiment identity and invariant dimensions without importing the detector."""
    findings: list[str] = []
    if design.get("experiment_id") != "ARARA-M38B-R" or design.get("stage") != "design_only":
        findings.append("DESIGN_IDENTITY_INVALID")
    if frozen_grid.get("latent_grid") != EXPECTED_GRID or spec.get("latent_grid") != EXPECTED_GRID:
        findings.append("LATENT_GRID_CHANGED")
    durations = spec.get("durations", [])
    if durations != list(range(24, 61)):
        findings.append("DURATION_GRID_CHANGED")
    endpoints = spec.get("endpoint_stop", 0) - spec.get("endpoint_start", 0) + 1
    if (spec.get("endpoint_start"), spec.get("endpoint_stop")) != (81, 179):
        findings.append("ENDPOINT_GRID_CHANGED")
    if spec.get("fixed_snr") != 13.75 or spec.get("primary_latency") != 4:
        findings.append("SIGNAL_OR_LATENCY_CHANGED")
    if spec.get("control_hypothesis_count") != endpoints * 4 * len(durations):
        findings.append("CONTROL_COUNT_INVALID")
    if spec.get("candidate_hypothesis_count") != endpoints * 4 * len(durations) * len(spec.get("latent_grid", [])):
        findings.append("CANDIDATE_COUNT_INVALID")
    if (
        spec.get("calibration_block_count") != 4
        or spec.get("calibration_negatives_per_block_per_family") != 50_000
        or spec.get("calibration_negatives_per_family") != 200_000
        or spec.get("holdout_count") != 10
        or spec.get("bootstrap_replicates") != 10_000
    ):
        findings.append("PROTOCOL_SAMPLE_COUNTS_CHANGED")
    if design.get("source_protocol_version") != spec.get("version"):
        findings.append("PROTOCOL_VERSION_MISMATCH")
    if design.get("source_grid_verdict") != frozen_grid.get("verdict"):
        findings.append("GRID_VERDICT_MISMATCH")
    seeds = design.get("proposed_seed_roots", {})
    if not isinstance(seeds, dict) or set(seeds) != {
        "calibration", "holdouts", "aggregate_bootstrap", "paired_bootstrap"
    }:
        findings.append("SEED_FIELDS_INVALID")
    elif (
        any(not isinstance(value, int) or isinstance(value, bool) for value in seeds.values())
        or len(set(seeds.values())) != 4
        or bool(set(seeds.values()) & PRIOR_SEEDS)
    ):
        findings.append("SEED_PLAN_INVALID")
    if spec.get("calibration_seed") != 2026090501:
        findings.append("HISTORICAL_SEED_CHANGED")
    if recovery.get("calibration_blocks", {}).get("0", {}).get("quiet", {}).get("entropy") != 2026090601:
        findings.append("RECOVERY_SEED_CHANGED")
    return findings


def run_preflight(root: Path = ROOT) -> dict:
    """Return integrity findings. An integrity pass is never an operational verdict."""
    design_dir = root / DESIGN
    freeze = json.loads((design_dir / "SOURCE_FREEZE.json").read_text(encoding="utf-8"))
    design = json.loads((design_dir / "PROTOCOL_DRAFT.json").read_text(encoding="utf-8"))
    archive_dir = root / ARCHIVE
    spec = json.loads((archive_dir / "ARARA_M38B_SPEC.json").read_text(encoding="utf-8"))
    grid = json.loads((archive_dir / "FROZEN_LATENT_GRID_M38A.json").read_text(encoding="utf-8"))
    recovery = json.loads((archive_dir / "FROZEN_SEEDS_RECOVERY.json").read_text(encoding="utf-8"))
    findings = verify_source_freeze(root, freeze)
    findings += verify_protocol(spec, grid, recovery, design)
    if freeze.get("source_commit") != design.get("archived_source_commit"):
        findings.append("SOURCE_COMMIT_MISMATCH")
    return {
        "experiment": "ARARA-M38B-R",
        "status": "PREFLIGHT_FAILED" if findings else "DESIGN_SOURCE_INTEGRITY_PASS",
        "approved_for_calibration": False,
        "operational_verdict": None,
        "frozen_archived_files": len(freeze.get("files", {})),
        "source_commit": freeze.get("source_commit"),
        "candidate_nominal_slots": 73_260,
        "candidate_evaluations_per_curve": 58_608,
        "remaining_conditions": [
            "Pin and verify a reproducible runtime environment",
            "Benchmark resources without inspecting scientific holdouts",
            "Freeze an independent runner, seeds, checkpoints and verifier",
            "Prospectively approve calibration only after all gates pass",
        ],
        "findings": sorted(set(findings)),
    }


def main() -> int:
    try:
        report = run_preflight()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "PREFLIGHT_FAILED", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "DESIGN_SOURCE_INTEGRITY_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
