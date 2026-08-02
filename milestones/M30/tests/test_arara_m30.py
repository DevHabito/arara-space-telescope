
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m30 as m30


def test_seed_plan_unique():
    cfg = m30.Config()
    plan = m30.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_baseline_equals_m28_length8():
    cfg = m30.Config()
    rng = np.random.default_rng(1)
    residual = rng.normal(size=(30, 180))
    template = rng.normal(size=(30, 180))
    onset = np.full(30, 80)
    endpoint = np.full(30, 110)

    observed = m30.m29.baseline_score(
        residual,
        template,
        endpoint,
        cfg,
    )
    expected = m30.m28.paired_confirmation_scores(
        residual,
        template,
        onset,
        endpoint,
        m30.m28.Config(),
    )["8"]
    assert np.allclose(observed, expected)


def test_zero_reference_equals_baseline():
    cfg = m30.Config()
    rng = np.random.default_rng(2)
    residual = rng.normal(size=(20, 180))
    template = rng.normal(size=(20, 180))
    reference = np.zeros((20, 180))
    endpoint = np.full(20, 120)

    candidate, diagnostics = (
        m30.reference_projected_score(
            residual,
            template,
            reference,
            endpoint,
            cfg,
        )
    )
    baseline = m30.m29.baseline_score(
        residual,
        template,
        endpoint,
        cfg,
    )
    assert np.allclose(candidate, baseline)
    assert np.all(
        diagnostics["reference_degenerate"]
    )
    assert np.allclose(
        diagnostics["energy_retention"],
        1.0,
    )


def test_invariant_to_reference_added_to_residual():
    cfg = m30.Config()
    rng = np.random.default_rng(3)
    n = 50
    residual = rng.normal(size=(n, 180))
    template = rng.normal(size=(n, 180))
    reference = rng.normal(size=(n, 180))
    endpoint = np.full(n, 120)

    score_1, _ = m30.reference_projected_score(
        residual,
        template,
        reference,
        endpoint,
        cfg,
    )

    modified = residual.copy()
    coefficients = rng.normal(size=n)
    modified[:, 113:121] += (
        coefficients[:, None]
        * reference[:, 113:121]
    )
    score_2, _ = m30.reference_projected_score(
        modified,
        template,
        reference,
        endpoint,
        cfg,
    )
    assert np.allclose(
        score_1,
        score_2,
        atol=1e-10,
        rtol=1e-10,
    )


def test_energy_retention_bounds():
    cfg = m30.Config()
    rng = np.random.default_rng(4)
    n = 100
    residual = rng.normal(size=(n, 180))
    template = rng.normal(size=(n, 180))
    reference = rng.normal(size=(n, 180))
    endpoint = np.full(n, 100)

    score, diagnostics = (
        m30.reference_projected_score(
            residual,
            template,
            reference,
            endpoint,
            cfg,
        )
    )
    energy = diagnostics["energy_retention"]
    assert np.all(energy >= 0.0)
    assert np.all(energy <= 1.0 + 1e-12)


def test_projection_removes_template_parallel_to_reference():
    cfg = m30.Config()
    rng = np.random.default_rng(5)
    n = 20
    residual = rng.normal(size=(n, 180))
    reference = rng.normal(size=(n, 180))
    template = np.zeros((n, 180))
    template[:, 113:121] = reference[:, 113:121]
    endpoint = np.full(n, 120)

    score, diagnostics = (
        m30.reference_projected_score(
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
    cfg = m30.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(6)
    paths = {}

    for family in m30.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_baseline8=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_reference_projected8=rng.normal(
                size=2_000
            ).astype(np.float32),
            reference_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
        )
        paths[family] = path

    details, table, diagnostics = (
        m30.freeze_thresholds(
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
        (3, len(m30.POSITIVE_STRATA), 4),
        dtype=np.int64,
    )
    counts[:, :, 0] = 500
    counts[:, :, 1] = 500
    output = m30.hierarchical_paired_bootstrap(
        counts,
        2_000,
        7,
    )
    assert np.quantile(output, 0.05) > 0.45


def test_partial_gain_verdict():
    cfg = m30.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_holdouts_with_delta=2,
        prediction_candidate_pass_low=0,
        bootstrap_replicates=1_000,
    )
    method_rows = []
    stratum_rows = []
    pair_rows = []
    diagnostic_rows = []

    for replication in range(3):
        for method, recall in (
            ("baseline8", 0.30),
            ("reference_projected8", 0.50),
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
            for stratum in m30.POSITIVE_STRATA:
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
            m30.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 1250,
                    "candidate_only": 500,
                    "baseline_only": 0,
                    "both": 750,
                    "n": 2500,
                }
            )
            diagnostic_rows.append(
                {
                    "replication": replication,
                    "population": "positive",
                    "group": stratum,
                    "n": 2500,
                    "reference_degenerate": 0,
                    "template_degenerate": 0,
                    "energy_retention_sum": 2250.0,
                    "energy_retention_median": 0.9,
                }
            )

    result = m30.aggregate_results(
        cfg,
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(pair_rows),
        pd.DataFrame(diagnostic_rows),
        thresholds={
            "baseline8": 10.0,
            "reference_projected8": 5.0,
        },
        threshold_drivers={
            "baseline8": "shared_step",
            "reference_projected8": "shared_ramp",
        },
    )
    assert result["verdict"] == (
        "PARTIAL_GAIN_NOT_OPERATIONAL"
    )
