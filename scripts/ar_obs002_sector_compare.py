"""AR-OBS002-P01: row-wise quality and availability audit of two TESS sectors.

A new protocol was committed before this implementation:
docs/preregistration/AR-OBS002-P01.md.

No light-curve fitting, transit search, or astrophysical event labels.
FITS files are fetched into a temporary directory and never archived.
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

from scripts.ar_obs001_tess_audit import (
    ArchiveHostRedirect,
    MAX_BYTES,
    TIC_ID,
)

PROTOCOL = "AR-OBS002-P01"
VERSION = "1.0.0"
FILE_ROOT = "https://archive.stsci.edu/missions/tess/tid"
TIC_PARTITION = "0000/0003/0721/0830"
SOURCES = {
    5: "tess2018319095959-s0005-0000000307210830-0125-s_lc.fits",
    2: "tess2018234235059-s0002-0000000307210830-0121-s_lc.fits",
}
FROZEN_SECTOR5_SHA256 = (
    "a54fa0f1ec9b4bd860083d9dbef49ccd667f1959e3c210e5c480ee6368e6a0ae"
)
REQUIRED_COLUMNS = (
    "TIME", "SAP_FLUX", "PDCSAP_FLUX", "QUALITY",
    "MOM_CENTR1", "MOM_CENTR2", "POS_CORR1", "POS_CORR2",
)
OPTIONAL_COLUMNS = ("PSF_CENTR1", "PSF_CENTR2")
MASK_NAMES = ("TIME", "SAP_FLUX", "PDCSAP_FLUX", "MOM_CENTR_PAIR", "POS_CORR_PAIR")


def product_url(sector: int) -> str:
    """Return only one of the two preregistered public FITS URLs."""
    if sector not in SOURCES:
        raise ValueError("Sector not preregistered")
    return f"{FILE_ROOT}/s{sector:04d}/{TIC_PARTITION}/{SOURCES[sector]}"


def validate_file_identity(headers: list, sector: int) -> dict:
    """Compare both FITS identifiers with the selected preregistered sector."""
    if sector not in SOURCES:
        raise ValueError("Sector not preregistered")
    verified = {}
    for name, expected in (("TICID", TIC_ID), ("SECTOR", sector)):
        reported = set()
        for header in headers:
            if name in header:
                try:
                    reported.add(int(header[name]))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid {name} FITS header") from exc
        if not reported or reported != {expected}:
            raise ValueError(
                f"{name} does not match selected file: "
                f"expected {expected}, found {sorted(reported)}"
            )
        verified[name] = expected
    return verified


def fetch_fits(sector: int, destination: Path) -> dict:
    """Download bounded bytes, rejecting changes to HTTPS archive origin."""
    url = product_url(sector)
    req = urllib.request.Request(
        url, headers={"User-Agent": "ARARA-OBS002/1.0 public-data audit"},
    )
    opener = urllib.request.build_opener(ArchiveHostRedirect())
    total = 0
    digest = hashlib.sha256()
    with opener.open(req, timeout=60) as response:
        resolved = response.geturl()
        parsed = urllib.parse.urlparse(resolved)
        if (parsed.scheme != "https" or not parsed.hostname
                or not parsed.hostname.endswith(".stsci.edu")
                or parsed.username is not None or parsed.password is not None):
            raise ValueError("Unexpected final archive URL")
        size = response.headers.get("Content-Length")
        if size is not None and int(size) > MAX_BYTES:
            raise ValueError("File exceeds 32 MiB limit")
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("File exceeds 32 MiB limit")
                digest.update(chunk)
                handle.write(chunk)
    if total == 0:
        raise ValueError("FITS download empty")
    return {
        "sector": sector,
        "file_name": SOURCES[sector],
        "source_url": url,
        "resolved_url": resolved,
        "bytes": total,
        "sha256": digest.hexdigest(),
    }


def classify_quality(quality: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Quality flags are integer processing annotations, not ground-truth labels."""
    values = np.asarray(quality)
    if values.ndim != 1 or not np.issubdtype(values.dtype, np.integer):
        raise ValueError("QUALITY must be a 1-D integer column")
    if np.any(values < 0):
        raise ValueError("Negative QUALITY flag")
    return values == 0, values.astype(np.int64)


