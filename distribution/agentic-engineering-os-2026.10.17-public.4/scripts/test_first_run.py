"""Continuation and output path regressions; disposable synthetic fixtures only."""
from pathlib import Path
import tempfile
import unittest
from demo import continuation_command, powershell_quote
from check_package import safe_path

class FirstRunTests(unittest.TestCase):
    def test_literal_parent_traversal_remains_refused(self):
        with self.assertRaisesRegex(ValueError, "Parent traversal"):
            safe_path(Path("../aeos first run"))

    def test_absolute_output_with_spaces_is_supported(self):
        with tempfile.TemporaryDirectory(prefix="aeos space ") as t:
            path = Path(t) / "fresh output"
            self.assertEqual(safe_path(path), path.resolve())
            self.assertFalse(path.exists())

    def test_powershell_quotes_apostrophes(self):
        self.assertEqual(powershell_quote("user's env"), "'user''s env'")

    def test_continuation_uses_explicit_absolute_environment_and_paths(self):
        with tempfile.TemporaryDirectory(prefix="aeos ' space ") as t:
            output, interpreter = Path(t)/"saved output", Path(t)/"env"/"python.exe"
            command = continuation_command(output, interpreter)
            self.assertTrue(command.startswith("& " + powershell_quote(interpreter) + " -B "))
            self.assertIn(powershell_quote(output / "handoff"), command)
            self.assertIn(powershell_quote(output / "vault"), command)
            self.assertNotIn("..", command)

    def test_continuation_preserves_alias_guard(self):
        with self.assertRaisesRegex(ValueError, "Parent traversal"):
            continuation_command(Path("../output"), Path("python.exe"))

if __name__ == "__main__":
    unittest.main()
