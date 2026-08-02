
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m34 as m34


def test_endpoint_grid_contract():
    cfg = m34.Config()
    assert cfg.endpoint_grid[0] == 81
    assert cfg.endpoint_grid[-1] == 179
    assert len(cfg.endpoint_grid) == 99


def test_grid_hinge_matches_scalar_estimator():
    cfg = m34.Config()
    rng = np.random.default_rng(1)
    residual = rng.normal(size=(12, 180))
    endpoints = np.array(
        [90, 110, 140, 179],
        dtype=np.int16,
    )

    grid_estimate, grid_score = (
        m34.estimate_onset_grid(
            residual,
            endpoints,
            cfg,
        )
    )

    for column, endpoint in enumerate(endpoints):
        repeated = np.full(
            len(residual),
            endpoint,
            dtype=np.int16,
        )
        scalar_estimate, scalar_score = (
            m34.m32.estimate_onset_split(
                residual,
                repeated,
                cfg,
            )
        )
        assert np.array_equal(
            grid_estimate[:, column],
            scalar_estimate,
        )
        assert np.allclose(
            grid_score[:, column],
            scalar_score,
            equal_nan=True,
        )


def test_local_template_grid_matches_full_processing():
    cfg = m34.Config()
    rng = np.random.default_rng(2)
    n = 10
    raw = rng.normal(size=(n, 180))
    reference_onset = rng.integers(
        80,
        111,
        size=n,
        dtype=np.int16,
    )
    endpoints = np.array(
        [100, 130, 170],
        dtype=np.int16,
    )
    estimated = rng.integers(
        70,
        121,
        size=(n, len(endpoints)),
        dtype=np.int16,
    )
    params = {
        "target_scale": rng.uniform(
            0.5,
            2.0,
            size=n,
        ),
        "residual_scale": rng.uniform(
            0.5,
            2.0,
            size=n,
        ),
        "residual_phi": rng.uniform(
            0.0,
            0.8,
            size=n,
        ),
    }

    observed = (
        m34.processed_template_grid_windows(
            raw,
            reference_onset,
            estimated,
            endpoints,
            params,
            cfg,
        )
    )

    for endpoint_index, endpoint in enumerate(
        endpoints
    ):
        offsets = (
            estimated[:, endpoint_index]
            - reference_onset
        )
        shifted = m34.m32.m24.shift_rows(
            raw,
            offsets,
        )
        full = m34.m32.m22.apply_signal_operator(
            shifted,
            params,
        )
        expected = m34.variable_endpoint_windows(
            full,
            np.full(
                n,
                endpoint,
                dtype=np.int16,
            ),
            cfg.window_length,
        )
        assert np.allclose(
            observed[:, endpoint_index, :],
            expected,
            atol=1e-12,
            rtol=1e-12,
        )


def test_projected_window_matches_m30_full_score():
    cfg = m34.Config()
    rng = np.random.default_rng(3)
    n = 20
    residual = rng.normal(size=(n, 180))
    template = rng.normal(size=(n, 180))
    reference = rng.normal(size=(n, 180))
    endpoints = rng.integers(
        90,
        170,
        size=n,
        dtype=np.int16,
    )

    local_score, local_diag = (
        m34.projected_window_score(
            m34.variable_endpoint_windows(
                residual,
                endpoints,
                cfg.window_length,
            ),
            m34.variable_endpoint_windows(
                template,
                endpoints,
                cfg.window_length,
            ),
            m34.variable_endpoint_windows(
                reference,
                endpoints,
                cfg.window_length,
            ),
        )
    )
    full_score, full_diag = (
        m34.m32.m30.reference_projected_score(
            residual,
            template,
            reference,
            endpoints,
            cfg,
        )
    )
    assert np.allclose(local_score, full_score)
    assert np.allclose(
        local_diag["energy_retention"],
        full_diag["energy_retention"],
    )


def test_first_crossing_definition():
    cfg = m34.Config()
    score = np.zeros((3, len(cfg.endpoint_grid)))
    score[0, 10] = 5.0
    score[0, 20] = 8.0
    score[1, 0] = 7.0
    threshold = 4.0

    crossing = score >= threshold
    any_crossing = crossing.any(axis=1)
    first_index = crossing.argmax(axis=1)
    first_endpoint = np.where(
        any_crossing,
        cfg.endpoint_grid[first_index],
        -1,
    )
    assert first_endpoint[0] == cfg.endpoint_grid[10]
    assert first_endpoint[1] == cfg.endpoint_grid[0]
    assert first_endpoint[2] == -1


def test_threshold_freeze_controls_curve_level_counts(
    tmp_path,
):
    cfg = m34.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(4)
    paths = {}

    for family in m34.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_hinge_exact_t50=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_rolling_hinge_first_crossing=rng.normal(
                size=2_000
            ).astype(np.float32),
            rolling_argmax_endpoint=rng.integers(
                81,
                180,
                size=2_000,
                dtype=np.int16,
            ),
            rolling_argmax_onset=rng.integers(
                70,
                121,
                size=2_000,
                dtype=np.int16,
            ),
            exact_energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
            rolling_energy_at_max=np.ones(
                2_000,
                dtype=np.float32,
            ),
        )
        paths[family] = path

    details, table, diagnostics = (
        m34.freeze_thresholds(
            cfg,
            paths,
        )
    )
    assert set(details["thresholds"]) == set(
        cfg.methods
    )
    assert np.all(table.alerts <= table.allowed)
    assert details["rolling_endpoint_count"] == 99


def _mock_frames(
    cfg: m34.Config,
    exact_recall: float,
    rolling_recall: float,
    rolling_pass: bool,
):
    method_rows = []
    stratum_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            (
                "hinge_exact_t50",
                exact_recall,
                True,
            ),
            (
                "rolling_hinge_first_crossing",
                rolling_recall,
                rolling_pass,
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
                    "auroc": 0.95,
                    "average_precision": 0.95,
                }
            )
            hits = int(round(recall * 2500))
            for stratum in m34.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        exact_hits = int(round(exact_recall * 2500))
        rolling_hits = int(
            round(rolling_recall * 2500)
        )
        both = min(exact_hits, rolling_hits)
        for index, stratum in enumerate(
            m34.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2500 - max(
                        exact_hits,
                        rolling_hits,
                    ),
                    "rolling_only": max(
                        rolling_hits - exact_hits,
                        0,
                    ),
                    "exact_only": max(
                        exact_hits - rolling_hits,
                        0,
                    ),
                    "both": both,
                    "n": 2500,
                }
            )

    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(pair_rows),
    )


def test_strong_fail_verdict():
    cfg = m34.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.77,
        rolling_recall=0.40,
        rolling_pass=False,
    )
    result = m34.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "hinge_exact_t50": 4.0,
            "rolling_hinge_first_crossing": 7.0,
        },
        threshold_drivers={
            "hinge_exact_t50": "shared_step",
            "rolling_hinge_first_crossing": "shared_step",
        },
    )
    assert result["verdict"] == (
        "STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT"
    )


def test_pass_verdict():
    cfg = m34.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.77,
        rolling_recall=0.68,
        rolling_pass=True,
    )
    result = m34.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "hinge_exact_t50": 4.0,
            "rolling_hinge_first_crossing": 7.0,
        },
        threshold_drivers={
            "hinge_exact_t50": "shared_step",
            "rolling_hinge_first_crossing": "shared_step",
        },
    )
    assert result["verdict"] == (
        "PASS_ROLLING_CAUSAL_ENDPOINT_CANDIDATE"
    )
