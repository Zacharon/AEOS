"""Exercise the link/privacy validator, including its bounded Floorplan exception."""
import base64
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_candidate as validator


class InlineImageTests(unittest.TestCase):
    def setUp(self):
        parser = validator.Links()
        parser.feed((validator.ROOT / "site/floorplan.html").read_text(encoding="utf8"))
        self.images = [row for row in parser.links if row[0].startswith("data:")]

    def scan(self, body, filename="site/floorplan.html"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("README.md", "docs/ARCHITECTURE.md", "docs/ADOPTING-AEOS.md",
                         "docs/PACKAGE-CANDIDATE.md", "docs/RELEASE-READINESS-public.4.md",
                         "site/verification-public.3.json", "site/verification-public.4.json"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("", encoding="utf8")
            target = root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf8")
            with patch.object(validator, "ROOT", root):
                return validator.validate_links_and_privacy()

    def test_actual_floorplan_images_and_full_scan_pass(self):
        self.assertEqual(len(self.images), 2)
        for value, tag, attribute, attrs in self.images:
            self.assertTrue(validator.is_safe_floorplan_image(
                value, validator.ROOT / "site/floorplan.html", tag, attribute, attrs))
        self.assertGreater(validator.validate_links_and_privacy()["local_links_checked"], 0)

    def test_invalid_or_unreviewed_payloads_refused_in_every_context(self):
        def encoded(value):
            return base64.b64encode(value).decode("ascii")
        values = ["data:image/png;base64," + payload for payload in (
            "", "A", "====", "@@@@", encoded(b"alert(1)"),
            encoded(b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'),
            encoded(b"<html><script>alert(1)</script></html>"),
            encoded(b"\x89PNG\r\n\x1a\n<script>alert(1)</script>"))]
        values += ["data:image/svg+xml;base64,PHN2Zy8+", "data:text/html;base64,PHAvPg==",
                   "data:image/png,<script>"]
        templates = ('<img src="{}">', '<link rel="icon" type="image/png" href="{}">',
                     '<script src="{}"></script>', '<iframe src="{}"></iframe>',
                     '<link rel="stylesheet" href="{}">', '<a href="{}">test</a>', '[test]({})')
        for value in values:
            for template in templates:
                filename = "README.md" if template.startswith("[") else "site/floorplan.html"
                with self.subTest(value=value, context=template):
                    with self.assertRaises(ValueError):
                        self.scan(template.format(value), filename)

    def test_reviewed_png_refused_in_other_contexts_and_files(self):
        for value, _, _, _ in self.images:
            for template in ('<script src="{}"></script>', '<iframe src="{}"></iframe>',
                             '<link rel="stylesheet" href="{}">', '<a href="{}">test</a>',
                             '<link rel="icon" href="{}">',
                             '<img src="{}" src="https://example.com/">'):
                with self.subTest(context=template):
                    with self.assertRaises(ValueError):
                        self.scan(template.format(value))
            with self.assertRaises(ValueError):
                self.scan('<img src="' + value + '">', "site/other.html")
            with self.assertRaises(ValueError):
                self.scan('[test](' + value + ')', "README.md")

    def test_complete_url_and_canonical_base64_required(self):
        for value, tag, attribute, attrs in self.images:
            source = validator.ROOT / "site/floorplan.html"
            mutations = [value + suffix for suffix in ("?ignored=<script>", "#ignored=<script>", "=", " ")]
            mutations += [value.replace("base64,", "base64,\n"),
                          value.replace("base64,", "base64,\t"),
                          value.replace("image/png", "image/jpeg"),
                          value.replace("image/png", "image/gif"),
                          value.replace("image/png", "image/webp"),
                          value[:-4] + "AAAA", value.replace("data:", "data://")]
            for mutated in mutations:
                with self.subTest(mutation=mutated[:40]):
                    self.assertFalse(validator.is_safe_floorplan_image(mutated, source, tag, attribute, attrs))
            self.assertFalse(validator.is_safe_floorplan_image(value + "A" * 8192, source, tag, attribute, attrs))


if __name__ == "__main__":
    unittest.main()
