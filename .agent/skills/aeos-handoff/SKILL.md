---
name: aeos-handoff
description: Use to package an approved task packet into a bounded handoff bundle, check it, validate a returned result, or resume saved work in a fresh session.
---

# Hand off, return and resume

The handoff CLI copies only selected sources into a bundle with hashes, so the receiving assistant sees a fixed, checkable context. It never dispatches work, runs a model, authenticates approval or issues independent review. Transport is manual.

All commands run from the vault parent with `vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py`, or from the vault root without the `vault/` prefix. Keep bundles outside the source vault.

## 1. Build

```powershell
python -B handoff.py build --vault-root <vault> --packet <task_packet.md> --executor <codex|grok-build|grok-fleet|hermes|human> --read <file> [--read <file> ...] --output <bundle-dir>
```

Between one and eight `--read`/`--skill` files in total. Each must be inside the packet's allowed reads, and every Read First file must be included.

## 2. Check before giving it to anyone

```powershell
python -B handoff.py check --bundle <bundle-dir> --vault-root <vault>
```

This rehashes every live source. Changed or missing sources mean stop: inspect what changed and build a new authorized bundle. Never edit stored hashes.

## 3. Execute (the receiving assistant)

Do only what the brief authorizes, inside its allowed writes. Fill the bundle's result template as `worker_result.json` with what actually happened, the artifacts and the check output. `proposed_writeback` is a suggestion; nobody applies it automatically.

## 4. Validate the return

```powershell
python -B handoff.py validate-result --bundle <bundle-dir> --result <worker_result.json>
python -B handoff.py review --bundle <bundle-dir> --vault-root <vault>
```

`validate-result` checks structure and evidence hashes. `review` combines source freshness with the saved result and is read-only. `complete` additionally checks actual scoped changes and their rationale; run `handoff.py complete --help` for its inputs.

## Resume in a fresh session

Run `review` against the saved bundle and read the returned artifact and next action. A missing result is **unknown**, not proof that work never happened. Drift needs inspection and a fresh authorized handoff, never a blind retry.

## Passing checks are not approval

A green `check`, `validate-result` or `complete` is mechanical evidence only. Independent review ([aeos-independent-review](../aeos-independent-review/SKILL.md)) and owner acceptance remain separate steps.
