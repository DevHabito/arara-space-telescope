"""AR-OBS007-P02: preregistered PLD-vs-quaternion correction and dip preservation.

See docs/preregistration/AR-OBS007-P02.md (commit 6635ead), frozen before
implementation. The injection is deliberately idealized; no physical event
labels, planet detections, or production-pipeline improvements are claimed.
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
from scripts.ar_obs004_pixel_morphology import TPF_FROZEN_SHA
from scripts.ar_obs005_tessvectors_alignment import (
    VECTOR_FILENAME, fetch_vector_csv, parse_lc,
)
from scripts.ar_obs006_quaternion_holdout import ENGINEERING_SHA, load_vector_features

PROTOCOL = "AR-OBS007-P02"
VERSION = "1.0.0"
TARGET = {"TICID":307210830, "SECTOR":5, "CAMERA":4, "CCD":4}
TRAIN_FRACTION = 0.60
EMBARGO_SIDE = 120
LAMBDA = 10.0
SHIFT = 97
DEPTH = 0.005
DURATION = 12
FLANK = 12
FIRST_START = 250
SPACING = 500
MIN_BLOCK = 500
METHODS = ("RAW", "PLD1", "PLD1_Q", "PLD1_Q_SHIFT97")


def assemble_eligible(
    tpids: np.ndarray, tpquality: np.ndarray, tptime: np.ndarray,
    cube: np.ndarray, optimal: np.ndarray, lc: dict, vec: dict,
) -> dict:
    """Exact cadence-key join; fail on a true SAP mismatch rather than cherry-pick."""
    source_ids = validate_ids(np.asarray(tpids), np.asarray(tpquality), np.asarray(tptime))
    order = np.argsort(source_ids)
    ids = source_ids[order]
    quality = np.asarray(tpquality, dtype=np.int64)[order]
    time = np.asarray(tptime, dtype=np.float64)[order]
    pix = np.asarray(cube)[order]
    if (pix.ndim != 3 or pix.shape[0] != len(ids)
            or np.asarray(optimal).shape != pix.shape[1:]):
        raise ValueError("Malformed TPF pixel cube or aperture")
    if len(ids) != lc["rows"] or not np.array_equal(ids, np.sort(lc["cadences"])):
        raise ValueError("TPF/LC cadence identifiers differ")
    li_map = {int(k): i for i, k in enumerate(lc["cadences"])}
    li = np.array([li_map[int(k)] for k in ids], dtype=int)
    if not np.array_equal(quality, lc["quality"][li]):
        raise ValueError("LC and TPF quality flags differ")
    if len(vec["cadences"]) != len(np.unique(vec["cadences"])):
        raise ValueError("Duplicate engineering cadence")
    vi_map = {int(k): i for i, k in enumerate(vec["cadences"])}
    vi = np.array([vi_map.get(int(k), -1) for k in ids])
    matched = vi >= 0
    q_features = np.full((len(ids), 3), np.nan)
    q_available = np.zeros(len(ids), dtype=bool)
    midtime_ok = np.zeros(len(ids), dtype=bool)
    if np.any(matched):
        j = vi[matched]
        q_features[matched] = vec["median_features"][j]
        s = vec["quat_stddev"][j]
        n = vec["quat_bins"][j]
        midtime_ok[matched] = np.isfinite(vec["midtime"][j])
        q_available[matched] = (
            np.isfinite(n) & (n > 0)
            & np.all(np.isfinite(s) & (s >= 0), axis=1)
            & np.all(np.isfinite(q_features[matched]), axis=1)
        )
    chosen = np.asarray(optimal)
    pixels = np.asarray(pix[:, chosen], dtype=np.float64)
    pixel_valid = np.all(np.isfinite(pixels), axis=1)
    pixel_total = np.sum(
        np.where(np.isfinite(pixels), pixels, 0.0), axis=1,
    )
    sap = np.asarray(lc["sap_flux"], dtype=np.float64)[li]
    eligible = (
        (quality == 0) & np.isfinite(time) & np.isfinite(lc["time"][li])
        & midtime_ok & q_available & pixel_valid
        & (pixel_total > 0) & np.isfinite(sap) & (sap > 0)
    )
    if not np.any(eligible):
        raise ValueError("No usable source cadences")
    discrepancy = (
        np.abs(pixel_total[eligible] - sap[eligible])
        / np.maximum(np.abs(sap[eligible]), 1.0)
    )
    if not np.isfinite(discrepancy).all() or np.any(discrepancy > .001):
        raise ValueError("SAP reconstruction violates predeclared 0.001 agreement")
    total = pixel_total[eligible]
    features = pixels[eligible] / total[:, None]
    if not np.isfinite(features).all():
        raise ValueError("Nonfinite selected PLD pixel fractions")
    return {
        "cadences": ids[eligible], "sap": sap[eligible],
        "pixels": pixels[eligible], "pld": features,
        "quat": q_features[eligible],
        "counts": {
            "original_cadences": int(len(ids)),
            "quality_zero": int(np.count_nonzero(quality == 0)),
            "vector_matches": int(np.count_nonzero(matched)),
            "eligible": int(np.count_nonzero(eligible)),
            "max_source_sap_relative_discrepancy": float(np.max(discrepancy)),
            "optimal_pixels": int(np.count_nonzero(chosen)),
        },
    }


def partition(n: int) -> dict:
    boundary = int(np.floor(TRAIN_FRACTION * n))
    train_end, test_start = boundary - EMBARGO_SIDE, boundary + EMBARGO_SIDE
    if train_end < 1 or test_start >= n:
        raise ValueError("Not enough rows for frozen embargo")
    return {
        "boundary": boundary, "train_end": train_end,
        "test_start": test_start, "embargo": test_start - train_end,
        "train_rows": train_end, "test_rows": n - test_start,
        "evaluable": train_end >= MIN_BLOCK and n - test_start >= MIN_BLOCK,
    }


def fixed_events(ids: np.ndarray) -> list[int]:
    """Index-only schedule, retaining complete consecutive 12+24 windows."""
    ids = np.asarray(ids)
    starts = []
    for start in range(FIRST_START, len(ids) - DURATION - FLANK + 1, SPACING):
        lower, upper = start - FLANK, start + DURATION + FLANK
        if lower < 0 or upper > len(ids):
            continue
        if np.all(np.diff(ids[lower:upper]) == 1):
            starts.append(start)
    return starts


def injection_mask(n: int, starts: list[int]) -> np.ndarray:
    mask = np.zeros(n, dtype=bool)
    for start in starts:
        if start < 0 or start + DURATION > n:
            raise ValueError("Invalid preregistered injection interval")
        if np.any(mask[start:start+DURATION]):
            raise ValueError("Overlapping injections")
        mask[start:start+DURATION] = True
    return mask


def ridge_predict(xtrain: np.ndarray, ytrain: np.ndarray, xtest: np.ndarray) -> np.ndarray:
    """Fixed ridge with training-only scaling, scalar outcome and intercept."""
    if (xtrain.ndim != 2 or xtest.ndim != 2 or xtrain.shape[1] != xtest.shape[1]
            or ytrain.shape != (len(xtrain),) or len(xtrain) < 1):
        raise ValueError("Malformed PLD design")
    if not all(np.isfinite(a).all() for a in (xtrain, ytrain, xtest)):
        raise ValueError("Nonfinite design matrix")
    mean = np.mean(xtrain, axis=0)
    sigma = np.std(xtrain, axis=0)
    zero = sigma == 0
    scale = np.where(zero, 1.0, sigma)
    ztr = (xtrain - mean) / scale
    zte = (xtest - mean) / scale
    ztr[:, zero] = 0
    zte[:, zero] = 0
    center = np.mean(ztr, axis=0)
    ztr -= center
    zte -= center
    ybar = float(np.mean(ytrain))
    beta = np.linalg.solve(
        ztr.T @ ztr + LAMBDA * np.eye(xtrain.shape[1]),
        ztr.T @ (ytrain - ybar),
    )
    pred = zte @ beta + ybar
    if not np.isfinite(pred).all():
        raise ValueError("Nonfinite ridge prediction")
    return pred


def method_design(method: str, pld: np.ndarray, q: np.ndarray,
                  s: dict) -> tuple[np.ndarray, np.ndarray]:
    """All methods use identical block partition and held-out rows."""
    train, test = slice(0, s["train_end"]), slice(s["test_start"], len(pld))
    if method == "PLD1":
        return pld[train], pld[test]
    if method == "PLD1_Q":
        return np.column_stack((pld[train], q[train])), np.column_stack((pld[test], q[test]))
    if method == "PLD1_Q_SHIFT97":
        return (
            np.column_stack((pld[train], np.roll(q[train], SHIFT, axis=0))),
            np.column_stack((pld[test], np.roll(q[test], SHIFT, axis=0))),
        )
    raise ValueError("Unknown modeled method")


def recovery(difference: np.ndarray, original: np.ndarray,
             test_starts: list[int], normalizer: float) -> dict:
    """Paired-world event depth recovered relative to the known injected signal."""
    ratios: list[float] = []
    for start in test_starts:
        middle = slice(start, start + DURATION)
        flanks = np.r_[difference[start-FLANK:start],
                       difference[start+DURATION:start+DURATION+FLANK]]
        expected = DEPTH * np.mean(original[middle] / normalizer)
        if not np.isfinite(expected) or expected <= 0:
            raise ValueError("Invalid injected event amplitude")
        observed = -(float(np.mean(difference[middle])) - float(np.mean(flanks)))
        ratios.append(observed / expected)
    if not ratios:
        return {"events":0, "median_recovered_fraction":None, "median_abs_error_from_one":None}
    arr = np.asarray(ratios)
    if not np.isfinite(arr).all():
        raise ValueError("Nonfinite injection recovery ratios")
    return {
        "events":len(arr),
        "median_recovered_fraction":float(np.median(arr)),
        "median_abs_error_from_one":float(np.median(np.abs(arr - 1))),
        "min_fraction":float(np.min(arr)),
        "max_fraction":float(np.max(arr)),
    }


def analyze(data: dict) -> dict:
    n = len(data["cadences"])
    split = partition(n)
    if not split["evaluable"]:
        return {"split":split, "evaluable":False, "hypotheses":{
            "H1_incremental_short_timescale":"NOT_EVALUABLE",
            "H2_injection_preservation":"NOT_EVALUABLE",
            "H3_shift_control":"NOT_EVALUABLE",
        }}
    train = slice(0, split["train_end"])
    test = slice(split["test_start"], n)
    test_ids = data["cadences"][test]
    starts_train = fixed_events(data["cadences"][train])
    starts_test = fixed_events(test_ids)
    training_mask = injection_mask(split["train_rows"], starts_train)
    test_mask = injection_mask(split["test_rows"], starts_test)
    mask = np.zeros(n, dtype=bool)
    mask[train] = training_mask
    mask[test] = test_mask
    original_sap = data["sap"]
    original_pixels = data["pixels"]
    pld = data["pld"]
    q = data["quat"]
    # The fixed common-mode photometric challenge leaves the PLD fractions invariant.
    scaled_pixels = original_pixels * (1.0 - DEPTH * mask[:,None])
    scaled_fraction = scaled_pixels / np.sum(scaled_pixels, axis=1)[:,None]
    invariance = float(np.max(np.abs(scaled_fraction - pld)))
    if not np.isfinite(invariance) or invariance > 1e-12:
        raise ValueError("Injected pixel-fraction invariance assumption violated")
    injected_sap = original_sap * (1.0 - DEPTH * mask)
    normalizer = float(np.median(original_sap[train]))
    if not np.isfinite(normalizer) or normalizer <= 0:
        raise ValueError("Invalid training-only SAP normalizer")
    orig = original_sap / normalizer - 1.0
    inj = injected_sap / normalizer - 1.0
    out = {
        "split":split,
        "evaluable":True,
        "injection":{
            "depth":DEPTH,
            "duration_cadences":DURATION,
            "flank_cadences":FLANK,
            "fixed_candidate_start":FIRST_START,
            "fixed_candidate_spacing":SPACING,
            "train_events":len(starts_train),
            "test_events":len(starts_test),
            "max_normalized_pld_fraction_change":invariance,
            "type":"Idealized common-mode multiplicative dimming on all optimal aperture pixels",
        },
        "scatter":{}, "injection_recovery":{}, "hypotheses":{},
    }
    test_consecutive = np.diff(test_ids) == 1
    out["consecutive_test_pairs"] = int(np.count_nonzero(test_consecutive))
    for method in METHODS:
        if method == "RAW":
            orig_resid = orig[test]
            inj_resid = inj[test]
        else:
            xtr, xte = method_design(method, pld, q, split)
            orig_pred = ridge_predict(xtr, orig[train], xte)
            inj_pred = ridge_predict(xtr, inj[train], xte)
            orig_resid = orig[test] - orig_pred
            inj_resid = inj[test] - inj_pred
        diff = np.diff(orig_resid)[test_consecutive]
        rms = float(np.sqrt(np.mean(diff**2))) if len(diff) else None
        out["scatter"][method] = {"point_to_point_rms":rms}
        out["injection_recovery"][method] = recovery(
            inj_resid - orig_resid, original_sap[test], starts_test, normalizer
        )
    q_rms = out["scatter"]["PLD1_Q"]["point_to_point_rms"]
    pld_rms = out["scatter"]["PLD1"]["point_to_point_rms"]
    sh_rms = out["scatter"]["PLD1_Q_SHIFT97"]["point_to_point_rms"]
    gain = 1 - (q_rms / pld_rms)**2 if q_rms is not None and pld_rms and pld_rms > 0 else None
    shift = 1 - (sh_rms / pld_rms)**2 if sh_rms is not None and pld_rms and pld_rms > 0 else None
    out["incremental_squared_rms_gain"] = gain
    out["shifted_squared_rms_gain"] = shift
    if gain is None or shift is None or out["consecutive_test_pairs"] < 100:
        out["hypotheses"]["H1_incremental_short_timescale"] = "NOT_EVALUABLE"
        out["hypotheses"]["H3_shift_control"] = "NOT_EVALUABLE"
    else:
        out["hypotheses"]["H1_incremental_short_timescale"] = (
            "SUPPORTED_IN_SELECTED_PRODUCTS"
            if gain >= .05 and gain - shift >= .03
            else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        )
        out["hypotheses"]["H3_shift_control"] = (
            "SUPPORTED_IN_SELECTED_PRODUCTS" if shift <= .02
            else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        )
    if len(starts_train) < 3 or len(starts_test) < 3:
        out["hypotheses"]["H2_injection_preservation"] = "NOT_EVALUABLE"
    else:
        pld_depth = out["injection_recovery"]["PLD1"]["median_recovered_fraction"]
        q_depth = out["injection_recovery"]["PLD1_Q"]["median_recovered_fraction"]
        out["hypotheses"]["H2_injection_preservation"] = (
            "SUPPORTED_IN_SELECTED_PRODUCTS"
            if .95 <= q_depth <= 1.05 and q_depth >= pld_depth - .03
            else "NOT_SUPPORTED_IN_SELECTED_PRODUCTS"
        )
    return out


def digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def run() -> dict:
    import astropy
    from astropy.io import fits

    report = {
        "protocol":PROTOCOL,"version":VERSION,
        "python_version":platform.python_version(),
        "numpy_version":np.__version__,"astropy_version":astropy.__version__,
        "selection":TARGET,
        "gates":{f"G{i}":"NOT_RUN" for i in range(1,6)},
        "hypotheses":{k:"INCONCLUSIVE_ACCESS_OR_SCHEMA" for k in (
            "H1_incremental_short_timescale",
            "H2_injection_preservation",
            "H3_shift_control",
        )},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="ar-obs007-p02-") as folder:
            root = Path(folder)
            tp_path, lc_path, v_path = root/TPF_NAME, root/"source_lc.fits", root/VECTOR_FILENAME
            sources = {
                "TPF":fetch_product("TPF",tp_path),
                "LC":fetch_product("LC",lc_path),
                "VECTOR":fetch_vector_csv(v_path),
            }
            report["sources"]=sources
            if (sources["TPF"]["sha256"]!=TPF_FROZEN_SHA
                or sources["LC"]["sha256"]!=LC_FROZEN_SHA
                or sources["VECTOR"]["sha256"]!=ENGINEERING_SHA):
                raise ValueError("Pinned source checksum mismatch")
            report["gates"]["G1"]="PASS"
            lc = parse_lc(lc_path)
            with fits.open(lc_path,memmap=False) as hdus:
                light=[h for h in hdus if isinstance(h,fits.BinTableHDU)
                       and h.name=="LIGHTCURVE" and h.data is not None]
                if len(light)!=1 or "SAP_FLUX" not in (light[0].columns.names or []):
                    raise ValueError("No original LC SAP flux")
                lc["sap_flux"]=np.asarray(light[0].data["SAP_FLUX"],dtype=float)
            vec=load_vector_features(v_path)
            with fits.open(tp_path,memmap=False) as hdus:
                if header_identity([h.header for h in hdus])!={"TICID":307210830,"SECTOR":5}:
                    raise ValueError("Wrong public TPF target or sector")
                for name in ("CAMERA","CCD"):
                    if {int(h.header[name]) for h in hdus if name in h.header}!={TARGET[name]}:
                        raise ValueError("Wrong camera or CCD")
                pixel=[h for h in hdus if isinstance(h,fits.BinTableHDU)
                       and h.name=="PIXELS" and h.data is not None]
                mask=[h for h in hdus if isinstance(h,fits.ImageHDU)
                      and h.name=="APERTURE" and h.data is not None]
                if len(pixel)!=1 or len(mask)!=1 or not all(
                    c in (pixel[0].columns.names or []) for c in ("TIME","QUALITY","CADENCENO","FLUX")
                ):
                    raise ValueError("Missing TPF fields")
                tab=pixel[0].data
                cube=np.asarray(tab["FLUX"])
                aperture,geo=describe_aperture(mask[0].data,tuple(cube.shape[1:]))
                if int(np.count_nonzero(aperture))!=21:
                    raise ValueError("Unexpected preregistered aperture size")
                report["gates"]["G2"]="PASS"
                data=assemble_eligible(
                    tab["CADENCENO"],tab["QUALITY"],tab["TIME"],
                    cube,aperture,lc,vec
                )
            report["gates"]["G3"]="PASS"
            outcome=analyze(data)
            report["gates"]["G4"]="PASS"
            report["measurements"]={"counts":data["counts"],"aperture":geo,"benchmark":outcome}
            report["hypotheses"]=outcome["hypotheses"]
            report["gates"]["G5"]="PASS"
            report["status"]="PASS"
    except Exception as error:
        report["status"]="FAIL"
        report["error_type"]=type(error).__name__
        report["error_detail"]=str(error)[:500]
    report["payload_sha256"]=digest(report)
    return report


def main() -> int:
    import sys
    output = Path(sys.argv[1]) if len(sys.argv)>1 else Path("ar_obs007_p02.json")
    result=run()
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    b=result.get("measurements",{}).get("benchmark",{})
    print(json.dumps({
        "status":result["status"],"hypotheses":result["hypotheses"],
        "gates":result["gates"],
        "source_eligible":result.get("measurements",{}).get("counts",{}).get("eligible"),
        "train_events":b.get("injection",{}).get("train_events"),
        "test_events":b.get("injection",{}).get("test_events"),
        "incremental_squared_rms_gain":b.get("incremental_squared_rms_gain"),
        "injection_recovery":b.get("injection_recovery"),
        "error":result.get("error_detail"),
        "payload_sha256":result["payload_sha256"],
    },sort_keys=True))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
