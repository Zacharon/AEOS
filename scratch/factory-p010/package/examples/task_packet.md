---
type: agent_task_packet
schema_version: "1.2"
run_id: RUN-2026-10-08-901
task_id: TASK-SAMPLE-001
status: approved
created: 2026-10-08
updated: 2026-10-08
project: Sample
project_path: 01_PROJECTS/Sample
role: Researcher
worker_tool: Human
risk_level: R0
h3_mode: lightweight
repair_cycle_limit: 3
repair_cycles_used: 0
verification_lifecycle: pending
h3_verdict: null
human_gates: [C]
controller: Synthetic demonstration only
---
# Synthetic source-count packet

## 1. Project
Sample local fixture. This fixture status is not real owner approval.

## 2. Task Identifier And Outcome
Count checked items from the supplied source and cite its exact bytes.

## 3. Known Current State
Only authored synthetic inputs are included. Silver remains pending.

## 4. Assumptions
No customer or production behavior is inferred from this example.

## 5. Read First
__READS__

## 6. Allowed Reads
__READS__

## 7. Allowed Writes
None (read-only)

## 8. Forbidden Actions
Do not read secret or private data, bypass a lock or human approval, take external actions, publish, send, promote Gold, or claim uncaptured evidence. Only bundle-local evidence is created by the demonstration controller.

## 9. Acceptance Criteria
| ID | Observable criterion | Priority | Evidence required |
|---|---|---|---|
| AC1 | Count matches two done rows; exact source cited; pending proposal stays pending. | must | artifacts/report.md |

## 10. Verification Plan
Command: demo.py performs source count and exact hash checks, validates candidate result and runs fresh-process review. Evidence: artifacts/report.md and commands.json.
Visual: not applicable to plain text computation.
Preserved behavior: sources and owner decision fields remain unchanged; no Gold application.

## 11. Delegated Agent Roles
No AI worker or independent reviewer is invoked by this deterministic demonstration.

## 12. Human Approval Gates
Fixture-only input. Real tasks require actual authority. Gate C blocks real canonical integration.

## 13. Writeback Targets
None. Candidate report remains bundle-local; an actual controller must review before factual canonical writeback.

## 14. Expected Final Response
Return source count, evidence, pending status, limits and next action.

## 15. Stop Conditions
Stop on missing evidence, source drift, scope conflict, missing approval or three unsuccessful repair cycles.

## 16. Repair Cycle Record
None.
