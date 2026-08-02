
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m31 as m31


def test_replication_config_changes_only_identity_and_seeds():
    cfg = m31.Config()
    parent = m31.m30.Config()

    assert cfg.version == "31.0"
    assert cfg.calibration_seed != parent.calibration_seed
    assert cfg.holdout_root_seed != parent.holdout_root_seed
    assert cfg.window_length == parent.window_length
    assert cfg.methods == parent.methods
    assert (
        cfg.minimum_global_recall_lower_one_sided_95
        == parent.minimum_global_recall_lower_one_sided_95
    )
    assert (
        cfg.minimum_paired_delta_lower_one_sided_95
        == parent.minimum_paired_delta_lower_one_sided_95
    )


def test_seed_plan_unique():
    cfg = m31.Config()
    plan = m31.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_candidate_equation_identical_to_m30():
    cfg = m31.Config()
    rng = np.random.default_rng(31)
    residual = rng.normal(size=(40, 180))
    template = rng.normal(size=(40, 180))
    reference = rng.normal(size=(40, 180))
    endpoint = np.full(40, 120)

    observed, observed_diag = (
        m31.reference_projected_score(
            residual,
            template,
            reference,
            endpoint,
            cfg,
        )
    )
    expected, expected_diag = (
        m31.m30.reference_projected_score(
            residual,
            template,
            reference,
            endpoint,
            m31.m30.Config(),
        )
    )

    assert np.array_equal(observed, expected)
    for key in expected_diag:
        assert np.array_equal(
            observed_diag[key],
            expected_diag[key],
        )


def test_baseline_equation_identical_to_m30():
    cfg = m31.Config()
    rng = np.random.default_rng(32)
    residual = rng.normal(size=(20, 180))
    template = rng.normal(size=(20, 180))
    endpoint = np.full(20, 115)

    observed = m31.m30.m29.baseline_score(
        residual,
        template,
        endpoint,
        cfg,
    )
    expected = m31.m30.m29.baseline_score(
        residual,
        template,
        endpoint,
        m31.m30.Config(),
    )
    assert np.array_equal(observed, expected)


def test_confirmation_label_on_replication_pass():
    cfg = m31.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_holdouts_with_delta=2,
        prediction_candidate_pass_low=2,
        prediction_candidate_pass_high=3,
        bootstrap_replicates=1_000,
    )

    method_rows = []
    stratum_rows = []
    pair_rows = []
    diagnostic_rows = []

    for replication in range(3):
        for method, recall, passed in (
            ("baseline8", 0.30, False),
            ("reference_projected8", 0.80, True),
        ):
            method_rows.append(
                {
                    "replication": replication,
                    "method": method,
                    "recall_point": recall,
                    "pass": passed,
                    "fpr_pass": True,
                    "maximum_fpr_upper_one_sided_95": 0.009,
                    "auroc": 0.98,
                    "average_precision": 0.98,
                }
            )
            hits = int(round(recall * 2500))
            for stratum in m31.POSITIVE_STRATA:
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
            m31.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 500,
                    "candidate_only": 1250,
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
                    "energy_retention_sum": 1250.0,
                    "energy_retention_median": 0.5,
                }
            )

    result = m31.aggregate_results(
        cfg,
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(pair_rows),
        pd.DataFrame(diagnostic_rows),
        thresholds={
            "baseline8": 16.0,
            "reference_projected8": 4.0,
        },
        threshold_drivers={
            "baseline8": "shared_step",
            "reference_projected8": "shared_step",
        },
    )

    assert result["verdict"] == (
        "CONFIRMED_REFERENCE_PROJECTION"
    )
    assert result["discovery_rule_verdict"] == (
        "PASS_REFERENCE_PROJECTION_CANDIDATE"
    )
