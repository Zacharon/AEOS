"""Verify the extracted package file set and bytes before running its demo."""
from pathlib import Path
import hashlib
import json
import sys

def check(root):
    root = root.resolve()
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf8"))
    paths = [r["path"] for r in manifest["files"]]
    assert len(paths) == len(set(paths)), "Duplicate manifest path"
    for row in manifest["files"]:
        rel = row["path"]
        assert not Path(rel).is_absolute() and ".." not in Path(rel).parts
        p = root / rel
        assert not p.is_symlink() and p.is_file(), "Missing or aliased file: " + rel
        raw = p.read_bytes()
        assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "Changed file: " + rel
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert actual == set(paths) | {"MANIFEST.json"}, "Unexpected or missing package files; run with python -B"
    return {"result": "package_bytes_match", "files": len(paths)}

if __name__ == "__main__":
    print(json.dumps(check(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]))))
