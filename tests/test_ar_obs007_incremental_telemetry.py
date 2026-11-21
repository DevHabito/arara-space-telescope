"""Network-free regression checks for the AR-OBS007 frozen incremental benchmark."""

import hashlib
import unittest

import numpy as np

from scripts.ar_obs007_incremental_telemetry import (
    EMBARGO_PER_SIDE,
    FRACTION_TRAIN,
    LAMBDA,
    MIN_BLOCK,
    METHODS,
    PROTOCOL,
    SHIFT_CONTROL,
    build_lagged_examples,
    digest,
    evaluate_examples,
    fit_ridge,
    verdicts,
)


def little_observation():
    ids = np.arange(100, 112)
    rng = np.random.default_rng(777)
    p = rng.permutation(len(ids))
    tp_ids = ids[p]
    tp_quality = np.zeros(len(ids), dtype=np.int64)
    tp_time = np.arange(len(ids), dtype=float)[p] + 1500
    pixel_cube = np.array([
        [[3.0 + i / 20, 2.0 + i / 14], [8.0, 5.0]]
        for i in range(len(ids))
    ])[p]
    selected = np.array([[True, True], [False, False]])
    lc = {
        "cadences": ids[::-1], "quality": np.zeros(len(ids), dtype=np.int64),
        "time": 1500 + np.arange(len(ids), dtype=float)[::-1],
        "rows": len(ids),
    }
    v = {
        "cadences": ids[::-1], "midtime": 1500 + np.arange(len(ids), dtype=float)[::-1],
        "quat_bins": np.full(len(ids), 60.0),
        "quat_stddev": np.full((len(ids), 4), 1.e-6),
        "median_features": np.column_stack((
            1e-7 * ids[::-1] ** 2,
            1e-7 * np.sin(ids[::-1]),
            1e-7 * np.cos(ids[::-1]),
        )),
    }
    return (tp_ids, tp_quality, tp_time, pixel_cube, selected, lc, v)


def generated_examples(n=3000, with_quaternion=True, seed=20261121):
    rng = np.random.default_rng(seed)
    ar = rng.normal(size=(n, 4))
    q = rng.normal(size=(n, 3))
    y = np.column_stack((1.1 * ar[:, 0] - .8 * ar[:, 2],
                         -.9 * ar[:, 1] + 1.4 * ar[:, 3]))
    if with_quaternion:
        y += np.column_stack((.8 * q[:, 0] + .6 * q[:, 2],
                              -.9 * q[:, 1] + .3 * q[:, 2]))
    y += rng.normal(scale=.15, size=(n, 2))
    return {"ar": ar, "q": q, "y": y,
            "end_cadences": np.arange(n) + 10000}


class IncrementalTelemetryTests(unittest.TestCase):
    def test_frozen_method_and_split_constants(self):
        self.assertEqual(PROTOCOL, "AR-OBS007-P01")
        self.assertEqual(FRACTION_TRAIN, .60)
        self.assertEqual(LAMBDA, 10)
        self.assertEqual(EMBARGO_PER_SIDE, 120)
        self.assertEqual(SHIFT_CONTROL, 97)
        self.assertEqual(MIN_BLOCK, 500)
        self.assertEqual(len(METHODS), 5)

    def test_join_and_motion_lags_follow_cadence_not_row_order(self):
        examples = build_lagged_examples(*little_observation())
        self.assertEqual(examples["counts"]["original_cadences"], 12)
        self.assertEqual(examples["counts"]["usable_consecutive_pairs"], 11)
        self.assertEqual(examples["counts"]["eligible_lagged_examples"], 9)
        np.testing.assert_array_equal(examples["end_cadences"], np.arange(103,112))
        self.assertEqual(examples["ar"].shape, (9, 4))
        self.assertEqual(examples["q"].shape, (9, 3))

    def test_quality_mismatch_is_not_silently_ignored(self):
        test = list(little_observation())
        test[5]["quality"][0] = 16
        with self.assertRaises(ValueError):
            build_lagged_examples(*test)

    def test_missing_engineering_row_rejects_consecutive_lagged_examples(self):
        test = list(little_observation())
        for column in ("cadences", "midtime", "quat_bins", "quat_stddev", "median_features"):
            test[6][column] = test[6][column][1:]
        examples = build_lagged_examples(*test)
        self.assertLess(examples["counts"]["eligible_lagged_examples"], 9)
        self.assertEqual(examples["counts"]["engineered_cadences_matched"], 11)

    def test_240_example_embargo_and_60_percent_chronological_boundary(self):
        out = evaluate_examples(generated_examples())
        self.assertEqual(out["boundary_before_embargo"], 1800)
        self.assertEqual(out["train_examples"], 1680)
        self.assertEqual(out["embargo_examples"], 240)
        self.assertEqual(out["test_examples"], 1080)
        self.assertEqual(out["test_first_ending_cadence"] - out["train_last_ending_cadence"], 241)

    def test_informative_quaternion_features_beat_ar2_on_holdout(self):
        metrics = evaluate_examples(generated_examples())
        v = verdicts(metrics)
        self.assertTrue(metrics["evaluable"])
        self.assertTrue(all(v[k] == "SUPPORTED_IN_SELECTED_PRODUCTS" for k in v))
        for axis in ("x", "y"):
            self.assertGreater(metrics["axes"][axis]["incremental_Q_gain_vs_AR2"], .10)
            self.assertLess(metrics["axes"][axis]["shifted_Q_gain_vs_AR2"], .02)

    def test_no_added_info_refutes_the_two_incremental_hypotheses(self):
        metrics = evaluate_examples(generated_examples(with_quaternion=False))
        v = verdicts(metrics)
        self.assertEqual(v["H1_x_incremental"], "NOT_SUPPORTED_IN_SELECTED_PRODUCTS")
        self.assertEqual(v["H2_y_incremental"], "NOT_SUPPORTED_IN_SELECTED_PRODUCTS")

    def test_short_examples_are_not_promoted_to_scientific_verdict(self):
        metrics = evaluate_examples(generated_examples(n=800))
        self.assertFalse(metrics["evaluable"])
        self.assertTrue(all(v == "NOT_EVALUABLE" for v in verdicts(metrics).values()))

    def test_zero_variance_ridge_feature_and_no_holdout_target_leakage(self):
        rng = np.random.default_rng(2207)
        tr = np.column_stack((rng.normal(size=100), np.zeros(100)))
        te = rng.normal(size=(20, 2))
        outcome = rng.normal(size=(100, 2))
        first, meta = fit_ridge(tr, outcome, te)
        second, _ = fit_ridge(tr, outcome, te)
        self.assertEqual(meta["zero_variance_feature_count"], 1)
        np.testing.assert_array_equal(first, second)

    def test_canonical_hash_without_timestamp(self):
        self.assertEqual(digest({"z":2,"a":3}),
                         hashlib.sha256(b'{"a":3,"z":2}').hexdigest())


if __name__ == "__main__":
    unittest.main()
