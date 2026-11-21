"""AR-OBS003-P01: provenance and SAP reconstruction for one TESS target pixel file.

The predeclared source, thresholds and limitations are fixed in
docs/preregistration/AR-OBS003-P01.md (commit add93ad1).
This script does not search for astronomical events.
"""

from __future__ import annotations

import hashlib
import json
import platform
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

from scripts.ar_obs001_tess_audit import ArchiveHostRedirect, header_identity

PROTOCOL = "AR-OBS003-P01"
VERSION = "1.0.0"
TIC_ID = 307210830
SECTOR = 5
SOURCE_DIRECTORY = (
    "https://archive.stsci.edu/missions/tess/tid/s0005/"
    "0000/0003/0721/0830/"
)
TPF_NAME = "tess2018319095959-s0005-0000000307210830-0125-s_tp.fits"
LC_NAME = "tess2018319095959-s0005-0000000307210830-0125-s_lc.fits"
LC_FROZEN_SHA = "a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae"
MAX_BYTES = 128 * 1024 * 1024
SOURCE_NAMES = {"TPF": TPF_NAME, "LC": LC_NAME}
TPF_REQUIRED = ("TIME", "CADENCENO", "QUALITY", "FLUX")
LC_REQUIRED = ("TIME", "CADENCENO", "QUALITY", "SAP_FLUX", "PDCSAP_FLUX")


def fetch_product(role: str, destination: Path) -> dict:
    """Retrieve only a frozen public STScI file with bounded transfer size."""
    if role not in SOURCE_NAMES:
        raise ValueError("Unknown frozen product role")
    url = SOURCE_DIRECTORY + SOURCE_NAMES[role]
    opener = urllib.request.build_opener(ArchiveHostRedirect())
    request = urllib.request.Request(
        url, headers={"User-Agent": "ARARA-OBS003/1.0 archival-pixel-audit"}
    )
    size = 0
    digest = hashlib.sha256()
    with opener.open(request, timeout=120) as response:
        resolved = response.geturl()
        parsed = urllib.parse.urlsplit(resolved)
        if (parsed.scheme != "https" or not parsed.hostname
                or not parsed.hostname.endswith(".stsci.edu")
                or parsed.username is not None or parsed.password is not None):
            raise ValueError("Unexpected FITS provider after HTTPS redirect")
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > MAX_BYTES:
            raise ValueError("FITS content length exceeds frozen cap")
        with destination.open("wb") as out:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("Downloaded FITS exceeds frozen cap")
                digest.update(chunk)
                out.write(chunk)
    if size == 0:
        raise ValueError("Empty FITS product")
    return {
        "role": role,
        "source_url": url,
        "resolved_url": resolved,
        "file_name": SOURCE_NAMES[role],
        "bytes": size,
        "sha256": digest.hexdigest(),
    }


def validate_ids(cadences: np.ndarray, quality: np.ndarray, time: np.ndarray) -> np.ndarray:
    """Validate a one-dimensional cadence key and quality-mask contract."""
    cadence = np.asarray(cadences)
    q = np.asarray(quality)
    t = np.asarray(time)
    if any(x.ndim != 1 for x in (cadence, q, t)):
        raise ValueError("Required cadence fields must be one-dimensional")
    if len(cadence) == 0 or q.shape != cadence.shape or t.shape != cadence.shape:
        raise ValueError("Empty or nonmatching cadence fields")
    if (not np.issubdtype(cadence.dtype, np.integer)
            or not np.issubdtype(q.dtype, np.integer)):
        raise ValueError("Cadence IDs and QUALITY must be integer arrays")
    if np.any(q < 0):
        raise ValueError("QUALITY flags must be nonnegative")
    if len(np.unique(cadence)) != len(cadence):
        raise ValueError("Duplicate CADENCENO in one archival product")
    return cadence.astype(np.int64, copy=False)


