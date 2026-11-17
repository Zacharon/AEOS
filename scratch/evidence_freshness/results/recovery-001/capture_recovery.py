"""Capture one fixed recovery suite and assess two receipts without editing them."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parent
REPLAY = ROOT / "replay"
ORIGINAL = ROOT.parent / "rehearsal-001"
CHECKER = ROOT.parent.parent / "checker.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def capture(label, arguments):
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    run = subprocess.run([sys.executable, *arguments], cwd=REPLAY,
                         capture_output=True, check=False, timeout=60)
    elapsed = perf_counter() - timer
    for stream, data in (("stdout", run.stdout), ("stderr", run.stderr)):
        with (REPLAY / f"{label}.{stream}.txt").open("xb") as out:
            out.write(data)
    record = {"command": ["<interpreter>", *[arg.replace(str(CHECKER), "../../../checker.py") for arg in arguments]],
              "cwd_relative_to_recovery_directory": "replay", "started_utc": started,
              "elapsed_seconds": elapsed, "exit_code": run.returncode,
              "stdout": f"{label}.stdout.txt", "stderr": f"{label}.stderr.txt",
              "stdout_sha256": sha(REPLAY / f"{label}.stdout.txt"),
              "stderr_sha256": sha(REPLAY / f"{label}.stderr.txt")}
    save(REPLAY / f"{label}.execution.json", record)
    print(run.stdout.decode("utf-8"), end="")
    return run, record


def main():
    if (REPLAY / "suite.execution.json").exists() or (ROOT / "result.json").exists():
        raise SystemExit("Prior recovery evidence exists; preserve it.")
    initial_failure = json.loads((ROOT / "initial-failure.json").read_text())
    if initial_failure["exit_code"] != 1 or not initial_failure["inputs_unchanged"]:
        raise SystemExit("The required original failure has not been observed.")
    historical = {"historical-receipt.json": "receipt.json", "check.stdout.txt": "check.stdout.txt",
                  "check.stderr.txt": "check.stderr.txt", "requirements-v2.txt": "requirements-v2.txt"}
    if not all(sha(REPLAY / dest) == sha(ORIGINAL / source) for dest, source in historical.items()):
        raise SystemExit("Historical receipt/output or current requirement copy differs.")
    dependency_names = ("count_items.py", "check_count.py", "check_recovery.py", "inputs/items.json",
                        "inputs/none-active.json", "inputs/empty.json")
    dependency_hashes = {name: sha(REPLAY / name) for name in dependency_names}
    source_hashes = {name: dependency_hashes[name] for name in dependency_names if name.endswith(".py")}
    source_revision = "sha256:" + hashlib.sha256(
        json.dumps(source_hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    environment = {"os": platform.system(), "os_version": platform.version(),
                   "implementation": platform.python_implementation(), "python": platform.python_version(),
                   "interpreter_sha256": sha(Path(sys.executable)), "flags": ["-I", "-B"]}
    save(ROOT / "environment.json", environment)
    save(ROOT / "source-manifest.json", {"source_revision": source_revision, "files": source_hashes,
                                         "dependencies": dependency_hashes,
                                         "specification_sha256": sha(REPLAY / "requirements-v2.txt")})
    suite, execution = capture("suite", ["-I", "-B", "check_recovery.py"])
    unchanged = dependency_hashes == {name: sha(REPLAY / name) for name in dependency_names}
    if suite.returncode != 0 or b"Cases passed: 3/3" not in suite.stdout or not unchanged:
        raise SystemExit("Corrected suite failed or changed input; evidence retained, no successful receipt.")

    current = json.loads((ORIGINAL / "current-after.json").read_text())
    runtime = f'{environment["implementation"]} {environment["python"]}; {environment["os"]} {environment["os_version"]}; interpreter-sha256={environment["interpreter_sha256"]}'
    current.update({"source_revision": source_revision,
                    "environment": {"runtime": runtime, "configuration": "isolated Python (-I -B); mixed=2, none-active=0, empty=0; cwd=replay-root"},
                    "check_id": "CHECK-active-count-suite", "command": " ".join(execution["command"]),
                    "dependencies": {name: name for name in dependency_names}})
    save(REPLAY / "current.json", current)
    receipt = json.loads((ORIGINAL / "receipt.json").read_text())
    for key in ("requirement_revision", "requirement_ids", "source_revision", "dependency_coverage", "environment", "check_id", "command"):
        receipt[key] = current[key]
    receipt.update({"specification_sha256": sha(REPLAY / "requirements-v2.txt"),
                    "dependency_sha256": dependency_hashes, "exit_code": suite.returncode,
                    "raw_output": execution["stdout"], "raw_sha256": execution["stdout_sha256"]})
    save(REPLAY / "replacement-receipt.json", receipt)
    args = ["-I", "-B", str(CHECKER), "--root", ".", "--current", "current.json", "--format", "text", "--receipt"]
    old, _ = capture("historical-assessment", [*args, "historical-receipt.json"])
    new, _ = capture("replacement-assessment", [*args, "replacement-receipt.json"])
    historical_intact = all(sha(REPLAY / dest) == sha(ORIGINAL / source) for dest, source in historical.items())
    old_text, new_text = old.stdout.decode(), new.stdout.decode()
    passed = (old.returncode == 1 and "Outcome: stale" in old_text
              and "source_revision_changed" in old_text and "specification_bytes_changed" in old_text
              and "missing_file" not in old_text and "integrity_mismatch" not in old_text
              and new.returncode == 0 and "Outcome: eligible" in new_text and historical_intact)
    save(ROOT / "result.json", {"status": "LOCAL_RECOVERY_PASSED" if passed else "LOCAL_RECOVERY_FAILED",
                                "original_behavior": {"expected": 2, "observed": 3, "exit_code": initial_failure["exit_code"]},
                                "corrected_checks": [{"case": "mixed", "expected": 2}, {"case": "none-active", "expected": 0}, {"case": "empty", "expected": 0}],
                                "suite_exit_code": suite.returncode, "suite_evidence": "replay/suite.stdout.txt",
                                "historical_decision_output": "replay/historical-assessment.stdout.txt",
                                "replacement_decision_output": "replay/replacement-assessment.stdout.txt",
                                "historical_evidence_copies_intact": historical_intact,
                                "source_inputs_unchanged_during_checks": unchanged, "checker_sha256": sha(CHECKER),
                                "replacement_covers": "All three cases executed by check_recovery.py, not just the mixed input",
                                "owner_acceptance": "pending", "independent_H3": "NOT_RUN",
                                "preparation_minutes": None, "reviewer_minutes": None, "productivity_improvement": None,
                                "real_handoff_started": False})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
