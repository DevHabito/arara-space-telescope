"""Regression and deliberately adverse tests for archived research provenance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_recovery import audit, verify_manifest  # noqa: E402


class FrozenManifestTests(unittest.TestCase):
    def test_matching_digest_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "record.txt").write_bytes(b"frozen")
            expected = hashlib.sha256(b"frozen").hexdigest()
            self.assertEqual(verify_manifest(root, {"record.txt": expected}), [])

    def test_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "record.txt").write_bytes(b"changed")
            original = hashlib.sha256(b"frozen").hexdigest()
            self.assertEqual(
                verify_manifest(root, {"record.txt": original}),
                ["FROZEN_HASH_MISMATCH:record.txt"],
            )

    def test_missing_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                verify_manifest(Path(directory), {"lost.txt": "0" * 64}),
                ["MISSING_FROZEN_FILE:lost.txt"],
            )

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                verify_manifest(Path(directory), {"../outside": "0" * 64}),
                ["UNSAFE_MANIFEST_PATH:../outside"],
            )


class RecoveryAuditTests(unittest.TestCase):
    @staticmethod
    def fixture(destination: Path) -> Path:
        package = destination / "milestones" / "M38B_recovery"
        (package / "results").mkdir(parents=True)
        specification = {
            "endpoint_start": 81,
            "endpoint_stop": 179,
            "durations": list(range(24, 61)),
            "latent_grid": [0.0, 0.25, 0.5, 0.75, 1.0],
            "control_hypothesis_count": 14_652,
            "candidate_hypothesis_count": 73_260,
            "calibration_seed": 2026090501,
            "holdout_count": 10,
        }
        source = package / "arara_m38b.py"
        source.write_text("# synthetic test fixture only\n", encoding="utf-8")
        (package / "run_full_recovery.py").write_text(
            "ROOT=Path('/mnt/data/ARARA_M38B')\n", encoding="utf-8"
        )
        (package / "ARARA_M38B_SPEC.json").write_text(
            json.dumps(specification), encoding="utf-8"
        )
        (package / "FROZEN_SEEDS_RECOVERY.json").write_text(
            json.dumps(
                {"calibration_blocks": {"0": {"quiet": {"entropy": 2026090601}}}}
            ),
            encoding="utf-8",
        )
        manifest = {"arara_m38b.py": hashlib.sha256(source.read_bytes()).hexdigest()}
        (package / "results/PRE_CALIBRATION_RECOVERY_FREEZE_SHA256.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return package

    def test_missing_results_remain_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            result = audit(Path(directory)) if False else None
            package = self.fixture(Path(directory))
            result = audit(Path(directory))
            self.assertEqual(result["status"], "NO_OPERATIONAL_VERDICT")
            self.assertIn("SPEC_RECOVERY_SEED_DIVERGENCE", result["findings"])
            self.assertIn("UNCOVERED_EXECUTABLE_SOURCES", result["findings"])
            self.assertIn("ABSOLUTE_EXECUTION_PATH", result["findings"])
            self.assertEqual(result["candidate_hypotheses"], 73_260)
            self.assertEqual(len(result["missing_holdouts"]), 10)

    def test_changed_source_is_integrity_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.fixture(Path(directory))
            (package / "arara_m38b.py").write_bytes(b"tampered")
            result = audit(Path(directory))
            self.assertEqual(result["status"], "INTEGRITY_FAILURE")
            self.assertIn("FROZEN_HASH_MISMATCH:arara_m38b.py", result["findings"])

    def test_hypothesis_count_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.fixture(Path(directory))
            specification = package / "ARARA_M38B_SPEC.json"
            data = json.loads(specification.read_text(encoding="utf-8"))
            data["candidate_hypothesis_count"] = 73_259
            specification.write_text(json.dumps(data), encoding="utf-8")
            result = audit(Path(directory))
            self.assertIn("HYPOTHESIS_COUNT_MISMATCH", result["findings"])

    def test_recalibrated_threshold_can_reverse_an_alert(self):
        control_score, control_threshold = 5, 4
        candidate_score, candidate_threshold = 6, 7
        self.assertGreaterEqual(candidate_score, control_score)
        self.assertGreaterEqual(control_score, control_threshold)
        self.assertLess(candidate_score, candidate_threshold)


class HistoricalEvidenceTests(unittest.TestCase):
    def test_archive_is_not_promoted_to_operational_pass(self):
        if not (ROOT / "milestones/M38B_recovery/ARARA_M38B_SPEC.json").exists():
            self.skipTest("Complete historical archive not present in local runtime")
        result = audit(ROOT)
        self.assertEqual(result["status"], "NO_OPERATIONAL_VERDICT")
        self.assertEqual(result["control_hypotheses"], 14_652)
        self.assertEqual(result["candidate_hypotheses"], 73_260)
        self.assertIn("INCOMPLETE_OPERATIONAL_EVIDENCE", result["findings"])
        self.assertIn("UNCOVERED_EXECUTABLE_SOURCES", result["findings"])


if __name__ == "__main__":
    unittest.main()
