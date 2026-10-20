"""Regressions for the cross-platform boundary scan; synthetic markers only.

Markers are assembled at runtime so this file never carries a literal one.
"""
from pathlib import Path
import io
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_public_boundary as boundary
from check_public_boundary import scan, scan_bytes, scan_history, scan_name

FAKE = {
    "private key block": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "AWS access key id": "AKIA" + "ABCDEFGHIJKLMNOP",
    "GitHub token": "ghp_" + "a" * 36,
    "Slack token": "xoxb-" + "1234567890-abc",
    "model provider API key": "sk-" + "ant-api03-" + "x" * 24,
    "Google API key": "AIza" + "B" * 35,
    "live payment key": "sk_" + "live_" + "c" * 24,
    "test payment key": "sk_" + "test_" + "d" * 24,
    "JSON web token": "eyJ" + "hbGciOiJIUzI1NiJ9" + ".eyJ" + "zdWIiOiIxMjM0In0" + "." + "e" * 43,
    "Azure storage key": "Account" + "Key=" + "f" * 86 + "==",
    "credential in URL": "postgres" + "://admin:" + "g" * 16 + "@db.example.com/app",
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

    def test_named_secret_assignments(self):
        for line in ("DB_" + "SECRET = 'h1ddenvalue99'", "export GITHUB_" + "TOKEN=abcdefgh1234"):
            with self.subTest(line=line):
                self.assertIn("credential assignment", markers("app.py", line))

    def test_placeholders_and_neutral_text_pass(self):
        neutral = "\n".join([
            "vault_root: <absolute path to your new vault>",
            "password: <set in your own secret store>",
            "api_key = ${API_KEY}",
            "C:\\Users\\<you>\\Workspace and C:\\Users\\Public",
            "/Users/<you>/vault",
            "postgres://<user>:<password>@localhost/app and https://example.com/a:b@c",
            "DB_SECRET = ${DB_SECRET}",
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

    def test_history_finds_deleted_secret(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "notes.md").write_text("token " + FAKE["GitHub token"], encoding="utf8")
            subprocess.run(git + ["add", "notes.md"], cwd=root, check=True)
            subprocess.run(git + ["commit", "-qm", "add"], cwd=root, check=True)
            (root / "notes.md").write_text("clean", encoding="utf8")
            subprocess.run(git + ["commit", "-qam", "remove"], cwd=root, check=True)
            self.assertEqual(scan(root)["findings"], [])
            result = scan_history(root)
        self.assertEqual(result["blobs_scanned"], 2)
        self.assertFalse(result["shallow"])
        self.assertEqual([(f["path"], f["marker"]) for f in result["findings"]], [("notes.md", "GitHub token")])

    def test_current_repository_is_clean(self):
        self.assertEqual(scan()["findings"], [])


class HistoryFilenameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.run(
            ["git", "-c", "user.name=Synthetic Test", "-c",
             "user.email=test@example.invalid", "-c", "commit.gpgsign=false", *args],
            cwd=self.root, check=True, capture_output=True).stdout

    def commit(self, files):
        for name, raw in files.items():
            path = self.root / name
            if raw is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        self.git("add", "-A")
        self.git("commit", "-qm", "synthetic fixture")

    def names(self, result):
        return {f["path"] for f in result["findings"]
                if f["marker"] == "secret-bearing file name"}

    def test_deleted_sensitive_filename_with_harmless_contents(self):
        self.commit({".env": b"harmless"})
        self.commit({".env": None, "README.md": b"ordinary"})
        self.assertEqual(scan(self.root)["findings"], [])
        self.assertEqual(self.names(scan_history(self.root)), {".env"})

    def test_deleted_sensitive_names_sharing_an_ordinary_blob(self):
        self.commit({"docs/notes.txt": b"harmless", ".env": b"harmless",
                     "old/credentials.json": b"harmless"})
        self.commit({".env": None, "old/credentials.json": None})
        self.assertEqual(scan(self.root)["findings"], [])
        result = scan_history(self.root)
        self.assertEqual(result["blobs_scanned"], 1)
        self.assertEqual(self.names(result), {".env", "old/credentials.json"})
        self.assertEqual(len(result["findings"]), 2)

    def test_sensitive_name_renamed_twice_without_content_changes(self):
        self.commit({"notes.txt": b"harmless"})
        self.git("mv", "notes.txt", ".env")
        self.git("commit", "-qm", "sensitive name")
        self.git("mv", ".env", "ordinary.txt")
        self.git("commit", "-qm", "ordinary name")
        result = scan_history(self.root)
        self.assertEqual(result["blobs_scanned"], 1)
        self.assertEqual(self.names(result), {".env"})

    def test_ordinary_duplicate_names_pass(self):
        self.commit({"docs/notes.txt": b"harmless", ".env.example": b"harmless",
                     "credentials.md": b"harmless"})
        self.commit({"docs/notes.txt": None})
        result = scan_history(self.root)
        self.assertEqual(result["blobs_scanned"], 1)
        self.assertEqual(result["findings"], [])

    def test_content_detection_is_deduplicated_but_labels_are_preserved(self):
        raw = FAKE["GitHub token"].encode()
        self.commit({"one.txt": raw, "two.txt": raw})
        with patch.object(boundary, "scan_text", wraps=boundary.scan_text) as text_scan:
            result = scan_history(self.root)
        self.assertEqual(text_scan.call_count, 1)
        self.assertEqual(result["blobs_scanned"], 1)
        self.assertEqual({(f["path"], f["marker"]) for f in result["findings"]},
                         {("one.txt", "GitHub token"), ("two.txt", "GitHub token")})

    def test_pattern_source_exemptions_are_applied_per_path(self):
        self.commit({"scripts/check_public_boundary.py": b"One" + b"Drive/notes",
                     "ordinary.txt": b"One" + b"Drive/notes"})
        result = scan_history(self.root)
        self.assertEqual([(f["path"], f["marker"]) for f in result["findings"]],
                         [("ordinary.txt", "synced personal folder")])

    def test_zip_aliases_and_archive_rename_keep_member_checks_and_bounds(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(".env", "harmless")
            archive.writestr("token.txt", FAKE["GitHub token"])
        raw = buffer.getvalue()
        self.commit({"data.bin": raw, "one.zip": raw, "two.ZIP": raw})
        self.commit({"one.zip": None, "two.ZIP": None})
        with patch.object(boundary, "scan_archive", wraps=boundary.scan_archive) as archive_scan:
            result = scan_history(self.root)
        self.assertEqual(archive_scan.call_count, 1)
        self.assertEqual(result["blobs_scanned"], 1)
        self.assertEqual(self.names(result), {"one.zip!.env", "two.ZIP!.env"})
        self.assertEqual({f["path"] for f in result["findings"] if f["marker"] == "GitHub token"},
                         {"one.zip!token.txt", "two.ZIP!token.txt"})
        for bound in ("MAX_ARCHIVE_MEMBERS", "MAX_ARCHIVE_BYTES"):
            with self.subTest(bound=bound), patch.object(boundary, bound, 1):
                findings = scan_history(self.root)["findings"]
                self.assertEqual({(f["path"], f["marker"]) for f in findings},
                                 {("one.zip", "archive exceeds scan bounds"),
                                  ("two.ZIP", "archive exceeds scan bounds")})

    def test_quoted_and_unicode_historical_paths(self):
        name = 'folder with spaces/caf\u00e9/.env'
        self.commit({name: b"harmless", "notes.txt": b"harmless"})
        self.commit({name: None})
        self.assertEqual(self.names(scan_history(self.root)), {name})

    def test_sensitive_name_on_merged_side_branch(self):
        self.commit({"notes.txt": b"harmless"})
        base = self.git("rev-parse", "HEAD").decode().strip()
        self.git("checkout", "-qb", "side")
        self.commit({".env": b"harmless"})
        self.commit({".env": None})
        self.git("checkout", "-qb", "other", base)
        self.commit({"other.txt": b"ordinary"})
        self.git("merge", "--no-ff", "-qm", "synthetic merge", "side")
        self.assertEqual(self.names(scan_history(self.root)), {".env"})

    def test_shallow_clone_reports_only_fetched_history(self):
        self.commit({".env": b"harmless", "notes.txt": b"harmless"})
        self.commit({".env": None})
        with tempfile.TemporaryDirectory() as temp:
            clone = Path(temp) / "clone"
            self.git("clone", "-q", "--depth=1", self.root.as_uri(), str(clone))
            result = scan_history(clone)
        self.assertTrue(result["shallow"])
        self.assertEqual(result["blobs_scanned"], 1)
        self.assertEqual(result["findings"], [])
        self.assertEqual(self.names(scan_history(self.root)), {".env"})

    def test_empty_commit_has_no_blobs(self):
        self.git("commit", "--allow-empty", "-qm", "empty synthetic root")
        result = scan_history(self.root)
        self.assertEqual(result["blobs_scanned"], 0)
        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
