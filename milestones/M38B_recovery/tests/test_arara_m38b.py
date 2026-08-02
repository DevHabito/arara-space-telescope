from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m38b as m38b


def test_frozen_latent_grid_literal():
    assert np.array_equal(
        m38b.LATENT_GRID,
        np.asarray([0.0, 0.25, 0.5, 0.75, 1.0]),
    )


def test_protocol_hypothesis_counts():
    cfg = m38b.Config()
    assert len(cfg.endpoint_grid) * len(m38b.SHAPES) * len(m38b.DURATIONS) == 14_652
    assert (
        len(cfg.endpoint_grid)
        * len(m38b.SHAPES)
        * len(m38b.DURATIONS)
        * len(m38b.LATENT_GRID)
        == 73_260
    )


def test_nearest_latent_ties_go_lower():
    values = np.asarray([0.0, 0.125, 0.25, 0.375, 0.625, 1.0])
    observed = m38b.nearest_latent_index(values)
    assert observed.tolist() == [0, 0, 1, 1, 2, 4]


def test_control_is_exact_m37r_bank():
    cfg = m38b.Config(
        calibration_block_count=1,
        calibration_negatives_per_block=8,
        calibration_negatives_per_family=8,
        calibration_batch_size=8,
    )
    core = m38b.calibration_core(cfg)
    rng = np.random.default_rng(1234)
    data_cfg = core.data_config()
    data = m38b.m2.generate_negative_family("shared_step", 8, rng, data_cfg)
    virtual = m38b.m36.generate_virtual_shape_bank(
        8, rng, cfg, data_cfg=data_cfg
    )
    residual, _, reference, params = (
        m38b.m32.m30.m29.sbw_with_reference_nuisance(
            data.y,
            virtual["true_signal"],
            data_cfg,
        )
    )
    parent = m38b.m37.score_duration_shape_bank(
        residual,
        virtual["onset"],
        virtual["latent_u"],
        np.ones(8),
        virtual["true_shape_index"],
        virtual["duration"],
        reference,
        params,
        cfg,
    )
    current = m38b.score_latent_grid_bank(
        residual,
        virtual["onset"],
        virtual["latent_u"],
        np.ones(8),
        virtual["true_shape_index"],
        virtual["duration"],
        reference,
        params,
        cfg,
    )
    assert np.array_equal(current["control_score_grid"], parent["full_score_grid"])
    assert np.array_equal(
        current["control_shape_index_grid"],
        parent["full_shape_index_grid"],
    )
    assert np.array_equal(
        current["control_duration_grid"],
        parent["full_duration_grid"],
    )


def test_candidate_contains_control_when_true_u_is_on_grid():
    cfg = m38b.Config(
        calibration_block_count=1,
        calibration_negatives_per_block=5,
        calibration_negatives_per_family=5,
        calibration_batch_size=5,
    )
    core = m38b.calibration_core(cfg)
    rng = np.random.default_rng(42)
    data_cfg = core.data_config()
    data = m38b.m2.generate_negative_family("quiet", 5, rng, data_cfg)
    virtual = m38b.m36.generate_virtual_shape_bank(
        5, rng, cfg, data_cfg=data_cfg
    )
    virtual["latent_u"][:] = m38b.LATENT_GRID
    residual, _, reference, params = (
        m38b.m32.m30.m29.sbw_with_reference_nuisance(
            data.y,
            virtual["true_signal"],
            data_cfg,
        )
    )
    output = m38b.score_latent_grid_bank(
        residual,
        virtual["onset"],
        virtual["latent_u"],
        np.ones(5),
        virtual["true_shape_index"],
        virtual["duration"],
        reference,
        params,
        cfg,
    )
    assert np.all(
        output["grid_score_grid"]
        >= output["control_score_grid"] - 1e-12
    )


def test_seed_plan_unique():
    cfg = m38b.Config()
    plan = m38b.build_seed_plan(cfg)
    seeds = [
        plan["calibration_blocks"][str(block)][family]["integer_seed"]
        for block in range(cfg.calibration_block_count)
        for family in m38b.NEGATIVE_FAMILIES
    ]
    assert len(seeds) == 20
    assert len(set(seeds)) == 20


def test_combine_blocks(tmp_path):
    paths = []
    for block in range(4):
        path = tmp_path / f"block_{block}.npz"
        np.savez_compressed(
            path,
            score=np.arange(10) + 10 * block,
            label=np.full(10, block, dtype=np.int8),
        )
        paths.append(path)
    output = m38b.combine_calibration_blocks(
        paths,
        expected_per_block=10,
        expected_total=40,
    )
    assert len(output["score"]) == 40
    assert np.array_equal(
        output["label"],
        np.repeat(np.arange(4, dtype=np.int8), 10),
    )


def _mock_frames(cfg, control_recall, grid_recall, control_pass, grid_pass, latent_accuracy):
    method_rows = []
    stratum_rows = []
    identification_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            ("rolling_full_duration_exact_latent_latency4", control_recall, control_pass),
            ("rolling_full_duration_latent_grid5_latency4", grid_recall, grid_pass),
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
            for stratum in m38b.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        hit_n = int(round(grid_recall * 20_000))
        nearest = int(round(latent_accuracy * hit_n))
        identification_rows.append(
            {
                "replication": replication,
                "primary_hit_n": hit_n,
                "nearest_cell_correct": nearest,
                "latent_within_half_spacing_correct": nearest,
                "latent_within_quarter_correct": int(round(0.7 * hit_n)),
                "duration_exact_correct": int(round(0.03 * hit_n)),
                "shape_correct": int(round(0.31 * hit_n)),
                "latent_identification_pass": latent_accuracy >= 0.72,
            }
        )

        control_hits = int(round(control_recall * 2500))
        grid_hits = int(round(grid_recall * 2500))
        both = min(control_hits, grid_hits)
        for index, stratum in enumerate(m38b.POSITIVE_STRATA):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2500 - max(control_hits, grid_hits),
                    "grid_only": max(grid_hits - control_hits, 0),
                    "control_only": max(control_hits - grid_hits, 0),
                    "both": both,
                    "n": 2500,
                }
            )

    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(identification_rows),
        pd.DataFrame(pair_rows),
    )


def test_invalid_control_label():
    cfg = m38b.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1000,
    )
    frames = _mock_frames(cfg, 0.75, 0.74, False, True, 0.3)
    result = m38b.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_full_duration_exact_latent_latency4": 7.1,
            "rolling_full_duration_latent_grid5_latency4": 7.3,
        },
        threshold_drivers={
            "rolling_full_duration_exact_latent_latency4": "shared_step",
            "rolling_full_duration_latent_grid5_latency4": "shared_step",
        },
    )
    assert result["verdict"] == "INVALID_M38B_EXACT_LATENT_CONTROL"


def test_detection_pass_latent_unreliable_label():
    cfg = m38b.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_latent_identification_holdouts=2,
        bootstrap_replicates=1000,
    )
    frames = _mock_frames(cfg, 0.755, 0.745, True, True, 0.3)
    result = m38b.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_full_duration_exact_latent_latency4": 7.1,
            "rolling_full_duration_latent_grid5_latency4": 7.3,
        },
        threshold_drivers={
            "rolling_full_duration_exact_latent_latency4": "shared_step",
            "rolling_full_duration_latent_grid5_latency4": "shared_step",
        },
    )
    assert result["verdict"] == "PASS_M38B_DETECTION_LATENT_UNRELIABLE"
