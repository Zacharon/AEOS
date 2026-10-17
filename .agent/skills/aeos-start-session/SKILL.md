---
name: aeos-start-session
description: Use at the start of any session in an AEOS vault to find the right project and read only the files the task needs.
---

# Start a session

AEOS keeps project facts in files so a fresh session can continue without chat memory. Read the minimum, in this order.

1. Read the vault `AGENTS.md`. Then read `00_SYSTEM/SESSION_START_ROUTER.md`.
2. **Named project:** read its `PROJECT_INDEX.md`, `PROJECT_STATE.md` and `NEXT_ACTIONS.md` under `01_PROJECTS/<Project>/`. Check current locks and what is actually authorized.
3. **Choosing among projects:** consult only `00_SYSTEM/GLOBAL_NEXT_ACTION_QUEUE.md`. Dashboards, summaries and prompts never select work.
4. **Continuing earlier work:** if a saved handoff bundle exists, run `handoff.py review` (see [aeos-handoff](../aeos-handoff/SKILL.md)) before trusting anything it says.
5. Select only the procedures and source notes the task needs. Never load the whole vault, raw capture, archives or generated packs.

## Source-of-truth order

Current project records and explicit owner decisions > primary specs > verified repository state > generated summaries > conversation memory > your own inference. When two records disagree, report the contradiction; do not pick a winner.

## Before acting

State the goal, allowed reads, allowed writes, acceptance evidence and the actual authorization. If any of these is missing, write it into a task packet ([aeos-task-packet](../aeos-task-packet/SKILL.md)) instead of guessing.

## Never

- Read secrets, credentials, `.env` files or private system/browser data.
- Treat the shipped `Sample` project, its packet or its status as permission for real work. It is synthetic.
- Put application code in the vault. It belongs in its own named repository.
