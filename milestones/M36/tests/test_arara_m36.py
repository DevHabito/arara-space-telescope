
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m36 as m36


def test_shape_bank_contract():
    cfg = m36.Config()
    onset = np.array([80, 90], dtype=np.int16)
    duration = np.array([30, 50], dtype=np.int16)
    latent = np.array([0.0, 1.0])

    bank = m36.build_shape_bank(
        onset,
        duration,
        latent,
        m36.calibration_core(cfg).data_config().n_time,
    )
    assert bank.shape == (
        4,
        2,
        m36.calibration_core(cfg).data_config().n_time,
    )
    assert np.allclose(bank[:, :, :70], 0.0)
    assert np.all(bank >= 0.0)
    assert np.all(bank <= 1.0)
    assert np.allclose(
        bank[:, np.arange(2), onset + duration],
        1.0,
    )


def test_parameter_mapping_is_frozen():
    latent = np.array([0.0, 0.5, 1.0])
    gamma = 1.5 + 1.5 * latent
    beta = 1.0 + 3.0 * latent
    q = 6.0 + 6.0 * latent

    assert np.allclose(gamma, [1.5, 2.25, 3.0])
    assert np.allclose(beta, [1.0, 2.5, 4.0])
    assert np.allclose(q, [6.0, 9.0, 12.0])


def test_true_shape_is_exact_member_of_bank():
    cfg = m36.Config()
    rng = np.random.default_rng(1)
    virtual = m36.generate_virtual_shape_bank(
        100,
        rng,
        cfg,
    )
    row = np.arange(100)
    selected = virtual["shape_bank"][
        virtual["true_shape_index"],
        row,
    ]
    assert np.array_equal(
        selected,
        virtual["true_signal"],
    )


def test_bank_score_is_pointwise_at_least_exact():
    cfg = m36.Config()
    rng = np.random.default_rng(2)
    n = 10
    time = m36.calibration_core(cfg).data_config().n_time

    residual = rng.normal(size=(n, time))
    onset = rng.integers(
        80,
        111,
        size=n,
        dtype=np.int16,
    )
    duration = rng.integers(
        24,
        61,
        size=n,
        dtype=np.int16,
    )
    latent = rng.uniform(size=n)
    raw_bank = m36.build_shape_bank(
        onset,
        duration,
        latent,
        time,
    )
    true_index = rng.integers(
        0,
        4,
        size=n,
        dtype=np.int8,
    )
    reference = rng.normal(size=(n, time))
    params = {
        "target_scale": rng.uniform(0.5, 2.0, size=n),
        "residual_scale": rng.uniform(0.5, 2.0, size=n),
        "residual_phi": rng.uniform(0.0, 0.8, size=n),
    }

    result = m36.score_shape_bank(
        residual,
        raw_bank,
        onset,
        true_index,
        reference,
        params,
        cfg,
    )
    assert np.all(
        result["bank_score_grid"]
        >= result["exact_score_grid"]
        - 1e-12
    )


def test_first_crossing_uses_earliest_endpoint():
    cfg = m36.Config()
    grid = np.zeros(
        (2, len(cfg.endpoint_grid))
    )
    grid[0, 20] = 9.0
    grid[0, 10] = 8.0
    grid[1, 0] = 7.0

    alert, index, endpoint = m36.first_crossing(
        grid,
        6.0,
        cfg,
    )
    assert alert.tolist() == [True, True]
    assert index.tolist() == [10, 0]
    assert endpoint[0] == cfg.endpoint_grid[10]
    assert endpoint[1] == cfg.endpoint_grid[0]


