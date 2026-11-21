"""Deterministic, network-free regression checks for AR-OBS005-P01."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.ar_obs005_tessvectors_alignment import (
    CAMERA,
    PROTOCOL,
    REQUIRED_VECTOR_COLUMNS,
    VECTOR_FILENAME,
    VECTOR_URL,
    canonical_digest,
    compare,
    hypotheses,
    parse_integral,
    parse_vectors,
)


def synthetic_rows(n=180):
    ids = np.arange(170000, 170000 + n, dtype=np.int64)
    base = 1430.0 + np.arange(n, dtype=float) / 720
    vector = {
        "rows": n, "cadences": ids,
        "midtime": base.copy(),
        "quat_bins": np.full(n, 80.0),
        "quat_stddev": np.full((n, 4), 0.00001),
    }
    lc = {
        "rows": n, "cadences": ids.copy(),
        "time": base + .001 + 1.0 / 86400.0,
        "timecorr": np.full(n, .001),
        "quality": np.zeros(n, dtype=np.int64),
    }
    return vector, lc


def sample_csv_content():
    return (
        "# TESSVector engineering archive example\n"
        "# Source information\n"
        "   - Other CCDs have slightly different observation times.\n"
        ",Cadence,MidTime,Quat_NBinned,Quat1_StdDev,Quat2_StdDev,Quat3_StdDev,Quat4_StdDev\n"
        "0,100.0,1500.0000,20,0.001,0.002,0.003,0.004\n"
        "1,101.0,1500.0014,0,nan,nan,nan,nan\n"
    )


class TessVectorsAlignmentTests(unittest.TestCase):
    def test_selection_and_source_frozen(self):
        self.assertEqual(PROTOCOL, "AR-OBS005-P01")
        self.assertEqual(CAMERA, 4)
        self.assertEqual(VECTOR_FILENAME, "TessVectors_S005_C4_120.csv")
        self.assertTrue(VECTOR_URL.startswith("https://heasarc.gsfc.nasa.gov/"))

    def test_integer_csv_compatibility_and_strictness(self):
        self.assertEqual(parse_integral("127.0", "Cadence"), 127)
        self.assertEqual(parse_integral("-2", "Cadence"), -2)
        for s in ("NaN", "1.5", "", "inf"):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):
                    parse_integral(s, "Cadence")

    def test_csv_preamble_and_integral_cadences(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example.csv"
            path.write_text(sample_csv_content(), encoding="utf-8")
            result = parse_vectors(path)
        self.assertEqual(result["preamble_line_count"], 3)
        self.assertEqual(result["rows"], 2)
        self.assertTrue(all(c in result["column_names"] for c in REQUIRED_VECTOR_COLUMNS))
        np.testing.assert_array_equal(result["cadences"], [100, 101])
        self.assertEqual(result["quat_bins"][1], 0)
        self.assertFalse(np.isfinite(result["quat_stddev"][1]).any())

    def test_csv_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                sample_csv_content().replace("101.0", "100.0"), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                parse_vectors(path)

    def test_csv_negative_quaternion_count_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                sample_csv_content().replace("1500.0014,0", "1500.0014,-1"),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                parse_vectors(path)

    def test_exact_cadence_keys_not_row_order(self):
        vec, lc = synthetic_rows()
        permutation = np.arange(180)[::-1]
        for name in ("cadences", "midtime", "quat_bins", "quat_stddev"):
            vec[name] = vec[name][permutation]
        m = compare(vec, lc)
        self.assertEqual(m["matched_rows"], 180)
        self.assertEqual(m["unmatched_lc"], 0)
        self.assertEqual(m["unmatched_vector"], 0)
        self.assertAlmostEqual(m["time_delta_seconds"]["median_abs"], 1.0, places=4)
        self.assertEqual(m["engineering_presence"]["matched_engineering_available"], 180)
        self.assertEqual(
            hypotheses(m), {
                "H1_cadence_coverage": "SUPPORTED_IN_SELECTED_PRODUCTS",
                "H2_clock_frame_alignment": "SUPPORTED_IN_SELECTED_PRODUCTS",
                "H3_quaternion_availability": "SUPPORTED_IN_SELECTED_PRODUCTS",
            },
        )

    def test_missing_engineering_data_is_not_replaced_with_zero(self):
        vec, lc = synthetic_rows()
        vec["quat_stddev"][::2, 1] = np.nan
        vec["quat_bins"][::5] = 0
        m = compare(vec, lc)
        self.assertLess(m["engineering_presence"]["matched_engineering_available"], 100)
        self.assertEqual(
            hypotheses(m)["H3_quaternion_availability"],
            "NOT_SUPPORTED_IN_SELECTED_PRODUCTS",
        )
        self.assertEqual(
            sum(m["engineering_presence"]["contingency"].values()),
            m["matched_rows"],
        )

    def test_missing_cadences_and_clock_failure_preserved(self):
        vec, lc = synthetic_rows()
        selection = np.arange(180) % 10 != 0
        for name in ("cadences", "midtime", "quat_bins", "quat_stddev"):
            vec[name] = vec[name][selection]
        vec["rows"] = int(np.count_nonzero(selection))
        lc["time"] += 10.0 / 86400.0
        m = compare(vec, lc)
        self.assertEqual(m["matched_rows"], 162)
        self.assertEqual(m["unmatched_lc"], 18)
        self.assertEqual(
            hypotheses(m)["H1_cadence_coverage"],
            "NOT_SUPPORTED_IN_SELECTED_PRODUCTS",
        )
        self.assertEqual(
            hypotheses(m)["H2_clock_frame_alignment"],
            "NOT_SUPPORTED_IN_SELECTED_PRODUCTS",
        )

    def test_non_evaluable_time_is_distinct_from_rejection(self):
        vec, lc = synthetic_rows()
        lc["time"][:] = np.nan
        m = compare(vec, lc)
        self.assertEqual(hypotheses(m)["H1_cadence_coverage"], "NOT_EVALUABLE")
        self.assertEqual(hypotheses(m)["H2_clock_frame_alignment"], "NOT_EVALUABLE")

    def test_canonical_payload_sha256(self):
        item = {"b": 3, "a": 1}
        self.assertEqual(
            canonical_digest(item),
            hashlib.sha256(b'{"a":1,"b":3}').hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
