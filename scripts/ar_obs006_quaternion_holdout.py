"""AR-OBS006-P01: chronological holdout of quaternion-to-pixel motion prediction.

The source products, eligibility masks, split, ridge penalty and decision
thresholds were preregistered at docs/preregistration/AR-OBS006-P01.md.
This does not classify astronomical events or infer causal independence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import tempfile
from pathlib import Path

import numpy as np

from scripts.ar_obs001_tess_audit import header_identity
from scripts.ar_obs003_pixel_aperture import (
    LC_FROZEN_SHA,
    TPF_NAME,
    fetch_product,
    describe_aperture,
    validate_ids,
)
from scripts.ar_obs004_pixel_morphology import (
    TPF_FROZEN_SHA,
    pixel_photocenters,
)
from scripts.ar_obs005_tessvectors_alignment import (
    VECTOR_FILENAME,
    fetch_vector_csv,
    parse_vectors,
    parse_lc,
    parse_optional_float,
    parse_integral,
)

PROTOCOL = "AR-OBS006-P01"
VERSION = "1.0.0"
ENGINEERING_SHA = "2aaa3580649782e3c9cb3642bb01101d408a4e2ac09df82e1ef54fa77f6deac8"
TIC_ID = 307210830
SECTOR = 5
CAMERA = 4
CCD = 4
FEATURES = ("Quat1_Med", "Quat2_Med", "Quat3_Med")
TRAIN_FRACTION = 0.60
RIDGE_LAMBDA = 10.0
SHIFT_PAIRS = 97
MIN_SPLIT_PAIRS = 500


def load_vector_features(path: Path) -> dict:
    """Use the already audited CSV parser; additionally retrieve medians in its row order."""
    vec = parse_vectors(path)
    if any(name not in vec["column_names"] for name in FEATURES):
        raise ValueError("Frozen quaternion median feature missing")
    keys = []
    medians = []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        for _ in range(vec["preamble_line_count"]):
            next(source)
        reader = csv.DictReader(source)
        if reader.fieldnames is None or list(reader.fieldnames) != vec["column_names"]:
            raise ValueError("CSV header differs from audited schema")
        for row in reader:
            if not any(str(value).strip() for value in row.values()):
                continue
            if None in row:
                raise ValueError("Malformed engineering CSV row")
            keys.append(parse_integral(row["Cadence"], "Cadence"))
            medians.append([parse_optional_float(row[name]) for name in FEATURES])
    if len(keys) != vec["rows"] or not np.array_equal(vec["cadences"], np.asarray(keys)):
        raise ValueError("Engineering quaternion rows do not match audited cadence keys")
    features = np.asarray(medians, dtype=np.float64)
    if features.shape != (vec["rows"], len(FEATURES)):
        raise ValueError("Unexpected engineering median shape")
    return {**vec, "median_features": features}


def prepare_pairs(tpids, tp_quality, tp_time, pixel_cube, aperture, lc, vec) -> tuple[np.ndarray, np.ndarray, dict]:
    """Assemble frozen consecutive observations from exact integer cadence identities."""
    original_ids = validate_ids(np.asarray(tpids), np.asarray(tp_quality), np.asarray(tp_time))
    if not np.array_equal(np.sort(original_ids), np.sort(lc["cadences"])):
        raise ValueError("TPF and LC have different cadence sets")
    order = np.argsort(original_ids)
    ids = original_ids[order]
    q = np.asarray(tp_quality, dtype=np.int64)[order]
    times = np.asarray(tp_time, dtype=np.float64)[order]
    pixels = np.asarray(pixel_cube)[order]
    selected = np.asarray(aperture)
    if pixels.ndim != 3 or pixels.shape[0] != len(ids):
        raise ValueError("Invalid pixel cube")
    cx, cy, centroid_valid = pixel_photocenters(pixels, selected)
    lc_indices = {int(k): i for i, k in enumerate(lc["cadences"])}
    li = np.array([lc_indices[int(k)] for k in ids], dtype=int)
    if np.any(q != lc["quality"][li]):
        raise ValueError("LC and TPF quality flag mismatch at matched cadence")
    finite_lc_time = np.isfinite(lc["time"][li])
    lookup = {int(k): i for i, k in enumerate(vec["cadences"])}
    vi = np.fromiter((lookup.get(int(k), -1) for k in ids), dtype=int, count=len(ids))
    has_vector = vi >= 0

    quat = np.full((len(ids), len(FEATURES)), np.nan)
    engineering_valid = np.zeros(len(ids), dtype=bool)
    mid_valid = np.zeros(len(ids), dtype=bool)
    if np.any(has_vector):
        known = vi[has_vector]
        quat[has_vector] = vec["median_features"][known]
        mid_valid[has_vector] = np.isfinite(vec["midtime"][known])
        stdev = vec["quat_stddev"][known]
        nb = vec["quat_bins"][known]
        engineering_valid[has_vector] = (
            np.isfinite(nb) & (nb > 0)
            & np.all(np.isfinite(stdev) & (stdev >= 0), axis=1)
            & np.all(np.isfinite(quat[has_vector]), axis=1)
        )

    individual = (
        (q == 0) & np.isfinite(times) & finite_lc_time
        & mid_valid & engineering_valid & centroid_valid
    )
    consecutive = np.diff(ids) == 1
    pair_mask = consecutive & individual[:-1] & individual[1:]
    X = np.diff(quat, axis=0)[pair_mask]
    Y = np.column_stack((np.diff(cx), np.diff(cy)))[pair_mask]
    if X.ndim != 2 or X.shape[1] != 3 or Y.shape != (len(X), 2):
        raise ValueError("Unexpected pair design matrix")
    if not (np.isfinite(X).all() and np.isfinite(Y).all()):
        raise ValueError("A frozen eligible pair contains nonfinite predictors or outcomes")
    counts = {
        "total_tpf_cadences": int(len(ids)),
        "matched_lc_cadences": int(len(ids)),
        "matched_engineering_cadences": int(np.count_nonzero(has_vector)),
        "quality_zero_rows": int(np.count_nonzero(q == 0)),
        "eligible_individual_cadences": int(np.count_nonzero(individual)),
        "eligible_consecutive_pairs": int(np.count_nonzero(pair_mask)),
        "ineligible_or_nonconsecutive_adjacent_rows": int(len(ids) - 1 - np.count_nonzero(pair_mask)),
        "exclusion_tallies_may_overlap": {
            "quality_nonzero": int(np.count_nonzero(q != 0)),
            "TPF_time_nonfinite": int(np.count_nonzero(~np.isfinite(times))),
            "LC_time_nonfinite": int(np.count_nonzero(~finite_lc_time)),
            "engineering_row_absent": int(np.count_nonzero(~has_vector)),
            "engineering_time_missing": int(np.count_nonzero(has_vector & ~mid_valid)),
            "engineering_quaternion_unusable": int(np.count_nonzero(has_vector & ~engineering_valid)),
            "pixel_photocenter_unusable": int(np.count_nonzero(~centroid_valid)),
        },
    }
    if counts["eligible_consecutive_pairs"] + counts["ineligible_or_nonconsecutive_adjacent_rows"] != len(ids) - 1:
        raise AssertionError("Pair accounting discrepancy")
    return X, Y, counts


def ridge_fit_predict(xtrain: np.ndarray, ytrain: np.ndarray, xtest: np.ndarray) -> tuple[np.ndarray, dict]:
    """Fit only on train; intercept not regularized; fixed ridge lambda."""
    if (xtrain.ndim != 2 or xtest.ndim != 2 or ytrain.ndim != 2
            or xtrain.shape[1] != len(FEATURES) or xtest.shape[1] != len(FEATURES)
            or ytrain.shape != (len(xtrain), 2) or len(xtest) == 0 or len(xtrain) == 0):
        raise ValueError("Unexpected training or holdout matrix dimensions")
    if not (np.isfinite(xtrain).all() and np.isfinite(ytrain).all() and np.isfinite(xtest).all()):
        raise ValueError("Nonfinite values in regression input")
    means = np.mean(xtrain, axis=0)
    stds = np.std(xtrain, axis=0)
    zero = stds == 0
    scales = np.where(zero, 1.0, stds)
    ztrain = (xtrain - means) / scales
    ztest = (xtest - means) / scales
    ztrain[:, zero] = 0
    ztest[:, zero] = 0
    center = np.mean(ztrain, axis=0)
    ztrain -= center
    ztest -= center
    ymean = np.mean(ytrain, axis=0)
    coeff = np.linalg.solve(
        ztrain.T @ ztrain + RIDGE_LAMBDA * np.eye(len(FEATURES)),
        ztrain.T @ (ytrain - ymean),
    )
    prediction = ztest @ coeff + ymean
    if not np.isfinite(prediction).all():
        raise ValueError("Ridge returned nonfinite holdout prediction")
    return prediction, {
        "zero_variance_training_feature_count": int(np.count_nonzero(zero)),
        "training_feature_stddev": [float(value) for value in stds],
    }


def holdout_metrics(x: np.ndarray, y: np.ndarray) -> dict:
    if x.ndim != 2 or x.shape != (len(y), 3) or y.ndim != 2 or y.shape[1] != 2:
        raise ValueError("Incompatible predictors/outcomes")
    n = len(y)
    split = int(np.floor(n * TRAIN_FRACTION))
    if split == 0 or split == n:
        return {"train_pairs": split, "holdout_pairs": n - split, "axes": {}, "evaluable": False}
    xtrain, xtest = x[:split], x[split:]
    ytrain, ytest = y[:split], y[split:]
    pred, meta = ridge_fit_predict(xtrain, ytrain, xtest)
    shifted_pred, shift_meta = ridge_fit_predict(
        np.roll(xtrain, SHIFT_PAIRS, axis=0), ytrain,
        np.roll(xtest, SHIFT_PAIRS, axis=0),
    )
    base = np.broadcast_to(np.mean(ytrain, axis=0), ytest.shape)
    out = {"train_pairs": split, "holdout_pairs": n - split, "axes": {},
           "features": FEATURES, "ridge_lambda": RIDGE_LAMBDA,
           "negative_control_shift_pairs": SHIFT_PAIRS,
           "training_parameters": meta,
           "negative_control_training_parameters": shift_meta}
    for axis, col in (("x", 0), ("y", 1)):
        truth = ytest[:, col]
        sse_base = float(np.sum((truth - base[:, col]) ** 2))
        sse_ridge = float(np.sum((truth - pred[:, col]) ** 2))
        sse_shift = float(np.sum((truth - shifted_pred[:, col]) ** 2))
        out["axes"][axis] = {
            "SSE_baseline": sse_base, "SSE_ridge": sse_ridge,
            "SSE_shift97": sse_shift,
            "R2_ridge": 1 - sse_ridge / sse_base if sse_base > 0 else None,
            "R2_shift97": 1 - sse_shift / sse_base if sse_base > 0 else None,
            "MAE_baseline": float(np.mean(np.abs(truth - base[:, col]))),
            "MAE_ridge": float(np.mean(np.abs(truth - pred[:, col]))),
            "MAE_shift97": float(np.mean(np.abs(truth - shifted_pred[:, col]))),
        }
    out["evaluable"] = (split >= MIN_SPLIT_PAIRS and n - split >= MIN_SPLIT_PAIRS
                        and all(out["axes"][a]["R2_ridge"] is not None for a in ("x", "y")))
    return out


def verdicts(metrics: dict) -> dict:
    names = ("H1_x_holdout_prediction", "H2_y_holdout_prediction",
             "H3_shifted_control_specificity")
    if not metrics["evaluable"]:
        return {name: "NOT_EVALUABLE" for name in names}
    x, y = metrics["axes"]["x"], metrics["axes"]["y"]
    def enough(row):
        return row["R2_ridge"] >= .10 and row["R2_ridge"] - row["R2_shift97"] >= .05
    checks = (enough(x), enough(y), x["R2_shift97"] <= .05 and y["R2_shift97"] <= .05)
    return {
        name: ("SUPPORTED_IN_SELECTED_PRODUCTS" if ok else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS")
        for name, ok in zip(names, checks)
    }


def canonical_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run() -> dict:
    import astropy
    from astropy.io import fits

    report = {
        "protocol": PROTOCOL, "implementation_version": VERSION,
        "python_version": platform.python_version(), "numpy_version": np.__version__,
        "astropy_version": astropy.__version__,
        "selection": {"TICID": TIC_ID, "SECTOR": SECTOR, "CAMERA": CAMERA, "CCD": CCD},
        "gates": {f"G{i}": "NOT_RUN" for i in range(1, 6)},
        "hypotheses": {k: "INCONCLUSIVE_ACCESS_OR_SCHEMA" for k in (
            "H1_x_holdout_prediction", "H2_y_holdout_prediction", "H3_shifted_control_specificity"
        )},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="ar-obs006-") as folder:
            path = Path(folder)
            tp_path, lc_path, vector_path = (path / TPF_NAME, path / "lightcurve.fits",
                                              path / VECTOR_FILENAME)
            sources = {
                "TPF": fetch_product("TPF", tp_path),
                "LC": fetch_product("LC", lc_path),
                "VECTOR": fetch_vector_csv(vector_path),
            }
            report["sources"] = sources
            if (sources["TPF"]["sha256"] != TPF_FROZEN_SHA
                    or sources["LC"]["sha256"] != LC_FROZEN_SHA
                    or sources["VECTOR"]["sha256"] != ENGINEERING_SHA):
                raise ValueError("Archival bytes do not match preregistered source SHA-256")
            report["gates"]["G1"] = "PASS"
            lc = parse_lc(lc_path)
            vec = load_vector_features(vector_path)
            with fits.open(tp_path, memmap=False) as tpf:
                if header_identity([h.header for h in tpf]) != {"TICID": TIC_ID, "SECTOR": SECTOR}:
                    raise ValueError("TPF header identity mismatch")
                camera = {int(h.header["CAMERA"]) for h in tpf if "CAMERA" in h.header}
                ccd = {int(h.header["CCD"]) for h in tpf if "CCD" in h.header}
                if camera != {CAMERA} or ccd != {CCD}:
                    raise ValueError("TPF camera or CCD mismatch")
                pixels = [h for h in tpf if isinstance(h, fits.BinTableHDU)
                          and h.name == "PIXELS" and h.data is not None]
                apertures = [h for h in tpf if isinstance(h, fits.ImageHDU)
                             and h.name == "APERTURE" and h.data is not None]
                if len(pixels) != 1 or len(apertures) != 1:
                    raise ValueError("Expected unique PIXELS and APERTURE extensions")
                p = pixels[0].data
                for c in ("CADENCENO", "TIME", "QUALITY", "FLUX"):
                    if c not in (pixels[0].columns.names or []):
                        raise ValueError("Missing TPF column: " + c)
                flux = np.asarray(p["FLUX"])
                selected, aperture_data = describe_aperture(
                    apertures[0].data, tuple(flux.shape[1:])
                )
                report["gates"]["G2"] = "PASS"
                X, Y, counts = prepare_pairs(
                    p["CADENCENO"], p["QUALITY"], p["TIME"], flux,
                    selected, lc, vec,
                )
                report["gates"]["G3"] = "PASS"
            metrics = holdout_metrics(X, Y)
            report["gates"]["G4"] = "PASS"
            report["measurements"] = {"counts": counts, "aperture": aperture_data,
                                      "model": metrics}
            report["hypotheses"] = verdicts(metrics)
            report["gates"]["G5"] = "PASS"
            report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["error_type"] = type(exc).__name__
        report["error_detail"] = str(exc)[:500]
    report["payload_sha256"] = canonical_hash(report)
    return report


def main() -> int:
    import sys
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ar_obs006_audit.json")
    result = run()
    output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "gates": result["gates"],
        "hypotheses": result["hypotheses"],
        "train_pairs": result.get("measurements", {}).get("model", {}).get("train_pairs"),
        "holdout_pairs": result.get("measurements", {}).get("model", {}).get("holdout_pairs"),
        "error": result.get("error_detail"),
        "digest": result["payload_sha256"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
