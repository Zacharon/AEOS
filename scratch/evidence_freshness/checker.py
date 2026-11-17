"""Read-only synthetic applicability checker; never executes receipt commands."""
import argparse
import hashlib
import json
from pathlib import Path
import re


class RecordError(ValueError):
    def __init__(self, outcome, code):
        self.outcome, self.code = outcome, code
        super().__init__(code)


def fail(code, outcome="invalid"):
    raise RecordError(outcome, code)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("duplicate_json_key")
        result[key] = value
    return result


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=unique_object)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(root, reference):
    """Reject aliases and links before reads; not a hostile concurrent FS sandbox."""
    if not isinstance(reference, str) or not reference:
        fail("invalid_file_reference")
    parts = reference.split("/")
    for part in parts:
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+", part)
                or part in {".", ".."} or part.endswith(".")
                or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])", part.split(".")[0])):
            fail("unsafe_file_reference")
    root = Path(root).absolute()
    # Inspect the root and its parents too: a linked fixture root is not isolation.
    path = root.joinpath(*parts)
    for node in (path, *path.parents):
        if node.is_symlink() or getattr(node, "is_junction", lambda: False)():
            fail("linked_file_reference")
    if not path.resolve().is_relative_to(root.resolve()):
        fail("escaped_file_reference")
    return path


def read_bytes(root, reference):
    path = safe_path(root, reference)
    try:
        if not path.is_file():
            fail("missing_file", "insufficient")
        return path.read_bytes()
    except OSError:
        fail("unreadable_file", "insufficient")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return (isinstance(value, list) and all(text(x) for x in value)
            and len(set(value)) == len(value))


def digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def mapping(value, validator=text):
    return isinstance(value, dict) and all(text(k) and validator(v) for k, v in value.items())


COMMON = {
    "schema_version": lambda v: type(v) is int and v == 1,
    "task_id": text, "claim_id": text, "requirement_revision": text,
    "requirement_ids": strings, "source_revision": text,
    "dependency_coverage": lambda v: v in ("complete", "unknown"),
    "environment": lambda v: mapping(v) and set(v) == {"runtime", "configuration"},
    "check_id": text, "command": text,
}
CURRENT = dict(COMMON, **{
    "withdrawn_ids": strings, "specification": text,
    "dependencies": mapping, "policy": lambda v: v == "exact-source-v1",
    "action": text, "authority": lambda v: v in ("allowed", "denied", "unknown"),
})
RECEIPT = dict(COMMON, **{
    "specification_sha256": digest,
    "dependency_sha256": lambda v: mapping(v, digest),
    "execution_status": lambda v: v in ("completed", "not_run", "interrupted"),
    "exit_code": lambda v: v is None or type(v) is int,
    "raw_output": lambda v: v is None or text(v),
    "raw_sha256": lambda v: v is None or digest(v),
    "assumptions": strings, "unrun_checks": strings,
    "historical_status": lambda v: v in ("recorded", "superseded"),
    "authority_at_execution": lambda v: v in ("allowed", "denied", "unknown"),
    "owner_acceptance": lambda v: v in ("pending", "accepted", "rejected", "unknown"),
})


def validate(record, schema, label):
    if not isinstance(record, dict):
        fail(label + ".not_object")
    missing = sorted(set(schema) - set(record))
    if missing:
        fail(label + ".missing:" + ",".join(missing), "insufficient")
    if set(record) - set(schema):
        fail(label + ".unknown_fields")
    for key, check in schema.items():
        if not check(record[key]):
            fail(label + ".malformed:" + key)


