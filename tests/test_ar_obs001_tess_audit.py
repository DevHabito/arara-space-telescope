"""Unit tests for AR-OBS001-P01 without any external observations."""

import hashlib
import json
import unittest

import numpy as np

from scripts.ar_obs001_tess_audit import (
    ARCHIVE_URL,
    FILE_NAME,
    MAX_BYTES,
    PROTOCOL,
    SECTOR,
    TIC_ID,
    canonical_hash,
    describe_lightcurve,
    finite_positive_counts,
    header_identity,
    summarize_quality,
)


class ObservationalAuditTests(unittest.TestCase):
    def test_frozen_source(self):
        self.assertEqual(PROTOCOL, "AR-OBS001-P01")
        self.assertEqual(TIC_ID, 307210830)
        self.assertEqual(SECTOR, 5)
        self.assertTrue(FILE_NAME.endswith("-s_lc.fits"))
        self.assertIn("s0005/", ARCHIVE_URL)
        self.assertEqual(MAX_BYTES, 32 * 1024 * 1024)

    def test_identity_headers(self):
        self.assertEqual(
            header_identity([{"TICID": str(TIC_ID)}, {"SECTOR": SECTOR}]),
            {"TICID": TIC_ID, "SECTOR": SECTOR},
        )
        with self.assertRaises(ValueError):
            header_identity([{"TICID": 123, "SECTOR": SECTOR}])
        with self.assertRaises(ValueError):
            header_identity([{"TICID": TIC_ID}])
        with self.assertRaises(ValueError):
            header_identity([{"TICID": TIC_ID}, {"TICID": 123, "SECTOR": SECTOR}])

    def test_quality_bits_can_overlap_and_counts_are_exact(self):
        flags = np.array([0, 1, 32, 33, 64, 2048], dtype=np.int32)
        out = summarize_quality(flags)
        self.assertEqual(out["zero_count"], 1)
        self.assertEqual(out["nonzero_count"], 5)
        self.assertEqual(out["bits_1_to_16"]["1"], 2)
        self.assertEqual(out["bits_1_to_16"]["6"], 2)
        self.assertEqual(out["bits_1_to_16"]["7"], 1)
        self.assertEqual(out["bits_1_to_16"]["12"], 1)
        with self.assertRaises(ValueError):
            summarize_quality(np.array([0.0, 1.0]))
        with self.assertRaises(ValueError):
            summarize_quality(np.array([-1, 0], dtype=int))

    def test_finite_positive_subsets(self):
        values = np.array([1.0, np.nan, -2.0, 0.0, 3.0])
        good = np.array([True, True, False, True, False])
        self.assertEqual(
            finite_positive_counts(values, good),
            {"all_rows": 2, "quality_zero_rows": 1},
        )

    def test_descriptive_summary_without_selecting_events(self):
        table = {
            "TIME": np.array([0.0, 1.0, np.nan, 3.0], dtype=float),
            "SAP_FLUX": np.array([1.0, 2.0, -1.0, 4.0]),
            "PDCSAP_FLUX": np.array([0.9, np.nan, 1.1, 4.1]),
            "QUALITY": np.array([0, 32, 0, 0], dtype=np.int32),
            "MOM_CENTR1": np.array([0.1, 0.2, np.nan, 0.4]),
        }
        out = describe_lightcurve(table, tuple(table))
        self.assertEqual(out["cadences"], 4)
        self.assertEqual(out["finite_time_rows"], 3)
        self.assertEqual(out["quality"]["zero_count"], 3)
        self.assertEqual(out["finite_positive_flux_rows"]["SAP_FLUX"]["all_rows"], 3)
        self.assertEqual(out["finite_positive_flux_rows"]["SAP_FLUX"]["quality_zero_rows"], 2)
        self.assertEqual(out["optional_columns"]["MOM_CENTR1"]["finite_rows"], 3)
        self.assertFalse(out["optional_columns"]["MOM_CENTR2"]["available"])

    def test_invalid_schema_is_not_filled_with_guesses(self):
        data = {
            "TIME": np.arange(2, dtype=float),
            "SAP_FLUX": np.ones(2),
            "PDCSAP_FLUX": np.ones(2),
            "QUALITY": np.zeros(2, dtype=int),
        }
        with self.assertRaises(ValueError):
            describe_lightcurve(data, ("TIME", "SAP_FLUX", "QUALITY"))
        data["TIME"] = np.full(2, np.nan)
        with self.assertRaises(ValueError):
            describe_lightcurve(data, tuple(data))

    def test_canonical_hash_is_stable_and_content_sensitive(self):
        a = {"b": 2, "a": 1}
        b = {"a": 1, "b": 2}
        self.assertEqual(canonical_hash(a), canonical_hash(b))
        self.assertEqual(
            canonical_hash(a),
            hashlib.sha256(b'{"a":1,"b":2}').hexdigest(),
        )
        self.assertNotEqual(canonical_hash(a), canonical_hash({"a": 2, "b": 2}))


if __name__ == "__main__":
    unittest.main()
