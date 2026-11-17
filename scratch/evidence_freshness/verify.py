"""Run bounded local checks and save a new evidence directory; no model calls."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from checker import safe_path, sha

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New directory relative to the experiment")
    args = parser.parse_args()
    output = safe_path(ROOT, args.output)
    output.mkdir(parents=True, exist_ok=False)
    commands = [
        ("fixtures", ROOT, ["run_fixtures.py", "--format", "json"]),
        ("focused-tests", ROOT, ["-m", "unittest", "-v", "test_freshness"]),
        ("repository-regressions", ROOT.parent.parent,
         ["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
    ]
    records = []
    with tempfile.TemporaryDirectory(prefix="temporary-", dir=output) as temp:
        env = dict(os.environ, TMP=temp, TEMP=temp, TMPDIR=temp, PYTHONDONTWRITEBYTECODE="1")
        for name, cwd, arguments in commands:
            command = [sys.executable, "-B", *arguments]
            run = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
            # Public evidence records use relative working directories and a
            # runtime-bound interpreter token, never local installation paths.
            def public_text(value):
                for path, label in ((str(ROOT), "<experiment>"),
                                    (str(ROOT.parent.parent), "<repository>"),
                                    (str(Path.home()), "<user-home>")):
                    value = value.replace(path, label).replace(path.replace("\\", "/"), label)
                return value
            stdout, stderr = public_text(run.stdout), public_text(run.stderr)
            for suffix, content in (("stdout", stdout), ("stderr", stderr)):
                (output / f"{name}.{suffix}.txt").write_text(content, encoding="utf-8", newline="\n")
            records.append({"name": name, "command": ["<interpreter>", "-B", *arguments],
                            "cwd_relative_to_experiment": "." if cwd == ROOT else "../..",
                            "exit_code": run.returncode,
                            "stdout": f"{name}.stdout.txt", "stderr": f"{name}.stderr.txt"})
            print(f"{name}: exit {run.returncode}")
    files = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
             for p in sorted(ROOT.rglob("*"))
             if p.is_file() and not p.is_relative_to(output) and "__pycache__" not in p.parts}
    result = {"status": "LOCAL_SYNTHETIC_CHECKS_PASSED" if all(r["exit_code"] == 0 for r in records) else "LOCAL_CHECK_FAILURE",
              "environment": {"os": platform.system(), "release": platform.release(),
                              "python": platform.python_version(), "implementation": platform.python_implementation()},
              "commands": records, "checked_file_sha256": files,
              "transcript_note": "Output retained with local absolute paths replaced only if present; interpreter token bound by environment above.",
              "full_package_install_validation": "NOT_RUN: installs unrelated third-party packages; outside this standard-library experiment",
              "other_operating_systems": "NOT_RUN", "independent_H3": "NOT_RUN",
              "owner_acceptance": "pending", "pilot_measurements": "NOT_COLLECTED",
              "candidate_comparison": "NOT_RUN: conservative baseline only"}
    (output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return int(any(r["exit_code"] != 0 for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
