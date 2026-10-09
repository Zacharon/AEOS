"""A repeated CLI call must preserve an existing reviewed packet byte for byte."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BUILDER = Path(__file__).resolve().parents[1] / "build_task_packet.py"

class PacketPreservationTests(unittest.TestCase):
    def test_existing_output_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "Demo"
            project.mkdir()
            (project / "PROJECT_INDEX.md").write_text("# Demo\n", encoding="utf8")
            target = root / "packet.md"
            cmd = [sys.executable, "-B", str(BUILDER), "--project-path", str(project),
                   "--goal", "Inspect the demo", "--output", str(target)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            target.write_bytes(b"Reviewed evidence\r\nDo not replace.\r\n")
            before = target.read_bytes()
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertIn("output already exists", second.stderr)
            self.assertEqual(target.read_bytes(), before)

if __name__ == "__main__":
    unittest.main()
