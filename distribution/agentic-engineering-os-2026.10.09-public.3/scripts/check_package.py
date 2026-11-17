"""Verify the extracted package file set and bytes before running its demo."""
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import sys

def safe_path(path):
    path = Path(path)
    if ".." in path.parts:
        raise ValueError("Parent traversal is forbidden")
    absolute = path.absolute()
    for entry in reversed((absolute, *absolute.parents)):
        try:
            info = entry.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Aliased package/destination path: " + str(entry))
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("Hardlinked package/destination file: " + str(entry))
    return absolute.resolve()


def manifest_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Manifest paths must be nonempty slash-separated relative strings")
    path = Path(value)
    if (path.is_absolute() or path.drive
            or any(part in {"", ".", ".."} or ":" in part or part.endswith((".", " "))
                   or getattr(os.path, "isreserved", lambda name: False)(part)
                   for part in value.split("/"))):
        raise ValueError("Unsafe manifest path: " + value)
    return path


def check(root):
    root = safe_path(root)
    if not root.is_dir():
        raise ValueError("Package root must be a directory")
    # Inspect EVERY entry before any manifest payload read or demo copy. Do not
    # follow directory links or silently ignore empty extra directories.
    actual, directories = set(), set()
    def walk(directory):
        for entry in directory.iterdir():
            p = safe_path(entry)
            rel = entry.relative_to(root).as_posix()
            if p.is_dir():
                directories.add(rel)
                walk(p)
            elif p.is_file():
                actual.add(rel)
            else:
                raise ValueError("Nonordinary package entry: " + rel)
    walk(root)
    manifest = json.loads(safe_path(root / "MANIFEST.json").read_text(encoding="utf8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("Manifest must contain a files array")
    paths, expected_dirs = [], set()
    for row in manifest["files"]:
        if not isinstance(row, dict) or not {"path", "bytes", "sha256"} <= row.keys():
            raise ValueError("Invalid manifest row")
        rel = row["path"]
        relative = manifest_path(rel)
        if rel == "MANIFEST.json" or rel.casefold() in {p.casefold() for p in paths}:
            raise ValueError("Duplicate/reserved manifest path: " + rel)
        paths.append(rel)
        expected_dirs.update(p.as_posix() for p in relative.parents if p != Path("."))
        if (type(row["bytes"]) is not int or row["bytes"] < 0
                or not isinstance(row["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
            raise ValueError("Invalid manifest length/digest: " + rel)
        p = safe_path(root / relative)
        if not p.is_file():
            raise ValueError("Missing or aliased file: " + rel)
        raw = p.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("Changed file: " + rel)
    if actual != set(paths) | {"MANIFEST.json"} or directories != expected_dirs:
        raise ValueError("Unexpected or missing package entries; run with python -B")
    return {"result": "package_bytes_match", "files": len(paths)}

if __name__ == "__main__":
    print(json.dumps(check(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).absolute().parents[1]))))
