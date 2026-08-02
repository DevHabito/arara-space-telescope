
from pathlib import Path
import json
import sys
import time

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

import arara_m37r as m


index = int(sys.argv[1])
results = root / "results"
holdout_dir = results / "holdouts"
holdout_dir.mkdir(exist_ok=True)

manifest = json.loads(
    (results / "PRE_HOLDOUT_FREEZE_SHA256.json").read_text(
        encoding="utf-8"
    )
)
for relative, expected in manifest.items():
    if m.sha256_file(root / relative) != expected:
        raise RuntimeError(f"pre-holdout freeze mismatch: {relative}")

opened = results / "HOLDOUTS_OPENED.json"
if not opened.exists():
    opened.write_text(
        json.dumps(
            {
                "status": "OPENED_ONCE",
                "holdout_count": 10,
                "control_hypotheses": 396,
                "full_hypotheses": 14652,
                "primary_latency": 4,
                "pooled_calibration_per_family": 200000,
                "thresholds_sha256": m.sha256_file(
                    results / "FROZEN_THRESHOLDS.json"
                ),
                "freeze_manifest_sha256": m.sha256_file(
                    results / "PRE_HOLDOUT_FREEZE_SHA256.json"
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

marker = (
    holdout_dir
    / f"holdout_{index:02d}_method_summary.csv"
)
if marker.exists():
    print(f"holdout {index}: already complete")
    raise SystemExit(0)

cfg = m.Config()
seeds = json.loads(
    (root / "FROZEN_SEEDS.json").read_text(
        encoding="utf-8"
    )
)
thresholds = json.loads(
    (results / "FROZEN_THRESHOLDS.json").read_text(
        encoding="utf-8"
    )
)["thresholds"]

start = time.perf_counter()
output = m.evaluate_holdout(
    cfg,
    seeds["holdouts"][index],
    thresholds,
)

for key, suffix in (
    ("method_summary", "method_summary"),
    ("stratum_summary", "strata"),
    ("negative_summary", "negative"),
    ("batch_summary", "batches"),
    ("pair_counts", "pair_counts"),
    ("paired_summary", "paired"),
    ("identification_summary", "identification"),
    ("timing_detail", "timing"),
    ("negative_selection_summary", "negative_selection"),
    ("projection_diagnostics", "projection"),
):
    output[key].to_csv(
        holdout_dir
        / f"holdout_{index:02d}_{suffix}.csv",
        index=False,
    )

methods = output["method_summary"].set_index("method")
identification = output["identification_summary"].iloc[0]
print(
    f"holdout {index}: "
    f"control={methods.loc['rolling_four_shape_exact_duration_latency4','recall_point']:.5f} "
    f"full={methods.loc['rolling_four_shape_full_duration_bank_latency4','recall_point']:.5f} "
    f"control_strata={int(methods.loc['rolling_four_shape_exact_duration_latency4','good_strata'])}/8 "
    f"full_strata={int(methods.loc['rolling_four_shape_full_duration_bank_latency4','good_strata'])}/8 "
    f"control_pass={bool(methods.loc['rolling_four_shape_exact_duration_latency4','pass'])} "
    f"full_pass={bool(methods.loc['rolling_four_shape_full_duration_bank_latency4','pass'])} "
    f"tol2={identification.duration_tolerance2_accuracy:.5f} "
    f"elapsed={time.perf_counter() - start:.2f}s"
)
