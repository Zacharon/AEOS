"""One fixed rehearsal using the existing checker; refuses prior run evidence."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parent
CHECKER = ROOT.parent.parent / "checker.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, data):
    with (ROOT / name).open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def capture(label, arguments):
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    run = subprocess.run([sys.executable, *arguments], cwd=ROOT,
                         capture_output=True, check=False, timeout=30)
    elapsed = perf_counter() - timer
    # These successful commands emit no local absolute paths. Preserve bytes.
    (ROOT / f"{label}.stdout.txt").write_bytes(run.stdout)
    (ROOT / f"{label}.stderr.txt").write_bytes(run.stderr)
    portable = ["<interpreter>", *arguments]
    portable = [arg.replace(str(CHECKER), "../../checker.py") for arg in portable]
    record = {"command": portable, "cwd": ".", "started_utc": started,
              "elapsed_seconds": elapsed, "exit_code": run.returncode,
              "stdout": f"{label}.stdout.txt", "stderr": f"{label}.stderr.txt",
              "stdout_sha256": digest(ROOT / f"{label}.stdout.txt"),
              "stderr_sha256": digest(ROOT / f"{label}.stderr.txt")}
    write_json(f"{label}.execution.json", record)
    return run, record


def main():
    # Only authored starting files may exist; a failed attempt must be preserved.
    starting = {"count_items.py", "check_count.py", "inputs/items.json",
                "requirements-v1.txt", "rehearse.py"}
    if {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()} != starting:
        raise SystemExit("Refusing an existing or unexpected evidence set; use a fresh rehearsal directory.")
    source_files = ("count_items.py", "check_count.py")
    source_manifest = {name: digest(ROOT / name) for name in source_files}
    source_revision = "sha256:" + hashlib.sha256(
        json.dumps(source_manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    initial_files = {name: digest(ROOT / name) for name in sorted(starting)}
    environment = {"os": platform.system(), "os_release": platform.release(),
                   "os_version": platform.version(), "implementation": platform.python_implementation(),
                   "python": platform.python_version(), "machine": platform.machine(),
                   "interpreter_sha256": digest(Path(sys.executable)),
                   "flags": ["-I", "-B"],
                   "capture_note": "Interpreter location is represented by a token; version and binary digest are observed."}
    write_json("environment.json", environment)
    write_json("source-manifest.json", {"files": source_manifest, "source_revision": source_revision,
                                        "algorithm": "sha256 of sorted compact UTF-8 JSON filename-to-sha256 map"})
    check, execution = capture("check", ["-I", "-B", "check_count.py", "--expected", "3"])
    if check.returncode != 0:
        raise SystemExit("Check failed; captured evidence retained, receipt not marked successful.")

    timer = perf_counter()
    dependencies = {name: name for name in (*source_files, "inputs/items.json")}
    runtime = f'{environment["implementation"]} {environment["python"]}; {environment["os"]} {environment["os_version"]}; interpreter-sha256={environment["interpreter_sha256"]}'
    current = {"schema_version": 1, "task_id": "REPLAY-count-001", "claim_id": "CLAIM-example-count",
               "requirement_revision": "intent-1", "requirement_ids": ["REQ-count"], "withdrawn_ids": [],
               "source_revision": source_revision, "dependency_coverage": "complete",
               "environment": {"runtime": runtime, "configuration": "isolated Python (-I -B); expected=3; cwd=replay-root"},
               "check_id": "CHECK-example-count", "command": " ".join(execution["command"]),
               "specification": "requirements-v1.txt", "dependencies": dependencies,
               "policy": "exact-source-v1", "action": "review-local-replay", "authority": "allowed"}
    common = ("schema_version", "task_id", "claim_id", "requirement_revision", "requirement_ids",
              "source_revision", "dependency_coverage", "environment", "check_id", "command")
    receipt = {key: copy.deepcopy(current[key]) for key in common}
    receipt.update({"specification_sha256": digest(ROOT / "requirements-v1.txt"),
                    "dependency_sha256": {key: digest(ROOT / path) for key, path in dependencies.items()},
                    "execution_status": "completed", "exit_code": check.returncode,
                    "raw_output": execution["stdout"], "raw_sha256": execution["stdout_sha256"],
                    "assumptions": [], "unrun_checks": [], "historical_status": "recorded",
                    "authority_at_execution": "allowed", "owner_acceptance": "pending"})
    write_json("current-before.json", current)
    write_json("receipt.json", receipt)
    record_assembly_seconds = perf_counter() - timer
    fixed = {**initial_files, **{name: digest(ROOT / name) for name in
             ("receipt.json", "current-before.json", "check.stdout.txt", "check.stderr.txt", "check.execution.json")}}
    checker_args = ["-I", "-B", str(CHECKER), "--root", ".", "--receipt", "receipt.json", "--format", "text", "--current"]
    before, _ = capture("before", [*checker_args, "current-before.json"])
    print(before.stdout.decode("utf-8"), end="")
    if before.returncode != 0 or "Outcome: eligible" not in before.stdout.decode():
        raise SystemExit("Unexpected before decision; preserve this attempt.")

    with (ROOT / "requirements-v2.txt").open("x", encoding="utf-8", newline="\n") as out:
        out.write("ISOLATED SYNTHETIC REPLAY, REQUIREMENT REQ-count, REVISION intent-2\n"
                  "Return only the number of items whose active field is true.\n"
                  "The same provided example must return 2; sample-b is excluded.\n"
                  "Passing this example establishes only this case, not general correctness.\n")
    after_current = dict(current, requirement_revision="intent-2", specification="requirements-v2.txt")
    write_json("current-after.json", after_current)
    after, _ = capture("after", [*checker_args, "current-after.json"])
    print(after.stdout.decode("utf-8"), end="")
    preserved = all(digest(ROOT / name) == expected for name, expected in fixed.items())
    changed_fields = sorted(key for key in current if current[key] != after_current[key])
    passed = (after.returncode == 1 and "Outcome: stale" in after.stdout.decode()
              and "requirement_revision_changed" in after.stdout.decode()
              and "specification_bytes_changed" in after.stdout.decode()
              and preserved and changed_fields == ["requirement_revision", "specification"])
    write_json("result.json", {"status": "LOCAL_REHEARSAL_PASSED" if passed else "LOCAL_REHEARSAL_FAILED",
                               "before": "eligible", "after_expected": "stale",
                               "check_exit_code": check.returncode, "after_exit_code": after.returncode,
                               "changed_current_fields": changed_fields,
                               "preserved_receipt_raw_output_and_source": preserved,
                               "preserved_file_sha256": fixed, "checker_sha256": digest(CHECKER),
                               "record_assembly_seconds": record_assembly_seconds,
                               "measurement_scope": "Automated JSON assembly only; excludes design, reading, authoring, check execution and owner review.",
                               "total_preparation_minutes": None, "active_operator_minutes": None,
                               "active_reviewer_minutes": None, "productivity_improvement": None,
                               "behavior_check_runs": 1, "retries": 0,
                               "owner_acceptance": "pending", "independent_H3": "NOT_RUN",
                               "revised_behavior_check": "NOT_RUN"})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
