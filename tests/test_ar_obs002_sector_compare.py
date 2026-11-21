"""Unit tests for AR-OBS002-P01 with no remote astronomical observations."""

import hashlib
import json
import unittest

import numpy as np

from scripts.ar_obs002_sector_compare import (
    FROZEN_SECTOR5_SHA256,
    PROTOCOL,
    SOURCES,
    canonical_sha,
    classify_quality,
    compare_results,
    contingency,
    measure_columns,
    percentage,
    product_url,
)


def synthetic_table():
    return {
        "TIME": np.array([0.0, 1.0, np.nan, 3.0, 4.0]),
        "SAP_FLUX": np.array([1.0, 1.1, 1.2, np.nan, 0.9]),
        "PDCSAP_FLUX": np.array([1.0, np.nan, 1.1, 1.0, 0.0]),
        "QUALITY": np.array([0, 1, 0, 33, 0], dtype=np.int32),
        "MOM_CENTR1": np.array([0.1, 0.2, np.nan, 0.4, 0.5]),
        "MOM_CENTR2": np.array([0.1, 0.2, 0.3, np.nan, 0.5]),
        "POS_CORR1": np.array([0.1, np.nan, 0.2, 0.3, 0.4]),
        "POS_CORR2": np.array([0.1, 0.2, 0.3, 0.4, np.nan]),
        "PSF_CENTR1": np.full(5, np.nan),
    }


class ObservationalComparisonTests(unittest.TestCase):
    def test_source_list_frozen_and_specific(self):
        self.assertEqual(PROTOCOL, "AR-OBS002-P01")
        self.assertEqual(set(SOURCES), {2, 5})
        self.assertEqual(FROZEN_SECTOR5_SHA256, "a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae")
        self.assertEqual(
            product_url(2),
            "https://archive.stsci.edu/missions/tess/tid/s0002/0000/0003/0721/0830/"
            "tess2018234235059-s0002-0000000307210830-0121-s_lc.fits",
        )
        with self.assertRaises(ValueError):
            product_url(8)

    def test_contingency_uses_rowwise_intersections(self):
        q_zero = np.array([True, True, False, False])
        valid = np.array([True, False, True, False])
        counts = contingency(q_zero, valid)
        self.assertEqual(counts, {
            "Q_and_valid": 1,
            "Q_and_invalid": 1,
            "flagged_and_valid": 1,
            "flagged_and_invalid": 1,
        })
        self.assertEqual(sum(counts.values()), 4)
        # Q=0 and valid have equal marginal counts, yet differ by row.
        self.assertEqual(np.count_nonzero(q_zero), np.count_nonzero(valid))
        self.assertFalse(np.array_equal(q_zero, valid))

    def test_contingency_shape_rejected(self):
        with self.assertRaises(ValueError):
            contingency(np.array([True]), np.array([True, False]))
        with self.assertRaises(ValueError):
            contingency(np.array([1], dtype=int), np.array([True]))

    def test_quality_rejects_non_integer_and_negative(self):
        q_zero, quality = classify_quality(np.array([0, 32, 33], dtype=np.int32))
        np.testing.assert_array_equal(q_zero, [True, False, False])
        self.assertTrue(np.issubdtype(quality.dtype, np.integer))
        with self.assertRaises(ValueError):
            classify_quality(np.array([0, -1]))
        with self.assertRaises(ValueError):
            classify_quality(np.array([0.0, 1.0]))

    def test_contingencies_and_bits_count_exactly(self):
        tab = synthetic_table()
        result = measure_columns(tab, tuple(tab))
        self.assertEqual(result["total_rows"], 5)
        self.assertEqual(result["quality_zero_rows"], 3)
        self.assertEqual(result["quality_flagged_rows"], 2)
        self.assertEqual(result["pdc_quality_mismatches"], {
            "quality_zero_but_pdc_invalid": 1,
            "quality_flagged_but_pdc_valid": 1,
        })
        self.assertFalse(result["pdc_quality_zero_equivalent_rowwise"])
        self.assertEqual(result["quality_bits_1_to_16"]["1"]["rows"], 2)
        self.assertEqual(result["quality_bits_1_to_16"]["6"]["rows"], 1)
        self.assertEqual(result["quality_bits_1_to_16"]["6"]["with_valid_pdc"], 1)
        self.assertEqual(result["valid_rows"]["TIME"], 4)
        self.assertEqual(result["valid_rows"]["MOM_CENTR_PAIR"], 3)
        self.assertEqual(result["valid_rows"]["POS_CORR_PAIR"], 3)
        self.assertTrue(result["optional_centroid_columns"]["PSF_CENTR1"]["present"])
        self.assertEqual(result["optional_centroid_columns"]["PSF_CENTR1"]["finite_rows"], 0)
        self.assertFalse(result["optional_centroid_columns"]["PSF_CENTR2"]["present"])
        for table in result["contingency"].values():
            self.assertEqual(sum(table.values()), 5)

    def test_equivalence_when_quality_and_pdc_match_exactly(self):
        tab = synthetic_table()
        tab["PDCSAP_FLUX"] = np.array([1.0, np.nan, 1.1, np.nan, 1.0])
        result = measure_columns(tab, tuple(tab))
        self.assertTrue(result["pdc_quality_zero_equivalent_rowwise"])
        self.assertEqual(
            result["pdc_quality_mismatches"],
            {"quality_zero_but_pdc_invalid": 0, "quality_flagged_but_pdc_valid": 0},
        )

    def test_schema_invalid_is_not_filled(self):
        tab = synthetic_table()
        with self.assertRaises(ValueError):
            measure_columns(tab, ("TIME", "SAP_FLUX", "PDCSAP_FLUX"))
        tab["TIME"] = np.full(5, np.nan)
        with self.assertRaises(ValueError):
            measure_columns(tab, tuple(tab))
        tab = synthetic_table()
        tab["SAP_FLUX"] = np.ones(3)
        with self.assertRaises(ValueError):
            measure_columns(tab, tuple(tab))

    def test_contrasts_do_not_claim_independent_source(self):
        m = measure_columns(synthetic_table(), tuple(synthetic_table()))
        row = {"fits": {"measurements": m}}
        stats = compare_results(row, row)
        self.assertEqual(stats["2"], stats["5"])
        self.assertFalse(stats["2"]["pdc_quality_equivalent"])
        self.assertEqual(stats["2"]["pdc_valid_given_quality_zero"], 2 / 3)
        self.assertEqual(stats["2"]["pdc_valid_given_flagged"], 1 / 2)
        self.assertIsNone(percentage(0, 0))

    def test_hash_deterministic_without_pretty_spacing(self):
        item = {"z": "ok", "a": 1}
        serialized = json.dumps(item, sort_keys=True, ensure_ascii=False,
                                separators=(",", ":"), allow_nan=False)
        self.assertEqual(canonical_sha(item), hashlib.sha256(serialized.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    unittest.main()
