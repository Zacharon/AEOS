"""Synthetic negative controls; no product repository or approval is exercised."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import code_rationale as c
import handoff as h
from test_handoff import packet_text


class RationaleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rationale-", dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name).resolve()
        self.root = self.work / "repo"
        self.root.mkdir()
        self.put("src/a.py", "# Existing dirty bytes, not HEAD\nvalue = 2\n")
        self.put("GUIDE.md", "# Editing values\nChange src/a.py; preserve integer values.\n")
        self.baseline = self.work / "baseline.json"
        self.report = self.work / "REPORT.md"
        self.task = "TASK-2026-09-04-901"
        self.freeze()

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")
        return target

    def freeze(self, scopes=None):
        self.base = c.snapshot(self.root, self.task, scopes or ["src/**"])
        raw = h.json_bytes(self.base)
        self.baseline.write_bytes(raw)
        self.seal = h.digest(raw)

    def record(self, disposition="documented"):
        _, delta = c.current_changes(self.root, self.baseline, self.seal)
        entries = []
        if delta:
            entries = [{"paths": [d["path"] for d in delta], "disposition": disposition,
                        "why": "Use the corrected fixture value.", "where_to_edit": "src/a.py value assignment",
                        "constraints": "Retain integer representation.",
                        "verification": "Fixture equality checked; no product runtime claim.",
                        "references": [] if disposition == "documentation-not-needed" else
                        [{"path": "GUIDE.md", "sha256": h.digest((self.root / "GUIDE.md").read_bytes()), "contains": "# Editing values"}]}]
        return {"task_id": self.task, "baseline_sha256": self.seal,
                "changes_sha256": h.digest(h.json_bytes(delta)), "entries": entries}

    def save(self, record):
        self.report.write_text("# Existing task report\n\n```code-rationale\n" + json.dumps(record) + "\n```\n", encoding="utf-8")

    def check(self):
        return c.check(self.root, self.baseline, self.seal, self.report)

    def test_missing_rationale_fails(self):
        self.put("src/a.py", "value = 3\n")
        self.report.write_text("# No rationale", encoding="utf-8")
        with self.assertRaisesRegex(h.HandoffError, "exactly one"):
            self.check()

    def test_broken_reference_fails(self):
        self.put("src/a.py", "value = 3\n")
        record = self.record()
        record["entries"][0]["references"][0]["path"] = "missing.md"
        self.save(record)
        with self.assertRaisesRegex(h.HandoffError, "missing"):
            self.check()

    def test_older_change_record_fails(self):
        self.put("src/a.py", "value = 3\n")
        self.save(self.record())
        self.put("src/a.py", "value = 4\n")
        with self.assertRaisesRegex(h.HandoffError, "older change"):
            self.check()

    def test_untracked_source_omitted_fails(self):
        self.put("src/a.py", "value = 3\n")
        self.put("src/new.language", "new source\n")
        record = self.record()
        record["entries"][0]["paths"] = ["src/a.py"]
        self.save(record)
        with self.assertRaisesRegex(h.HandoffError, "coverage mismatch"):
            self.check()

    def test_simple_change_no_new_inline_comment_passes(self):
        self.put("src/a.py", "value = 3\n")
        self.save(self.record("documentation-not-needed"))
        self.assertEqual(self.check()["result"], "coverage_passed")
        self.assertEqual(self.check()["semantic_quality"], "NOT_VERIFIED")

    def test_preexisting_dirty_and_untracked_not_attributed(self):
        self.put("src/preexisting.py", "existing = True\n")
        self.freeze()
        self.save(self.record())
        self.assertEqual(self.check()["changed_paths"], [])
        self.put("src/a.py", "value = 3\n")
        self.save(self.record())
        self.assertEqual(self.check()["changed_paths"], ["src/a.py"])

    def test_rename_with_edit_requires_both_paths(self):
        (self.root / "src/a.py").rename(self.root / "src/b.py")
        self.put("src/b.py", "value = 4\n")
        self.save(self.record())
        self.assertEqual(set(self.check()["changed_paths"]), {"src/a.py", "src/b.py"})
        delta = c.current_changes(self.root, self.baseline, self.seal)[1]
        self.assertEqual([d["kind"] for d in delta], ["deleted", "added"])

    def test_deleted_file_still_requires_record(self):
        (self.root / "src/a.py").unlink()
        record = self.record()
        record["entries"] = []
        self.save(record)
        with self.assertRaisesRegex(h.HandoffError, "coverage mismatch"):
            self.check()

    def test_stale_reference_and_locator_fail(self):
        self.put("src/a.py", "value = 3\n")
        self.save(self.record())
        self.put("GUIDE.md", "# Editing replaced\n")
        with self.assertRaisesRegex(h.HandoffError, "Stale reference"):
            self.check()
        self.save(self.record())
        with self.assertRaisesRegex(h.HandoffError, "Missing reference symbol"):
            self.check()

    def test_baseline_rewrite_fails(self):
        self.baseline.write_bytes(self.baseline.read_bytes() + b" ")
        with self.assertRaisesRegex(h.HandoffError, "controller-held digest"):
            c.current_changes(self.root, self.baseline, self.seal)

    def test_controls_cannot_be_weakened_in_same_task(self):
        with patch.object(c, "controls", return_value={"tampered": "rule"}):
            with self.assertRaisesRegex(h.HandoffError, "independent review required"):
                c.current_changes(self.root, self.baseline, self.seal)

    def test_private_path_rejected_before_read(self):
        self.put("src/.env", "SYNTHETIC ONLY")
        with self.assertRaisesRegex(h.HandoffError, "Secret/private"):
            c.current_changes(self.root, self.baseline, self.seal)

    def test_hardlink_refused(self):
        os.link(self.root / "src/a.py", self.root / "src/hard.py")
        with self.assertRaisesRegex(h.HandoffError, "Hard-linked"):
            c.current_changes(self.root, self.baseline, self.seal)

    def test_reference_escape_refused(self):
        self.put("src/a.py", "value = 3\n")
        record = self.record()
        record["entries"][0]["references"][0]["path"] = "../outside.md"
        self.save(record)
        with self.assertRaises(h.HandoffError):
            self.check()

    def test_cli_is_read_only_and_rejects_invalid_report(self):
        self.put("src/a.py", "value = 3\n")
        self.save(self.record())
        before = {p: p.read_bytes() for p in self.work.rglob("*") if p.is_file()}
        cmd = [sys.executable, "-B", str(Path(c.__file__)), "check", "--root", str(self.root),
               "--baseline", str(self.baseline), "--baseline-sha256", self.seal, "--report", str(self.report)]
        run = subprocess.run(cmd, capture_output=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in self.work.rglob("*") if p.is_file()})
        self.report.write_text("no record", encoding="utf-8")
        run = subprocess.run(cmd, capture_output=True, timeout=20)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stderr)["result"], "rejected")

    def completion_fixture(self):
        self.put("00_SYSTEM/policy.md", "# Synthetic policy\n")
        self.put("task_packet.md", packet_text(writes=["src/**"]))
        bundle = self.work / "bundle"
        h.build(argparse.Namespace(vault_root=str(self.root), packet="task_packet.md", executor="codex",
                                  read=["00_SYSTEM/policy.md"], skill=[], output=str(bundle)))
        self.put("src/a.py", "value = 3\n")
        self.report = bundle / "artifacts/REPORT.md"
        self.save(self.record())
        raw = self.report.read_bytes()
        worker = h.worker_template(h.parse_packet((self.root / "task_packet.md").read_bytes())["frontmatter"], "codex")
        worker.update(execution_state="ready_for_review", summary="Fixture changed.",
                      artifacts=[{"path": "artifacts/REPORT.md", "sha256": h.digest(raw), "description": "Task report"}],
                      changed_paths=["src/a.py"], checks=[{"name": "Fixture", "command": "Equality check", "outcome": "passed", "evidence": "artifacts/REPORT.md"}],
                      risks=[], proposed_writeback=[], next_action="Independent H3 review.")
        result_path = bundle / "worker_result.json"
        result_path.write_bytes(h.json_bytes(worker))
        args = argparse.Namespace(bundle=str(bundle), result=str(result_path), rationale_root=str(self.root),
                                  rationale_baseline=str(self.baseline), rationale_baseline_sha256=self.seal,
                                  rationale_report=str(self.report))
        return args

    def test_runner_completion_and_freshness(self):
        args = self.completion_fixture()
        out = c.complete(args)
        self.assertEqual(out["result"], "candidate_completion_checked")
        self.assertEqual(out["verification_lifecycle"], "needs-review")
        self.assertIsNone(out["h3_verdict"])
        self.put("00_SYSTEM/policy.md", "# Changed policy\n")
        with self.assertRaisesRegex(h.HandoffError, "Live source drift"):
            c.complete(args)

    def test_runner_omitted_file_rejected_via_cli(self):
        args = self.completion_fixture()
        self.put("src/omitted.py", "value = 5\n")
        cmd = [sys.executable, "-B", str(Path(h.__file__)), "complete"]
        for key, value in vars(args).items():
            cmd.extend(["--" + key.replace("_", "-"), value])
        run = subprocess.run(cmd, capture_output=True, timeout=20)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stderr)["result"], "rejected")

    def test_runner_cannot_narrow_baseline_scope(self):
        args = self.completion_fixture()
        self.freeze(["src/a.py"])
        args.rationale_baseline_sha256 = self.seal
        with self.assertRaisesRegex(h.HandoffError, "all packet Allowed Writes"):
            c.complete(args)


if __name__ == "__main__":
    unittest.main()
