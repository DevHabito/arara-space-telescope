from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m37 as m37


def test_full_bank_contract():
    cfg = m37.Config()
    assert len(m37.DURATIONS) == 37
    assert m37.DURATIONS[0] == 24
    assert m37.DURATIONS[-1] == 60
    assert len(cfg.endpoint_grid) == 99
    assert len(m37.DURATIONS) * len(m37.SHAPES) * len(cfg.endpoint_grid) == 14652


def test_duration_template_contains_exact_generator():
    cfg = m37.Config()
    onset = np.array([80, 95], dtype=np.int16)
    latent = np.array([0.2, 0.8])
    duration = np.array([30, 55], dtype=np.int16)
    n_time = m37.calibration_core(cfg).data_config().n_time
    for shape in m37.SHAPES:
        full = m37.build_duration_templates_for_shape(
            shape, onset, latent, n_time
        )
        exact = m37.m36.event_shape_from_latent(
            shape,
            np.arange(n_time, dtype=float)[None, :],
            onset,
            duration,
            latent,
        )
        selected = full[
            np.arange(len(onset)),
            duration - int(m37.DURATIONS[0]),
        ]
        assert np.allclose(selected, exact, atol=1e-12, rtol=1e-12)


def test_multi_duration_processing_matches_single_helper():
    cfg = m37.Config()
    rng = np.random.default_rng(1)
    n = 8
    n_time = m37.calibration_core(cfg).data_config().n_time
    raw = rng.normal(size=(n, 3, n_time))
    onset = rng.integers(80, 111, size=n, dtype=np.int16)
    estimated = rng.integers(
        70, 121, size=(n, len(cfg.endpoint_grid)), dtype=np.int16
    )
    params = {
        "target_scale": rng.uniform(0.5, 2.0, size=n),
        "residual_scale": rng.uniform(0.5, 2.0, size=n),
        "residual_phi": rng.uniform(0.0, 0.8, size=n),
    }
    multi = m37.processed_template_duration_windows(
        raw,
        onset,
        estimated,
        cfg.endpoint_grid,
        params,
        cfg,
    )
    for hypothesis in range(3):
        single = m37.m34.processed_template_grid_windows(
            raw[:, hypothesis, :],
            onset,
            estimated,
            cfg.endpoint_grid,
            params,
            cfg,
        )
        assert np.allclose(
            multi[:, hypothesis, :, :],
            single,
            atol=1e-12,
            rtol=1e-12,
        )


def test_multi_hypothesis_projection_matches_single_score():
    rng = np.random.default_rng(2)
    n, h, e, w = 10, 5, 12, 8
    residual = rng.normal(size=(n, e, w))
    template = rng.normal(size=(n, h, e, w))
    reference = rng.normal(size=(n, e, w))
    scores, diagnostics = m37.projected_scores_hypotheses(
        residual, template, reference
    )
    for hypothesis in range(h):
        single, single_diag = m37.m34.projected_window_score(
            residual,
            template[:, hypothesis],
            reference,
        )
        assert np.allclose(scores[:, hypothesis], single, atol=1e-12, rtol=1e-12)
        assert np.allclose(
            diagnostics["energy_retention"][:, hypothesis],
            single_diag["energy_retention"],
            atol=1e-12,
            rtol=1e-12,
        )


def test_full_bank_pointwise_at_least_control():
    cfg = m37.Config()
    rng = np.random.default_rng(3)
    n = 6
    data_cfg = m37.calibration_core(cfg).data_config()
    residual = rng.normal(size=(n, data_cfg.n_time))
    reference = rng.normal(size=(n, data_cfg.n_time))
    onset = rng.integers(80, 111, size=n, dtype=np.int16)
    latent = rng.uniform(size=n)
    true_shape = rng.integers(0, 4, size=n, dtype=np.int8)
    true_duration = rng.integers(24, 61, size=n, dtype=np.int16)
    params = {
        "target_scale": rng.uniform(0.5, 2.0, size=n),
        "residual_scale": rng.uniform(0.5, 2.0, size=n),
        "residual_phi": rng.uniform(0.0, 0.8, size=n),
    }
    output = m37.score_duration_shape_bank(
        residual,
        onset,
        latent,
        np.ones(n),
        true_shape,
        true_duration,
        reference,
        params,
        cfg,
    )
    assert np.all(
        output["full_score_grid"] >= output["control_score_grid"] - 1e-12
    )


