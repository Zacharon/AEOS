"""Bounded Windows validation of the actual candidate ZIP and published journey."""
from pathlib import Path
import argparse
import html
from html.parser import HTMLParser
import importlib.metadata
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import zipfile
from build_candidate import ROOT, NAME, SOURCE, COMMANDS, build, sha


def archive_members(raw):
    """Validate all names/identities/bounds before ANY extraction effect."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        if len(infos) > 100 or sum(i.file_size for i in infos) > 5_000_000:
            raise ValueError("Archive exceeds candidate bounds")
        seen, members = set(), {}
        for i in infos:
            p = i.orig_filename
            if (not p or "\\" in p or "\x00" in p or p.startswith("/") or ":" in p
                or any(part in {"", ".", ".."} or part.endswith((".", " "))
                       or getattr(os.path, "isreserved", lambda _: False)(part) for part in p.split("/"))
                or p.casefold() in seen or i.is_dir()
                or stat.S_IFMT(i.external_attr >> 16) not in {0, stat.S_IFREG}):
                raise ValueError("Unsafe archive entry: " + p)
            seen.add(p.casefold())
            members[p] = z.read(i)
        if "MANIFEST.json" not in members:
            raise ValueError("Archive lacks manifest")
        for p in members:
            if any(parent.as_posix().casefold() in seen for parent in Path(p).parents if parent != Path(".")):
                raise ValueError("Archive file/directory conflict")
        manifest = json.loads(members["MANIFEST.json"])
        rows = manifest["files"]
        if len({r["path"].casefold() for r in rows}) != len(rows):
            raise ValueError("Duplicate manifest entries")
        if set(members) != {r["path"] for r in rows} | {"MANIFEST.json"}:
            raise ValueError("Archive/manifest file set differs")
        for row in rows:
            raw = members[row["path"]]
            if len(raw) != row["bytes"] or sha(raw) != row["sha256"]:
                raise ValueError("Archive payload drift: " + row["path"])
        return members


def extract(raw, destination):
    members = archive_members(raw)
    if destination.exists():
        raise ValueError("Use a new extraction directory")
    destination.mkdir()
    for path, content in members.items():
        out = destination / path
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("xb") as f:
            f.write(content)
    return members


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in {"href", "src"} and value)


def validate_links_and_privacy():
    checked = 0
    files = list((ROOT / "site").rglob("*.html"))
    files += [ROOT / "README.md", ROOT / "docs/PACKAGE-CANDIDATE.md"]
    candidate = ROOT / "distribution" / NAME
    files += [p for p in candidate.rglob("*") if p.is_file()]
    for path in files:
        try:
            text = path.read_text(encoding="utf8")
        except UnicodeError:
            continue
        if re.search(r"(?i)(?:[a-z]:[/\\]users[/\\]|onedrive|file://|sk-proj-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)", text):
            raise ValueError("Private path/credential marker in " + str(path.relative_to(ROOT)))
        if path.suffix == ".html":
            parser = Links()
            parser.feed(text)
            links = parser.links
        elif path.suffix == ".md":
            links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)
        else:
            continue
        for value in links:
            url = urlsplit(html.unescape(value))
            if url.scheme or url.netloc:
                if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                    raise ValueError("Unsafe public link in " + str(path.relative_to(ROOT)))
                continue  # Static safety; upstream HTTP health is intentionally separate.
            if not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                raise ValueError("Missing/outside local link: " + str(path.relative_to(ROOT)) + " -> " + value)
            if path.is_relative_to(ROOT / "site") and not target.is_relative_to(ROOT / "site"):
                raise ValueError("Website publication-root escape")
            checked += 1
    return {"text_files_scanned": len(files), "local_links_checked": checked, "upstream_health": "NOT_RUN", "limit": "Bounded current payload/path/credential marker scan, not exhaustive secret audit"}


def first_block(text):
    return re.search(r"```powershell\s*\n(.*?)\n```", text, re.S).group(1).replace("\r\n", "\n")


def run(command, cwd, records, expected=0, timeout=300):
    p = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    records.append({"command": command, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    if p.returncode != expected:
        raise RuntimeError(f"Expected exit {expected}, got {p.returncode}: {p.stdout}\n{p.stderr}")
    return p


def journey(extracted, records):
    doc = (extracted / "FIRST_RUN.md").read_text(encoding="utf8")
    block = first_block(doc)
    if block != COMMANDS or first_block((ROOT / "README.md").read_text(encoding="utf8")) != block:
        raise ValueError("README/FIRST_RUN command drift")
    site = (ROOT / "site/first-run.html").read_text(encoding="utf8")
    site_block = html.unescape(re.search(r"<pre><code>(.*?)</code></pre>", site, re.S).group(1)).replace("\r\n", "\n")
    if site_block != block:
        raise ValueError("Website/FIRST_RUN command drift")
    # Execute verbatim published steps, only bind 'python' to the selected 3.14.5.
    lines = block.splitlines()
    lines[0] = "& '" + sys.executable.replace("'", "''") + "'" + lines[0][len("python"):]
    script = "$ErrorActionPreference = 'Stop'\n" + "\n".join(line + ("\nif ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }" if not line.startswith("$") else "") for line in lines)
    run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], extracted, records)
    output = extracted.parent / "aeos-first-run"
    receipt = json.loads((output / "RESULT.json").read_bytes())
    if not (receipt["result"] == "DEMO_LOCAL_PASSED" and receipt["owner_decision"] == "pending"
            and receipt["gold_applied"] is False and receipt["h3_verdict"] is None and receipt["stale_and_missing_refused"]):
        raise ValueError("Demo receipt crossed acceptance boundary")
    resume = re.search(r"To resume,.*?```powershell\s*\n(.*?)\n```", doc, re.S).group(1)
    run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", resume + "\nexit $LASTEXITCODE"], output, records)
    python = extracted.parent / "aeos-env/Scripts/python.exe"
    # Fresh negative security evidence before effects, same extracted package.
    rejected = output.parent / "refused-output"
    p = subprocess.run([str(python), "-B", "scripts/demo.py", "--output", "../refused-output"], cwd=extracted, capture_output=True, text=True)
    records.append({"command": "literal ../refused-output security regression", "exit_code": p.returncode, "stderr": p.stderr})
    if p.returncode == 0 or "Parent traversal is forbidden" not in p.stderr or rejected.exists():
        raise ValueError("Traversal guard weakened")
    p = subprocess.run([str(python), "-B", "scripts/demo.py", "--output", str(output)], cwd=extracted, capture_output=True, text=True)
    records.append({"command": "existing destination security regression", "exit_code": p.returncode, "stderr": p.stderr})
    if p.returncode == 0 or "prior evidence is preserved" not in p.stderr:
        raise ValueError("Existing-output refusal weakened")
    return python, receipt


def validate():
    if os.name != "nt" or sys.version_info[:3] != (3, 14, 5):
        raise ValueError("Intended validation requires Windows CPython 3.14.5")
    hashes = build(check=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="AEOS package with spaces ") as temp:
        base = Path(temp)
        old = base / "historical"
        extract((ROOT / "distribution" / (SOURCE + ".zip")).read_bytes(), old)
        old_cmd = first_block((old / "FIRST_RUN.md").read_text(encoding="utf8")).splitlines()[-1]
        # Reproduce the actual historical documented demo destination in extraction.
        p = subprocess.run([sys.executable, "-B", "scripts/demo.py", "--output", old_cmd.split("--output ")[1]], cwd=old, capture_output=True, text=True)
        records.append({"command": old_cmd, "exit_code": p.returncode, "stderr": p.stderr})
        if p.returncode == 0 or "Parent traversal is forbidden" not in p.stderr or (base / "aeos-first-run").exists():
            raise ValueError("Historical failure not reproduced")
        extracted = base / "candidate"
        extract((ROOT / "distribution" / (NAME + ".zip")).read_bytes(), extracted)
        python, receipt = journey(extracted, records)
        suites = [("scripts", 7), ("vault/00_SYSTEM/AGENTIC_LIBRARIAN/tests", 38), ("vault/09_TOOLS/agent_runner_v1/unified_handoff", 40), ("vault/09_TOOLS/agent_runner_v1/scripts/tests", 1)]
        for directory, count in suites:
            result = run([str(python), "-B", "-m", "unittest", "discover", "-s", directory, "-p", "test_*.py"], extracted, records, timeout=600)
            if f"Ran {count} tests" not in result.stderr and f"Ran {count} test" not in result.stderr:
                raise ValueError("Existing suite count changed")
            if "skipped=" in result.stderr:
                raise ValueError("Required Windows security regression skipped")
        run([str(python), "-B", "scripts/check_package.py", "."], extracted, records)
        regression = run([str(python), "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], ROOT, records)
    return {"state": "LOCAL_VERIFIED", "archive": hashes, "environment": {"os": sys.platform, "python": sys.version.split()[0]}, "baseline_tests": 86, "new_tests_output": regression.stderr, "packaged_journey": receipt, "public_boundaries": validate_links_and_privacy(), "commands": records, "ci": "NOT_RUN_BY_LOCAL_COMMAND", "independent_H3": "NOT_RUN_BY_IMPLEMENTER", "publication": "NOT_RUN_OWNER_GATED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = validate()
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps({key: value for key, value in result.items() if key != "commands"}, indent=2))
