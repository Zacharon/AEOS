"""Synthetic boundary tests; no network, model, credentials or owner decisions."""
import json
from pathlib import Path
import tempfile
import unittest

import issue_handoff as P


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_draft_cannot_dispatch(self):
        run = P.prepare(P.HERE / "synthetic_issue.json", self.root / "run")
        self.assertIn("status: draft", (run / "worktree" / P.PACKET).read_text())
        with self.assertRaisesRegex(ValueError, "already be approved"):
            P.bundle(run)
        self.assertFalse((run / "handoff").exists())

    def test_existing_output_preserved(self):
        target = self.root / "run"
        target.mkdir()
        P.write(target / "sentinel.md", "preserve")
        with self.assertRaisesRegex(ValueError, "new absent"):
            P.prepare(P.HERE / "synthetic_issue.json", target)
        self.assertEqual((target / "sentinel.md").read_text(), "preserve")

    def test_issue_cannot_inject_packet_or_commands(self):
        run = P.prepare(P.HERE / "synthetic_issue.json", self.root / "run")
        text = (run / "worktree" / P.SELECTED[1]).read_text()
        recovered = json.loads(text.split("\n> ", 1)[1])
        original = json.loads((P.HERE / "synthetic_issue.json").read_text())
        self.assertEqual(recovered, original)
        self.assertEqual(text.count("\n## Allowed Writes"), 0)
        packet = (run / "worktree" / P.PACKET).read_text()
        self.assertNotIn("../../outside", packet)
        self.assertNotIn("$(echo unsafe)", packet)
        self.assertIn("None (read-only)", packet)
        self.assertFalse((self.root / "outside.md").exists())
        commands = [P.H.read_json(x)["argv"] for x in (run / "audit").glob("*.json")]
        self.assertFalse(any("unsafe" in str(c) or "example.invalid/attachment" in str(c) for c in commands))

    def test_bad_inputs_refused_before_output(self):
        base = json.loads((P.HERE / "synthetic_issue.json").read_text())
        cases = [dict(base, number=True), dict(base, body="x" * 16001),
                 dict(base, url="https://example.invalid/issue"), dict(base, number=1),
                 dict(base, labels=[{"name": 5}]), dict(base, body="ghp_" + "A" * 36),
                 dict(base, body="api_key: synthetic-credential-marker")]
        for index, case in enumerate(cases):
            source = self.root / f"input-{index}.json"
            P.write(source, case)
            with self.assertRaises(ValueError):
                P.prepare(source, self.root / f"run-{index}")
            self.assertFalse((self.root / f"run-{index}").exists())

    def test_duplicate_json_key_refused(self):
        source = self.root / "input.json"
        P.write(source, '{"number":1,"number":2}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            P.prepare(source, self.root / "run")

    def test_synthetic_mode_cannot_process_other_issue(self):
        case = json.loads((P.HERE / "synthetic_issue.json").read_text())
        case["title"] = "Other issue"
        source = self.root / "input.json"
        P.write(source, case)
        with self.assertRaisesRegex(ValueError, "only the shipped fixture"):
            P.prepare(source, self.root / "run", synthetic=True)
        self.assertFalse((self.root / "run").exists())

    def test_symlink_input_refused(self):
        link = self.root / "link.json"
        try:
            link.symlink_to(P.HERE / "synthetic_issue.json")
        except OSError:
            self.skipTest("Host does not grant symlink creation")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            P.prepare(link, self.root / "run")


class ReturnTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "run"
        self.receipt = P.demo(self.root)
        self.result_path = self.root / "handoff/worker_result.json"

    def mutate_result(self, **fields):
        result = P.H.read_json(self.result_path)
        result.update(fields)
        self.result_path.write_bytes(P.H.json_bytes(result))

    def test_round_trip_keeps_h3_and_owner_pending(self):
        self.assertEqual(self.receipt["status"], "candidate_needs_independent_H3")
        self.assertIsNone(self.receipt["h3_verdict"])
        self.assertEqual(self.receipt["owner_acceptance"], "pending")
        self.assertFalse(self.receipt["ai_worker_invoked"])
        self.assertFalse(self.receipt["external_actions"])
        self.assertEqual(P.tree(self.root / "worktree"), P.H.read_json(self.root / "baseline.json")["files"])
        self.assertTrue((self.root / "source/.git/worktrees/worktree").is_dir())
        events = [P.H.read_json(p) for p in (self.root / "audit").glob("*.json")]
        self.assertTrue(all(e["exit_code"] == 0 for e in events))
        self.assertIn("validate-result", [arg for e in events for arg in e["argv"]])

    def test_replay_cannot_overwrite_bundle(self):
        before = P.sha(self.root / "handoff/context_manifest.json")
        with self.assertRaisesRegex(ValueError, "Command failed"):
            P.bundle(self.root)
        self.assertEqual(before, P.sha(self.root / "handoff/context_manifest.json"))
        event = P.H.read_json(sorted((self.root / "audit").glob("*.json"))[-1])
        self.assertEqual(event["exit_code"], 2)

    def test_stale_live_source_refused(self):
        path = self.root / "worktree" / P.SELECTED[0]
        path.write_text("changed")
        with self.assertRaisesRegex(ValueError, "Unexpected worktree"):
            P.verify(self.root)
        # Also exercise the upstream check independently of wrapper inventory.
        P.hand(self.root, "check", "--bundle", str(self.root / "handoff"),
               "--vault-root", str(self.root / "worktree"), expected=2)

    def test_missing_source_refused(self):
        (self.root / "worktree" / P.SELECTED[0]).unlink()
        P.hand(self.root, "check", "--bundle", str(self.root / "handoff"),
               "--vault-root", str(self.root / "worktree"), expected=2)
        with self.assertRaises(ValueError):
            P.verify(self.root)

    def test_snapshot_tamper_refused(self):
        snapshot = next((self.root / "handoff/context").glob("*PROJECT_INDEX.md"))
        snapshot.write_text("changed")
        with self.assertRaisesRegex(ValueError, "Command failed"):
            P.verify(self.root)

    def test_manifest_reseal_cannot_override_controller_baseline(self):
        path = self.root / "handoff/context_manifest.json"
        manifest = P.H.read_json(path)
        manifest["created_utc"] = "different"
        path.write_bytes(P.H.json_bytes(manifest))
        (self.root / "handoff/context_manifest.sha256").write_text(P.sha(path) + "  context_manifest.json\n")
        with self.assertRaisesRegex(ValueError, "Manifest drift"):
            P.verify(self.root)

    def test_artifact_tamper_refused(self):
        (self.root / "handoff/artifacts/report.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "Command failed"):
            P.verify(self.root)

    def test_self_hashed_incorrect_report_refused(self):
        report = self.root / "handoff/artifacts/report.json"
        value = P.H.read_json(report)
        value["label_count"] = 999
        report.write_bytes(P.H.json_bytes(value))
        result = P.H.read_json(self.result_path)
        result["artifacts"][0]["sha256"] = P.sha(report)
        self.mutate_result(artifacts=result["artifacts"])
        with self.assertRaisesRegex(ValueError, "does not match source"):
            P.verify(self.root)

    def test_worker_h3_claim_refused(self):
        self.mutate_result(h3_verdict="VERIFIED")
        with self.assertRaisesRegex(ValueError, "Command failed"):
            P.verify(self.root)

    def test_declared_out_of_scope_write_refused(self):
        self.mutate_result(changed_paths=["01_PROJECTS/Issue/PROJECT_INDEX.md"])
        with self.assertRaisesRegex(ValueError, "Command failed"):
            P.verify(self.root)

    def test_undeclared_worktree_write_refused(self):
        P.write(self.root / "worktree/unreported.md", "unexpected")
        with self.assertRaisesRegex(ValueError, "Unexpected worktree"):
            P.verify(self.root)

    def test_failed_check_cannot_pass_candidate_gate(self):
        result = P.H.read_json(self.result_path)
        result["checks"][0]["outcome"] = "failed"
        self.mutate_result(checks=result["checks"])
        with self.assertRaisesRegex(ValueError, "Candidate blocked/failed"):
            P.verify(self.root)

    def test_missing_worker_result_stops_instead_of_redispatch(self):
        self.result_path.unlink()
        with self.assertRaisesRegex(ValueError, "Command failed"):
            P.verify(self.root)


if __name__ == "__main__":
    unittest.main()
