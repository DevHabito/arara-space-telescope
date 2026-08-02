
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m33 as m33


def test_seed_plan_unique():
    cfg = m33.Config()
    plan = m33.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    values.extend(
        item["integer_seed"]
        for item in plan[
            "calibration_permutation"
        ].values()
    )
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
        values.append(record["permutation_seed"])
    assert len(values) == len(set(values))


def test_derangement_has_no_fixed_points():
    rng = np.random.default_rng(1)
    permutation = m33.random_derangement(125, rng)
    assert np.all(
        permutation != np.arange(125)
    )
    assert np.array_equal(
        np.sort(permutation),
        np.arange(125),
    )


def test_permutation_preserves_multiset():
    rng = np.random.default_rng(2)
    onset = rng.integers(70, 121, size=125)
    permutation = m33.random_derangement(
        len(onset),
        rng,
    )
    permuted = onset[permutation]
    assert np.array_equal(
        np.sort(onset),
        np.sort(permuted),
    )


def test_three_scores_equal_when_templates_equal():
    cfg = m33.Config()
    rng = np.random.default_rng(3)
    residual = rng.normal(size=(20, 180))
    template = rng.normal(size=(20, 180))
    reference = rng.normal(size=(20, 180))
    endpoint = np.full(20, 120)

    scores, diagnostics = m33.three_reference_scores(
        residual,
        template,
        template,
        template,
        reference,
        endpoint,
        cfg,
    )
    exact = scores[
        "exact_reference_projected8"
    ]
    hinge = scores[
        "hinge_reference_projected8"
    ]
    permuted = scores[
        "permuted_hinge_reference_projected8"
    ]
    assert np.array_equal(exact, hinge)
    assert np.array_equal(hinge, permuted)


def test_threshold_freeze_obeys_counts(tmp_path):
    cfg = m33.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(4)
    paths = {}
    for family in m33.NEGATIVE_FAMILIES:
        permutation = m33.random_derangement(
            2_000,
            rng,
        )
        hinge_onset = rng.integers(
            70,
            121,
            size=2_000,
            dtype=np.int16,
        )
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_exact_reference_projected8=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_hinge_reference_projected8=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_permuted_hinge_reference_projected8=rng.normal(
                size=2_000
            ).astype(np.float32),
            reference_onset=np.full(
                2_000,
                80,
                dtype=np.int16,
            ),
            hinge_onset=hinge_onset,
            permuted_onset=hinge_onset[permutation],
            endpoint=np.full(
                2_000,
                110,
                dtype=np.int16,
            ),
            exact_energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
            hinge_energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
            permuted_energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
            exact_template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            hinge_template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            permuted_template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            reference_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            permutation=permutation.astype(np.int16),
        )
        paths[family] = path

    details, table, diagnostics = (
        m33.freeze_thresholds(
            cfg,
            paths,
        )
    )
    assert set(details["thresholds"]) == set(
        cfg.methods
    )
    assert np.all(table.alerts <= table.allowed)
    assert diagnostics.same_onset_multiset.all()


def _mock_frames(
    cfg: m33.Config,
    exact_recall: float,
    hinge_recall: float,
    permuted_recall: float,
):
    method_rows = []
    stratum_rows = []
    onset_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall in (
            (
                "exact_reference_projected8",
                exact_recall,
            ),
            (
                "hinge_reference_projected8",
                hinge_recall,
            ),
            (
                "permuted_hinge_reference_projected8",
                permuted_recall,
            ),
        ):
            method_rows.append(
                {
                    "replication": replication,
                    "method": method,
                    "recall_point": recall,
                    "pass": True,
                    "fpr_pass": True,
                    "maximum_fpr_upper_one_sided_95": 0.009,
                    "auroc": 0.98,
                    "average_precision": 0.98,
                }
            )
            hits = int(round(recall * 2500))
            for stratum in m33.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        for method, accuracy in (
            ("hinge_reference_projected8", 0.25),
            (
                "permuted_hinge_reference_projected8",
                0.20,
            ),
        ):
            alert_n = int(round(
                (
                    hinge_recall
                    if method.startswith("hinge")
                    else permuted_recall
                )
                * 20_000
            ))
            onset_rows.append(
                {
                    "replication": replication,
                    "method": method,
                    "alert_n": alert_n,
                    "alert_in_envelope": int(
                        round(accuracy * alert_n)
                    ),
                    "all_positive_n": 20_000,
                    "all_positive_in_envelope": int(
                        round(accuracy * 20_000)
                    ),
                    "alert_early_below_minus2": 0,
                    "alert_late_above_plus1": 0,
                }
            )

        hinge_hits = int(round(hinge_recall * 2500))
        permuted_hits = int(
            round(permuted_recall * 2500)
        )
        both = min(hinge_hits, permuted_hits)
        for index, stratum in enumerate(
            m33.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2500 - max(
                        hinge_hits,
                        permuted_hits,
                    ),
                    "hinge_only": max(
                        hinge_hits - permuted_hits,
                        0,
                    ),
                    "permuted_only": max(
                        permuted_hits - hinge_hits,
                        0,
                    ),
                    "both": both,
                    "n": 2500,
                }
            )

    return (
        pd.DataFrame(method_rows),
        pd.DataFrame(stratum_rows),
        pd.DataFrame(onset_rows),
        pd.DataFrame(pair_rows),
    )


def test_distribution_only_verdict():
    cfg = m33.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_holdouts_with_association_delta=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.80,
        hinge_recall=0.765,
        permuted_recall=0.760,
    )
    result = m33.aggregate_results(
        cfg,
        *frames,
        thresholds={
            method: 4.0
            for method in cfg.methods
        },
        threshold_drivers={
            method: "shared_step"
            for method in cfg.methods
        },
    )
    assert result["verdict"] == (
        "ONSET_DISTRIBUTION_ONLY"
    )


def test_curve_specific_verdict():
    cfg = m33.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_holdouts_with_association_delta=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_frames(
        cfg,
        exact_recall=0.80,
        hinge_recall=0.76,
        permuted_recall=0.70,
    )
    result = m33.aggregate_results(
        cfg,
        *frames,
        thresholds={
            method: 4.0
            for method in cfg.methods
        },
        threshold_drivers={
            method: "shared_step"
            for method in cfg.methods
        },
    )
    assert result["verdict"] == (
        "PASS_CURVE_SPECIFIC_ONSET_INFORMATION"
    )
