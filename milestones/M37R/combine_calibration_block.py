
from pathlib import Path
import sys

import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

import arara_m37r as m


family = sys.argv[1]
block_index = int(sys.argv[2])
cfg = m.Config()

chunk_dir = root / "results" / "calibration_chunks"
block_dir = root / "results" / "calibration_blocks"
block_dir.mkdir(exist_ok=True)

paths = sorted(
    chunk_dir.glob(
        f"{family}_block_{block_index:02d}_chunk_*.npz"
    )
)
if not paths:
    raise RuntimeError("No chunks found.")

expected_chunk_count = (
    cfg.calibration_negatives_per_block
    // 10_000
)
if len(paths) != expected_chunk_count:
    raise RuntimeError(
        f"Expected {expected_chunk_count} chunks, found {len(paths)}."
    )

arrays = m.combine_calibration_blocks(
    paths,
    expected_per_block=10_000,
    expected_total=cfg.calibration_negatives_per_block,
)
output = (
    block_dir
    / f"{family}_block_{block_index:02d}.npz"
)
np.savez_compressed(output, **arrays)
print(
    f"{family} block {block_index}: "
    f"n={len(next(iter(arrays.values())))} "
    f"size={output.stat().st_size / 1024**2:.3f}MB"
)
