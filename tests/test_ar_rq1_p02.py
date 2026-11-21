"""Regression and independent sanity checks for AR-RQ1-P02."""

import hashlib
import json
import math
import unittest

import numpy as np

from scripts.ar_rq1_p02 import (
    EPOCHS,
    MODELS,
    PAIRS,
    REFERENCE_STARS,
    SCENARIOS,
    THRESHOLD,
    classification_metrics,
    evaluate,
    paired_observation,
    photometry_depth,
)


class PairedDiagnosticTests(unittest.TestCase):
    def test_determinism_and_seed_variation(self):
        first = paired_observation(0)
        repeated = paired_observation(0)
        other = paired_observation(1)
        for left, right in zip(first[:2], repeated[:2]):
            np.testing.assert_array_equal(left, right)
        self.assertEqual(first[2:], repeated[2:])
        self.assertFalse(np.array_equal(first[0], other[0]))

    def test_contract_shape_and_dip(self):
        target, references, z_a, z_i = paired_observation(2)
        self.assertEqual(target.shape, (EPOCHS,))
        self.assertEqual(references.shape, (REFERENCE_STARS, EPOCHS))
        self.assertTrue(np.isfinite(target).all())
        self.assertTrue(np.isfinite(references).all())
        self.assertNotEqual(z_a, z_i)

    def test_bounds_rejected(self):
        with self.assertRaises(ValueError):
            paired_observation(-1)
        with self.assertRaises(ValueError):
            paired_observation(PAIRS)
        target, refs, _, _ = paired_observation(1)
        with self.assertRaises(ValueError):
            photometry_depth(target[:-1], refs)
        with self.assertRaises(ValueError):
            photometry_depth(target, refs[:1])

    def test_fixed_contrast_matches_independent_loop(self):
        target, references, _, _ = paired_observation(4)
        reference_medians = np.array([
            sorted(references[:, t].tolist())[REFERENCE_STARS // 2]
            for t in range(EPOCHS)
        ])
        curve = target - reference_medians
        oracle = (
            sum(curve[128:136]) / 8
            - (sum(curve[104:112]) / 8 + sum(curve[152:160]) / 8) / 2
        )
        self.assertAlmostEqual(photometry_depth(target, references), oracle, places=12)

    def test_confusion_count_accounting(self):
        m = classification_metrics(200, 300)
        self.assertEqual(m['astro_retention'], 200 / PAIRS)
        self.assertEqual(m['artifact_rejection'], 300 / PAIRS)
        self.assertEqual(m['artifact_miss_rate'], 212 / PAIRS)
        self.assertEqual(m['balanced_accuracy'], 250 / PAIRS)

    def test_frozen_experiment_gates_and_report_integrity(self):
        out = evaluate()
        self.assertEqual(out['pairs'], PAIRS)
        self.assertEqual(out['identical_photometry_pairs'], PAIRS)
        self.assertEqual(set(out['results']), set(SCENARIOS))
        self.assertTrue(all(v == 'PASS' for v in out['gates'].values()))
        for scenario in SCENARIOS:
            self.assertEqual(set(out['results'][scenario]), set(MODELS))
            self.assertEqual(
                out['results'][scenario]['PHOTOMETRY_ONLY']['balanced_accuracy'], 0.5
            )
        actual = dict(out)
        digest = actual.pop('payload_sha256')
        encoded = json.dumps(actual, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        self.assertEqual(hashlib.sha256(encoded.encode('utf-8')).hexdigest(), digest)
        gaussian_expectation = (1 + math.erf(THRESHOLD / math.sqrt(2))) / 2
        self.assertAlmostEqual(out['expected_gaussian_balanced_accuracy']['ALIGNED'], gaussian_expectation)

    def test_no_fitted_decision_rule_or_telescope_claim(self):
        self.assertEqual(THRESHOLD, 0.75)
        self.assertEqual(SCENARIOS['ALIGNED'], (0.0, 1.5))
        self.assertEqual(SCENARIOS['UNINFORMATIVE'], (0.75, 0.75))
        self.assertEqual(SCENARIOS['INVERTED'], (1.5, 0.0))


if __name__ == '__main__':
    unittest.main()
