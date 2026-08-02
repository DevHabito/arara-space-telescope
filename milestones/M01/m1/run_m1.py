
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from arara_m1 import Config, run_all

if __name__ == "__main__":
    out = HERE / "results"
    result = run_all(out, Config())
    print(json.dumps(
        {
            "elapsed_seconds": result["elapsed_seconds"],
            "thresholds": result["development"]["thresholds"],
            "verdict": result["holdout"]["verdict"],
        },
        indent=2,
    ))
