"""AR-OBS001-P01: verify one public TESS light-curve file and its schema.

Protocol frozen before this implementation in
docs/preregistration/AR-OBS001-P01.md.

No transit search, astrophysical classification or event selection is performed.
The source FITS file remains temporary and is not redistributed.
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

PROTOCOL = "AR-OBS001-P01"
SCHEMA_VERSION = "1.0.0"
TIC_ID = 307210830
SECTOR = 5
FILE_NAME = "tess2018319095959-s0005-0000000307210830-0125-s_lc.fits"
ARCHIVE_URL = (
    "https://archive.stsci.edu/missions/tess/tid/s0005/"
    "0000/0003/0721/0830/" + FILE_NAME
)
MAX_BYTES = 32 * 1024 * 1024
REQUIRED_COLUMNS = ("TIME", "SAP_FLUX", "PDCSAP_FLUX", "QUALITY")
OPTIONAL_COLUMNS = (
    "MOM_CENTR1", "MOM_CENTR2", "PSF_CENTR1", "PSF_CENTR2",
    "POS_CORR1", "POS_CORR2", "SAP_BKG",
)


class ArchiveHostRedirect(urllib.request.HTTPRedirectHandler):
    """Reject redirects outside official HTTPS stsci.edu archive hosts."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if (parsed.scheme != "https"
                or not parsed.hostname
                or not parsed.hostname.endswith(".stsci.edu")
                or parsed.username is not None
                or parsed.password is not None):
            raise ValueError("Redirect left the permitted STScI HTTPS archive hosts")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def download_archive_file(destination: Path) -> dict:
    """Download a bounded, named public archive product."""
    opener = urllib.request.build_opener(ArchiveHostRedirect())
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"User-Agent": "ARARA-OBS001/1.0 observational provenance audit"},
    )
    total = 0
    digest = hashlib.sha256()
    with opener.open(request, timeout=60) as response:
        final_url = response.geturl()
        final = urllib.parse.urlparse(final_url)
        if (final.scheme != "https" or not final.hostname
                or not final.hostname.endswith(".stsci.edu")):
            raise ValueError("Unexpected final archive host")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_BYTES:
            raise ValueError("Archive file exceeds the frozen size limit")
        with destination.open("wb") as out:
            while chunk := response.read(256 * 1024):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("Archive file exceeds the frozen size limit")
                digest.update(chunk)
                out.write(chunk)
    if total == 0:
        raise ValueError("Archive response had no bytes")
    return {
        "source_url": ARCHIVE_URL,
        "resolved_url": final_url,
        "file_name": FILE_NAME,
        "download_bytes": total,
        "download_sha256": digest.hexdigest(),
    }


def header_identity(headers: list) -> dict:
    """Require an unambiguous TIC and sector in available FITS headers."""
    result = {}
    for key, required in (("TICID", TIC_ID), ("SECTOR", SECTOR)):
        found = set()
        for header in headers:
            if key in header:
                try:
                    found.add(int(header[key]))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Non-integer {key} FITS header") from exc
        if not found or found != {required}:
            raise ValueError(f"{key} does not match frozen source identity: {sorted(found)}")
        result[key] = required
    return result


def summarize_quality(quality: np.ndarray) -> dict:
    """Count standard 1-indexed TESS quality bits without selecting events."""
    if quality.ndim != 1 or not np.issubdtype(quality.dtype, np.integer):
        raise ValueError("QUALITY must be a one-dimensional integer array")
    if np.any(quality < 0):
        raise ValueError("Negative QUALITY values are outside this audit contract")
    quality = quality.astype(np.int64)
    return {
        "zero_count": int(np.count_nonzero(quality == 0)),
        "nonzero_count": int(np.count_nonzero(quality != 0)),
        "bits_1_to_16": {
            str(bit): int(np.count_nonzero((quality & (1 << (bit - 1))) != 0))
            for bit in range(1, 17)
        },
    }


def finite_positive_counts(values: np.ndarray, good: np.ndarray) -> dict:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 1 or data.shape != good.shape:
        raise ValueError("Unexpected flux or quality shape")
    valid = np.isfinite(data) & (data > 0)
    return {
        "all_rows": int(np.count_nonzero(valid)),
        "quality_zero_rows": int(np.count_nonzero(valid & good)),
    }


