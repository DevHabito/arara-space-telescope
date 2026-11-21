"""AR-OBS005-P01: provenance audit of TESSVectors camera-level engineering data.

Protocol: docs/preregistration/AR-OBS005-P01.md (frozen before code/data).
This is a cadence/clock-frame study, NOT a physical fault classifier.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

from scripts.ar_obs003_pixel_aperture import fetch_product, LC_FROZEN_SHA
from scripts.ar_obs001_tess_audit import header_identity

PROTOCOL = "AR-OBS005-P01"
VERSION = "1.0.0"
TIC_ID = 307210830
SECTOR = 5
CAMERA = 4
CCD = 4
VECTOR_URL = (
    "https://heasarc.gsfc.nasa.gov/docs/tess/data/TESSVectors/"
    "Vectors/120_Cadence/TessVectors_S005_C4_120.csv"
)
VECTOR_FILENAME = "TessVectors_S005_C4_120.csv"
VECTOR_MAX_BYTES = 24 * 1024 * 1024
REQUIRED_VECTOR_COLUMNS = (
    "Cadence", "MidTime", "Quat_NBinned", "Quat1_StdDev",
    "Quat2_StdDev", "Quat3_StdDev", "Quat4_StdDev",
)
REQUIRED_LC_COLUMNS = ("CADENCENO", "TIME", "TIMECORR", "QUALITY")


class FixedHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if (target.scheme != "https"
                or target.hostname != "heasarc.gsfc.nasa.gov"
                or target.username or target.password):
            raise ValueError("Engineering-vector download redirected outside selected provider")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_vector_csv(destination: Path) -> dict:
    opener = urllib.request.build_opener(FixedHostRedirect())
    req = urllib.request.Request(
        VECTOR_URL,
        headers={"User-Agent": "ARARA-OBS005/1.0 provenance-audit"},
    )
    sha = hashlib.sha256()
    count = 0
    with opener.open(req, timeout=90) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != "heasarc.gsfc.nasa.gov":
            raise ValueError("Unexpected engineering-vector HTTPS response")
        length = response.headers.get("Content-Length")
        if length and int(length) > VECTOR_MAX_BYTES:
            raise ValueError("Engineering file exceeds frozen size limit")
        with destination.open("wb") as out:
            while True:
                block = response.read(256 * 1024)
                if not block:
                    break
                count += len(block)
                if count > VECTOR_MAX_BYTES:
                    raise ValueError("Downloaded engineering CSV exceeded frozen cap")
                sha.update(block)
                out.write(block)
    if not count:
        raise ValueError("Empty engineering vector file")
    return {
        "source_url": VECTOR_URL,
        "resolved_url": response.geturl(),
        "bytes": count,
        "sha256": sha.hexdigest(),
        "file_name": VECTOR_FILENAME,
    }


def parse_integral(value: str, name: str) -> int:
    """Accept integral numeric CSV representations such as '127.0'."""
    try:
        numeric = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid integer-valued {name}") from exc
    if not math.isfinite(numeric) or not numeric.is_integer() or abs(numeric) > 1e12:
        raise ValueError(f"Nonintegral or nonfinite {name}")
    return int(numeric)


def parse_optional_float(value: str | None) -> float:
    if value is None or not str(value).strip():
        return float("nan")
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("Malformed numeric engineering-value field") from exc


def parse_vectors(path: Path) -> dict:
    """Locate the actual CSV header after public explanatory preamble text."""
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        header = None
        preamble_lines = 0
        for line in source:
            cols = next(csv.reader([line]))
            if ("Cadence" in cols and "MidTime" in cols):
                if header is not None:
                    raise ValueError("Repeated vector header")
                header = line
                break
            preamble_lines += 1
            if preamble_lines > 250:
                raise ValueError("No documented CSV header in first 250 lines")
        if header is None:
            raise ValueError("Missing engineering CSV header")
        columns = [field.strip() for field in next(csv.reader([header]))]
        missing = set(REQUIRED_VECTOR_COLUMNS) - set(columns)
        if missing:
            raise ValueError("Required vector fields missing: " + ", ".join(sorted(missing)))
        if len(columns) != len(set(columns)):
            # The unnamed exported index column is allowed exactly once.
            raise ValueError("Duplicate engineering column names")
        reader = csv.DictReader(source, fieldnames=columns)
        ids: list[int] = []
        midtime: list[float] = []
        nquat: list[float] = []
        stdevs: list[tuple[float, float, float, float]] = []
        metadata_columns = tuple(c for c in ("Sector", "Camera") if c in columns)
        for row in reader:
            if not any(str(v).strip() for v in row.values()):
                continue
            if None in row:
                raise ValueError("CSV row contains more fields than header")
            if len(ids) >= 100000:
                raise ValueError("Engineering vector table exceeds frozen row limit")
            cadence = parse_integral(row["Cadence"], "Cadence")
            for name, expected in (("Sector", SECTOR), ("Camera", CAMERA)):
                if name in row and str(row[name]).strip():
                    if parse_integral(row[name], name) != expected:
                        raise ValueError(f"Contradictory engineering {name} field")
            vals = [
                parse_optional_float(row[name])
                for name in ("Quat1_StdDev", "Quat2_StdDev", "Quat3_StdDev", "Quat4_StdDev")
            ]
            count = parse_optional_float(row["Quat_NBinned"])
            if math.isfinite(count) and count < 0:
                raise ValueError("Negative quaternion bin count")
            ids.append(cadence)
            midtime.append(parse_optional_float(row["MidTime"]))
            nquat.append(count)
            stdevs.append(tuple(vals))
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("No engineering rows or nonunique cadence IDs")
    t = np.asarray(midtime, dtype=np.float64)
    if not np.any(np.isfinite(t)):
        raise ValueError("No finite engineering exposure midpoints")
    return {
        "column_names": columns,
        "preamble_line_count": preamble_lines,
        "rows": len(ids),
        "cadences": np.asarray(ids, dtype=np.int64),
        "midtime": t,
        "quat_bins": np.asarray(nquat, dtype=np.float64),
        "quat_stddev": np.asarray(stdevs, dtype=np.float64),
        "identity_columns_present": list(metadata_columns),
    }


def parse_lc(path: Path) -> dict:
    from astropy.io import fits

    with fits.open(path, memmap=False) as hdus:
        header = header_identity([h.header for h in hdus])
        if header != {"TICID": TIC_ID, "SECTOR": SECTOR}:
            raise ValueError("Unexpected target/sector header")
        for key, expected in (("CAMERA", CAMERA), ("CCD", CCD)):
            found = set()
            for hdu in hdus:
                if key in hdu.header:
                    found.add(int(hdu.header[key]))
            if found != {expected}:
                raise ValueError(f"Unexpected {key} header: {sorted(found)}")
        tables = [
            h for h in hdus if isinstance(h, fits.BinTableHDU)
            and h.name == "LIGHTCURVE" and h.data is not None
            and all(name in (h.columns.names or []) for name in REQUIRED_LC_COLUMNS)
        ]
        if len(tables) != 1:
            raise ValueError("Missing unique LIGHTCURVE time/cadence/quality table")
        tab = tables[0].data
        cadences = np.asarray(tab["CADENCENO"])
        quality = np.asarray(tab["QUALITY"])
        time = np.asarray(tab["TIME"], dtype=np.float64)
        corr = np.asarray(tab["TIMECORR"], dtype=np.float64)
        n = len(cadences)
        if (n == 0 or any(a.shape != (n,) for a in (quality, time, corr))
                or not np.issubdtype(cadences.dtype, np.integer)
                or not np.issubdtype(quality.dtype, np.integer)
                or np.any(quality < 0) or len(np.unique(cadences)) != n):
            raise ValueError("Invalid LC cadence/time/quality schema")
        return {
            "rows": n, "cadences": cadences.astype(np.int64),
            "time": time, "timecorr": corr,
            "quality": quality.astype(np.int64),
        }


def percentile95(values: np.ndarray) -> float:
    return float(np.percentile(values, 95))


def compare(vector: dict, lc: dict) -> dict:
    """Perform exactly one integer-key join and frozen descriptive metrics."""
    common, i_v, i_l = np.intersect1d(
        vector["cadences"], lc["cadences"],
        assume_unique=True, return_indices=True,
    )
    matched = len(common)
    v_time = vector["midtime"][i_v]
    l_time = lc["time"][i_l]
    corr = lc["timecorr"][i_l]
    finite = np.isfinite(v_time) & np.isfinite(l_time) & np.isfinite(corr)
    delta = ((l_time[finite] - corr[finite]) - v_time[finite]) * 86400.0
    if not np.all(np.isfinite(delta)):
        raise ValueError("Nonfinite time difference on nominally valid match")
    abs_delta = np.abs(delta)
    qzero = lc["quality"][i_l] == 0
    stdev = vector["quat_stddev"][i_v]
    bins = vector["quat_bins"][i_v]
    engineering_available = (
        np.isfinite(bins) & (bins > 0)
        & np.all(np.isfinite(stdev) & (stdev >= 0), axis=1)
    )
    contingency = {
        "quality_zero_and_engineering": int(np.count_nonzero(qzero & engineering_available)),
        "quality_zero_and_no_engineering": int(np.count_nonzero(qzero & ~engineering_available)),
        "quality_flagged_and_engineering": int(np.count_nonzero(~qzero & engineering_available)),
        "quality_flagged_and_no_engineering": int(np.count_nonzero(~qzero & ~engineering_available)),
    }
    if sum(contingency.values()) != matched:
        raise AssertionError("Engineering mask contingency does not conserve matches")
    available_bins = bins[engineering_available]
    finite_lc_time = int(np.count_nonzero(np.isfinite(lc["time"])))
    coverage_numerator = int(np.count_nonzero(np.isfinite(v_time) & np.isfinite(l_time)))
    return {
        "lc_rows": lc["rows"], "vector_rows": vector["rows"],
        "matched_rows": matched,
        "unmatched_lc": lc["rows"] - matched,
        "unmatched_vector": vector["rows"] - matched,
        "lc_finite_time_rows": finite_lc_time,
        "matched_finite_lc_and_vector_time_rows": coverage_numerator,
        "finite_time_comparison_rows": int(np.count_nonzero(finite)),
        "time_delta_seconds": {
            "median_abs": float(np.median(abs_delta)) if len(abs_delta) else None,
            "p95_abs": percentile95(abs_delta) if len(abs_delta) else None,
            "max_abs": float(np.max(abs_delta)) if len(abs_delta) else None,
            "median_signed": float(np.median(delta)) if len(delta) else None,
        },
        "engineering_presence": {
            "matched_finite_quat_nbins": int(np.count_nonzero(np.isfinite(bins))),
            "matched_engineering_available": int(np.count_nonzero(engineering_available)),
            "median_bins_for_available": float(np.median(available_bins))
            if len(available_bins) else None,
            "quality_zero_matched_rows": int(np.count_nonzero(qzero)),
            "contingency": contingency,
        },
    }


def hypotheses(m: dict) -> dict:
    presence = m["engineering_presence"]
    q0 = presence["quality_zero_matched_rows"]
    ct = presence["contingency"]
    td = m["time_delta_seconds"]
    results = {}
    if m["lc_finite_time_rows"] == 0:
        results["H1_cadence_coverage"] = "NOT_EVALUABLE"
    else:
        ratio = (m["matched_finite_lc_and_vector_time_rows"]
                 / m["lc_finite_time_rows"])
        results["H1_cadence_coverage"] = (
            "SUPPORTED_IN_SELECTED_PRODUCTS" if ratio >= .95
            else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        )
    if m["finite_time_comparison_rows"] < 100 or td["median_abs"] is None:
        results["H2_clock_frame_alignment"] = "NOT_EVALUABLE"
    else:
        yes = td["median_abs"] <= 2.0 and td["p95_abs"] <= 5.0
        results["H2_clock_frame_alignment"] = (
            "SUPPORTED_IN_SELECTED_PRODUCTS" if yes
            else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        )
    if q0 < 100:
        results["H3_quaternion_availability"] = "NOT_EVALUABLE"
    else:
        yes = ct["quality_zero_and_engineering"] / q0 >= .50
        results["H3_quaternion_availability"] = (
            "SUPPORTED_IN_SELECTED_PRODUCTS" if yes
            else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        )
    return results


def canonical_digest(payload: dict) -> str:
    data = json.dumps(
        payload, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def run() -> dict:
    import astropy

    report = {
        "protocol": PROTOCOL, "implementation_version": VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "astropy_version": astropy.__version__,
        "selection": {
            "tic_id": TIC_ID, "sector": SECTOR, "camera": CAMERA, "ccd": CCD,
            "engineering_file": VECTOR_FILENAME,
        },
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
        "hypotheses": {
            "H1_cadence_coverage": "INCONCLUSIVE_ACCESS_OR_SCHEMA",
            "H2_clock_frame_alignment": "INCONCLUSIVE_ACCESS_OR_SCHEMA",
            "H3_quaternion_availability": "INCONCLUSIVE_ACCESS_OR_SCHEMA",
        },
    }
    try:
        with tempfile.TemporaryDirectory(prefix="ar-obs005-") as tmp:
            csv_path = Path(tmp) / VECTOR_FILENAME
            lc_path = Path(tmp) / "lightcurve.fits"
            v_source = fetch_vector_csv(csv_path)
            lc_source = fetch_product("LC", lc_path)
            report["source_files"] = {"VECTOR": v_source, "LC": lc_source}
            if lc_source["sha256"] != LC_FROZEN_SHA:
                raise ValueError("LC SHA-256 differs from frozen source")
            report["gates"]["G1"] = "PASS"
            vec = parse_vectors(csv_path)
            lc = parse_lc(lc_path)
            report["gates"]["G2"] = "PASS"
            measurement = compare(vec, lc)
            report["gates"]["G3"] = "PASS"
            report["gates"]["G4"] = "PASS"
            report["engineering_columns"] = vec["column_names"]
            report["engineering_preamble_lines"] = vec["preamble_line_count"]
            report["engineering_identity_columns"] = vec["identity_columns_present"]
            report["measurements"] = measurement
            report["hypotheses"] = hypotheses(measurement)
            report["gates"]["G5"] = "PASS"
            report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error_type"] = type(error).__name__
        report["error_detail"] = str(error)[:500]
    report["payload_sha256"] = canonical_digest(report)
    return report


def main() -> int:
    import sys

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs005_audit.json")
    result = run()
    out.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "gates": result["gates"],
        "hypotheses": result["hypotheses"],
        "error_detail": result.get("error_detail"),
        "rows": result.get("measurements", {}).get("matched_rows"),
        "digest": result["payload_sha256"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
