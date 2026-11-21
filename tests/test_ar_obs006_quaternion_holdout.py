"""Network-free tests for preregistered AR-OBS006 chronological prediction."""

import hashlib
import json
import unittest

import numpy as np

from scripts.ar_obs006_quaternion_holdout import (
    ENGINEERING_SHA,
    FEATURES,
    MIN_SPLIT_PAIRS,
    PROTOCOL,
    RIDGE_LAMBDA,
    SHIFT_PAIRS,
    TRAIN_FRACTION,
    canonical_hash,
    holdout_metrics,
    prepare_pairs,
    ridge_fit_predict,
    verdicts,
)


def mock_products():
    """Shuffled TPF/LC rows with six distinct consecutive cadences."""
    tpf_ids = np.array([103, 100, 102, 101, 104, 105], dtype=np.int32)
    lc_ids = np.array([105, 104, 103, 102, 101, 100], dtype=np.int32)
    lc = {
        "cadences": lc_ids,
        "quality": np.zeros(6, dtype=np.int64),
        "time": np.arange(6, dtype=float) / 720 + 1400.0,
    }
    ids = np.arange(100, 106, dtype=np.int64)
    vec = {
        "cadences": ids,
        "midtime": np.linspace(1400, 1400.01, 6),
        "quat_bins": np.full(6, 60.0),
        "quat_stddev": np.ones((6, 4)) * 1e-7,
        "median_features": np.column_stack((
            ids * 1e-8, (ids ** 2) * 1e-10, np.sin(ids) * 1e-7
        )),
    }
    pixels = np.array([
        [[2.0 + i, 6.0 - 0.2 * i], [3.0, 4.0]]
        for i in range(6)
    ], dtype=float)
    aperture = np.array([[True, True], [False, False]])
    tpf_q = np.zeros(6, dtype=np.int64)
    tpf_time = np.linspace(1400, 1400.01, 6)
    return tpf_ids, tpf_q, tpf_time, pixels, aperture, lc, vec