def describe_lightcurve(table, columns: tuple[str, ...]) -> dict:
    """Read lengths and missingness, not flux event morphology."""
    missing = sorted(set(REQUIRED_COLUMNS) - set(columns))
    if missing:
        raise ValueError("Missing required columns: " + ",".join(missing))
    time = np.asarray(table["TIME"], dtype=np.float64)
    flux = np.asarray(table["SAP_FLUX"], dtype=np.float64)
    pdc = np.asarray(table["PDCSAP_FLUX"], dtype=np.float64)
    quality = np.asarray(table["QUALITY"])
    n = len(time)
    if not n or n > 1000000 or any(len(a) != n for a in (flux, pdc, quality)):
        raise ValueError("Empty, oversized or inconsistent light-curve arrays")
    if np.count_nonzero(np.isfinite(time)) == 0:
        raise ValueError("No finite timestamps")
    flags = summarize_quality(quality)
    good = quality == 0
    optional = {}
    for key in OPTIONAL_COLUMNS:
        if key in columns:
            array = np.asarray(table[key], dtype=np.float64)
            if array.shape != (n,):
                raise ValueError("Unexpected optional column shape: " + key)
            optional[key] = {
                "available": True,
                "finite_rows": int(np.count_nonzero(np.isfinite(array))),
            }
        else:
            optional[key] = {"available": False}
    return {
        "cadences": n,
        "finite_time_rows": int(np.count_nonzero(np.isfinite(time))),
        "quality": flags,
        "finite_positive_flux_rows": {
            "SAP_FLUX": finite_positive_counts(flux, good),
            "PDCSAP_FLUX": finite_positive_counts(pdc, good),
        },
        "optional_columns": optional,
    }


def inspect_fits(path: Path) -> dict:
    """Check actual FITS identity and measurement availability."""
    from astropy.io import fits

    with fits.open(path, memmap=False) as hdul:
        identity = header_identity([h.header for h in hdul])
        tables = [
            h for h in hdul
            if isinstance(h, (fits.BinTableHDU, fits.TableHDU))
            and h.data is not None
            and all(name in (h.columns.names or []) for name in REQUIRED_COLUMNS)
        ]
        if len(tables) != 1:
            raise ValueError("Expected exactly one light-curve table")
        table = tables[0]
        columns = tuple(table.columns.names or [])
        stats = describe_lightcurve(table.data, columns)
        units = {
            col.name: col.unit for col in table.columns
            if col.name in REQUIRED_COLUMNS + OPTIONAL_COLUMNS
        }
        return {
            "identity": identity,
            "table_extension": table.name,
            "columns": list(columns),
            "units": units,
            "observations": stats,
            "headers": {
                key: str(next(
                    (h.header[key] for h in hdul if key in h.header), ""
                ))
                for key in ("TELESCOP", "INSTRUME", "CAMERA", "CCD", "TIMESYS", "PROCVER")
            },
        }


def canonical_hash(payload: dict) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_audit() -> dict:
    import astropy

    payload = {
        "protocol": PROTOCOL,
        "schema_version": SCHEMA_VERSION,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "astropy_version": astropy.__version__,
        "selection": {
            "mission": "TESS", "sector": SECTOR, "tic_id": TIC_ID,
            "file": FILE_NAME,
        },
        "gates": {
            "download": "NOT_RUN",
            "fits_parse": "NOT_RUN",
            "identity": "NOT_RUN",
            "schema": "NOT_RUN",
        },
    }
    try:
        with tempfile.TemporaryDirectory(prefix="arara-obs001-") as root:
            path = Path(root) / FILE_NAME
            payload["download"] = download_archive_file(path)
            payload["gates"]["download"] = "PASS"
            inspected = inspect_fits(path)
            payload["gates"]["fits_parse"] = "PASS"
            payload["gates"]["identity"] = "PASS"
            payload["gates"]["schema"] = "PASS"
            payload["fits"] = inspected
    except Exception as exc:
        payload["status"] = "FAIL"
        payload["error_category"] = type(exc).__name__
        payload["error_detail"] = str(exc)[:600]
    else:
        payload["status"] = "PASS"
    payload["payload_sha256"] = canonical_hash(payload)
    return payload


def main() -> int:
    import sys

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs001_audit.json")
    report = run_audit()
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "gates": report["gates"],
        "output": str(output),
        "error": report.get("error_detail"),
        "payload_sha256": report["payload_sha256"],
    }, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
