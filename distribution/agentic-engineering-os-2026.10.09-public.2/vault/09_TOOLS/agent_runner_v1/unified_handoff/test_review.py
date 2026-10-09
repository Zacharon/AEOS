"""Fresh-session reads must not turn absent or stale evidence into completion."""
import argparse
import json
import unittest
import test_handoff as fixtures
import handoff as h

class ReviewTests(unittest.TestCase):
    setUp = fixtures.AdapterTests.setUp
    put = fixtures.AdapterTests.put
    build = fixtures.AdapterTests.build
    result = fixtures.AdapterTests.result
    validate = fixtures.AdapterTests.validate

    def args(self):
        return argparse.Namespace(bundle=str(self.bundle), vault_root=str(self.vault), result=None)

    def test_missing_result_is_unknown_and_does_not_write(self):
        self.build()
        before = {str(p): p.read_bytes() for p in self.work.rglob("*") if p.is_file()}
        result = h.review(self.args())
        self.assertEqual(result["execution_state"], "unknown")
        self.assertEqual(result["result_state"], "missing")
        self.assertIsNone(result["h3_verdict"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.work.rglob("*") if p.is_file()})

    def test_source_drift_refuses_before_next_action(self):
        self.build()
        self.put("00_SYSTEM/policy.md", "# Changed source\n")
        with self.assertRaisesRegex(h.HandoffError, "Live source drift"):
            h.review(self.args())

    def test_missing_source_refuses(self):
        self.build()
        (self.vault / "00_SYSTEM/policy.md").unlink()
        with self.assertRaises((h.HandoffError, OSError)):
            h.review(self.args())

    def test_unfinished_template_refuses(self):
        self.build()
        (self.bundle / "worker_result.json").write_bytes((self.bundle / "worker_result.template.json").read_bytes())
        with self.assertRaises(h.HandoffError):
            h.review(self.args())

    def test_valid_result_does_not_become_independent_review(self):
        self.build()
        self.validate(self.result())
        result = h.review(self.args())
        self.assertEqual(result["execution_state"], "ready_for_review")
        self.assertEqual(result["result_state"], "candidate_valid")
        self.assertIsNone(result["h3_verdict"])
        self.assertIn("independent", result["next_action"])
        (self.bundle / "artifacts/check.txt").write_text("changed", encoding="utf8")
        with self.assertRaisesRegex(h.HandoffError, "Artifact hash mismatch"):
            h.review(self.args())

if __name__ == "__main__":
    unittest.main()
