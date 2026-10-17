#!/usr/bin/env python3
"""Deterministic Agentic Librarian command-line boundary."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


IMPLEMENTATION_VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(IMPLEMENTATION_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPLEMENTATION_VAULT_ROOT))

from kernel.artifact_ledger import (  # noqa: E402
    ARTIFACT_KNOWLEDGE_PROPOSAL_APPLIED,
    ARTIFACT_KNOWLEDGE_PROPOSAL_CREATED,
    ARTIFACT_KNOWLEDGE_PROPOSAL_REJECTED,
    ARTIFACT_KNOWLEDGE_PROPOSAL_VERIFIED,
    ARTIFACT_KNOWLEDGE_CONTRADICTION_RESOLVED,
    ARTIFACT_KNOWLEDGE_ROLLBACK,
    ARTIFACT_KNOWLEDGE_SOURCE_INGESTED,
    ARTIFACT_KNOWLEDGE_OWNER_DECISION,
    ArtifactLedger,
    ArtifactLedgerError,
)


SOURCE_ID_RE = re.compile(r"^SRC-(\d{4})-(\d{6})$")
PROPOSAL_ID_RE = re.compile(r"^PROP-(\d{4})-(\d{6})$")
SYSTEM_RELATIVE = Path("00_SYSTEM") / "AGENTIC_LIBRARIAN"
ALLOWED_GOLD_ROOTS = {
    "00_SYSTEM",
    "01_PROJECTS",
    "04_ACTIVE_PROJECTS",
    "04_RESEARCH",
    "05_TEMPLATES",
    "08_TEMPLATES",
    "Agentic_OS",
    "docs",
    "kernel",
}
PROTECTED_TARGETS = {
    "00_SYSTEM/CANONICAL_VAULT_ROOT.md",
    "00_SYSTEM/GIT_BASELINE_MANIFEST.md",
    "00_SYSTEM/AGENTIC_OS_RISK_REGISTER.md",
}
ALLOWED_PROPOSAL_STATUSES = {
    "pending",
    "approved",
    "rejected",
    "needs_revision",
    "deferred",
    "applied",
    "rolled_back",
}
VERIFICATION_FINGERPRINT_EXCLUDED_FIELDS = {
    "status",
    "owner_decision",
    "owner_decision_by",
    "owner_decision_at",
    "owner_notes",
    "verification_fingerprint",
    "review_body_sha256",
    "applied_at",
    "applied_sha256",
    "checkpoint_head",
    "backup_path",
    "rolled_back_at",
    "rollback_checkpoint_head",
    "restored_sha256",
    "archived_at",
}
EVIDENCE_CLASSIFICATIONS = {
    "DIRECT_SOURCE_FACT",
    "OWNER_STATEMENT",
    "DETERMINISTIC_RESULT",
    "AGENT_INFERENCE",
    "SPECULATION",
}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
UPDATE_PROPOSAL_TYPES = {
    "UPDATE_KNOWLEDGE",
    "CORRECT_KNOWLEDGE",
    "SUPERSEDE_KNOWLEDGE",
    "ADD_RELATIONSHIP",
    "REMOVE_DEPRECATE_RELATIONSHIP",
    "RECORD_DECISION",
    "UPDATE_PROJECT_STATE",
    "RESOLVE_CONTRADICTION",
    "MERGE_DUPLICATES",
    "ARCHIVE_STALE_KNOWLEDGE",
}


class LibrarianError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def no_alias_path(path: Path) -> Path:
    """Inspect lexical ancestors before resolving; reject Windows reparse aliases.

    This is a same-user integrity guard, not isolation against hostile concurrent
    filesystem replacement. File hardlinks are rejected at evidence boundaries.
    """
    path = Path(path)
    if ".." in path.parts:
        raise LibrarianError("illegal_path", "Parent traversal is not permitted")
    absolute = path.absolute()
    for entry in reversed((absolute, *absolute.parents)):
        try:
            info = entry.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise LibrarianError("aliased_path", f"Aliases and reparse points are forbidden: {entry}")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise LibrarianError("aliased_path", f"Hardlinked files are forbidden: {entry}")
    return absolute.resolve()


def require_store_integrity(vault_root: Path) -> None:
    root = no_alias_path(vault_root / SYSTEM_RELATIVE)
    if not root.exists():
        return
    def walk(directory: Path) -> None:
        for entry in directory.iterdir():
            checked = no_alias_path(entry)
            if checked.is_dir():
                walk(checked)
            elif not checked.is_file():
                raise LibrarianError("illegal_path", f"Store entries must be ordinary files/directories: {entry}")
    walk(root)


def input_path(vault_root: Path, value: str) -> Path:
    lexical = Path(value).absolute()
    resolved = no_alias_path(Path(value))
    for candidate in (lexical, resolved):
        try:
            relative = candidate.relative_to(no_alias_path(vault_root)).as_posix().casefold()
        except ValueError:
            continue
        if relative in {item.casefold() for item in PROTECTED_TARGETS}:
            raise LibrarianError("protected_target", "Protected governance files cannot be imported")
    return resolved


def sha256_file(path: Path) -> str:
    path = no_alias_path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def emit(value: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return code


def system_dir(vault_root: Path) -> Path:
    return no_alias_path(vault_root / SYSTEM_RELATIVE)


def ledger(vault_root: Path) -> ArtifactLedger:
    directory = no_alias_path(system_dir(vault_root) / "ledger")
    no_alias_path(directory / "artifact_ledger.jsonl")
    return ArtifactLedger(directory)


def append_event(
    vault_root: Path,
    artifact_type: str,
    run_id: str,
    **payload: Any,
) -> dict[str, Any]:
    try:
        return ledger(vault_root).append(
            artifact_type,
            {"run_id": run_id, **payload},
        )
    except ArtifactLedgerError as exc:
        raise LibrarianError("ledger_error", str(exc)) from exc


def next_id(existing: list[str], pattern: re.Pattern[str], prefix: str) -> str:
    year = datetime.now(timezone.utc).year
    highest = 0
    for candidate in existing:
        match = pattern.fullmatch(candidate)
        if match and int(match.group(1)) == year:
            highest = max(highest, int(match.group(2)))
    return f"{prefix}-{year}-{highest + 1:06d}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    path = no_alias_path(path)
    if not path.exists():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LibrarianError("invalid_registry", f"Invalid JSONL at {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise LibrarianError("invalid_registry", f"Registry row at {path}:{line_number} is not an object")
        rows.append(row)
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path = no_alias_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(row) + "\n")


def validate_schema(name: str, value: dict[str, Any]) -> None:
    schema_path = no_alias_path(IMPLEMENTATION_VAULT_ROOT / SYSTEM_RELATIVE / "schemas" / f"{name}.schema.json")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LibrarianError("schema_unavailable", f"Cannot load {name} schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise LibrarianError("schema_invalid", f"{name} {location}: {first.message}")


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "source.bin"


def copy_new_file(source: Path, destination: Path) -> None:
    """Interrupted, unregistered evidence still belongs to its prior capture.

    Exclusive creation prevents ingest/propose from reusing that identity. Only
    a partial file created by this invocation may be removed on copy failure.
    """
    source, destination = no_alias_path(source), no_alias_path(destination)
    if destination.exists():
        raise LibrarianError("artifact_already_exists", "Preserve the existing capture/payload; inspect interrupted evidence")
    owned = False
    try:
        with source.open("rb") as incoming:
            try:
                outgoing = destination.open("xb")
            except FileExistsError as exc:
                raise LibrarianError("artifact_already_exists", "Capture/payload destination already exists") from exc
            owned = True
            with outgoing:
                shutil.copyfileobj(incoming, outgoing)
    except BaseException:
        if owned:
            no_alias_path(destination).unlink(missing_ok=True)
        raise


def ingest(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    require_store_integrity(vault_root)
    source = input_path(vault_root, args.source)
    if not source.is_file():
        raise LibrarianError("source_not_found", f"Source file does not exist: {source}")

    root = system_dir(vault_root)
    registry = root / "bronze" / "source_registry.jsonl"
    rows = read_jsonl(registry)
    source_id = next_id(
        [str(row.get("source_id", "")) for row in rows], SOURCE_ID_RE, "SRC"
    )
    destination = root / "bronze" / "sources" / f"{source_id}__{safe_name(source.name)}"
    imported_at = utc_now()
    row = {
        "source_id": source_id,
        "title": args.title or source.stem,
        "source_type": args.source_type,
        "original_uri": str(source),
        "imported_at": imported_at,
        "captured_at": args.captured_at or imported_at,
        "project": args.project,
        "content_sha256": sha256_file(source),
        "source_author": args.source_author,
        "original_modified_at": datetime.fromtimestamp(
            source.stat().st_mtime, tz=timezone.utc
        ).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "ingestion_method": "librarian_cli_copy",
        "originating_agent": args.originating_agent,
        "source_reliability": args.source_reliability,
        "supersedes": args.supersedes,
        "superseded_by": None,
        "tags": args.tag,
        "stored_path": destination.relative_to(vault_root).as_posix(),
    }
    validate_schema("source", row)
    resolved_destination = resolve_artifact_path(
        vault_root,
        row["stored_path"],
        SYSTEM_RELATIVE / "bronze" / "sources",
        field_name="stored_path",
    )
    resolved_destination.parent.mkdir(parents=True, exist_ok=True)
    copy_new_file(source, resolved_destination)
    if sha256_file(resolved_destination) != row["content_sha256"]:
        resolved_destination.unlink(missing_ok=True)
        raise LibrarianError("source_copy_mismatch", "Bronze copy did not match the source hash")
    append_jsonl(registry, row)
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_SOURCE_INGESTED,
        source_id,
        project=args.project,
        source_id=source_id,
        stored_path=row["stored_path"],
        content_sha256=row["content_sha256"],
    )
    return row


def proposal_path(vault_root: Path, proposal_id: str) -> Path:
    if not isinstance(proposal_id, str) or not PROPOSAL_ID_RE.fullmatch(proposal_id):
        raise LibrarianError("invalid_proposal_id", f"Invalid proposal ID: {proposal_id!r}")
    directory = no_alias_path(system_dir(vault_root) / "silver" / "proposals")
    path = no_alias_path(directory / f"{proposal_id}.md")
    if path.parent != directory:
        raise LibrarianError("illegal_path", "Proposal path must remain directly under Silver proposals")
    return path


def write_proposal(path: Path, metadata: dict[str, Any], body: str) -> None:
    path = no_alias_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8", newline="")


def read_proposal(path: Path) -> tuple[dict[str, Any], str]:
    path = no_alias_path(path)
    with path.open(encoding="utf-8", newline="") as handle:
        text = handle.read()
    opening, separator = (5, "\r\n---\r\n") if text.startswith("---\r\n") else (4, "\n---\n")
    if not text.startswith(("---\n", "---\r\n")) or separator not in text[opening:]:
        raise LibrarianError("invalid_proposal", f"Proposal has invalid frontmatter: {path}")
    frontmatter, body = text[opening:].split(separator, 1)
    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        raise LibrarianError("invalid_proposal", f"Proposal frontmatter is not an object: {path}")
    return metadata, body


def proposal_inventory(vault_root: Path) -> list[dict[str, Any]]:
    require_store_integrity(vault_root)
    directory = no_alias_path(system_dir(vault_root) / "silver" / "proposals")
    proposals: list[dict[str, Any]] = []
    if not directory.exists():
        return proposals
    seen: set[str] = set()
    for path in sorted(directory.glob("PROP-*.md")):
        metadata, _ = read_proposal(path)
        proposal_id = metadata.get("proposal_id")
        if proposal_id != path.stem or not isinstance(proposal_id, str):
            raise LibrarianError("invalid_proposal_id", f"Proposal ID does not match filename: {path.name}")
        if proposal_id in seen:
            raise LibrarianError("duplicate_proposal_id", f"Duplicate proposal ID: {proposal_id}")
        seen.add(proposal_id)
        proposals.append({**metadata, "proposal_path": path.relative_to(vault_root).as_posix()})
    return proposals


def require_proposal_inventory_integrity(vault_root: Path) -> None:
    proposal_inventory(vault_root)


def propose(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    require_store_integrity(vault_root)
    root = system_dir(vault_root)
    proposal_dir = root / "silver" / "proposals"
    existing = [path.stem for path in proposal_dir.glob("PROP-*.md")] if proposal_dir.exists() else []
    proposal_id = next_id(existing, PROPOSAL_ID_RE, "PROP")

    proposed_file = input_path(vault_root, args.proposed_file)
    if not proposed_file.is_file():
        raise LibrarianError("proposed_content_missing", f"Proposed content does not exist: {proposed_file}")
    payload_path = root / "silver" / "payloads" / f"{proposal_id}{proposed_file.suffix or '.txt'}"
    payload_relative_value = payload_path.relative_to(vault_root).as_posix()
    resolved_payload_path = resolve_artifact_path(
        vault_root,
        payload_relative_value,
        SYSTEM_RELATIVE / "silver" / "payloads",
        field_name="proposed_content_path",
    )
    resolved_payload_path.parent.mkdir(parents=True, exist_ok=True)
    copy_new_file(proposed_file, resolved_payload_path)

    computed_risk = compute_risk(args.proposal_type, args.target, bool(args.contradiction))
    effective_risk = max((args.risk, computed_risk), key=lambda value: RISK_ORDER[value])
    metadata = {
        "proposal_id": proposal_id,
        "status": "pending",
        "proposal_type": args.proposal_type,
        "project": args.project,
        "knowledge_type": args.knowledge_type,
        "risk": args.risk,
        "computed_risk": computed_risk,
        "effective_risk": effective_risk,
        "confidence": args.confidence,
        "created_at": utc_now(),
        "created_by": args.created_by,
        "target_path": args.target.replace("\\", "/"),
        "target_note": Path(args.target).name,
        "target_sha256": None,
        "source_ids": args.source_id,
        "evidence_classification": args.evidence_classification,
        "contradiction_detected": bool(args.contradiction),
        "verification_status": "pending",
        "owner_decision": "pending",
        "owner_decision_by": None,
        "owner_decision_at": None,
        "applied_at": None,
        "supersedes": args.supersedes,
        "proposed_content_path": payload_relative_value,
        "proposed_content_sha256": sha256_file(resolved_payload_path),
        "title": args.title,
        "summary": args.summary,
        "project_path": args.project_path,
    }
    body = (
        f"# {args.title}\n\n"
        f"## EXECUTIVE SUMMARY\n\n{args.summary}\n\n"
        "## WHY THIS IS BEING PROPOSED\n\nCandidate knowledge requires owner review before canonical write.\n\n"
        "## CURRENT CANONICAL STATE\n\nCaptured deterministically during verification.\n\n"
        "## PROPOSED STATE\n\nSee the immutable proposed-content payload referenced in frontmatter.\n\n"
        "## DIFF\n\nGenerated during verification when the target exists.\n\n"
        "## SOURCE EVIDENCE\n\n"
        + "\n".join(f"- `{source_id}`" for source_id in args.source_id)
        + "\n\n## CONTRADICTIONS / CONCERNS\n\n"
        + ("Contradiction review is required.\n" if args.contradiction else "None declared.\n")
        + "\n## DETERMINISTIC CHECKS\n\n- [ ] Run `librarian verify` before decision or apply.\n"
        "\n## LIBRARIAN RECOMMENDATION\n\nPending deterministic verification. Recommendation is advisory only.\n"
        "\n## OWNER DECISION\n\nEdit only the owner-controlled frontmatter fields in Obsidian. Agents must not set them.\n"
        "\n## OWNER NOTES\n\n"
    )
    path = proposal_path(vault_root, proposal_id)
    validate_schema("proposal", metadata)
    write_proposal(path, metadata, body)
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_PROPOSAL_CREATED,
        proposal_id,
        project=args.project,
        proposal_id=proposal_id,
        source_ids=args.source_id,
        target=metadata["target_path"],
        status="pending",
    )
    return {
        "proposal_id": proposal_id,
        "status": "pending",
        "proposal_path": path.relative_to(vault_root).as_posix(),
    }


def compute_risk(proposal_type: str, target: str, contradiction: bool) -> str:
    normalized = target.replace("\\", "/").lower()
    if contradiction or proposal_type in {
        "SUPERSEDE_KNOWLEDGE",
        "RESOLVE_CONTRADICTION",
        "ARCHIVE_STALE_KNOWLEDGE",
        "REMOVE_DEPRECATE_RELATIONSHIP",
    }:
        return "high"
    if normalized.startswith("00_system/") or normalized.startswith("kernel/"):
        return "high"
    if any(token in normalized for token in ("security", "financial", "production", "deploy", "decision")):
        return "high"
    if proposal_type in UPDATE_PROPOSAL_TYPES:
        return "medium"
    return "low"


def source_rows_by_id(vault_root: Path) -> dict[str, dict[str, Any]]:
    registry = system_dir(vault_root) / "bronze" / "source_registry.jsonl"
    rows = read_jsonl(registry)
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        validate_schema("source", row)
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            raise LibrarianError("invalid_source_id", f"Invalid source ID in registry: {source_id!r}")
        if source_id in by_id:
            raise LibrarianError("duplicate_source_id", f"Duplicate source ID: {source_id}")
        by_id[source_id] = row
    return by_id


def safe_relative_path(relative: str, *, field_name: str) -> Path:
    normalized = relative.replace("\\", "/")
    candidate = Path(normalized)
    if (candidate.is_absolute() or candidate.drive or not normalized
            or any(part in {"", ".", ".."} or ":" in part or part.endswith((".", " "))
                   or getattr(os.path, "isreserved", lambda value: False)(part)
                   for part in normalized.split("/"))):
        raise LibrarianError("illegal_path", f"{field_name} must be a clean vault-relative path")
    return candidate


def safe_artifact_path(relative: str, expected_subtree: Path, *, field_name: str) -> Path:
    candidate = safe_relative_path(relative, field_name=field_name)
    expected_parts = expected_subtree.parts
    if candidate.parts[: len(expected_parts)] != expected_parts or len(candidate.parts) <= len(expected_parts):
        raise LibrarianError(
            "artifact_path_outside_subtree",
            f"{field_name} must stay under {expected_subtree.as_posix()}",
        )
    return candidate


def resolve_artifact_path(
    vault_root: Path,
    relative: str,
    expected_subtree: Path,
    *,
    field_name: str,
) -> Path:
    candidate = safe_artifact_path(relative, expected_subtree, field_name=field_name)
    expected_root = no_alias_path(vault_root / expected_subtree)
    resolved = no_alias_path(vault_root / candidate)
    if expected_root != resolved and expected_root not in resolved.parents:
        raise LibrarianError(
            "artifact_path_outside_subtree",
            f"{field_name} resolves outside {expected_subtree.as_posix()}",
        )
    return resolved


def parse_timestamp(value: Any, *, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LibrarianError("invalid_timestamp", f"{field_name} must be a UTC ISO-8601 timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LibrarianError("invalid_timestamp", f"{field_name} is invalid") from exc


def target_path(vault_root: Path, metadata: dict[str, Any]) -> Path:
    relative = safe_relative_path(str(metadata.get("target_path", "")), field_name="target_path")
    posix = relative.as_posix()
    if relative.parts[0] not in ALLOWED_GOLD_ROOTS:
        raise LibrarianError("target_not_allowed", f"Target root is not approved for Gold writes: {posix}")
    if posix.casefold() in {item.casefold() for item in PROTECTED_TARGETS}:
        raise LibrarianError("protected_target", f"Target is protected from proposal apply: {posix}")
    if relative.suffix.lower() != ".md":
        raise LibrarianError("target_not_allowed", "V1 Gold targets must be Markdown notes")
    resolved = no_alias_path(vault_root / relative)
    try:
        actual_relative = resolved.relative_to(no_alias_path(vault_root))
    except ValueError as exc:
        raise LibrarianError("illegal_path", f"Target escapes vault root: {posix}") from exc
    if actual_relative.as_posix().casefold() in {item.casefold() for item in PROTECTED_TARGETS}:
        raise LibrarianError("protected_target", "Resolved target is protected")
    if actual_relative.parts[0] not in ALLOWED_GOLD_ROOTS:
        raise LibrarianError("target_not_allowed", "Resolved target root is not approved")
    if system_dir(vault_root).resolve() == resolved or system_dir(vault_root).resolve() in resolved.parents:
        raise LibrarianError("target_not_allowed", "Librarian governance files cannot be Gold targets")
    project_path_value = metadata.get("project_path")
    if relative.parts[0] in {"01_PROJECTS", "04_ACTIVE_PROJECTS"} and not project_path_value:
        raise LibrarianError("project_scope_required", "Project Gold targets require an explicit project_path")
    if project_path_value:
        project_relative = safe_relative_path(str(project_path_value), field_name="project_path")
        project_root = no_alias_path(vault_root / project_relative)
        if project_root != resolved and project_root not in resolved.parents:
            raise LibrarianError("project_scope_mismatch", "Target is outside the proposal's declared project path")
        if project_relative.parts[0] in {"01_PROJECTS", "04_ACTIVE_PROJECTS"}:
            declared = re.sub(r"[^a-z0-9]", "", str(metadata.get("project", "")).lower())
            scoped = re.sub(r"[^a-z0-9]", "", project_relative.name.lower())
            if declared != scoped:
                raise LibrarianError("project_scope_mismatch", "Project name does not match project_path")
    return resolved


def validate_proposal(
    vault_root: Path,
    metadata: dict[str, Any],
    *,
    target_mode: str = "pre_apply",
) -> dict[str, Any]:
    validate_schema("proposal", {key: value for key, value in metadata.items() if key != "proposal_path"})
    proposal_id = metadata.get("proposal_id")
    if not isinstance(proposal_id, str) or not PROPOSAL_ID_RE.fullmatch(proposal_id):
        raise LibrarianError("invalid_proposal_id", f"Invalid proposal ID: {proposal_id!r}")

    sources = source_rows_by_id(vault_root)
    source_ids = metadata.get("source_ids")
    if not isinstance(source_ids, list) or not source_ids:
        raise LibrarianError("missing_source", "Evidence-dependent proposals require source IDs")
    for source_id in source_ids:
        if source_id not in sources:
            raise LibrarianError("missing_source", f"Referenced source does not exist: {source_id}")
        source_row = sources[source_id]
        stored_path = resolve_artifact_path(
            vault_root,
            source_row["stored_path"],
            SYSTEM_RELATIVE / "bronze" / "sources",
            field_name="stored_path",
        )
        if not stored_path.is_file():
            raise LibrarianError("missing_source", f"Stored Bronze source is missing: {source_id}")
        if sha256_file(stored_path) != source_row.get("content_sha256"):
            raise LibrarianError("source_hash_mismatch", f"Bronze source hash changed: {source_id}")

    payload_relative = safe_artifact_path(
        str(metadata.get("proposed_content_path", "")),
        SYSTEM_RELATIVE / "silver" / "payloads",
        field_name="proposed_content_path",
    )
    payload = resolve_artifact_path(
        vault_root,
        str(metadata.get("proposed_content_path", "")),
        SYSTEM_RELATIVE / "silver" / "payloads",
        field_name="proposed_content_path",
    )
    if not payload.is_file():
        raise LibrarianError("proposed_content_missing", f"Proposed payload is missing: {payload_relative}")
    if sha256_file(payload) != metadata.get("proposed_content_sha256"):
        raise LibrarianError("proposed_content_hash_mismatch", "Proposed payload hash changed")

    target = target_path(vault_root, metadata)
    proposal_type = metadata.get("proposal_type")
    target_hash = sha256_file(target) if target.is_file() else None
    recorded_hash = metadata.get("target_sha256")
    if target_mode == "pre_apply":
        if proposal_type == "CREATE_KNOWLEDGE" and target.exists():
            raise LibrarianError("target_exists", "CREATE_KNOWLEDGE target already exists")
        if proposal_type != "CREATE_KNOWLEDGE" and not target.is_file():
            raise LibrarianError("target_missing", "Update proposal target does not exist")
        if recorded_hash is not None and recorded_hash != target_hash:
            raise LibrarianError("stale_target", "Canonical target changed after proposal verification")
        fingerprint_target_hash = target_hash
    elif target_mode == "verified_snapshot":
        fingerprint_target_hash = recorded_hash
    else:
        raise LibrarianError("invalid_target_mode", target_mode)

    return {
        "proposal_id": proposal_id,
        "target": target,
        "target_sha256": fingerprint_target_hash,
        "current_target_sha256": target_hash,
        "payload": payload,
    }


def compute_verification_fingerprint(
    vault_root: Path,
    metadata: dict[str, Any],
    body: str,
    validated: dict[str, Any],
) -> tuple[str, str]:
    sources = source_rows_by_id(vault_root)
    source_snapshot = [sources[source_id] for source_id in metadata["source_ids"]]
    metadata_snapshot = {
        key: value
        for key, value in metadata.items()
        if key not in VERIFICATION_FINGERPRINT_EXCLUDED_FIELDS and key != "proposal_path"
    }
    review_body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    snapshot = {
        "metadata": metadata_snapshot,
        "sources": source_snapshot,
        "payload_actual_sha256": sha256_file(validated["payload"]),
        "target_actual_sha256": validated["target_sha256"],
        "review_body_sha256": review_body_sha256,
        "diff_actual_sha256": sha256_file(resolve_artifact_path(
            vault_root, str(metadata.get("diff_path", "")), SYSTEM_RELATIVE / "silver" / "diffs",
            field_name="diff_path")),
    }
    fingerprint = hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()
    return fingerprint, review_body_sha256


def require_current_verification_fingerprint(
    vault_root: Path,
    metadata: dict[str, Any],
    body: str,
    validated: dict[str, Any],
) -> None:
    expected, body_hash = compute_verification_fingerprint(vault_root, metadata, body, validated)
    if metadata.get("review_body_sha256") != body_hash or metadata.get("verification_fingerprint") != expected:
        raise LibrarianError(
            "stale_verification",
            "Proposal, evidence, target, payload, or rendered review changed after verification",
        )


def clipped_text(path: Path | None, limit: int | None = None) -> str:
    if path is None or not path.is_file():
        return "(target does not exist; this is a create proposal)"
    path = no_alias_path(path)
    if limit is None and path.stat().st_size > 2 * 1024 * 1024:
        raise LibrarianError("review_content_too_large", "Complete Gold/Silver review requires files at most 2 MiB")
    try:
        with path.open(encoding="utf-8", errors="strict" if limit is None else "replace", newline="") as handle:
            text = handle.read()
    except UnicodeDecodeError as exc:
        raise LibrarianError("review_content_not_utf8", "Complete review requires valid UTF-8") from exc
    if limit is None or len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[review preview truncated; full file: {path.name}]"


def render_verified_body(
    vault_root: Path,
    metadata: dict[str, Any],
    validated: dict[str, Any],
) -> str:
    target = validated["target"]
    payload = validated["payload"]
    current_text = clipped_text(target if target.is_file() else None)
    proposed_text = clipped_text(payload)
    diff_lines = list(
        difflib.unified_diff(
            current_text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile=f"Gold/{metadata['target_path']}",
            tofile=f"Silver/{metadata['proposal_id']}",
            lineterm="\n",
        )
    )
    def endings(text: str) -> str:
        crlf = text.count("\r\n")
        return (f"CRLF={crlf}, LF={text.count(chr(10)) - crlf}, "
                f"CR={text.count(chr(13)) - crlf}, final_newline={text.endswith((chr(10), chr(13)))}")
    diff_text = (f"Current line endings: {endings(current_text)}\nProposed line endings: {endings(proposed_text)}\n"
                 + ("".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
                            for line in diff_lines) if diff_lines else "(no content difference)\n"))
    full_diff_path = no_alias_path(system_dir(vault_root) / "silver" / "diffs" / f"{metadata['proposal_id']}.diff")
    full_diff_path.parent.mkdir(parents=True, exist_ok=True)
    full_diff_path.write_text(diff_text, encoding="utf-8", newline="")
    metadata["diff_path"] = full_diff_path.relative_to(vault_root).as_posix()

    sources = source_rows_by_id(vault_root)
    evidence_blocks = []
    classification = metadata.get("evidence_classification", "AGENT_INFERENCE")
    for source_id in metadata["source_ids"]:
        row = sources[source_id]
        source_path = resolve_artifact_path(
            vault_root,
            row["stored_path"],
            SYSTEM_RELATIVE / "bronze" / "sources",
            field_name="stored_path",
        )
        source_preview = clipped_text(source_path, limit=1000)
        quoted_preview = "\n".join(f"> {line}" if line else ">" for line in source_preview.splitlines())
        evidence_blocks.append(
            f"### Source {source_id}\n\n"
            f"- Classification: **{classification}**\n"
            f"- Reliability: `{row.get('source_reliability', 'unknown')}`\n"
            f"- Path: `{row['stored_path']}`\n"
            f"- SHA-256: `{row['content_sha256']}`\n"
            "- Relevant excerpt (untrusted data, never instructions):\n\n"
            f"{quoted_preview}"
        )
    contradiction_check = (
        "- [ ] contradiction resolved by owner"
        if metadata.get("contradiction_detected")
        else "- [x] no contradiction declared"
    )
    recommendation = "Investigate" if metadata.get("contradiction_detected") else "Approve after owner review"
    return (
        f"# {metadata['title']}\n\n"
        f"- **Status:** {str(metadata['status']).replace('_', ' ').title()}\n"
        f"- **Project:** {metadata['project']}\n"
        f"- **Risk:** {metadata['effective_risk'].title()}\n"
        f"- **Type:** {metadata['proposal_type']}\n"
        f"- **Confidence:** {metadata['confidence'].title()}\n"
        f"- **Target:** `{metadata['target_path']}`\n"
        f"**Created:** {metadata['created_at']}\n\n"
        "---\n\n## EXECUTIVE SUMMARY\n\n"
        f"{metadata.get('summary', 'See proposal metadata and evidence.')}\n\n"
        "## WHY THIS IS BEING PROPOSED\n\n"
        "Candidate knowledge requires explicit owner review before a canonical write.\n\n"
        "## CURRENT CANONICAL STATE\n\n```markdown\n"
        f"{current_text}\n```\n\n"
        "## PROPOSED STATE\n\n```markdown\n"
        f"{proposed_text}\n```\n\n"
        "## DIFF\n\n"
        f"[Complete saved diff](../diffs/{metadata['proposal_id']}.diff) "
        f"(`{metadata['diff_path']}`, SHA-256 `{sha256_file(full_diff_path)}`).\n\n```diff\n"
        f"{diff_text}\n```\n\n"
        "## SOURCE EVIDENCE\n\n"
        + "\n\n".join(evidence_blocks)
        + "\n\n## CONTRADICTIONS / CONCERNS\n\n"
        + ("Conflict requires an explicit owner resolution.\n" if metadata.get("contradiction_detected") else "None declared.\n")
        + "\n## DETERMINISTIC CHECKS\n\n"
        "- [x] source exists\n"
        "- [x] source hash verified\n"
        "- [x] proposal schema valid\n"
        "- [x] destination allowed\n"
        "- [x] target hash recorded / no stale target\n"
        f"{contradiction_check}\n\n"
        "## LIBRARIAN RECOMMENDATION\n\n"
        f"**Advisory only:** {recommendation}. Confidence never substitutes for owner approval.\n\n"
        "## OWNER DECISION\n\n"
        "Change only the owner-controlled frontmatter fields: `status`, `owner_decision`, "
        "`owner_decision_by`, and `owner_decision_at`. Agents must not set them.\n\n"
        "## OWNER NOTES\n"
    )


def verify_proposal(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    require_proposal_inventory_integrity(vault_root)
    path = proposal_path(vault_root, args.proposal_id)
    if not path.is_file():
        raise LibrarianError("proposal_not_found", f"Proposal does not exist: {args.proposal_id}")
    metadata, body = read_proposal(path)
    if metadata.get("status") != "pending" or metadata.get("owner_decision") != "pending":
        raise LibrarianError(
            "owner_decision_already_set",
            "Verification must complete before the owner records a disposition; create a revision instead",
        )
    try:
        validated = validate_proposal(vault_root, metadata)
    except LibrarianError as exc:
        if exc.code == "stale_target":
            metadata["verification_status"] = "stale_target"
            metadata["verified_at"] = utc_now()
            write_proposal(path, metadata, body)
        append_event(
            vault_root,
            ARTIFACT_KNOWLEDGE_PROPOSAL_VERIFIED,
            args.proposal_id,
            project=metadata.get("project"),
            proposal_id=args.proposal_id,
            target=metadata.get("target_path"),
            verification="failed",
            error_code=exc.code,
        )
        raise
    metadata["target_sha256"] = validated["target_sha256"]
    metadata["verification_status"] = "passed"
    metadata["verified_at"] = utc_now()
    body = render_verified_body(vault_root, metadata, validated)
    fingerprint, body_hash = compute_verification_fingerprint(vault_root, metadata, body, validated)
    metadata["review_body_sha256"] = body_hash
    metadata["verification_fingerprint"] = fingerprint
    validate_schema("proposal", metadata)
    write_proposal(path, metadata, body)
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_PROPOSAL_VERIFIED,
        args.proposal_id,
        project=metadata.get("project"),
        proposal_id=args.proposal_id,
        target=metadata.get("target_path"),
        verification="passed",
    )
    return {
        "proposal_id": args.proposal_id,
        "verification_status": "passed",
        "target_sha256": validated["target_sha256"],
    }


def require_clean_git_checkpoint(vault_root: Path, required_paths: list[Path] | None = None) -> str:
    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(vault_root), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    head = git("rev-parse", "--verify", "HEAD")
    if head.returncode != 0:
        raise LibrarianError("git_checkpoint_required", "A valid local Git HEAD is required before Gold apply")
    status = git("status", "--porcelain")
    if status.returncode != 0 or status.stdout.strip():
        raise LibrarianError("git_worktree_not_clean", "Commit or otherwise resolve the local checkpoint before Gold apply")
    if required_paths:
        top = git("rev-parse", "--show-toplevel")
        if top.returncode != 0:
            raise LibrarianError("git_checkpoint_required", "Cannot identify checkpoint root")
        repository = no_alias_path(Path(top.stdout.strip()))
        for path in required_paths:
            path = no_alias_path(path)
            try:
                relative = path.relative_to(repository).as_posix()
            except ValueError as exc:
                raise LibrarianError("git_evidence_missing", "Evidence is outside the checkpoint repository") from exc
            flags = git("ls-files", "-v", "--", str(path))
            if (flags.returncode != 0 or not flags.stdout.strip()
                    or any(line[0].islower() or line[0] == "S" for line in flags.stdout.splitlines())):
                raise LibrarianError("git_evidence_missing", "Evidence must be tracked without skip/assume flags: " + relative)
            attrs = git("check-attr", "filter", "working-tree-encoding", "--", str(path))
            if attrs.returncode != 0 or any(line.rsplit(": ", 1)[-1] not in {"unspecified", "unset"}
                                           for line in attrs.stdout.splitlines()):
                raise LibrarianError("git_evidence_filtered", "Filtered evidence is not an exact-byte checkpoint: " + relative)
            entry = subprocess.run(["git", "-C", str(repository), "ls-tree", "-z", head.stdout.strip(), "--", relative],
                                   capture_output=True, check=False)
            records = entry.stdout.split(b"\0")
            if (entry.returncode != 0 or len(records) != 2 or not records[0]
                    or records[0].split(b" ", 1)[0] not in {b"100644", b"100755"}):
                raise LibrarianError("git_evidence_missing", "Evidence must exist as an ordinary HEAD blob: " + relative)
            blob = subprocess.run(["git", "-C", str(repository), "cat-file", "blob", head.stdout.strip() + ":" + relative],
                                  capture_output=True, check=False)
            if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != sha256_file(path):
                raise LibrarianError("git_evidence_mismatch", "Checkpoint bytes differ from approved evidence: " + relative)
    return head.stdout.strip()


def checkpoint_evidence(vault_root: Path, metadata: dict[str, Any], target: Path) -> list[Path]:
    paths = [proposal_path(vault_root, metadata["proposal_id"]),
             system_dir(vault_root) / "bronze" / "source_registry.jsonl",
             system_dir(vault_root) / "ledger" / "artifact_ledger.jsonl"]
    rows = source_rows_by_id(vault_root)
    paths.extend(resolve_artifact_path(vault_root, rows[source_id]["stored_path"],
                 SYSTEM_RELATIVE / "bronze" / "sources", field_name="stored_path")
                 for source_id in metadata["source_ids"])
    paths.extend([resolve_artifact_path(vault_root, metadata["proposed_content_path"],
                  SYSTEM_RELATIVE / "silver" / "payloads", field_name="proposed_content_path"),
                  resolve_artifact_path(vault_root, metadata["diff_path"],
                  SYSTEM_RELATIVE / "silver" / "diffs", field_name="diff_path")])
    if target.exists():
        paths.append(target)
    return paths


def temporary_path(target: Path, proposal_id: str) -> Path:
    temporary = no_alias_path(target.with_name(f".{target.name}.{proposal_id}.tmp"))
    if temporary.exists():
        raise LibrarianError("temporary_path_exists", "Refusing a pre-existing application/rollback temporary file")
    return temporary


def apply_proposal(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    require_proposal_inventory_integrity(vault_root)
    path = proposal_path(vault_root, args.proposal_id)
    if not path.is_file():
        raise LibrarianError("proposal_not_found", f"Proposal does not exist: {args.proposal_id}")
    metadata, body = read_proposal(path)
    if metadata.get("status") != "approved" or metadata.get("owner_decision") != "approved":
        raise LibrarianError("proposal_not_approved", "Only an explicitly owner-approved proposal can apply")
    if metadata.get("owner_decision_by") != "owner" or not metadata.get("owner_decision_at"):
        raise LibrarianError("owner_decision_incomplete", "Owner identity and decision timestamp are required")
    if metadata.get("verification_status") != "passed":
        raise LibrarianError("proposal_not_verified", "Proposal must pass deterministic verification before apply")
    verified_at = parse_timestamp(metadata.get("verified_at"), field_name="verified_at")
    owner_decision_at = parse_timestamp(metadata.get("owner_decision_at"), field_name="owner_decision_at")
    if owner_decision_at < verified_at:
        raise LibrarianError(
            "approval_precedes_verification",
            "Owner approval must occur after the current successful verification",
        )

    require_clean_git_checkpoint(vault_root)
    validated = validate_proposal(vault_root, metadata)
    require_current_verification_fingerprint(vault_root, metadata, body, validated)
    target = validated["target"]
    payload = validated["payload"]
    temporary = temporary_path(target, args.proposal_id)
    backup_path = None
    if target.exists():
        backup_path = no_alias_path(system_dir(vault_root) / "backups" / args.proposal_id / target.name)
        if backup_path.exists():
            raise LibrarianError("backup_path_exists", "Preserve existing recovery evidence; create a new proposal")
    checkpoint = require_clean_git_checkpoint(vault_root, checkpoint_evidence(vault_root, metadata, target))
    if args.dry_run:
        return {
            "proposal_id": args.proposal_id,
            "status": "approved",
            "dry_run": True,
            "target": metadata["target_path"],
            "checkpoint_head": checkpoint,
            "would_apply_sha256": metadata["proposed_content_sha256"],
        }
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_OWNER_DECISION,
        args.proposal_id,
        project=metadata.get("project"),
        proposal_id=args.proposal_id,
        decision="approved",
        decision_by="owner",
        decision_at=metadata.get("owner_decision_at"),
    )
    before_proposal = path.read_bytes()
    before_target = target.read_bytes() if target.exists() else None
    if before_target is not None:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with backup_path.open("xb") as handle:
            handle.write(before_target)
            handle.flush()
            os.fsync(handle.fileno())

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_owned = False
    target_replaced = False
    try:
        with temporary.open("xb") as handle:
            temporary_owned = True
            handle.write(payload.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        if sha256_file(temporary) != metadata["proposed_content_sha256"]:
            raise LibrarianError("proposed_content_hash_mismatch", "Payload changed during staging")
        no_alias_path(target)
        os.replace(temporary, target)
        temporary_owned = False
        target_replaced = True
        metadata["status"] = "applied"
        metadata["applied_at"] = utc_now()
        metadata["applied_sha256"] = sha256_file(target)
        metadata["checkpoint_head"] = checkpoint
        metadata["backup_path"] = (
            backup_path.relative_to(vault_root).as_posix() if backup_path else None
        )
        write_proposal(path, metadata, body)
        append_event(
            vault_root,
            ARTIFACT_KNOWLEDGE_PROPOSAL_APPLIED,
            args.proposal_id,
            project=metadata.get("project"),
            proposal_id=args.proposal_id,
            target=metadata.get("target_path"),
            checkpoint_head=checkpoint,
            applied_sha256=metadata["applied_sha256"],
        )
        if metadata.get("proposal_type") == "RESOLVE_CONTRADICTION":
            append_event(
                vault_root,
                ARTIFACT_KNOWLEDGE_CONTRADICTION_RESOLVED,
                args.proposal_id,
                project=metadata.get("project"),
                proposal_id=args.proposal_id,
                target=metadata.get("target_path"),
                decision="approved_and_applied",
            )
    except Exception:
        if temporary_owned:
            no_alias_path(temporary).unlink(missing_ok=True)
        if target_replaced:
            if before_target is None:
                no_alias_path(target).unlink(missing_ok=True)
            else:
                no_alias_path(target).write_bytes(before_target)
            no_alias_path(path).write_bytes(before_proposal)
        raise

    return {
        "proposal_id": args.proposal_id,
        "status": "applied",
        "target": metadata["target_path"],
        "applied_sha256": metadata["applied_sha256"],
        "checkpoint_head": checkpoint,
    }


def rollback_proposal(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    require_proposal_inventory_integrity(vault_root)
    if args.confirm_proposal_id != args.proposal_id:
        raise LibrarianError("rollback_confirmation_required", "Confirmation must exactly match the proposal ID")
    path = proposal_path(vault_root, args.proposal_id)
    if not path.is_file():
        raise LibrarianError("proposal_not_found", f"Proposal does not exist: {args.proposal_id}")
    metadata, body = read_proposal(path)
    if metadata.get("status") != "applied" or not metadata.get("applied_at"):
        raise LibrarianError("proposal_not_applied", "Only an applied proposal can be rolled back")
    require_clean_git_checkpoint(vault_root)
    validated = validate_proposal(vault_root, metadata, target_mode="verified_snapshot")
    require_current_verification_fingerprint(vault_root, metadata, body, validated)
    target = target_path(vault_root, metadata)
    if not target.is_file() or sha256_file(target) != metadata.get("applied_sha256"):
        raise LibrarianError("stale_applied_target", "Applied target changed after proposal apply")

    backup = None
    backup_value = metadata.get("backup_path")
    if metadata.get("target_sha256") is not None:
        expected = SYSTEM_RELATIVE / "backups" / args.proposal_id / target.name
        if not backup_value or str(backup_value) != expected.as_posix():
            raise LibrarianError("rollback_backup_missing", "Original-target recovery requires the exact proposal backup")
        backup = resolve_artifact_path(vault_root, str(backup_value), SYSTEM_RELATIVE / "backups" / args.proposal_id,
                                       field_name="backup_path")
        if not backup.is_file():
            raise LibrarianError("rollback_backup_missing", "Rollback backup is missing")
        if sha256_file(backup) != metadata["target_sha256"]:
            raise LibrarianError("rollback_backup_hash_mismatch", "Rollback backup differs from the verified original target")
    elif backup_value:
        raise LibrarianError("rollback_backup_hash_mismatch", "Create proposals cannot restore an unverified backup")
    temporary = temporary_path(target, args.proposal_id)
    evidence = checkpoint_evidence(vault_root, metadata, target)
    if backup:
        evidence.append(backup)
    checkpoint = require_clean_git_checkpoint(vault_root, evidence)

    if args.dry_run:
        return {
            "proposal_id": args.proposal_id,
            "status": "applied",
            "dry_run": True,
            "target": metadata.get("target_path"),
            "checkpoint_head": checkpoint,
        }

    if backup:
        owned = False
        try:
            with temporary.open("xb") as handle:
                owned = True
                handle.write(backup.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
            if sha256_file(temporary) != metadata["target_sha256"]:
                raise LibrarianError("rollback_backup_hash_mismatch", "Backup changed during rollback staging")
            no_alias_path(target)
            os.replace(temporary, target)
            owned = False
        finally:
            if owned:
                no_alias_path(temporary).unlink(missing_ok=True)
        restored_sha256 = sha256_file(target)
    else:
        target.unlink()
        restored_sha256 = None

    metadata["status"] = "rolled_back"
    metadata["rolled_back_at"] = utc_now()
    metadata["rollback_checkpoint_head"] = checkpoint
    metadata["restored_sha256"] = restored_sha256
    write_proposal(path, metadata, body)
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_ROLLBACK,
        args.proposal_id,
        project=metadata.get("project"),
        proposal_id=args.proposal_id,
        target=metadata.get("target_path"),
        checkpoint_head=checkpoint,
        restored_sha256=restored_sha256,
    )
    return {
        "proposal_id": args.proposal_id,
        "status": "rolled_back",
        "target": metadata.get("target_path"),
        "restored_sha256": restored_sha256,
    }


def archive_proposal(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    require_proposal_inventory_integrity(vault_root)
    path = proposal_path(vault_root, args.proposal_id)
    if not path.is_file():
        raise LibrarianError("proposal_not_found", f"Proposal does not exist: {args.proposal_id}")
    metadata, body = read_proposal(path)
    if metadata.get("status") != "rejected" or metadata.get("owner_decision") != "rejected":
        raise LibrarianError("proposal_not_rejected", "Only an explicitly owner-rejected proposal can be archived")
    if metadata.get("owner_decision_by") != "owner" or not metadata.get("owner_decision_at"):
        raise LibrarianError("owner_decision_incomplete", "Owner identity and decision timestamp are required")
    metadata["archived_at"] = utc_now()
    validate_schema("proposal", metadata)
    write_proposal(path, metadata, body)
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_OWNER_DECISION,
        args.proposal_id,
        project=metadata.get("project"),
        proposal_id=args.proposal_id,
        decision="rejected",
        decision_by="owner",
        decision_at=metadata.get("owner_decision_at"),
    )
    append_event(
        vault_root,
        ARTIFACT_KNOWLEDGE_PROPOSAL_REJECTED,
        args.proposal_id,
        project=metadata.get("project"),
        proposal_id=args.proposal_id,
        target=metadata.get("target_path"),
        owner_decision_at=metadata.get("owner_decision_at"),
        archived_at=metadata["archived_at"],
    )
    return {
        "proposal_id": args.proposal_id,
        "status": "rejected",
        "archived_at": metadata["archived_at"],
        "proposal_path": path.relative_to(vault_root).as_posix(),
    }


def status_projection(vault_root: Path) -> dict[str, Any]:
    proposals = proposal_inventory(vault_root)
    counts = {
        "pending_review": sum(item.get("status") == "pending" for item in proposals),
        "high_risk": sum(
            item.get("effective_risk", item.get("risk")) == "high"
            and item.get("status") in {"pending", "approved", "needs_revision"}
            for item in proposals
        ),
        "contradictions": sum(
            bool(item.get("contradiction_detected")) and item.get("status") not in {"applied", "rejected", "rolled_back"}
            for item in proposals
        ),
        "needs_revision": sum(item.get("status") == "needs_revision" for item in proposals),
        "deferred": sum(item.get("status") == "deferred" for item in proposals),
        "approved_awaiting_apply": sum(item.get("status") == "approved" for item in proposals),
        "recently_applied": sum(item.get("status") == "applied" for item in proposals),
        "recently_rejected": sum(item.get("status") == "rejected" for item in proposals),
        "total": len(proposals),
    }
    ledger_path = system_dir(vault_root) / "ledger" / "artifact_ledger.jsonl"
    events = read_jsonl(ledger_path)
    last_apply = next(
        (event.get("timestamp") for event in reversed(events) if event.get("artifact_type") == ARTIFACT_KNOWLEDGE_PROPOSAL_APPLIED),
        None,
    )
    return {
        "generated_at": utc_now(),
        "counts": counts,
        "last_librarian_run": events[-1].get("timestamp") if events else None,
        "last_gold_apply": last_apply,
        "verification_health": "review doctor output",
    }


def decision_studio_base() -> dict[str, Any]:
    columns = [
        "file.name",
        "status",
        "project",
        "proposal_type",
        "risk",
        "effective_risk",
        "confidence",
        "contradiction_detected",
        "verification_status",
        "target_path",
        "created_at",
    ]
    return {
        "filters": {"and": ['file.inFolder("00_SYSTEM/AGENTIC_LIBRARIAN/silver/proposals")']},
        "properties": {
            "status": {"displayName": "Owner status"},
            "project": {"displayName": "Project"},
            "proposal_type": {"displayName": "Type"},
            "risk": {"displayName": "Risk"},
            "effective_risk": {"displayName": "Effective risk"},
            "confidence": {"displayName": "Confidence"},
            "contradiction_detected": {"displayName": "Contradiction"},
            "verification_status": {"displayName": "Verification"},
            "target_path": {"displayName": "Target"},
            "created_at": {"displayName": "Created"},
        },
        "views": [
            {"type": "table", "name": "INBOX", "filters": {"and": ['status == "pending"']}, "order": list(columns)},
            {
                "type": "table",
                "name": "NEEDS MY ATTENTION",
                "filters": {
                    "and": [
                        {"or": ['effective_risk == "high"', "contradiction_detected == true", 'verification_status == "stale_target"']},
                        {"not": ['status == "applied"', 'status == "rejected"', 'status == "rolled_back"']},
                    ]
                },
                "order": list(columns),
            },
            {"type": "table", "name": "BY PROJECT", "groupBy": {"property": "project", "direction": "ASC"}, "order": list(columns)},
            {"type": "table", "name": "CONTRADICTIONS", "filters": {"and": ["contradiction_detected == true"]}, "order": list(columns)},
            {"type": "table", "name": "APPROVED / READY TO APPLY", "filters": {"and": ['status == "approved"']}, "order": list(columns)},
            {"type": "table", "name": "APPLIED HISTORY", "filters": {"or": ['status == "applied"', 'status == "rolled_back"']}, "order": list(columns)},
            {"type": "table", "name": "REJECTED / LESSONS", "filters": {"and": ['status == "rejected"']}, "order": list(columns)},
        ],
    }


def write_decision_studio(vault_root: Path, projection: dict[str, Any]) -> None:
    require_store_integrity(vault_root)
    root = system_dir(vault_root)
    studio = root / "decision_studio"
    generated = root / "generated"
    studio.mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)
    (studio / "Decision Studio.base").write_text(
        yaml.safe_dump(decision_studio_base(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    counts = projection["counts"]
    (studio / "DECISION_STUDIO.md").write_text(
        "---\ntype: dashboard\nstatus: active\ntags: [agentic-librarian, decision-studio, hitl]\n---\n"
        "# Agentic Librarian - Decision Studio\n\n"
        "> [!warning] Human authority boundary\n"
        "> Silver proposals are not approved facts. Only the owner may change owner-decision fields.\n\n"
        "## What needs a decision\n\n"
        f"- Pending review: **{counts['pending_review']}**\n"
        f"- High risk: **{counts['high_risk']}**\n"
        f"- Contradictions: **{counts['contradictions']}**\n"
        f"- Needs revision: **{counts['needs_revision']}**\n"
        f"- Deferred: **{counts['deferred']}**\n"
        f"- Approved awaiting apply: **{counts['approved_awaiting_apply']}**\n\n"
        "## Inbox\n\n![[Decision Studio.base#INBOX]]\n\n"
        "## Needs my attention\n\n![[Decision Studio.base#NEEDS MY ATTENTION]]\n\n"
        "## By project\n\n![[Decision Studio.base#BY PROJECT]]\n\n"
        "## Contradictions\n\n![[Decision Studio.base#CONTRADICTIONS]]\n\n"
        "## Approved / ready to apply\n\n![[Decision Studio.base#APPROVED / READY TO APPLY]]\n\n"
        "## Applied history\n\n![[Decision Studio.base#APPLIED HISTORY]]\n\n"
        "## Rejected / lessons\n\n![[Decision Studio.base#REJECTED / LESSONS]]\n\n"
        "## Plain-Markdown fallback\n\n"
        "Open `silver/proposals/` and sort by frontmatter `status`, `risk`, `project`, and `created_at`. "
        "Run `librarian status --write` to refresh these generated counts.\n",
        encoding="utf-8",
    )
    (generated / "status.json").write_text(
        json.dumps(projection, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def status_command(vault_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    projection = status_projection(vault_root)
    if args.write:
        write_decision_studio(vault_root, projection)
    return projection


def inbox_command(vault_root: Path, _args: argparse.Namespace) -> dict[str, Any]:
    proposals = [
        item
        for item in proposal_inventory(vault_root)
        if item.get("status") in {"pending", "approved", "needs_revision", "deferred"}
    ]
    proposals.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return {"count": len(proposals), "proposals": proposals}


def doctor_command(vault_root: Path, _args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    checks: list[dict[str, str]] = []

    def record(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    try:
        sources = source_rows_by_id(vault_root)
        for source_id, row in sources.items():
            validate_schema("source", row)
            stored = resolve_artifact_path(
                vault_root,
                row["stored_path"],
                SYSTEM_RELATIVE / "bronze" / "sources",
                field_name="stored_path",
            )
            if not stored.is_file():
                raise LibrarianError("missing_source", source_id)
            if sha256_file(stored) != row.get("content_sha256"):
                raise LibrarianError("source_hash_mismatch", source_id)
        record("bronze_sources", "PASS", f"{len(sources)} source records verified")
    except LibrarianError as exc:
        record("bronze_sources", "FAIL", f"{exc.code}: {exc}")

    try:
        proposals = proposal_inventory(vault_root)
        for item in proposals:
            if item.get("status") not in ALLOWED_PROPOSAL_STATUSES:
                raise LibrarianError("invalid_status", str(item.get("status")))
            mode = (
                "pre_apply"
                if item.get("status") in {"pending", "approved"}
                else "verified_snapshot"
            )
            validated = validate_proposal(vault_root, item, target_mode=mode)
            if item.get("verification_status") == "passed":
                item_path = proposal_path(vault_root, item["proposal_id"])
                item_metadata, item_body = read_proposal(item_path)
                require_current_verification_fingerprint(
                    vault_root, item_metadata, item_body, validated
                )
        record("silver_proposals", "PASS", f"{len(proposals)} proposals verified")
    except LibrarianError as exc:
        record("silver_proposals", "FAIL", f"{exc.code}: {exc}")

    try:
        proposals = proposal_inventory(vault_root)
        for item in proposals:
            target = target_path(vault_root, item)
            current_hash = sha256_file(target) if target.is_file() else None
            status = item.get("status")
            proposal_type = item.get("proposal_type")
            if status in {"pending", "approved"}:
                validate_proposal(vault_root, item, target_mode="pre_apply")
            elif status == "applied":
                if not target.is_file() or current_hash != item.get("applied_sha256"):
                    raise LibrarianError(
                        "applied_target_mismatch", str(item.get("target_path"))
                    )
                if current_hash != item.get("proposed_content_sha256"):
                    raise LibrarianError(
                        "applied_payload_mismatch", str(item.get("target_path"))
                    )
            elif status == "rolled_back":
                if proposal_type == "CREATE_KNOWLEDGE":
                    if target.exists() or item.get("restored_sha256") is not None:
                        raise LibrarianError(
                            "rollback_state_mismatch", str(item.get("target_path"))
                        )
                elif (
                    not target.is_file()
                    or current_hash != item.get("restored_sha256")
                    or current_hash != item.get("target_sha256")
                ):
                    raise LibrarianError(
                        "rollback_state_mismatch", str(item.get("target_path"))
                    )
            else:
                # Rejected/revision/deferred records are historical Silver evidence;
                # their old target snapshot may legitimately drift.
                validate_proposal(vault_root, item, target_mode="verified_snapshot")
        record("gold_targets", "PASS", f"{len(proposals)} declared Gold targets checked")
    except LibrarianError as exc:
        record("gold_targets", "FAIL", f"{exc.code}: {exc}")

    ledger_path = system_dir(vault_root) / "ledger" / "artifact_ledger.jsonl"
    try:
        rows = read_jsonl(ledger_path)
        run_ids = {row.get("run_id") for row in rows}
        for run_id in run_ids:
            if isinstance(run_id, str):
                ledger(vault_root).query(run_id)
        record("artifact_ledger", "PASS", f"{len(rows)} append-only events replay-validated")
    except (LibrarianError, ArtifactLedgerError) as exc:
        record("artifact_ledger", "FAIL", str(exc))

    studio = system_dir(vault_root) / "decision_studio"
    base_path = studio / "Decision Studio.base"
    markdown_path = studio / "DECISION_STUDIO.md"
    if base_path.is_file() and markdown_path.is_file():
        try:
            parsed = yaml.safe_load(base_path.read_text(encoding="utf-8"))
            if not isinstance(parsed, dict) or len(parsed.get("views", [])) < 7:
                raise ValueError("required views missing")
            record("decision_studio", "PASS", "Markdown fallback and seven Bases views exist")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            record("decision_studio", "FAIL", str(exc))
    else:
        record("decision_studio", "WARN", "Run status --write to generate Decision Studio")

    head = subprocess.run(
        ["git", "-C", str(vault_root), "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if head.returncode != 0:
        record("git_recovery", "WARN", "No valid local Git HEAD; Gold apply will fail closed")
    else:
        git_status = subprocess.run(
            ["git", "-C", str(vault_root), "status", "--porcelain"],
            text=True,
            capture_output=True,
            check=False,
        )
        if git_status.returncode != 0:
            record("git_recovery", "FAIL", "Unable to inspect local Git worktree")
        elif git_status.stdout.strip():
            record("git_recovery", "WARN", f"Checkpoint exists at {head.stdout.strip()}, but worktree is dirty")
        else:
            record("git_recovery", "PASS", f"Local checkpoint available at {head.stdout.strip()}")

    if any(check["status"] == "FAIL" for check in checks):
        overall, code = "FAIL", 2
    elif any(check["status"] == "WARN" for check in checks):
        overall, code = "WARN", 1
    else:
        overall, code = "PASS", 0
    return {"status": overall, "checked_at": utc_now(), "checks": checks}, code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="librarian")
    parser.add_argument("--vault-root", required=True)
    commands = parser.add_subparsers(dest="command", required=True)

    ingest_parser = commands.add_parser("ingest")
    ingest_parser.add_argument("source")
    ingest_parser.add_argument("--project", required=True)
    ingest_parser.add_argument("--title")
    ingest_parser.add_argument("--source-type", default="markdown")
    ingest_parser.add_argument("--captured-at")
    ingest_parser.add_argument("--source-author")
    ingest_parser.add_argument("--originating-agent", default="owner_request")
    ingest_parser.add_argument(
        "--source-reliability",
        choices=[
            "owner_statement",
            "primary_source",
            "official_documentation",
            "direct_observation",
            "internal_project_artifact",
            "reputable_secondary",
            "community_report",
            "AI_generated",
            "unknown",
        ],
        default="unknown",
    )
    ingest_parser.add_argument("--supersedes")
    ingest_parser.add_argument("--tag", action="append", default=[])

    propose_parser = commands.add_parser("propose")
    propose_parser.add_argument("--project", required=True)
    propose_parser.add_argument(
        "--proposal-type",
        choices=["CREATE_KNOWLEDGE", *sorted(UPDATE_PROPOSAL_TYPES)],
        required=True,
    )
    propose_parser.add_argument(
        "--knowledge-type",
        choices=["durable_knowledge", "operational_state", "ephemeral_information"],
        default="durable_knowledge",
    )
    propose_parser.add_argument("--risk", choices=["low", "medium", "high"], required=True)
    propose_parser.add_argument("--confidence", choices=["low", "medium", "high"], required=True)
    propose_parser.add_argument(
        "--evidence-classification",
        choices=sorted(EVIDENCE_CLASSIFICATIONS),
        default="AGENT_INFERENCE",
    )
    propose_parser.add_argument("--title", required=True)
    propose_parser.add_argument("--summary", required=True)
    propose_parser.add_argument("--target", required=True)
    propose_parser.add_argument("--source-id", action="append", required=True)
    propose_parser.add_argument("--proposed-file", required=True)
    propose_parser.add_argument("--created-by", default="agentic_librarian")
    propose_parser.add_argument("--contradiction", action="store_true")
    propose_parser.add_argument("--supersedes")
    propose_parser.add_argument("--project-path")

    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("proposal_id")
    apply_parser.add_argument("--dry-run", action="store_true")

    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("proposal_id")

    rollback_parser = commands.add_parser("rollback")
    rollback_parser.add_argument("proposal_id")
    rollback_parser.add_argument("--confirm-proposal-id", required=True)
    rollback_parser.add_argument("--dry-run", action="store_true")

    archive_parser = commands.add_parser("archive")
    archive_parser.add_argument("proposal_id")

    status_parser = commands.add_parser("status")
    status_parser.add_argument("--write", action="store_true")

    commands.add_parser("inbox")
    commands.add_parser("doctor")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        vault_root = no_alias_path(Path(args.vault_root))
        if not vault_root.is_dir():
            return emit({"error": "vault_not_found", "message": str(vault_root)}, 2)
        require_store_integrity(vault_root)
        if args.command == "ingest":
            return emit(ingest(vault_root, args))
        if args.command == "propose":
            return emit(propose(vault_root, args))
        if args.command == "apply":
            return emit(apply_proposal(vault_root, args))
        if args.command == "verify":
            return emit(verify_proposal(vault_root, args))
        if args.command == "rollback":
            return emit(rollback_proposal(vault_root, args))
        if args.command == "archive":
            return emit(archive_proposal(vault_root, args))
        if args.command == "status":
            return emit(status_command(vault_root, args))
        if args.command == "inbox":
            return emit(inbox_command(vault_root, args))
        if args.command == "doctor":
            result, code = doctor_command(vault_root, args)
            return emit(result, code)
    except LibrarianError as exc:
        return emit({"error": exc.code, "message": str(exc)}, 2)
    return emit({"error": "unknown_command", "message": args.command}, 2)


if __name__ == "__main__":
    sys.exit(main())
