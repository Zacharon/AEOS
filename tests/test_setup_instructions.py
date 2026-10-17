"""Follow the primary setup route, rather than only the later candidate block."""
import html
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SetupInstructionsTests(unittest.TestCase):
    def test_primary_readme_guide_reaches_candidate_verified_commands(self):
        readme = (ROOT / "README.md").read_text(encoding="utf8")
        primary = readme.split("## Try it\n", 1)[1].split("\n## ", 1)[0]
        guide_link = re.search(r"Follow[^\n]*?\[[^\]]+\]\(([^)]+)\)", primary)
        self.assertIsNotNone(guide_link, "Primary setup must link to corrected instructions")
        guide = (ROOT / guide_link.group(1)).resolve()
        self.assertTrue(guide.is_relative_to(ROOT))
        text = guide.read_text(encoding="utf8")
        commands = html.unescape(re.search(r"<pre><code>(.*?)</code></pre>", text, re.S).group(1))
        candidate = ROOT / "distribution/agentic-engineering-os-2026.10.12-public.4-candidate.1/FIRST_RUN.md"
        candidate_commands = re.search(r"```powershell\s*\n(.*?)\n```", candidate.read_text(encoding="utf8"), re.S).group(1)
        self.assertEqual(commands.replace("\r\n", "\n"), candidate_commands.replace("\r\n", "\n"))
        self.assertNotIn("--output ../aeos-first-run", commands)


if __name__ == "__main__":
    unittest.main()
