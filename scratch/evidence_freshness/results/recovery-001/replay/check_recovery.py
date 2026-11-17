"""Three explicit counterexamples for the revised active-count requirement."""
import subprocess
import sys

cases = (("mixed", "inputs/items.json", 2),
         ("none-active", "inputs/none-active.json", 0),
         ("empty", "inputs/empty.json", 0))
failures = 0
for name, path, expected in cases:
    arguments = ["-I", "-B", "check_count.py", "--input", path, "--expected", str(expected)]
    run = subprocess.run([sys.executable, *arguments], capture_output=True, check=False, timeout=10)
    print("CASE " + name)
    print("Command: <interpreter> " + " ".join(arguments))
    print(run.stdout.decode("utf-8"), end="")
    print("Check exit: " + str(run.returncode))
    if run.stderr:
        print(run.stderr.decode("utf-8"), file=sys.stderr, end="")
    failures += run.returncode != 0
print(f"Cases passed: {len(cases) - failures}/{len(cases)}")
raise SystemExit(1 if failures else 0)
