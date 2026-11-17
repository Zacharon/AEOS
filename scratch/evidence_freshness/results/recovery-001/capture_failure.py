"""Capture the requested check against the untouched original rehearsal."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

root = Path(__file__).resolve().parent
original = root.parent / "rehearsal-001"
if (root / "initial-failure.json").exists():
    raise SystemExit("Prior capture exists; preserve it.")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
paths = ("count_items.py", "check_count.py", "inputs/items.json", "requirements-v2.txt")
before = {name: sha(original / name) for name in paths}
started = datetime.now(timezone.utc).isoformat()
timer = perf_counter()
run = subprocess.run([sys.executable, "-I", "-B", "check_count.py", "--expected", "2"],
                     cwd=original, capture_output=True, check=False, timeout=30)
elapsed = perf_counter() - timer
for stream, data in (("stdout", run.stdout), ("stderr", run.stderr)):
    with (root / f"initial-failure.{stream}.txt").open("xb") as out:
        out.write(data)
record = {"command": ["<interpreter>", "-I", "-B", "check_count.py", "--expected", "2"],
          "cwd_relative_to_this_directory": "../rehearsal-001", "started_utc": started,
          "elapsed_seconds": elapsed, "exit_code": run.returncode,
          "stdout": "initial-failure.stdout.txt", "stderr": "initial-failure.stderr.txt",
          "source_and_input_sha256": before,
          "inputs_unchanged": before == {name: sha(original / name) for name in paths},
          "environment": {"os": platform.system(), "os_version": platform.version(),
                          "implementation": platform.python_implementation(), "python": platform.python_version(),
                          "interpreter_sha256": sha(Path(sys.executable)), "flags": ["-I", "-B"]}}
with (root / "initial-failure.json").open("x", encoding="utf-8", newline="\n") as out:
    out.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(run.stdout.decode("utf-8"), end="")
print("Observed exit: " + str(run.returncode))
if run.returncode != 1 or b"FAIL expected=2 actual=3" not in run.stdout or not record["inputs_unchanged"]:
    raise SystemExit("Unexpected result; investigate before making a correction.")
