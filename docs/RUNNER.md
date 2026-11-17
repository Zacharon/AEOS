# Runner v1: attended bounded work

Runner v1 is a file-based operator harness. A controller prepares and reviews a packet, an attended worker performs its scoped task, and the controller checks the return. The public package supplies packet and handoff commands; it does not install a background scheduler or model client. Use [Architecture](ARCHITECTURE.md) and the [handoff skill](../.agent/skills/aeos-handoff/SKILL.md) for the shipped command contracts.

## Packet contract

The general Runner schema records packet and task identity, version, project boundary, role, worker tool, risk, controller and human gates. It separately records execution status, verification lifecycle, nullable independent verdict and a repair limit of three.

Its body identifies the observable outcome, inspected current state, assumptions, ordered read-first set, exact allowed reads and writes, forbidden actions, acceptance criteria, check commands, preserved behavior, delegation ownership, approval gates, writeback targets, return format, stop conditions and repair history. Keep worker hydration to at most eight read-first files. A draft is not executable authority.

The [blank worksheet](../templates/task-packet.md) helps author that contract; it is not a machine-valid Runner packet. Use the shipped scaffolder and its schema when a CLI consumes a packet, and validate before dispatch. Do not infer schema compatibility from similar headings.

## Lanes and oversight

A controller scopes and integrates; a researcher returns source-backed drafts; a builder implements; a separate reviewer checks evidence; an authorized documentation role writes verified facts; a maintenance role proposes hygiene work. These lanes describe responsibilities, not installed agents. The [four role cards](../.agent/README.md#role-cards) describe narrower read-only specialists.

Before dispatch, check authorization and current sources. After return, inspect scope, actual changes and check evidence. Source drift requires inspection and a fresh authorized bundle. Missing results remain unknown; do not fabricate results or blindly repeat work. Integration, external effects and global writeback each retain their applicable human gates.

## Kernel boundary

The broader execution-kernel design standardizes run state, review packets, checkpoints, evaluation and append-only artifact records. Replay inspects recorded transitions and missing evidence; it does not repeat live actions or guarantee reproduction of model choices. The public package exposes only the subset documented in Architecture. These docs add no general kernel runner or private implementation.
