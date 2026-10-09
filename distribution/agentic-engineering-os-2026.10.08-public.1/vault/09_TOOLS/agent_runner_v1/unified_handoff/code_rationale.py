"""Read-only, bounded change coverage for existing Runner task reports.

The controller retains the baseline digest outside worker control. This checks
bytes and coverage, never the truth of prose or permission to accept a change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import handoff as h

MAX_FILES = 10000
MAX_TOTAL = 64 * 1024 * 1024
CONTROL_NAMES = ("code_rationale.py", "handoff.py", "CODE_RATIONALE.md")


def controls():
    """Pin the executed checker, its completion adapter, and rationale rule."""
    parent = Path(__file__).resolve().parent
    return {name: h.digest(h.read_bytes(h.no_links(parent / name), h.MAX_ARTIFACT_BYTES))
            for name in CONTROL_NAMES}


def scope_path(value):
    return h.safe_relative(value, grant=True)


def inventory(root, scopes):
    """Hash actual scoped bytes, including ignored/untracked files, without Git writes.

    Directory scopes must cover the complete authorized editing boundary. No
    extension filter is used: a new source language must not escape coverage.
    Links, private paths, and excessive trees fail rather than silently skip.
    """
    result, total, visited = {}, 0, 0

    def visit(path):
        nonlocal total, visited
        visited += 1
        h.require(visited <= MAX_FILES, "Inventory entry budget exceeded")
        rel = path.relative_to(root).as_posix()
        h.safe_relative(rel)
        h.no_links(path)
        if path.is_dir():
            for child in sorted(path.iterdir()):
                visit(child)
        elif path.is_file():
            h.require(path.stat().st_nlink == 1, f"Hard-linked file refused: {rel}")
            data = h.read_bytes(path, h.MAX_ARTIFACT_BYTES)
            total += len(data)
            h.require(total <= MAX_TOTAL and len(result) < MAX_FILES, "Inventory budget exceeded")
            result[rel] = h.digest(data)
        else:
            h.require(not path.exists(), f"Unsupported file type: {rel}")

    for scope in scopes:
        path = h.within(root, scope.removesuffix('/**'))
        h.require(not path.is_dir() or scope.endswith('/**'), "Directory scope requires /**")
        visit(path)
    return dict(sorted(result.items()))


def snapshot(root_value, task_id, scopes):
    root = h.root_dir(root_value)
    h.nonempty(task_id, "task_id")
    scopes = [scope_path(s) for s in scopes]
    h.require(scopes and len(set(scopes)) == len(scopes), "Supply unique, nonempty scopes")
    # Reject overlapping scopes so the declared boundary has one interpretation.
    for a in scopes:
        for b in scopes:
            h.require(a == b or not (a.endswith('/**') and b.startswith(a[:-2])), "Overlapping scopes")
    return {"schema_version": "1", "task_id": task_id, "root": str(root),
            "scopes": sorted(scopes), "controls": controls(), "files": inventory(root, scopes)}


def load_baseline(path, expected):
    raw = h.read_bytes(h.no_links(Path(path)), 2 * 1024 * 1024)
    h.require(h.digest(raw) == expected, "Baseline differs from controller-held digest")
    base = h.read_json(Path(path), 2 * 1024 * 1024)
    h.exact_keys(base, {"schema_version", "task_id", "root", "scopes", "controls", "files"}, "Baseline")
    h.require(base["schema_version"] == "1", "Unsupported baseline")
    h.require(base["controls"] == controls(), "Checker, adapter or rule changed; independent review required")
    return base


def changes(base, current):
    """Represent renames as deletion plus addition, including edited renames.

    Guessing rename identity can hide edits or pair unrelated equal-content files.
    Explicitly covering both paths retains all evidence without that heuristic.
    """
    before = base["files"]
    return [{"path": p, "before": before.get(p), "after": current.get(p),
             "kind": "added" if p not in before else "deleted" if p not in current else "modified"}
            for p in sorted(before.keys() | current.keys()) if before.get(p) != current.get(p)]


def current_changes(root_value, baseline, expected):
    base = load_baseline(baseline, expected)
    root = h.root_dir(root_value)
    h.require(str(root) == base["root"], "Baseline belongs to another working directory")
    return base, changes(base, inventory(root, base["scopes"]))


def report_record(path):
    """Read one JSON fence from an existing Markdown task report; no new ledger."""
    text = h.read_bytes(h.no_links(Path(path)), h.MAX_ARTIFACT_BYTES).decode("utf-8-sig")
    marker = "```code-rationale\n"
    text = text.replace("\r\n", "\n")
    h.require(text.count(marker) == 1, "Task report needs exactly one code-rationale fence")
    tail = text.split(marker, 1)[1]
    h.require("\n```" in tail, "Unclosed code-rationale fence")
    return json.loads(tail.split("\n```", 1)[0], object_pairs_hook=h.no_duplicate_pairs)


def check(root_value, baseline, expected, report):
    base, delta = current_changes(root_value, baseline, expected)
    root = h.root_dir(root_value)
    # Keeping the task report outside coverage avoids an impossible self-hash.
    report_path = h.no_links(Path(report))
    if report_path.is_relative_to(root):
        h.require(not h.covered(report_path.relative_to(root).as_posix(), base["scopes"]),
                  "Task report must be outside the frozen editing scope")
    record = report_record(report)
    h.exact_keys(record, {"task_id", "baseline_sha256", "changes_sha256", "entries"}, "Rationale record")
    h.require(record["task_id"] == base["task_id"] and record["baseline_sha256"] == expected,
              "Rationale belongs to another task or baseline")
    h.require(record["changes_sha256"] == h.digest(h.json_bytes(delta)), "Rationale describes an older change set")
    h.require(isinstance(record["entries"], list), "Entries must be a list")
    entries = record["entries"]
    covered = []
    for entry in entries:
        h.exact_keys(entry, {"paths", "disposition", "why", "where_to_edit", "constraints", "verification", "references"}, "Rationale entry")
        h.require(isinstance(entry["paths"], list) and entry["paths"], "Entry needs paths")
        for path in entry["paths"]:
            covered.append(h.safe_relative(path))
        h.require(entry["disposition"] in {"documented", "documentation-not-needed"}, "Invalid disposition")
        for field in ("why", "where_to_edit", "constraints", "verification"):
            h.nonempty(entry[field], field)
        h.require(isinstance(entry["references"], list), "References must be a list")
        h.require(entry["disposition"] != "documented" or entry["references"], "Documented changes need references")
        for ref in entry["references"]:
            h.exact_keys(ref, {"path", "sha256", "contains"}, "Reference")
            path = h.within(root, h.safe_relative(ref["path"]))
            data = h.read_bytes(path, h.MAX_ARTIFACT_BYTES)
            h.require(h.digest(data) == ref["sha256"], f"Stale reference: {ref['path']}")
            h.nonempty(ref["contains"], "Reference symbol or heading")
            h.require(ref["contains"] in data.decode("utf-8-sig"), f"Missing reference symbol: {ref['path']}")
    h.require(len(covered) == len(set(covered)), "Duplicate coverage")
    h.require(set(covered) == {d["path"] for d in delta}, "Changed-file coverage mismatch (including new/deleted paths)")
    return {"result": "coverage_passed", "task_id": base["task_id"], "changed_paths": covered,
            "scope": base["scopes"], "changes_sha256": record["changes_sha256"],
            "semantic_quality": "NOT_VERIFIED", "h3_verdict": None}


def complete(args):
    """Extend existing result review, preserving all original bundle checks."""
    result = h.validate_result(args)
    _, manifest, packet = h.verified_bundle(args.bundle, args.rationale_root)
    base = load_baseline(args.rationale_baseline, args.rationale_baseline_sha256)
    h.require(base["task_id"] == manifest["task_id"], "Completion task identity mismatch")
    h.require(set(base["scopes"]) == set(packet["allowed_writes"]),
              "Frozen coverage scope must equal all packet Allowed Writes")
    worker = h.read_json(Path(args.result))
    report = h.no_links(Path(args.rationale_report))
    bundle = h.root_dir(args.bundle)
    h.require(report.is_relative_to(bundle), "Report must be an existing hashed result artifact")
    rel = report.relative_to(bundle).as_posix()
    h.require(any(a["path"] == rel for a in worker["artifacts"]), "Rationale report is not declared evidence")
    coverage = check(args.rationale_root, args.rationale_baseline, args.rationale_baseline_sha256, report)
    h.require(set(worker["changed_paths"]) == set(coverage["changed_paths"]), "Worker changed paths differ from actual changes")
    result.update(result="candidate_completion_checked", documentation=coverage)
    result["limitation"] = "Coverage and bundle freshness only; explanation truth, execution, independent H3 and owner acceptance remain separate."
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot", help="Emit task-start baseline to stdout; controller stores it")
    snap.add_argument("--root", required=True)
    snap.add_argument("--task-id", required=True)
    snap.add_argument("--scope", action="append", required=True)
    for verb in ("changes", "check"):
        cmd = sub.add_parser(verb)
        cmd.add_argument("--root", required=True)
        cmd.add_argument("--baseline", required=True)
        cmd.add_argument("--baseline-sha256", required=True)
        if verb == "check":
            cmd.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            out = snapshot(args.root, args.task_id, args.scope)
        elif args.command == "changes":
            _, delta = current_changes(args.root, args.baseline, args.baseline_sha256)
            out = {"changes": delta, "changes_sha256": h.digest(h.json_bytes(delta))}
        else:
            out = check(args.root, args.baseline, args.baseline_sha256, args.report)
        sys.stdout.buffer.write(h.json_bytes(out))
        return 0
    except (h.HandoffError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"result": "rejected", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
