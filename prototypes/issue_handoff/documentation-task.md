---
type: agent_task_packet
schema_version: "1.2"
run_id: RUN-2026-11-13-002
task_id: AEOS-DOC-PR-PILOT
status: approved
created: 2026-11-13
updated: 2026-11-13
project: AEOS
project_path: .
role: Documentation/Writeback
worker_tool: Codex
risk_level: R1
h3_mode: full
repair_cycle_limit: 3
repair_cycles_used: 0
verification_lifecycle: pending
h3_verdict: null
human_gates: [publication, owner-acceptance]
controller: Local task controller
---

# Local documentation pilot packet

## 1. Project
AEOS source checkout; public-safe documentation only. The local pilot is
authorized by its operator. This reusable example never authenticates approval.

## 2. Task Identifier And Outcome
Add a short troubleshooting section to docs/DOCUMENTATION_PR_WORKFLOW.md,
explaining how to recover from missing contracts, stale inputs/evidence,
incomplete rationale and required checks that did not pass. Use actual messages
and behavior from the adapter. Do not claim checks or adoption that did not run.

## 3. Known Current State
Frozen public.4 provides packet, bundle, result and rationale validation.
The source adapter composes these checks; native delegation is controller-owned.

## 4. Assumptions
The controller verifies the bound repository, branch and baseline separately.
One writer owns the allowed document. No private installation is used as input.

## 5. Read First
- `AGENTS.md`
- `prototypes/issue_handoff/WORKER_CONTRACT.md`
- `.agent/skills/aeos-handoff/SKILL.md`

## 6. Allowed Reads
- `AGENTS.md`
- `.agent/README.md`
- `prototypes/issue_handoff/WORKER_CONTRACT.md`
- `.agent/skills/aeos-handoff/SKILL.md`
- `prototypes/issue_handoff/documentation_workflow.py`
- `docs/DOCUMENTATION_PR_WORKFLOW.md`
- `tests/test_documentation_workflow.py`
- `distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py`
- `distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/code_rationale.py`

## 7. Allowed Writes
- `docs/DOCUMENTATION_PR_WORKFLOW.md`

## 8. Forbidden Actions
No secrets, private data, external actions, approval changes, lock bypass,
fabricated evidence, frozen package edits, other repository changes, subagents,
Git mutations, publication or canonical vault writeback. Preserve prior evidence.

## 9. Acceptance Criteria
| ID | Observable criterion | Priority | Evidence required |
|---|---|---|---|
| A1 | Recovery guidance matches adapter messages and preserves old evidence | must | artifacts/report.md |
| A2 | Focused workflow tests pass and return includes complete rationale | must | artifacts/checks.txt |

## 10. Verification Plan
Command: python -B -m unittest discover -s tests -p test_documentation_workflow.py -v.
Required check name: workflow-tests. Evidence: captured artifacts/checks.txt.
Visual: not applicable to CLI/documentation. Preserved: all other files,
historical evidence, selected inputs and frozen package bytes.

## 11. Delegated Agent Roles
One documentation worker. Separate independent H3 reviewer after integration.
Controller validates the return, reruns checks and owns factual writeback.

## 12. Human Approval Gates
The owner authorized this local pilot. Status is not authenticated identity.
Publication, merge, deploy and owner acceptance remain separate decisions.

## 13. Writeback Targets
None for the worker. Return candidate evidence; controller owns private state.

## 14. Expected Final Response
Return worker_result.json, artifacts/report.md and artifacts/checks.txt using
the complete selected contract. Include a documentation delta in the report.
Declare optional hosted CI and owner acceptance not_run. Stop ready_for_review.

## 15. Stop Conditions
Stop on stale input, wrong checkout, incomplete contract, failed check or three
unsuccessful repairs. Never repair a baseline digest or overwrite prior evidence.

## 16. Repair Cycle Record
Zero at packet preparation. Preserve failed attempts and controller decisions.

## Context selection
```context-selection
{
  "sources": [
    {"path":"AGENTS.md","scope":"repository-rules","authority":"Repository boundary and entry rules","status":"active","replacement":null,"references":[".agent/README.md"]},
    {"path":"prototypes/issue_handoff/WORKER_CONTRACT.md","scope":"worker-contract","authority":"Complete public.4 return and rationale shapes","status":"active","replacement":null,"references":["distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/handoff.py","distribution/agentic-engineering-os-2026.10.17-public.4/vault/09_TOOLS/agent_runner_v1/unified_handoff/code_rationale.py"]},
    {"path":".agent/skills/aeos-handoff/SKILL.md","scope":"handoff-procedure","authority":"Repository handoff usage","status":"active","replacement":null,"references":[]}
  ],
  "dependencies":["prototypes/issue_handoff/documentation_workflow.py","tests/test_documentation_workflow.py"],
  "contracts":{"return":"prototypes/issue_handoff/WORKER_CONTRACT.md","rationale":"prototypes/issue_handoff/WORKER_CONTRACT.md"},
  "documentation":[{"paths":["docs/DOCUMENTATION_PR_WORKFLOW.md"],"documents":["docs/DOCUMENTATION_PR_WORKFLOW.md"]}],
  "required_artifacts":["artifacts/report.md","artifacts/checks.txt"],
  "required_checks":["workflow-tests"]
}
```
