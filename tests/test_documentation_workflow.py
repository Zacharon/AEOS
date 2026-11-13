"""Real frozen validators, synthetic temporary roots, no worker executor."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "prototypes/issue_handoff/documentation_workflow.py"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


d = module("documentation_workflow_test_adapter", CLI)
fixture = module("documentation_workflow_packet_fixture", d.TOOLS / "test_handoff.py")


class DocumentationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aeos-doc-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "source"
        self.root.mkdir()
        self.run = self.base / "run"
        self.write("policy.md", "---\nstatus: active\nscope: policy\n---\n# Active policy\nUse value 2.\n")
        self.write("old.md", "# Historical policy\nUse value 99.\n")
        self.write("contract.md", d.CONTRACT.read_text(encoding="utf-8"))
        self.write("dependency.txt", "Required dependency bytes.\n")
        self.write("src/code.py", "value = 1\n")
        self.write("docs/guide.md", "# Guide\nOriginal behavior.\n")
        self.meta = {"sources": [
            {"path": "policy.md", "scope": "policy", "authority": "Task constraints", "status": "active", "replacement": None, "references": ["dependency.txt"]},
            {"path": "contract.md", "scope": "worker-return", "authority": "Full return and rationale schema", "status": "active", "replacement": None, "references": []},
            {"path": "old.md", "scope": "policy", "authority": "Historical decisions", "status": "superseded", "replacement": "policy.md", "references": []}],
            "dependencies": ["dependency.txt"], "contracts": {"return": "contract.md", "rationale": "contract.md"},
            "documentation": [{"paths": ["src/**"], "documents": ["docs/guide.md"]}],
            "required_artifacts": ["artifacts/report.md", "artifacts/checks.txt"], "required_checks": ["unit"]}
        self.packet()

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8", newline="\n")

    def packet(self):
        text = fixture.packet_text(reads=["policy.md", "contract.md"], writes=["src/**", "docs/**"])
        text = text.replace("## 6. Allowed Reads\n- `policy.md`\n- `contract.md`", "## 6. Allowed Reads\n- `policy.md`\n- `contract.md`\n- `old.md`\n- `dependency.txt`\n- `docs/**`\n- `linked/**`")
        self.write("packet.md", text + "\n```context-selection\n" + json.dumps(self.meta) + "\n```\n")

    def cli(self, *args, expected=0):
        process = subprocess.run([sys.executable, "-B", str(CLI), *map(str, args)], capture_output=True, text=True, timeout=30)
        self.assertEqual(expected, process.returncode, process.stdout + process.stderr)
        return json.loads(process.stdout if expected == 0 else process.stderr)

    def prepare(self):
        return d.prepare(self.root, "packet.md", self.run)

    def returned(self, *, docs=True, waiver=False, value=2):
        self.prepare()
        self.write("src/code.py", f"value = {value}\n")
        if docs:
            self.write("docs/guide.md", f"# Guide\nValue now defaults to {value}.\n")
        bundle = self.run / "bundle"
        control = d.load(self.run / "controller/prepared.json")
        _, delta = d.rationale.current_changes(self.root, self.run / "controller/baseline.json", control["baseline_sha256"])
        changed = [item["path"] for item in delta]
        refs = [] if waiver else [{"path": "docs/guide.md", "sha256": d.h.digest((self.root / "docs/guide.md").read_bytes()), "contains": "# Guide"}]
        record = {"task_id": "TASK-2026-09-04-901", "baseline_sha256": control["baseline_sha256"], "changes_sha256": d.h.digest(d.h.json_bytes(delta)),
                  "entries": [{"paths": changed, "disposition": "documentation-not-needed" if waiver else "documented",
                  "why": "The src/code.py value change is an internal fixture detail with no public behavior." if waiver else "The guide records the changed default value.",
                  "where_to_edit": "Edit the value fixture and its guide together.", "constraints": "Synthetic local fixture only.",
                  "verification": "Captured the fixture check in checks.txt.", "references": refs}]}
        report = "# Task report\n\nDocumentation delta: the guide describes the new default value; this fixture checks structural coverage only and does not prove semantic quality.\n\n```code-rationale\n" + json.dumps(record) + "\n```\n"
        (bundle / "artifacts/report.md").write_text(report, encoding="utf-8", newline="\n")
        actual = (self.root / "src/code.py").read_text(encoding="utf-8")
        self.assertEqual(f"value = {value}\n", actual)
        (bundle / "artifacts/checks.txt").write_text(f"Synthetic captured assertion passed: code fixture equals value = {value}.\n", encoding="utf-8")
        result = d.load(bundle / "worker_result.template.json")
        result.update(execution_state="ready_for_review", summary="Updated the synthetic value and accounted for documentation.", changed_paths=changed,
                      risks=["H3 has not run."], next_action="Request independent review.",
                      checks=[{"name": "unit", "command": "synthetic value check", "outcome": "passed", "evidence": "artifacts/checks.txt"},
                              {"name": "visual", "command": "manual visual check", "outcome": "not_run", "evidence": None}])
        result["artifacts"] = [{"path": p, "sha256": d.h.digest((bundle / p).read_bytes()), "description": "Synthetic captured evidence"} for p in self.meta["required_artifacts"]]
        self.result(result)
        return result

    def result(self, value):
        (self.run / "bundle/worker_result.json").write_bytes(d.h.json_bytes(value))

    def tree(self):
        return {p.relative_to(self.base).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.base.rglob("*") if p.is_file()}

    def test_manual_return_cli_and_idempotent_receipt(self):
        self.returned()
        first = self.cli("verify", "--run", self.run)
        before = self.tree()
        receipt = d.load(Path(first["receipt"]))
        self.assertEqual("NOT_VERIFIED", receipt["semantic_quality"])
        self.assertIsNone(receipt["h3_verdict"])
        self.assertEqual("not_run", receipt["optional_not_run"][0]["outcome"])
        self.assertEqual(first, self.cli("verify", "--run", self.run))
        self.cli("check", "--run", self.run)
        self.cli("check", "--run", self.run)
        self.assertEqual(before, self.tree())

    def test_selection_and_explicit_history_are_read_only(self):
        before = self.tree()
        lint = self.cli("lint", "--root", self.root, "--packet", "packet.md")
        self.assertEqual(["policy.md", "contract.md"], lint["active"])
        history = self.cli("history", "--root", self.root, "--packet", "packet.md", "--path", "old.md")
        self.assertEqual("superseded", history["classification"])
        self.assertFalse(history["executable_packet"])
        self.assertIn("Use value 99", history["content"])
        self.assertEqual(before, self.tree())
        with self.assertRaises(ValueError):
            d.history(self.root, "packet.md", "policy.md")
        self.prepare()
        bundled = "\n".join(p.read_text(encoding="utf-8") for p in (self.run / "bundle/context").glob("*.md"))
        self.assertIn("Use value 2", bundled)
        self.assertNotIn("Use value 99", bundled)

    def test_invalid_context_rejected_before_creating_run(self):
        original = copy.deepcopy(self.meta)
        mutations = [lambda m: m["sources"][0].update(status="archived"),
                     lambda m: m["sources"][1].update(scope="policy"),
                     lambda m: m["sources"][2].update(replacement=None),
                     lambda m: m["sources"][2].update(replacement="contract.md"),
                     lambda m: m["sources"][0].update(references=["absent.md"]),
                     lambda m: m["dependencies"].append("../outside.txt"),
                     lambda m: m["dependencies"].append("src/code.py"),
                     lambda m: m.update(unexpected=True),
                     lambda m: m["contracts"].update(rationale="old.md"),
                     lambda m: m.update(required_checks=["unit", "UNIT"])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.meta = copy.deepcopy(original)
                mutate(self.meta)
                self.packet()
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.run.exists())

    def test_contradictory_active_frontmatter_and_missing_source(self):
        for front in ("status: archived", "status: superseded", "status: rejected", "scope: other"):
            self.write("policy.md", "---\n" + front + "\n---\n# Policy\n")
            with self.subTest(front=front), self.assertRaises(ValueError):
                self.prepare()
        (self.root / "policy.md").unlink()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_incomplete_contract_and_duplicate_json_rejected(self):
        self.write("contract.md", "# Worker input and return contract\n## Rationale coverage\n")
        with self.assertRaisesRegex(ValueError, "contract"):
            self.prepare()
        self.write("contract.md", d.CONTRACT.read_text(encoding="utf-8"))
        path = self.root / "packet.md"
        path.write_text(path.read_text().replace('"sources":', '"dependencies": [], "sources":'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.prepare()

    def test_dependency_drift_and_fresh_run_reconciliation(self):
        self.prepare()
        before = self.tree()
        d.check(self.run)
        self.assertEqual(before, self.tree())
        self.write("dependency.txt", "Updated approved dependency.\n")
        with self.assertRaisesRegex(ValueError, "dependency"):
            d.check(self.run)
        self.assertFalse((self.run / "controller/verification.json").exists())
        d.prepare(self.root, "packet.md", self.base / "reconciled")
        d.check(self.base / "reconciled")

    def test_packet_read_authority_applies_to_history_and_required_refs(self):
        packet = self.root / "packet.md"
        text = packet.read_text(encoding="utf-8")
        packet.write_text(text.replace("- `old.md`\n", ""), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Allowed Reads"):
            d.history(self.root, "packet.md", "old.md")
        self.meta["sources"][2]["references"] = ["src/code.py"]
        self.packet()
        with self.assertRaisesRegex(ValueError, "Allowed Reads"):
            self.prepare()

    def test_changed_active_requirement_requires_fresh_complete_return(self):
        self.returned()
        original_receipt = Path(d.verify(self.run)["receipt"])
        saved = original_receipt.read_bytes()
        self.write("policy.md", "---\nstatus: active\nscope: policy\n---\n# Active policy\nUse value 3.\n")
        with self.assertRaisesRegex(ValueError, "Live source drift"):
            d.check(self.run)
        with self.assertRaisesRegex(ValueError, "Live source drift"):
            d.verify(self.run)
        self.assertEqual(saved, original_receipt.read_bytes())
        self.run = self.base / "reconciled"
        self.returned(value=3)
        self.assertEqual("value = 3\n", (self.root / "src/code.py").read_text())
        self.assertEqual("structurally_verified_candidate", d.verify(self.run)["result"])
        self.assertEqual(saved, original_receipt.read_bytes())

    def test_git_identity_is_pinned_without_git_writes(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        def git(*args):
            proc = subprocess.run(["git", "-C", str(self.root), *args], env=env, capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stderr)
        git("init", "--initial-branch=fixture")
        git("-c", "user.name=Synthetic Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull, "commit", "--allow-empty", "-m", "Synthetic baseline")
        self.prepare()
        before = self.tree()
        d.check(self.run)
        self.assertEqual(before, self.tree())
        git("symbolic-ref", "HEAD", "refs/heads/changed")
        with self.assertRaises(ValueError):
            d.check(self.run)

    def test_reconciled_delta_cannot_refresh_existing_receipt(self):
        self.returned(docs=False, waiver=True)
        d.verify(self.run)
        self.write("src/code.py", "value = 3\n")
        report = self.run / "bundle/artifacts/report.md"
        record = d.rationale.report_record(report)
        control = d.load(self.run / "controller/prepared.json")
        _, delta = d.rationale.current_changes(self.root, self.run / "controller/baseline.json", control["baseline_sha256"])
        record["changes_sha256"] = d.h.digest(d.h.json_bytes(delta))
        report.write_text("Documentation delta: this internal fixture adjustment has no public behavior change; all claims remain subject to independent review.\n```code-rationale\n" + json.dumps(record) + "\n```\n", encoding="utf-8")
        result = d.load(self.run / "bundle/worker_result.json")
        result["artifacts"][0]["sha256"] = d.h.digest(report.read_bytes())
        self.result(result)
        before = (self.run / "controller/verification.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "stale"):
            d.verify(self.run)
        self.assertEqual(before, (self.run / "controller/verification.json").read_bytes())

    def test_unchanged_document_and_rationale_reference_drift(self):
        self.returned(docs=False, waiver=True)
        d.verify(self.run)
        self.write("docs/guide.md", "# Guide\nChanged after receipt.\n")
        with self.assertRaises(ValueError):
            d.check(self.run)

    def test_required_checks_artifacts_and_result_schema(self):
        result = self.returned()
        for status in ("blocked", "failed", "not_run"):
            bad = copy.deepcopy(result)
            bad["checks"][0]["outcome"] = status
            self.result(bad)
            with self.subTest(status=status), self.assertRaises(ValueError):
                d.verify(self.run)
        bad = copy.deepcopy(result)
        bad["artifacts"] = bad["artifacts"][1:]
        self.result(bad)
        with self.assertRaises(ValueError):
            d.verify(self.run)
        bad = dict(result, h3_verdict="VERIFIED")
        self.result(bad)
        with self.assertRaises(ValueError):
            d.verify(self.run)
        self.assertFalse((self.run / "controller/verification.json").exists())

    def test_missing_rationale_and_stale_reference_rejected(self):
        result = self.returned()
        self.write("docs/guide.md", "# Guide\nDifferent current content.\n")
        report = self.run / "bundle/artifacts/report.md"
        record = d.rationale.report_record(report)
        control = d.load(self.run / "controller/prepared.json")
        _, delta = d.rationale.current_changes(self.root, self.run / "controller/baseline.json", control["baseline_sha256"])
        record["changes_sha256"] = d.h.digest(d.h.json_bytes(delta))
        report.write_text("Documentation delta: the guide describes the new value and preserves the fixture meaning for later independent review.\n```code-rationale\n" + json.dumps(record) + "\n```\n", encoding="utf-8")
        result["artifacts"][0]["sha256"] = d.h.digest(report.read_bytes())
        self.result(result)
        with self.assertRaisesRegex(ValueError, "Stale reference"):
            d.verify(self.run)
        report.write_text("Documentation was updated with the changed default value and all structural checks were captured.\n", encoding="utf-8")
        result["artifacts"][0]["sha256"] = d.h.digest(report.read_bytes())
        self.result(result)
        with self.assertRaisesRegex(ValueError, "code-rationale"):
            d.verify(self.run)

    def test_documentation_impact_requires_change_or_specific_waiver(self):
        self.returned(docs=False)
        with self.assertRaisesRegex(ValueError, "Impacted scope"):
            d.verify(self.run)

    def test_specific_no_documentation_reason_is_accepted(self):
        self.returned(docs=False, waiver=True)
        receipt = d.load(Path(d.verify(self.run)["receipt"]))
        self.assertEqual("documentation-not-needed", receipt["documentation_impacts"][0]["disposition"])

    def test_receipt_stales_on_change_result_or_artifact(self):
        result = self.returned()
        d.verify(self.run)
        changed = dict(result, summary="Changed worker assertion after verification.")
        self.result(changed)
        with self.assertRaisesRegex(ValueError, "stale"):
            d.check(self.run)
        with self.assertRaisesRegex(ValueError, "stale"):
            d.verify(self.run)
        evidence = self.run / "bundle/artifacts/checks.txt"
        evidence.write_text("Different captured check assertion.\n", encoding="utf-8")
        result["artifacts"][1]["sha256"] = d.h.digest(evidence.read_bytes())
        self.result(result)
        with self.assertRaisesRegex(ValueError, "stale"):
            d.check(self.run)

    def test_empty_documentation_waiver_and_heading_only_report_rejected(self):
        result = self.returned(docs=False, waiver=True)
        report = self.run / "bundle/artifacts/report.md"
        record = d.rationale.report_record(report)
        record["entries"][0]["why"] = "No documentation needed."
        def returned_report(prose):
            report.write_text(prose + "\n```code-rationale\n" + json.dumps(record) + "\n```\n", encoding="utf-8")
            result["artifacts"][0]["sha256"] = d.h.digest(report.read_bytes())
            self.result(result)
        returned_report("Documentation delta: the internal fixture change does not affect public behavior and requires independent review of this explanation.")
        with self.assertRaisesRegex(ValueError, "Impacted scope"):
            d.verify(self.run)
        record["entries"][0]["why"] = "The src/code.py fixture change leaves public behavior unchanged."
        returned_report("# Documentation delta")
        with self.assertRaisesRegex(ValueError, "prose"):
            d.verify(self.run)

    def test_output_collision_and_traversal(self):
        self.run.mkdir()
        for output in (self.run, self.root / "nested", self.base / "missing" / "run", self.base / "other" / ".." / "new"):
            with self.subTest(output=output), self.assertRaises(ValueError):
                d.prepare(self.root, "packet.md", output)

    def test_hardlinks_are_rejected(self):
        source = self.root / "dependency.txt"
        os.link(source, self.base / "alias.txt")
        with self.assertRaisesRegex(ValueError, "hardlink"):
            self.prepare()

    def test_hardlinked_return_artifact_is_rejected(self):
        self.returned()
        os.link(self.run / "bundle/artifacts/checks.txt", self.base / "evidence-alias.txt")
        with self.assertRaisesRegex(ValueError, "hardlinked artifact"):
            d.verify(self.run)

    def test_symlink_is_rejected(self):
        source = self.root / "dependency.txt"
        source.unlink()
        external = self.base / "external.txt"
        external.write_text("Outside content", encoding="utf-8")
        try:
            source.symlink_to(external)
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.prepare()

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_native_junction_is_rejected(self):
        external = self.base / "external"
        external.mkdir()
        (external / "ref.txt").write_text("Outside content", encoding="utf-8")
        junction = self.root / "linked"
        command = "New-Item -ItemType Junction -Path $env:AEOS_TEST_LINK -Target $env:AEOS_TEST_TARGET | Out-Null"
        env = dict(os.environ, AEOS_TEST_LINK=str(junction), AEOS_TEST_TARGET=str(external))
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", command], env=env, capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.meta["dependencies"] = ["linked/ref.txt"]
        self.packet()
        try:
            with self.assertRaisesRegex(ValueError, "junction"):
                self.prepare()
        finally:
            # Remove only the junction itself; never recurse into its target.
            os.rmdir(junction)


if __name__ == "__main__":
    unittest.main()