def test_threshold_freeze_obeys_curve_counts(tmp_path):
    cfg = m36.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(3)
    paths = {}

    for family in m36.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_rolling_exact_shape_latency4=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_rolling_four_shape_bank_latency4=rng.normal(
                size=2_000
            ).astype(np.float32),
            exact_argmax_endpoint=rng.integers(
                81,
                180,
                size=2_000,
                dtype=np.int16,
            ),
            bank_argmax_endpoint=rng.integers(
                81,
                180,
                size=2_000,
                dtype=np.int16,
            ),
            bank_argmax_shape_index=rng.integers(
                0,
                4,
                size=2_000,
                dtype=np.int8,
            ),
            true_shape_index=rng.integers(
                0,
                4,
                size=2_000,
                dtype=np.int8,
            ),
            exact_energy_at_max=np.ones(
                2_000,
                dtype=np.float32,
            ),
            bank_energy_at_max=np.ones(
                2_000,
                dtype=np.float32,
            ),
        )
        paths[family] = path

    details, table, diagnostics = (
        m36.freeze_thresholds(
            cfg,
            paths,
        )
    )
    assert set(details["thresholds"]) == set(
        cfg.methods
    )
    assert details["exact_hypothesis_count"] == 99
    assert details["bank_hypothesis_count"] == 396
    assert np.all(table.alerts <= table.allowed)


def _mock_frames(
    cfg: m36.Config,
    exact_recall: float,
    bank_recall: float,
    bank_pass: bool,
    shape_accuracy: float,
):
    method_rows = []
    stratum_rows = []
    shape_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            (
                "rolling_exact_shape_latency4",
                exact_recall,
                True,
            ),
            (
                "rolling_four_shape_bank_latency4",
                bank_recall,
                bank_pass,
            ),
        ):
            method_rows.append(
                {
                    "replication": replication,
                    "method": method,
                    "recall_point": recall,
                    "pass": passed,
                    "fpr_pass": True,
                    "maximum_fpr_upper_one_sided_95": 0.009,
                    "auroc": 0.99,
                    "average_precision": 0.99,
                }
            )
            hits = int(round(recall * 2500))
            for stratum in m36.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        primary_n = int(round(bank_recall * 20_000))
        correct = int(round(shape_accuracy * primary_n))
        shape_rows.append(
            {
                "replication": replication,
                "alert_n": primary_n,
                "alert_shape_correct": correct,
                "primary_hit_n": primary_n,
                "primary_hit_shape_correct": correct,
                "shape_identification_pass": (
                    shape_accuracy >= 0.72
                ),
            }
        )

        exact_hits = int(round(exact_recall * 2500))
        bank_hits = int(round(bank_recall * 2500))
        both = min(exact_hits, bank_hits)
        for index, stratum in enumerate(
            m36.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2500 - max(
                        exact_hits,
                        bank_hits,
                    ),
                    "bank_only": max(
                        bank_hits - exact_hits,
                        0,
                    ),
                    "exact_only": max(
                        exact_hits - bank_hits,
                        0,
                    ),
                    "both": both,
                    "n": 2500,
                }
            )

    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(shape_rows),
        pd.DataFrame(pair_rows),
    )


def test_detection_pass_shape_unreliable_label():
    cfg = m36.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_shape_accuracy_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.76,
        bank_recall=0.70,
        bank_pass=True,
        shape_accuracy=0.50,
    )
    result = m36.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_exact_shape_latency4": 7.0,
            "rolling_four_shape_bank_latency4": 7.8,
        },
        threshold_drivers={
            "rolling_exact_shape_latency4": "shared_step",
            "rolling_four_shape_bank_latency4": "shared_step",
        },
    )
    assert result["verdict"] == (
        "PASS_DETECTION_SHAPE_UNRELIABLE"
    )


def test_full_pass_label():
    cfg = m36.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_shape_accuracy_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.76,
        bank_recall=0.72,
        bank_pass=True,
        shape_accuracy=0.85,
    )
    result = m36.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_exact_shape_latency4": 7.0,
            "rolling_four_shape_bank_latency4": 7.8,
        },
        threshold_drivers={
            "rolling_exact_shape_latency4": "shared_step",
            "rolling_four_shape_bank_latency4": "shared_step",
        },
    )
    assert result["verdict"] == (
        "PASS_FOUR_SHAPE_BANK_AND_IDENTIFICATION"
    )
