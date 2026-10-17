"""Cross-platform public-boundary scan of every tracked file and archive member.

Complements validate_candidate.py (Windows, candidate-scoped) with a fast check
that runs on any OS: credential markers, private paths and secret-bearing file
names anywhere in the repository, including inside committed ZIP archives.
Bounded pattern scan, not an exhaustive secret audit.
"""
from pathlib import Path, PurePosixPath
import argparse
import io
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]

CONTENT_MARKERS = {
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "AWS access key id": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "GitHub token": r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})",
    "Slack token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "model provider API key": r"\bsk-(?:proj-|ant-[a-z0-9]+-)?[A-Za-z0-9_-]{20,}",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "live payment key": r"\b[rs]k_live_[0-9A-Za-z]{20,}",
    "credential assignment": r"(?im)^\s*(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[^\s'\"<{$]{8,}",
    "Windows user path": r"(?i)\b[a-z]:[/\\]+users[/\\]+(?!<|%|\{|\$|public\b|default\b)[^/\\\s]+",
    "macOS user path": r"/Users/(?!<|\{|\$|Shared\b)[A-Za-z0-9._-]+/",
    "synced personal folder": r"(?i)onedrive|dropbox[/\\]|google drive[/\\]",
    "local file URL": r"(?i)file://",
}
PATTERNS = {name: re.compile(rx) for name, rx in CONTENT_MARKERS.items()}

SECRET_NAMES = re.compile(
    r"(?i)^(?:\.env(?!\.(?:example|sample|template)$)(?:\..+)?|\.netrc|\.npmrc|\.pypirc|"
    r"credentials(?:\.json)?|id_(?:rsa|dsa|ecdsa|ed25519)(?:\.pub)?|.+\.(?:pem|key|p12|pfx|jks|keystore|kdbx))$")

# The scanners' own pattern source necessarily spells these markers.
PATTERN_SOURCES = {"scripts/check_public_boundary.py", "scripts/validate_candidate.py"}
PATTERN_SOURCE_MARKERS = {"synced personal folder", "local file URL"}

MAX_ARCHIVE_MEMBERS = 500
MAX_ARCHIVE_BYTES = 50_000_000


def scan_text(label, text):
    return [{"path": label, "marker": name} for name, rx in PATTERNS.items() if rx.search(text)]


def scan_name(label):
    name = PurePosixPath(label.replace("\\", "/")).name
    return [{"path": label, "marker": "secret-bearing file name"}] if SECRET_NAMES.match(name) else []


def scan_bytes(label, raw):
    findings = scan_name(label)
    if label.lower().endswith(".zip"):
        return findings + scan_archive(label, raw)
    try:
        text = raw.decode("utf8")
    except UnicodeDecodeError:
        return findings  # Binary payloads are out of scope for this text scan.
    return findings + scan_text(label, text)


def scan_archive(label, raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            if len(infos) > MAX_ARCHIVE_MEMBERS or sum(i.file_size for i in infos) > MAX_ARCHIVE_BYTES:
                return [{"path": label, "marker": "archive exceeds scan bounds"}]
            findings = []
            for info in infos:
                findings += scan_bytes(label + "!" + info.filename, z.read(info))
            return findings
    except zipfile.BadZipFile:
        return [{"path": label, "marker": "unreadable archive"}]


def tracked_files(root):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf8").split("\0") if p]


def scan(root=ROOT, paths=None):
    paths = tracked_files(root) if paths is None else paths
    findings = []
    for rel in paths:
        path = root / rel
        if path.is_file():
            findings += [f for f in scan_bytes(rel, path.read_bytes())
                         if not (rel in PATTERN_SOURCES and f["marker"] in PATTERN_SOURCE_MARKERS)]
    return {"files_scanned": len(paths), "findings": findings,
            "limit": "Bounded marker/name scan of tracked files and ZIP members, not an exhaustive secret audit"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="Repository-relative files (default: all tracked files)")
    args = parser.parse_args()
    result = scan(paths=args.paths or None)
    print(json.dumps(result, indent=2))
    sys.exit(1 if result["findings"] else 0)
