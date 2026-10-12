"""Build a new deterministic candidate; never rewrite historical releases."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "agentic-engineering-os-2026.10.09-public.2"
VERSION = "2026.10.12-public.4-candidate.1"
NAME = "agentic-engineering-os-" + VERSION
COMMANDS = """python -m venv ../aeos-env
../aeos-env/Scripts/python -m pip install -r requirements.txt
../aeos-env/Scripts/python -B scripts/check_package.py .
$demoOutput = [System.IO.Path]::GetFullPath((Join-Path $PWD.Path '../aeos-first-run'))
../aeos-env/Scripts/python -B scripts/demo.py --output $demoOutput"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def render():
    source = ROOT / "distribution" / SOURCE
    old = json.loads((source / "MANIFEST.json").read_bytes())
    payload = {row["path"]: (source / row["path"]).read_bytes() for row in old["files"]}
    for row in old["files"]:
        raw = payload[row["path"]]
        if sha(raw) != row["sha256"] or len(raw) != row["bytes"]:
            raise ValueError("Historical source drift: " + row["path"])
    first = payload["FIRST_RUN.md"].decode("utf8")
    start, end = first.index("```powershell\n") if "```powershell\n" in first else first.index("```powershell\r\n"), None
    end = first.index("```", start + 3)
    first = first[:start] + "```powershell\n" + COMMANDS + "\n" + first[end:]
    first = first.replace("python -B vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py review", "../aeos-env/Scripts/python -B vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py review")
    first = first.replace("Choose new folder names", "The output expression resolves the sibling folder to an absolute path; the traversal guard still rejects literal `..` segments. Choose new folder names")
    payload["FIRST_RUN.md"] = first.encode("utf8")
    payload["README.md"] = payload["README.md"].replace(b"2026.10.09-public.2", VERSION.encode())
    manifest = {**old, "version": VERSION, "candidate_status": "UNPUBLISHED_REVIEW_CANDIDATE", "based_on": SOURCE}
    manifest["files"] = [{**row, "sha256": sha(payload[row["path"]]), "bytes": len(payload[row["path"]])} for row in old["files"]]
    payload["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(path, date_time=(2026, 10, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw, compresslevel=9)
    raw_zip = archive.getvalue()
    hashes = {"version": VERSION, "status": "UNPUBLISHED_REVIEW_CANDIDATE", "archive": NAME + ".zip", "sha256": sha(raw_zip), "bytes": len(raw_zip), "manifest_sha256": sha(payload["MANIFEST.json"]), "payload_files": len(payload) - 1}
    return payload, raw_zip, (json.dumps(hashes, indent=2) + "\n").encode()


def build(check=False):
    payload, archive, hashes = render()
    outputs = {ROOT / "distribution" / NAME / p: raw for p, raw in payload.items()}
    outputs[ROOT / "distribution" / (NAME + ".zip")] = archive
    outputs[ROOT / "distribution" / (NAME + ".sha256.json")] = hashes
    if check:
        for path, raw in outputs.items():
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError("Candidate differs from deterministic build: " + str(path.relative_to(ROOT)))
    else:
        if any(p.exists() for p in outputs) or (ROOT / "distribution" / NAME).exists():
            raise ValueError("Candidate already exists; use --check or a new version, never overwrite")
        for path, raw in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as f:
                f.write(raw)
    return json.loads(hashes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    print(json.dumps(build(parser.parse_args().check), indent=2))
