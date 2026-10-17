---
name: aeos-close-session
description: Use when ending an AEOS work session to write back only verified facts and leave an honest report for the next session.
---

# Close a session

The next session will know only what is in the files. Leave them accurate.

1. Update only the records whose facts changed: the project's `PROJECT_STATE.md` and `NEXT_ACTIONS.md`, a decision record if a decision was made, and a dated run record. Preserve existing run evidence.
2. Write back only what is verified, and only if you are the authorized controller for that project. Otherwise leave the writeback as a proposal in the report.
3. Record unknown, missing, stale and contradictory information explicitly. Do not smooth it over.
4. Report, in this order:
   - what changed (files and commits),
   - what was verified and how,
   - what still needs independent review or an owner decision,
   - the single next action.

## Never claim

A test, push, merge, deploy, publication or human response that did not happen. If you are unsure whether something happened, say it is unknown.
