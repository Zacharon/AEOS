"""Replay fixed synthetic observations, with future truth hidden from assess()."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
from policy import VERSION, assess

ROOT = Path(__file__).resolve().parent


def expand(case):
    rounds = []
    for i, (failure, remaining) in enumerate(zip(case["failures"], case["remaining"], strict=True), 1):
        passed = failure == "PASS"
        rounds.append({
            "scope_revision": "synthetic-r1",
            "usage": {"elapsed_seconds": i * 10, "cost_units": i},
            "checks": {"acceptance": {"status": "passed" if passed else "failed", "evidence": [f"synthetic:check-{i}"]}},
            "failures": [] if passed else [{"check": "acceptance", "category": "assertion", "subject": "sample", "expected": "valid", "actual": failure, "diagnostic": f"temporary-token-{i}", "observed_at": f"synthetic-time-{i}"}],
            "progress": {"remaining": remaining, "evidence": [] if remaining is None else [f"synthetic:metric-{i}"]},
            "remaining_actions": [{"action": "try another bounded repair", "justification": "synthetic distinct hypothesis or documented transient"}] if i in case.get("actions_at", []) else [],
            "blocker": {"reason": "missing_authority", "resume_condition": "Obtain exact owner authorization."} if i == case.get("blocker_at") else None,
        })
    return {"schema": VERSION, "scope_revision": "synthetic-r1", "required_checks": ["acceptance"], "metric": "synthetic unresolved obligations", "limits": {"elapsed_seconds": case.get("time_limit", 100), "cost_units": case.get("cost_limit", 10)}, "rounds": rounds}


def replay(trace, novelty):
    decisions = []
    for i in range(1, len(trace["rounds"]) + 1):
        result = assess(dict(trace, rounds=trace["rounds"][:i]), novelty=novelty)
        decisions.append(result)
        if result["execution_state"] != "in_progress":
            return result, decisions
    raise ValueError("fixture lacks a terminal observation")


def compare(fixtures):
    splits = {}
    for split in ("development", "held_out"):
        rows = []
        for case in fixtures[split]:
            trace = expand(case)
            baseline, _ = replay(trace, False)
            candidate, decisions = replay(trace, True)
            future = case["solvable_at"]
            # Separate inherited hard-budget stops from extra policy abandonment.
            extra_stop = (future is not None and baseline["execution_state"] == "ready_for_review" and candidate["rounds_observed"] < future)
            rows.append({"id": case["id"], "solvable_at": future, "baseline": baseline, "candidate": candidate, "candidate_decisions": decisions, "saved_rounds": baseline["rounds_observed"] - candidate["rounds_observed"], "premature_abandonment_added": extra_stop})
        saved = sum(r["saved_rounds"] for r in rows if r["solvable_at"] is None)
        abandoned = sum(r["premature_abandonment_added"] for r in rows)
        splits[split] = {"case_count": len(rows), "unsolved_rounds_saved": saved, "premature_abandonments_added": abandoned, "baseline_rounds": sum(r["baseline"]["rounds_observed"] for r in rows), "candidate_rounds": sum(r["candidate"]["rounds_observed"] for r in rows), "cases": rows}
    return {"schema": "failure-novelty-comparison/v1", "synthetic_only": True, "splits": splits, "promotion": "REJECT" if any(s["premature_abandonments_added"] for s in splits.values()) or not all(s["unsolved_rounds_saved"] > 0 for s in splits.values()) else "ELIGIBLE_FOR_FURTHER_EVALUATION", "real_worker_trials": "NOT_RUN", "installed_policy_change": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new directory under this experiment's results/")
    args = parser.parse_args()
    destination = args.output.resolve()
    if not destination.is_relative_to(ROOT / "results") or destination == ROOT / "results":
        parser.error("output must be a new child of this experiment's results directory")
    fixtures = json.loads((ROOT / "fixtures/cases.json").read_text(encoding="utf-8"))
    summary = compare(fixtures)
    sources = ["policy.py", "compare.py", "test_policy.py", "README.md", "fixtures/cases.json"]
    summary["sha256"] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    summary["python_version"] = platform.python_version()
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("output already exists; choose a new results directory")
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    sample = expand(fixtures["development"][0])
    sample["rounds"] = sample["rounds"][:2]
    (destination / "sample-trace.json").write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"promotion": summary["promotion"], **{k: {field: v[field] for field in ("case_count", "unsolved_rounds_saved", "premature_abandonments_added", "baseline_rounds", "candidate_rounds")} for k, v in summary["splits"].items()}}, indent=2))
    return 0  # Successful experiment execution, not successful promotion.


if __name__ == "__main__":
    sys.exit(main())