def assess(current, receipt, root):
    """Conservative whole-task baseline. Current input is trusted synthetic truth."""
    issues = []
    def issue(outcome, code):
        issues.append({"outcome": outcome, "code": code})

    try:
        validate(current, CURRENT, "current")
        validate(receipt, RECEIPT, "receipt")
        if set(current["requirement_ids"]) & set(current["withdrawn_ids"]):
            fail("contradictory_current_requirements")
        if not current["requirement_ids"]:
            issue("stale", "no_active_requirement_for_claim")
        if (not receipt["requirement_ids"] or
                set(receipt["requirement_ids"]) != set(current["requirement_ids"])):
            issue("stale", "active_requirement_set_changed")
        if set(receipt["requirement_ids"]) & set(current["withdrawn_ids"]):
            issue("stale", "requirement_withdrawn")
        for key in ("task_id", "claim_id", "requirement_revision", "source_revision",
                    "environment", "check_id", "command"):
            if current[key] != receipt[key]:
                issue("stale", key + "_changed")
        if receipt["historical_status"] == "superseded":
            issue("stale", "receipt_superseded")
        if (current["dependency_coverage"] != "complete" or
                receipt["dependency_coverage"] != "complete"):
            issue("insufficient", "unknown_dependency_coverage")
        if set(current["dependencies"]) != set(receipt["dependency_sha256"]):
            issue("insufficient", "dependency_set_incomplete")
        for logical_id, reference in sorted(current["dependencies"].items()):
            try:
                actual = sha(read_bytes(root, reference))
                expected = receipt["dependency_sha256"].get(logical_id)
                if expected is not None and actual != expected:
                    issue("stale", "dependency_changed:" + logical_id)
            except RecordError as exc:
                issue(exc.outcome, "dependency:" + logical_id + ":" + exc.code)
        try:
            if sha(read_bytes(root, current["specification"])) != receipt["specification_sha256"]:
                issue("stale", "specification_bytes_changed")
        except RecordError as exc:
            issue(exc.outcome, "specification:" + exc.code)
        if receipt["execution_status"] != "completed" or receipt["exit_code"] != 0:
            issue("insufficient", "successful_execution_not_recorded")
        if receipt["raw_output"] is None or receipt["raw_sha256"] is None:
            issue("insufficient", "raw_evidence_not_recorded")
        else:
            try:
                if sha(read_bytes(root, receipt["raw_output"])) != receipt["raw_sha256"]:
                    issue("invalid", "raw_evidence_integrity_mismatch")
            except RecordError as exc:
                issue(exc.outcome, "raw_evidence:" + exc.code)
        if receipt["unrun_checks"]:
            issue("insufficient", "required_checks_not_run")
        if receipt["assumptions"]:
            issue("insufficient", "outstanding_assumptions")
    except RecordError as exc:
        issue(exc.outcome, exc.code)

    # Authority has its own axis, so stale/invalid evidence never hides a denial.
    # This is a supplied fixture condition, not identity or approval authentication.
    authority = current.get("authority") if isinstance(current, dict) else None
    if authority == "denied":
        action = "blocked"
    elif authority == "allowed":
        action = "allowed_by_synthetic_input"
    else:
        action = "unknown"
        issue("insufficient", "current_authority_unknown")
    evidence = next((state for state in ("invalid", "stale", "insufficient")
                     if any(i["outcome"] == state for i in issues)), "eligible")
    if action == "blocked":
        issue("blocked", "current_authority_denied")
    if not issues:
        issue("eligible", "applicability_rules_satisfied_only")
    return {"outcome": "blocked" if action == "blocked" else evidence,
            "evidence_outcome": evidence, "action_outcome": action,
            "reasons": issues,
            "owner_acceptance_inferred": False,
            "execution_authenticity_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, help="Current-state JSON relative to --root")
    parser.add_argument("--receipt", required=True, help="Historical receipt JSON relative to --root")
    parser.add_argument("--root", required=True, type=Path, help="Synthetic fixture directory")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()
    try:
        current = load_json(safe_path(args.root, args.current))
        receipt = load_json(safe_path(args.root, args.receipt))
        result = assess(current, receipt, args.root)
    except (RecordError, OSError, ValueError) as exc:
        result = {"outcome": getattr(exc, "outcome", "invalid"),
                  "reasons": [{"code": getattr(exc, "code", "unreadable_or_malformed_json")} ]}
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Outcome: " + result["outcome"])
        for reason in result["reasons"]:
            print("- " + reason["code"])
        print("Synthetic applicability only; no acceptance or execution permission is granted.")
    return 0 if result["outcome"] == "eligible" else 1


if __name__ == "__main__":
    raise SystemExit(main())
