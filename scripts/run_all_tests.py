from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MILESTONES = ROOT / "milestones"


def find_tests(milestone: Path) -> list[Path]:
    locations = []
    for directory in milestone.rglob("tests"):
        if directory.is_dir() and any(directory.glob("test_*.py")):
            locations.append(directory)
    if any(milestone.glob("test_*.py")):
        locations.append(milestone)
    return sorted(set(locations))


def main() -> int:
    requested = set(sys.argv[1:])
    milestones = [
        path for path in sorted(MILESTONES.iterdir())
        if path.is_dir() and (not requested or path.name in requested)
    ]
    missing = requested - {path.name for path in milestones}
    if missing:
        print("Milestones not found:", ", ".join(sorted(missing)))
        return 2

    failures = []
    skipped = []
    for milestone in milestones:
        tests = find_tests(milestone)
        if not tests:
            skipped.append(milestone.name)
            continue

        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [
                str(milestone),
                str(milestone / "dependency"),
                env.get("PYTHONPATH", ""),
            ]
        )
        print(f"\n===== {milestone.name} =====", flush=True)
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *map(str, tests)],
            cwd=milestone,
            env=env,
            check=False,
        )
        if process.returncode:
            failures.append((milestone.name, process.returncode))

    print("\n===== SUMMARY =====")
    print("Milestones with tests:", len(milestones) - len(skipped))
    print("Milestones without available tests:", len(skipped))
    if skipped:
        print("No tests:", ", ".join(skipped))
    if failures:
        for name, code in failures:
            print(f"FAIL {name}: exit code {code}")
        return 1
    print("All available suites passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
