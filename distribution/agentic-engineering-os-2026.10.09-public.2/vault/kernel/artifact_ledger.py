"""Append-only artifact ledger for the deterministic execution kernel.

The ledger stores JSONL entries under ``.kernel_runs/ledger/``. Each entry is
canonicalized before writing so the payload hash is stable across process runs.
Existing entries are never updated in place.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from kernel.execution_contract import (
    ARTIFACT_EVAL_RESULT,
    ARTIFACT_EVIDENCE_LINK,
    ARTIFACT_EXECUTION_CONTRACT,
    ARTIFACT_EXECUTION_PLAN,
    ARTIFACT_KNOWLEDGE_CONTRADICTION_RESOLVED,
    ARTIFACT_KNOWLEDGE_OWNER_DECISION,
    ARTIFACT_KNOWLEDGE_PROPOSAL_APPLIED,
    ARTIFACT_KNOWLEDGE_PROPOSAL_CREATED,
    ARTIFACT_KNOWLEDGE_PROPOSAL_REJECTED,
    ARTIFACT_KNOWLEDGE_PROPOSAL_VERIFIED,
    ARTIFACT_KNOWLEDGE_ROLLBACK,
    ARTIFACT_KNOWLEDGE_SOURCE_INGESTED,
    ARTIFACT_MEMORY_CHECKPOINT,
    ARTIFACT_REVIEW_DECISION,
    ARTIFACT_REVIEW_PACKET,
    ARTIFACT_RUN_STATE,
    ARTIFACT_STATE_TRANSITION,
    ARTIFACT_TOOL_GATEWAY_CALL,
    ARTIFACT_UNCERTAINTY_ASSESSMENT,
    VALID_ARTIFACT_TYPES,
)


DEFAULT_LEDGER_DIR = Path(".kernel_runs") / "ledger"
DEFAULT_LEDGER_FILE = "artifact_ledger.jsonl"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ArtifactLedgerError(Exception):
    """Base error for artifact ledger failures."""


class InvalidArtifactTypeError(ArtifactLedgerError, ValueError):
    """Raised when an artifact type is outside the kernel ledger contract."""


class InvalidPayloadError(ArtifactLedgerError, ValueError):
    """Raised when a payload cannot be safely recorded."""


class LedgerCorruptionError(ArtifactLedgerError):
    """Raised when an existing ledger entry fails replay validation."""


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidPayloadError("payload must be canonical JSON serializable") from exc


def _payload_hash(payload: Any) -> str:
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _entry_hash_payload(entry: dict[str, Any]) -> str:
    if "payload" not in entry:
        raise LedgerCorruptionError("ledger entry is missing payload")
    return _payload_hash(entry["payload"])


def _entry_hash(entry: dict[str, Any]) -> str:
    hash_material = {
        "timestamp": entry["timestamp"],
        "run_id": entry["run_id"],
        "artifact_type": entry["artifact_type"],
        "payload_hash": entry["payload_hash"],
    }
    return hashlib.sha256(_canonical_json(hash_material).encode("utf-8")).hexdigest()


def _validate_artifact_type(artifact_type: str) -> None:
    if artifact_type not in VALID_ARTIFACT_TYPES:
        allowed = ", ".join(sorted(VALID_ARTIFACT_TYPES))
        raise InvalidArtifactTypeError(
            f"unsupported artifact_type {artifact_type!r}; expected one of: {allowed}"
        )


def _extract_run_id(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise InvalidPayloadError("payload must be a JSON object containing run_id")

    return _validate_run_id(payload.get("run_id"), field_name="payload.run_id")


def _validate_run_id(run_id: Any, *, field_name: str = "run_id") -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise InvalidPayloadError(f"{field_name} must be a non-empty string")

    normalized = run_id.strip()
    if normalized != run_id:
        raise InvalidPayloadError(f"{field_name} must not have leading/trailing space")
    if normalized in {".", ".."} or not RUN_ID_PATTERN.fullmatch(normalized):
        raise InvalidPayloadError(
            f"{field_name} must use only letters, numbers, dot, underscore, or hyphen; "
            "it must start with a letter or number and must not contain path separators"
        )

    return normalized


def _deepcopy_json_payload(payload: Any) -> Any:
    return json.loads(_canonical_json(payload))


class ArtifactLedger:
    """File-backed append-only JSONL ledger.

    Parameters:
        ledger_dir: Directory for ledger files. Defaults to
            ``.kernel_runs/ledger/`` relative to the current working directory.
        ledger_file: JSONL file name inside the ledger directory.
    """

    def __init__(
        self,
        ledger_dir: str | Path = DEFAULT_LEDGER_DIR,
        ledger_file: str = DEFAULT_LEDGER_FILE,
    ) -> None:
        self.ledger_dir = Path(ledger_dir)
        self.ledger_path = self.ledger_dir / ledger_file

    def append(self, artifact_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Append one immutable artifact entry and return the entry.

        The payload must contain ``run_id``. The payload is deep-copied through
        canonical JSON before hashing and writing, so caller-side mutations after
        append cannot affect the recorded entry.
        """

        _validate_artifact_type(artifact_type)
        run_id = _extract_run_id(payload)
        frozen_payload = _deepcopy_json_payload(payload)

        entry = {
            "timestamp": _utc_timestamp(),
            "run_id": run_id,
            "artifact_type": artifact_type,
            "payload": frozen_payload,
            "payload_hash": _payload_hash(frozen_payload),
        }
        entry["entry_hash"] = _entry_hash(entry)

        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as ledger:
            ledger.write(f"{_canonical_json(entry)}\n")

        return copy.deepcopy(entry)

    def query(self, run_id: str) -> list[dict[str, Any]]:
        """Return replay-validated entries for one run ID in append order."""

        validated_run_id = _validate_run_id(run_id)

        return [
            entry for entry in self._iter_entries() if entry["run_id"] == validated_run_id
        ]

    def export(self, run_id: str) -> str:
        """Return canonical JSONL for one run ID.

        Export output is replay-safe: every returned entry has already been
        validated against its stored payload hash, and each line is canonical
        JSON with sorted keys.
        """

        return "".join(f"{_canonical_json(entry)}\n" for entry in self.query(run_id))

    def _iter_entries(self) -> Iterable[dict[str, Any]]:
        if not self.ledger_path.exists():
            return

        with self.ledger_path.open("r", encoding="utf-8") as ledger:
            for line_number, line in enumerate(ledger, start=1):
                stripped = line.strip()
                if not stripped:
                    continue

                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise LedgerCorruptionError(
                        f"invalid JSONL at {self.ledger_path}:{line_number}"
                    ) from exc

                self._validate_entry(entry, line_number)
                yield entry

    def _validate_entry(self, entry: Any, line_number: int) -> None:
        if not isinstance(entry, dict):
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} must be a JSON object"
            )

        required_fields = {
            "timestamp",
            "run_id",
            "artifact_type",
            "payload",
            "payload_hash",
            "entry_hash",
        }
        missing = sorted(required_fields - set(entry))
        if missing:
            joined = ", ".join(missing)
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} is missing: {joined}"
            )

        _validate_artifact_type(entry["artifact_type"])
        if not isinstance(entry["timestamp"], str) or not entry["timestamp"]:
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} has invalid timestamp"
            )
        if not isinstance(entry["run_id"], str) or not entry["run_id"]:
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} has invalid run_id"
            )

        payload_run_id = _extract_run_id(entry["payload"])
        if payload_run_id != entry["run_id"]:
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} run_id does not match payload"
            )

        expected_hash = _entry_hash_payload(entry)
        if entry["payload_hash"] != expected_hash:
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} payload hash mismatch"
            )

        expected_entry_hash = _entry_hash(entry)
        if entry["entry_hash"] != expected_entry_hash:
            raise LedgerCorruptionError(
                f"ledger entry at line {line_number} entry hash mismatch"
            )


_default_ledger = ArtifactLedger()


def append(artifact_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append an entry to the default ledger."""

    return _default_ledger.append(artifact_type, payload)


def query(run_id: str) -> list[dict[str, Any]]:
    """Query entries from the default ledger by run ID."""

    return _default_ledger.query(run_id)


def export(run_id: str) -> str:
    """Export entries from the default ledger by run ID as JSONL."""

    return _default_ledger.export(run_id)
