
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m28 as m28


def test_seed_plan_unique():
    cfg = m28.Config()
    plan = m28.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_paired_scores_fixed_and_full():
    cfg = m28.Config()
    residual = np.zeros((1, 40))
    template = np.zeros((1, 40))
    residual[0, 10:31] = np.arange(1.0, 22.0)
    template[0, 10:31] = np.arange(1.0, 22.0)
    onset = np.array([10])
    endpoint = np.array([30])

    scores = m28.paired_confirmation_scores(
        residual,
        template,
        onset,
        endpoint,
        cfg,
    )

    expected_8 = np.sqrt(
        np.sum(np.arange(14.0, 22.0) ** 2)
    )
    expected_16 = np.sqrt(
        np.sum(np.arange(6.0, 22.0) ** 2)
    )
    expected_24 = np.sqrt(
        np.sum(np.arange(1.0, 22.0) ** 2)
    )
    expected_full = expected_24

    assert np.allclose(scores["8"], expected_8)
    assert np.allclose(scores["16"], expected_16)
    assert np.allclose(scores["24"], expected_24)
    assert np.allclose(scores["full"], expected_full)


def test_fixed_window_before_onset_is_harmless():
    cfg = m28.Config()
    residual = np.ones((1, 40))
    template = np.zeros((1, 40))
    template[0, 25:31] = 2.0
    onset = np.array([25])
    endpoint = np.array([30])

    scores = m28.paired_confirmation_scores(
        residual,
        template,
        onset,
        endpoint,
        cfg,
    )
    expected = 12.0 / np.sqrt(24.0)
    assert np.allclose(scores["8"], expected)
    assert np.allclose(scores["16"], expected)
    assert np.allclose(scores["24"], expected)
    assert np.allclose(scores["full"], expected)


def test_threshold_freeze_obeys_counts(tmp_path):
    cfg = m28.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(2)
    paths = {}
    for family in m28.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        arrays = {
            f"score_{label}": rng.normal(
                size=2_000
            ).astype(np.float32)
            for label in cfg.length_labels
        }
        arrays["onset"] = np.full(
            2_000,
            80,
            dtype=np.int16,
        )
        arrays["endpoint"] = np.full(
            2_000,
            100,
            dtype=np.int16,
        )
        np.savez_compressed(path, **arrays)
        paths[family] = path

    details, table = m28.freeze_thresholds(
        cfg,
        paths,
    )
    assert set(details["thresholds"]) == set(
        cfg.length_labels
    )
    assert np.all(table.alerts <= table.allowed)


def _mock_frames(
    cfg: m28.Config,
    pass_counts: dict[str, int],
    recalls: dict[str, float],
):
    summary_rows = []
    stratum_rows = []
    for label in cfg.length_labels:
        for replication in range(cfg.holdout_count):
            passed = replication < pass_counts[label]
            summary_rows.append(
                {
                    "replication": replication,
                    "length": label,
                    "recall_point": recalls[label],
                    "pass": passed,
                    "fpr_pass": True,
                    "maximum_fpr_upper_one_sided_95": 0.009,
                }
            )
            hits = int(round(recalls[label] * 2500))
            for stratum in m28.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "length": label,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )
    return (
        pd.DataFrame(summary_rows),
        pd.DataFrame(stratum_rows),
    )


def test_all_strong_fail_global_verdict():
    cfg = m28.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    summary, strata = _mock_frames(
        cfg,
        {label: 0 for label in cfg.length_labels},
        {label: 0.20 for label in cfg.length_labels},
    )
    result = m28.aggregate_results(
        cfg,
        summary,
        strata,
        thresholds={
            "8": 10.0,
            "16": 11.0,
            "24": 12.0,
            "full": 13.0,
        },
        threshold_drivers={
            label: "shared_step"
            for label in cfg.length_labels
        },
    )
    assert result["verdict"] == (
        "STRONG_FAIL_ALL_LENGTHS"
    )


def test_passing_length_becomes_candidate():
    cfg = m28.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    summary, strata = _mock_frames(
        cfg,
        {"8": 2, "16": 0, "24": 0, "full": 0},
        {"8": 0.70, "16": 0.20, "24": 0.15, "full": 0.10},
    )
    result = m28.aggregate_results(
        cfg,
        summary,
        strata,
        thresholds={
            "8": 10.0,
            "16": 11.0,
            "24": 12.0,
            "full": 13.0,
        },
        threshold_drivers={
            label: "shared_step"
            for label in cfg.length_labels
        },
    )
    assert result["verdict"] == (
        "PASS_LENGTH_CANDIDATE"
    )
    assert result["candidate_length"] == "8"
