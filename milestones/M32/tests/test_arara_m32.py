
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m32 as m32


def test_seed_plan_unique():
    cfg = m32.Config()
    plan = m32.build_seed_plan(cfg)
    values = [
        item["integer_seed"]
        for item in plan["calibration"].values()
    ]
    for record in plan["holdouts"]:
        values.extend(record["seeds"].values())
    assert len(values) == len(set(values))


def test_split_boundaries_identical_to_m25():
    cfg = m32.Config()
    endpoint = np.array([110, 125], dtype=np.int16)
    observed = m32.m25.split_boundaries(
        endpoint,
        cfg,
    )
    expected = (
        np.array([101, 116], dtype=np.int16),
        np.array([102, 117], dtype=np.int16),
        np.array([103, 118], dtype=np.int16),
    )
    for left, right in zip(observed, expected):
        assert np.array_equal(left, right)


def test_zero_shift_reproduces_exact_template():
    cfg = m32.Config()
    rng = np.random.default_rng(1)
    raw = rng.normal(size=(10, 180))
    onset = np.full(10, 80, dtype=np.int16)
    params = {
        "target_scale": np.ones(10),
        "residual_scale": np.ones(10),
        "residual_phi": np.zeros(10),
    }
    processed = m32.process_shifted_template(
        raw,
        onset,
        onset,
        params,
    )
    assert np.array_equal(processed, raw)


def test_paired_scores_equal_when_templates_equal():
    cfg = m32.Config()
    rng = np.random.default_rng(2)
    residual = rng.normal(size=(20, 180))
    template = rng.normal(size=(20, 180))
    reference = rng.normal(size=(20, 180))
    endpoint = np.full(20, 120)

    scores, diagnostics = m32.paired_reference_scores(
        residual,
        template,
        template,
        reference,
        endpoint,
        cfg,
    )
    assert np.array_equal(
        scores["exact_reference_projected8"],
        scores["split_onset_reference_projected8"],
    )
    assert np.array_equal(
        diagnostics["exact_energy_retention"],
        diagnostics["estimated_energy_retention"],
    )


def test_threshold_freeze_obeys_counts(tmp_path):
    cfg = m32.Config(
        calibration_negatives_per_family=2_000
    )
    rng = np.random.default_rng(3)
    paths = {}
    for family in m32.NEGATIVE_FAMILIES:
        path = tmp_path / f"{family}.npz"
        np.savez_compressed(
            path,
            score_exact_reference_projected8=rng.normal(
                size=2_000
            ).astype(np.float32),
            score_split_onset_reference_projected8=rng.normal(
                size=2_000
            ).astype(np.float32),
            reference_onset=np.full(
                2_000,
                80,
                dtype=np.int16,
            ),
            estimated_onset=np.full(
                2_000,
                82,
                dtype=np.int16,
            ),
            endpoint=np.full(
                2_000,
                110,
                dtype=np.int16,
            ),
            exact_energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
            estimated_energy_retention=np.ones(
                2_000,
                dtype=np.float32,
            ),
            exact_template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            estimated_template_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
            reference_degenerate=np.zeros(
                2_000,
                dtype=np.int8,
            ),
        )
        paths[family] = path

    details, table, diagnostics = (
        m32.freeze_thresholds(
            cfg,
            paths,
        )
    )
    assert set(details["thresholds"]) == set(
        cfg.methods
    )
    assert np.all(table.alerts <= table.allowed)


def _mock_aggregate_frames(
    cfg: m32.Config,
    exact_recall: float,
    candidate_recall: float,
    candidate_pass: bool,
    onset_accuracy: float,
):
    method_rows = []
    stratum_rows = []
    onset_rows = []
    pair_rows = []

    for replication in range(cfg.holdout_count):
        for method, recall, passed in (
            (
                "exact_reference_projected8",
                exact_recall,
                True,
            ),
            (
                "split_onset_reference_projected8",
                candidate_recall,
                candidate_pass,
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
                    "auroc": 0.98,
                    "average_precision": 0.98,
                }
            )
            hits = int(round(recall * 2500))
            for stratum in m32.POSITIVE_STRATA:
                stratum_rows.append(
                    {
                        "replication": replication,
                        "method": method,
                        "stratum": stratum,
                        "hits": hits,
                        "n": 2500,
                    }
                )

        detected = int(round(candidate_recall * 20_000))
        good = int(round(onset_accuracy * detected))
        onset_rows.append(
            {
                "replication": replication,
                "detected_n": detected,
                "detected_in_envelope": good,
                "detected_accuracy": onset_accuracy,
                "onset_pass": onset_accuracy >= 0.91,
                "all_positive_n": 20_000,
                "all_positive_in_envelope": int(
                    round(onset_accuracy * 20_000)
                ),
                "detected_early_below_minus2": 0,
                "detected_late_above_plus1": detected - good,
                "all_early_below_minus2": 0,
                "all_late_above_plus1": (
                    20_000
                    - int(round(onset_accuracy * 20_000))
                ),
            }
        )

        exact_hits = int(round(exact_recall * 2500))
        candidate_hits = int(
            round(candidate_recall * 2500)
        )
        both = min(exact_hits, candidate_hits)
        for index, stratum in enumerate(
            m32.POSITIVE_STRATA
        ):
            pair_rows.append(
                {
                    "replication": replication,
                    "stratum_index": index,
                    "stratum": stratum,
                    "neither": 2500 - max(
                        exact_hits,
                        candidate_hits,
                    ),
                    "candidate_only": max(
                        candidate_hits - exact_hits,
                        0,
                    ),
                    "exact_only": max(
                        exact_hits - candidate_hits,
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


def test_detection_pass_onset_unreliable_label():
    cfg = m32.Config(
        holdout_count=3,
        minimum_holdout_passes=2,
        minimum_fpr_pass_holdouts=2,
        minimum_onset_pass_holdouts=2,
        bootstrap_replicates=1_000,
    )
    frames = _mock_aggregate_frames(
        cfg,
        exact_recall=0.80,
        candidate_recall=0.70,
        candidate_pass=True,
        onset_accuracy=0.30,
    )
    result = m32.aggregate_results(
        cfg,
        *frames,
        thresholds={
            "exact_reference_projected8": 4.0,
            "split_onset_reference_projected8": 4.5,
        },
        threshold_drivers={
            "exact_reference_projected8": "shared_step",
            "split_onset_reference_projected8": "shared_ramp",
        },
    )
    assert result["verdict"] == (
        "PASS_DETECTION_ONSET_UNRELIABLE"
    )
