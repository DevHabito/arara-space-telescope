from pathlib import Path
import csv
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "repository_files_sha256.csv"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures = []
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            path = ROOT / row["path"]
            if not path.exists():
                failures.append((row["path"], "missing"))
            elif digest(path) != row["sha256"]:
                failures.append((row["path"], "hash mismatch"))
    if failures:
        for path, reason in failures:
            print(f"{path}: {reason}")
        return 1
    print("Manifest verified: all hashes match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
