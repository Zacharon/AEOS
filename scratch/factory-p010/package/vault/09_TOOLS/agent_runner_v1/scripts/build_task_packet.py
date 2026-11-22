#!/usr/bin/env python3
"""Build a local schema-v1.2 draft task packet from one explicit project path.

Reads only known Markdown routing filenames, writes only --output, uses no
network or APIs, and refuses secret-like paths. The result remains draft until
a human completes the allowlists/checks and approves Gate A.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.2"
KNOWN_PROJECT_FILES = (
    "PROJECT_INDEX.md",
    "PROJECT_STATE.md",
    "NEXT_ACTIONS.md",
    "PROJECT_BRAIN.md",
    "CONTEXT_INDEX.md",
    "README.md",
    "current_state.md",
    "next_tasks.md",
    "DECISIONS.md",
    "OPEN_LOOPS.md",
)
ROLES = {
    "Commander",
    "Researcher",
    "Builder",
    "QA/H3 Verifier",
    "Documentation/Writeback",
    "Maintenance",
}
SECRET_PATTERNS = tuple(
    re.compile(pattern, re.I)
    for pattern in (r"^\.env", r"secret", r"credential", r"token", r"password", r"\.pem$", r"id_rsa")
)


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def preparation_module():
    """The lean export supports base packets without the optional plan catalog."""
    try:
        import capability_preparation
        return capability_preparation
    except ModuleNotFoundError as exc:
        if exc.name != "capability_preparation":
            raise
        die("capability preparation is not included in this lean installation; use the base packet builder or separately reviewed full preparation components")


def is_secretish(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def safe_directory(path: Path) -> Path:
    if not path.exists() or not path.is_dir():
        die(f"project path is not an existing directory: {path}")
    if any(is_secretish(part) for part in path.parts):
        die("refusing a project path with a secret-like component")
    return path.resolve()


def safe_output(path: Path) -> Path:
    if any(part in {".env", ".ssh", ".aws"} or is_secretish(part) for part in path.parts):
        die("refusing an output path with a secret-like component")
    return path


def collect_read_first(project: Path, vault_root: Path | None = None) -> list[str]:
    # Legacy detail can contain retired executable tasks. It is a fallback for
    # a missing canonical owner, never an additional current instruction set.
    fallbacks = {"current_state.md": "PROJECT_STATE.md", "next_tasks.md": "NEXT_ACTIONS.md"}
    paths = [project / name for name in KNOWN_PROJECT_FILES if (project / name).is_file()
             and not (name in fallbacks and (project / fallbacks[name]).is_file())]
    # Absence of a canonical owner cannot revive explicitly retired guidance.
    def retired(path: Path) -> bool:
        text = path.read_text(encoding='utf-8-sig')
        front = text.split('---', 2)[1] if text.startswith('---') else ''
        match = re.search(r'^status:\s*(.+)$', front, re.M | re.I)
        return bool(match and match.group(1).strip().strip('\"\'').lower()
                    in {'superseded', 'archived', 'rejected'})
    paths = [path for path in paths if path.name not in fallbacks or not retired(path)]
    found = [(path.relative_to(vault_root) if vault_root else path).as_posix() for path in paths]
    return found[:8]


def render(args: argparse.Namespace, project: Path, read_first: list[str]) -> str:
    today = dt.date.today().isoformat()
    run_id = f"RUN-{today}-000"
    task_id = f"TASK-{today}-000"
    project_name = args.project_name or project.name
    reads = "\n".join(f"{index}. `{path}`" for index, path in enumerate(read_first, 1))
    if not reads:
        reads = "1. `(no known routing Markdown found - fill manually)`"
    allowed_reads = "\n".join(f"- `{path}`" for path in read_first) or "- `(fill explicit read path)`"

    return f'''---
type: agent_task_packet
schema_version: "{SCHEMA_VERSION}"
run_id: {run_id}
task_id: {task_id}
status: draft
created: {today}
updated: {today}
project: {project_name}
project_path: "{project.as_posix()}"
role: {args.role}
worker_tool: {args.worker_tool}
risk_level: {args.risk_level}
h3_mode: {args.h3_mode}
repair_cycle_limit: 3
repair_cycles_used: 0
verification_lifecycle: pending
h3_verdict: null
human_gates: [A, C]
controller: Designated parent session
---
# Task Packet - {args.goal[:80]}

> Generated locally by `build_task_packet.py`. Complete every placeholder and obtain Gate A before dispatch.

## 1. Project

- **Name:** {project_name}
- **Path:** `{project.as_posix()}`
- **Routing files:** confirm from Read First

## 2. Task Identifier And Outcome

- **Task ID:** `{task_id}`
- **Outcome:** {args.goal}

## 3. Known Current State

- Builder found {len(read_first)} known routing Markdown file(s); inspect them before adding state claims.

## 4. Assumptions

- None recorded by the builder; add and verify any task assumptions.

## 5. Read First

{reads}

## 6. Allowed Reads

{allowed_reads}

## 7. Allowed Writes

- `(human must fill explicit path, or None (read-only))`

## 8. Forbidden Actions

- Do not move, rename, delete, archive, clean, reset, stash, or overwrite unrelated work.
- Do not push, merge, deploy, publish, send, open a PR, or change an external account without separate approval.
- Do not read, reproduce, or store `.env` contents, secrets, credentials, tokens, account numbers, raw browser data, or private records.
- Do not promote raw private data, bypass locks/gates, or claim unverified commands or actions.
- Do not edit global control files unless Allowed Writes names them.
- Do not spawn child agents unless the packet and parent protocol allow it.

## 9. Acceptance Criteria

| ID | Observable criterion | Priority | Evidence required |
|---|---|---|---|
| AC1 | Goal end state is observable. | must | `(fill)` |

## 10. Verification Plan

### Commands And Deterministic Checks

| ID | Command or exact check | Expected result | Evidence target |
|---|---|---|---|
| V1 | `(fill before work)` | `(fill)` | `(fill)` |

### Visual Verification

- **Required:** no
- **If not applicable:** `(state why deterministic checks are sufficient)`

### Preserved Behavior

- [ ] Locks and human gates remain intact.
- [ ] No private/raw data or unrelated work changes.
- [ ] Worktree and file ownership remain isolated.

## 11. Delegated Agent Roles

| Role/agent | Goal | Read boundary | Write boundary | Independent from |
|---|---|---|---|---|
| None | | | | |

## 12. Human Approval Gates

- **A - Packet approval:** required before dispatch.
- **C - Integration:** required before verified writeback/closure.
- **D - Live or external action:** none by default.
- **R3 approval:** not applicable unless scope changes.

## 13. Writeback Targets

- H3 episode/report: `(fill)`
- Project state/next/session files: `(fill only if facts change)`
- Optional global file: `(fill only for a global fact)`

## 14. Expected Final Response

Return working context; files read/created/modified; outcome; command and visual results; independent H3 verdict; repair cycles used; writeback; risks/human decisions; and exactly one next action. Separate verified, not independently verified, blocked, and not attempted.

## 15. Stop Conditions

- Draft packet, missing context/authority, unverifiable must-have criterion, scope/lock/worktree conflict, secret/private-data risk, unavailable independent H3, or three unsuccessful repair cycles.

## 16. Repair Cycle Record

| Cycle | Reproduced defect | Targeted repair | Checks rerun | Result |
|---:|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local schema-v1.2 draft task packet.")
    parser.add_argument("--project-path")
    parser.add_argument("--vault-root", help="Emit vault-relative scope paths for unified_handoff; project must be inside this verified vault.")
    parser.add_argument("--goal", help="Task/gig brief; treated as untrusted data in preparation mode")
    parser.add_argument("--role", default="Builder", choices=sorted(ROLES))
    parser.add_argument("--worker-tool", default="Codex", choices=["Cursor", "Codex", "Grok", "PowerShell", "Human"])
    parser.add_argument("--risk-level", default="R1", choices=["R0", "R1", "R2", "R3"])
    parser.add_argument("--h3-mode", default="full", choices=["full", "lightweight", "none"])
    parser.add_argument("--project-name")
    parser.add_argument("--output")
    parser.add_argument("--constraints", help="Optional capability-aware preparation JSON; no dispatch or approval")
    parser.add_argument("--check-preparation", help="Revalidate an exported capability_receipt.json without writes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_preparation:
        cp = preparation_module()
        if not args.vault_root or args.constraints or args.output or args.goal or args.project_path:
            die("check-preparation requires only --vault-root and a receipt")
        try:
            cp.no_links(Path(args.vault_root).absolute())
        except (ValueError,OSError) as exc:
            die(str(exc))
        root = safe_directory(Path(args.vault_root))
        if not (root / "00_SYSTEM/VAULT_INDEX.md").is_file():
            die("vault root must contain 00_SYSTEM/VAULT_INDEX.md")
        try:
            import json
            print(json.dumps(cp.recheck(root, Path(args.check_preparation).absolute()), indent=2))
            return 0
        except (ValueError, OSError, KeyError, TypeError) as exc:
            die(str(exc))
    if not args.project_path or not args.goal or not args.output:
        die("project-path, goal and output are required for packet generation")
    goal = args.goal.strip()
    if not goal:
        die("goal must be non-empty")
    args.goal = goal
    if args.constraints:
        cp = preparation_module()
        try:
            cp.no_links(Path(args.project_path).absolute())
            if args.vault_root: cp.no_links(Path(args.vault_root).absolute())
        except (ValueError,OSError) as exc:
            die(str(exc))
    project = safe_directory(Path(args.project_path))
    vault_root = safe_directory(Path(args.vault_root)) if args.vault_root else None
    if vault_root is not None:
        if not (vault_root / "00_SYSTEM" / "VAULT_INDEX.md").is_file():
            die("vault root must contain 00_SYSTEM/VAULT_INDEX.md")
        if not project.is_relative_to(vault_root):
            die("project path must be inside --vault-root")
    if args.constraints:
        cp = preparation_module()
        try:
            c, reads, receipt = cp.prepare(args, project, vault_root, args.constraints)
            args.role = "Researcher" if not receipt['proposed_write_scope'] else args.role
            args.risk_level = "R0" if not receipt['proposed_write_scope'] else args.risk_level
            draft = cp.augment(render(args, project, reads), c, reads, receipt)
            output = cp.export(vault_root, args.output, draft, receipt)
            print(f"Prepared v{SCHEMA_VERSION} draft and capability_receipt.json: {output}")
            print("NOT APPROVED / NOT DISPATCHED; revalidate before manual review")
            return 0
        except (ValueError, OSError, KeyError, TypeError) as exc:
            die(str(exc))
    output = safe_output(Path(args.output))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Packets can carry reviewed scope and decisions. A repeated invocation must
    # never replace that evidence, including a racing writer's newly created file.
    try:
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(render(args, project, collect_read_first(project, vault_root)))
    except FileExistsError:
        die("output already exists; preserve the packet and choose a new output path")
    print(f"Wrote schema-v{SCHEMA_VERSION} draft packet: {output.resolve()}")
    print("Next: fill placeholders, verify boundaries/checks, and obtain human Gate A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
