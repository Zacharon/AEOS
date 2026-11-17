"""Builder tests use public bytes in disposable fixtures, never release writes."""
import importlib.util
from pathlib import Path
import json
import shutil
import tempfile
import unittest
import zipfile
import io
import sys

REPO = Path(__file__).absolute().parents[1]
spec = importlib.util.spec_from_file_location("public_builder", REPO / "tools/build_public.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="public build ")
        self.root = Path(self.tmp.name)
        shutil.copytree(REPO / "distribution" / builder.OLD, self.root / "distribution" / builder.OLD)
        shutil.copytree(REPO / "tools/package_overrides", self.root / "tools/package_overrides")
        builder.REPO = self.root

    def tearDown(self):
        builder.REPO = REPO
        self.tmp.cleanup()

    def test_repeated_build_is_identical(self):
        first = builder.build()
        self.assertEqual(first, builder.build())
        self.assertEqual((self.root/"distribution"/(builder.NEW+".zip")).read_bytes(), (self.root/"site/downloads"/(builder.NEW+".zip")).read_bytes())

    def test_unknown_overlay_refused_before_output(self):
        (self.root/"tools/package_overrides/secret.txt").write_text("fixture")
        with self.assertRaisesRegex(ValueError, "Overlay allowlist"):
            builder.build()
        self.assertFalse((self.root/"distribution"/builder.NEW).exists())

    def test_extra_empty_overlay_directory_refused_before_output(self):
        (self.root/"tools/package_overrides/empty").mkdir()
        with self.assertRaisesRegex(ValueError,"Overlay allowlist"):
            builder.build()
        self.assertFalse((self.root/"distribution"/builder.NEW).exists())

    def test_overlay_directory_alias_refused_before_output(self):
        outside=self.root/"outside"
        outside.mkdir()
        alias=self.root/"tools/package_overrides/alias"
        import os
        import subprocess
        if os.name=="nt":
            made=subprocess.run(["cmd.exe","/d","/c","mklink","/J",str(alias),str(outside)],capture_output=True)
            self.assertEqual(made.returncode,0,made.stderr)
        else:
            alias.symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,"Aliased"):
            builder.build()
        self.assertFalse((self.root/"distribution"/builder.NEW).exists())
        self.assertEqual(list(outside.iterdir()),[])

    def test_changed_seed_refused_before_output(self):
        (self.root/"distribution"/builder.OLD/"FIRST_RUN.md").write_text("changed")
        with self.assertRaisesRegex(ValueError, "Changed file"):
            builder.build()
        self.assertFalse((self.root/"distribution"/builder.NEW).exists())

    def test_conflicting_archive_preserved(self):
        path=self.root/"distribution"/(builder.NEW+".zip")
        path.write_bytes(b"previous evidence")
        with self.assertRaisesRegex(ValueError, "Existing output differs"):
            builder.build()
        self.assertEqual(path.read_bytes(), b"previous evidence")

    def test_archive_has_exact_manifest_set_and_no_runtime_outputs(self):
        entries=builder.payload()
        raw=builder.archive(entries)
        self.assertEqual(raw,builder.archive(entries))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual(z.namelist(),sorted(entries))
            for rel in z.namelist():
                self.assertNotIn("__pycache__",rel)
                self.assertNotIn("..",Path(rel).parts)
                self.assertEqual(z.read(rel),entries[rel])
        manifest=json.loads(entries["MANIFEST.json"])
        self.assertEqual({r["path"] for r in manifest["files"]},set(entries)-{"MANIFEST.json"})

    def test_refresh_preserves_conflicting_archive(self):
        builder.build()
        path=self.root/"distribution"/(builder.NEW+".zip")
        path.write_bytes(b"conflicting evidence")
        with self.assertRaisesRegex(ValueError,"exact prior candidate archive"):
            builder.build(refresh=True)
        self.assertEqual(path.read_bytes(),b"conflicting evidence")

    def test_verified_refresh_only_updates_new_candidate(self):
        old=(self.root/"distribution"/builder.OLD/"README.md").read_bytes()
        first=builder.build()
        overlay=self.root/"tools/package_overrides/README.md"
        overlay.write_bytes(overlay.read_bytes()+b"\nSynthetic review correction.\n")
        with self.assertRaisesRegex(ValueError,"Existing output differs"):
            builder.build()
        updated=builder.build(refresh=True)
        self.assertNotEqual(first["archive_sha256"],updated["archive_sha256"])
        self.assertEqual((self.root/"distribution"/builder.OLD/"README.md").read_bytes(),old)
        self.assertEqual(updated,builder.build())

    def test_archive_verification_refuses_before_output_creation(self):
        sys.path.insert(0,str(REPO/"tools"))
        try:
            import qualify_public
            expected=builder.payload()
            expected["scripts/demo.py"]=b"tampered fixture"
            path=self.root/"tampered.zip"
            path.write_bytes(builder.archive(expected))
            destination=self.root/"not created"
            with self.assertRaisesRegex(ValueError,"Archive bytes differ"):
                qualify_public.extract_verified(path,destination,builder.payload())
            self.assertFalse(destination.exists())
            # Same complete-byte guard also refuses extra, traversal and
            # duplicate members before any directory creation.
            for name in ("extra.log","../outside"):
                with zipfile.ZipFile(path,"a") as z:
                    z.writestr(name,b"fixture")
                with self.assertRaisesRegex(ValueError,"member allowlist"):
                    qualify_public.extract_verified(path,destination,builder.payload())
                self.assertFalse(destination.exists())
        finally:
            sys.path.pop(0)

    def test_overlay_links_use_generated_destination_and_missing_target_refuses(self):
        sys.path.insert(0,str(REPO/"tools"))
        import qualify_public
        original=qualify_public.REPO
        qualify_public.REPO=self.root
        try:
            builder.build()
            path=self.root/"tools/package_overrides/ARCHITECTURE.md"
            self.assertGreater(qualify_public.validate_local_links(path,path.read_text(encoding="utf8")),0)
            with self.assertRaisesRegex(RuntimeError,"Missing public link"):
                qualify_public.validate_local_links(path,"[Missing](vault/does-not-exist.md)")
        finally:
            qualify_public.REPO=original
            sys.path.pop(0)

    def test_unbound_or_stale_saved_logs_cannot_resume_qualification(self):
        import subprocess
        from unittest.mock import patch
        sys.path.insert(0,str(REPO/"tools"))
        try:
            import qualify_public
            saved=self.root/"new-handoff.log"
            saved.write_bytes(b"unrelated synthetic output\nRan 40 tests in 0.001s\n\nOK\n")
            stale=self.root/"public-safe-receipt.json"
            stale.write_bytes(b'{"archive_sha256":"stale-synthetic-identity"}')
            before={p.name:p.read_bytes() for p in (saved,stale)}
            result=subprocess.run([sys.executable,"-B",str(REPO/"tools/qualify_public.py"),"--resume-work",str(self.root)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn("--work --extract-public-3 is required",result.stderr)
            unknown=subprocess.run([sys.executable,"-B",str(REPO/"tools/qualify_public.py"),"--work",str(self.root),"--resume-work",str(self.root)],capture_output=True,text=True)
            self.assertEqual(unknown.returncode,2)
            self.assertIn("unrecognized arguments",unknown.stderr)
            with patch.object(qualify_public.subprocess,"run",side_effect=AssertionError("No command may run before prior evidence refusal")):
                with self.assertRaisesRegex(ValueError,"Prior qualification evidence"):
                    qualify_public.qualify(self.root)
            self.assertEqual({p.name:p.read_bytes() for p in (saved,stale)},before)
            self.assertFalse((self.root/"steps.json").exists())
        finally:
            sys.path.pop(0)

if __name__ == "__main__":
    unittest.main()
