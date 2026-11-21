"""AR-OBS004-P01: pixel photocenter, pointing-proxy and background-mask audit.

Protocol frozen first at docs/preregistration/AR-OBS004-P01.md.
No transit search, event labeling, pixel-image redistribution or classifier fitting.
"""

from __future__ import annotations

import hashlib
import json
import platform
import tempfile
from pathlib import Path

import numpy as np

from scripts.ar_obs003_pixel_aperture import (
    LC_FROZEN_SHA,
    SECTOR,
    TIC_ID,
    TPF_NAME,
    LC_NAME,
    describe_aperture,
    fetch_product,
    validate_ids,
)
from scripts.ar_obs001_tess_audit import header_identity

PROTOCOL = "AR-OBS004-P01"
VERSION = "1.0.0"
TPF_FROZEN_SHA = "c3e5fea929c73e81beac06deee6ff5c24af76d78f258aef2cf448a449bbcef4b"
TPF_COLUMNS = ("TIME", "CADENCENO", "QUALITY", "FLUX", "FLUX_BKG", "POS_CORR1", "POS_CORR2")
LC_COLUMNS = ("TIME", "CADENCENO", "QUALITY")
SHIFT = 24


def pixel_photocenters(flux: np.ndarray, aperture: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Local positive-clipped pixel photocenters, no flux-derived tuning."""
    pix = np.asarray(flux)
    sel = np.asarray(aperture)
    if pix.ndim != 3 or sel.ndim != 2 or sel.dtype != np.bool_ or pix.shape[1:] != sel.shape or not np.any(sel):
        raise ValueError("Pixel cube and selected optimal aperture are incompatible")
    if len(pix) < 1:
        raise ValueError("Empty pixel cube")
    selected_flux = np.asarray(pix[:, sel], dtype=np.float64)
    finite = np.all(np.isfinite(selected_flux), axis=1)
    weighted = np.maximum(np.where(np.isfinite(selected_flux), selected_flux, 0.0), 0.0)
    denominator = np.sum(weighted, axis=1)
    valid = finite & (denominator > 0) & np.isfinite(denominator)
    y_coords, x_coords = np.nonzero(sel)
    cx = np.full(len(pix), np.nan)
    cy = np.full(len(pix), np.nan)
    cx[valid] = (weighted[valid] @ x_coords.astype(float)) / denominator[valid]
    cy[valid] = (weighted[valid] @ y_coords.astype(float)) / denominator[valid]
    if not (np.all(np.isfinite(cx[valid])) and np.all(np.isfinite(cy[valid]))):
        raise ValueError("Nonfinite centroid for an eligible row")
    return cx, cy, valid


def background_medians(bkg: np.ndarray, background_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Median pipeline-estimated background on fixed bit-three mask."""
    pix = np.asarray(bkg)
    sel = np.asarray(background_mask)
    if pix.ndim != 3 or sel.ndim != 2 or pix.shape[1:] != sel.shape or sel.dtype != np.bool_ or not np.any(sel):
        raise ValueError("No valid background-mask pixels")
    values = np.asarray(pix[:, sel], dtype=np.float64)
    finite = np.all(np.isfinite(values), axis=1)
    medians = np.full(len(pix), np.nan)
    medians[finite] = np.median(values[finite], axis=1)
    return medians, finite


def correlation(x: np.ndarray, y: np.ndarray) -> float | None:
    """Return a descriptive Pearson correlation, not a p-value."""
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or len(a) < 100:
        return None
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("Nonfinite input in matched correlation vectors")
    a = a - np.mean(a)
    b = b - np.mean(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom <= 0 or not np.isfinite(denom):
        return None
    value = float(a @ b / denom)
    return max(-1.0, min(1.0, value))


def summarize_movement(
    cadences: np.ndarray, quality: np.ndarray, times: np.ndarray,
    cx: np.ndarray, cy: np.ndarray, valid_centroid: np.ndarray,
    pos1: np.ndarray, pos2: np.ndarray,
) -> dict:
    n = len(cadences)
    if any(np.asarray(a).shape != (n,) for a in (quality, times, cx, cy, valid_centroid, pos1, pos2)):
        raise ValueError("Inconsistent movement array shapes")
    q = np.asarray(quality)
    usable = (
        (q == 0) & np.isfinite(times) & valid_centroid
        & np.isfinite(pos1) & np.isfinite(pos2)
    )
    pair_mask = usable[:-1] & usable[1:] & (np.diff(cadences) == 1)
    # The same pair mask is used for x and y, including shift controls.
    dx = np.diff(cx)[pair_mask]
    dy = np.diff(cy)[pair_mask]
    dp1 = np.diff(pos1)[pair_mask]
    dp2 = np.diff(pos2)[pair_mask]
    rx = correlation(dx, dp1)
    ry = correlation(dy, dp2)
    sx = correlation(dx, np.roll(dp1, SHIFT))
    sy = correlation(dy, np.roll(dp2, SHIFT))
    return {
        "usable_individual_rows": int(np.count_nonzero(usable)),
        "eligible_consecutive_pairs": int(np.count_nonzero(pair_mask)),
        "nonconsecutive_or_ineligible_adjacent_rows": int((n - 1) - np.count_nonzero(pair_mask)),
        "x": {"r_zero_lag": rx, "r_shift24": sx},
        "y": {"r_zero_lag": ry, "r_shift24": sy},
    }


def summarize_background(background: np.ndarray, finite: np.ndarray, quality: np.ndarray) -> dict:
    q = np.asarray(quality)
    b = np.asarray(background, dtype=np.float64)
    good = np.asarray(finite)
    if any(arr.ndim != 1 or arr.shape != q.shape for arr in (b, good)):
        raise ValueError("Unexpected background and quality vector shapes")
    groups = {
        "QUALITY_ZERO": q == 0,
        "BIT_6_DESATURATION": (q & (1 << (6 - 1))) != 0,
        "BIT_13_SCATTERED_LIGHT": (q & (1 << (13 - 1))) != 0,
    }
    result = {}
    for name, mask in groups.items():
        subset = mask & good
        result[name] = {
            "total_rows": int(np.count_nonzero(mask)),
            "finite_background_rows": int(np.count_nonzero(subset)),
            "median_estimated_background": float(np.median(b[subset]))
            if np.any(subset) else None,
        }
    a = result["QUALITY_ZERO"]
    b13 = result["BIT_13_SCATTERED_LIGHT"]
    diff = (
        b13["median_estimated_background"] - a["median_estimated_background"]
        if (b13["median_estimated_background"] is not None
            and a["median_estimated_background"] is not None)
        else None
    )
    result["bit13_minus_quality_zero_median"] = diff
    return result


def verdicts(movement: dict, background: dict) -> dict:
    answers = {}
    pairs = movement["eligible_consecutive_pairs"]
    for axis, key in (("x", "H1_x_movement_association"), ("y", "H2_y_movement_association")):
        r0 = movement[axis]["r_zero_lag"]
        rshift = movement[axis]["r_shift24"]
        if pairs < 100 or r0 is None or rshift is None:
            answers[key] = "NOT_EVALUABLE"
        else:
            accepted = abs(r0) >= 0.20 and abs(r0) - abs(rshift) >= 0.10
            answers[key] = "SUPPORTED_IN_SELECTED_PRODUCT" if accepted else "NOT_SUPPORTED_IN_SELECTED_PRODUCT"
    a = background["QUALITY_ZERO"]
    f = background["BIT_13_SCATTERED_LIGHT"]
    if a["finite_background_rows"] < 100 or f["finite_background_rows"] < 30:
        answers["H3_background_flag_selection"] = "NOT_EVALUABLE"
    else:
        yes = background["bit13_minus_quality_zero_median"] > 0
        answers["H3_background_flag_selection"] = (
            "SUPPORTED_IN_SELECTED_PRODUCT" if yes else "NOT_SUPPORTED_IN_SELECTED_PRODUCT"
        )
    return answers


def inspect_files(tpf: Path, lcf: Path) -> dict:
    from astropy.io import fits

    with fits.open(tpf, memmap=False) as tp, fits.open(lcf, memmap=False) as lc:
        if header_identity([h.header for h in tp]) != {"TICID": TIC_ID, "SECTOR": SECTOR}:
            raise ValueError("Unexpected TPF target/sector")
        if header_identity([h.header for h in lc]) != {"TICID": TIC_ID, "SECTOR": SECTOR}:
            raise ValueError("Unexpected LC target/sector")
        pixel = [h for h in tp if isinstance(h, fits.BinTableHDU) and h.name == "PIXELS" and h.data is not None]
        light = [h for h in lc if isinstance(h, fits.BinTableHDU) and h.name == "LIGHTCURVE" and h.data is not None]
        mask_hdus = [h for h in tp if isinstance(h, fits.ImageHDU) and h.name == "APERTURE" and h.data is not None]
        if len(pixel) != 1 or len(light) != 1 or len(mask_hdus) != 1:
            raise ValueError("Expected one PIXELS, LIGHTCURVE and APERTURE extension")
        p, l = pixel[0].data, light[0].data
        if not all(name in (pixel[0].columns.names or []) for name in TPF_COLUMNS):
            raise ValueError("TPF missing required pixel/background/position column")
        if not all(name in (light[0].columns.names or []) for name in LC_COLUMNS):
            raise ValueError("LC missing cadence/quality/time columns")
        tpids = validate_ids(np.asarray(p["CADENCENO"]), np.asarray(p["QUALITY"]), np.asarray(p["TIME"]))
        lcids = validate_ids(np.asarray(l["CADENCENO"]), np.asarray(l["QUALITY"]), np.asarray(l["TIME"]))
        if len(tpids) != len(lcids) or not np.array_equal(np.sort(tpids), np.sort(lcids)):
            raise ValueError("TPF/LC cadence mismatch; no silent row imputation")
        lc_index = {int(cadence): i for i, cadence in enumerate(lcids)}
        matching = np.array([lc_index[int(cadence)] for cadence in tpids], dtype=int)
        if np.count_nonzero(np.asarray(p["QUALITY"]) != np.asarray(l["QUALITY"])[matching]):
            raise ValueError("Quality mismatch on the same cadence")
        flux = np.asarray(p["FLUX"])
        bkg = np.asarray(p["FLUX_BKG"])
        if flux.ndim != 3 or flux.shape != bkg.shape or flux.shape[0] != len(tpids):
            raise ValueError("Invalid TPF cube dimensions")
        selected, aperture = describe_aperture(mask_hdus[0].data, tuple(flux.shape[1:]))
        bmask = (np.asarray(mask_hdus[0].data) & 4) != 0
        cx, cy, goodphot = pixel_photocenters(flux, selected)
        estimated_bkg, finite_bkg = background_medians(bkg, bmask)
        quality = np.asarray(p["QUALITY"], dtype=np.int64)
        movement = summarize_movement(
            tpids, quality, np.asarray(p["TIME"], dtype=float),
            cx, cy, goodphot,
            np.asarray(p["POS_CORR1"], dtype=float),
            np.asarray(p["POS_CORR2"], dtype=float),
        )
        background = summarize_background(estimated_bkg, finite_bkg, quality)
        if movement["eligible_consecutive_pairs"] > len(tpids) - 1:
            raise AssertionError("Invalid consecutive-pair accounting")
        return {
            "cadences": len(tpids),
            "pixel_shape": list(flux.shape),
            "aperture": aperture,
            "finite_positive_centroid_rows": int(np.count_nonzero(goodphot)),
            "finite_background_rows": int(np.count_nonzero(finite_bkg)),
            "quality_zero_rows": int(np.count_nonzero(quality == 0)),
            "quality_flagged_rows": int(np.count_nonzero(quality != 0)),
            "matched_cadences": len(tpids),
            "movement": movement,
            "background": background,
            "hypotheses": verdicts(movement, background),
            "source_column_units": {
                col.name: col.unit for col in pixel[0].columns
                if col.name in ("FLUX", "FLUX_BKG", "POS_CORR1", "POS_CORR2")
            },
        }


def digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def run() -> dict:
    import astropy

    report = {
        "protocol": PROTOCOL, "implementation_version": VERSION,
        "python_version": platform.python_version(), "numpy_version": np.__version__,
        "astropy_version": astropy.__version__,
        "source_names": {"TPF": TPF_NAME, "LC": LC_NAME},
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
        "hypotheses": {k: "INCONCLUSIVE_ACCESS_OR_SCHEMA" for k in (
            "H1_x_movement_association", "H2_y_movement_association",
            "H3_background_flag_selection",
        )},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="ar-obs004-") as folder:
            tp_path = Path(folder) / TPF_NAME
            lc_path = Path(folder) / LC_NAME
            tp_source = fetch_product("TPF", tp_path)
            lc_source = fetch_product("LC", lc_path)
            report["sources"] = {"TPF": tp_source, "LC": lc_source}
            if tp_source["sha256"] != TPF_FROZEN_SHA or lc_source["sha256"] != LC_FROZEN_SHA:
                raise ValueError("Original FITS source bytes differ from frozen SHA")
            report["gates"]["G1"] = "PASS"
            observed = inspect_files(tp_path, lc_path)
            report["gates"].update({f"G{i}": "PASS" for i in range(2, 6)})
            report["measurements"] = observed
            report["hypotheses"] = observed["hypotheses"]
            report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error_type"] = type(error).__name__
        report["error_detail"] = str(error)[:500]
    report["payload_sha256"] = digest(report)
    return report


def main() -> int:
    import sys

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs004_audit.json")
    result = run()
    path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "hypotheses": result["hypotheses"],
        "gates": result["gates"], "error": result.get("error_detail"),
        "payload_sha256": result["payload_sha256"], "output": str(path),
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
