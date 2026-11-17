"""Identical local acceptance checks for baseline and candidate copies."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(variant):
    folder = ROOT / variant
    results = folder / "results"
    results.mkdir(exist_ok=True)
    rows = []
    for kind in ("directory", "file"):
        target = results / ("existing-" + kind)
        if kind == "directory":
            target.mkdir(exist_ok=True)
            marker = target / "preserve.txt"
        else:
            marker = target
        if not marker.exists():
            marker.write_bytes(b"synthetic evidence: preserve these bytes\n")
        before = digest(marker)
        started = time.perf_counter()
        command = subprocess.run([sys.executable, "-B", "compare.py", "--output", str(target)], cwd=folder, capture_output=True, text=True, timeout=30)
        rows.append({"check": "existing_" + kind, "exit_code": command.returncode, "clear_error": "output already exists" in command.stderr, "traceback": "Traceback" in command.stderr, "bytes_preserved": digest(marker) == before, "command_seconds": round(time.perf_counter() - started, 4)})
    started = time.perf_counter()
    fresh = results / "fresh"
    if fresh.exists():
        raise ValueError("fresh output already exists; preserve this run and prepare a new trial")
    command = subprocess.run([sys.executable, "-B", "compare.py", "--output", str(fresh)], cwd=folder, capture_output=True, text=True, timeout=30)
    rows.append({"check": "new_output", "exit_code": command.returncode, "artifacts_present": all((fresh / name).is_file() for name in ("summary.json", "sample-trace.json")), "command_seconds": round(time.perf_counter() - started, 4)})
    started = time.perf_counter()
    tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_policy"], cwd=folder, capture_output=True, text=True, timeout=60)
    rows.append({"check": "focused_regressions", "exit_code": tests.returncode, "count_confirmed": "Ran 18 tests" in tests.stderr, "command_seconds": round(time.perf_counter() - started, 4)})
    original = ROOT.parent / "failure_novelty"
    manifest = json.loads((ROOT / "source-manifest.json").read_text(encoding="utf-8"))
    originals_unchanged = all(digest(original / name) == sha for name, sha in manifest.items())
    baseline_unchanged = all(digest(ROOT / "baseline" / name) == sha for name, sha in manifest.items())
    collisions_passed = all(r["exit_code"] == 2 and r["clear_error"] and not r["traceback"] and r["bytes_preserved"] for r in rows[:2])
    passed = collisions_passed and rows[2]["exit_code"] == 0 and rows[2]["artifacts_present"] and tests.returncode == 0 and rows[3]["count_confirmed"] and originals_unchanged and baseline_unchanged
    return {"schema": "tstack-local-pilot/v1", "variant": variant, "python": platform.python_version(), "acceptance_passed": passed, "checks": rows, "originals_unchanged": originals_unchanged, "baseline_unchanged": baseline_unchanged, "candidate_sha256": digest(ROOT / "candidate/compare.py"), "model_usage": "UNKNOWN", "model_elapsed_seconds": "UNKNOWN", "human_attention_seconds": "UNKNOWN", "pr_lifecycle": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("baseline", "candidate"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "evidence") or output == ROOT / "evidence" or output.exists():
        parser.error("use a new evidence file under this trial's evidence directory")
    evidence = run(args.variant)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["acceptance_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
