"""Network-free checks of preregistered AR-SWARM001-P01 service-health experiment."""

import hashlib
import unittest

import numpy as np

from scripts.ar_swarm001_operational_stability import (
    CHAMPION_OPTIONS, SCENARIOS, SCORES, START_SEED,
    TARGET_EXTERNAL_ADEQUACY, WINDOWS_PER_EPISODE,
    aggregate, canonical_hash, confusion, episode_seed, evaluate,
    generate_cohorts, generate_episode, hypothesis_verdicts,
    score_telemetry, tie_aware_auc, trained_normalization,
)


class OperationalStabilityTests(unittest.TestCase):
    def test_frozen_registration_and_scopes(self):
        self.assertEqual(START_SEED, 20261123)
        self.assertEqual(len(SCENARIOS), 5)
        self.assertEqual(WINDOWS_PER_EPISODE, 48)
        self.assertEqual(TARGET_EXTERNAL_ADEQUACY, .80)
        self.assertEqual(CHAMPION_OPTIONS, SCORES[1:])

    def test_seed_allocation_and_bounds(self):
        self.assertEqual(episode_seed(0, 0), 20261123)
        self.assertEqual(episode_seed(4, 49), 20265172)
        seeds = [episode_seed(i, j) for i in range(5) for j in range(50)]
        self.assertEqual(len(set(seeds)), len(seeds))
        with self.assertRaises(ValueError):
            episode_seed(4, 50)

    def test_episode_replay_is_bitwise_deterministic(self):
        a = generate_episode("VISIBLE_CORRUPTION", 4)
        b = generate_episode("VISIBLE_CORRUPTION", 4)
        np.testing.assert_array_equal(a.telemetry, b.telemetry)
        np.testing.assert_array_equal(a.labels, b.labels)
        self.assertEqual(a.telemetry.shape, (42, 3))
        self.assertEqual(a.labels.shape, (42,))
        self.assertTrue(np.isfinite(a.telemetry).all())
        self.assertTrue(np.all(a.telemetry[:, 1:] > 0))
        self.assertTrue(np.isin(a.labels, [0, 1]).all())

    def test_unseen_hidden_faults_never_enter_training(self):
        train, obs, hidden = generate_cohorts()
        self.assertEqual((len(train), len(obs), len(hidden)), (120, 80, 50))
        self.assertEqual({b.regime for b in hidden}, {"HIDDEN_CORRUPTION"})
        self.assertFalse(any(b.regime == "HIDDEN_CORRUPTION" for b in train))
        self.assertTrue(all(b.episode < 30 for b in train))
        self.assertTrue(all(b.episode >= 30 for b in obs))
        self.assertEqual(aggregate(hidden)[0].shape, (2100, 3))

    def test_unfitted_romero_formula(self):
        norm = trained_normalization(np.array([[10., .1, 2.], [20., .2, 4.]]))
        risk = score_telemetry(np.array([[10., .1, 2.]]), norm)
        self.assertAlmostEqual(risk["RZS"][0], -50.)
        self.assertAlmostEqual(risk["B_ONLY"][0], -10.)
        self.assertAlmostEqual(risk["I_ONLY"][0], .1)
        self.assertAlmostEqual(risk["TAU_ONLY"][0], 2.)
        self.assertAlmostEqual(risk["LINEAR"][0], -1.)
        self.assertAlmostEqual(risk["MAX"][0], 1.)

    def test_training_only_normalization(self):
        train = np.array([[9., .02, .1], [11., .04, .2], [13., .06, .3]])
        unseen = np.array([[400., .8, 5.]])
        first = score_telemetry(unseen, trained_normalization(train))
        again = score_telemetry(unseen, trained_normalization(train.copy()))
        self.assertTrue(all(np.array_equal(first[k], again[k]) for k in SCORES))

    def test_constant_proxy_is_not_artificially_scaled(self):
        norm = trained_normalization(np.array([[3., .02, .4], [3., .02, .4]]))
        output = score_telemetry(np.array([[4., .2, .9]]), norm)
        self.assertEqual(output["LINEAR"].item(), 0.)
        self.assertEqual(output["MAX"].item(), 0.)

    def test_tie_aware_auc_and_missing_class(self):
        self.assertAlmostEqual(tie_aware_auc([0, 0, 1, 1], [0, 0, 0, 0]), .5)
        self.assertAlmostEqual(tie_aware_auc([0, 1, 0, 1], [0, 4, 2, 6]), 1.)
        self.assertAlmostEqual(tie_aware_auc([0, 1, 0, 1], [4, 0, 6, 2]), 0.)
        self.assertIsNone(tie_aware_auc([0, 0], [0, 1]))
        with self.assertRaises(ValueError):
            tie_aware_auc([1, 0], [np.nan, 1])

    def test_confusion_table_invariants(self):
        item = confusion(np.array([1, 1, 0, 0]), np.array([1., 2., 0., 2.]), 1.)
        self.assertEqual((item["TP"], item["FN"], item["FP"], item["TN"]), (1, 1, 1, 1))
        self.assertEqual(item["recall"], .5)
        self.assertEqual(item["false_positive_rate"], .5)
        self.assertEqual(item["alarm_coverage"], .5)

    def test_hypotheses_can_be_supported_or_rejected(self):
        yes = hypothesis_verdicts(
            {"RZS": {"roc_auc": .90, "recall": .7, "false_positive_rate": .1},
             "MAX": {"roc_auc": .8}},
            {"RZS": {"recall": .12}}, "MAX",
        )
        self.assertEqual(yes["H1_added_ranking_information"], "SUPPORTED_IN_SIMULATION")
        self.assertEqual(yes["H2_advance_alarm"], "SUPPORTED_IN_SIMULATION")
        self.assertEqual(yes["H3_hidden_corruption_limit"], "BLIND_SPOT_EXPOSED_IN_SIMULATION")
        no = hypothesis_verdicts(
            {"RZS": {"roc_auc": .75, "recall": .3, "false_positive_rate": .3},
             "MAX": {"roc_auc": .83}},
            {"RZS": {"recall": .4}}, "MAX",
        )
        self.assertEqual(no["H1_added_ranking_information"], "NOT_SUPPORTED_IN_SIMULATION")
        self.assertEqual(no["H2_advance_alarm"], "NOT_SUPPORTED_IN_SIMULATION")
        self.assertEqual(no["H3_hidden_corruption_limit"], "BLIND_SPOT_NOT_ESTABLISHED")

    def test_evaluation_conserves_label_counts(self):
        risk = {name: np.array([.1, .2, .3, .4]) for name in SCORES}
        metrics = evaluate(np.array([0, 0, 1, 1]), risk, {k: .2 for k in SCORES})
        self.assertEqual(metrics["RZS"]["TP"], 2)
        self.assertEqual(metrics["RZS"]["FP"], 0)
        self.assertEqual(metrics["RZS"]["roc_auc"], 1.)

    def test_canonical_payload_digest(self):
        self.assertEqual(
            canonical_hash({"z": 2, "a": 3}),
            hashlib.sha256(b'{"a":3,"z":2}').hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
