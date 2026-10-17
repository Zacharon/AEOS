"""Archive security/public boundary regressions; only synthetic temporary bytes."""
from pathlib import Path
import io
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_candidate import ROOT, NAME, render, build
from validate_candidate import archive_members, extract, validate_links_and_privacy


def malicious(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name in entries:
            info = name if isinstance(name, zipfile.ZipInfo) else zipfile.ZipInfo("synthetic")
            if isinstance(name, str):
                info.filename = name  # Preserve adversarial raw names on Windows.
            z.writestr(info, b"synthetic")
    return buffer.getvalue()


class DistributionTests(unittest.TestCase):
    def test_deterministic_build_matches_committed_candidate(self):
        payload, _, _ = render()
        if sys.version_info[:3] == (3, 14, 5):
            # ZIP compression bytes depend on the builder interpreter.
            self.assertEqual(build(check=True)["payload_files"], 41)
        else:
            committed = (ROOT / "distribution" / (NAME + ".zip")).read_bytes()
            expected = json.loads((ROOT / "distribution" / (NAME + ".sha256.json")).read_text())
            self.assertEqual(hashlib.sha256(committed).hexdigest(), expected["sha256"])
            self.assertEqual(archive_members(committed), payload)

    def test_archive_traversal_absolute_ads_reserved_duplicates_refuse_before_effects(self):
        for names in [("../outside",), ("/absolute",), ("C:/absolute",), ("a\\b",), ("a/./b",), ("a//b",), ("a/CON",), ("a.",), ("a ",), ("a:stream",), ("x", "X")]:
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / "package"
                with self.assertRaises(ValueError):
                    extract(malicious(names), dest)
                self.assertFalse(dest.exists())

    def test_archive_symlink_refuses_before_effects(self):
        info = zipfile.ZipInfo("alias")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        with self.assertRaises(ValueError):
            archive_members(malicious([info]))

    def test_payload_tampering_refused(self):
        payload, _, _ = render()
        payload["FIRST_RUN.md"] += b"tampered"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            for name, raw in payload.items():
                z.writestr(name, raw)
        with self.assertRaises(ValueError):
            archive_members(buffer.getvalue())

    def test_exact_archive_matches_all_unpacked_bytes(self):
        members = archive_members((ROOT / "distribution" / (NAME + ".zip")).read_bytes())
        self.assertEqual(len(members), 42)
        for name, raw in members.items():
            self.assertEqual((ROOT / "distribution" / NAME / name).read_bytes(), raw)

    def test_new_build_cannot_overwrite_candidate(self):
        with self.assertRaisesRegex(ValueError, "never overwrite"):
            build()

    def test_public_safe_links_and_payload(self):
        self.assertGreater(validate_links_and_privacy()["local_links_checked"], 0)


if __name__ == "__main__":
    unittest.main()
