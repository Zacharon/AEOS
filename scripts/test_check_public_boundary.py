"""Regressions for the cross-platform boundary scan; synthetic markers only.

Markers are assembled at runtime so this file never carries a literal one.
"""
from pathlib import Path
import io
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_public_boundary import scan, scan_bytes, scan_name

FAKE = {
    "private key block": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "AWS access key id": "AKIA" + "ABCDEFGHIJKLMNOP",
    "GitHub token": "ghp_" + "a" * 36,
    "Slack token": "xoxb-" + "1234567890-abc",
    "model provider API key": "sk-" + "ant-api03-" + "x" * 24,
    "Google API key": "AIza" + "B" * 35,
    "live payment key": "sk_" + "live_" + "c" * 24,
    "credential assignment": "api_key" + " = " + "s3cr3tvalue99",
    "Windows user path": "C:" + "\\Users\\" + "someone\\vault",
    "macOS user path": "/Users/" + "someone/vault",
    "synced personal folder": "One" + "Drive/notes",
    "local file URL": "file" + ":///tmp/x",
}


def markers(label, text):
    return {f["marker"] for f in scan_bytes(label, text.encode("utf8"))}


class BoundaryScanTests(unittest.TestCase):
    def test_each_marker_detected(self):
        for marker, sample in FAKE.items():
            with self.subTest(marker=marker):
                self.assertIn(marker, markers("doc.md", "context\n" + sample + " context"))

    def test_placeholders_and_neutral_text_pass(self):
        neutral = "\n".join([
            "vault_root: <absolute path to your new vault>",
            "password: <set in your own secret store>",
            "api_key = ${API_KEY}",
            "C:\\Users\\<you>\\Workspace and C:\\Users\\Public",
            "/Users/<you>/vault",
            "Do not store credentials in this file.",
        ])
        self.assertEqual(markers("README.md", neutral), set())

    def test_secret_bearing_names(self):
        for name in (".env", ".env.local", "deploy.pem", "id_ed25519", "credentials.json", "a/b/store.pfx", ".netrc"):
            with self.subTest(name=name):
                self.assertTrue(scan_name(name))
        for name in (".env.example", "README.md", "keys.md", "credentials.md", "check_package.py"):
            with self.subTest(name=name):
                self.assertFalse(scan_name(name))

    def test_archive_members_scanned(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("pkg/README.md", "clean")
            z.writestr("pkg/config.md", "token " + FAKE["GitHub token"])
            z.writestr("pkg/.env", "X=1")
        found = scan_bytes("dist/pkg.zip", buffer.getvalue())
        self.assertIn({"path": "dist/pkg.zip!pkg/config.md", "marker": "GitHub token"}, found)
        self.assertIn({"path": "dist/pkg.zip!pkg/.env", "marker": "secret-bearing file name"}, found)
        self.assertFalse([f for f in found if f["path"].endswith("README.md")])

    def test_unreadable_archive_is_a_finding(self):
        self.assertEqual(scan_bytes("x.zip", b"not a zip")[0]["marker"], "unreadable archive")

    def test_tracked_files_in_a_synthetic_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "ok.md").write_text("neutral", encoding="utf8")
            (root / "leak.md").write_text(FAKE["AWS access key id"], encoding="utf8")
            (root / "untracked.md").write_text(FAKE["AWS access key id"], encoding="utf8")
            subprocess.run(["git", "add", "ok.md", "leak.md"], cwd=root, check=True)
            result = scan(root)
        self.assertEqual(result["files_scanned"], 2)
        self.assertEqual(result["findings"], [{"path": "leak.md", "marker": "AWS access key id"}])

    def test_current_repository_is_clean(self):
        self.assertEqual(scan()["findings"], [])


if __name__ == "__main__":
    unittest.main()
