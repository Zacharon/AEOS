"""Run a synthetic source-to-candidate workflow using the packaged public CLIs.

This is deterministic demonstration code, not an AI executor. It never edits
owner decision fields, applies Gold, or reports its own independent H3 verdict.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(cmd, log, expected=0):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    log.append({"command": cmd, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    if p.returncode != expected:
        raise RuntimeError(f"Expected {expected}, got {p.returncode}: {p.stderr or p.stdout}")
    return json.loads(p.stdout) if p.stdout.strip().startswith("{") else p.stdout

def demo(package, output):
    package, output = package.resolve(), output.absolute()
    if output.exists():
        raise ValueError("Use a new absent demo directory; prior evidence is preserved")
    for p in (output, *output.parents):
        if p.is_symlink() or getattr(p, "is_junction", lambda: False)():
            raise ValueError("Demo destination cannot use aliases")
    subprocess.run([sys.executable, "-B", str(package / "scripts/check_package.py"), str(package)], check=True, capture_output=True)
    output.mkdir()
    vault = output / "vault"
    shutil.copytree(package / "vault", vault)
    log = []
    lib = [sys.executable, "-B", str(vault / "00_SYSTEM/AGENTIC_LIBRARIAN/librarian.py"), "--vault-root", str(vault)]
    source = run(lib + ["ingest", str(package / "examples/source.md"), "--project", "Sample", "--source-reliability", "internal_project_artifact", "--source-author", "Setup demonstration"], log)
    proposal = run(lib + ["propose", "--project", "Sample", "--proposal-type", "CREATE_KNOWLEDGE", "--risk", "low", "--confidence", "medium", "--title", "Sample source summary", "--summary", "Synthetic candidate remains pending owner review.", "--target", "04_RESEARCH/Sample_summary.md", "--source-id", source["source_id"], "--proposed-file", str(package / "examples/candidate.md")], log)
    run(lib + ["verify", proposal["proposal_id"]], log)
    # Read the generated proposal as evidence, never an authorization source.
    proposal_path = vault / proposal["proposal_path"]
    import yaml
    meta = yaml.safe_load(proposal_path.read_text(encoding="utf8").split("---", 2)[1])
    assert meta["owner_decision"] == "pending" and meta["status"] == "pending"
    selected = ["01_PROJECTS/Sample/PROJECT_STATE.md", source["stored_path"], proposal["proposal_path"], meta["proposed_content_path"]]
    packet_path = vault / "09_TOOLS/agent_runner_v1/runs/sample/task_packet.md"
    packet_path.parent.mkdir(parents=True)
    packet = (package / "examples/task_packet.md").read_text(encoding="utf8")
    packet = packet.replace("__READS__", "\n".join(f"- `{p}`" for p in selected))
    packet_path.write_text(packet, encoding="utf8")
    bundle = output / "handoff"
    hand = [sys.executable, "-B", str(vault / "09_TOOLS/agent_runner_v1/unified_handoff/handoff.py")]
    cmd = hand + ["build", "--vault-root", str(vault), "--packet", packet_path.relative_to(vault).as_posix(), "--executor", "human", "--output", str(bundle)]
    for rel in selected:
        cmd += ["--read", rel]
    run(cmd, log)
    run(hand + ["check", "--vault-root", str(vault), "--bundle", str(bundle)], log)
    manifest = json.loads((bundle / "context_manifest.json").read_text())
    record = next(r for r in manifest["sources"] if r["source"] == source["stored_path"])
    text = (bundle / record["snapshot"]).read_text(encoding="utf8")
    rows = [line.split("|")[1:-1] for line in text.splitlines() if line.startswith("| ") and " | done |" in line]
    done = len(rows)
    assert done == 2, "Source-grounded count differs from sample acceptance"
    report = bundle / "artifacts/report.md"
    report.write_text(f"# Sample result\n\n{done} items have recorded checks. The pending item still needs review.\n\nSource: `{record['source']}` SHA-256 `{record['sha256']}`.\n\nProposal `{proposal['proposal_id']}` is pending; it supplies candidate context, not approved policy. No Gold target was written.\n", encoding="utf8")
    result = json.loads((bundle / "worker_result.template.json").read_text())
    result.update(execution_state="ready_for_review", summary="Two checked sample items found in the captured source; Silver stays pending.",
                  artifacts=[{"path": "artifacts/report.md", "sha256": digest(report), "description": "Deterministic sample source count and provenance"}],
                  changed_paths=[], checks=[{"name": "Source count", "command": "demo.py: count done rows in selected source snapshot", "outcome": "passed", "evidence": "artifacts/report.md"}],
                  risks=["Synthetic deterministic demonstration; no AI executor, independent H3, owner acceptance or Gold apply."],
                  proposed_writeback=[], next_action="Review the remaining sample item and the pending Silver proposal; obtain separate owner approval before Gold application.")
    (bundle / "worker_result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    run(hand + ["validate-result", "--bundle", str(bundle), "--result", str(bundle / "worker_result.json")], log)
    review = run(hand + ["review", "--bundle", str(bundle), "--vault-root", str(vault)], log)
    # Fault injection touches only this disposable demo source, then restores its
    # exact bytes. It proves the stale/missing refusal without mutating Bronze.
    state = vault / selected[0]
    before = state.read_bytes()
    try:
        state.write_bytes(before + b"\nSynthetic changed state.\n")
        run(hand + ["review", "--bundle", str(bundle), "--vault-root", str(vault)], log, 2)
        state.unlink()
        run(hand + ["review", "--bundle", str(bundle), "--vault-root", str(vault)], log, 2)
    finally:
        state.write_bytes(before)
    run(hand + ["review", "--bundle", str(bundle), "--vault-root", str(vault)], log)
    assert not (vault / "04_RESEARCH/Sample_summary.md").exists()
    (output / "commands.json").write_text(json.dumps(log, indent=2), encoding="utf8")
    receipt = {"result": "DEMO_LOCAL_PASSED", "source_id": source["source_id"], "proposal_id": proposal["proposal_id"],
               "owner_decision": "pending", "gold_applied": False, "ai_worker_invoked": False, "h3_verdict": None,
               "source_count_done": done, "stale_and_missing_refused": True, "fresh_review": review,
               "next_action": "Open handoff/artifacts/report.md and the Silver proposal; continue through independent review."}
    (output / "RESULT.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
    (output / "START_HERE.md").write_text("# Continue this demonstration\n\nRead RESULT.json, then handoff/task_packet.md and handoff/artifacts/report.md. The source is synthetic, Silver is pending, H3 and owner acceptance are not claimed.\n\nRun from this directory:\n\n```powershell\npython -B vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py review --bundle handoff --vault-root vault\n```\n", encoding="utf8")
    return {"result": receipt["result"], "output": str(output), "entry": str(output / "START_HERE.md")}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    print(json.dumps(demo(Path(__file__).resolve().parents[1], Path(a.output)), indent=2))
