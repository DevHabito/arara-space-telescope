
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m23 as m23


def test_seed_plan_is_unique():
    cfg = m23.Config()
    plan = m23.build_seed_plan(cfg)
    calibration = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    holdout_values = []
    for record in plan["holdouts"]:
        holdout_values.extend(
            record["seeds"].values()
        )
    values = calibration + holdout_values
    assert len(values) == len(set(values))


def test_analysis_configuration_is_frozen():
    cfg = m23.Config()
    analysis = cfg.analysis_config()
    assert analysis.fixed_snr == 13.75
    assert analysis.target_fraction == 0.50
    assert analysis.onset_offsets == (0, 1, 2)
    assert analysis.holdout_batches == 20


def test_legacy_endpoint_field_contains_t50():
    cfg = m23.Config()
    analysis = cfg.analysis_config()
    seed_record = m23.build_seed_plan(cfg)[
        "holdouts"
    ][0]
    core = analysis.core_config(seed_record)
    panel = m23.m22.m9.generate_positive_panel(
        "linear",
        "clean",
        20,
        np.random.default_rng(1),
        core,
    )
    expected = m23.m22.m9.time_at_fraction(
        panel.shape_values, 0.50
    )
    assert np.array_equal(panel.t100, expected)


def test_threshold_freeze_obeys_counts(tmp_path):
    cfg = m23.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(4)
    paths = {}
    for family in m23.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        arrays = {
            f"offset_{offset}": rng.normal(
                size=2_000
            ).astype(np.float32)
            for offset in cfg.onset_offsets
        }
        np.savez_compressed(path, **arrays)
        paths[family] = path

    details, table = m23.freeze_thresholds(
        cfg, paths
    )
    assert set(details["thresholds"]) == {
        "0", "1", "2"
    }
    assert np.all(table.alerts <= table.allowed)


def _mock_frames(
    cfg: m23.Config,
    verdict_pattern: dict[int, int],
):
    holdout_rows = []
    stratum_rows = []
    for offset in cfg.onset_offsets:
        pass_count = verdict_pattern[offset]
        for holdout in range(cfg.holdout_count):
            passed = holdout < pass_count
            holdout_rows.append(
                {
                    "replication": holdout,
                    "offset": offset,
                    "recall_point": (
                        0.66 if passed else 0.61
                    ),
                    "fpr_pass": True,
                    "maximum_fpr_upper_95": 0.009,
                    "pass": passed,
                }
            )
            for stratum in m23.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": holdout,
                        "offset": offset,
                        "stratum": stratum,
                        "hits": (
                            1650 if passed else 1525
                        ),
                        "n": 2500,
                    }
                )
    return (
        pd.DataFrame(holdout_rows),
        pd.DataFrame(stratum_rows),
    )


def test_plus1_global_verdict():
    cfg = m23.Config(
        bootstrap_replicates=1_000
    )
    holdouts, strata = _mock_frames(
        cfg, {0: 8, 1: 8, 2: 5}
    )
    result = m23.aggregate_results(
        cfg, holdouts, strata
    )
    assert result["verdict"] == (
        "PASS_LATE_ONSET_PLUS1"
    )


def test_plus2_global_verdict():
    cfg = m23.Config(
        bootstrap_replicates=1_000
    )
    holdouts, strata = _mock_frames(
        cfg, {0: 8, 1: 8, 2: 8}
    )
    result = m23.aggregate_results(
        cfg, holdouts, strata
    )
    assert result["verdict"] == (
        "PASS_LATE_ONSET_PLUS2"
    )
