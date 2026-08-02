
from pathlib import Path
import json
import sys
import time

import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

import arara_m37r as m


family = sys.argv[1]
block_index = int(sys.argv[2])
chunk_index = int(sys.argv[3])
chunk_size = int(sys.argv[4]) if len(sys.argv) > 4 else 10_000

cfg = m.Config()
if family not in m.NEGATIVE_FAMILIES:
    raise ValueError(family)
if not 0 <= block_index < cfg.calibration_block_count:
    raise ValueError(block_index)
if chunk_size % cfg.calibration_batch_size:
    raise ValueError(
        "chunk_size must be divisible by the frozen batch size."
    )

results = root / "results"
chunk_dir = results / "calibration_chunks"
chunk_dir.mkdir(exist_ok=True)

chunk_path = (
    chunk_dir
    / f"{family}_block_{block_index:02d}_chunk_{chunk_index:02d}.npz"
)
state_path = (
    chunk_dir
    / f"{family}_block_{block_index:02d}_state_{chunk_index:02d}.json"
)
if chunk_path.exists() and state_path.exists():
    print(
        f"{family} block {block_index} chunk {chunk_index}: already complete"
    )
    raise SystemExit(0)

manifest = json.loads(
    (results / "PRE_CALIBRATION_FREEZE_SHA256.json").read_text(
        encoding="utf-8"
    )
)
for relative, expected in manifest.items():
    if m.sha256_file(root / relative) != expected:
        raise RuntimeError(f"freeze mismatch: {relative}")

plan = json.loads(
    (root / "FROZEN_SEEDS.json").read_text(
        encoding="utf-8"
    )
)

if chunk_index == 0:
    rng = np.random.default_rng(
        plan["calibration_blocks"][str(block_index)][family][
            "integer_seed"
        ]
    )
else:
    prior_state = (
        chunk_dir
        / f"{family}_block_{block_index:02d}_state_{chunk_index - 1:02d}.json"
    )
    if not prior_state.exists():
        raise RuntimeError(f"missing prior state: {prior_state}")
    rng = np.random.default_rng()
    rng.bit_generator.state = json.loads(
        prior_state.read_text(encoding="utf-8")
    )

core = m.calibration_core(cfg)
pieces = {
    key: []
    for key in (
        "score_rolling_four_shape_exact_duration_latency4",
        "score_rolling_four_shape_full_duration_bank_latency4",
        "control_argmax_endpoint",
        "full_argmax_endpoint",
        "full_argmax_shape_index",
        "full_argmax_duration",
        "true_shape_index",
        "true_duration",
        "control_energy_at_max",
        "full_energy_at_max",
    )
}

remaining = chunk_size
start = time.perf_counter()
while remaining > 0:
    n = min(cfg.calibration_batch_size, remaining)
    output = m.evaluate_negative_family(
        family,
        n,
        rng,
        cfg,
        core,
    )
    control_grid = output["control_score_grid"]
    full_grid = output["full_score_grid"]
    control_argmax = np.argmax(control_grid, axis=1)
    full_argmax = np.argmax(full_grid, axis=1)
    row = np.arange(n)

    pieces[
        "score_rolling_four_shape_exact_duration_latency4"
    ].append(
        control_grid[row, control_argmax].astype(np.float32)
    )
    pieces[
        "score_rolling_four_shape_full_duration_bank_latency4"
    ].append(
        full_grid[row, full_argmax].astype(np.float32)
    )
    pieces["control_argmax_endpoint"].append(
        cfg.endpoint_grid[control_argmax].astype(np.int16)
    )
    pieces["full_argmax_endpoint"].append(
        cfg.endpoint_grid[full_argmax].astype(np.int16)
    )
    pieces["full_argmax_shape_index"].append(
        output["full_shape_index_grid"][
            row,
            full_argmax,
        ].astype(np.int8)
    )
    pieces["full_argmax_duration"].append(
        output["full_duration_grid"][
            row,
            full_argmax,
        ].astype(np.int16)
    )
    pieces["true_shape_index"].append(
        output["true_shape_index"].astype(np.int8)
    )
    pieces["true_duration"].append(
        output["true_duration"].astype(np.int16)
    )
    pieces["control_energy_at_max"].append(
        output["control_energy_grid"][
            row,
            control_argmax,
        ].astype(np.float32)
    )
    pieces["full_energy_at_max"].append(
        output["full_energy_grid"][
            row,
            full_argmax,
        ].astype(np.float32)
    )
    remaining -= n

arrays = {
    key: np.concatenate(values)
    for key, values in pieces.items()
}
np.savez_compressed(chunk_path, **arrays)
state_path.write_text(
    json.dumps(rng.bit_generator.state),
    encoding="utf-8",
)

print(
    f"{family} block {block_index} chunk {chunk_index}: "
    f"n={chunk_size} elapsed={time.perf_counter() - start:.2f}s"
)
