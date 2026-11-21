"""AR-OBS007-P01: refutable incremental engineering-information benchmark.

Methods and thresholds were frozen before implementation in
docs/preregistration/AR-OBS007-P01.md (commit 3856e8c).
Only historical public archival products are read, never committed.
"""

from __future__ import annotations

import hashlib
import json
import platform
import tempfile
from pathlib import Path

import numpy as np

from scripts.ar_obs001_tess_audit import header_identity
from scripts.ar_obs003_pixel_aperture import (
    LC_FROZEN_SHA, TPF_NAME, fetch_product, describe_aperture, validate_ids,
)
from scripts.ar_obs004_pixel_morphology import (
    TPF_FROZEN_SHA, pixel_photocenters,
)
from scripts.ar_obs005_tessvectors_alignment import (
    VECTOR_FILENAME, fetch_vector_csv, parse_lc,
)
from scripts.ar_obs006_quaternion_holdout import (
    ENGINEERING_SHA, load_vector_features,
)

PROTOCOL = "AR-OBS007-P01"
VERSION = "1.0.0"
TARGET = {"TICID": 307210830, "SECTOR": 5, "CAMERA": 4, "CCD": 4}
LAMBDA = 10.0
FRACTION_TRAIN = 0.60
EMBARGO_PER_SIDE = 120
SHIFT_CONTROL = 97
MIN_BLOCK = 500
METHODS = ("MEAN", "AR2", "Q", "AR2_Q", "AR2_Q_SHIFT97")


def build_lagged_examples(
    tp_ids: np.ndarray,
    tp_quality: np.ndarray,
    tp_time: np.ndarray,
    cube: np.ndarray,
    aperture: np.ndarray,
    lc: dict,
    vectors: dict,
) -> dict:
    """Pair true source cadences, never use lags across data gaps."""
    original = validate_ids(np.asarray(tp_ids), np.asarray(tp_quality), np.asarray(tp_time))
    sort_idx = np.argsort(original)
    ids = original[sort_idx]
    quality = np.asarray(tp_quality, dtype=np.int64)[sort_idx]
    time = np.asarray(tp_time, dtype=float)[sort_idx]
    data = np.asarray(cube)[sort_idx]
    if len(ids) != lc["rows"] or not np.array_equal(ids, np.sort(lc["cadences"])):
        raise ValueError("TPF/LC cadence sets differ")
    if data.ndim != 3 or data.shape[0] != len(ids):
        raise ValueError("Malformed pixel cube")
    c_x, c_y, center_ok = pixel_photocenters(data, np.asarray(aperture))
    ilc = {int(k): i for i, k in enumerate(lc["cadences"])}
    li = np.array([ilc[int(i)] for i in ids])
    if not np.array_equal(quality, lc["quality"][li]):
        raise ValueError("TPF/LC quality disagreement")
    if len(vectors["cadences"]) != len(np.unique(vectors["cadences"])):
        raise ValueError("Duplicate engineering cadence")
    ivec = {int(k): i for i, k in enumerate(vectors["cadences"])}
    vi = np.array([ivec.get(int(k), -1) for k in ids])
    vector_match = vi >= 0
    quats = np.full((len(ids), 3), np.nan)
    vtime = np.zeros(len(ids), dtype=bool)
    engineering_ok = np.zeros(len(ids), dtype=bool)
    if np.any(vector_match):
        found = vi[vector_match]
        qmed = vectors["median_features"][found]
        bins = vectors["quat_bins"][found]
        std = vectors["quat_stddev"][found]
        quats[vector_match] = qmed
        vtime[vector_match] = np.isfinite(vectors["midtime"][found])
        engineering_ok[vector_match] = (
            np.isfinite(bins) & (bins > 0)
            & np.all(np.isfinite(std) & (std >= 0), axis=1)
            & np.all(np.isfinite(qmed), axis=1)
        )
    usable = (
        (quality == 0) & np.isfinite(time)
        & np.isfinite(lc["time"][li])
        & vtime & engineering_ok & center_ok
    )
    interval_mask = (np.diff(ids) == 1) & usable[:-1] & usable[1:]
    end_ids = ids[1:][interval_mask]
    motion = np.column_stack((np.diff(c_x), np.diff(c_y)))[interval_mask]
    qdiff = np.diff(quats, axis=0)[interval_mask]
    keep = (
        (end_ids[2:] - end_ids[1:-1] == 1)
        & (end_ids[1:-1] - end_ids[:-2] == 1)
    )
    ends = end_ids[2:][keep]
    y = motion[2:][keep]
    x_ar = np.column_stack((
        motion[1:-1, 0][keep], motion[:-2, 0][keep],
        motion[1:-1, 1][keep], motion[:-2, 1][keep],
    ))
    x_q = qdiff[2:][keep]
    if x_ar.shape != (len(y), 4) or x_q.shape != (len(y), 3):
        raise AssertionError("Lagged design shape mismatch")
    if not (np.isfinite(x_ar).all() and np.isfinite(x_q).all() and np.isfinite(y).all()):
        raise ValueError("Nonfinite eligible model example")
    return {
        "ar": x_ar, "q": x_q, "y": y, "end_cadences": ends,
        "counts": {
            "original_cadences": len(ids),
            "engineered_cadences_matched": int(np.count_nonzero(vector_match)),
            "quality_zero": int(np.count_nonzero(quality == 0)),
            "individual_usable": int(np.count_nonzero(usable)),
            "original_adjacent_cadence_pairs": len(ids) - 1,
            "usable_consecutive_pairs": len(end_ids),
            "pairs_rejected_for_missing_two_consecutive_lags": len(end_ids) - len(y),
            "eligible_lagged_examples": len(y),
        },
    }