def describe_aperture(mask: np.ndarray, image_shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    """Use bit 2 exactly as documented by the official TESS archive."""
    array = np.asarray(mask)
    if array.ndim != 2 or array.shape != image_shape:
        raise ValueError("APERTURE image dimensions do not match pixel cubes")
    if not np.issubdtype(array.dtype, np.integer) or np.any(array < 0):
        raise ValueError("APERTURE must contain nonnegative integer flags")
    selected = (array & 2) != 0
    if not np.any(selected):
        raise ValueError("Missing optimal photometric aperture")
    counts = {
        str(bit): int(np.count_nonzero((array & (1 << (bit - 1))) != 0))
        for bit in range(1, 10)
    }
    return selected, {
        "image_shape": list(image_shape),
        "optimal_pixel_count": int(np.count_nonzero(selected)),
        "background_pixel_count": int(np.count_nonzero((array & 4) != 0)),
        "aperture_bit_counts_1_to_9": counts,
    }


def evaluate_paired_cadences(
    tp_cadences: np.ndarray,
    tp_quality: np.ndarray,
    tp_time: np.ndarray,
    cube: np.ndarray,
    selected: np.ndarray,
    lc_cadences: np.ndarray,
    lc_quality: np.ndarray,
    lc_time: np.ndarray,
    lc_sap: np.ndarray,
) -> dict:
    """Compute fixed paired-key and aperture reconstruction diagnostics."""
    t_ids = validate_ids(tp_cadences, tp_quality, tp_time)
    l_ids = validate_ids(lc_cadences, lc_quality, lc_time)
    t_q = np.asarray(tp_quality, dtype=np.int64)
    l_q = np.asarray(lc_quality, dtype=np.int64)
    t_time = np.asarray(tp_time, dtype=np.float64)
    l_time = np.asarray(lc_time, dtype=np.float64)
    lc_flux = np.asarray(lc_sap, dtype=np.float64)
    pix = np.asarray(cube)
    sel = np.asarray(selected)
    if (pix.ndim != 3 or pix.shape[0] != len(t_ids)
            or sel.shape != pix.shape[1:]
            or sel.dtype != np.bool_ or not np.any(sel)):
        raise ValueError("Pixel cube does not match a nonempty binary aperture")
    if lc_flux.ndim != 1 or lc_flux.shape != l_ids.shape:
        raise ValueError("SAP_FLUX shape mismatch")

    common, idx_tp, idx_lc = np.intersect1d(
        t_ids, l_ids, assume_unique=True, return_indices=True
    )
    n = len(common)
    q_tp, q_lc = t_q[idx_tp], l_q[idx_lc]
    quality_mismatches = int(np.count_nonzero(q_tp != q_lc))
    timestamps_ok = np.isfinite(t_time[idx_tp]) & np.isfinite(l_time[idx_lc])
    offsets = np.abs(t_time[idx_tp[timestamps_ok]] - l_time[idx_lc[timestamps_ok]])

    pixel_rows = np.asarray(pix[idx_tp][:, sel], dtype=np.float64)
    all_pixel_finite = np.all(np.isfinite(pixel_rows), axis=1)
    any_pixel_finite = np.any(np.isfinite(pixel_rows), axis=1)
    good_quality = (q_tp == 0) & (q_lc == 0)
    sap = lc_flux[idx_lc]
    good_sap = np.isfinite(sap) & (sap > 0)

    eligible = good_quality & good_sap & all_pixel_finite
    values = np.sum(pixel_rows[eligible], axis=1)
    observed = sap[eligible]
    differences = values - observed
    errors = np.abs(differences) / np.maximum(np.abs(observed), 1.0)
    if not np.all(np.isfinite(errors)):
        raise ValueError("Nonfinite reconstruction discrepancy")

    count_eligible = int(np.count_nonzero(eligible))
    skipped = {
        "not_quality_zero_in_both": int(np.count_nonzero(~good_quality)),
        "quality_zero_but_invalid_sap": int(np.count_nonzero(good_quality & ~good_sap)),
        "quality_zero_valid_sap_but_missing_selected_pixel": int(
            np.count_nonzero(good_quality & good_sap & ~all_pixel_finite)
        ),
    }
    if sum(skipped.values()) + count_eligible != n:
        raise AssertionError("Eligibility counts do not conserve matched cadences")

    within = int(np.count_nonzero(errors <= 0.001))
    return {
        "tpf_cadences": len(t_ids),
        "lc_cadences": len(l_ids),
        "matched_cadences": n,
        "unmatched_tpf": len(t_ids) - n,
        "unmatched_lc": len(l_ids) - n,
        "quality_mismatch_rows": quality_mismatches,
        "finite_paired_times": int(np.count_nonzero(timestamps_ok)),
        "time_offset_days_max": float(np.max(offsets)) if len(offsets) else None,
        "time_offset_days_median": float(np.median(offsets)) if len(offsets) else None,
        "matched_rows_with_any_selected_pixel_finite": int(np.count_nonzero(any_pixel_finite)),
        "matched_rows_with_all_selected_pixels_finite": int(np.count_nonzero(all_pixel_finite)),
        "eligible_reconstruction_rows": count_eligible,
        "skipped_by_reason": skipped,
        "sap_reconstruction": {
            "median_relative_error": float(np.median(errors)) if len(errors) else None,
            "max_relative_error": float(np.max(errors)) if len(errors) else None,
            "median_signed_difference_electrons_per_second": (
                float(np.median(differences)) if len(differences) else None
            ),
            "count_relative_error_le_0_001": within,
            "fraction_relative_error_le_0_001": within / count_eligible if count_eligible else None,
        },
    }


def load_products(tp_path: Path, lc_path: Path) -> dict:
    from astropy.io import fits

    with fits.open(tp_path, memmap=False) as tp, fits.open(lc_path, memmap=False) as lc:
        tp_id = header_identity([h.header for h in tp])
        lc_id = header_identity([h.header for h in lc])
        if tp_id != lc_id or tp_id != {"TICID": TIC_ID, "SECTOR": SECTOR}:
            raise ValueError("Target/sector header identity conflict")
        pixels = [
            h for h in tp if isinstance(h, fits.BinTableHDU)
            and h.name == "PIXELS" and h.data is not None
            and all(c in (h.columns.names or []) for c in TPF_REQUIRED)
        ]
        lightcurves = [
            h for h in lc if isinstance(h, fits.BinTableHDU)
            and h.name == "LIGHTCURVE" and h.data is not None
            and all(c in (h.columns.names or []) for c in LC_REQUIRED)
        ]
        apertures = [h for h in tp if isinstance(h, fits.ImageHDU)
                     and h.name == "APERTURE" and h.data is not None]
        if len(pixels) != 1 or len(lightcurves) != 1 or len(apertures) != 1:
            raise ValueError("Unexpected FITS extensions or required columns")
        t_table, l_table = pixels[0].data, lightcurves[0].data
        cube = np.asarray(t_table["FLUX"])
        if cube.ndim != 3 or any(dim < 1 for dim in cube.shape):
            raise ValueError("No usable 3-D calibrated target pixel cube")
        selected, aperture_info = describe_aperture(
            apertures[0].data, tuple(cube.shape[1:])
        )
        diag = evaluate_paired_cadences(
            np.asarray(t_table["CADENCENO"]), np.asarray(t_table["QUALITY"]),
            np.asarray(t_table["TIME"]), cube, selected,
            np.asarray(l_table["CADENCENO"]), np.asarray(l_table["QUALITY"]),
            np.asarray(l_table["TIME"]), np.asarray(l_table["SAP_FLUX"])
        )
        return {
            "identity": tp_id,
            "pixel_table_columns": list(pixels[0].columns.names or []),
            "lightcurve_table_columns": list(lightcurves[0].columns.names or []),
            "pixel_flux_units": pixels[0].columns["FLUX"].unit,
            "sap_flux_units": lightcurves[0].columns["SAP_FLUX"].unit,
            "pixel_cube_shape": list(cube.shape),
            "aperture": aperture_info,
            "paired_observations": diag,
        }


def assess_hypotheses(data: dict) -> dict:
    d = data["paired_observations"]
    aligned = (
        d["matched_cadences"] >= 1
        and d["finite_paired_times"] >= 1
        and d["quality_mismatch_rows"] == 0
        and d["time_offset_days_max"] is not None
        and d["time_offset_days_max"] <= 1e-6
    )
    r = d["sap_reconstruction"]
    reconstructed = (
        d["eligible_reconstruction_rows"] >= 100
        and r["median_relative_error"] is not None
        and r["median_relative_error"] <= 0.0001
        and r["fraction_relative_error_le_0_001"] is not None
        and r["fraction_relative_error_le_0_001"] >= 0.95
    )
    return {
        "H1_cadence_quality_time_alignment": (
            "SUPPORTED_IN_SELECTED_PRODUCT_PAIR"
            if aligned else "NOT_SUPPORTED_IN_SELECTED_PRODUCT_PAIR"
        ),
        "H2_sap_aperture_reconstruction": (
            "SUPPORTED_IN_SELECTED_PRODUCT_PAIR"
            if reconstructed else "NOT_SUPPORTED_IN_SELECTED_PRODUCT_PAIR"
        ),
    }


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_audit() -> dict:
    import astropy

    result = {
        "protocol": PROTOCOL,
        "version": VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "astropy_version": astropy.__version__,
        "selected_tic_id": TIC_ID,
        "sector": SECTOR,
        "products": {},
        "hypotheses": {
            "H1_cadence_quality_time_alignment": "INCONCLUSIVE_ACCESS_OR_SCHEMA",
            "H2_sap_aperture_reconstruction": "INCONCLUSIVE_ACCESS_OR_SCHEMA",
        },
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="arara-obs003-") as folder:
            tp_file = Path(folder) / TPF_NAME
            lc_file = Path(folder) / LC_NAME
            result["products"]["TPF"] = fetch_product("TPF", tp_file)
            result["products"]["LC"] = fetch_product("LC", lc_file)
            if result["products"]["LC"]["sha256"] != LC_FROZEN_SHA:
                raise ValueError("LC checksum differs from preregistered archival product")
            result["gates"]["G1"] = "PASS"
            measurements = load_products(tp_file, lc_file)
            result["measurements"] = measurements
            result["gates"]["G2"] = "PASS"
            result["gates"]["G3"] = "PASS"
            result["gates"]["G4"] = "PASS"
        result["hypotheses"] = assess_hypotheses(measurements)
        result["gates"]["G5"] = "PASS"
        result["status"] = "PASS"
    except Exception as exc:
        result["status"] = "FAIL"
        result["error_type"] = type(exc).__name__
        result["error_detail"] = str(exc)[:500]
    result["payload_sha256"] = canonical_digest(result)
    return result


def main() -> int:
    import sys

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs003_audit.json")
    result = run_audit()
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "gates": result["gates"],
        "hypotheses": result["hypotheses"],
        "pixel_shape": result.get("measurements", {}).get("pixel_cube_shape"),
        "matched_cadences": result.get("measurements", {}).get(
            "paired_observations", {}
        ).get("matched_cadences"),
        "eligible_reconstruction_rows": result.get("measurements", {}).get(
            "paired_observations", {}
        ).get("eligible_reconstruction_rows"),
        "error_detail": result.get("error_detail"),
        "output": str(out), "payload_sha256": result["payload_sha256"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
