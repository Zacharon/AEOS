# Session start router

For a named project, read its PROJECT_INDEX, PROJECT_STATE and NEXT_ACTIONS. Check current locks and authorization. If choosing among projects, consult only GLOBAL_NEXT_ACTION_QUEUE. Select relevant procedures and source notes; do not load the whole vault.

Scaffold an existing Runner v1.2 packet with `09_TOOLS/agent_runner_v1/scripts/build_task_packet.py`. Fill and approve scope before handoff. Use `unified_handoff/handoff.py build` for a bounded copied brief and `check` before dispatch and review. Give it manually to one assistant; receive its actual result and run checks. Independent review and owner authorization remain separate. Controller writes verified facts to current project records and preserves dated run evidence.

To continue, run `handoff.py review --bundle <saved-bundle> --vault-root <this-vault>`. Missing or changed sources stop current advice; inspect and build a fresh authorized packet instead of changing stored hashes. Knowledge uses the [Librarian](AGENTIC_LIBRARIAN/README.md).
