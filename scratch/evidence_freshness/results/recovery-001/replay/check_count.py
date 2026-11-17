"""Run the replay executable and compare its output with a supplied oracle."""
import argparse
import json
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--expected", type=int, required=True)
parser.add_argument("--input", default="inputs/items.json")
args = parser.parse_args()
command = [sys.executable, "-I", "-B", "count_items.py", args.input]
run = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
print("Command: <interpreter> -I -B count_items.py " + args.input)
print("Source stdout: " + run.stdout.strip())
print("Source exit: " + str(run.returncode))
if run.stderr:
    print(run.stderr, file=sys.stderr, end="")
if run.returncode != 0:
    raise SystemExit(1)
actual = json.loads(run.stdout)["count"]
passed = type(actual) is int and actual == args.expected
print(f'{"PASS" if passed else "FAIL"} expected={args.expected} actual={actual}')
raise SystemExit(0 if passed else 1)
