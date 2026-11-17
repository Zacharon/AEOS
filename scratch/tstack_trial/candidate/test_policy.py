import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compare import ROOT, compare, expand, replay
from policy import assess, signature


def trace(failures=("A", "A"), remaining=(3, 3), **extras):
    return expand(dict(failures=failures, remaining=remaining, **extras))


class PolicyTests(unittest.TestCase):
    def test_repeat_stops_early_with_resume_condition(self):
        result = assess(trace())
        self.assertEqual((result["execution_state"], result["reason"]), ("blocked", "stalled"))
        self.assertTrue(result["resume_conditions"])
        self.assertNotIn("impossible", json.dumps(result))

    def test_cycle_detected_at_cap(self):
        self.assertEqual(assess(trace(("A", "B", "A"), (3, 3, 3)))["reason"], "stalled")

    def test_semantic_set_identity_and_diagnostic_noise(self):
        a = trace()["rounds"][0]["failures"][0]
        b = dict(a, actual="B")
        noisy = dict(a, diagnostic="new temporary path", observed_at="other time", subject="  sample  ")
        self.assertEqual(signature([a, b, a]), signature([b, noisy]))
        self.assertNotEqual(signature([a]), signature([b]))
        self.assertNotEqual(signature([a]), signature([dict(a, actual="a")]))

    def test_progress_under_same_error_continues(self):
        self.assertEqual(assess(trace(remaining=(3, 2)))["execution_state"], "in_progress")

    def test_regression_is_not_convergence(self):
        self.assertEqual(assess(trace(remaining=(3, 4)))["execution_state"], "in_progress")

    def test_progress_inside_cycle_not_stalled(self):
        self.assertEqual(assess(trace(("A", "B", "A"), (3, 2, 3)))["reason"], "round_cap")

    def test_unknown_progress_does_not_establish_stall(self):
        self.assertEqual(assess(trace(remaining=(None, None)))["execution_state"], "in_progress")

    def test_justified_retry_keeps_budget(self):
        self.assertEqual(assess(trace(actions_at=[2]))["execution_state"], "in_progress")
        self.assertEqual(assess(trace(("A", "A", "A"), (3, 3, 3), actions_at=[2, 3]))["reason"], "round_cap")

    def test_novelty_cannot_escape_cap(self):
        self.assertEqual(assess(trace(("A", "B", "C"), (3, 3, 3)))["reason"], "round_cap")
        with self.assertRaises(ValueError):
            assess(trace(("A", "B", "C", "D"), (3, 3, 3, 3)))

    def test_cost_and_time_limits_precede_stall_and_success(self):
        for kw in ({"cost_limit": 2}, {"time_limit": 20}):
            self.assertEqual(assess(trace(**kw))["reason"], "budget_exhausted")
            self.assertEqual(assess(trace(("A", "PASS"), (3, 0), **kw))["reason"], "budget_exhausted")

    def test_blocker_and_success(self):
        self.assertEqual(assess(trace(("A",), (3,), blocker_at=1))["reason"], "missing_authority")
        self.assertEqual(assess(trace(("PASS",), (0,)))["execution_state"], "ready_for_review")

    def test_empty_failure_set_cannot_forge_success(self):
        t = trace(("A",), (3,))
        t["rounds"][0]["failures"] = []
        with self.assertRaises(ValueError):
            assess(t)
        t["rounds"][0]["checks"]["acceptance"] = {"status": "not_run", "evidence": []}
        self.assertEqual(assess(t)["execution_state"], "in_progress")

    def test_missing_check_or_evidence_rejected(self):
        for change in (lambda r: r.update(checks={}), lambda r: r["checks"]["acceptance"].update(evidence=[]), lambda r: r["progress"].update(evidence=[])):
            t = trace(("A",), (3,))
            change(t["rounds"][0])
            with self.assertRaises(ValueError):
                assess(t)

    def test_bad_usage_and_scope_rejected(self):
        for value in (-1, float("nan"), float("inf"), True):
            t = trace()
            t["rounds"][-1]["usage"]["cost_units"] = value
            with self.assertRaises(ValueError):
                assess(t)
        t = trace()
        t["rounds"][-1]["scope_revision"] = "changed"
        with self.assertRaises(ValueError):
            assess(t)

    def test_terminal_history_cannot_reset(self):
        with self.assertRaises(ValueError):
            assess(trace(("A", "A", "PASS"), (3, 3, 0)))

    def test_missing_progress_value_is_invalid_not_unknown(self):
        t = trace(("A",), (3,))
        del t["rounds"][0]["progress"]["remaining"]
        with self.assertRaises(ValueError):
            assess(t)

    def test_supplied_trace_unmodified_and_cli_parity_after_restart(self):
        t = trace()
        original = copy.deepcopy(t)
        direct = assess(t)
        self.assertEqual(t, original)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "trace.json"
            source.write_text(json.dumps(t), encoding="utf-8")
            command = [sys.executable, "-B", str(ROOT / "policy.py"), str(source)]
            first = subprocess.run(command + ["--format", "json"], capture_output=True, text=True)
            second = subprocess.run(command + ["--format", "json"], capture_output=True, text=True)
            human = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(json.loads(first.stdout), direct)
            self.assertIn("blocked: stalled", human.stdout)
            source.write_text("{}", encoding="utf-8")
            bad = subprocess.run(command + ["--format", "json"], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("error", json.loads(bad.stderr))

    def test_frozen_counterfactual_exposes_false_abandonment(self):
        fixtures = json.loads((ROOT / "fixtures/cases.json").read_text(encoding="utf-8"))
        result = compare(fixtures)
        self.assertEqual(result["promotion"], "REJECT")
        self.assertEqual(result["splits"]["development"]["premature_abandonments_added"], 0)
        self.assertEqual(result["splits"]["held_out"]["premature_abandonments_added"], 1)
        self.assertTrue(all(s["unsolved_rounds_saved"] > 0 for s in result["splits"].values()))


if __name__ == "__main__":
    unittest.main()
