"""Build only the frozen public.2 allowlist plus reviewed public.3 overlays.

No private source lookup, environment discovery, release or provider action.
Existing output must already equal the deterministic result; never clobber it.
"""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import sys
import zipfile

REPO = Path(__file__).absolute().parents[1]
OLD = "agentic-engineering-os-2026.10.09-public.2"
NEW = "agentic-engineering-os-2026.10.09-public.3"
SEED_MANIFEST = "5fb40043afdc13984c1d04f9c7b0e3397af38c5f21b896a8a9dcc4558e745a7f"
OVERLAYS = ("FIRST_RUN.md", "README.md", "ARCHITECTURE.md", "SECURITY-REPAIRS.md", "scripts/demo.py", "scripts/test_first_run.py")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def checker():
    spec = importlib.util.spec_from_file_location("public_package_check", REPO / "distribution" / OLD / "scripts/check_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def payload():
    guard = checker()
    seed = guard.safe_path(REPO / "distribution" / OLD)
    manifest_raw = (seed / "MANIFEST.json").read_bytes()
    if sha(manifest_raw) != SEED_MANIFEST:
        raise ValueError("Frozen public.2 manifest changed")
    guard.check(seed)
    old = json.loads(manifest_raw)
    paths = [row["path"] for row in old["files"]]
    entries = {rel: (seed / guard.manifest_path(rel)).read_bytes() for rel in paths}
    overlay = guard.safe_path(REPO / "tools/package_overrides")
    actual, directories = set(), set()
    def inspect(directory):
        for entry in directory.iterdir():
            path = guard.safe_path(entry)
            rel = entry.relative_to(overlay).as_posix()
            if path.is_dir():
                directories.add(rel)
                inspect(path)
            elif path.is_file():
                actual.add(rel)
            else:
                raise ValueError("Nonordinary overlay entry: " + rel)
    inspect(overlay)
    expected_dirs = {p.as_posix() for rel in OVERLAYS for p in Path(rel).parents if p != Path(".")}
    if actual != set(OVERLAYS) or directories != expected_dirs:
        raise ValueError("Overlay allowlist differs")
    for rel in OVERLAYS:
        entries[rel] = guard.safe_path(overlay / rel).read_bytes()
    manifest = {"schema_version": 1, "package": old["package"], "version": "2026.10.09-public.3",
                "scope": old["scope"], "basis": "Frozen public.2 file allowlist plus explicit public.3 overlays",
                "files": [{"path": rel, "bytes": len(raw), "sha256": sha(raw), "source": "public-baseline/" + rel}
                          for rel, raw in sorted(entries.items())]}
    entries["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return entries

def archive(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(rel, (2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    return stream.getvalue()

def write_exact(path, raw, previous=None):
    path = checker().safe_path(path)
    if path.exists():
        if not path.is_file():
            raise ValueError("Existing output differs; preserve and inspect: " + str(path))
        current = path.read_bytes()
        if current != raw:
            if previous is None or current != previous:
                raise ValueError("Existing output differs; preserve and inspect: " + str(path))
            path.write_bytes(raw)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as f:
            f.write(raw)

def build(refresh=False):
    entries = payload()
    root = checker().safe_path(REPO / "distribution" / NEW)
    previous = {}
    previous_archive = None
    if root.exists():
        checker().check(root)
        if {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} != set(entries):
            raise ValueError("Existing public.3 file set differs")
        if refresh:
            previous = {rel: (root / rel).read_bytes() for rel in entries}
            previous_archive = archive(previous)
            for directory in ("distribution", "site/downloads"):
                path = checker().safe_path(REPO / directory / (NEW + ".zip"))
                if not path.is_file() or path.read_bytes() != previous_archive:
                    raise ValueError("Refresh requires exact prior candidate archive copies")
    for rel, raw in entries.items():
        write_exact(root / rel, raw, previous.get(rel))
    checker().check(root)
    raw = archive(entries)
    for directory in ("distribution", "site/downloads"):
        write_exact(REPO / directory / (NEW + ".zip"), raw, previous_archive)
    return {"version": "2026.10.09-public.3", "files": len(entries), "manifest_payload_entries": len(entries)-1,
            "manifest_sha256": sha(entries["MANIFEST.json"]), "archive_sha256": sha(raw), "archive_bytes": len(raw),
            "copies_identical": True, "deterministic": True}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--refresh", action="store_true", help="Update only a byte-verified existing public.3 candidate and its exact archive copies")
    print(json.dumps(build(p.parse_args().refresh), indent=2))
