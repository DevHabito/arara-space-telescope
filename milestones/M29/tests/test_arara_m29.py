
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m29 as m29


def test_seed_plan_unique():
    cfg = m29.Config()
    plan = m29.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_sbw_residual_and_signal_match_frozen_m5():
    cfg = m29.Config()
    analysis = cfg.analysis_config()
    seed_record = m29.build_seed_plan(cfg)[
        "holdouts"
    ][0]
    core = analysis.core_config(seed_record)
    panel = m29.m22.m9.generate_positive_panel(
        "linear",
        "clean",
        30,
        np.random.default_rng(1),
        core,
    )
    raw_signal = (
        cfg.fixed_snr
        * panel.stationary_target_sd[:, None]
        * panel.shape_values
    )
    observed = panel.base_y.copy()
    observed[:, 0, :] += raw_signal

    expected_residual, expected_signal, _ = (
        m29.m22.m5.sbw_with_signal_operator(
            observed,
            raw_signal,
            core.data_config(),
        )
    )
    residual, signal, reference, params = (
        m29.sbw_with_reference_nuisance(
            observed,
            raw_signal,
            core.data_config(),
        )
    )
    assert np.allclose(
        residual,
        expected_residual,
    )
    assert np.allclose(
        signal,
        expected_signal,
    )
    assert reference.shape == residual.shape


def test_baseline_equals_m28_length8():
    cfg = m29.Config()
    rng = np.random.default_rng(2)
    residual = rng.normal(size=(20, 180))
    template = rng.normal(size=(20, 180))
    onset = np.full(20, 80)
    endpoint = np.full(20, 110)

    observed = m29.baseline_score(
        residual,
        template,
        endpoint,
        cfg,
    )
    expected = m29.m28.paired_confirmation_scores(
        residual,
        template,
        onset,
        endpoint,
        m29.m28.Config(),
    )["8"]
    assert np.allclose(observed, expected)


def test_projection_invariant_to_nuisance_added_to_residual():
    cfg = m29.Config()
    rng = np.random.default_rng(3)
    n = 40
    endpoint = np.full(n, 120)
    residual = rng.normal(size=(n, 180))
    template = rng.normal(size=(n, 180))
    reference = rng.normal(size=(n, 180))

    score_1, diagnostics = (
        m29.projected_partial_t_score(
            residual,
            template,
            reference,
            endpoint,
            cfg,
        )
    )

    window_indices = np.arange(113, 121)
    ramp = np.linspace(-1.0, 1.0, 8)
    modified = residual.copy()
    coefficients = rng.normal(size=(n, 3))
    modified[:, window_indices] += (
        coefficients[:, 0, None]
        + coefficients[:, 1, None] * ramp
        + coefficients[:, 2, None]
        * reference[:, window_indices]
    )

    score_2, _ = m29.projected_partial_t_score(
        modified,
        template,
        reference,
        endpoint,
        cfg,
    )
    assert np.allclose(
        score_1,
        score_2,
        atol=1e-9,
        rtol=1e-9,
    )


def test_projection_removes_pure_nuisance_template():
    cfg = m29.Config()
    n = 10
    endpoint = np.full(n, 120)
    residual = np.zeros((n, 180))
    template = np.zeros((n, 180))
    reference = np.zeros((n, 180))
    ramp = np.linspace(-1.0, 1.0, 8)
    template[:, 113:121] = (
        2.0
        + 3.0 * ramp[None, :]
    )
    score, diagnostics = (
        m29.projected_partial_t_score(
            residual,
            template,
            reference,
            endpoint,
            cfg,
        )
    )
    assert np.all(score == 0.0)
    assert np.all(
        diagnostics["template_degenerate"]
    )


def test_threshold_freeze_obeys_counts(tmp_path):
    cfg = m29.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(4)
    paths = {}
    for family in m29.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_baseline8=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_projected_t8=rng.normal(
                size=2_000
            ).astype(np.float32),
            rank=np.full(
                2_000,
                3,
                dtype=np.int16,
            ),
            template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            residual_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
        )
        paths[family] = path

    details, table, diagnostics = (
        m29.freeze_thresholds(
            cfg,
            paths,
        )
    )
    assert set(details["thresholds"]) == set(
        cfg.methods
    )
    assert np.all(
        table.alerts <= table.allowed
    )


def test_hierarchical_paired_bootstrap_positive_delta():
    counts = np.zeros(
        (3, len(m29.POSITIVE_STRATA), 4),
        dtype=np.int64,
    )
    counts[:, :, 0] = 500
    counts[:, :, 1] = 500
    output = m29.hierarchical_paired_bootstrap(
        counts,
        2_000,
        5,
    )
    assert np.quantile(output, 0.05) > 0.45


def test_partial_gain_verdict():
    cfg = m29.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_holdouts_with_delta=2,
        bootstrap_replicates=1_000,
    )
    method_rows = []
    stratum_rows = []
    pair_rows = []

    for replication in range(3):
        for method, recall in (
            ("baseline8", 0.30),
            ("projected_t8", 0.50),
        ):
            method_rows.append(
                {
                    "replication": replication,
                    "method": method,
                    "recall_point": recall,
                    "pass": False,
                    "fpr_pass": True,
                    "maximum_fpr_upper_one_sided_95": 0.009,
                    "auroc": 0.9,
                    "average_precision": 0.9,
                }
            )
            hits = int(round(recall * 2500))
            for stratum in m29.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        for index, stratum in enumerate(
            m29.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 1250,
                    "projected_only": 500,
                    "baseline_only": 0,
                    "both": 750,
                    "n": 2500,
                }
            )

    result = m29.aggregate_results(
        cfg,
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(pair_rows),
        thresholds={
            "baseline8": 10.0,
            "projected_t8": 5.0,
        },
        threshold_drivers={
            "baseline8": "shared_step",
            "projected_t8": "shared_bump",
        },
    )
    assert result["verdict"] == (
        "PARTIAL_GAIN_NOT_OPERATIONAL"
    )