def contingency(q_zero: np.ndarray, valid: np.ndarray) -> dict:
    """Exhaustive 2x2 table; counts must conserve all original cadences."""
    if q_zero.ndim != 1 or valid.ndim != 1 or q_zero.shape != valid.shape:
        raise ValueError("Contingency mask shape mismatch")
    if q_zero.dtype != np.bool_ or valid.dtype != np.bool_:
        raise ValueError("Contingency expects boolean masks")
    output = {
        "Q_and_valid": int(np.count_nonzero(q_zero & valid)),
        "Q_and_invalid": int(np.count_nonzero(q_zero & ~valid)),
        "flagged_and_valid": int(np.count_nonzero(~q_zero & valid)),
        "flagged_and_invalid": int(np.count_nonzero(~q_zero & ~valid)),
    }
    if sum(output.values()) != len(q_zero):
        raise AssertionError("Contingency count conservation failure")
    return output


def measure_columns(table, columns: tuple[str, ...]) -> dict:
    if any(name not in columns for name in REQUIRED_COLUMNS):
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        raise ValueError("Required FITS columns missing: " + ",".join(missing))
    time = np.asarray(table["TIME"], dtype=np.float64)
    sap = np.asarray(table["SAP_FLUX"], dtype=np.float64)
    pdc = np.asarray(table["PDCSAP_FLUX"], dtype=np.float64)
    mc1 = np.asarray(table["MOM_CENTR1"], dtype=np.float64)
    mc2 = np.asarray(table["MOM_CENTR2"], dtype=np.float64)
    pos1 = np.asarray(table["POS_CORR1"], dtype=np.float64)
    pos2 = np.asarray(table["POS_CORR2"], dtype=np.float64)
    q_zero, quality = classify_quality(np.asarray(table["QUALITY"]))
    n = len(time)
    arrays = (time, sap, pdc, mc1, mc2, pos1, pos2, quality)
    if not 0 < n <= 1_000_000 or any(array.shape != (n,) for array in arrays):
        raise ValueError("Empty, oversized or inconsistent FITS columns")
    if not np.any(np.isfinite(time)):
        raise ValueError("No finite time cadences")

    masks = {
        "TIME": np.isfinite(time),
        "SAP_FLUX": np.isfinite(sap) & (sap > 0),
        "PDCSAP_FLUX": np.isfinite(pdc) & (pdc > 0),
        "MOM_CENTR_PAIR": np.isfinite(mc1) & np.isfinite(mc2),
        "POS_CORR_PAIR": np.isfinite(pos1) & np.isfinite(pos2),
    }
    rows = {key: contingency(q_zero, valid) for key, valid in masks.items()}
    if set(rows) != set(MASK_NAMES):
        raise AssertionError("Missing preregistered mask")

    quality_bits = {}
    for bit in range(1, 17):
        flagged = (quality & (1 << (bit - 1))) != 0
        bit_count = int(np.count_nonzero(flagged))
        pdc_count = int(np.count_nonzero(flagged & masks["PDCSAP_FLUX"]))
        moment_count = int(np.count_nonzero(flagged & masks["MOM_CENTR_PAIR"]))
        if any(c > bit_count for c in (pdc_count, moment_count)):
            raise AssertionError("Flag subset count exceeds bit count")
        quality_bits[str(bit)] = {
            "rows": bit_count,
            "with_valid_pdc": pdc_count,
            "with_valid_moment_centroids": moment_count,
        }

    optional = {}
    for key in OPTIONAL_COLUMNS:
        if key not in columns:
            optional[key] = {"present": False}
        else:
            array = np.asarray(table[key], dtype=np.float64)
            if array.shape != (n,):
                raise ValueError("Optional FITS column shape mismatch: " + key)
            optional[key] = {
                "present": True,
                "finite_rows": int(np.count_nonzero(np.isfinite(array))),
            }

    pdc_table = rows["PDCSAP_FLUX"]
    mismatches = {
        "quality_zero_but_pdc_invalid": pdc_table["Q_and_invalid"],
        "quality_flagged_but_pdc_valid": pdc_table["flagged_and_valid"],
    }
    return {
        "total_rows": n,
        "quality_zero_rows": int(np.count_nonzero(q_zero)),
        "quality_flagged_rows": int(np.count_nonzero(~q_zero)),
        "contingency": rows,
        "valid_rows": {key: int(np.count_nonzero(mask)) for key, mask in masks.items()},
        "pdc_quality_zero_equivalent_rowwise": sum(mismatches.values()) == 0,
        "pdc_quality_mismatches": mismatches,
        "quality_bits_1_to_16": quality_bits,
        "optional_centroid_columns": optional,
    }


