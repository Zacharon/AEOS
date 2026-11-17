"""Risk-focused tests of transitions, honest evidence, and read containment."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from checker import assess, load_json, RecordError, safe_path, sha
from run_fixtures import evaluate, FIXTURES, load_cases, ROOT


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.current = load_json(FIXTURES / "current.json")
        self.receipt = load_json(FIXTURES / "receipt.json")

    def decide(self):
        return assess(self.current, self.receipt, FIXTURES)

    def test_twelve_authored_expectations_and_reasons(self):
        summary = evaluate()
        self.assertEqual(summary["failed"], 0, summary)
        self.assertEqual(summary["passed"], 12)

    def test_deterministic_read_only_replay(self):
        before = {p.relative_to(FIXTURES): p.read_bytes() for p in FIXTURES.rglob("*") if p.is_file()}
        for case_id, current, receipt in load_cases():
            with self.subTest(case=case_id):
                inputs = copy.deepcopy((current, receipt))
                first = assess(current, receipt, FIXTURES)
                self.assertEqual(first, assess(current, receipt, FIXTURES))
                self.assertEqual(inputs, (current, receipt))
        after = {p.relative_to(FIXTURES): p.read_bytes() for p in FIXTURES.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_relevant_change_invalidates_and_restore_recovers(self):
        original = copy.deepcopy(self.current)
        self.assertEqual(self.decide()["outcome"], "eligible")
        for field, changed in (
            ("requirement_revision", "intent-next"),
            ("source_revision", "snapshot-next"),
            ("specification", "inputs/specification-v2.txt"),
            ("dependencies", {"source": "inputs/source-v2.txt"}),
            ("environment", {"runtime": "synthetic-next", "configuration": "config-1"}),
            ("claim_id", "CLAIM-other"),
        ):
            with self.subTest(field=field):
                self.current[field] = changed
                self.assertEqual(self.decide()["outcome"], "stale")
                self.current = copy.deepcopy(original)
                self.assertEqual(self.decide()["outcome"], "eligible")

    def test_authority_is_current_separate_and_not_owner_acceptance(self):
        self.receipt["owner_acceptance"] = "accepted"
        self.current["authority"] = "denied"
        result = self.decide()
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["evidence_outcome"], "eligible")
        self.assertFalse(result["owner_acceptance_inferred"])
        self.receipt["raw_output"] = "raw/altered.txt"
        result = self.decide()
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["evidence_outcome"], "invalid")
        self.current["authority"] = "unknown"
        self.receipt = load_json(FIXTURES / "receipt.json")
        self.assertEqual(self.decide()["outcome"], "insufficient")

    def test_unknown_coverage_and_incomplete_dependency_inventory(self):
        for record in (self.current, self.receipt):
            record["dependency_coverage"] = "unknown"
            self.assertEqual(self.decide()["outcome"], "insufficient")
            record["dependency_coverage"] = "complete"
        self.receipt["dependency_sha256"] = {}
        self.assertEqual(self.decide()["outcome"], "insufficient")

    def test_malformed_missing_and_ambiguous_records_fail_closed(self):
        for field, bad in (("exit_code", False), ("raw_sha256", "bad"),
                           ("requirement_ids", ["REQ-1", "REQ-1"]),
                           ("environment", "unknown")):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt[field] = bad
                self.assertEqual(assess(self.current, receipt, FIXTURES)["outcome"], "invalid")
        missing = copy.deepcopy(self.receipt)
        del missing["source_revision"]
        self.assertEqual(assess(self.current, missing, FIXTURES)["outcome"], "insufficient")
        self.current["policy"] = "reuse-whatever-passes"
        self.assertEqual(self.decide()["outcome"], "invalid")

    def test_failed_unrun_missing_or_tampered_output_never_passes(self):
        changes = (
            {"execution_status": "not_run", "exit_code": None},
            {"execution_status": "interrupted", "exit_code": None},
            {"exit_code": 1}, {"raw_output": None}, {"raw_sha256": None},
            {"raw_output": "raw/absent.txt"}, {"raw_output": "raw/altered.txt"},
            {"unrun_checks": ["CHECK-other"]}, {"assumptions": ["Unresolved requirement"]},
        )
        for change in changes:
            with self.subTest(change=change):
                receipt = dict(self.receipt, **change)
                self.assertNotEqual(assess(self.current, receipt, FIXTURES)["outcome"], "eligible")

    def test_path_escape_aliases_and_streams_refused_for_every_file_role(self):
        references = ("../outside.txt", "/outside.txt", "X:/outside.txt", "//server/share",
                      "raw/../recorded.txt", "raw\\recorded.txt", "raw/recorded.txt:stream",
                      "raw//recorded.txt", "raw/./recorded.txt", "raw/NUL.txt", "raw/recorded.txt.")
        for reference in references:
            for role in ("specification", "dependency", "raw"):
                with self.subTest(reference=reference, role=role):
                    current, receipt = copy.deepcopy(self.current), copy.deepcopy(self.receipt)
                    if role == "specification":
                        current["specification"] = reference
                    elif role == "dependency":
                        current["dependencies"]["source"] = reference
                    else:
                        receipt["raw_output"] = reference
                    self.assertEqual(assess(current, receipt, FIXTURES)["outcome"], "invalid")

    def test_real_filesystem_link_cannot_escape_fixture_root(self):
        # Both target and test root remain inside this experiment. On Windows a
        # junction tests real redirection without requiring symlink privileges.
        with tempfile.TemporaryDirectory(prefix="containment-", dir=ROOT) as tmp:
            base = Path(tmp)
            isolated, sibling = base / "fixture", base / "sibling"
            isolated.mkdir()
            sibling.mkdir()
            (sibling / "evidence.txt").write_text("synthetic", encoding="utf-8")
            link = isolated / "alias"
            if os.name == "nt":
                result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(sibling)],
                                        capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, "Could not create local test junction")
            else:
                link.symlink_to(sibling, target_is_directory=True)
            with self.assertRaises(RecordError) as caught:
                safe_path(isolated, "alias/evidence.txt")
            self.assertEqual(caught.exception.code, "linked_file_reference")
            with self.assertRaises(RecordError):
                safe_path(link, "evidence.txt")

    def test_consistent_forgery_demonstrates_authenticity_limit(self):
        # Matching bytes and digest cannot detect a producer lying about execution.
        self.receipt["raw_output"] = "raw/altered.txt"
        self.receipt["raw_sha256"] = sha((FIXTURES / "raw/altered.txt").read_bytes())
        result = self.decide()
        self.assertEqual(result["outcome"], "eligible")
        self.assertFalse(result["execution_authenticity_verified"])

    def test_human_and_agent_cli_use_same_decision_and_exit_status(self):
        args = [sys.executable, "-B", "checker.py", "--root", "fixtures", "--current", "current.json", "--receipt", "receipt.json"]
        human = subprocess.run(args + ["--format", "text"], cwd=ROOT, capture_output=True, text=True)
        agent = subprocess.run(args + ["--format", "json"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(human.returncode, 0, human.stderr)
        self.assertEqual(agent.returncode, 0, agent.stderr)
        self.assertIn("Outcome: eligible", human.stdout)
        self.assertEqual(json.loads(agent.stdout), self.decide())
        refused = subprocess.run(args[:-1] + ["../outside.json", "--format", "json"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(json.loads(refused.stdout)["outcome"], "invalid")

    def test_duplicate_json_and_command_injection_are_not_executed(self):
        with tempfile.TemporaryDirectory(prefix="json-", dir=ROOT) as tmp:
            record = Path(tmp) / "duplicate.json"
            record.write_text('{"authority":"denied","authority":"allowed"}', encoding="utf-8")
            with self.assertRaises(RecordError):
                load_json(record)
        # A command string is data. The assessor must never dispatch it.
        from unittest.mock import patch
        self.current["command"] = self.receipt["command"] = "never-execute-this"
        with patch("subprocess.run", side_effect=AssertionError("Unexpected dispatch")):
            self.assertEqual(self.decide()["outcome"], "eligible")


if __name__ == "__main__":
    unittest.main()
