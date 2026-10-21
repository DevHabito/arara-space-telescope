"""Deliberately adverse regressions for the prospective M38B-R integrity gate."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from m38br_preflight import (  # noqa: E402
    digest_file,
    run_preflight,
    validated_archive_path,
    verify_protocol,
    verify_source_freeze,
)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "milestones/M38B_recovery"
        self.design_dir = self.root / "experiments/M38B-R"
        self.archive.mkdir(parents=True)
        self.design_dir.mkdir(parents=True)
        self.spec = {
            "version": "38B.0", "endpoint_start": 81, "endpoint_stop": 179,
            "durations": list(range(24, 61)),
            "latent_grid": [0.0, 0.25, 0.5, 0.75, 1.0],
            "control_hypothesis_count": 14652, "candidate_hypothesis_count": 73260,
            "fixed_snr": 13.75, "primary_latency": 4,
            "calibration_block_count": 4,
            "calibration_negatives_per_block_per_family": 50000,
            "calibration_negatives_per_family": 200000,
            "holdout_count": 10, "bootstrap_replicates": 10000,
            "calibration_seed": 2026090501,
        }
        self.grid = {
            "latent_grid": [0.0, 0.25, 0.5, 0.75, 1.0],
            "verdict": "PASS_M38A_LATENT_GRID_ELIGIBLE_K5",
        }
        self.recovery = {"calibration_blocks": {"0": {"quiet": {"entropy": 2026090601}}}}
        self.design = {
            "experiment_id": "ARARA-M38B-R",
            "stage": "design_only",
            "archived_source_commit": "test-commit",
            "source_protocol_version": "38B.0",
            "source_grid_verdict": "PASS_M38A_LATENT_GRID_ELIGIBLE_K5",
            "proposed_seed_roots": {
                "calibration": 2026102101, "holdouts": 2026102102,
                "aggregate_bootstrap": 2026102103, "paired_bootstrap": 2026102104,
            },
        }
        self.write_fixture()

    def write_fixture(self):
        fixture_files = {
            "ARARA_M38B_SPEC.json": self.spec,
            "FROZEN_LATENT_GRID_M38A.json": self.grid,
            "FROZEN_SEEDS_RECOVERY.json": self.recovery,
        }
        for name, value in fixture_files.items():
            (self.archive / name).write_text(json.dumps(value), encoding="utf-8")
        files = {
            f"milestones/M38B_recovery/{file.name}": digest_file(file)
            for file in self.archive.iterdir() if file.is_file()
        }
        (self.design_dir / "SOURCE_FREEZE.json").write_text(
            json.dumps({
                "source_commit": "test-commit",
                "frozen_file_count": len(files),
                "files": files,
            }), encoding="utf-8",
        )
        (self.design_dir / "PROTOCOL_DRAFT.json").write_text(
            json.dumps(self.design), encoding="utf-8"
        )

    def test_pass_remains_design_only(self):
        result = run_preflight(self.root)
        self.assertEqual(result["status"], "DESIGN_SOURCE_INTEGRITY_PASS")
        self.assertFalse(result["approved_for_calibration"])
        self.assertIsNone(result["operational_verdict"])

    def test_file_mutation_is_detected(self):
        (self.archive / "ARARA_M38B_SPEC.json").write_text("{}", encoding="utf-8")
        result = run_preflight(self.root)
        self.assertEqual(result["status"], "PREFLIGHT_FAILED")
        self.assertTrue(any(item.startswith("MODIFIED_FILE:") for item in result["findings"]))

    def test_additional_unfrozen_source_is_detected(self):
        (self.archive / "new_source.py").write_text("pass\n", encoding="utf-8")
        self.assertTrue(any(
            item.startswith("UNFROZEN_ARCHIVE_FILE:")
            for item in run_preflight(self.root)["findings"]
        ))

    def test_missing_file_is_detected(self):
        (self.archive / "ARARA_M38B_SPEC.json").unlink()
        freeze = json.loads((self.design_dir / "SOURCE_FREEZE.json").read_text())
        self.assertTrue(any(
            item.startswith("MISSING_FILE:")
            for item in verify_source_freeze(self.root, freeze)
        ))

    def test_path_escape_is_rejected(self):
        for path in (
            "milestones/M38B_recovery/../../escape",
            "/milestones/M38B_recovery/escape",
            "milestones\\M38B_recovery\\escape",
            "C:/milestones/M38B_recovery/escape",
        ):
            self.assertIsNone(validated_archive_path(self.root, path))

    def test_reused_seed_is_detected(self):
        self.design["proposed_seed_roots"]["calibration"] = 2026090601
        self.assertIn(
            "SEED_PLAN_INVALID",
            verify_protocol(self.spec, self.grid, self.recovery, self.design),
        )

    def test_hypothesis_count_change_is_detected(self):
        self.spec["candidate_hypothesis_count"] -= 1
        self.assertIn(
            "CANDIDATE_COUNT_INVALID",
            verify_protocol(self.spec, self.grid, self.recovery, self.design),
        )

    def test_reduced_calibration_is_detected(self):
        self.spec["calibration_negatives_per_family"] = 20000
        self.assertIn(
            "PROTOCOL_SAMPLE_COUNTS_CHANGED",
            verify_protocol(self.spec, self.grid, self.recovery, self.design),
        )

    def test_mutated_seed_design_cannot_pass(self):
        self.design["proposed_seed_roots"]["calibration"] = 2026090501
        (self.design_dir / "PROTOCOL_DRAFT.json").write_text(
            json.dumps(self.design), encoding="utf-8"
        )
        self.assertEqual(run_preflight(self.root)["status"], "PREFLIGHT_FAILED")

    def test_symlink_is_rejected(self):
        link = self.archive / "external.py"
        try:
            link.symlink_to(self.design_dir / "PROTOCOL_DRAFT.json")
        except (OSError, NotImplementedError):
            self.skipTest("No symlink support")
        self.assertIsNone(validated_archive_path(self.root, "milestones/M38B_recovery/external.py"))


if __name__ == "__main__":
    unittest.main()
