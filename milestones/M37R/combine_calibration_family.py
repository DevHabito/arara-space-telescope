
from pathlib import Path
import sys

import numpy as np

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

import arara_m37r as m


family = sys.argv[1]
cfg = m.Config()

block_dir = root / "results" / "calibration_blocks"
parts_dir = root / "results" / "calibration_parts"
parts_dir.mkdir(exist_ok=True)

paths = [
    block_dir / f"{family}_block_{block:02d}.npz"
    for block in range(cfg.calibration_block_count)
]
for path in paths:
    if not path.exists():
        raise RuntimeError(f"Missing block: {path}")

arrays = m.combine_calibration_blocks(
    paths,
    expected_per_block=cfg.calibration_negatives_per_block,
    expected_total=cfg.calibration_negatives_per_family,
)
output = parts_dir / f"{family}.npz"
np.savez_compressed(output, **arrays)
print(
    f"{family}: pooled n={len(next(iter(arrays.values())))} "
    f"size={output.stat().st_size / 1024**2:.3f}MB"
)