class AROBS006Tests(unittest.TestCase):
    def test_prespecified_model_and_source_digest(self):
        self.assertEqual(PROTOCOL, "AR-OBS006-P01")
        self.assertEqual(FEATURES, ("Quat1_Med", "Quat2_Med", "Quat3_Med"))
        self.assertEqual(ENGINEERING_SHA, "2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8")
        self.assertEqual(TRAIN_FRACTION, .60)
        self.assertEqual(RIDGE_LAMBDA, 10)
        self.assertEqual(SHIFT_PAIRS, 97)

    def test_exact_cadence_pairs_not_source_row_order(self):
        x, y, counts = prepare_pairs(*mock_products())
        self.assertEqual(x.shape, (5, 3))
        self.assertEqual(y.shape, (5, 2))
        self.assertEqual(counts["eligible_consecutive_pairs"], 5)
        self.assertEqual(counts["eligible_individual_cadences"], 6)
        self.assertEqual(counts["matched_engineering_cadences"], 6)
        self.assertEqual(counts["ineligible_or_nonconsecutive_adjacent_rows"], 0)

    def test_quality_and_missing_vectors_reduce_adjacency(self):
        fixture = list(mock_products())
        fixture[1][2] = 32  # TPF cadence 102
        fixture[5]["quality"][3] = 32  # matching LC cadence 102
        x, y, counts = prepare_pairs(*fixture)
        self.assertEqual(len(x), 3)
        self.assertEqual(counts["quality_zero_rows"], 5)
        self.assertEqual(counts["ineligible_or_nonconsecutive_adjacent_rows"], 2)
        self.assertEqual(counts["exclusion_tallies_may_overlap"]["quality_nonzero"], 1)

        fixture = list(mock_products())
        for key in ("cadences", "midtime", "quat_bins", "quat_stddev", "median_features"):
            fixture[6][key] = fixture[6][key][:-1]
        x, y, counts = prepare_pairs(*fixture)
        self.assertEqual(len(x), 4)
        self.assertEqual(counts["matched_engineering_cadences"], 5)
        self.assertEqual(counts["exclusion_tallies_may_overlap"]["engineering_row_absent"], 1)

    def test_duplicate_tp_cadence_and_quality_mismatch_fail(self):
        fixture = list(mock_products())
        fixture[0][0] = fixture[0][1]
        with self.assertRaises(ValueError):
            prepare_pairs(*fixture)
        fixture = list(mock_products())
        fixture[5]["quality"][0] = 16
        with self.assertRaises(ValueError):
            prepare_pairs(*fixture)

    def test_informative_synthetic_features_predict_heldout(self):
        rng = np.random.default_rng(901)
        x = rng.normal(size=(1200, 3))
        y = np.column_stack((
            .03 * x[:, 0] - .02 * x[:, 2],
            .025 * x[:, 1] + .015 * x[:, 2],
        )) + rng.normal(scale=.005, size=(1200, 2))
        metrics = holdout_metrics(x, y)
        self.assertEqual(metrics["train_pairs"], 720)
        self.assertEqual(metrics["holdout_pairs"], 480)
        self.assertFalse(metrics["evaluable"])  # 480 is below the frozen 500-pair gate
        self.assertTrue(all(metrics["axes"][a]["R2_ridge"] > .5 for a in ("x", "y")))
        self.assertTrue(all(metrics["axes"][a]["R2_shift97"] < .05 for a in ("x", "y")))
        self.assertTrue(all(v == "NOT_EVALUABLE" for v in verdicts(metrics).values()))

    def test_positive_gates_only_when_both_splits_have_500_pairs(self):
        rng = np.random.default_rng(910)
        x = rng.normal(size=(1500, 3))
        y = np.column_stack((2 * x[:, 0] - x[:, 1], -x[:, 2])) + rng.normal(
            scale=.05, size=(1500, 2)
        )
        metrics = holdout_metrics(x, y)
        self.assertTrue(metrics["evaluable"])
        self.assertEqual(metrics["train_pairs"], 900)
        self.assertEqual(metrics["holdout_pairs"], 600)
        self.assertTrue(all(v == "SUPPORTED_IN_SELECTED_PRODUCTS"
                            for v in verdicts(metrics).values()))

    def test_no_holdout_information_enters_model_training(self):
        rng = np.random.default_rng(911)
        train_x = rng.normal(size=(900, 3))
        train_y = rng.normal(size=(900, 2))
        test_x = rng.normal(size=(600, 3))
        first, meta = ridge_fit_predict(train_x, train_y, test_x)
        altered_test_outcome = rng.normal(size=(600, 2))  # never passed to fit
        second, other = ridge_fit_predict(train_x, train_y, test_x)
        self.assertEqual(altered_test_outcome.shape, first.shape)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(meta, other)

    def test_zero_variance_feature_is_explicit(self):
        rng = np.random.default_rng(812)
        x = np.column_stack((
            rng.normal(size=700), np.zeros(700), rng.normal(size=700)
        ))
        y = rng.normal(size=(700, 2))
        pred, info = ridge_fit_predict(x[:500], y[:500], x[500:])
        self.assertEqual(info["zero_variance_training_feature_count"], 1)
        self.assertTrue(np.isfinite(pred).all())

    def test_noninformative_data_returns_negative_or_small_R2(self):
        rng = np.random.default_rng(73)
        x = rng.normal(size=(1500, 3))
        y = rng.normal(size=(1500, 2))
        m = holdout_metrics(x, y)
        self.assertTrue(all(m["axes"][a]["R2_ridge"] < .10 for a in ("x", "y")))
        self.assertTrue(all(
            verdicts(m)[k] == "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
            for k in ("H1_x_holdout_prediction", "H2_y_holdout_prediction")
        ))

    def test_canonical_digest_has_no_ambient_timestamp(self):
        self.assertEqual(
            canonical_hash({"b": 4, "a": 2}),
            hashlib.sha256(b'{"a":2,"b":4}').hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
