"""The primary setup route follows the current immutable release."""
import html
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SetupInstructionsTests(unittest.TestCase):
    def test_primary_readme_guide_matches_current_website_and_archive(self):
        readme = (ROOT / "README.md").read_text(encoding="utf8")
        primary = readme.split("## Try it\n", 1)[1].split("\n## ", 1)[0]
        guide_link = re.search(r"Follow[^\n]*?\[[^\]]+\]\(([^)]+)\)", primary)
        self.assertIsNotNone(guide_link, "Primary setup must link to current instructions")
        guide = (ROOT / guide_link.group(1)).resolve()
        self.assertTrue(guide.is_relative_to(ROOT))
        text = guide.read_text(encoding="utf8")
        commands = re.search(r"```powershell\s*\n(.*?)\n```", text, re.S).group(1)
        site = (ROOT / "site/first-run.html").read_text(encoding="utf8")
        site_commands = html.unescape(re.search(r"<pre><code>(.*?)</code></pre>", site, re.S).group(1))
        self.assertEqual(commands.replace("\r\n", "\n"), site_commands.replace("\r\n", "\n"))
        self.assertIn("sys.version_info >= (3,11)", commands)
        self.assertNotIn("--output ../aeos-first-run", commands)
        archive = "agentic-engineering-os-2026.10.17-public.4.zip"
        self.assertIn(archive, primary)
        self.assertIn(archive, site)
        self.assertTrue((ROOT / "site/downloads" / archive).is_file())


if __name__ == "__main__":
    unittest.main()
