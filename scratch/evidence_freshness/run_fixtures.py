"""Evaluate frozen authored fixtures against separately authored expectations."""
import argparse
import copy
import json
from pathlib import Path

from checker import assess, load_json, read_bytes

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"


def load_cases():
    current = load_json(FIXTURES / "current.json")
    receipt = load_json(FIXTURES / "receipt.json")
    cases = load_json(FIXTURES / "cases.json")
    if not isinstance(cases, list) or len(cases) != 12:
        raise ValueError("Expected twelve authored fixture cases")
    seen = set()
    for case in cases:
        if (set(case) != {"id", "current", "receipt", "context_reads", "ground_truth"}
                or not isinstance(case["id"], str) or case["id"] in seen
                or not case["ground_truth"]):
            raise ValueError("Invalid fixture metadata")
        seen.add(case["id"])
        for record in ("current", "receipt"):
            if not isinstance(case[record], dict):
                raise ValueError("Fixture override must be an object")
        # Context reads are a separate log; checking references does not turn
        # those files into semantic dependencies of the recorded check.
        if not isinstance(case["context_reads"], list):
            raise ValueError("Invalid context log")
        for context in case["context_reads"]:
            if set(context) != {"at_read", "now", "relationship"} or context["relationship"] != "context_only":
                raise ValueError("Invalid context relationship")
            read_bytes(FIXTURES, context["at_read"])
            read_bytes(FIXTURES, context["now"])
        case_current, case_receipt = copy.deepcopy(current), copy.deepcopy(receipt)
        # Whole fields replace base fields: no implicit recursive dependency merge.
        case_current.update(copy.deepcopy(case["current"]))
        case_receipt.update(copy.deepcopy(case["receipt"]))
        yield case["id"], case_current, case_receipt


def evaluate():
    expected = load_json(FIXTURES / "expected.json")
    cases = list(load_cases())
    if set(expected) != {row[0] for row in cases}:
        raise ValueError("Expectations and cases differ")
    rows = []
    for case_id, current, receipt in cases:
        wanted = expected[case_id]
        if (set(wanted) != {"outcome", "reason", "rationale"}
                or wanted["outcome"] not in {"eligible", "stale", "invalid", "insufficient", "blocked"}
                or not wanted["rationale"]):
            raise ValueError("Invalid independent expectation")
        result = assess(current, receipt, FIXTURES)
        codes = [r["code"] for r in result["reasons"]]
        matched = result["outcome"] == wanted["outcome"] and wanted["reason"] in codes
        rows.append({"case_id": case_id, "expected": wanted["outcome"],
                     "matched": matched, "decision": result})
    return {"kind": "deterministic_synthetic_baseline", "cases": rows,
            "passed": sum(r["matched"] for r in rows), "failed": sum(not r["matched"] for r in rows),
            "productivity_measured": False, "owner_acceptance": "pending"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()
    summary = evaluate()
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for row in summary["cases"]:
            print(f'{row["case_id"]}: {row["decision"]["outcome"]} ({"PASS" if row["matched"] else "FAIL"})')
        print(f'{summary["passed"]}/12 expectations matched; {summary["failed"]} mismatches.')
        print("Synthetic rule checks only; no correctness, approval, or productivity claim.")
    return int(summary["failed"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
