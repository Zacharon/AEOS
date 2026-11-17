"""Read-only candidate stopping policy. Supplied evidence is not authenticated."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

VERSION = "failure-novelty/v1"
MAX_ROUNDS = 3
IDENTITY = ("check", "category", "subject", "expected", "actual")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    return (type(value) is int and value >= 0) or (type(value) is float and math.isfinite(value) and value >= 0)


def strings(value):
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def signature(failures):
    rows = sorted({tuple(" ".join(row[k].split()) for k in IDENTITY) for row in failures})
    return hashlib.sha256(json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def validate(trace):
    require(isinstance(trace, dict), "trace must be an object")
    require(trace.get("schema") == VERSION, "unsupported schema")
    require(isinstance(trace.get("scope_revision"), str) and trace["scope_revision"].strip(), "scope_revision required")
    checks = trace.get("required_checks")
    require(strings(checks) and checks and len(checks) == len(set(checks)), "required_checks must be nonempty and unique")
    limits = trace.get("limits", {})
    require(isinstance(limits, dict) and set(limits) == {"elapsed_seconds", "cost_units"} and all(number(limits.get(k)) and limits[k] > 0 for k in ("elapsed_seconds", "cost_units")), "positive finite time and cost limits required")
    require(isinstance(trace.get("metric"), str) and trace["metric"].strip(), "fixed remaining-work metric required")
    rounds = trace.get("rounds")
    require(isinstance(rounds, list) and 1 <= len(rounds) <= MAX_ROUNDS, "trace needs one to three rounds")
    previous = {"elapsed_seconds": 0, "cost_units": 0}
    for r in rounds:
        require(isinstance(r, dict), "round must be an object")
        require(r.get("scope_revision") == trace["scope_revision"], "scope revision changed; start a new authorized trace")
        usage = r.get("usage", {})
        require(isinstance(usage, dict) and set(usage) == set(previous) and all(number(usage.get(k)) and usage[k] >= previous[k] for k in previous), "usage must be finite, nonnegative and cumulative")
        previous = usage
        observed = r.get("checks")
        require(isinstance(observed, dict) and set(observed) == set(checks), "each round must cover exactly required_checks")
        for check in observed.values():
            require(isinstance(check, dict) and check.get("status") in {"passed", "failed", "not_run"} and strings(check.get("evidence")), "invalid check observation")
            require(check["status"] == "not_run" or bool(check["evidence"]), "executed checks require evidence references")
        failures = r.get("failures")
        require(isinstance(failures, list), "failures must be a list")
        for f in failures:
            require(isinstance(f, dict) and all(isinstance(f.get(k), str) and f[k].strip() for k in IDENTITY), "failure requires five nonempty semantic fields")
            require(f["check"] in observed and observed[f["check"]]["status"] == "failed", "failure must bind a failed required check")
        require({f["check"] for f in failures} == {k for k, v in observed.items() if v["status"] == "failed"}, "failed checks and failure records disagree")
        progress = r.get("progress", {})
        require(isinstance(progress, dict) and "remaining" in progress and (progress["remaining"] is None or number(progress["remaining"])) and strings(progress.get("evidence")), "invalid progress record")
        require(progress.get("remaining") is None or bool(progress["evidence"]), "known progress requires evidence references")
        actions = r.get("remaining_actions")
        require(isinstance(actions, list), "remaining_actions must be a list")
        require(all(isinstance(a, dict) and all(isinstance(a.get(k), str) and a[k].strip() for k in ("action", "justification")) for a in actions), "remaining actions require justification")
        blocker = r.get("blocker")
        require(blocker is None or (isinstance(blocker, dict) and all(isinstance(blocker.get(k), str) and blocker[k].strip() for k in ("reason", "resume_condition"))), "blocker requires reason and resume_condition")
    return trace


def _decision(trace, novelty):
    rounds = trace["rounds"]
    r = rounds[-1]
    common = {"schema": VERSION, "rounds_observed": len(rounds), "failure_signature": signature(r["failures"]), "advisory_only": True}

    def result(state, reason, resume):
        return dict(common, execution_state=state, reason=reason, resume_conditions=resume)

    if r["blocker"]:
        return result("blocked", r["blocker"]["reason"], [r["blocker"]["resume_condition"]])
    exhausted = [k for k in trace["limits"] if k in r["usage"] and r["usage"][k] >= trace["limits"][k]]
    if exhausted:
        return result("blocked", "budget_exhausted", ["Obtain a newly authorized budget and recheck current context before resuming."])
    if all(c["status"] == "passed" for c in r["checks"].values()):
        return result("ready_for_review", "checks_passed", [])
    if novelty and r["failures"] and not r["remaining_actions"]:
        current = signature(r["failures"])
        for index, prior in enumerate(rounds[:-1]):
            if signature(prior["failures"]) == current:
                segment = rounds[index:]
                values = [x["progress"]["remaining"] for x in segment]
                if all(x is not None for x in values) and len(set(values)) == 1:
                    return result("blocked", "stalled", ["Supply new evidence or a materially different justified action; recheck scope and remaining budgets before a new authorized attempt."])
    if len(rounds) == MAX_ROUNDS:
        return result("blocked", "round_cap", ["Review the unresolved checks and obtain a new bounded task authorization; do not reset this trace to evade the cap."])
    return result("in_progress", "bounded_next_attempt", [])


def assess(trace, *, novelty=True):
    validate(trace)
    # Refuse histories that continued after a terminal recommendation. A replay
    # experiment must supply prefixes, never smuggle future rounds to the policy.
    for count in range(1, len(trace["rounds"])):
        prefix = dict(trace, rounds=trace["rounds"][:count])
        require(_decision(prefix, novelty)["execution_state"] == "in_progress", "trace continues after a terminal decision")
    return _decision(trace, novelty)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="JSON trace; read only, no evidence paths are opened")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        result = assess(json.loads(args.trace.read_text(encoding="utf-8")))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}) if args.format == "json" else "Invalid input: " + str(exc), file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['execution_state']}: {result['reason']} (round {result['rounds_observed']}/3; advisory only)")
        for condition in result["resume_conditions"]:
            print("Resume: " + condition)
    return 0


if __name__ == "__main__":
    sys.exit(main())