def fit_ridge(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, dict]:
    """Training-only feature scaling, unpenalized intercept and frozen ridge."""
    if (train_x.ndim != 2 or test_x.ndim != 2 or train_y.shape != (len(train_x), 2)
            or train_x.shape[1] != test_x.shape[1] or len(train_x) == 0):
        raise ValueError("Malformed ridge matrices")
    if not all(np.isfinite(a).all() for a in (train_x, train_y, test_x)):
        raise ValueError("Missing model values")
    means = np.mean(train_x, axis=0)
    std = np.std(train_x, axis=0)
    zeros = std == 0
    scale = np.where(zeros, 1.0, std)
    ztr = (train_x - means) / scale
    zte = (test_x - means) / scale
    ztr[:, zeros] = 0.0
    zte[:, zeros] = 0.0
    center = np.mean(ztr, axis=0)
    ztr -= center
    zte -= center
    ybar = np.mean(train_y, axis=0)
    beta = np.linalg.solve(
        ztr.T @ ztr + LAMBDA * np.eye(train_x.shape[1]),
        ztr.T @ (train_y - ybar),
    )
    pred = zte @ beta + ybar
    if not np.all(np.isfinite(pred)):
        raise ValueError("Nonfinite model prediction")
    return pred, {"zero_variance_feature_count": int(np.count_nonzero(zeros))}


