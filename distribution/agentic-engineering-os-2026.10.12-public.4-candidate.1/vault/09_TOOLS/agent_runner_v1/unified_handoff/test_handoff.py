"""Deterministic adapter tests. Fixtures stay under this new tool subtree."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import handoff


def packet_text(*, worker_tool="Codex", status="approved", schema="1.2", reads=None, writes=None):
    """Synthetic test-only packet; never approval for a real assignment."""
    reads = reads or ["00_SYSTEM/policy.md"]
    writes = writes if writes is not None else ["01_PROJECTS/Demo/**"]
    paths = "\n".join(f"- `{path}`" for path in reads)
    write_paths = "\n".join(f"- `{path}`" for path in writes) if writes else "None (read-only)"
    return f'''---
type: agent_task_packet
schema_version: "{schema}"
run_id: RUN-2026-09-04-901
task_id: TASK-2026-09-04-901
status: {status}
created: 2026-09-04
updated: 2026-09-04
project: Synthetic fixture only
project_path: 01_PROJECTS/Demo
role: Builder
worker_tool: {worker_tool}
risk_level: R2
h3_mode: full
repair_cycle_limit: 3
repair_cycles_used: 0
verification_lifecycle: pending
h3_verdict: null
human_gates: [C]
controller: Test harness; fixture only
---
# Synthetic packet; not real approval

## 1. Project
Fixture at `01_PROJECTS/Demo`. Routing is the policy fixture.

## 2. Task Identifier And Outcome
TASK-2026-09-04-901: a bounded draft report exists and passes the named file check.

## 3. Known Current State
Fixture worktree only. No external actions or live project state; input is a synthetic policy.

## 4. Assumptions
None.

## 5. Read First
{paths}

## 6. Allowed Reads
{paths}

## 7. Allowed Writes
{write_paths}

## 8. Forbidden Actions
Do not read secret or private data. Do not bypass a lock or human approval. Do not take external actions. Do not claim work without captured evidence. Do not publish, send, or promote canonical changes.

## 9. Acceptance Criteria
| ID | Observable criterion | Priority | Evidence required |
|---|---|---|---|
| AC1 | Draft report file exists with fixture findings. | must | artifacts/check.txt |

## 10. Verification Plan
Command/exact deterministic check: open the draft report and compare its first line with the policy fixture. Expected result: matching first line. Evidence: artifacts/check.txt.
Visual verification: not applicable because this is plain-text local packaging.
Preserved behavior: source files and live locks remain unchanged.

## 11. Delegated Agent Roles
Builder creates the draft; a different independent read-only H3 reviewer reviews captured evidence. Test fixture only.

## 12. Human Approval Gates
Synthetic packet approval is fixture data only. Gate C blocks canonical integration. No external action is authorized.

## 13. Writeback Targets
Only a proposed `01_PROJECTS/Demo/report.md`; no canonical writeback occurs in this fixture.

## 14. Expected Final Response
Return run/task IDs, worker, execution state, summary, changed paths, checks, evidence artifacts, risks, proposed writeback and next action. Independent H3 remains a separate reviewer record.

## 15. Stop Conditions
Stop for missing evidence, approval, scope/lock conflict, unavailable independent H3, or three unsuccessful repair cycles.

## 16. Repair Cycle Record
None; zero repair attempts.
'''


class AdapterTests(unittest.TestCase):
    def setUp(self):
        # Explicit absolute target under the allowed new subtree; TemporaryDirectory
        # owns and cleans only this directory and its synthetic children.
        self.parent = Path(__file__).resolve().parent
        self.temp = tempfile.TemporaryDirectory(prefix="test-work-", dir=self.parent)
        self.work = Path(self.temp.name).resolve()
        assert self.work.is_relative_to(self.parent)
        self.addCleanup(self.temp.cleanup)
        self.vault = self.work / "vault"
        self.vault.mkdir()
        self.put("00_SYSTEM/policy.md", "# Synthetic policy\nOnly a fixture.\n")
        self.put("task_packet.md", packet_text())
        self.bundle = self.work / "bundle"

    def put(self, rel, text):
        path = self.vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def build(self, **overrides):
        args = dict(vault_root=str(self.vault), packet="task_packet.md", executor="codex",
                    read=["00_SYSTEM/policy.md"], skill=[], output=str(self.bundle))
        args.update(overrides)
        return handoff.build(argparse.Namespace(**args))

    def check(self):
        return handoff.check(argparse.Namespace(bundle=str(self.bundle), vault_root=str(self.vault)))

    def result(self):
        evidence = b"Observed: synthetic report exists.\n"
        (self.bundle / "artifacts/check.txt").write_bytes(evidence)
        out = handoff.worker_template(handoff.parse_packet((self.vault / "task_packet.md").read_bytes())["frontmatter"], "codex")
        out.update(execution_state="ready_for_review", summary="Synthetic draft exists; worker claim pending independent review.",
                   artifacts=[{"path": "artifacts/check.txt", "sha256": hashlib.sha256(evidence).hexdigest(), "description": "Synthetic check evidence"}],
                   changed_paths=["01_PROJECTS/Demo/report.md"],
                   checks=[{"name": "Fixture check", "command": "Read synthetic report first line", "outcome": "passed", "evidence": "artifacts/check.txt"}],
                   risks=["Synthetic fixture only; no independent H3 or live executor test."],
                   proposed_writeback=[{"target": "01_PROJECTS/Demo/report.md", "artifact": "artifacts/check.txt", "rationale": "Candidate only."}],
                   next_action="Have an independent reviewer inspect the candidate evidence.")
        return out

    def validate(self, result):
        path = self.bundle / "worker_result.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        return handoff.validate_result(argparse.Namespace(bundle=str(self.bundle), result=str(path)))

    def test_build_check_and_candidate_result(self):
        self.assertEqual(self.build()["result"], "candidate_built")
        self.assertEqual(self.check()["result"], "integrity_and_live_sources_match")
        result = self.validate(self.result())
        self.assertEqual(result["result"], "candidate_result_valid")
        self.assertIsNone(result["h3_verdict"])
        self.assertEqual(result["verification_lifecycle"], "needs-review")

    def test_all_executor_mappings(self):
        for executor, tool in handoff.EXECUTOR_TOOLS.items():
            with self.subTest(executor=executor):
                self.put("task_packet.md", packet_text(worker_tool=tool))
                self.build(executor=executor, output=str(self.work / executor))
        self.put("task_packet.md", packet_text(worker_tool="Grok"))
        with self.assertRaisesRegex(handoff.HandoffError, "requires packet worker_tool"):
            self.build()

    def test_draft_and_old_schema_rejected_without_output(self):
        for change in ({"status": "draft"}, {"status": "blocked"}, {"schema": "1.1"}):
            with self.subTest(change=change):
                self.put("task_packet.md", packet_text(**change))
                with self.assertRaises(handoff.HandoffError):
                    self.build()
                self.assertFalse(self.bundle.exists())

    def test_malformed_packet_rejected(self):
        for old, new in (("## 9. Acceptance Criteria", "## 9. Wrong section"),
                         ("repair_cycle_limit: 3", "repair_cycle_limit: 4"),
                         ("repair_cycles_used: 0", "repair_cycles_used: 3"),
                         ("h3_verdict: null", "h3_verdict: verified"),
                         ("| must | artifacts/check.txt |", "| must |  |"),
                         ("## 4. Assumptions\nNone.", "## 4. Assumptions\n- [ ] Ready")):
            with self.subTest(old=old):
                text = packet_text().replace(old, new)
                if text == packet_text():
                    text = packet_text().replace("## 4. Assumptions\n\nNone.", new)
                self.put("task_packet.md", text)
                with self.assertRaises(handoff.HandoffError):
                    self.build()

    def test_source_packet_and_context_drift(self):
        self.build()
        for relative in ("task_packet.md", "00_SYSTEM/policy.md"):
            original = (self.vault / relative).read_bytes()
            (self.vault / relative).write_bytes(original + b"\nDrift.\n")
            with self.assertRaisesRegex(handoff.HandoffError, "Live source drift"):
                self.check()
            (self.vault / relative).write_bytes(original)

    def test_snapshot_and_manifest_tamper(self):
        self.build()
        path = self.bundle / "context/01_policy.md"
        original = path.read_bytes()
        path.write_bytes(original + b"changed")
        with self.assertRaisesRegex(handoff.HandoffError, "Snapshot changed"):
            self.check()
        path.write_bytes(original)
        manifest = self.bundle / "context_manifest.json"
        manifest.write_bytes(manifest.read_bytes() + b" ")
        with self.assertRaisesRegex(handoff.HandoffError, "Manifest digest mismatch"):
            self.check()

    def test_output_collision_and_canonical_output_rejected(self):
        self.build()
        original = (self.bundle / "context_manifest.json").read_bytes()
        with self.assertRaisesRegex(handoff.HandoffError, "collision"):
            self.build()
        self.assertEqual((self.bundle / "context_manifest.json").read_bytes(), original)
        with self.assertRaisesRegex(handoff.HandoffError, "outside the source vault"):
            self.build(output=str(self.vault / "new-run"))

    def test_traversal_absolute_secret_and_raw_paths_rejected(self):
        for path in ("../outside.md", "00_SYSTEM/../outside.md", "/outside.md", "C:/private.md", ".env.md", "09_RAW_CAPTURE/note.md", "private/note.md", "notes/api_token.md", "notes\\policy.md", "notes/nul.md"):
            with self.subTest(path=path), self.assertRaises(handoff.HandoffError):
                self.build(read=[path])

    def test_symlink_source_or_root_rejected(self):
        target = self.vault / "00_SYSTEM/policy.md"
        link = self.vault / "00_SYSTEM/linked.md"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"OS does not permit synthetic symlink creation: {exc}")
        self.put("task_packet.md", packet_text(reads=["00_SYSTEM/linked.md"]))
        with self.assertRaisesRegex(handoff.HandoffError, "Symlink/junction/reparse"):
            self.build(read=["00_SYSTEM/linked.md"])

    def test_oversize_and_possible_secret_content_rejected(self):
        for content in ("x" * (handoff.MAX_FILE_BYTES + 1), "password: synthetic_long_secret_value\n"):
            self.put("00_SYSTEM/policy.md", content)
            with self.assertRaises(handoff.HandoffError):
                self.build()

    def test_scope_and_eight_file_budget(self):
        self.put("other.md", "# other")
        with self.assertRaisesRegex(handoff.HandoffError, "exceeds packet Allowed Reads"):
            self.build(read=["00_SYSTEM/policy.md", "other.md"])
        with self.assertRaisesRegex(handoff.HandoffError, "1 through 8"):
            self.build(read=[f"context/{i}.md" for i in range(9)])
        with self.assertRaisesRegex(handoff.HandoffError, "Every packet Read First"):
            self.build(read=["other.md"])

    def test_skill_snapshot_and_scope(self):
        skill = ".codex/skills/demo/SKILL.md"
        self.put(skill, "# Demo skill\nFollow packet scope.\n")
        self.put("task_packet.md", packet_text(reads=["00_SYSTEM/policy.md", skill]))
        self.build(skill=[skill])
        self.check()

    def test_registered_markdown_skill_snapshot(self):
        skill = "03_SKILLS/skills/context-router.md"
        self.put(skill, "# Registered skill\nFollow packet scope.\n")
        self.put("task_packet.md", packet_text(reads=["00_SYSTEM/policy.md", skill]))
        self.build(skill=[skill])
        self.check()

    def test_r2_independent_verifier_can_be_read_only(self):
        self.put("task_packet.md", packet_text(writes=[]).replace("role: Builder", "role: QA/H3 Verifier"))
        self.build()
        result = self.result()
        result["changed_paths"] = []
        result["proposed_writeback"] = []
        self.assertEqual(self.validate(result)["result"], "candidate_result_valid")
        result["changed_paths"] = ["01_PROJECTS/Demo/report.md"]
        with self.assertRaisesRegex(handoff.HandoffError, "exceeds Allowed Writes"):
            self.validate(result)

    def test_worker_authority_fields_forbidden(self):
        self.build()
        base = self.result()
        for field in ("h3_verdict", "owner_approval", "verification_lifecycle", "approved", "owner_decision"):
            result = copy.deepcopy(base)
            result[field] = "verified"
            with self.subTest(field=field), self.assertRaisesRegex(handoff.HandoffError, "authority-setting"):
                self.validate(result)
        result = copy.deepcopy(base)
        result["checks"][0]["h3_verdict"] = "verified"
        with self.assertRaisesRegex(handoff.HandoffError, "authority-setting"):
            self.validate(result)

    def test_result_identity_artifact_and_scope_rejections(self):
        self.build()
        base = self.result()
        for change in ({"run_id": "RUN-2026-09-04-999"}, {"worker": "hermes"},
                       {"execution_state": "verified"}, {"changed_paths": ["00_SYSTEM/policy.md"]}):
            result = copy.deepcopy(base)
            result.update(change)
            with self.subTest(change=change), self.assertRaises(handoff.HandoffError):
                self.validate(result)
        for path in ("artifacts/missing.txt", "../outside.txt", "context/01_policy.md"):
            result = copy.deepcopy(base)
            result["artifacts"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(handoff.HandoffError):
                self.validate(result)
        result = copy.deepcopy(base)
        result["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(handoff.HandoffError, "hash mismatch"):
            self.validate(result)

    def test_result_template_cannot_claim_a_run(self):
        self.build()
        template = json.loads((self.bundle / "worker_result.template.json").read_text())
        with self.assertRaisesRegex(handoff.HandoffError, "completed nonempty"):
            self.validate(template)


if __name__ == "__main__":
    unittest.main(verbosity=2)
