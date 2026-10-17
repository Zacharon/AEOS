"""Build public.4 from the frozen public.3 archive without rewriting history."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile
from validate_candidate import archive_members

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "agentic-engineering-os-2026.10.09-public.3"
NAME = "agentic-engineering-os-2026.10.17-public.4"
SOURCE_SHA = "5fd48062e579e4f15c712e82b4abbf3592cac81566c7a1550102babca836d079"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def replace(payload, name, old, new):
    raw, before = payload[name], old.encode("utf-8")
    if raw.count(before) != 1:
        raise ValueError(f"Expected one occurrence in {name}: {old}")
    payload[name] = raw.replace(before, new.encode("utf-8"))

def render():
    source_zip = (ROOT / "distribution" / (SOURCE + ".zip")).read_bytes()
    if sha(source_zip) != SOURCE_SHA:
        raise ValueError("Frozen public.3 archive changed")
    payload = archive_members(source_zip)
    for name, raw in payload.items():
        if (ROOT / "distribution" / SOURCE / name).read_bytes() != raw:
            raise ValueError("Frozen public.3 extraction changed: " + name)
    payload = dict(payload)
    version_old = "sys.version_info[:3] == (3,14,5) else 'Use CPython 3.14.5'"
    version_new = "sys.version_info >= (3,11) else 'Use CPython 3.11 or newer'"
    changes = [
        ("README.md", "2026.10.09-public.3", "2026.10.17-public.4"),
        ("README.md", "- CPython 3.14.5; this revision qualified in a fresh Windows virtual environment with CPython 3.14.5, PyYAML 6.0.3 and jsonschema 4.26.0.",
         "- CPython 3.11 or newer; tested on Windows with CPython 3.11.15 and 3.14.5 in fresh virtual environments, PyYAML 6.0.3 and jsonschema 4.26.0."),
        ("README.md", "This is a reviewable repair candidate, not a merged release.",
         "This public.4 source preview derives from frozen public.3. The separate public.4-candidate.1 remains an unpublished public.2-lineage candidate."),
        ("FIRST_RUN.md", "Use your installed CPython 3.14.5.",
         "Use CPython 3.11 or newer (tested on 3.11.15 and 3.14.5 on Windows)."),
        ("FIRST_RUN.md", version_old, version_new),
        ("FIRST_RUN.md", "Windows PowerShell and CPython 3.14.5 are locally qualified; hosted CI is defined separately and has not run for this candidate.",
         "Windows PowerShell with CPython 3.11.15 and 3.14.5 is locally tested. Hosted CI results are reported separately in the repository."),
        ("ARCHITECTURE.md", version_old, version_new),
        ("ARCHITECTURE.md", "current candidate [public.3 package](README.md). Historical public.1 and public.3 remain separate, frozen revisions.",
         "current [public.4 package](README.md). Historical public.1, public.2 and public.3 remain separate, frozen revisions."),
    ]
    for name, old, new in changes:
        replace(payload, name, old, new)
    # Python 3.11 lacks os.path.isreserved; retain reserved-name refusal.
    for name in ("scripts/check_package.py", "vault/00_SYSTEM/AGENTIC_LIBRARIAN/librarian.py"):
        old = ('getattr(os.path, "isreserved", lambda name: False)(part)' if name.startswith("scripts/")
               else 'getattr(os.path, "isreserved", lambda value: False)(part)')
        replace(payload, name, old,
                'getattr(os.path, "isreserved", lambda value: PureWindowsPath(value).is_reserved())(part)')
        replace(payload, name, "from pathlib import Path", "from pathlib import Path, PureWindowsPath")
    # onerror is supported by both versions; these callbacks ignore the exception object.
    for name in ("vault/00_SYSTEM/AGENTIC_LIBRARIAN/tests/test_librarian_cli.py",
                 "vault/00_SYSTEM/AGENTIC_LIBRARIAN/tests/test_librarian_integrity.py"):
        replace(payload, name, "onexc=", "onerror=")
    replace(payload, "vault/00_SYSTEM/AGENTIC_LIBRARIAN/tests/test_librarian_integrity.py",
            "self.assertTrue(link.is_junction())",
            "self.assertTrue(bool(getattr(link.lstat(), 'st_file_attributes', 0) & 0x400))")
    manifest = json.loads(payload["MANIFEST.json"])
    manifest["version"] = "2026.10.17-public.4"
    manifest["basis"] = "Frozen public.3 archive with CPython 3.11 compatibility adjustments"
    manifest["based_on"] = SOURCE
    manifest["files"] = [
        {**row, "bytes": len(payload[row["path"]]), "sha256": sha(payload[row["path"]])}
        for row in manifest["files"]
    ]
    payload["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw, compresslevel=9)
    archive = buffer.getvalue()
    archive_members(archive)
    hashes = {
        "version": manifest["version"], "based_on": SOURCE, "status": "PUBLIC_SOURCE_PREVIEW",
        "archive": NAME + ".zip", "sha256": sha(archive), "bytes": len(archive),
        "manifest_sha256": sha(payload["MANIFEST.json"]), "payload_files": len(payload) - 1,
    }
    return payload, archive, (json.dumps(hashes, indent=2) + "\n").encode("utf-8")

def build(check=False):
    payload, archive, hashes = render()
    outputs = {ROOT / "distribution" / NAME / path: raw for path, raw in payload.items()}
    outputs[ROOT / "distribution" / (NAME + ".zip")] = archive
    outputs[ROOT / "distribution" / (NAME + ".sha256.json")] = hashes
    outputs[ROOT / "site" / "downloads" / (NAME + ".zip")] = archive
    if check:
        for path, raw in outputs.items():
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError("Public.4 output differs: " + str(path.relative_to(ROOT)))
    else:
        if any(path.exists() for path in outputs) or (ROOT / "distribution" / NAME).exists():
            raise ValueError("Public.4 exists; use --check or a new version")
        for path, raw in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(raw)
    return json.loads(hashes)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    print(json.dumps(build(parser.parse_args().check), indent=2))