def evaluate_examples(examples: dict) -> dict:
    """Identical chronological test points for every model; 240-sample embargo."""
    ar = examples["ar"]
    q = examples["q"]
    y = examples["y"]
    n = len(y)
    if ar.shape != (n, 4) or q.shape != (n, 3) or y.shape != (n, 2):
        raise ValueError("Unexpected example matrix")
    boundary = int(np.floor(n * FRACTION_TRAIN))
    train_end = max(0, boundary - EMBARGO_PER_SIDE)
    test_start = min(n, boundary + EMBARGO_PER_SIDE)
    train, test = slice(0, train_end), slice(test_start, n)
    if test_start - train_end != 2 * EMBARGO_PER_SIDE:
        raise ValueError("Insufficient lagged examples to reserve full embargo")
    result = {
        "eligible_examples": n,
        "boundary_before_embargo": boundary,
        "train_examples": train_end,
        "embargo_examples": test_start - train_end,
        "test_examples": n - test_start,
        "test_first_ending_cadence": int(examples["end_cadences"][test_start])
        if n > test_start else None,
        "train_last_ending_cadence": int(examples["end_cadences"][train_end - 1])
        if train_end else None,
        "ridge_lambda": LAMBDA,
        "control_quaternion_shift": SHIFT_CONTROL,
        "methods": {},
        "axes": {},
    }
    result["evaluable"] = train_end >= MIN_BLOCK and n - test_start >= MIN_BLOCK
    if not result["evaluable"]:
        return result
    train_y, test_y = y[train], y[test]
    mean_pred = np.broadcast_to(np.mean(train_y, axis=0), test_y.shape)
    train_ar, test_ar = ar[train], ar[test]
    train_q, test_q = q[train], q[test]
    predictions = {"MEAN": mean_pred}
    meta = {}
    for method, xt, xs in (
        ("AR2", train_ar, test_ar),
        ("Q", train_q, test_q),
        ("AR2_Q", np.column_stack((train_ar, train_q)),
         np.column_stack((test_ar, test_q))),
        ("AR2_Q_SHIFT97",
         np.column_stack((train_ar, np.roll(train_q, SHIFT_CONTROL, axis=0))),
         np.column_stack((test_ar, np.roll(test_q, SHIFT_CONTROL, axis=0)))),
    ):
        predictions[method], meta[method] = fit_ridge(xt, train_y, xs)
    for method in METHODS:
        err = predictions[method] - test_y
        result["methods"][method] = {
            "SSE_x": float(np.sum(err[:, 0] ** 2)),
            "SSE_y": float(np.sum(err[:, 1] ** 2)),
            "MAE_x": float(np.mean(np.abs(err[:, 0]))),
            "MAE_y": float(np.mean(np.abs(err[:, 1]))),
            "zero_variance_training_features": meta.get(method, {}).get(
                "zero_variance_feature_count", 0
            ),
        }
    for axis in ("x", "y"):
        sse_mean = result["methods"]["MEAN"][f"SSE_{axis}"]
        sse_ar = result["methods"]["AR2"][f"SSE_{axis}"]
        sse_aug = result["methods"]["AR2_Q"][f"SSE_{axis}"]
        sse_shift = result["methods"]["AR2_Q_SHIFT97"][f"SSE_{axis}"]
        result["axes"][axis] = {
            "baseline_AR2_SSE": sse_ar,
            "R2_AR2_vs_mean": 1 - sse_ar / sse_mean if sse_mean > 0 else None,
            "R2_Q_vs_mean": (1 - result["methods"]["Q"][f"SSE_{axis}"] / sse_mean)
            if sse_mean > 0 else None,
            "R2_AR2_Q_vs_mean": 1 - sse_aug / sse_mean if sse_mean > 0 else None,
            "incremental_Q_gain_vs_AR2": 1 - sse_aug / sse_ar if sse_ar > 0 else None,
            "shifted_Q_gain_vs_AR2": 1 - sse_shift / sse_ar if sse_ar > 0 else None,
        }
    return result


def verdicts(result: dict) -> dict:
    names = ("H1_x_incremental", "H2_y_incremental", "H3_shift_control")
    if (not result["evaluable"]
            or any(result["axes"].get(axis, {}).get("incremental_Q_gain_vs_AR2") is None
                   for axis in ("x", "y"))):
        return {name: "NOT_EVALUABLE" for name in names}
    x, y = result["axes"]["x"], result["axes"]["y"]
    def extra(row):
        qgain = row["incremental_Q_gain_vs_AR2"]
        shifted = row["shifted_Q_gain_vs_AR2"]
        return qgain >= 0.05 and qgain - shifted >= 0.03
    decisions = (
        extra(x), extra(y),
        x["shifted_Q_gain_vs_AR2"] <= 0.02
        and y["shifted_Q_gain_vs_AR2"] <= 0.02,
    )
    return {
        name: "SUPPORTED_IN_SELECTED_PRODUCTS" if ok else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        for name, ok in zip(names, decisions)
    }


def digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def run() -> dict:
    import astropy
    from astropy.io import fits

    report = {
        "protocol": PROTOCOL, "version": VERSION,
        "python_version": platform.python_version(), "numpy_version": np.__version__,
        "astropy_version": astropy.__version__, "selection": TARGET,
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
        "hypotheses": {name: "INCONCLUSIVE_ACCESS_OR_SCHEMA" for name in
                       ("H1_x_incremental", "H2_y_incremental", "H3_shift_control")},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="ar-obs007-") as temp:
            work = Path(temp)
            tpf = work / TPF_NAME
            lcfile = work / "source_lc.fits"
            csvfile = work / VECTOR_FILENAME
            sources = {
                "TPF": fetch_product("TPF", tpf),
                "LC": fetch_product("LC", lcfile),
                "VECTOR": fetch_vector_csv(csvfile),
            }
            report["sources"] = sources
            if (sources["TPF"]["sha256"] != TPF_FROZEN_SHA
                    or sources["LC"]["sha256"] != LC_FROZEN_SHA
                    or sources["VECTOR"]["sha256"] != ENGINEERING_SHA):
                raise ValueError("Original source hash differs from frozen source")
            report["gates"]["G1"] = "PASS"
            lcv = parse_lc(lcfile)
            vec = load_vector_features(csvfile)
            with fits.open(tpf, memmap=False) as hdus:
                if header_identity([h.header for h in hdus]) != {
                    "TICID": TARGET["TICID"], "SECTOR": TARGET["SECTOR"]
                }:
                    raise ValueError("TPF identity mismatch")
                for field in ("CAMERA", "CCD"):
                    if {int(h.header[field]) for h in hdus if field in h.header} != {TARGET[field]}:
                        raise ValueError("TPF camera/CCD mismatch")
                data = [h for h in hdus if isinstance(h, fits.BinTableHDU)
                        and h.name == "PIXELS" and h.data is not None]
                mask = [h for h in hdus if isinstance(h, fits.ImageHDU)
                        and h.name == "APERTURE" and h.data is not None]
                if len(data) != 1 or len(mask) != 1 or not all(
                    name in (data[0].columns.names or [])
                    for name in ("CADENCENO", "QUALITY", "TIME", "FLUX")
                ):
                    raise ValueError("TPF extension/columns invalid")
                tab = data[0].data
                pixels = np.asarray(tab["FLUX"])
                selected, geometry = describe_aperture(mask[0].data, tuple(pixels.shape[1:]))
                report["gates"]["G2"] = "PASS"
                examples = build_lagged_examples(
                    tab["CADENCENO"], tab["QUALITY"], tab["TIME"],
                    pixels, selected, lcv, vec,
                )
            report["gates"]["G3"] = "PASS"
            metric = evaluate_examples(examples)
            report["gates"]["G4"] = "PASS"
            report["measurements"] = {
                "counts": examples["counts"],
                "aperture": geometry,
                "model": metric,
            }
            report["hypotheses"] = verdicts(metric)
            report["gates"]["G5"] = "PASS"
            report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error_type"] = type(error).__name__
        report["error_detail"] = str(error)[:500]
    report["payload_sha256"] = digest(report)
    return report


def main() -> int:
    import sys
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs007_p01.json")
    result = run()
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "gates": result["gates"],
        "hypotheses": result["hypotheses"], "error": result.get("error_detail"),
        "model": result.get("measurements", {}).get("model", {}).get("axes"),
        "payload_sha256": result["payload_sha256"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
