"""Cross-platform public-boundary scan of every tracked file and archive member.

Complements validate_candidate.py (Windows, candidate-scoped) with a fast check
that runs on any OS: credential markers, private paths and secret-bearing file
names anywhere in the repository, including inside committed ZIP archives.
With --history it scans every file version reachable from HEAD, so a secret
committed and later deleted is still found. Bounded pattern scan, not an
exhaustive secret audit.
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
    "test payment key": r"\b[rs]k_test_[0-9A-Za-z]{20,}",
    "JSON web token": r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "Azure storage key": r"(?i)\bAccountKey=[A-Za-z0-9+/]{40,}",
    "credential in URL": r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:@'\"<>]+:[^\s/@'\"<>{$%]{6,}@",
    "credential assignment": r"(?im)^\s*(?:export\s+)?(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|[a-z0-9_]*_(?:secret|token|password|api_key))\s*[:=]\s*['\"]?[^\s'\"<{$]{8,}",
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
    return scan_name(label) + scan_content(label, raw)


def scan_content(label, raw):
    if label.lower().endswith(".zip"):
        return scan_archive(label, raw)
    try:
        text = raw.decode("utf8")
    except UnicodeDecodeError:
        return []  # Binary payloads are out of scope for this text scan.
    return scan_text(label, text)


def scan_archive(label, raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            if len(infos) > MAX_ARCHIVE_MEMBERS or sum(i.file_size for i in infos) > MAX_ARCHIVE_BYTES:
                return [{"path": label, "marker": "archive exceeds scan bounds"}]
            findings = []
            for info in infos:
                # Check the member's own basename before adding its display prefix.
                findings += [dict(f, path=label + "!" + f["path"])
                             for f in scan_bytes(info.filename, z.read(info))]
            return findings
    except zipfile.BadZipFile:
        return [{"path": label, "marker": "unreadable archive"}]


def tracked_files(root):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf8").split("\0") if p]


def history_blobs(root):
    """Yield (paths, short SHA, bytes), reading each reachable blob once.

    Raw, NUL-delimited diffs retain every blob/path association, including
    deleted names, merge parents and renames (represented as delete/add).
    rev-list --objects supplies only one name for a shared object.
    """
    listing = subprocess.run(
        ["git", "log", "--format=", "--raw", "-r", "-z", "--no-abbrev",
         "--no-renames", "--root", "-m", "HEAD"], cwd=root,
        capture_output=True, check=True).stdout.split(b"\0")
    paths = {}
    for index in range(0, len(listing) - 1, 2):
        old_mode, new_mode, old_sha, new_sha, _ = listing[index].lstrip(b"\n:").split()
        rel = listing[index + 1].decode("utf8", errors="surrogateescape")
        for mode, sha in ((old_mode, old_sha), (new_mode, new_sha)):
            # Regular files and symlinks are blobs; gitlinks are commits.
            if mode.startswith((b"100", b"120")):
                paths.setdefault(sha.decode("ascii"), {})[rel] = None
    # Keep one blob's bytes at a time, rather than buffering all payloads.
    with subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as batch:
        for sha in paths:
            batch.stdin.write((sha + "\n").encode("ascii"))
            batch.stdin.flush()
            header = batch.stdout.readline().split()
            if len(header) != 3 or header[:2] != [sha.encode("ascii"), b"blob"]:
                raise ValueError("Unexpected Git blob response")
            size = int(header[2])
            raw = batch.stdout.read(size)
            if len(raw) != size or batch.stdout.read(1) != b"\n":
                raise ValueError("Incomplete Git blob response")
            yield list(paths[sha]), sha[:12], raw
        batch.stdin.close()
        if batch.wait():
            raise subprocess.CalledProcessError(batch.returncode, batch.args)


def is_shallow(root):
    out = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=root, capture_output=True, check=True)
    return out.stdout.strip() == b"true"


def exempt(rel, finding):
    return rel in PATTERN_SOURCES and finding["marker"] in PATTERN_SOURCE_MARKERS


def scan_history(root=ROOT):
    findings, count = [], 0
    for paths, short, raw in history_blobs(root):
        count += 1
        content = {}
        for rel in paths:
            findings += [dict(f, blob=short) for f in scan_name(rel)]
            # A blob can occur under both ZIP and ordinary names. Scan each
            # interpretation once, then apply labels and exemptions per path.
            archive = rel.lower().endswith(".zip")
            if archive not in content:
                content[archive] = (rel, scan_content(rel, raw))
            source, matches = content[archive]
            for match in matches:
                finding = dict(match, path=rel + match["path"][len(source):], blob=short)
                if not exempt(rel, finding):
                    findings.append(finding)
    return {"blobs_scanned": count, "shallow": is_shallow(root), "findings": findings,
            "limit": "Bounded marker/name scan of every blob/path association reachable from HEAD, "
                     "not an exhaustive secret audit; a shallow clone covers only its fetched history"}


def scan(root=ROOT, paths=None):
    paths = tracked_files(root) if paths is None else paths
    findings = []
    for rel in paths:
        path = root / rel
        if path.is_file():
            findings += [f for f in scan_bytes(rel, path.read_bytes()) if not exempt(rel, f)]
    return {"files_scanned": len(paths), "findings": findings,
            "limit": "Bounded marker/name scan of tracked files and ZIP members, not an exhaustive secret audit"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="Repository-relative files (default: all tracked files)")
    parser.add_argument("--history", action="store_true", help="Scan every file version reachable from HEAD")
    args = parser.parse_args()
    if args.history and args.paths:
        parser.error("--history scans all reachable history; it takes no paths")
    result = scan_history() if args.history else scan(paths=args.paths or None)
    print(json.dumps(result, indent=2))
    sys.exit(1 if result["findings"] else 0)