def inspect_product(path: Path, sector: int) -> dict:
    from astropy.io import fits

    with fits.open(path, memmap=False) as hdus:
        identity = validate_file_identity([h.header for h in hdus], sector)
        if identity["TICID"] != TIC_ID or identity["SECTOR"] != sector:
            raise ValueError("Header identity mismatch")
        tables = [
            h for h in hdus
            if isinstance(h, fits.BinTableHDU) and h.data is not None
            and all(c in (h.columns.names or []) for c in REQUIRED_COLUMNS)
        ]
        if len(tables) != 1:
            raise ValueError("Expected exactly one matching light-curve binary table")
        tab = tables[0]
        columns = tuple(tab.columns.names or [])
        return {
            "header_identity": identity,
            "header_pipeline_version": str(
                next((h.header["PROCVER"] for h in hdus if "PROCVER" in h.header), "")
            ),
            "table_extension": tab.name,
            "column_units": {
                col.name: col.unit for col in tab.columns
                if col.name in REQUIRED_COLUMNS + OPTIONAL_COLUMNS
            },
            "measurements": measure_columns(tab.data, columns),
        }


def percentage(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def compare_results(sector5: dict, sector2: dict) -> dict:
    """Preserve descriptive cross-sector differences, not statistical claims."""
    out = {}
    for sector, item in ((5, sector5), (2, sector2)):
        m = item["fits"]["measurements"]
        t = m["contingency"]["PDCSAP_FLUX"]
        out[str(sector)] = {
            "pdc_valid_given_quality_zero": percentage(
                t["Q_and_valid"], m["quality_zero_rows"]
            ),
            "pdc_valid_given_flagged": percentage(
                t["flagged_and_valid"], m["quality_flagged_rows"]
            ),
            "pdc_quality_equivalent": m["pdc_quality_zero_equivalent_rowwise"],
            "quality_zero_fraction": m["quality_zero_rows"] / m["total_rows"],
        }
    return out


def canonical_sha(payload: dict) -> str:
    raw = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_audit() -> dict:
    import astropy

    report = {
        "protocol": PROTOCOL,
        "version": VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "astropy_version": astropy.__version__,
        "target_tic": TIC_ID,
        "sectors": [5, 2],
        "products": {},
        "hypotheses": {"H1_sector5": "INCONCLUSIVE_SOURCE_ACCESS", "H2_sector2": "INCONCLUSIVE_SOURCE_ACCESS"},
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="arara-obs002-") as work:
            for sector in (5, 2):
                file_path = Path(work) / SOURCES[sector]
                d = fetch_fits(sector, file_path)
                if sector == 5 and d["sha256"] != FROZEN_SECTOR5_SHA256:
                    raise ValueError("Sector 5 differs from the frozen original SHA-256")
                fit = inspect_product(file_path, sector)
                report["products"][str(sector)] = {"download": d, "fits": fit}
        report["gates"].update({f"G{i}": "PASS" for i in range(1, 6)})
        report["comparisons"] = compare_results(
            report["products"]["5"], report["products"]["2"]
        )
        for sector, key in ((5, "H1_sector5"), (2, "H2_sector2")):
            ok = report["products"][str(sector)]["fits"]["measurements"][
                "pdc_quality_zero_equivalent_rowwise"
            ]
            report["hypotheses"][key] = (
                "SUPPORTED_IN_SELECTED_FILE" if ok else "NOT_SUPPORTED_IN_SELECTED_FILE"
            )
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["error_type"] = type(exc).__name__
        report["error_detail"] = str(exc)[:500]
    report["payload_sha256"] = canonical_sha(report)
    return report


def main() -> int:
    import sys

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs002_audit.json")
    result = run_audit()
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "gates": result["gates"],
        "hypotheses": result["hypotheses"],
        "output": str(path),
        "payload_sha256": result["payload_sha256"],
        "error": result.get("error_detail"),
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
