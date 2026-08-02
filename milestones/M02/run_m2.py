
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from arara_m2 import Config, evaluate_development, evaluate_holdout

if __name__ == "__main__":
    raise SystemExit(
        "Use the frozen development and one-time holdout notebooks/scripts. "
        "Direct all-in-one execution is intentionally disabled."
    )
