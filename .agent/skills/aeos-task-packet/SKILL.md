---
name: aeos-task-packet
description: Use to turn a goal into a bounded AEOS task packet with explicit scope, risk level, checks and authorization before any work starts.
---

# Write a task packet

A task packet is the contract for one bounded piece of work. A draft packet is not approval.

## Scaffold

From the vault root:

```powershell
python -B 09_TOOLS/agent_runner_v1/scripts/build_task_packet.py --vault-root . --project-path 01_PROJECTS/<Project> --goal "<one verifiable outcome>" --output 09_TOOLS/agent_runner_v1/runs/<task-id>/task_packet.md
```

Useful options: `--role`, `--worker-tool`, `--risk-level R0|R1|R2|R3`, `--h3-mode full|lightweight|none`. Run with `--help` for the rest. The goal text is treated as untrusted data.

## Fill it in

- **Allowed reads and writes:** exact files or folders. Every file the worker must read first has to be inside allowed reads.
- **Acceptance checks:** commands or observations that prove the outcome, with expected results.
- **Risk level:** pick the higher level when unsure.
  - R0 read-only.
  - R1 a narrow document or mechanical write.
  - R2 a bounded multi-file change: capture the before-state, run checks, report fully, independent review when material.
  - R3 structural, destructive, permission, deploy, publish or external writes: explicit human approval first; stop at `needs-review`.
- **Independent review:** whether H3 is required and in which mode.
- **Authorization:** who approved this scope and when. Leave it empty if nobody has; do not fill it yourself.

## Rules

- One packet, one outcome. Split anything larger.
- Never widen scope during the work. Stop and write a new packet instead.
- Publishing, sending, spending, account changes and destructive actions each need their own explicit approval.
