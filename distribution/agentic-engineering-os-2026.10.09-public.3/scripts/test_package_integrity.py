"""Synthetic tiny packages; no real package manifest or external data modified."""
import hashlib
import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CHECK = Path(__file__).with_name("check_package.py")
DEMO = Path(__file__).with_name("demo.py")


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="pi-"))
        self.root = self.base / "p"
        self.root.mkdir()
        (self.root / "file").write_bytes(b"safe")
        (self.root / "MANIFEST.json").write_text(json.dumps({"files": [{"path": "file", "bytes": 4,
            "sha256": hashlib.sha256(b"safe").hexdigest()}]}))

    def tearDown(self):
        shutil.rmtree(self.base)

    def check(self, optimized=False):
        return subprocess.run([sys.executable, "-B", *( ["-O"] if optimized else []), str(CHECK), str(self.root)], capture_output=True)

    def test_extra_directory_alias_is_refused_before_demo_copy(self):
        outside = self.base / "out"
        outside.mkdir()
        try:
            (self.root / "vault").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(str(exc))
        self.assertNotEqual(self.check().returncode, 0)

    def test_modified_file_is_refused_when_optimized(self):
        (self.root / "file").write_bytes(b"evil")
        self.assertNotEqual(self.check(True).returncode, 0)

    def test_exact_package_passes_optimized(self):
        self.assertEqual(self.check(True).returncode, 0)

    def test_modified_extra_missing_and_traversal_refuse_all_modes(self):
        original = (self.root / "MANIFEST.json").read_bytes()
        for mode, inherited in (([], None), (["-O"], None), (["-OO"], None), ([], "1"), ([], "2")):
            for fault in ("changed", "extra", "missing", "traversal", "duplicate", "empty_dir"):
                with self.subTest(mode=mode, inherited=inherited, fault=fault):
                    (self.root / "file").write_bytes(b"evil" if fault == "changed" else b"safe")
                    if fault == "extra":
                        (self.root / "extra").write_bytes(b"extra")
                    elif fault == "missing":
                        (self.root / "file").unlink()
                    elif fault == "empty_dir":
                        (self.root / "empty").mkdir()
                    elif fault in {"traversal", "duplicate"}:
                        manifest = json.loads(original)
                        if fault == "traversal":
                            manifest["files"][0]["path"] = "../file"
                        else:
                            manifest["files"].append(manifest["files"][0])
                        (self.root / "MANIFEST.json").write_text(json.dumps(manifest))
                    env = dict(os.environ)
                    env.pop("PYTHONOPTIMIZE", None)
                    if inherited:
                        env["PYTHONOPTIMIZE"] = inherited
                    result = subprocess.run([sys.executable, "-B", *mode, str(CHECK), str(self.root)], env=env, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    (self.root / "MANIFEST.json").write_bytes(original)
                    (self.root / "extra").unlink(missing_ok=True)
                    if (self.root / "empty").exists():
                        (self.root / "empty").rmdir()

    def test_native_junction_rejected_before_demo_output_created(self):
        if os.name != "nt":
            self.skipTest("Native Windows junction test")
        outside = self.base / "out"
        outside.mkdir()
        made = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(self.root / "vault"), str(outside)], capture_output=True)
        self.assertEqual(made.returncode, 0, made.stderr)
        self.assertNotEqual(self.check().returncode, 0)
        sys.path.insert(0, str(DEMO.parent))
        try:
            spec = importlib.util.spec_from_file_location("synthetic_demo", DEMO)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            output = self.base / "demo"
            with self.assertRaises(ValueError):
                module.demo(self.root, output)
            self.assertFalse(output.exists())
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            sys.path.pop(0)

    def test_alias_ancestor_and_hardlink_rejected(self):
        outside = self.base / "out"
        os.link(self.root / "file", outside)
        self.assertNotEqual(self.check().returncode, 0)
        outside.unlink()
        alias = self.base / "alias"
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except OSError as exc:
            self.skipTest(str(exc))
        result = subprocess.run([sys.executable, "-B", str(CHECK), str(alias)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_production_gates_do_not_use_assert(self):
        for path in (CHECK, DEMO):
            self.assertFalse(any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(path.read_text(encoding="utf8")))))


if __name__ == "__main__":
    unittest.main()
