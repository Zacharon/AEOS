#!/usr/bin/env python3
"""Bounded local documentation handoffs; structural checks, never execution or approval."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff"
sys.path.insert(0, str(TOOLS))
import handoff as h
import code_rationale as rationale

# Exact complete guide, normalized only for cross-platform line endings.
CONTRACT = ROOT / "prototypes/issue_handoff/WORKER_CONTRACT.md"
CONTRACT_SHA256 = "d011946cd4746f75f432fcd2515d6e46e5d702babd1edde2f5536fb3bb6fd98d"
LIMITATION = ("Structural applicability and byte identity only; commands are never executed. "
              "The controller must rerun prescribed checks. Prose quality, authenticated approval, "
              "independent H3 and owner acceptance remain unverified. Protect controller records "
              "outside worker write access; their hashes are not authentication.")


def raw(path, limit=h.MAX_ARTIFACT_BYTES):
    path = h.no_links(Path(path))
    h.require(path.is_file() and path.stat().st_nlink == 1, f"Missing or hardlinked file: {path}")
    return h.read_bytes(path, limit)


def load(path):
    return json.loads(raw(path, h.MAX_RESULT_BYTES), object_pairs_hook=h.no_duplicate_pairs)


def save(path, value):
    path = h.no_links(Path(path))
    with path.open("xb") as stream:
        stream.write(h.json_bytes(value))


def paths(value, label, *, grants=False, nonempty=False):
    h.require(isinstance(value, list) and len(value) <= 100 and (value or not nonempty), f"Invalid {label} list")
    out = [h.safe_relative(p, grant=grants) for p in value]
    h.require(len({p.casefold() for p in out}) == len(out), f"Duplicate {label}")
    return out


def overlap(a, b):
    a, b = a.casefold(), b.casefold()
    return a == b or (a.endswith('/**') and b.startswith(a[:-2])) or (b.endswith('/**') and a.startswith(b[:-2]))


def contract_bytes(data):
    return data.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")


def inspect(root_value, packet_value):
    root = h.root_dir(root_value)
    packet_path = h.safe_relative(packet_value, markdown=True)
    packet_data = raw(h.within(root, packet_path), h.MAX_FILE_BYTES)
    h.markdown_bytes(h.within(root, packet_path))
    packet = h.parse_packet(packet_data)
    text = packet_data.decode("utf-8-sig").replace("\r\n", "\n")
    fences = re.findall(r"^```context-selection\n(.*?)\n```[ \t]*$", text, re.M | re.S)
    h.require(len(fences) == 1 and len(re.findall(r"^```context-selection\b", text, re.M)) == 1,
              "Packet needs exactly one closed context-selection JSON fence")
    meta = json.loads(fences[0], object_pairs_hook=h.no_duplicate_pairs)
    h.exact_keys(meta, {"sources", "dependencies", "contracts", "documentation", "required_artifacts", "required_checks"}, "Context selection")
    h.require(isinstance(meta["sources"], list) and 1 <= len(meta["sources"]) <= 100, "Invalid sources")
    active, records, scopes = [], {}, set()
    dependencies = paths(meta["dependencies"], "dependencies")
    for source in meta["sources"]:
        h.exact_keys(source, {"path", "scope", "authority", "status", "replacement", "references"}, "Source")
        path = h.safe_relative(source["path"], markdown=True)
        h.require(path.casefold() not in records, "Duplicate source path")
        records[path.casefold()] = source
        h.nonempty(source["scope"], "source scope")
        h.nonempty(source["authority"], "source authority purpose")
        h.require(source["status"] in {"active", "archived", "superseded"}, "Invalid source status")
        if source["replacement"] is not None:
            h.safe_relative(source["replacement"], markdown=True)
        refs = paths(source["references"], "source references")
        # Validate named paths only, never discover or recursively follow document links.
        source_path = h.within(root, path)
        h.require(source_path.is_file() and source_path.stat().st_nlink == 1, "Missing or hardlinked source")
        if source["status"] == "active":
            h.require(h.covered(path, packet["allowed_reads"]), "Active source exceeds Allowed Reads")
            h.require(source["replacement"] is None, "Active source cannot have a replacement")
            h.require(source["scope"].casefold() not in scopes, "Conflicting active canonical scope")
            scopes.add(source["scope"].casefold())
            data = raw(h.within(root, path), h.MAX_FILE_BYTES)
            h.markdown_bytes(h.within(root, path))
            front = re.match(r"\A---\n(.*?)\n---(?:\n|$)", data.decode("utf-8-sig").replace("\r\n", "\n"), re.S)
            if front:
                for key in ("status", "scope"):
                    values = re.findall(r"^" + key + r":\s*(.*?)\s*$", front[1], re.M)
                    h.require(len(values) <= 1, "Ambiguous source frontmatter")
                    if values:
                        value = h.scalar(values[0])
                        if key == "status":
                            h.require(isinstance(value, str) and value.casefold() not in {"archived", "superseded", "rejected"}, "Active selection contradicts source status")
                        else:
                            h.require(value == source["scope"], "Source scope contradicts metadata")
            active.append(path)
            dependencies.extend(refs)
        else:
        # Excluded sources are named metadata, not implicit reads of historical content.
            h.require(h.within(root, path).is_file(), f"Missing historical source: {path}")
        for ref in refs:
            h.require(h.covered(ref, packet["allowed_reads"]), "Required reference exceeds Allowed Reads")
            raw(h.within(root, ref))
    for source in meta["sources"]:
        replacement = source["replacement"]
        h.require(source["status"] != "superseded" or replacement is not None, "Superseded source requires active replacement")
        if replacement is not None:
            target = records.get(replacement.casefold())
            h.require(target is not None and target["path"] == replacement and target["status"] == "active" and target["scope"] == source["scope"], "Replacement must be active in the same scope")
    h.require(1 <= len(active) <= 8, "Select one through eight active sources")
    h.require(set(packet["read_first"]) <= set(active), "Read First must be a subset of active selection")
    h.require(all(h.covered(p, packet["allowed_reads"]) for p in active), "Active source exceeds Allowed Reads")
    h.exact_keys(meta["contracts"], {"return", "rationale"}, "Contracts")
    for path in meta["contracts"].values():
        h.safe_relative(path, markdown=True)
        h.require(path in active, "Complete return and rationale contracts must be selected")
        h.require(h.digest(contract_bytes(raw(h.within(root, path)))) == CONTRACT_SHA256, "Incomplete or unsupported worker contract")
    dependencies = sorted(set(dependencies))
    for path in [packet_path, *active, *dependencies]:
        h.require(not any(overlap(path, grant) for grant in packet["allowed_writes"]), "Selected inputs/dependencies cannot overlap Allowed Writes")
        h.require(path == packet_path or h.covered(path, packet["allowed_reads"]), "Dependency exceeds Allowed Reads")
        raw(h.within(root, path))
    h.require(isinstance(meta["documentation"], list) and len(meta["documentation"]) <= 100, "Invalid documentation mapping")
    for rule in meta["documentation"]:
        h.exact_keys(rule, {"paths", "documents"}, "Documentation impact")
        grants = paths(rule["paths"], "impact paths", grants=True, nonempty=True)
        rule["paths"] = grants
        docs = paths(rule["documents"], "impact documents", nonempty=True)
        for grant in grants:
            h.require(h.covered(grant, packet["allowed_writes"]), "Impact path exceeds Allowed Writes")
        for doc in docs:
            h.require(h.covered(doc, packet["allowed_reads"]) or h.covered(doc, packet["allowed_writes"]), "Documentation exceeds packet scope")
            target = h.within(root, doc)
            if target.exists():
                raw(target)
            else:
                h.require(h.covered(doc, packet["allowed_writes"]), "Missing documentation outside Allowed Writes")
    artifacts = paths(meta["required_artifacts"], "required artifacts", nonempty=True)
    h.require("artifacts/report.md" in artifacts and all(p.startswith("artifacts/") for p in artifacts), "Require artifacts/report.md and artifact-relative evidence paths")
    checks = meta["required_checks"]
    h.require(isinstance(checks, list) and 1 <= len(checks) <= 100, "Invalid required checks")
    for check in checks:
        h.nonempty(check, "required check name")
    h.require(len({c.casefold() for c in checks}) == len(checks), "Duplicate required check")
    h.require(packet_path not in active, "Packet cannot be its own selected context")
    h.require(sum(len(raw(h.within(root, p), h.MAX_FILE_BYTES)) for p in [packet_path, *active]) <= h.MAX_TOTAL_BYTES, "Context budget exceeded")
    return root, packet, meta, active, dependencies


def lint(root, packet):
    _, _, meta, active, deps = inspect(root, packet)
    return {"result": "selection_valid", "active": active, "excluded": [s for s in meta["sources"] if s["status"] != "active"],
            "dependencies": deps, "documentation": meta["documentation"], "limitation": LIMITATION}


def history(root, packet, path):
    root, parsed, meta, _, _ = inspect(root, packet)
    h.safe_relative(path, markdown=True)
    h.require(h.covered(path, parsed["allowed_reads"]), "Historical lookup exceeds Allowed Reads")
    source = next((s for s in meta["sources"] if s["path"] == path), None)
    h.require(source is not None and source["status"] != "active", "History requires an explicitly named historical source")
    data = raw(h.within(root, path), h.MAX_FILE_BYTES)
    h.markdown_bytes(h.within(root, path))
    return {"result": "historical_content_only", "classification": source["status"], "path": path,
            "replacement": source["replacement"], "content": data.decode("utf-8-sig"), "executable_packet": False}


def identity(root):
    # Read-only Git queries; no packet command or ambient Git environment is used.
    if not (root / ".git").exists():
        return None
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    def git(*args):
        proc = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull, "-C", str(root), "rev-parse", *args],
                              env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
        h.require(proc.returncode == 0, "Unable to verify Git identity")
        return proc.stdout.strip()
    return {"root": git("--show-toplevel"), "branch": git("--abbrev-ref", "HEAD"), "head": git("HEAD")}


def controls():
    # WHY: docs/DOCUMENTATION_PR_WORKFLOW.md#design-and-limits separates drift
    # detection from authentication; these records require controller protection.
    return {"adapter": h.digest(raw(Path(__file__))), "worker_contract": h.digest(raw(CONTRACT)), **rationale.controls()}


def prepare(root, packet, output, executor=None):
    root, parsed, meta, active, deps = inspect(root, packet)
    output_arg = Path(output)
    h.require(output_arg.is_absolute() and ".." not in output_arg.parts, "Output must be absolute without traversal")
    output = h.no_links(output_arg)
    h.require(not output.exists() and output.parent.is_dir() and not output.is_relative_to(root), "Output must be a new outside-root directory with an existing parent")
    matches = [e for e, tool in h.EXECUTOR_TOOLS.items() if tool == parsed["frontmatter"]["worker_tool"]]
    executor = executor or (matches[0] if len(matches) == 1 else None)
    h.require(executor in matches, "Choose an executor matching the authoritative packet")
    baseline = rationale.snapshot(root, parsed["frontmatter"]["task_id"], parsed["allowed_writes"])
    frozen = {p: h.digest(raw(h.within(root, p))) for p in sorted(set([packet, *active, *deps]))}
    control = {"root": str(root), "packet": packet, "git": identity(root), "controls": controls(), "inputs": frozen,
               "baseline_sha256": h.digest(h.json_bytes(baseline))}
    output.mkdir()
    (output / "controller").mkdir()
    built = h.build(argparse.Namespace(vault_root=str(root), packet=packet, executor=executor, read=active, skill=[], output=str(output / "bundle")))
    h.check(argparse.Namespace(bundle=str(output / "bundle"), vault_root=str(root)))
    control["manifest_sha256"] = built["manifest_sha256"]
    save(output / "controller/baseline.json", baseline)
    save(output / "controller/prepared.json", control)
    save(output / "controller/prepared.sha256", h.digest(h.json_bytes(control)))
    check(output)
    return {"result": "prepared_candidate_only", "run": str(output), "bundle": str(output / "bundle"), "baseline_sha256": control["baseline_sha256"], "limitation": LIMITATION}


def current(run_value):
    run = h.root_dir(run_value)
    control = load(h.within(run, "controller/prepared.json"))
    h.require(h.digest(raw(run / "controller/prepared.json")) == load(run / "controller/prepared.sha256"), "Controller record changed")
    h.exact_keys(control, {"root", "packet", "git", "controls", "inputs", "baseline_sha256", "manifest_sha256"}, "Controller record")
    h.require(control["controls"] == controls(), "Adapter or validator controls changed; reconcile in a fresh run")
    root = h.root_dir(control["root"])
    h.require(identity(root) == control["git"], "Git identity changed")
    bundle = h.root_dir(run / "bundle")
    h.require(h.digest(raw(bundle / "context_manifest.json")) == control["manifest_sha256"], "Manifest differs from trusted controller digest")
    h.verified_bundle(bundle, root)
    _, packet, meta, active, deps = inspect(root, control["packet"])
    expected = sorted(set([control["packet"], *active, *deps]))
    h.require(control["inputs"] == {p: h.digest(raw(h.within(root, p))) for p in expected}, "Selected source or dependency changed; reconcile in a fresh run")
    base, delta = rationale.current_changes(root, run / "controller/baseline.json", control["baseline_sha256"])
    h.require(base["task_id"] == packet["frontmatter"]["task_id"] and set(base["scopes"]) == set(packet["allowed_writes"]), "Baseline identity/scope mismatch")
    return run, root, bundle, control, meta, delta


def candidate(run, root, bundle, control, meta, delta):
    result_path = bundle / "worker_result.json"
    result = load(result_path)
    # Frozen validation reads artifact/reference bytes. Reject aliases first,
    # so a later hash rejection cannot accidentally read outside the boundary.
    h.require(isinstance(result.get("artifacts"), list), "Artifacts must be a list")
    for artifact in result["artifacts"]:
        h.exact_keys(artifact, {"path", "sha256", "description"}, "Artifact")
        path = h.safe_relative(artifact["path"])
        h.require(path.startswith("artifacts/"), "Evidence must be under artifacts/")
        target = h.within(bundle, path)
        h.require(target.is_file() and target.stat().st_nlink == 1, "Missing or hardlinked artifact")
    h.validate_result(argparse.Namespace(bundle=str(bundle), result=str(result_path)))
    h.require(result["execution_state"] == "ready_for_review", "Worker must return ready_for_review")
    artifacts = {a["path"] for a in result["artifacts"]}
    h.require(set(meta["required_artifacts"]) <= artifacts, "Missing required artifact")
    check_names = [c["name"] for c in result["checks"]]
    h.require(len({n.casefold() for n in check_names}) == len(check_names), "Duplicate worker check names")
    checks = {c["name"]: c for c in result["checks"]}
    h.require(all(n in checks and checks[n]["outcome"] == "passed" for n in meta["required_checks"]), "Missing or nonpassing required check")
    h.require(all(c["outcome"] in {"passed", "not_run"} for c in result["checks"]), "Failed or blocked checks require reconciliation")
    report = bundle / "artifacts/report.md"
    record = rationale.report_record(report)
    packet = h.parse_packet(raw(bundle / "task_packet.md", h.MAX_FILE_BYTES))
    h.require(isinstance(record.get("entries"), list), "Rationale entries must be a list")
    for entry in record["entries"]:
        h.require(isinstance(entry, dict) and isinstance(entry.get("references"), list), "Invalid rationale references")
        for ref in entry["references"]:
            h.exact_keys(ref, {"path", "sha256", "contains"}, "Reference")
            path = h.safe_relative(ref["path"])
            h.require(h.covered(path, packet["allowed_reads"] + packet["allowed_writes"]), "Rationale reference exceeds packet scope")
            target = h.within(root, path)
            h.require(target.is_file() and target.stat().st_nlink == 1, "Missing or hardlinked rationale reference")
    completion = rationale.complete(argparse.Namespace(bundle=str(bundle), result=str(result_path), rationale_root=str(root),
        rationale_baseline=str(run / "controller/baseline.json"), rationale_baseline_sha256=control["baseline_sha256"], rationale_report=str(report)))
    prose = re.sub(r"```code-rationale\n.*?\n```", "", raw(report).decode("utf-8-sig").replace("\r\n", "\n"), flags=re.S)
    prose = "\n".join(line for line in prose.splitlines() if not line.lstrip().startswith("#"))
    h.require(re.search(r"\bdocumentation\b", prose, re.I) and len(prose.split()) >= 12, "Report must explain the documentation delta in prose")
    changed = {d["path"] for d in delta}
    impacts, document_hashes = [], {}
    for rule in meta["documentation"]:
        affected = sorted(p for p in changed if h.covered(p, rule["paths"]))
        if not affected:
            continue
        for doc in rule["documents"]:
            document_hashes[doc] = h.digest(raw(h.within(root, doc)))
        documented = bool(changed & set(rule["documents"]))
        # A structural anchor makes each waiver specific to the impacted change;
        # whether its explanation is true remains a reviewer decision.
        waived = {p for e in record["entries"] if e["disposition"] == "documentation-not-needed"
                  for p in e["paths"] if p in e["why"]}
        h.require(documented or set(affected) <= waived, "Impacted scope needs changed documentation or specific documentation-not-needed rationale")
        impacts.append({"changed_paths": affected, "documents": rule["documents"], "disposition": "documentation_changed" if documented else "documentation-not-needed"})
    refs = {r["path"]: h.digest(raw(h.within(root, r["path"]))) for e in record["entries"] for r in e["references"]}
    return {"result": "structurally_verified_candidate", "verification_lifecycle": "needs-review", "semantic_quality": "NOT_VERIFIED", "h3_verdict": None,
            "changes_sha256": h.digest(h.json_bytes(delta)), "prepared_sha256": h.digest(raw(run / "controller/prepared.json")),
            "inputs": control["inputs"], "result_sha256": h.digest(raw(result_path)),
            "artifacts": {p: h.digest(raw(h.within(bundle, p))) for p in sorted(artifacts)}, "references": refs,
            "optional_not_run": [c for c in result["checks"] if c["outcome"] == "not_run"], "documentation_impacts": impacts,
            "documents": document_hashes,
            "completion": completion["result"], "limitation": LIMITATION}


def check(run):
    state = current(run)
    receipt = state[0] / "controller/verification.json"
    if receipt.exists():
        h.require(load(receipt) == candidate(*state), "Verification receipt is stale; reconcile in a fresh run")
    return {"result": "current", "receipt": str(receipt) if receipt.exists() else None, "limitation": LIMITATION}


def verify(run):
    # WHY: docs/DOCUMENTATION_PR_WORKFLOW.md#design-and-limits requires a fresh
    # reconciliation after drift, never silently refreshing an old receipt.
    state = current(run)
    value = candidate(*state)
    receipt = state[0] / "controller/verification.json"
    if receipt.exists():
        h.require(load(receipt) == value, "Verification receipt is stale; reconcile in a fresh run")
    else:
        save(receipt, value)
    return {"result": value["result"], "receipt": str(receipt), "limitation": LIMITATION}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("lint", "history", "prepare"):
        sub = commands.add_parser(name)
        sub.add_argument("--root", required=True)
        sub.add_argument("--packet", required=True)
        if name == "history":
            sub.add_argument("--path", required=True)
        if name == "prepare":
            sub.add_argument("--output", required=True)
            sub.add_argument("--executor", choices=h.EXECUTORS)
    for name in ("check", "verify"):
        sub = commands.add_parser(name)
        sub.add_argument("--run", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    try:
        print(json.dumps(globals()[command](**args), indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, UnicodeError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({"result": "rejected", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
