from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

from .synthetic import generate_dataset, SyntheticSample
from .detectors import flux_z_score, cusum_score, dp1_reconstructed_score
from .evaluation import evaluate_precomputed
from .math_core import (
    photon_count_flat_fnu,
    photon_count_numeric,
    snr_aperture,
    encircled_energy_offset_gaussian,
    binomial_tail,
    beta_binomial_tail,
    ppv,
    raw_data_volume_bytes,
)


def score_functions():
    return {
        "Flux-z": lambda s: flux_z_score(s.flux),
        "CUSUM": lambda s: cusum_score(s.flux),
        "DP1-R_external": lambda s: dp1_reconstructed_score(s.flux, s.cadence_s),
    }


def aggregate_seed_results(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [c for c in df.columns if c not in {"seed", "method", "target_fpr", "health_gate"}]
    rows = []
    for keys, g in df.groupby(["method", "target_fpr", "health_gate"], dropna=False):
        row = {"method": keys[0], "target_fpr": keys[1], "health_gate": keys[2]}
        for m in metrics:
            vals = pd.to_numeric(g[m], errors="coerce").dropna().to_numpy()
            row[f"{m}_median"] = float(np.median(vals)) if len(vals) else np.nan
            row[f"{m}_p05"] = float(np.quantile(vals, 0.05)) if len(vals) else np.nan
            row[f"{m}_p95"] = float(np.quantile(vals, 0.95)) if len(vals) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def main(out_dir: str | Path = "results") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seeds = [1103, 2207, 3301, 4409, 5519, 6619]
    rows = []
    for seed in seeds:
        train = generate_dataset(seed, n_per_class=100)
        test = generate_dataset(seed + 1_000_000, n_per_class=200)
        for method, fn in score_functions().items():
            train_scores = [fn(s) for s in train]
            test_scores = [fn(s) for s in test]
            for target in (0.01, 0.05):
                for gate in (False, True):
                    r = evaluate_precomputed(train, test, train_scores, test_scores, target_fpr=target, use_health_gate=gate)
                    rows.append({
                        "seed": seed,
                        "method": method,
                        "target_fpr": target,
                        "health_gate": gate,
                        **r.__dict__,
                    })
    seed_df = pd.DataFrame(rows)
    agg_df = aggregate_seed_results(seed_df)
    seed_df.to_csv(out / "synthetic_by_seed.csv", index=False)
    agg_df.to_csv(out / "synthetic_aggregate.csv", index=False)

    # FLOCK: old event-window FPR cannot be promoted to candidate coincidence probability.
    # We therefore publish a sensitivity grid over explicit candidate-level p_false.
    flock_rows = []
    p_true_grid = [0.10, 0.25, 0.50]
    p_false_grid = [1e-4, 1e-3, 1e-2, 5e-2]
    for n, m in [(3, 2), (5, 3), (7, 4)]:
        for p_t in p_true_grid:
            for p_f in p_false_grid:
                for rho_t in [0.0, 0.1, 0.3]:
                    for rho_f in [0.0, 0.1, 0.3]:
                        tpr_eff = beta_binomial_tail(n, m, p_t, rho_t)
                        fpr_eff = beta_binomial_tail(n, m, p_f, rho_f)
                        for prevalence in [1e-2, 1e-3, 1e-4]:
                            flock_rows.append({
                                "n": n, "m": m,
                                "p_true_candidate": p_t,
                                "p_false_candidate": p_f,
                                "rho_true": rho_t,
                                "rho_false": rho_f,
                                "prevalence": prevalence,
                                "tpr_effective": tpr_eff,
                                "fpr_effective": fpr_eff,
                                "ppv": ppv(prevalence, tpr_eff, fpr_eff),
                            })
    pd.DataFrame(flock_rows).to_csv(out / "flock_sensitivity.csv", index=False)

    # Analytic optics examples: explicitly assumption-driven, not a closed payload.
    optics_rows = []
    for mag in [10, 12, 14, 16, 18]:
        params = dict(
            magnitude_ab=float(mag), diameter_m=0.10, exposure_s=120.0,
            lambda_min_m=600e-9, lambda_max_m=1000e-9, throughput=0.35,
        )
        source = photon_count_flat_fnu(**params)
        numeric = photon_count_numeric(**params)
        optics_rows.append({
            "magnitude_ab": mag,
            "source_e_flat_fnu": source,
            "numeric_relative_error": abs(source - numeric) / source,
            "snr_example_low_background": snr_aperture(source, 20.0, 0.2, 3.0, 25.0),
        })
    pd.DataFrame(optics_rows).to_csv(out / "photon_snr_examples.csv", index=False)

    jitter_rows = []
    for offset_sigma in np.linspace(0, 4, 17):
        jitter_rows.append({
            "offset_sigma": offset_sigma,
            "encircled_energy_R_3sigma": encircled_energy_offset_gaussian(3.0, 1.0, float(offset_sigma)),
        })
    pd.DataFrame(jitter_rows).to_csv(out / "jitter_encircled_energy.csv", index=False)

    data_volume = raw_data_volume_bytes(2048, 2048, 16, 432)
    audit = {
        "status": "independent_reconstruction_not_legacy_reproduction",
        "legacy_numbers_reused": False,
        "synthetic_seeds": seeds,
        "train_per_class_per_seed": 100,
        "test_per_class_per_seed": 200,
        "baseline_contract": "first 36 samples are before every synthetic onset",
        "auc_window_contract": "same baseline-to-reference window rule for events and non-events",
        "lead_time_contract": "first threshold crossing, never argmax",
        "housekeeping_contract": "latent instrument process generated independently of astrophysical class",
        "flock_warning": "candidate-level false coincidence probability is not identifiable from event-window FPR; sensitivity grid only",
        "raw_data_volume_bytes_example": data_volume,
    }
    (out / "audit_manifest.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    # Human-readable first report.
    report = [
        "# ARARA independent reconstruction v0.1 — execution report",
        "",
        "This package does not reproduce the deleted implementation. It reconstructs an auditable model from the published equations and explicitly rejects undocumented numerical inheritance.",
        "",
        "## Contracts enforced",
        "- Equal pre-reference evaluation rule for positive and negative samples.",
        "- Clean baseline before every synthetic event onset.",
        "- Lead time from the first threshold crossing.",
        "- Housekeeping generated from a latent instrument process independent of astrophysical class.",
        "- Validated library implementations for AUROC and average precision.",
        "- FLOCK reported only as a candidate-level sensitivity analysis.",
        "",
        "## Aggregate synthetic results",
        agg_df.to_markdown(index=False),
        "",
        "## Interpretation boundary",
        "Synthetic performance only tests internal consistency of the reconstructed pipeline. It is not evidence of real-sky performance or mission feasibility.",
        "",
        "The 6U/12U legacy power verdict is not reissued because component-level input distributions were not preserved. The package keeps only a dimensionally correct energy-accounting function and unit tests.",
    ]
    (out / "EXECUTION_REPORT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