def test_threshold_freeze_counts(tmp_path):
    cfg = m37.Config(calibration_negatives_per_family=2000)
    rng = np.random.default_rng(4)
    paths = {}
    for family in m37.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_rolling_four_shape_exact_duration_latency4=rng.normal(size=2000).astype(np.float32),
            score_rolling_four_shape_full_duration_bank_latency4=rng.normal(size=2000).astype(np.float32),
            control_argmax_endpoint=rng.integers(81, 180, size=2000, dtype=np.int16),
            full_argmax_endpoint=rng.integers(81, 180, size=2000, dtype=np.int16),
            full_argmax_shape_index=rng.integers(0, 4, size=2000, dtype=np.int8),
            full_argmax_duration=rng.integers(24, 61, size=2000, dtype=np.int16),
            true_shape_index=rng.integers(0, 4, size=2000, dtype=np.int8),
            true_duration=rng.integers(24, 61, size=2000, dtype=np.int16),
            control_energy_at_max=np.ones(2000, dtype=np.float32),
            full_energy_at_max=np.ones(2000, dtype=np.float32),
        )
        paths[family] = path
    details, table, diagnostics = m37.freeze_thresholds(cfg, paths)
    assert details["control_hypothesis_count"] == 396
    assert details["full_hypothesis_count"] == 14652
    assert np.all(table.alerts <= table.allowed)
    assert len(diagnostics) == 5


def _mock_frames(cfg, control_recall, full_recall, full_pass, tol_accuracy):
    method_rows, stratum_rows, identification_rows, pair_rows = [], [], [], []
    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            ("rolling_four_shape_exact_duration_latency4", control_recall, True),
            ("rolling_four_shape_full_duration_bank_latency4", full_recall, full_pass),
        ):
            method_rows.append({
                "replication": replication,
                "method": method,
                "recall_point": recall,
                "pass": passed,
                "fpr_pass": True,
                "maximum_fpr_upper_one_sided_95": 0.009,
                "auroc": 0.99,
                "average_precision": 0.99,
            })
            hits = int(round(recall * 2500))
            for stratum in m37.POSITIVE_STRATA:
                stratum_rows.append({
                    "replication": replication,
                    "method": method,
                    "stratum": stratum,
                    "hits": hits,
                    "n": 2500,
                })
        hit_n = int(round(full_recall * 20000))
        tol_correct = int(round(tol_accuracy * hit_n))
        exact_correct = int(round(0.1 * hit_n))
        identification_rows.append({
            "replication": replication,
            "primary_hit_n": hit_n,
            "duration_exact_correct": exact_correct,
            "duration_tolerance2_correct": tol_correct,
            "shape_correct": int(round(0.3 * hit_n)),
            "duration_identification_pass": tol_accuracy >= 0.72,
        })
        control_hits = int(round(control_recall * 2500))
        full_hits = int(round(full_recall * 2500))
        both = min(control_hits, full_hits)
        for index, stratum in enumerate(m37.POSITIVE_STRATA):
            pair_rows.append({
                "replication": replication,
                "stratum_index": index,
                "stratum": stratum,
                "neither": 2500 - max(control_hits, full_hits),
                "full_only": max(full_hits - control_hits, 0),
                "control_only": max(control_hits - full_hits, 0),
                "both": both,
                "n": 2500,
            })
    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(identification_rows),
        pd.DataFrame(pair_rows),
    )


def test_detection_pass_duration_unreliable_label():
    cfg = m37.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_duration_identification_holdouts=2,
        bootstrap_replicates=1000,
    )
    frames = _mock_frames(cfg, 0.76, 0.74, True, 0.30)
    result = m37.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_four_shape_exact_duration_latency4": 7.1,
            "rolling_four_shape_full_duration_bank_latency4": 7.6,
        },
        threshold_drivers={
            "rolling_four_shape_exact_duration_latency4": "shared_step",
            "rolling_four_shape_full_duration_bank_latency4": "shared_step",
        },
    )
    assert result["verdict"] == "PASS_DETECTION_DURATION_UNRELIABLE"


def test_full_identification_pass_label():
    cfg = m37.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_duration_identification_holdouts=2,
        bootstrap_replicates=1000,
    )
    frames = _mock_frames(cfg, 0.76, 0.74, True, 0.85)
    result = m37.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "rolling_four_shape_exact_duration_latency4": 7.1,
            "rolling_four_shape_full_duration_bank_latency4": 7.6,
        },
        threshold_drivers={
            "rolling_four_shape_exact_duration_latency4": "shared_step",
            "rolling_four_shape_full_duration_bank_latency4": "shared_step",
        },
    )
    assert result["verdict"] == "PASS_FULL_DURATION_BANK_AND_IDENTIFICATION"
